"""Node endpoints: public read + admin CRUD under ``/api/v1/nodes`` and ``/api/v1/admin/nodes``.

The public ``GET /api/v1/nodes`` is anonymous (peers need the node list to choose a PoP) and
returns NodePublic (no token). Admin CRUD lives under /api/v1/admin/nodes and returns NodeAdmin
(includes the agent token, needed to enroll a node service). Node create/update reuse the same
validation helpers as the HTML admin routes (_clean_node_fields, normalize_node_host).

节点端点: 公开读 + admin CRUD。公开 GET /api/v1/nodes 匿名(peer 需节点清单以选 PoP),回 NodePublic
(无 token)。admin CRUD 在 /api/v1/admin/nodes 下,回 NodeAdmin(含 agent token,注册 node service
所需)。node create/update 复用与 HTML admin 路由相同的验证 helper。
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_api_admin
from app.api.schemas import NodeAdmin, NodeCreateRequest, NodePublic, NodeUpdateRequest, OkResponse
from app.db.models import Node, PeerRequest, User
from app.db.session import get_db
from app.peer.deploy import fetch_node_public_key
from app.peer.validation import normalize_node_host
from app.web.admin import _clean_node_fields

public_router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])
admin_router = APIRouter(prefix="/api/v1/admin/nodes", tags=["nodes-admin"])


def _node_to_admin(node: Node) -> NodeAdmin:
    return NodeAdmin(
        id=node.id,
        name=node.name,
        location=node.location,
        url=node.url,
        asn=node.asn,
        dn42_ipv4=node.dn42_ipv4,
        dn42_ipv6=node.dn42_ipv6,
        wg_public_key=node.wg_public_key,
        enabled=node.enabled,
        token=node.token,
        last_seen_at=node.last_seen_at,
        system_status_json=node.system_status_json,
        created_at=node.created_at,
    )


# --------------------------------------------------------------------------- public read


@public_router.get("", response_model=list[NodePublic])
def list_public_nodes(db: Session = Depends(get_db)):
    """Anonymous list of enabled nodes, ordered by name. Disabled nodes are hidden — they are
    not accepting peers. Returns NodePublic (token/system_status_json stripped).
    匿名列出已启用节点(按名排序)。已禁用节点隐藏——它们不接受 peer。回 NodePublic
    (剥离 token/system_status_json)。"""
    nodes = db.query(Node).filter(Node.enabled.is_(True)).order_by(Node.name).all()
    return [NodePublic.model_validate(n) for n in nodes]


@public_router.get("/{node_id}", response_model=NodePublic)
def get_public_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id, Node.enabled.is_(True)).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return NodePublic.model_validate(node)


# --------------------------------------------------------------------------- admin CRUD


@admin_router.get("", response_model=list[NodeAdmin])
def admin_list_nodes(admin: User = Depends(require_api_admin), db: Session = Depends(get_db)):
    """Admin list of ALL nodes (including disabled), with token + runtime fields. Admin-only —
    the token is a node-service enrollment credential.
    admin 列出全部节点(含已禁用),含 token 与运行时字段。仅 admin——token 是 node service
    注册凭据。"""
    nodes = db.query(Node).order_by(Node.name).all()
    return [_node_to_admin(n) for n in nodes]


@admin_router.post("", response_model=NodeAdmin, status_code=201)
def admin_create_node(
    body: NodeCreateRequest,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    name = body.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Node name is required.")
    try:
        url = normalize_node_host(body.url)
        asn, dn42_ipv4, dn42_ipv6 = _clean_node_fields(body.asn, body.dn42_ipv4, body.dn42_ipv6)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if db.query(Node).filter(Node.name == name).one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"A node named '{name}' already exists.")
    node = Node(
        name=name,
        location=body.location.strip(),
        url=url,
        asn=asn,
        dn42_ipv4=dn42_ipv4,
        dn42_ipv6=dn42_ipv6,
        token=secrets.token_urlsafe(32),
        enabled=body.enabled,
    )
    db.add(node)
    db.commit()
    db.refresh(node)
    return _node_to_admin(node)


@admin_router.get("/{node_id}", response_model=NodeAdmin)
def admin_get_node(
    node_id: str,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return _node_to_admin(node)


@admin_router.patch("/{node_id}", response_model=NodeAdmin)
def admin_update_node(
    node_id: str,
    body: NodeUpdateRequest,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if body.name is not None:
        name = body.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Node name is required.")
        if (
            db.query(Node).filter(Node.name == name, Node.id != node.id).one_or_none()
            is not None
        ):
            raise HTTPException(status_code=409, detail=f"A node named '{name}' already exists.")
        node.name = name
    if body.location is not None:
        node.location = body.location.strip()
    if body.url is not None:
        try:
            node.url = normalize_node_host(body.url)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
    if body.asn is not None or body.dn42_ipv4 is not None or body.dn42_ipv6 is not None:
        try:
            asn, dn42_ipv4, dn42_ipv6 = _clean_node_fields(
                body.asn if body.asn is not None else node.asn,
                body.dn42_ipv4 if body.dn42_ipv4 is not None else node.dn42_ipv4,
                body.dn42_ipv6 if body.dn42_ipv6 is not None else node.dn42_ipv6,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        node.asn, node.dn42_ipv4, node.dn42_ipv6 = asn, dn42_ipv4, dn42_ipv6
    if body.enabled is not None:
        node.enabled = body.enabled
    # Re-sync the public key from the (maybe changed) URL; keep old value if the node is down.
    fetched = fetch_node_public_key(node)
    if fetched is not None:
        node.wg_public_key = fetched
    db.commit()
    db.refresh(node)
    return _node_to_admin(node)


@admin_router.delete("/{node_id}", response_model=OkResponse)
def admin_delete_node(
    node_id: str,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    # Refuse if peers still homed here — deleting would orphan their deployed configs.
    if db.query(PeerRequest).filter(PeerRequest.node_id == node.id).first() is not None:
        raise HTTPException(
            status_code=409,
            detail="Delete or move this node's peers before deleting it.",
        )
    name = node.name
    db.delete(node)
    db.commit()
    return OkResponse(ok=True, message=f"Deleted node '{name}'.")


@admin_router.post("/{node_id}/reset-token", response_model=NodeAdmin)
def admin_reset_node_token(
    node_id: str,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    """Rotate the node's agent token. The old token stops working immediately; the node service
    must be reconfigured with the new one. Returns the full NodeAdmin so the new token is visible
    once (it is not retrievable later without admin access).
    轮换节点 agent token。旧 token 立即失效;node service 须以新 token 重配。回完整 NodeAdmin,
    使新 token 可见一次(之后非 admin 无法再取得)。"""
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    node.token = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(node)
    return _node_to_admin(node)
