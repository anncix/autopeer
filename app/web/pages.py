"""Public pages and auth callbacks: home, nodes, login/logout, Kioubit + Telegram auth."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.kioubit import KioubitAuthError, KioubitVerifier
from app.auth.service import consume_challenge, create_challenge, upsert_user_from_kioubit
from app.auth.session import current_user, login_user, logout_user
from app.db.models import Node, PeerRequest
from app.db.session import get_db
from app.node_ws import node_runtime_context
from app.web.deps import build_map_data, render, settings

router = APIRouter()

# Region mapping based on location keywords
REGION_KEYWORDS = {
    "asia": ["china", "japan", "jp", "korea", "kr", "hong kong", "hk", "taipei", "taiwan", "cn", "beijing", "shanghai", "shenzhen", "guangzhou", "chengdu", "tokyo", "osaka", "seoul"],
    "southeast-asia": ["singapore", "sg", "malaysia", "my", "indonesia", "id", "thailand", "th", "vietnam", "vn", "philippines", "ph", "bangkok", "jakarta", "kuala lumpur"],
    "europe": ["germany", "de", "france", "fr", "uk", "gb", "britain", "netherlands", "nl", "belgium", "be", "switzerland", "ch", "austria", "at", "italy", "it", "spain", "es", "portugal", "pt", "poland", "pl", "sweden", "se", "norway", "no", "denmark", "dk", "finland", "fi", "ireland", "ie", "russia", "ru", "turkey", "tr", "frankfurt", "paris", "london", "amsterdam", "brussels", "zurich", "vienna", "milan", "madrid", "warsaw", "stockholm", "oslo", "copenhagen", "helsinki", "dublin", "moscow", "istanbul"],
    "north-america": ["usa", "us", "canada", "ca", "mexico", "mx", "los angeles", "new york", "chicago", "san francisco", "seattle", "toronto", "vancouver", "montreal", "washington", "boston", "dallas", "miami", "houston"],
    "oceania": ["australia", "au", "new zealand", "nz", "sydney", "melbourne", "brisbane", "auckland", "wellington"],
}

def infer_region(location: str) -> str:
    """Infer region from location string."""
    if not location:
        return "other"
    location_lower = location.lower()
    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in location_lower:
                return region
    return "other"


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Landing page: intro, a peering guide, and live network stats."""
    nodes = db.query(Node).order_by(Node.name).all()
    runtime = node_runtime_context(nodes)
    node_count = len(nodes)
    nodes_online = sum(1 for r in runtime.values() if r.get("online"))
    peer_count = db.query(func.count(PeerRequest.id)).scalar() or 0
    deployed_count = (
        db.query(func.count(PeerRequest.id))
        .filter(PeerRequest.deploy_status == "deployed")
        .scalar()
        or 0
    )

    return render(
        request,
        "home.html",
        {
            "stats_nodes": node_count,
            "stats_nodes_online": nodes_online,
            "stats_peers": peer_count,
            "stats_deployed": deployed_count,
        },
        user=current_user(request, db),
        active="home",
    )


@router.get("/nodes", response_class=HTMLResponse)
def nodes_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Public node directory: all nodes with their live status (iEdon-style)."""
    nodes = db.query(Node).order_by(Node.name).all()
    runtime = node_runtime_context(nodes)
    nodes_online = sum(1 for item in runtime.values() if item["online"])
    nodes_total = len(nodes)
    nodes_enabled = sum(1 for n in nodes if n.enabled)

    # Per-node peer stats
    peer_stats: dict[str, dict] = {}
    all_peers = db.query(PeerRequest).all()
    for peer in all_peers:
        stats = peer_stats.setdefault(peer.node_id, {"total": 0, "deployed": 0})
        stats["total"] += 1
        if peer.deploy_status == "deployed":
            stats["deployed"] += 1

    # Collect distinct tunnel types used per node
    node_tunnel_types: dict[str, list[str]] = {}
    for peer in all_peers:
        tt = peer.tunnel_type
        if not tt:
            continue
        bucket = node_tunnel_types.setdefault(peer.node_id, [])
        if tt not in bucket:
            bucket.append(tt)

    nodes_with_region = [(node, infer_region(node.location)) for node in nodes]

    return render(
        request,
        "nodes.html",
        {
            "nodes": nodes,
            "nodes_with_region": nodes_with_region,
            "node_runtime": runtime,
            "node_peer_stats": peer_stats,
            "node_tunnel_types": node_tunnel_types,
            "nodes_online": nodes_online,
            "nodes_total": nodes_total,
            "nodes_enabled": nodes_enabled,
        },
        user=current_user(request, db),
        active="nodes",
    )


@router.get("/map", response_class=HTMLResponse)
def map_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Public network topology map: real-time latency across all nodes.

    Front-facing counterpart to the admin map — same SVG world map and mock latency data,
    but visible to all visitors (not just admins). Pass ?demo=1 to force all enabled
    nodes online with mock latency for preview/testing.
    """
    demo = request.query_params.get("demo") in ("1", "true", "yes")
    mock = request.query_params.get("mock") in ("1", "true", "yes")
    map_data = build_map_data(db, demo=demo, mock=mock)
    return render(
        request,
        "map.html",
        map_data,
        user=current_user(request, db),
        active="map",
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    challenge = create_challenge(db, purpose="web")
    return render(
        request,
        "login.html",
        {
            "return_url": f"{settings.base_url}/auth/kioubit/callback",
            "token": challenge.token,
        },
        user=current_user(request, db),
    )


@router.get("/logout")
def logout(request: Request) -> RedirectResponse:
    logout_user(request)
    return RedirectResponse("/", status_code=303)


@router.get("/auth/kioubit/callback")
def kioubit_callback(
    request: Request,
    params: str,
    signature: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    verifier = KioubitVerifier(settings.kioubit_public_key_path, settings.auth_domain)
    try:
        data = verifier.verify(params=params, signature=signature)
        consume_challenge(db, data.get("user_token", ""), purpose="web")
        user = upsert_user_from_kioubit(db, data, settings)
    except (KioubitAuthError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    login_user(request, user)
    return RedirectResponse("/portal", status_code=303)


@router.get("/telegram/auth", response_class=HTMLResponse)
def telegram_auth_page(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return render(
        request,
        "telegram_auth.html",
        {
            "return_url": f"{settings.base_url}/telegram/auth?token={token}",
            "token": token,
        },
        user=current_user(request, db),
    )
