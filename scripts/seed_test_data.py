"""Seed script: Generate 10 nodes, 1000+ peers, and intra links.

Usage: python scripts/seed_test_data.py [--clear-existing]
"""

import sys
import os
import secrets
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, event, func
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.models import Base, Node, PeerRequest, IntraLink, User
from app.intra.config import (
    generate_listen_port,
    generate_link_local_address,
    intra_protocol_name,
    INTRA_LISTEN_PORT_BASE,
    INTRA_LISTEN_PORT_MAX,
)


def new_uuid() -> str:
    return str(uuid.uuid4())


def generate_wg_pubkey() -> str:
    return secrets.token_urlsafe(32)[:44]


def seed_database(clear_existing: bool = False):
    """Seed the database with proper test data."""
    settings = get_settings()
    database_url = settings.database_url

    print(f"Database URL: {database_url}")

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    engine = create_engine(database_url, connect_args=connect_args)

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    db = SessionLocal()

    try:
        if clear_existing:
            print("Clearing existing data...")
            db.query(IntraLink).delete()
            db.query(PeerRequest).delete()
            db.query(Node).delete()
            db.query(User).delete()
            db.commit()
            print("Cleared.")

        # Check if we have a user (admin)
        admin_user = db.query(User).filter(User.is_admin == True).first()
        if admin_user is None:
            print("Creating admin user...")
            admin_user = User(
                primary_asn=settings.local_asn or "AS65000",
                first_email="admin@example.com",
                is_admin=True,
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"  ✓ Created admin user: {admin_user.primary_asn}")

        # Create 10 nodes if not exists
        existing_nodes = db.query(Node).count()
        if existing_nodes == 0:
            print("Creating 10 nodes...")
            cities = [
                "Frankfurt", "Amsterdam", "London", "Paris", "Zurich",
                "Vienna", "Prague", "Warsaw", "Budapest", "Munich"
            ]

            nodes = []
            for i in range(10):
                node = Node(
                    id=new_uuid(),
                    name=f"node-{cities[i].lower()}-{i+1}",
                    location=cities[i],
                    url=f"vpn{i+1}.example.com",
                    token=secrets.token_hex(32),
                    wg_public_key=generate_wg_pubkey(),
                    asn=f"AS424242000{i}",
                    dn42_ipv4=f"172.23.{i}.1/32",
                    dn42_ipv6=f"fd86:115:{i}::1/128",
                    enabled=True,
                )
                db.add(node)
                nodes.append(node)

            db.commit()
            print(f"  ✓ Created {len(nodes)} nodes")
        else:
            print(f"Found {existing_nodes} nodes, skipping creation.")
            nodes = db.query(Node).all()

        # Create 1000 peers if not enough
        existing_peers = db.query(PeerRequest).count()
        target_peers = 1000
        peers_to_create = max(0, target_peers - existing_peers)

        if peers_to_create > 0:
            print(f"Creating {peers_to_create} peers...")

            # Get existing ASNs to avoid duplicates
            existing_asns = set()
            existing = db.query(PeerRequest.asn).all()
            for (asn,) in existing:
                existing_asns.add(asn)

            created_peers = 0
            errors = []

            for i in range(peers_to_create):
                # Generate unique ASN
                asn_num = 4242430000 + i
                asn = f"AS{asn_num}"
                while asn in existing_asns:
                    asn_num += 1
                    asn = f"AS{asn_num}"
                existing_asns.add(asn)

                # Distribute peers across nodes
                node = nodes[i % len(nodes)]

                # Generate peer addresses
                peer_link = f"172.24.{i // 256}.{(i % 256) + 1}/32"
                local_link = f"172.24.0.1/32"

                peer = PeerRequest(
                    id=new_uuid(),
                    user_id=admin_user.id,
                    asn=asn,
                    node_id=node.id,
                    tunnel_type="wireguard",
                    endpoint=f"peer{i+1}.example.com:{51820 + (i % 100)}",
                    wg_public_key=generate_wg_pubkey(),
                    wg_mtu=1420,
                    local_link_address=local_link,
                    peer_link_address=peer_link,
                    peer_dn42_ipv4=f"172.25.{i % 256}.{i % 256 + 1}/32",
                    peer_dn42_ipv6=f"fd86:116:{i}::1/128",
                    bgp_extended=True,
                    status="pending",
                    deploy_status="not_deployed",
                )
                db.add(peer)
                created_peers += 1

                if created_peers % 200 == 0:
                    db.commit()
                    print(f"  Progress: {created_peers}/{peers_to_create}...")

            db.commit()
            print(f"  ✓ Created {created_peers} peers")

            if errors:
                print(f"  ⚠ Errors: {len(errors)}")
        else:
            print(f"Already have {existing_peers} peers, target is {target_peers}. Skipping.")

        # Create intra links between nodes
        existing_links = db.query(IntraLink).count()
        target_links = 50
        links_to_create = max(0, target_links - existing_links)

        if links_to_create > 0:
            print(f"Creating {links_to_create} intra links...")

            used_ports: set[int] = set()
            existing = db.query(IntraLink.listen_port).all()
            for (port,) in existing:
                used_ports.add(port)

            used_protocol_names: set[str] = set()
            existing = db.query(IntraLink.protocol_name).all()
            for (name,) in existing:
                used_protocol_names.add(name)

            created_links = 0
            errors = []

            for i in range(links_to_create):
                src_node = nodes[i % len(nodes)]
                dst_node = nodes[(i + 1) % len(nodes)]
                if src_node.id == dst_node.id:
                    dst_node = nodes[(i + 2) % len(nodes)]

                link_id = new_uuid()
                protocol_name = intra_protocol_name(link_id)
                retries = 0
                while protocol_name in used_protocol_names and retries < 5:
                    link_id = new_uuid()
                    protocol_name = intra_protocol_name(link_id)
                    retries += 1

                if protocol_name in used_protocol_names:
                    errors.append(f"Could not generate unique protocol name for link {i}")
                    continue
                used_protocol_names.add(protocol_name)

                port = None
                for _ in range(10):
                    candidate = generate_listen_port()
                    if candidate not in used_ports:
                        port = candidate
                        used_ports.add(candidate)
                        break

                if port is None:
                    errors.append(f"Could not allocate unique port for link {i}")
                    continue

                link = IntraLink(
                    id=link_id,
                    node_id=src_node.id,
                    remote_node_id=dst_node.id,
                    label=f"{src_node.name}_{dst_node.name}",
                    protocol_name=protocol_name,
                    remote_public_key=dst_node.wg_public_key or generate_wg_pubkey(),
                    remote_endpoint=dst_node.url,
                    listen_port=port,
                    link_local_address=generate_link_local_address(),
                    deploy_status="not_deployed",
                )
                db.add(link)
                created_links += 1

            db.commit()
            print(f"  ✓ Created {created_links} intra links")

            if errors:
                print(f"  ⚠ Errors: {len(errors)}")
        else:
            print(f"Already have {existing_links} intra links. Skipping.")

        # Verify
        node_count = db.query(func.count(Node.id)).scalar()
        peer_count = db.query(func.count(PeerRequest.id)).scalar()
        link_count = db.query(func.count(IntraLink.id)).scalar()
        unique_ports = db.query(func.count(IntraLink.listen_port.distinct())).scalar()

        print()
        print("=" * 50)
        print("VERIFICATION")
        print("=" * 50)
        print(f"  Nodes: {node_count}")
        print(f"  Peers: {peer_count}")
        print(f"  Intra Links: {link_count}")
        print(f"  Unique Ports: {unique_ports}")

        if link_count == unique_ports:
            print(f"  ✓ All ports are unique")
        else:
            print(f"  ✗ DUPLICATE PORTS DETECTED!")

        print()
        print("Per-node distribution:")
        nodes_with_counts = db.query(
            Node.name,
            func.count(IntraLink.id)
        ).outerjoin(
            IntraLink, IntraLink.node_id == Node.id
        ).group_by(
            Node.name
        ).order_by(Node.name).all()

        for name, count in nodes_with_counts:
            peer_count_for_node = db.query(func.count(PeerRequest.id)).filter(
                PeerRequest.node_id.in_([n.id for n in nodes if n.name == name])
            ).scalar() or 0
            print(f"  {name}: {count} links, {peer_count_for_node} peers")

    finally:
        db.close()


if __name__ == "__main__":
    clear_existing = "--clear-existing" in sys.argv
    seed_database(clear_existing=clear_existing)
