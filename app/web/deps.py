from __future__ import annotations
"""Shared building blocks for the web (HTML) routes.

Holds the process-wide configured objects (settings, Jinja templates, the looking-glass rate
limiter) and the small helpers every router needs: ``render`` for template responses,
``query_enabled_nodes`` for the common node query, ``client_ip`` for rate-limit identity, the
``flash`` one-shot session messages, the ``Pagination`` helper, and the ``require_admin`` FastAPI
dependency that replaces the repeated admin-auth checks.
"""

import logging
import math
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.session import current_user
from app.config import get_settings
from app.db.models import IntraLink, Node, PeerRequest, User
from app.db.session import get_db
from app.lg.ratelimit import SlidingWindowRateLimiter
from app.node_ws import node_runtime_context
from app.version import VERSION

logger = logging.getLogger("dn42.autopeer")
settings = get_settings()
templates = Jinja2Templates(directory="app/templates")
lg_rate_limiter = SlidingWindowRateLimiter(settings.lg_rate_limit, settings.lg_rate_window_seconds)

# Session key holding pending one-shot flash messages until the next rendered page drains them.
_FLASH_KEY = "_flash"


def flash(request: Request, message: str, category: str = "info") -> None:
    """Queue a one-shot message shown on the next rendered page, then discarded.

    Used by browser form routes to report a validation error (then redirect back) instead of
    dumping FastAPI's raw ``{"detail": ...}`` JSON. ``category`` is one of info/success/error and
    only selects the banner style. 表單錯誤以 flash 顯示後即丟棄,取代原本的 JSON 錯誤回應。
    """
    request.session.setdefault(_FLASH_KEY, []).append({"category": category, "message": message})


def render(
    request: Request,
    name: str,
    context: dict | None = None,
    user: User | None = None,
    active: str | None = None,
) -> HTMLResponse:
    """Render ``name`` with the base context (request, settings, user, active nav, flashes).

    ``active`` is the current top-nav key (``lg``/``portal``/``admin``) for highlighting. Pending
    flashes are popped from the session here so they show exactly once.
    """
    base = {
        "request": request,
        "settings": settings,
        "user": user,
        "active": active,
        "version": VERSION,
        "flashes": request.session.pop(_FLASH_KEY, []),
    }
    if context:
        base.update(context)
    return templates.TemplateResponse(request=request, name=name, context=base)


def query_enabled_nodes(db: Session):
    """Query of enabled nodes ordered by name. Returns the query so callers can refine it."""
    return db.query(Node).filter(Node.enabled.is_(True)).order_by(Node.name)


def client_ip(request: Request) -> str:
    """Best-effort client identity for rate limiting.

    Uses request.client.host by default. Set FORWARDED_IP_HEADER (e.g. ``X-Forwarded-For``)
    only when running behind a trusted reverse proxy that sets it, otherwise every request
    would share one bucket (the proxy IP).
    """
    header = settings.forwarded_ip_header.strip()
    if header:
        value = request.headers.get(header, "")
        if value:
            return value.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def require_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """FastAPI dependency: return the current admin user, or raise 403.

    ``get_db`` is request-cached, so declaring this dependency does not open a second session;
    a route can keep its own ``db: Session = Depends(get_db)`` and share the same one.
    """
    user = current_user(request, db)
    if user is None or not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


@dataclass
class Pagination:
    """Page math for list views. Clamps ``page`` into ``[1, pages]`` against ``total``.

    The route supplies the raw ``page`` query param and the row ``total``; the clamped ``page`` and
    ``offset`` then drive the ``LIMIT``/``OFFSET`` query, and the template uses ``pages``/
    ``has_prev``/``has_next`` to draw the pager.
    """

    page: int
    per_page: int
    total: int

    def __post_init__(self) -> None:
        self.page = max(1, min(self.page, self.pages))

    @property
    def pages(self) -> int:
        return max(1, math.ceil(self.total / self.per_page))

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.pages


# ---------------------------------------------------------------------------
# Network map data
# ---------------------------------------------------------------------------

_MAP_LOCATION_COORDS = {
    "frankfurt": (50.1109, 8.6821),
    "berlin": (52.5200, 13.4050),
    "paris": (48.8566, 2.3522),
    "london": (51.5074, -0.1278),
    "amsterdam": (52.3676, 4.9041),
    "toronto": (43.6532, -79.3832),
    "new york": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "tokyo": (35.6762, 139.6503),
    "singapore": (1.3521, 103.8198),
    "beijing": (39.9042, 116.4074),
    "shanghai": (31.2304, 121.4737),
    "sydney": (-33.8688, 151.2093),
    "sao paulo": (-23.5505, -46.6333),
    "cape town": (-33.9249, 18.4241),
    "hong kong": (22.3193, 114.1694),
    "seoul": (37.5665, 126.9780),
    "mumbai": (19.0760, 72.8777),
    "bangkok": (13.7563, 100.5018),
    "dubai": (25.2048, 55.2708),
    "jakarta": (-6.2088, 106.8456),
    "kuala lumpur": (3.1390, 101.6869),
    "tehran": (35.6892, 51.3890),
    "stockholm": (59.3293, 18.0686),
    "madrid": (40.4168, -3.7038),
    "rome": (41.9028, 12.4964),
    "warsaw": (52.2297, 21.0122),
    "istanbul": (41.0082, 28.9784),
    "chicago": (41.8781, -87.6298),
    "san francisco": (37.7749, -122.4194),
    "vancouver": (49.2827, -123.1207),
    "mexico city": (19.4326, -99.1332),
    "miami": (25.7617, -80.1918),
    "buenos aires": (-34.6037, -58.3816),
    "lima": (-12.0464, -77.0428),
    "bogota": (4.7110, -74.0721),
    "cairo": (30.0444, 31.2357),
    "lagos": (6.5244, 3.3792),
    "melbourne": (-37.8136, 144.9631),
    "auckland": (-36.8485, 174.7633),
    "germany": (50.1109, 8.6821),
    "de": (50.1109, 8.6821),
    "france": (48.8566, 2.3522),
    "fr": (48.8566, 2.3522),
    "uk": (51.5074, -0.1278),
    "britain": (51.5074, -0.1278),
    "gbr": (51.5074, -0.1278),
    "netherlands": (52.3676, 4.9041),
    "holland": (52.3676, 4.9041),
    "nl": (52.3676, 4.9041),
    "canada": (43.6532, -79.3832),
    "ca": (43.6532, -79.3832),
    "us": (39.8283, -98.5795),
    "usa": (39.8283, -98.5795),
    "america": (39.8283, -98.5795),
    "japan": (35.6762, 139.6503),
    "jp": (35.6762, 139.6503),
    "sg": (1.3521, 103.8198),
}


def _map_coords(location: str | None) -> tuple[float, float] | None:
    if not location:
        return None
    loc = location.lower()
    for key, coords in _MAP_LOCATION_COORDS.items():
        if key in loc:
            return coords
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    import math
    R = 6371.0
    rlat1, rlat2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _latency_from_distance(dist_km: float) -> float:
    import random
    base = dist_km / 200.0
    routing = 5.0
    jitter = random.uniform(-3, 8)
    return max(1.0, round(base + routing + jitter, 1))


# 10 test cities spanning every continent for alignment verification (?mock=1)
_MOCK_CITIES = [
    ("mock-beijing",   "Beijing",     "Beijing, China",           39.9,  116.4),
    ("mock-shanghai",  "Shanghai",    "Shanghai, China",          31.2,  121.5),
    ("mock-newyork",   "New York",    "New York, USA",            40.7,  -74.0),
    ("mock-london",    "London",      "London, UK",               51.5,   -0.1),
    ("mock-tokyo",     "Tokyo",       "Tokyo, Japan",             35.7,  139.7),
    ("mock-sydney",    "Sydney",      "Sydney, Australia",       -33.9,  151.2),
    ("mock-singapore", "Singapore",   "Singapore",                 1.3,  103.8),
    ("mock-frankfurt", "Frankfurt",   "Frankfurt, Germany",       50.1,    8.7),
    ("mock-saopaulo",  "Sao Paulo",   "Sao Paulo, Brazil",       -23.5,  -46.6),
    ("mock-capetown",  "Cape Town",   "Cape Town, South Africa", -33.9,   18.4),
]


def build_map_data(db: Session, demo: bool = False, mock: bool = False) -> dict:
    """Build the node/latency/link data for the network map (public + admin share this).

    Generates mock latency from geographic distance using a fiber transmission model.
    Returns ``{"stats", "nodes_geo", "intra_links"}`` ready for the map template.

    When ``demo=True``, all enabled nodes are treated as online with mock latency
    so the map is populated for preview/testing without real node heartbeats.

    When ``mock=True``, returns 10 hardcoded test cities (one per major continent)
    with full-mesh links, bypassing the database entirely. Used to verify that
    node dots align perfectly with the continent outlines in world-map.json.
    """
    import random
    from sqlalchemy import func

    # ── Mock mode: 10 test cities, no database access ──
    if mock:
        nodes_geo: list[dict] = []
        for nid, name, location, lat, lng in _MOCK_CITIES:
            history = [round(max(5.0, lat * 0 + 15 + random.uniform(-6, 10)), 1) for _ in range(5)]
            nodes_geo.append({
                "id": nid,
                "name": name,
                "location": location,
                "lat": lat,
                "lng": lng,
                "online": True,
                "latency": history[-1],
                "history": history,
            })

        intra_links_data: list[dict] = []
        for i in range(len(_MOCK_CITIES)):
            src_id, src_name, _, src_lat, src_lng = _MOCK_CITIES[i]
            for j in range(i + 1, len(_MOCK_CITIES)):
                tgt_id, tgt_name, _, tgt_lat, tgt_lng = _MOCK_CITIES[j]
                dist = _haversine_km(src_lat, src_lng, tgt_lat, tgt_lng)
                latency = max(1.0, round(_latency_from_distance(dist), 1))
                intra_links_data.append({
                    "id": f"mock-{src_id}-{tgt_id}",
                    "source_id": src_id,
                    "target_id": tgt_id,
                    "source_lat": src_lat,
                    "source_lng": src_lng,
                    "target_lat": tgt_lat,
                    "target_lng": tgt_lng,
                    "label": f"{src_name} ↔ {tgt_name}",
                    "latency": latency,
                    "deployed": True,
                })

        return {
            "stats": {
                "nodes_total": len(_MOCK_CITIES),
                "nodes_enabled": len(_MOCK_CITIES),
                "nodes_online": len(_MOCK_CITIES),
                "peers_total": 0,
                "peers_deployed": 0,
                "peers_failed": 0,
                "links_total": len(intra_links_data),
            },
            "nodes_geo": nodes_geo,
            "intra_links": intra_links_data,
        }


    nodes_for_runtime = db.query(Node).order_by(Node.name).all()
    runtime = node_runtime_context(nodes_for_runtime)

    # In demo mode, treat all enabled nodes as online
    if demo:
        for n in nodes_for_runtime:
            if n.enabled:
                runtime[n.id] = {**runtime.get(n.id, {}), "online": True}

    nodes_online = sum(1 for item in runtime.values() if item["online"])

    def count(model, *filters) -> int:
        query = db.query(func.count(model.id))
        for f in filters:
            query = query.filter(f)
        return query.scalar() or 0

    stats = {
        "nodes_total": count(Node),
        "nodes_enabled": count(Node, Node.enabled.is_(True)),
        "nodes_online": nodes_online,
        "peers_total": count(PeerRequest),
        "peers_deployed": count(PeerRequest, PeerRequest.deploy_status == "deployed"),
        "peers_failed": count(PeerRequest, PeerRequest.deploy_status == "failed"),
        "links_total": count(IntraLink),
    }

    nodes_geo: list[dict] = []
    node_coords_map: dict[str, tuple[float, float]] = {}
    node_online_map: dict[str, bool] = {}
    for n in nodes_for_runtime:
        coords = _map_coords(n.location)
        online = runtime.get(n.id, {}).get("online", False)
        if coords:
            node_coords_map[n.id] = coords
        node_online_map[n.id] = online
        nodes_geo.append({
            "id": n.id,
            "name": n.name,
            "location": n.location,
            "lat": coords[0] if coords else None,
            "lng": coords[1] if coords else None,
            "online": online,
        })

    for node_entry in nodes_geo:
        nid = node_entry["id"]
        online = node_entry["online"]
        if not online or nid not in node_coords_map:
            node_entry["latency"] = None
            node_entry["history"] = []
            continue

        lat, lon = node_coords_map[nid]
        peer_latencies: list[float] = []
        for other_id, (olat, olon) in node_coords_map.items():
            if other_id == nid:
                continue
            dist = _haversine_km(lat, lon, olat, olon)
            peer_latencies.append(_latency_from_distance(dist))

        base_latency = sum(peer_latencies) / len(peer_latencies) if peer_latencies else 20.0

        history: list[float] = []
        current = base_latency
        for _ in range(5):
            delta = random.uniform(-8, 12)
            current = max(1.0, current + delta)
            history.append(round(current, 1))
        node_entry["history"] = history
        node_entry["latency"] = history[-1]

    intra_links_data: list[dict] = []
    links_query = db.query(IntraLink).filter(
        IntraLink.remote_node_id.isnot(None),
        IntraLink.deploy_status == "deployed",
    ).all()
    for link in links_query:
        local_coords = node_coords_map.get(link.node_id)
        remote_coords = node_coords_map.get(link.remote_node_id)
        if not local_coords or not remote_coords:
            continue
        local_online = node_online_map.get(link.node_id, False)
        remote_online = node_online_map.get(link.remote_node_id, False)
        if not local_online or not remote_online:
            continue

        dist = _haversine_km(local_coords[0], local_coords[1], remote_coords[0], remote_coords[1])
        link_latency = _latency_from_distance(dist)
        link_latency = max(1.0, round(link_latency + random.uniform(-2, 5), 1))

        intra_links_data.append({
            "id": link.id,
            "source_id": link.node_id,
            "target_id": link.remote_node_id,
            "source_lat": local_coords[0],
            "source_lng": local_coords[1],
            "target_lat": remote_coords[0],
            "target_lng": remote_coords[1],
            "label": link.label,
            "latency": link_latency,
            "deployed": True,
        })

    # In demo mode, generate full-mesh links (n-1 per node) so every node
    # connects to every other node for visual verification. Discard any DB
    # links first so node pairs aren't duplicated (DB links are a subset of
    # the full mesh anyway, and duplicates create overlapping curves).
    if demo:
        intra_links_data = []
        online_nodes = [
            (n["id"], n["lat"], n["lng"], n["name"])
            for n in nodes_geo
            if n["online"] and n["lat"] is not None
        ]
        for i in range(len(online_nodes)):
            src_id, src_lat, src_lng, src_name = online_nodes[i]
            for j in range(i + 1, len(online_nodes)):
                tgt_id, tgt_lat, tgt_lng, tgt_name = online_nodes[j]
                dist = _haversine_km(src_lat, src_lng, tgt_lat, tgt_lng)
                latency = max(1.0, round(_latency_from_distance(dist), 1))
                intra_links_data.append({
                    "id": f"demo-{src_id}-{tgt_id}",
                    "source_id": src_id,
                    "target_id": tgt_id,
                    "source_lat": src_lat,
                    "source_lng": src_lng,
                    "target_lat": tgt_lat,
                    "target_lng": tgt_lng,
                    "label": f"{src_name} ↔ {tgt_name}",
                    "latency": latency,
                    "deployed": True,
                })

    return {
        "stats": stats,
        "nodes_geo": nodes_geo,
        "intra_links": intra_links_data,
    }
