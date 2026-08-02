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
# Ensure INFO-level diagnostic logs reach stderr (uvicorn doesn't configure app loggers)
if not logger.handlers:
    import sys
    _h = logging.StreamHandler(sys.stderr)
    _h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(_h)
    logger.setLevel(logging.INFO)
    logger.propagate = False
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
    "new york city": (40.7128, -74.0060),
    "los angeles": (34.0522, -118.2437),
    "tokyo": (35.6762, 139.6503),
    "singapore": (1.3521, 103.8198),
    "beijing": (39.9042, 116.4074),
    "shanghai": (31.2304, 121.4737),
    "guangzhou": (23.1291, 113.2644),
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

# Chinese display names for map nodes — falls back to English name if missing.
_NODE_NAME_ZH = {
    "Beijing": "北京",
    "Shanghai": "上海",
    "Guangzhou": "广州",
    "Tokyo": "东京",
    "Hong Kong": "香港",
    "Singapore": "新加坡",
    "San Francisco": "硅谷",
    "Los Angeles": "洛杉矶",
    "New York": "纽约",
    "London": "伦敦",
    "Paris": "巴黎",
    "Frankfurt": "法兰克福",
    "Warsaw": "华沙",
    "Amsterdam": "阿姆斯特丹",
}

# Peer-count baselines per node — major Internet hubs get more peers.
# Demo mode adds ±random variation so values change on each page load.
_NODE_PEER_BASELINE = {
    "Singapore": 28,       # Major Asian exchange hub
    "Frankfurt": 26,       # DE-CIX, largest European exchange
    "Amsterdam": 24,       # AMS-IX, major European exchange
    "London": 22,          # LINX, major European exchange
    "Tokyo": 20,           # Major Asian hub (JPIX)
    "Hong Kong": 18,       # Major Asian exchange hub
    "Paris": 16,           # France-IX
    "Shanghai": 15,        # Chinese exchange hub
    "Los Angeles": 14,     # US west coast hub
    "New York": 16,        # US east coast hub (Equinix NY)
    "Beijing": 12,         # Chinese exchange hub
    "San Francisco": 10,   # US west coast
    "Guangzhou": 8,        # Chinese regional hub
    "Warsaw": 5,           # European regional
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
    # Fiber optic: ~200km/ms (speed of light in fiber ≈ 2/3 c)
    base = dist_km / 200.0
    # Routing overhead (hops, processing): 3-12ms
    routing = random.uniform(3, 12)
    # Jitter: ±3ms
    jitter = random.uniform(-3, 3)
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
                "peer_count": max(1, int(random.uniform(8, 35))),
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
        _enabled_count = sum(1 for n in nodes_for_runtime if n.enabled)
        logger.info("[map-data] DEMO mode active, setting %d/%d enabled nodes online",
                    _enabled_count, len(nodes_for_runtime))
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

    # Per-node peer counts: real DB count, or weighted mock in demo mode.
    peer_counts: dict[str, int] = {}
    if demo:
        for n in nodes_for_runtime:
            base = _NODE_PEER_BASELINE.get(n.name, 8)
            peer_counts[n.id] = max(1, int(base + random.uniform(-4, 6)))
    else:
        from sqlalchemy import func as _func
        pc_rows = db.query(
            PeerRequest.node_id, _func.count(PeerRequest.id)
        ).filter(PeerRequest.status == "active").group_by(PeerRequest.node_id).all()
        peer_counts = {nid: cnt for nid, cnt in pc_rows}

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
            "name_zh": _NODE_NAME_ZH.get(n.name, n.name),
            "location": n.location,
            "lat": coords[0] if coords else None,
            "lng": coords[1] if coords else None,
            "online": online,
            "peer_count": peer_counts.get(n.id, 0),
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

        # Mean-reverting random walk: pulls toward base_latency, adds symmetric noise
        history: list[float] = []
        current = base_latency + random.uniform(-3, 3)
        for _ in range(5):
            pull = (base_latency - current) * 0.3
            noise = random.uniform(-4, 4)
            current = max(1.0, current + pull + noise)
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
            (n["id"], n["lat"], n["lng"], n.get("name_zh") or n["name"])
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

    # ── Diagnostic logging: data injection integrity ──
    from datetime import datetime
    _ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    # Field completeness check per node
    _missing_coords = [n["name"] for n in nodes_geo if n["lat"] is None or n["lng"] is None]
    _missing_peers = [n["name"] for n in nodes_geo if n.get("peer_count") is None]
    _zero_peers = [n["name"] for n in nodes_geo if n.get("peer_count", 0) == 0]
    _missing_lat = [n["name"] for n in nodes_geo if n.get("latency") is None and n["online"]]
    _extreme_coords = [
        n["name"] for n in nodes_geo
        if n.get("lat") is not None and (abs(n["lat"]) > 85 or abs(n["lng"]) > 180)
    ]

    # New York specific check
    _ny = next((n for n in nodes_geo if n["name"] == "New York"), None)
    _ny_status = "OK"
    if not _ny:
        _ny_status = "MISSING"
    else:
        _ny_issues = []
        if _ny.get("lat") is None: _ny_issues.append("NO_LAT")
        if _ny.get("lng") is None: _ny_issues.append("NO_LNG")
        if _ny.get("peer_count") is None: _ny_issues.append("NO_PEERS")
        if _ny.get("latency") is None and _ny.get("online"): _ny_issues.append("NO_LATENCY")
        if _ny_issues: _ny_status = ",".join(_ny_issues)

    # Link integrity check
    _link_issues = []
    for l in intra_links_data:
        li = []
        if l.get("latency") is None: li.append("NO_LAT")
        if l.get("source_lat") is None: li.append("NO_SRC_COORD")
        if l.get("target_lat") is None: li.append("NO_TGT_COORD")
        if l.get("source_id") is None or l.get("target_id") is None: li.append("NO_ID")
        if li:
            _link_issues.append("%s: %s" % (l.get("id", "?"), ",".join(li)))

    # Check for orphan links (source/target not in node set)
    _node_ids = {n["id"] for n in nodes_geo}
    _orphan_links = [
        l["id"] for l in intra_links_data
        if l.get("source_id") not in _node_ids or l.get("target_id") not in _node_ids
    ]

    logger.info(
        "[%s][map-data] RECEIVED nodes=%d online=%d links=%d | "
        "missing_coords=%s zero_peers=%s missing_lat=%s extreme_coords=%s | "
        "new_york=%s | link_issues=%d orphan_links=%s",
        _ts, len(nodes_geo), stats["nodes_online"], len(intra_links_data),
        _missing_coords or "none", _zero_peers or "none", _missing_lat or "none",
        _extreme_coords or "none",
        _ny_status,
        len(_link_issues), _orphan_links or "none",
    )

    if demo:
        _peer_summary = {n["name_zh"]: n["peer_count"] for n in nodes_geo}
        _lat_summary = {n["name_zh"]: n.get("latency") for n in nodes_geo if n.get("latency")}
        logger.debug("[%s][map-data] DETAIL peers=%s", _ts, _peer_summary)
        logger.debug("[%s][map-data] DETAIL latency=%s", _ts, _lat_summary)
        logger.debug("[%s][map-data] DETAIL ny=%s", _ts, _ny)

    return {
        "stats": stats,
        "nodes_geo": nodes_geo,
        "intra_links": intra_links_data,
    }
