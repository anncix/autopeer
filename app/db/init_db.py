import secrets
import uuid

from sqlalchemy import inspect, text

from app.db.session import Base, SessionLocal, engine
from app.db.models import Node
from app.peer.validation import DEFAULT_WIREGUARD_MTU


def create_schema() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_node_columns()
    _ensure_peer_request_columns()
    _ensure_indexes()


# 40 test cities for map alignment verification — auto-seeded on startup if missing.
# Location strings must match keys in _MAP_LOCATION_COORDS (deps.py) for coordinate lookup.
_MAP_SEED_CITIES = [
    # Asia (12)
    ("Beijing",       "Beijing, China"),
    ("Shanghai",      "Shanghai, China"),
    ("Tokyo",         "Tokyo, Japan"),
    ("Singapore",     "Singapore"),
    ("Hong Kong",     "Hong Kong, China"),
    ("Seoul",         "Seoul, South Korea"),
    ("Mumbai",        "Mumbai, India"),
    ("Bangkok",       "Bangkok, Thailand"),
    ("Dubai",         "Dubai, UAE"),
    ("Jakarta",       "Jakarta, Indonesia"),
    ("Kuala Lumpur",  "Kuala Lumpur, Malaysia"),
    ("Tehran",        "Tehran, Iran"),
    # Europe (10)
    ("London",        "London, UK"),
    ("Frankfurt",     "Frankfurt, Germany"),
    ("Paris",         "Paris, France"),
    ("Amsterdam",     "Amsterdam, Netherlands"),
    ("Berlin",        "Berlin, Germany"),
    ("Stockholm",     "Stockholm, Sweden"),
    ("Madrid",        "Madrid, Spain"),
    ("Rome",          "Rome, Italy"),
    ("Warsaw",        "Warsaw, Poland"),
    ("Istanbul",      "Istanbul, Turkey"),
    # North America (8)
    ("New York",      "New York, USA"),
    ("Los Angeles",   "Los Angeles, USA"),
    ("Toronto",       "Toronto, Canada"),
    ("Chicago",       "Chicago, USA"),
    ("San Francisco", "San Francisco, USA"),
    ("Vancouver",     "Vancouver, Canada"),
    ("Mexico City",   "Mexico City, Mexico"),
    ("Miami",         "Miami, USA"),
    # South America (4)
    ("Sao Paulo",     "Sao Paulo, Brazil"),
    ("Buenos Aires",  "Buenos Aires, Argentina"),
    ("Lima",          "Lima, Peru"),
    ("Bogota",        "Bogota, Colombia"),
    # Africa (3)
    ("Cape Town",     "Cape Town, South Africa"),
    ("Cairo",         "Cairo, Egypt"),
    ("Lagos",         "Lagos, Nigeria"),
    # Oceania (3)
    ("Sydney",        "Sydney, Australia"),
    ("Melbourne",     "Melbourne, Australia"),
    ("Auckland",      "Auckland, New Zealand"),
]


def seed_map_test_nodes() -> None:
    """Idempotently insert test-city nodes so the map shows them without ?mock=1.

    Run on startup via the lifespan handler. Uses the server's own engine, avoiding
    SQLite multi-process lock issues. Visit /map?demo=1 to see them online with
    full-mesh links.
    """
    inspector = inspect(engine)
    if "nodes" not in inspector.get_table_names():
        return

    db = SessionLocal()
    try:
        created = 0
        for i, (name, location) in enumerate(_MAP_SEED_CITIES):
            existing = db.query(Node).filter(Node.name == name).first()
            if existing:
                existing.location = location
                existing.enabled = True
                continue
            node = Node(
                id=str(uuid.uuid4()),
                name=name,
                location=location,
                url=f"node{i+1}.map-test.local",
                token=secrets.token_hex(32),
                wg_public_key=secrets.token_urlsafe(32)[:44],
                asn=f"AS4242421{i:02d}",
                dn42_ipv4=f"172.23.{i+1}.1/32",
                dn42_ipv6=f"fd86:115:{i+1:x}::1/128",
                enabled=True,
            )
            db.add(node)
            created += 1
        db.commit()
        if created:
            import logging
            logging.getLogger("dn42.autopeer").info(
                "Seeded %d map test nodes (total: %d)", created, db.query(Node).count()
            )
    finally:
        db.close()


def _ensure_node_columns() -> None:
    """Backfill columns added to ``Node`` after a database was first created.

    ``Base.metadata.create_all`` only creates missing tables, never missing columns, so a
    column introduced later must be added with an idempotent ALTER on an existing DB.
    """
    inspector = inspect(engine)
    if "nodes" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("nodes")}
    additions = {
        "wg_public_key": "VARCHAR(128) NOT NULL DEFAULT ''",
        "last_seen_at": "DATETIME",
        "system_status_json": "TEXT NOT NULL DEFAULT '{}'",
        "asn": "VARCHAR(32) NOT NULL DEFAULT ''",
        "dn42_ipv4": "VARCHAR(64) NOT NULL DEFAULT ''",
        "dn42_ipv6": "VARCHAR(64) NOT NULL DEFAULT ''",
    }
    for name, ddl in additions.items():
        if name not in columns:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE nodes ADD COLUMN {name} {ddl}"))


def _ensure_peer_request_columns() -> None:
    """Backfill columns added to ``PeerRequest`` after a database was first created."""
    inspector = inspect(engine)
    if "peer_requests" not in inspector.get_table_names():
        return
    columns = {col["name"] for col in inspector.get_columns("peer_requests")}
    additions = {
        "wg_mtu": f"INTEGER NOT NULL DEFAULT {DEFAULT_WIREGUARD_MTU}",
        "peer_dn42_ipv4": "VARCHAR(64) NOT NULL DEFAULT ''",
        "peer_dn42_ipv6": "VARCHAR(64) NOT NULL DEFAULT ''",
        "bgp_extended": "BOOLEAN NOT NULL DEFAULT 1",
    }
    for name, ddl in additions.items():
        if name not in columns:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE peer_requests ADD COLUMN {name} {ddl}"))


def _ensure_indexes() -> None:
    """Create sort indexes used by admin list views, idempotently."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    indexes = {
        "peer_requests": {
            "ix_peer_requests_created_at": "created_at",
            "ix_peer_requests_updated_at": "updated_at",
        },
        "lg_queries": {
            "ix_lg_queries_created_at": "created_at",
        },
        "intra_links": {
            "ix_intra_links_created_at": "created_at",
            "ix_intra_links_updated_at": "updated_at",
        },
    }
    with engine.begin() as conn:
        for table, table_indexes in indexes.items():
            if table not in tables:
                continue
            columns = {col["name"] for col in inspector.get_columns(table)}
            existing = {idx["name"] for idx in inspector.get_indexes(table)}
            for name, column in table_indexes.items():
                if column in columns and name not in existing:
                    conn.execute(text(f"CREATE INDEX {name} ON {table} ({column})"))
