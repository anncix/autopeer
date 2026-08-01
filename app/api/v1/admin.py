"""Admin-only REST endpoints: global peers, intra-links, users — under ``/api/v1/admin``.

Everything here requires require_api_admin. These complement the user-scoped /api/v1/peers
(which an admin can also use for their own peers) with the cross-user management views an
operator needs: list/inspect any peer, manage backbone intra-links, list users.

Admin-only REST 端点: 全域 peer、intra-links、users。全部需 require_api_admin。这些端点补充
用户范围的 /api/v1/peers(admin 也可用它管理自己的 peer),提供操作者所需的跨用户管理视图:
列出/检视任意 peer、管理骨干 intra-links、列出用户。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_api_admin
from app.api.schemas import (
    IntraLinkAdmin,
    IntraLinkCreateRequest,
    IntraLinkOut,
    OkResponse,
    PeerAdmin,
    UserOut,
    peer_to_dict,
)
from app.db.models import IntraLink, Node, PeerRequest, User
from app.db.session import get_db
from app.intra.deploy import remove_intra_link
from app.peer.queries import peer_with_node
from app.web.admin import _provision_intra_link
from app.web.deps import settings

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _peer_to_admin(peer: PeerRequest) -> PeerAdmin:
    return PeerAdmin(
        **peer_to_dict(peer),
        deploy_output=peer.deploy_output or "",
        admin_note=peer.admin_note or "",
    )


def _intra_to_out(link: IntraLink) -> IntraLinkOut:
    return IntraLinkOut(
        id=link.id,
        node_id=link.node_id,
        remote_node_id=link.remote_node_id,
        label=link.label,
        protocol_name=link.protocol_name,
        remote_endpoint=link.remote_endpoint,
        listen_port=link.listen_port,
        link_local_address=link.link_local_address,
        deploy_status=link.deploy_status,
        created_at=link.created_at,
    )


def _intra_to_admin(link: IntraLink) -> IntraLinkAdmin:
    return IntraLinkAdmin(
        **_intra_to_out(link).model_dump(),
        deploy_output=link.deploy_output or "",
        deployed_at=link.deployed_at,
    )


# --------------------------------------------------------------------------- peers (global)


@router.get("/peers", response_model=list[PeerAdmin])
def admin_list_peers(admin: User = Depends(require_api_admin), db: Session = Depends(get_db)):
    """List all peers across all users (newest first). Returns PeerAdmin (includes deploy_output
    for diagnosing failures). This is the admin counterpart to the user-scoped GET /api/v1/peers.
    列出所有用户的所有 peer(最新在前)。回 PeerAdmin(含 deploy_output 以诊断失败)。
    此为 admin 版的用户范围 GET /api/v1/peers。"""
    peers = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .order_by(PeerRequest.created_at.desc())
        .all()
    )
    return [_peer_to_admin(p) for p in peers]


@router.get("/peers/{peer_id}", response_model=PeerAdmin)
def admin_get_peer(
    peer_id: str,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    peer = peer_with_node(db, peer_id)
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    return _peer_to_admin(peer)


# --------------------------------------------------------------------------- intra-links


@router.get("/nodes/{node_id}/intra-links", response_model=list[IntraLinkAdmin])
def admin_list_intra_links(
    node_id: str,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    """List intra-links on a node. Admin-only — backbone topology is operator-sensitive.
    列出节点上的 intra-links。仅 admin——骨干拓扑对操作者敏感。"""
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    links = (
        db.query(IntraLink)
        .filter(IntraLink.node_id == node.id)
        .order_by(IntraLink.created_at.desc())
        .all()
    )
    return [_intra_to_admin(lnk) for lnk in links]


@router.post("/nodes/{node_id}/intra-links", response_model=IntraLinkAdmin, status_code=201)
def admin_create_intra_link_api(
    node_id: str,
    body: IntraLinkCreateRequest,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    """Create an intra link. Reuses _provision_intra_link (the same helper the HTML form and the
    progressive-enhancement /api endpoint use), so validation + deploy logic is identical. A typed
    Pydantic body (IntraLinkCreateRequest) rejects malformed fields with 422 before the handler.
    reverse creates a matching link on the remote node too.
    创建 intra-link。复用 _provision_intra_link(与 HTML 表单、渐进增强 /api 端点同一 helper),
    验证 + 部署逻辑一致。使用 Pydantic 类型化请求体(IntraLinkCreateRequest),格式错误以 422 拒绝。
    reverse 会同时在远端节点建立匹配链路。"""
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    remote_node_id = (body.remote_node_id or "").strip()
    remote_public_key = body.remote_public_key
    remote_endpoint = body.remote_endpoint
    label = body.label.strip()
    deploy = body.deploy
    reverse = body.reverse

    remote_node: Node | None = None
    if remote_node_id:
        remote_node = db.query(Node).filter(Node.id == remote_node_id).one_or_none()
        if remote_node is None:
            raise HTTPException(status_code=400, detail="Selected remote node was not found.")
        if not remote_public_key.strip():
            remote_public_key = remote_node.wg_public_key or ""
        if not remote_endpoint.strip():
            remote_endpoint = remote_node.url

    link, ok, msg = _provision_intra_link(
        db, settings, node, remote_node_id, remote_public_key, remote_endpoint, label, deploy
    )
    if link is None:
        raise HTTPException(status_code=400, detail=msg)
    if reverse and remote_node is not None:
        if not node.wg_public_key:
            raise HTTPException(
                status_code=400,
                detail=f"Reverse link skipped: {node.name} has no registered WireGuard public key.",
            )
        rev_label = label or f"{node.name}-{remote_node.name}"
        _provision_intra_link(
            db, settings, remote_node, node.id, node.wg_public_key, node.url, rev_label, deploy
        )
    return _intra_to_admin(link)


@router.delete("/nodes/{node_id}/intra-links/{link_id}", response_model=OkResponse)
def admin_delete_intra_link_api(
    node_id: str,
    link_id: str,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    link = (
        db.query(IntraLink)
        .filter(IntraLink.id == link_id, IntraLink.node_id == node_id)
        .one_or_none()
    )
    if link is None:
        raise HTTPException(status_code=404, detail="Intra link not found")
    if link.deploy_status == "deployed":
        try:
            remove_intra_link(link, link.node)
        except Exception:  # noqa: BLE001 - best-effort teardown; still delete the record
            pass
    db.delete(link)
    db.commit()
    return OkResponse(ok=True, message=f"Intra link {link.protocol_name} deleted.")


# --------------------------------------------------------------------------- users


@router.get("/users", response_model=list[UserOut])
def admin_list_users(admin: User = Depends(require_api_admin), db: Session = Depends(get_db)):
    """List users. Returns UserOut — Telegram chat ids and ASN-identity maintainer JSON are
    stripped (PII / identity metadata not needed for user management).
    列出用户。回 UserOut——剥离 Telegram chat id 与 ASN 身份 maintainer JSON(管理用户无需的
    PII/身分元数据)。"""
    users = db.query(User).order_by(User.primary_asn).all()
    return [UserOut.model_validate(u) for u in users]
