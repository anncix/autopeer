"""User-facing peer CRUD: ``/api/v1/peers``.

A user manages only their own peers (scoped by user_id from the session). Ownership is enforced
via owned_peer_with_node — a user can never read or mutate another user's peer by id, so the API
returns 404 (not 403) for foreign ids to avoid leaking their existence.

Reuse: create/update/delete delegate to app.peer.service, the same functions the HTML portal and
admin routes use, so validation, deploy, and teardown logic stay in one place.

用户 peer CRUD: ``/api/v1/peers``。用户仅管理自己的 peer(按 session 的 user_id 限定)。所有权经
owned_peer_with_node 强制——用户无法以 id 读写他人 peer,故对外来 id 回 404(非 403)以避免泄漏存在性。
复用: create/update/delete 委托给 app.peer.service,与 HTML portal/admin 路由同一套函数,验证、部署、
拆除逻辑只维护一处。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_api_user
from app.api.schemas import (
    OkResponse,
    PeerAdmin,
    PeerCreateRequest,
    PeerOut,
    PeerUpdateRequest,
    peer_to_dict,
)
from app.db.models import User
from app.db.session import get_db
from app.peer.queries import enabled_node_by_id, owned_peer_with_node, peers_for_user_with_nodes
from app.peer.service import create_peer, delete_peer, update_peer
from app.web.deps import settings

router = APIRouter(prefix="/api/v1/peers", tags=["peers"])


def _peer_to_out(peer, *, admin: bool) -> PeerOut | PeerAdmin:
    """Serialise a peer row, gating deploy_output/admin_note behind the admin flag. The shared
    ``peer_to_dict`` builds the common base; the schema whitelist does the actual field stripping.
    序列化 peer 行,按 admin 标志决定是否含 deploy_output/admin_note。共用 peer_to_dict 构建基础
    字段;实际字段裁剪由 schema 白名单完成。"""
    if admin:
        return PeerAdmin(
            **peer_to_dict(peer),
            deploy_output=peer.deploy_output or "",
            admin_note=peer.admin_note or "",
        )
    return PeerOut(**peer_to_dict(peer))


@router.get("", response_model=list[PeerOut])
def list_peers(user: User = Depends(require_api_user), db: Session = Depends(get_db)):
    """List the caller's own peers (newest first). Only the owner's rows — there is no admin
    "list all peers" here; admins use /api/v1/admin/peers for the global view.
    列出调用者自己的 peer(最新在前)。仅属主行——admin 的「列出全部 peer」不在此处,
    admin 用 /api/v1/admin/peers 取得全局视图。"""
    peers = peers_for_user_with_nodes(db, user.id)
    return [_peer_to_out(p, admin=user.is_admin) for p in peers]


@router.post("", response_model=PeerOut, status_code=201)
def create_peer_endpoint(
    body: PeerCreateRequest,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    """Create a peer for the caller on an enabled node. The peer's ASN is the caller's
    primary_asn — a user cannot peer as someone else. Validation errors (bad key, duplicate,
    missing address) surface as 400 with the validator's message.
    为调用者在已启用节点上创建 peer。peer 的 ASN 为调用者的 primary_asn——用户无法以他人身分对等。
    验证错误(无效公钥、重复、缺地址)以 400 回传验证器信息。"""
    node = enabled_node_by_id(db, body.node_id)
    if node is None:
        raise HTTPException(status_code=400, detail="Unknown or disabled node.")
    try:
        peer = create_peer(
            db,
            user=user,
            node=node,
            endpoint=body.endpoint,
            wg_public_key=body.wg_public_key,
            wg_mtu=body.wg_mtu,
            peer_dn42_ipv4=body.peer_dn42_ipv4,
            peer_dn42_ipv6=body.peer_dn42_ipv6,
            peer_link_address=body.peer_link_address,
            bgp_extended=body.bgp_extended,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _peer_to_out(peer, admin=user.is_admin)


@router.get("/{peer_id}", response_model=PeerOut)
def get_peer(
    peer_id: str,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    """Get one of the caller's own peers. Foreign ids return 404 (ownership check hides existence).
    获取调用者自己的某个 peer。外来 id 回 404(所有权检查隐藏存在性)。"""
    peer = owned_peer_with_node(db, user.id, peer_id)
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    return _peer_to_out(peer, admin=user.is_admin)


@router.patch("/{peer_id}", response_model=PeerOut)
def update_peer_endpoint(
    peer_id: str,
    body: PeerUpdateRequest,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    """Partially update one of the caller's own peers. Unspecified fields keep their current
    value. Setting status=disabled tears the peer down; redeploy=true re-pushes config. A node_id
    change moves the peer (orphan config on the old node is best-effort torn down).
    部分更新调用者自己的某个 peer。未指定字段保留现值。status=disabled 触发拆除;
    redeploy=true 重新推送设定。node_id 变更会迁移 peer(旧节点上的孤儿设定尽力拆除)。"""
    peer = owned_peer_with_node(db, user.id, peer_id)
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    node = peer.node
    if body.node_id is not None and body.node_id != peer.node_id:
        node = enabled_node_by_id(db, body.node_id)
        if node is None:
            raise HTTPException(status_code=400, detail="Unknown or disabled node.")
    try:
        updated = update_peer(
            db,
            peer=peer,
            node=node,
            endpoint=body.endpoint if body.endpoint is not None else peer.endpoint,
            wg_public_key=body.wg_public_key
            if body.wg_public_key is not None
            else peer.wg_public_key,
            wg_mtu=body.wg_mtu if body.wg_mtu is not None else peer.wg_mtu,
            local_link_address=body.local_link_address
            if body.local_link_address is not None
            else peer.local_link_address,
            peer_link_address=body.peer_link_address
            if body.peer_link_address is not None
            else peer.peer_link_address,
            peer_dn42_ipv4=body.peer_dn42_ipv4
            if body.peer_dn42_ipv4 is not None
            else peer.peer_dn42_ipv4,
            peer_dn42_ipv6=body.peer_dn42_ipv6
            if body.peer_dn42_ipv6 is not None
            else peer.peer_dn42_ipv6,
            bgp_extended=body.bgp_extended if body.bgp_extended is not None else peer.bgp_extended,
            status=body.status if body.status is not None else peer.status,
            redeploy=body.redeploy,
            settings=settings,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _peer_to_out(updated, admin=user.is_admin)


@router.delete("/{peer_id}", response_model=OkResponse)
def delete_peer_endpoint(
    peer_id: str,
    user: User = Depends(require_api_user),
    db: Session = Depends(get_db),
):
    """Delete one of the caller's own peers (best-effort teardown on the node). Returns 200 with
    {ok:true} — 200 (not 204) so the body can carry a human message for non-English clients.
    删除调用者自己的某个 peer(节点上尽力拆除)。回 200 {ok:true}——用 200(非 204)让 body
    能携带供非英语客户端阅读的信息。"""
    peer = owned_peer_with_node(db, user.id, peer_id)
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    delete_peer(db, peer=peer)
    return OkResponse(ok=True, message="Peer deleted and torn down.")
