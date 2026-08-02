"""Seed script: Persist 10 test-city nodes for map alignment verification.

Inserts the 10 cities (Beijing, Shanghai, New York, London, Tokyo, Sydney,
Singapore, Frankfurt, Sao Paulo, Cape Town) as enabled Node records so the
map page shows them without needing ?mock=1. Use ?demo=1 on /map to force
them online with mock latency and full-mesh links.

Usage:
    python scripts/seed_map_nodes.py              # upsert 10 cities, keep existing
    python scripts/seed_map_nodes.py --clear      # remove ALL nodes, then insert 10
"""

import sys
import secrets
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.session import SessionLocal
from app.db.models import Node


def new_uuid() -> str:
    return str(uuid.uuid4())


def generate_wg_pubkey() -> str:
    return secrets.token_urlsafe(32)[:44]


# 10 test cities — names must match _MAP_LOCATION_COORDS keys for coordinate lookup
SEED_CITIES = [
    ("Beijing",     "Beijing, China"),
    ("Shanghai",    "Shanghai, China"),
    ("New York",    "New York, USA"),
    ("London",      "London, UK"),
    ("Tokyo",       "Tokyo, Japan"),
    ("Sydney",      "Sydney, Australia"),
    ("Singapore",   "Singapore"),
    ("Frankfurt",   "Frankfurt, Germany"),
    ("Sao Paulo",   "Sao Paulo, Brazil"),
    ("Cape Town",   "Cape Town, South Africa"),
]


def seed(clear: bool = False):
    db = SessionLocal()

    try:
        if clear:
            deleted = db.query(Node).delete()
            db.commit()
            print(f"  ✓ Cleared {deleted} existing nodes")

        existing_count = db.query(Node).count()
        print(f"  Existing nodes: {existing_count}")

        created, skipped = 0, 0
        for i, (name, location) in enumerate(SEED_CITIES):
            existing = db.query(Node).filter(Node.name == name).first()
            if existing:
                # Update location in case it changed
                existing.location = location
                existing.enabled = True
                skipped += 1
                continue

            node = Node(
                id=new_uuid(),
                name=name,
                location=location,
                url=f"node{i+1}.map-test.local",
                token=secrets.token_hex(32),
                wg_public_key=generate_wg_pubkey(),
                asn=f"AS4242421{i:02d}",
                dn42_ipv4=f"172.23.{i+1}.1/32",
                dn42_ipv6=f"fd86:115:{i+1:x}::1/128",
                enabled=True,
            )
            db.add(node)
            created += 1

        db.commit()
        print(f"  ✓ Created {created} nodes, updated {skipped} existing")
        print(f"  Total nodes now: {db.query(Node).count()}")
        print(f"\n  Visit: http://127.0.0.1:8000/map?demo=1")
    finally:
        db.close()


if __name__ == "__main__":
    clear = "--clear" in sys.argv
    seed(clear=clear)
