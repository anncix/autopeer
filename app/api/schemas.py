"""Pydantic response models for the JSON REST API — the sensitive-data isolation layer.

Each model is an explicit whitelist of the fields an API response may carry. Sensitive fields
(``Node.token``, ``AuthChallenge.token``, ``deploy_output`` for non-admins, Telegram chat ids)
are simply absent from these models, so they can never leak through an API response even if a
future handler accidentally returns the ORM object. ``model_config = from_attributes`` lets us
build a model straight from an ORM row.

Pydantic 响应模型——敏感数据隔离层。每个模型是 API 响应可携带字段的显式白名单。敏感字段
(Node.token、AuthChallenge.token、非 admin 的 deploy_output、Telegram chat id)直接不出现在
这些模型中,故即便未来处理器不慎返回 ORM 对象也不会泄漏。from_attributes 允许直接从 ORM 行构造。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NodePublic(BaseModel):
    """What any caller (even anonymous) may see about a node: its identity and dial address.
    The node ``token`` (the WSS bearer credential) and ``system_status_json`` (raw agent output)
    are never included — only an admin sees those, via NodeAdmin.
    任意调用者(含匿名)可见的节点信息: 身份与拨号地址。node token(WSS 凭据)与
    system_status_json(原始 agent 输出)绝不包含——仅 admin 经 NodeAdmin 可见。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    location: str
    url: str
    asn: str
    dn42_ipv4: str
    dn42_ipv6: str
    wg_public_key: str
    enabled: bool


class NodeAdmin(NodePublic):
    """Admin-only node view: adds the agent token and last-seen/runtime fields. Returned only
    behind require_api_admin. The token is shown here (admins need it to reconfigure a node
    service) but is never returned to non-admin callers.
    仅 admin 可见的节点视图: 增加 agent token 与 last-seen/运行时字段。仅在 require_api_admin
    后返回。token 在此可见(admin 需它来重配 node service),但绝不返回给非 admin 调用者。"""

    token: str
    last_seen_at: datetime | None = None
    system_status_json: str = "{}"
    created_at: datetime


class PeerOut(BaseModel):
    """A peer as seen by its owner or an admin. deploy_output is omitted by default — it can
    contain node-side error text (hostnames, paths). Admins get it via PeerAdmin.
    peer 的属主/admin 视图。默认省略 deploy_output——可能含节点侧错误文本(主机名、路径)。
    admin 经 PeerAdmin 获取。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    asn: str
    node_id: str
    node_name: str | None = None
    endpoint: str
    wg_public_key: str
    wg_mtu: int
    local_link_address: str
    peer_link_address: str
    peer_dn42_ipv4: str
    peer_dn42_ipv6: str
    bgp_extended: bool
    status: str
    deploy_status: str
    created_at: datetime
    updated_at: datetime


class PeerAdmin(PeerOut):
    """Admin-only peer view: adds deploy_output (for diagnosing failed deploys) and admin_note.
    仅 admin 可见的 peer 视图: 增加 deploy_output(用于诊断失败部署)与 admin_note。"""

    deploy_output: str
    admin_note: str = ""


class IntraLinkOut(BaseModel):
    """An internal backbone link. remote_public_key is included (a peer needs it to bring up the
    other end of its own tunnel), but deploy_output is admin-only via IntraLinkAdmin.
    内部骨干链路。包含 remote_public_key(peer 需它来建立自身隧道另一端),但 deploy_output
    仅 admin 经 IntraLinkAdmin 可见。"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    node_id: str
    remote_node_id: str | None = None
    label: str
    protocol_name: str
    remote_endpoint: str
    listen_port: int
    link_local_address: str
    deploy_status: str
    created_at: datetime


class IntraLinkAdmin(IntraLinkOut):
    deploy_output: str
    deployed_at: datetime | None = None


class UserOut(BaseModel):
    """A user as seen by an admin. Telegram chat ids and ASN-identity maintainer JSON are
    omitted — they are PII / identity metadata not needed for user management. The admin flag
    and primary ASN (already public-ish via dn42 registry) are shown.
    admin 视角的用户。省略 Telegram chat id 与 ASN 身份 maintainer JSON——属 PII/身分元数据,
    管理用户无需。显示 admin 标志与 primary ASN(本就经 dn42 注册表半公开)。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    primary_asn: str
    first_email: str | None = None
    is_admin: bool
    created_at: datetime
    last_login_at: datetime | None = None


class OkResponse(BaseModel):
    """Generic {ok, message} envelope for mutating endpoints that don't return a resource."""

    ok: bool
    message: str


class PeerCreateRequest(BaseModel):
    """Body for POST /api/v1/peers. The user's own primary_asn is used (not a body field), so a
    user cannot create peers for another AS. node_id must reference an enabled node.
    POST /api/v1/peers 的请求体。使用用户自身的 primary_asn(非 body 字段),故用户无法为他 AS
    建 peer。node_id 须指向已启用节点。"""

    node_id: str
    wg_public_key: str
    endpoint: str = ""
    peer_dn42_ipv4: str = ""
    peer_dn42_ipv6: str = ""
    peer_link_address: str = ""
    wg_mtu: int | None = None
    bgp_extended: bool = True


class PeerUpdateRequest(BaseModel):
    """Body for PATCH /api/v1/peers/{id}. All fields optional (partial update). node_id lets an
    owner move their peer to another node. status toggles approved/disabled (disabled tears down).
    PATCH /api/v1/peers/{id} 的请求体。所有字段可选(部分更新)。node_id 允许属主将 peer 移至
    其他节点。status 切换 approved/disabled(disabled 触发拆除)。"""

    node_id: str | None = None
    endpoint: str | None = None
    wg_public_key: str | None = None
    wg_mtu: int | None = None
    peer_link_address: str | None = None
    peer_dn42_ipv4: str | None = None
    peer_dn42_ipv6: str | None = None
    local_link_address: str | None = None
    bgp_extended: bool | None = None
    status: str | None = None
    redeploy: bool = False


class NodeCreateRequest(BaseModel):
    """Body for POST /api/v1/admin/nodes. Admin-only. The agent token is generated server-side
    (never accepted from the client) and returned once in the response.
    POST /api/v1/admin/nodes 的请求体。仅 admin。agent token 由服务端生成(绝不接受客户端传入)
    并在响应中返回一次。"""

    name: str
    location: str = ""
    url: str
    asn: str = ""
    dn42_ipv4: str = ""
    dn42_ipv6: str = ""
    enabled: bool = True


class NodeUpdateRequest(BaseModel):
    """Body for PATCH /api/v1/admin/nodes/{id}. All fields optional. token is not editable here
    — use POST .../reset-token (it is a destructive credential rotation, not a field edit).
    PATCH /api/v1/admin/nodes/{id} 的请求体。所有字段可选。token 不可在此编辑——使用
    POST .../reset-token(它是破坏性凭据轮换,而非字段编辑)。"""

    name: str | None = None
    location: str | None = None
    url: str | None = None
    asn: str | None = None
    dn42_ipv4: str | None = None
    dn42_ipv6: str | None = None
    enabled: bool | None = None
