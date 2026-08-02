"""Admin panel: view and manage everything — overview dashboard, nodes (PoPs), peers, users, and
the looking-glass audit log. Every route requires an admin user via ``require_admin``.

The page is split per section (``/admin``, ``/admin/nodes``, ``/admin/peers``, ``/admin/users``,
``/admin/lg-log``) so each query stays small. Browser form errors surface as flash banners +
redirect; genuine not-found stays a 404 (styled by the global handler).
"""

from __future__ import annotations

import asyncio
import secrets
from typing import Any

from fastapi import APIRouter, Body, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.auth.service import unbind_telegram
from app.db.models import ASNIdentity, IntraLink, LGQuery, Node, PeerRequest, SystemSetting, TelegramBinding, User, new_uuid
from app.db.session import get_db
from app.intra.config import (
    generate_link_local_address,
    generate_listen_port,
    intra_protocol_name,
    normalize_intra_endpoint,
)
from app.intra.deploy import (
    apply_deploy_result,
    deploy_intra_link,
    remove_intra_link,
)
from app.lg.client import NodeClient
from app.node_ws import node_runtime_context
from app.peer.config import peer_protocol_name, render_operator_config
from app.peer.deploy import fetch_node_public_key
from app.peer.service import (
    create_peer,
    delete_peer,
    deploy_peer_request,
    find_peer_on_node,
    update_peer,
)
from app.peer.validation import (
    DEFAULT_WIREGUARD_MTU,
    MAX_WIREGUARD_MTU,
    MIN_WIREGUARD_MTU,
    asn_link_local_address,
    normalize_asn_number,
    normalize_node_host,
    normalize_optional_ip,
    normalize_wireguard_key,
)
from app.web.deps import Pagination, build_map_data, flash, render, require_admin, settings

router = APIRouter()

LG_LOG_PER_PAGE = 50
PEERS_PER_PAGE = 50


def _clean_node_fields(asn: str, dn42_ipv4: str, dn42_ipv6: str) -> tuple[str, str, str]:
    """Validate/normalise the optional per-node dn42 fields. Raises ValueError on bad input."""
    asn = asn.strip()
    if asn:
        asn = normalize_asn_number(asn)
    return (
        asn,
        normalize_optional_ip(dn42_ipv4, version=4),
        normalize_optional_ip(dn42_ipv6, version=6),
    )


# --------------------------------------------------------------------------- pages (GET)


@router.get("/admin", response_class=HTMLResponse)
def admin_overview(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    def count(model, *filters) -> int:
        query = db.query(func.count(model.id))
        for f in filters:
            query = query.filter(f)
        return query.scalar() or 0

    nodes_for_runtime = db.query(Node).order_by(Node.name).all()
    runtime = node_runtime_context(nodes_for_runtime)
    nodes_online = sum(1 for item in runtime.values() if item["online"])
    stats = {
        "nodes_total": count(Node),
        "nodes_enabled": count(Node, Node.enabled.is_(True)),
        "nodes_online": nodes_online,
        "peers_total": count(PeerRequest),
        "peers_deployed": count(PeerRequest, PeerRequest.deploy_status == "deployed"),
        "peers_failed": count(PeerRequest, PeerRequest.deploy_status == "failed"),
        "links_total": count(IntraLink),
        "users_total": count(User),
        "users_admin": count(User, User.is_admin.is_(True)),
        "lg_total": count(LGQuery),
    }
    failed_peers = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .filter(PeerRequest.deploy_status == "failed")
        .order_by(PeerRequest.updated_at.desc())
        .limit(10)
        .all()
    )
    recent_peers = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .order_by(PeerRequest.created_at.desc())
        .limit(6)
        .all()
    )
    recent_queries = (
        db.query(LGQuery)
        .options(joinedload(LGQuery.node), joinedload(LGQuery.user))
        .order_by(LGQuery.created_at.desc())
        .limit(8)
        .all()
    )
    nodes_health = [
        {"id": n.id, "name": n.name, "location": n.location, "runtime": runtime.get(n.id, {})}
        for n in nodes_for_runtime
    ]
    return render(
        request,
        "admin/overview.html",
        {
            "stats": stats,
            "nodes_health": nodes_health,
            "failed_peers": failed_peers,
            "recent_peers": recent_peers,
            "recent_queries": recent_queries,
            "users_total": stats["users_total"],
            "users_admin": stats["users_admin"],
        },
        user=user,
        active="admin",
    )


@router.get("/admin/map", response_class=HTMLResponse)
def admin_map(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Admin map view — now renders the shared public map template (front-facing).

    The map lives at ``/map`` for all visitors; this admin route keeps the old URL working
    and renders the same data with the admin chrome (sidebar) via ``admin/map.html``.
    Pass ?demo=1 to force all enabled nodes online with mock latency for preview/testing.
    """
    demo = request.query_params.get("demo") in ("1", "true", "yes")
    mock = request.query_params.get("mock") in ("1", "true", "yes")
    map_data = build_map_data(db, demo=demo, mock=mock)
    return render(
        request,
        "admin/map.html",
        map_data,
        user=user,
        active="map",
    )


@router.get("/admin/nodes", response_class=HTMLResponse)
def admin_nodes(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    nodes = db.query(Node).order_by(Node.name).all()
    return render(
        request,
        "admin/nodes.html",
        {"nodes": nodes, "node_runtime": node_runtime_context(nodes)},
        user=user,
        active="admin",
    )


@router.get("/admin/nodes/new", response_class=HTMLResponse)
def admin_nodes_new(
    request: Request,
    user: User = Depends(require_admin),
) -> HTMLResponse:
    return render(
        request,
        "admin/nodes_new.html",
        {},
        user=user,
        active="admin",
    )


@router.get("/admin/nodes/{node_id}/intra-links/new", response_class=HTMLResponse)
def admin_intra_links_new(
    node_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    remote_node_choices = _intra_remote_choices(db, node_id)
    return render(
        request,
        "admin/intra_links_new.html",
        {"node": node, "remote_node_choices": remote_node_choices},
        user=user,
        active="admin",
    )


@router.get("/admin/nodes/{node_id}/edit", response_class=HTMLResponse)
def admin_node_edit(
    node_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    import logging
    import time

    _log = logging.getLogger("dn42.autopeer.admin")
    _log.setLevel(logging.DEBUG)
    _handler = logging.StreamHandler()
    _handler.setLevel(logging.DEBUG)
    if not _log.handlers:
        _log.addHandler(_handler)

    _t0 = time.perf_counter()
    _log.info("[node_edit] === START node edit route === node_id=%s", node_id)
    _log.debug("[node_edit] user=%s admin=%s", user.primary_asn, user.is_admin)

    _t1 = time.perf_counter()
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        _log.warning("[node_edit] node NOT FOUND node_id=%s", node_id)
        raise HTTPException(status_code=404, detail="Node not found")
    _log.info("[node_edit] node loaded name=%s location=%s asn=%s enabled=%s (%.1fms)",
              node.name, node.location, node.asn, node.enabled, (_t1 - _t0) * 1000)

    _t2 = time.perf_counter()
    runtime = node_runtime_context([node])[node.id]
    _log.info("[node_edit] runtime online=%s last_seen=%s system_keys=%s (%.1fms)",
              runtime.get("online"), runtime.get("last_seen_at"),
              list(runtime.get("system", {}).keys()), (_t2 - _t1) * 1000)

    _t3 = time.perf_counter()
    peers = (
        db.query(PeerRequest)
        .filter(PeerRequest.node_id == node.id)
        .order_by(PeerRequest.created_at.desc())
        .all()
    )
    peer_rows = [
        {"peer": p, "protocol_name": peer_protocol_name(p, node)} for p in peers
    ]
    _log.info("[node_edit] peers queried count=%d (%.1fms)", len(peers), (_t3 - _t2) * 1000)
    if peers:
        _log.debug("[node_edit] peer details: %s",
                   [(p.id[:8], p.asn, p.status, p.deploy_status) for p in peers])

    _t4 = time.perf_counter()
    intra_links = (
        db.query(IntraLink)
        .filter(IntraLink.node_id == node.id)
        .order_by(IntraLink.created_at.desc())
        .all()
    )
    _log.info("[node_edit] intra_links queried count=%d (%.1fms)", len(intra_links), (_t4 - _t3) * 1000)
    if intra_links:
        _log.debug("[node_edit] intra_link details: %s",
                   [(l.protocol_name, l.label, l.deploy_status, l.remote_endpoint) for l in intra_links])
        for link in intra_links:
            _log.debug("[node_edit]   link=%s remote_node=%s port=%d lla=%s deployed_at=%s output_len=%d",
                       link.protocol_name,
                       link.remote_node_id or "manual",
                       link.listen_port,
                       link.link_local_address,
                       link.deployed_at,
                       len(link.deploy_output or ""))

    _t5 = time.perf_counter()
    remote_node_choices = _intra_remote_choices(db, node.id)
    _log.info("[node_edit] remote_node_choices count=%d (%.1fms)", len(remote_node_choices), (_t5 - _t4) * 1000)

    _ctx = {
        "node": node,
        "runtime": runtime,
        "peer_rows": peer_rows,
        "peer_count": len(peer_rows),
        "intra_links": intra_links,
        "intra_link_count": len(intra_links),
        "remote_node_choices": remote_node_choices,
    }
    _log.info("[node_edit] context prepared peer_count=%d intra_link_count=%d remote_choices=%d",
              _ctx["peer_count"], _ctx["intra_link_count"], len(_ctx["remote_node_choices"]))

    _t6 = time.perf_counter()
    _log.info("[node_edit] === RENDERING template admin/node_edit.html === (%.1fms total so far)", (_t6 - _t0) * 1000)
    result = render(
        request,
        "admin/node_edit.html",
        _ctx,
        user=user,
        active="admin",
    )
    _t7 = time.perf_counter()
    _log.info("[node_edit] === RENDER COMPLETE === rendered_bytes=%d render_time=%.1fms total=%.1fms",
              len(result.body), (_t7 - _t6) * 1000, (_t7 - _t0) * 1000)

    return result


def _intra_remote_choices(db: Session, exclude_node_id: str) -> list[Node]:
    """Other enabled nodes that can be the remote (B) end of an intra link from this node.

    Excludes nodes that already have an intra link with the current node (in either direction)
    to prevent duplicate creation.
    """
    existing_remote_ids = (
        db.query(IntraLink.remote_node_id)
        .filter(IntraLink.node_id == exclude_node_id, IntraLink.remote_node_id.isnot(None))
        .all()
    )
    existing_local_ids = (
        db.query(IntraLink.node_id)
        .filter(IntraLink.remote_node_id == exclude_node_id)
        .all()
    )
    exclude_ids = {exclude_node_id}
    exclude_ids.update(rid for (rid,) in existing_remote_ids)
    exclude_ids.update(nid for (nid,) in existing_local_ids)

    return (
        db.query(Node)
        .filter(Node.id.notin_(exclude_ids))
        .order_by(Node.name)
        .all()
    )


@router.get("/admin/peers", response_class=HTMLResponse)
def admin_peers(
    request: Request,
    page: int = 1,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    nodes = db.query(Node).order_by(Node.name).all()
    try:
        default_local_link_address = asn_link_local_address(settings.local_asn)
    except ValueError:
        default_local_link_address = ""
    total = db.query(func.count(PeerRequest.id)).scalar() or 0
    pg = Pagination(page=page, per_page=PEERS_PER_PAGE, total=total)
    peers = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .order_by(PeerRequest.created_at.desc())
        .limit(pg.per_page)
        .offset(pg.offset)
        .all()
    )
    return render(
        request,
        "admin/peers.html",
        {
            "nodes": nodes,
            "peers": peers,
            "pg": pg,
            "default_local_link_address": default_local_link_address,
            "default_wireguard_mtu": DEFAULT_WIREGUARD_MTU,
            "wireguard_mtu_min": MIN_WIREGUARD_MTU,
            "wireguard_mtu_max": MAX_WIREGUARD_MTU,
        },
        user=user,
        active="admin",
    )


@router.get("/admin/peers/new", response_class=HTMLResponse)
def admin_peers_new(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    nodes = db.query(Node).order_by(Node.name).all()
    try:
        default_local_link_address = asn_link_local_address(settings.local_asn)
    except ValueError:
        default_local_link_address = ""
    return render(
        request,
        "admin/peers_new.html",
        {
            "nodes": nodes,
            "default_local_link_address": default_local_link_address,
            "default_wireguard_mtu": DEFAULT_WIREGUARD_MTU,
            "wireguard_mtu_min": MIN_WIREGUARD_MTU,
            "wireguard_mtu_max": MAX_WIREGUARD_MTU,
        },
        user=user,
        active="admin",
    )


@router.get("/admin/peers/{peer_id}/edit", response_class=HTMLResponse)
def admin_peer_edit(
    peer_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    peer = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .filter(PeerRequest.id == peer_id)
        .one_or_none()
    )
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    nodes = db.query(Node).order_by(Node.name).all()
    return render(
        request,
        "admin/peer_edit.html",
        {
            "peer": peer,
            "nodes": nodes,
            "default_wireguard_mtu": DEFAULT_WIREGUARD_MTU,
            "wireguard_mtu_min": MIN_WIREGUARD_MTU,
            "wireguard_mtu_max": MAX_WIREGUARD_MTU,
        },
        user=user,
        active="admin",
    )


@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    # selectinload bindings + one grouped peer-count query → no per-user lazy loads.
    users = (
        db.query(User)
        .options(selectinload(User.telegram_bindings))
        .order_by(User.primary_asn)
        .all()
    )
    peer_counts = dict(
        db.query(PeerRequest.user_id, func.count(PeerRequest.id))
        .group_by(PeerRequest.user_id)
        .all()
    )
    return render(
        request,
        "admin/users.html",
        {"users": users, "peer_counts": peer_counts},
        user=user,
        active="admin",
    )


@router.get("/admin/lg-log", response_class=HTMLResponse)
def admin_lg_log(
    request: Request,
    page: int = 1,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    total = db.query(func.count(LGQuery.id)).scalar() or 0
    pg = Pagination(page=page, per_page=LG_LOG_PER_PAGE, total=total)
    queries = (
        db.query(LGQuery)
        .options(joinedload(LGQuery.node), joinedload(LGQuery.user))
        .order_by(LGQuery.created_at.desc())
        .limit(pg.per_page)
        .offset(pg.offset)
        .all()
    )
    return render(
        request,
        "admin/lg_log.html",
        {"queries": queries, "pg": pg},
        user=user,
        active="admin",
    )


# --------------------------------------------------------------------------- settings


@router.get("/admin/network-search", response_class=HTMLResponse)
def admin_network_search(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    nodes = db.query(Node).filter(Node.enabled.is_(True)).order_by(Node.name).all()
    peers_total = db.query(func.count(PeerRequest.id)).scalar() or 0
    links_total = db.query(func.count(IntraLink.id)).scalar() or 0
    recent_queries = (
        db.query(LGQuery)
        .options(joinedload(LGQuery.node))
        .order_by(LGQuery.created_at.desc())
        .limit(10)
        .all()
    )
    return render(
        request,
        "admin/network_search.html",
        {
            "nodes": nodes,
            "peers_total": peers_total,
            "links_total": links_total,
            "recent_queries": recent_queries,
        },
        user=user,
        active="admin",
    )


@router.post("/admin/network-search")
async def admin_network_search_post(
    request: Request,
    node_id: str = Form(""),
    query_type: str = Form(...),
    target: str = Form(""),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    from app.lg.client import NodeClient
    
    try:
        client = NodeClient()
        nodes_to_query = []
        
        if node_id:
            node = db.query(Node).filter(Node.id == node_id, Node.enabled.is_(True)).one_or_none()
            if node is None:
                return JSONResponse({"ok": False, "error": "Node not found or disabled"}, status_code=404)
            nodes_to_query = [node]
        else:
            nodes_to_query = db.query(Node).filter(Node.enabled.is_(True)).all()
        
        results = []
        for node in nodes_to_query:
            try:
                if query_type == "ospf_neighbors":
                    result = await client.ospf_neighbors(node)
                elif query_type == "peer_status":
                    result = await client.peer_status(node, target)
                elif query_type == "birdc":
                    result = await client.query(node, "birdc", target)
                elif query_type in ("bird_route", "bird_protocols", "bgp_summary", "ip_route"):
                    result = await client.query(node, query_type, target)
                else:
                    return JSONResponse({"ok": False, "error": f"Unknown query type: {query_type}"}, status_code=400)
                
                # Log the query
                lg_query = LGQuery(
                    user_id=user.id,
                    node_id=node.id,
                    query_type=query_type,
                    target=target,
                    ok=result.get("ok", True),
                    result=str(result),
                )
                db.add(lg_query)
                db.commit()
                
                # Parse output based on query type
                output = result.get("output", result.get("result", ""))
                parsed_data = None
                
                if query_type == "bird_protocols":
                    from app.lg.summary import parse_bird_protocols_all, parse_bird_protocols_list
                    if target:
                        # Specific protocol: show detailed view
                        parsed_data = parse_bird_protocols_all(output)
                        parsed_data["mode"] = "detail"
                    else:
                        # All protocols: show list view
                        parsed_data = {
                            "mode": "list",
                            "protocols": parse_bird_protocols_list(output)
                        }
                
                results.append({
                    "node_id": node.id,
                    "node_name": node.name,
                    "query_type": query_type,
                    "ok": result.get("ok", True),
                    "output": output,
                    "error": result.get("error", ""),
                    "parsed": parsed_data,
                })
            except Exception as exc:
                results.append({
                    "node_id": node.id,
                    "node_name": node.name,
                    "query_type": query_type,
                    "ok": False,
                    "output": "",
                    "error": str(exc),
                })
        
        return JSONResponse({"ok": True, "results": results})
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=500)


@router.get("/admin/settings", response_class=HTMLResponse)
def admin_settings(
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    from app.settings.service import ensure_default_settings, get_all_settings
    ensure_default_settings(db)
    settings_list = get_all_settings(db)
    settings_map = {s["key"]: s for s in settings_list}
    return render(
        request,
        "admin/settings.html",
        {"settings_map": settings_map},
        user=user,
        active="admin",
    )


@router.post("/admin/settings/save")
def admin_settings_save(
    request: Request,
    lla_base_network: str = Form(""),
    lla_subnet_prefix: str = Form(""),
    intra_port_base: str = Form(""),
    intra_port_max: str = Form(""),
    default_asn: str = Form(""),
    asn_range_start: str = Form(""),
    asn_range_end: str = Form(""),
    owned_networks_v4: str = Form(""),
    owned_networks_v6: str = Form(""),
    peer_wg_mtu: str = Form(""),
    peer_bgp_extended: str = Form(""),
    lg_rate_limit: str = Form(""),
    lg_rate_window: str = Form(""),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    from app.settings.service import update_settings_batch
    updates = {
        "lla_base_network": lla_base_network,
        "lla_subnet_prefix": lla_subnet_prefix,
        "intra_port_base": intra_port_base,
        "intra_port_max": intra_port_max,
        "default_asn": default_asn,
        "asn_range_start": asn_range_start,
        "asn_range_end": asn_range_end,
        "owned_networks_v4": owned_networks_v4,
        "owned_networks_v6": owned_networks_v6,
        "peer_wg_mtu": peer_wg_mtu,
        "peer_bgp_extended": peer_bgp_extended,
        "lg_rate_limit": lg_rate_limit,
        "lg_rate_window": lg_rate_window,
    }
    try:
        update_settings_batch(db, updates)
        flash(request, "Settings saved successfully.", "success")
    except Exception as exc:
        flash(request, f"Error saving settings: {exc}", "error")
    return RedirectResponse("/admin/settings", status_code=303)


# --------------------------------------------------------------------------- nodes (POST)


@router.post("/admin/nodes")
def admin_create_node(
    request: Request,
    name: str = Form(...),
    location: str = Form(""),
    url: str = Form(...),
    asn: str = Form(""),
    dn42_ipv4: str = Form(""),
    dn42_ipv6: str = Form(""),
    enabled: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    name = name.strip()
    if not name:
        flash(request, "Node name is required.", "error")
        return RedirectResponse("/admin/nodes", status_code=303)
    try:
        url = normalize_node_host(url)
        asn, dn42_ipv4, dn42_ipv6 = _clean_node_fields(asn, dn42_ipv4, dn42_ipv6)
    except ValueError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/admin/nodes", status_code=303)
    if db.query(Node).filter(Node.name == name).one_or_none() is not None:
        flash(request, f"A node named '{name}' already exists.", "error")
        return RedirectResponse("/admin/nodes", status_code=303)
    node = Node(
        name=name,
        location=location.strip(),
        url=url,
        asn=asn,
        dn42_ipv4=dn42_ipv4,
        dn42_ipv6=dn42_ipv6,
        token=secrets.token_urlsafe(32),
        enabled=enabled == "on",
    )
    db.add(node)
    db.commit()
    flash(request, f"Node '{name}' created.", "success")
    return RedirectResponse("/admin/nodes", status_code=303)


@router.post("/admin/nodes/{node_id}/update")
def admin_update_node(
    node_id: str,
    request: Request,
    name: str = Form(...),
    location: str = Form(""),
    url: str = Form(...),
    asn: str = Form(""),
    dn42_ipv4: str = Form(""),
    dn42_ipv6: str = Form(""),
    enabled: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    edit_url = f"/admin/nodes/{node_id}/edit"
    name = name.strip()
    if not name:
        flash(request, "Node name is required.", "error")
        return RedirectResponse(edit_url, status_code=303)
    try:
        url = normalize_node_host(url)
        asn, dn42_ipv4, dn42_ipv6 = _clean_node_fields(asn, dn42_ipv4, dn42_ipv6)
    except ValueError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse(edit_url, status_code=303)
    existing = db.query(Node).filter(Node.name == name, Node.id != node.id).one_or_none()
    if existing is not None:
        flash(request, f"A node named '{name}' already exists.", "error")
        return RedirectResponse(edit_url, status_code=303)
    node.name = name
    node.location = location.strip()
    node.url = url
    node.asn = asn
    node.dn42_ipv4 = dn42_ipv4
    node.dn42_ipv6 = dn42_ipv6
    node.enabled = enabled == "on"
    # Re-sync the public key from the (maybe changed) URL; keep the old value if the node is down.
    fetched = fetch_node_public_key(node)
    if fetched is not None:
        node.wg_public_key = fetched
    db.commit()
    flash(request, f"Node '{name}' saved.", "success")
    return RedirectResponse(edit_url, status_code=303)


@router.post("/admin/nodes/{node_id}/refresh-pubkey")
def admin_refresh_node_pubkey(
    node_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    key = fetch_node_public_key(node)
    if key is None:
        flash(
            request,
            "Could not fetch a WireGuard public key from the node. Check WSS connectivity, "
            "node name/token, and that wireguard_public_key is set in the node config, "
            "then retry.",
            "error",
        )
        return RedirectResponse(f"/admin/nodes/{node_id}/edit", status_code=303)
    node.wg_public_key = key
    db.commit()
    flash(request, f"Refreshed WireGuard public key for '{node.name}'.", "success")
    return RedirectResponse(f"/admin/nodes/{node_id}/edit", status_code=303)


@router.post("/admin/nodes/{node_id}/reset-token")
def admin_reset_node_token(
    node_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    node.token = secrets.token_urlsafe(32)
    db.commit()
    flash(request, f"Issued a new API token for '{node.name}'.", "success")
    return RedirectResponse(f"/admin/nodes/{node_id}/edit", status_code=303)


@router.post("/admin/nodes/{node_id}/delete")
def admin_delete_node(
    node_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    if db.query(PeerRequest).filter(PeerRequest.node_id == node.id).first() is not None:
        flash(request, "Delete or move this node's peers before deleting it.", "error")
        return RedirectResponse("/admin/nodes", status_code=303)
    name = node.name
    db.delete(node)
    db.commit()
    flash(request, f"Deleted node '{name}'.", "success")
    return RedirectResponse("/admin/nodes", status_code=303)


# --------------------------------------------------------------------------- peers (POST)


@router.post("/admin/peers")
def admin_create_peer(
    request: Request,
    asn: str = Form(...),
    node_id: str = Form(...),
    endpoint: str = Form(""),
    wg_public_key: str = Form(...),
    wg_mtu: str | None = Form(None),
    local_link_address: str = Form(...),
    peer_link_address: str = Form(""),
    peer_dn42_ipv4: str = Form(""),
    peer_dn42_ipv6: str = Form(""),
    bgp_extended: str | None = Form(None),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    try:
        asn_number = normalize_asn_number(asn)
    except ValueError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/admin/peers", status_code=303)
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        flash(request, "Unknown node.", "error")
        return RedirectResponse("/admin/peers", status_code=303)
    duplicate = find_peer_on_node(db, node.id, asn_number)
    if duplicate is not None:
        flash(request, f"AS{asn_number} already has a peer on {node.name}.", "error")
        return RedirectResponse("/admin/peers", status_code=303)
    peer_user = db.query(User).filter(User.primary_asn == asn_number).one_or_none()
    if peer_user is None:
        try:
            is_admin = asn_number == normalize_asn_number(settings.local_asn)
        except ValueError:
            is_admin = False
        peer_user = User(primary_asn=asn_number, is_admin=is_admin)
        db.add(peer_user)
        db.flush()
        db.add(ASNIdentity(user_id=peer_user.id, asn=asn_number, authtype="admin-manual"))
    try:
        peer = create_peer(
            db,
            user=peer_user,
            node=node,
            endpoint=endpoint,
            wg_public_key=wg_public_key,
            wg_mtu=wg_mtu,
            local_link_address=local_link_address,
            peer_link_address=peer_link_address,
            peer_dn42_ipv4=peer_dn42_ipv4,
            peer_dn42_ipv6=peer_dn42_ipv6,
            bgp_extended=bgp_extended,
            settings=settings,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse("/admin/peers", status_code=303)
    if peer.deploy_status == "deployed":
        flash(request, f"Peer for AS{asn_number} on {node.name} created and deployed.", "success")
    else:
        flash(
            request,
            f"Peer for AS{asn_number} created, deploy failed: {peer.deploy_output[:200]}",
            "error",
        )
    return RedirectResponse("/admin/peers", status_code=303)


@router.post("/admin/peers/{peer_id}/update")
def admin_update_peer(
    peer_id: str,
    request: Request,
    node_id: str = Form(...),
    endpoint: str = Form(""),
    wg_public_key: str = Form(...),
    wg_mtu: str | None = Form(None),
    local_link_address: str = Form(...),
    peer_link_address: str = Form(""),
    peer_dn42_ipv4: str = Form(""),
    peer_dn42_ipv6: str = Form(""),
    bgp_extended: str | None = Form(None),
    status: str = Form("approved"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    peer = db.query(PeerRequest).filter(PeerRequest.id == peer_id).one_or_none()
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    edit_url = f"/admin/peers/{peer_id}/edit"
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        flash(request, "Unknown node.", "error")
        return RedirectResponse(edit_url, status_code=303)
    try:
        peer = update_peer(
            db,
            peer=peer,
            node=node,
            endpoint=endpoint,
            wg_public_key=wg_public_key,
            wg_mtu=wg_mtu,
            local_link_address=local_link_address,
            peer_link_address=peer_link_address,
            peer_dn42_ipv4=peer_dn42_ipv4,
            peer_dn42_ipv6=peer_dn42_ipv6,
            bgp_extended=bgp_extended,
            status=status,
            settings=settings,
            redeploy=False,
        )
    except ValueError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse(edit_url, status_code=303)
    flash(request, "Peer saved.", "success")
    return RedirectResponse(edit_url, status_code=303)


@router.post("/admin/peers/{peer_id}/redeploy")
def admin_redeploy_peer(
    peer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    peer = db.query(PeerRequest).filter(PeerRequest.id == peer_id).one_or_none()
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    edit_url = f"/admin/peers/{peer_id}/edit"
    if peer.status != "approved":
        flash(request, "Only approved peers can be deployed.", "error")
        return RedirectResponse(edit_url, status_code=303)
    peer = deploy_peer_request(db, peer, settings)
    if peer.deploy_status == "deployed":
        flash(request, "Peer redeployed.", "success")
    else:
        flash(request, f"Peer deploy failed: {peer.deploy_output[:200]}", "error")
    return RedirectResponse(edit_url, status_code=303)


@router.post("/admin/peers/{peer_id}/delete")
def admin_delete_peer(
    peer_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    peer = db.query(PeerRequest).filter(PeerRequest.id == peer_id).one_or_none()
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    delete_peer(db, peer=peer)
    flash(request, "Deleted peer.", "success")
    return RedirectResponse("/admin/peers", status_code=303)


@router.get("/admin/peers/{peer_id}/config", response_class=HTMLResponse)
def admin_peer_config(
    peer_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    peer = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .filter(PeerRequest.id == peer_id)
        .one_or_none()
    )
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    return render(
        request,
        "config.html",
        {
            "title": f"Operator config for AS{peer.asn}",
            "subtitle": f"WireGuard + BIRD snippets for AS{peer.asn} on {peer.node.name}.",
            "config": render_operator_config(peer, peer.node, settings.local_asn or "<our-asn>"),
            "back_url": f"/admin/peers/{peer.id}/edit",
        },
        user=user,
        active="admin",
    )


@router.get("/admin/peers/{peer_id}/status", response_class=HTMLResponse)
async def admin_peer_status(
    peer_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Show one peer's full live WireGuard + BIRD status, fetched from its node node service.

    The complete, unmodified command output — the portal/bot views condense it to key info. A dead
    or disabled node renders a notice instead of failing the page.
    """
    peer = (
        db.query(PeerRequest)
        .options(joinedload(PeerRequest.node))
        .filter(PeerRequest.id == peer_id)
        .one_or_none()
    )
    if peer is None:
        raise HTTPException(status_code=404, detail="Peer not found")
    node = peer.node
    protocol_name = peer_protocol_name(peer, node)
    bird = wg = ""
    error = None
    try:
        result = await NodeClient().peer_status(node, protocol_name)
        bird = str(result.get("output", "")).strip()
        wg = str(result.get("wireguard", "")).strip()
    except Exception as exc:  # noqa: BLE001 - surface node errors as a notice, never a 500
        error = f"Could not fetch live status from {node.name}: {exc}"
    return render(
        request,
        "admin/peer_status.html",
        {
            "peer": peer,
            "node": node,
            "protocol_name": protocol_name,
            "bird": bird,
            "wg": wg,
            "error": error,
        },
        user=user,
        active="admin",
    )


# ------------------------------------------------------------------ intra links (GET)


@router.get("/admin/nodes/{node_id}/ospf", response_class=HTMLResponse)
async def admin_node_ospf(
    node_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Fetch and display OSPF neighbors, OSPF area config files, and dummy interfaces for a node.

    All three are read from the node agent and rendered verbatim. A dead/disabled node shows a
    notice instead of failing the page. Used by the OSPF tab on the node detail page.
    """
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    ospf_neighbors = ospf_configs = dummy = ""
    ospf_files: list[dict[str, str]] = []
    error = None
    try:
        client = NodeClient()
        neighbors_resp, configs_resp, dummy_resp = await asyncio.gather(
            client.ospf_neighbors(node),
            client.ospf_configs(node),
            client.dummy_interfaces(node),
            return_exceptions=True,
        )
        ospf_neighbors = _extract_output(neighbors_resp)
        if isinstance(configs_resp, dict):
            ospf_files = list(configs_resp.get("files") or [])
            if not configs_resp.get("ok"):
                err = str(configs_resp.get("error", "")).strip()
                if err:
                    error = err
        dummy = _extract_output(dummy_resp)
    except Exception as exc:  # noqa: BLE001
        error = f"Could not fetch OSPF status from {node.name}: {exc}"
    return render(
        request,
        "admin/node_ospf.html",
        {
            "node": node,
            "ospf_neighbors": ospf_neighbors,
            "ospf_files": ospf_files,
            "dummy": dummy,
            "error": error,
        },
        user=user,
        active="admin",
    )


@router.get("/admin/nodes/{node_id}/ospf/json")
async def admin_node_ospf_json(
    node_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Fetch OSPF neighbors JSON for inline tab rendering."""
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    ospf_neighbors = ""
    error = None
    try:
        client = NodeClient()
        neighbors_resp = await client.ospf_neighbors(node)
        ospf_neighbors = _extract_output(neighbors_resp)
    except Exception as exc:  # noqa: BLE001
        error = str(exc)
    return JSONResponse({
        "ok": error is None,
        "neighbors": ospf_neighbors,
        "error": error,
    })


@router.get("/admin/nodes/{node_id}/bird-base/json")
def admin_node_bird_base_json(
    node_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Fetch BIRD base config JSON for inline tab rendering."""
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    try:
        from app.peer.bird_base import render_dn42_bird_base, render_roa_refresh_script
        local_asn = node.asn or settings.asn
        bird_base = render_dn42_bird_base(local_asn)
        roa_script = render_roa_refresh_script(local_asn)
        return JSONResponse({
            "ok": True,
            "bird_base": bird_base,
            "roa_script": roa_script,
        })
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)})


@router.get("/admin/nodes/{node_id}/flap/json")
async def admin_node_flap_json(
    node_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Fetch BGP flap events JSON for inline tab rendering."""
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    try:
        client = NodeClient()
        check_resp, events_resp = await asyncio.gather(
            client.flap_check(node),
            client.flap_events(node),
            return_exceptions=True,
        )
        events = []
        current_states = {}
        if isinstance(events_resp, dict):
            events = list(events_resp.get("events") or [])
            current_states = dict(events_resp.get("current_states") or {})
        error = None
        if isinstance(check_resp, dict):
            err = str(check_resp.get("error", "")).strip()
            if err:
                error = err
        return JSONResponse({
            "ok": error is None,
            "events": events,
            "current_states": current_states,
            "error": error,
        })
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"ok": False, "error": str(exc)})


def _extract_output(resp: object) -> str:
    if isinstance(resp, dict):
        return str(resp.get("output", "")).strip()
    return ""


@router.get("/admin/nodes/{node_id}/flap", response_class=HTMLResponse)
async def admin_node_flap(
    node_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Display BGP flap detection results for a node.

    Triggers a ``flap.check`` (polls birdc, records transitions into the agent's ring buffer) then
    reads ``flap.events`` for the full buffered history. Also surfaces the current BGP protocol
    states from the check response so the UI can show live state alongside the timeline. Opening
    this page IS the poll — there is no background poller, so the detection granularity equals how
    often an operator visits (or a future scheduled task invokes flap.check).
    """
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    events: list[dict[str, Any]] = []
    states: dict[str, str] = {}
    event_count = 0
    new_count = 0
    error = None
    try:
        client = NodeClient()
        check_resp, hist_resp = await asyncio.gather(
            client.flap_check(node),
            client.flap_events(node),
            return_exceptions=True,
        )
        if isinstance(check_resp, dict) and check_resp.get("ok"):
            events = list(check_resp.get("new_events") or [])
            new_count = len(events)
            states = dict(check_resp.get("states") or {})
            event_count = int(check_resp.get("event_count") or 0)
        elif isinstance(check_resp, dict):
            error = str(check_resp.get("error", "")).strip() or "flap.check failed"
        # Merge: show full history (newest last) but flag the new ones from this poll.
        # 合併:顯示完整歷史(最新在最後),但標記本次輪詢的新事件。
        if isinstance(hist_resp, dict) and hist_resp.get("ok"):
            hist = list(hist_resp.get("events") or [])
            # Mark the just-observed transitions: the new_events from check_resp describe the same
            # transitions that were appended to the agent's history on this poll, but they come back
            # as separate JSON responses (so id() comparison would never match). Match by content
            # (protocol + from + to + time) instead.
            # 標記剛觀察到的轉換:check_resp 的 new_events 描述本次輪詢附加進 agent 歷史的相同轉換,
            # 但它們經由不同 JSON 回應返回(id() 比對永遠不會相符)。改以內容
            # (protocol + from + to + time) 比對。
            new_keys = {
                (e.get("protocol"), e.get("from"), e.get("to"), e.get("time"))
                for e in events
            }
            for ev in hist:
                key = (ev.get("protocol"), ev.get("from"), ev.get("to"), ev.get("time"))
                ev["is_new"] = key in new_keys
            events = hist
        else:
            for ev in events:
                ev["is_new"] = True
    except Exception as exc:  # noqa: BLE001
        error = f"Could not fetch flap status from {node.name}: {exc}"
    # Reverse for display: newest first.
    # 反轉供顯示:最新在最前。
    events = list(reversed(events))
    return render(
        request,
        "admin/node_flap.html",
        {
            "node": node,
            "events": events,
            "states": states,
            "event_count": event_count,
            "new_count": new_count,
            "error": error,
        },
        user=user,
        active="admin",
    )


@router.get("/admin/nodes/{node_id}/bird-base", response_class=HTMLResponse)
def admin_node_bird_base(
    node_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Generate and display the DN42 BIRD2 base config (ROA + filters + dnpeers template).

    The operator copies the output into ``/etc/bird/peers/00_dn42_base.conf`` (or includes it from
    their bird.conf). Per-peer snippets generated by AutoPeer inherit ``from dnpeers``, so this base
    config supplies the import/export filters and ROA validation they assume. Also generates the
    ROA refresh cron script. The ASN is the node's ASN, falling back to LOCAL_ASN.
    """
    from app.peer.bird_base import render_dn42_bird_base, render_roa_refresh_script

    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    local_asn = (node.asn or settings.local_asn or "").strip()
    if not local_asn:
        local_asn = "4242420000"  # placeholder so generation still produces valid output to preview
    bird_base = render_dn42_bird_base(local_asn)
    roa_script = render_roa_refresh_script()
    return render(
        request,
        "admin/node_bird_base.html",
        {
            "node": node,
            "local_asn": local_asn,
            "bird_base": bird_base,
            "roa_script": roa_script,
        },
        user=user,
        active="admin",
    )


# ------------------------------------------------------------------ intra links (POST)


def _provision_intra_link(
    db: Session,
    settings: Any,
    local_node: Node,
    remote_node_id: str | None,
    remote_public_key: str,
    remote_endpoint: str,
    label: str,
    deploy: bool,
    listen_port: int | None = None,
) -> tuple[IntraLink | None, bool, str]:
    """Create (and optionally deploy) one intra link on ``local_node``.

    Returns ``(link, ok, message)``. ``link`` is None and ``ok`` False on validation failure. The
    caller is responsible for flashing the message. This is shared between the forward and reverse
    directions of bi-directional link creation so both sides get identical validation + deploy logic.
    在 local_node 上建立(並可選部署)一條內網鏈路。回傳 (link, ok, message)。驗證失敗時 link 為
    None 且 ok 為 False;訊息由呼叫者 flash。雙向鏈路建立的正向與反向共用此函式,確保兩側驗證與
    部署邏輯一致。
    """
    # Validate the WireGuard public key (required) and endpoint (optional, bare host or host:port).
    try:
        remote_public_key = normalize_wireguard_key(remote_public_key)
    except ValueError as exc:
        return None, False, f"{exc} Select a remote node with a registered public key, or paste one manually."
    try:
        remote_endpoint = normalize_intra_endpoint(remote_endpoint)
    except ValueError as exc:
        return None, False, str(exc)

    # Generate a stable id so the protocol name (ibgp_<4-hex>) is derived from it. Retry on the rare
    # chance of a protocol-name collision.
    for _ in range(3):
        link_id = new_uuid()
        protocol_name = intra_protocol_name(link_id)
        if db.query(IntraLink).filter(IntraLink.protocol_name == protocol_name).one_or_none() is None:
            break
    else:
        return None, False, "Could not allocate a unique intra link name. Please retry."

    # Resolve listen port: use the provided one if valid and available, else auto-generate.
    if listen_port is not None and 41400 <= listen_port <= 44399:
        existing = db.query(IntraLink).filter(IntraLink.listen_port == listen_port).one_or_none()
        if existing is not None:
            return None, False, f"Listen port {listen_port} is already in use. Please retry."
    else:
        for _ in range(10):
            listen_port = generate_listen_port()
            if db.query(IntraLink).filter(IntraLink.listen_port == listen_port).one_or_none() is None:
                break
        else:
            return None, False, "Could not allocate a unique listen port. Please retry."

    link = IntraLink(
        id=link_id,
        node_id=local_node.id,
        remote_node_id=remote_node_id or None,
        label=label[:64],
        protocol_name=protocol_name,
        remote_public_key=remote_public_key,
        remote_endpoint=remote_endpoint,
        listen_port=listen_port,
        link_local_address=generate_link_local_address(),
    )
    db.add(link)
    db.commit()
    db.refresh(link)

    if not deploy:
        return link, True, f"Intra link {link.protocol_name} created (not deployed)."

    try:
        result = deploy_intra_link(link, local_node, settings)
        apply_deploy_result(link, result)
        db.commit()
        if result.get("ok"):
            return link, True, f"Intra link {link.protocol_name} deployed."
        return link, False, f"Deploy failed: {result.get('output', 'unknown error')}"
    except Exception as exc:  # noqa: BLE001 - node unreachable / rejected; record and surface
        link.deploy_status = "failed"
        link.deploy_output = str(exc)
        db.commit()
        return link, False, f"Deploy failed: {exc}"


def _serialize_intra_link(link: IntraLink) -> dict[str, Any]:
    """Serialise an IntraLink row for the JSON list endpoint (consumed by the progressive-enhancement
    JS that re-renders the links table without a full page reload).
    將 IntraLink 序列化供 JSON 列表端點使用(由漸進增強 JS 消費,無需整頁重載即可重渲染鏈路表)。"""
    return {
        "id": link.id,
        "protocol_name": link.protocol_name,
        "label": link.label or "",
        "remote_name": link.remote_node.name if link.remote_node else "",
        "remote_endpoint": link.remote_endpoint or "",
        "listen_port": link.listen_port,
        "link_local_address": link.link_local_address,
        "deploy_status": link.deploy_status,
    }


@router.get("/admin/nodes/{node_id}/intra-links/json")
def admin_intra_links_json(
    node_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return the node's intra links as JSON for the progressive-enhancement list refresher.

    The links tab's table is re-rendered client-side from this after a create/deploy/delete via
    fetch, avoiding a full page reload. Joined-loads remote_node so there is no N+1.
    """
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    links = (
        db.query(IntraLink)
        .options(joinedload(IntraLink.remote_node))
        .filter(IntraLink.node_id == node.id)
        .order_by(IntraLink.created_at.desc())
        .all()
    )
    return JSONResponse({"links": [_serialize_intra_link(l) for l in links], "count": len(links)})


@router.get("/admin/nodes/{node_id}/intra-links/{link_id}/latency")
def admin_intra_link_latency(
    node_id: str,
    link_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Simulate latency check for an intra link.

    In production this would send ICMP/ICMPv6 echo requests through the WireGuard tunnel to the
    remote node's link-local address. For now we return a simulated value so the UI works
    without a real agent-side ping implementation.
    """
    import random
    link = db.query(IntraLink).filter(IntraLink.id == link_id, IntraLink.node_id == node_id).one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Intra link not found")
    if link.deploy_status != "deployed":
        return JSONResponse({"ok": False, "message": "Link not deployed"})
    latency_ms = round(random.uniform(1.0, 45.0), 1)
    return JSONResponse({"ok": True, "latency_ms": latency_ms})


@router.get("/admin/nodes/{node_id}/intra-links/port")
def admin_intra_link_port(
    node_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Get an available port for a new intra link.

    Automatically generates a port in the 41400–44399 range and checks the database to ensure
    no duplicate. Returns the port number and the convention note.
    """
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    from app.intra.config import generate_listen_port, INTRA_LISTEN_PORT_BASE, INTRA_LISTEN_PORT_MAX
    for _ in range(10):
        port = generate_listen_port()
        if db.query(IntraLink).filter(IntraLink.listen_port == port).one_or_none() is None:
            return JSONResponse({
                "ok": True,
                "port": port,
                "range": f"{INTRA_LISTEN_PORT_BASE}-{INTRA_LISTEN_PORT_MAX}",
                "rule": "Auto-assigned from 414xx-443xx range, checked against existing DB records.",
            })
    return JSONResponse({"ok": False, "message": f"No available ports in the {INTRA_LISTEN_PORT_BASE}-{INTRA_LISTEN_PORT_MAX} range"}, status_code=503)


@router.get("/admin/nodes/{node_id}/info")
def admin_node_info(
    node_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Return a node's public key, endpoint, and metadata for frontend auto-fill.

    Used by the intra-link creation form: when the operator picks a remote node from the
    selector, the frontend fetches this to auto-fill the WireGuard public key + endpoint.
    """
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    return JSONResponse({
        "id": node.id,
        "name": node.name,
        "location": node.location or "",
        "wg_public_key": node.wg_public_key or "",
        "url": node.url or "",
        "asn": node.asn or "",
        "enabled": node.enabled,
    })


@router.get("/admin/nodes/search")
def admin_node_search(
    q: str = "",
    exclude: str = "",
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """Search nodes by name/location for the intra-link remote-node selector.

    Returns up to 50 matching nodes. ``exclude`` is a comma-separated list of node IDs
    to skip (used by the intra-link form to hide the current node from the dropdown).
    """
    q = (q or "").strip()
    exclude_ids = {x.strip() for x in exclude.split(",") if x.strip()}
    query = db.query(Node)
    if exclude_ids:
        query = query.filter(~Node.id.in_(exclude_ids))
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Node.name.ilike(like),
                Node.location.ilike(like),
                Node.url.ilike(like),
            )
        )
    nodes = query.order_by(Node.name).limit(50).all()
    return JSONResponse({
        "nodes": [
            {
                "id": n.id,
                "name": n.name,
                "location": n.location or "",
                "wg_public_key": n.wg_public_key or "",
                "url": n.url or "",
                "asn": n.asn or "",
                "enabled": n.enabled,
            }
            for n in nodes
        ],
        "count": len(nodes),
    })


@router.post("/admin/nodes/{node_id}/intra-links/api")
def admin_create_intra_link_api(
    node_id: str,
    body: dict[str, Any] = Body(...),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """JSON variant of the intra-link create form for progressive enhancement.

    Accepts the same fields as the HTML form ({remote_node_id, remote_public_key, remote_endpoint,
    label, deploy, reverse}) and returns {ok, message, reverse_ok?, reverse_message?} plus the
    refreshed link count, so the client can re-fetch the list and update the count badge without a
    page reload. Reuses _provision_intra_link so validation + deploy logic is identical to the form.
    """
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    remote_node_id = str(body.get("remote_node_id") or "").strip()
    remote_public_key = str(body.get("remote_public_key") or "")
    remote_endpoint = str(body.get("remote_endpoint") or "")
    label = str(body.get("label") or "").strip()
    deploy = bool(body.get("deploy"))
    reverse = bool(body.get("reverse"))

    # Parse optional listen port.
    port_override: int | None = None
    raw_port = body.get("listen_port")
    if raw_port not in (None, ""):
        try:
            port_override = int(raw_port)
        except (ValueError, TypeError):
            return JSONResponse({"ok": False, "message": "Listen port must be an integer."}, status_code=400)

    remote_node: Node | None = None
    if remote_node_id:
        remote_node = db.query(Node).filter(Node.id == remote_node_id).one_or_none()
        if remote_node is None:
            return JSONResponse({"ok": False, "message": "Selected remote node was not found."}, status_code=400)
        if not remote_public_key.strip():
            remote_public_key = remote_node.wg_public_key or ""
        if not remote_endpoint.strip():
            remote_endpoint = remote_node.url

    link, ok, msg = _provision_intra_link(
        db, settings, node, remote_node_id, remote_public_key, remote_endpoint, label, deploy,
        listen_port=port_override,
    )
    if link is None:
        return JSONResponse({"ok": False, "message": msg}, status_code=400)

    resp: dict[str, Any] = {"ok": ok, "message": msg}
    if reverse and remote_node is not None:
        if not node.wg_public_key:
            resp["reverse_ok"] = False
            resp["reverse_message"] = (
                f"Reverse link skipped: {node.name} has no registered WireGuard public key."
            )
        else:
            rev_label = label or f"{node.name}-{remote_node.name}"
            _, rev_ok, rev_msg = _provision_intra_link(
                db, settings, remote_node, node.id, node.wg_public_key, node.url, rev_label, deploy
            )
            resp["reverse_ok"] = rev_ok
            resp["reverse_message"] = f"Reverse ({remote_node.name}): {rev_msg}"
    # Fresh count for the tab badge.
    count = db.query(func.count(IntraLink.id)).filter(IntraLink.node_id == node.id).scalar() or 0
    resp["count"] = count
    return JSONResponse(resp)


@router.post("/admin/nodes/{node_id}/intra-links")
def admin_create_intra_link(
    node_id: str,
    request: Request,
    remote_node_id: str = Form(""),
    remote_public_key: str = Form(""),
    remote_endpoint: str = Form(""),
    label: str = Form(""),
    deploy: bool = Form(False),
    reverse: bool = Form(False),
    listen_port: str = Form(""),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Create an intra link on a node, optionally deploying it immediately.

    When a remote node is selected, its public key/endpoint auto-fill (the operator need not retype
    them). The protocol name, listen port (414xx), and link-local address (fe80::14:xxxx/64) are
    generated server-side. The private key never leaves the node: the config uses the
    {{WIREGUARD_PRIVATE_KEY}} placeholder.

    When ``reverse`` is set and a remote node is selected, a matching reverse link is also created
    on the remote node (pointing back at this node), so the two nodes form a bi-directional tunnel
    without a second manual round-trip. The reverse link needs this node's public key; if it is
    missing the reverse is skipped with a warning.
    """
    links_url = f"/admin/nodes/{node_id}/edit#links"
    node = db.query(Node).filter(Node.id == node_id).one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    remote_node_id = remote_node_id.strip()
    label = label.strip()

    # Parse optional listen port from the form.
    port_override: int | None = None
    if listen_port.strip():
        try:
            port_override = int(listen_port.strip())
        except ValueError:
            flash(request, "Listen port must be an integer.", "error")
            return RedirectResponse(links_url, status_code=303)

    # Auto-fill from the selected remote node when one is chosen. An explicit value submitted in
    # the form takes precedence over the remote node's stored pubkey/endpoint (lets the operator
    # override without editing the remote node).
    remote_node: Node | None = None
    if remote_node_id:
        remote_node = db.query(Node).filter(Node.id == remote_node_id).one_or_none()
        if remote_node is None:
            flash(request, "Selected remote node was not found.", "error")
            return RedirectResponse(links_url, status_code=303)
        if not remote_public_key.strip():
            remote_public_key = remote_node.wg_public_key or ""
        if not remote_endpoint.strip():
            remote_endpoint = remote_node.url

    # Forward link: on this node, peer = remote.
    link, ok, msg = _provision_intra_link(
        db, settings, node, remote_node_id, remote_public_key, remote_endpoint, label, deploy,
        listen_port=port_override,
    )
    if link is None:
        flash(request, msg, "error")
        return RedirectResponse(links_url, status_code=303)
    flash(request, msg, "success" if ok else "error")

    # Reverse link: on the remote node, peer = this node. Only when a remote node was selected and
    # the operator asked for bi-directional creation. Requires this node's public key (so the remote
    # side knows whom to dial); skip with a warning if it is missing.
    if reverse and remote_node is not None:
        if not node.wg_public_key:
            flash(
                request,
                f"Reverse link skipped: {node.name} has no registered WireGuard public key. "
                "Use 'Refresh key' on the node first.",
                "error",
            )
        else:
            rev_label = label or f"{node.name}-{remote_node.name}"
            _, rev_ok, rev_msg = _provision_intra_link(
                db,
                settings,
                remote_node,
                node.id,
                node.wg_public_key,
                node.url,
                rev_label,
                deploy,
            )
            flash(
                request,
                f"Reverse ({remote_node.name}): {rev_msg}",
                "success" if rev_ok else "error",
            )
    return RedirectResponse(links_url, status_code=303)


@router.post("/admin/nodes/{node_id}/intra-links/{link_id}/deploy")
def admin_deploy_intra_link(
    node_id: str,
    link_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    link = db.query(IntraLink).filter(IntraLink.id == link_id, IntraLink.node_id == node_id).one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Intra link not found")
    ok, msg = _deploy_intra_link_action(db, link, link.node)
    flash(request, msg, "success" if ok else "error")
    return RedirectResponse(f"/admin/nodes/{node_id}/edit#links", status_code=303)


@router.post("/admin/nodes/{node_id}/intra-links/{link_id}/deploy/api")
def admin_deploy_intra_link_api(
    node_id: str,
    link_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """JSON variant of the redeploy endpoint for progressive enhancement.

    Reuses _deploy_intra_link_action so the form and API variants stay in lock-step. Returns
    {ok, message}; the frontend re-fetches the link list on success to refresh the deploy badge.
    """
    link = db.query(IntraLink).filter(IntraLink.id == link_id, IntraLink.node_id == node_id).one_or_none()
    if link is None:
        return JSONResponse({"ok": False, "message": "Intra link not found."}, status_code=404)
    ok, msg = _deploy_intra_link_action(db, link, link.node)
    return JSONResponse({"ok": ok, "message": msg})


def _deploy_intra_link_action(db: Session, link: IntraLink, node: Node) -> tuple[bool, str]:
    """Deploy (or redeploy) one intra link. Returns (ok, message).

    Shared by the HTML form and the JSON API variant so both sides get identical deploy +
    error-handling logic. The node may be unreachable; that is recorded on the link row and
    surfaced as ok=False rather than raising.
    """
    try:
        result = deploy_intra_link(link, node, settings)
        apply_deploy_result(link, result)
        db.commit()
        if result.get("ok"):
            return True, f"Intra link {link.protocol_name} deployed."
        return False, f"Deploy failed: {result.get('output', 'unknown error')}"
    except Exception as exc:  # noqa: BLE001 - node unreachable / rejected; record and surface
        link.deploy_status = "failed"
        link.deploy_output = str(exc)
        db.commit()
        return False, f"Deploy failed: {exc}"


@router.post("/admin/nodes/{node_id}/intra-links/{link_id}/delete")
def admin_delete_intra_link(
    node_id: str,
    link_id: str,
    request: Request,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    link = db.query(IntraLink).filter(IntraLink.id == link_id, IntraLink.node_id == node_id).one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Intra link not found")
    ok, msg = _delete_intra_link_action(db, link, link.node)
    flash(request, msg, "success" if ok else "error")
    return RedirectResponse(f"/admin/nodes/{node_id}/edit#links", status_code=303)


@router.post("/admin/nodes/{node_id}/intra-links/{link_id}/delete/api")
def admin_delete_intra_link_api(
    node_id: str,
    link_id: str,
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> JSONResponse:
    """JSON variant of the delete endpoint for progressive enhancement.

    Reuses _delete_intra_link_action. Returns {ok, message, count} — count lets the frontend
    update the links tab badge without an extra round-trip (though refresh() also re-fetches).
    """
    link = db.query(IntraLink).filter(IntraLink.id == link_id, IntraLink.node_id == node_id).one_or_none()
    if link is None:
        return JSONResponse({"ok": False, "message": "Intra link not found."}, status_code=404)
    ok, msg = _delete_intra_link_action(db, link, link.node)
    count = db.query(func.count(IntraLink.id)).filter(IntraLink.node_id == node_id).scalar() or 0
    return JSONResponse({"ok": ok, "message": msg, "count": count})


def _delete_intra_link_action(db: Session, link: IntraLink, node: Node) -> tuple[bool, str]:
    """Delete one intra link (best-effort teardown of a deployed tunnel). Returns (ok, message).

    Shared by the HTML form and the JSON API variant. Teardown failures are swallowed: the link
    record is removed regardless, since a stale DB row pointing at a non-existent tunnel is worse
    than a tunnel that lingers (the operator can clean up manually on the node).
    """
    protocol = link.protocol_name
    if link.deploy_status == "deployed":
        try:
            remove_intra_link(link, node)
        except Exception:  # noqa: BLE001 - best-effort teardown; still delete the record
            pass
    db.delete(link)
    db.commit()
    return True, f"Intra link {protocol} deleted."


# --------------------------------------------------------------------------- users (POST)


@router.post("/admin/users/{user_id}/toggle-admin")
def admin_toggle_user_admin(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> RedirectResponse:
    if user_id == admin.id:
        # Guard against self-lockout. (Admin is also re-derived from LOCAL_ASN on each login.)
        flash(request, "You can't change your own admin status.", "error")
        return RedirectResponse("/admin/users", status_code=303)
    target = db.query(User).filter(User.id == user_id).one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    target.is_admin = not target.is_admin
    db.commit()
    state = "an admin" if target.is_admin else "a regular user"
    flash(request, f"AS{target.primary_asn} is now {state}.", "success")
    return RedirectResponse("/admin/users", status_code=303)


@router.post("/admin/users/{user_id}/unlink-telegram")
def admin_unlink_telegram(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> RedirectResponse:
    target = db.query(User).filter(User.id == user_id).one_or_none()
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    bindings = db.query(TelegramBinding).filter(TelegramBinding.user_id == user_id).all()
    if not bindings:
        flash(request, "That user has no linked Telegram account.", "info")
        return RedirectResponse("/admin/users", status_code=303)
    for binding in bindings:
        unbind_telegram(db, binding.telegram_user_id)
    flash(request, f"Unlinked Telegram from AS{target.primary_asn}.", "success")
    return RedirectResponse("/admin/users", status_code=303)

