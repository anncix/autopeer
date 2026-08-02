"""Comprehensive seed script: nodes, peers, intra links, users, LG queries.

Usage: python scripts/seed_comprehensive.py [--clear-existing]
"""

import sys
import os
import secrets
import uuid
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, event, func
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db.models import (
    Base, Node, PeerRequest, IntraLink, LGQuery, User, ASNIdentity, SystemSetting, new_uuid
)
from app.intra.config import (
    generate_listen_port,
    generate_link_local_address,
    intra_protocol_name,
)


def generate_wg_pubkey() -> str:
    return secrets.token_urlsafe(32)[:44]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def seed_database(clear_existing: bool = False):
    """Seed the database with comprehensive test data."""
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
            print("Clearing all existing data...")
            db.query(LGQuery).delete()
            db.query(IntraLink).delete()
            db.query(PeerRequest).delete()
            db.query(Node).delete()
            db.query(ASNIdentity).delete()
            db.query(User).delete()
            db.query(SystemSetting).delete()
            db.commit()
            print("  ✓ All tables cleared.")

        # ── System settings ──
        print("\nCreating system settings...")
        settings_data = [
            ("lla_base_network", "172.24.0.0", "Link-local address base network"),
            ("lla_subnet_prefix", "/24", "Link-local subnet prefix for peers"),
            ("intra_port_base", "41400", "Intra link listen port base"),
            ("intra_port_max", "44399", "Intra link listen port max"),
            ("default_asn", "AS65000", "Default local ASN"),
            ("asn_range_start", "AS4242420000", "Peer ASN range start"),
            ("asn_range_end", "AS4242429999", "Peer ASN range end"),
            ("owned_networks_v4", "172.20.0.0/14,172.24.0.0/14", "Owned IPv4 networks"),
            ("owned_networks_v6", "fd00::/8,fd86::/16", "Owned IPv6 networks"),
            ("peer_wg_mtu", "1420", "Default WireGuard MTU"),
            ("peer_bgp_extended", "true", "Enable extended BGP communities"),
            ("lg_rate_limit", "20", "LG rate limit per minute"),
            ("lg_rate_window", "60", "LG rate window seconds"),
        ]
        for key, value, desc in settings_data:
            existing = db.query(SystemSetting).filter(SystemSetting.key == key).one_or_none()
            if not existing:
                db.add(SystemSetting(key=key, value=value, description=desc))
        db.commit()
        print(f"  ✓ Created {len(settings_data)} system settings")

        # ── Users ──
        print("\nCreating users...")
        admin_user = db.query(User).filter(User.is_admin == True).first()
        if admin_user is None:
            admin_user = User(
                primary_asn=settings.local_asn or "AS65000",
                first_email="admin@autopeer.dev",
                is_admin=True,
                last_login_at=utcnow(),
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            print(f"  ✓ Created admin user: {admin_user.primary_asn}")

        # Create additional peer users
        peer_asns = [
            "AS65001", "AS65002", "AS65003", "AS65004", "AS65005",
            "AS65006", "AS65007", "AS65008", "AS65009", "AS65010",
            "AS65011", "AS65012",
        ]
        peer_users = {}
        for asn in peer_asns:
            existing = db.query(User).filter(User.primary_asn == asn).first()
            if not existing:
                user = User(
                    primary_asn=asn,
                    first_email=f"peer{asn[-3:]}@example.com",
                    is_admin=False,
                    last_login_at=utcnow() - timedelta(days=random.randint(1, 30)),
                )
                db.add(user)
                db.flush()
                db.add(ASNIdentity(user_id=user.id, asn=asn, authtype="kioubit"))
                peer_users[asn] = user
        db.commit()
        print(f"  ✓ Created {len(peer_users)} peer users")

        # ── Nodes ──
        print("\nCreating nodes...")
        node_defs = [
            # (name, location, url, asn, ipv4, ipv6, online)
            ("fra-01", "Frankfurt, DE", "fra01.autopeer.dev", "AS65001", "172.20.1.1/32", "fd00::1::1/128", True),
            ("fra-02", "Paris, FR", "fra02.autopeer.dev", "AS65008", "172.20.8.1/32", "fd00::8::1/128", True),
            ("deu-01", "Berlin, DE", "deu01.autopeer.dev", "AS65009", "172.20.9.1/32", "fd00::9::1/128", False),
            ("nld-01", "Amsterdam, NL", "nld01.autopeer.dev", "AS65002", "172.20.2.1/32", "fd00::2::1/128", True),
            ("gbr-01", "London, UK", "gbr01.autopeer.dev", "AS65007", "172.20.7.1/32", "fd00::7::1/128", True),
            ("can-01", "Toronto, CA", "can01.autopeer.dev", "AS65010", "172.20.10.1/32", "fd00::10::1/128", False),
            ("usa-01", "New York, US", "usa01.autopeer.dev", "AS65003", "172.20.3.1/32", "fd00::3::1/128", True),
            ("usa-02", "Los Angeles, US", "usa02.autopeer.dev", "AS65004", "172.20.4.1/32", "fd00::4::1/128", False),
            ("sgp-01", "Singapore", "sgp01.autopeer.dev", "AS65006", "172.20.6.1/32", "fd00::6::1/128", True),
            ("jpn-01", "Tokyo, JP", "jpn01.autopeer.dev", "AS65005", "172.20.5.1/32", "fd00::5::1/128", True),
        ]

        nodes = []
        for name, location, url, asn, ipv4, ipv6, online in node_defs:
            existing = db.query(Node).filter(Node.name == name).first()
            if existing:
                nodes.append(existing)
                continue

            last_seen = utcnow() if online else utcnow() - timedelta(hours=random.randint(1, 48))
            system_status = {
                "cpu": random.randint(2, 35) if online else 0,
                "memory": random.randint(20, 60) if online else 0,
                "uptime_hours": random.randint(100, 5000) if online else 0,
                "bird_protocols": random.randint(5, 20) if online else 0,
                "wireguard_peers": random.randint(2, 15) if online else 0,
            }

            node = Node(
                id=new_uuid(),
                name=name,
                location=location,
                url=url,
                token=secrets.token_hex(32),
                wg_public_key=generate_wg_pubkey(),
                asn=asn,
                dn42_ipv4=ipv4,
                dn42_ipv6=ipv6,
                enabled=True,
                last_seen_at=last_seen,
                system_status_json=str(system_status).replace("'", '"'),
            )
            db.add(node)
            nodes.append(node)

        db.commit()
        print(f"  ✓ Created {len(nodes)} nodes")

        # ── Peers ──
        print("\nCreating peers...")
        nodes.sort(key=lambda n: n.name)

        peer_configs = []
        # Self peers (admin's own ASN on each node)
        for node in nodes:
            peer_configs.append({
                "asn": settings.local_asn or "AS65000",
                "user_id": admin_user.id,
                "node": node,
                "deploy_status": "deployed",
                "status": "approved",
                "created_days_ago": random.randint(1, 60),
            })

        # Peer user peers across nodes
        for i, (asn, user) in enumerate(peer_users.items()):
            node = nodes[i % len(nodes)]
            deploy_status = random.choices(
                ["deployed", "failed", "not_deployed"],
                weights=[70, 15, 15],
                k=1
            )[0]
            peer_configs.append({
                "asn": asn,
                "user_id": user.id,
                "node": node,
                "deploy_status": deploy_status,
                "status": "approved" if deploy_status != "not_deployed" else "pending",
                "created_days_ago": random.randint(1, 90),
            })

        # Generate additional peers for density
        for i in range(30):
            asn_num = 4242430000 + i
            asn = f"AS{asn_num}"
            node = nodes[i % len(nodes)]
            deploy_status = random.choices(
                ["deployed", "failed", "not_deployed"],
                weights=[60, 20, 20],
                k=1
            )[0]
            peer_configs.append({
                "asn": asn,
                "user_id": admin_user.id,
                "node": node,
                "deploy_status": deploy_status,
                "status": "approved" if deploy_status != "not_deployed" else "pending",
                "created_days_ago": random.randint(1, 120),
            })

        created_peers = 0
        for cfg in peer_configs:
            existing = db.query(PeerRequest).filter(
                PeerRequest.node_id == cfg["node"].id,
                PeerRequest.asn == cfg["asn"]
            ).first()
            if existing:
                continue

            days_ago = cfg["created_days_ago"]
            created_at = utcnow() - timedelta(days=days_ago)

            peer_idx = created_peers
            peer = PeerRequest(
                id=new_uuid(),
                user_id=cfg["user_id"],
                asn=cfg["asn"],
                node_id=cfg["node"].id,
                tunnel_type="wireguard",
                endpoint=f"peer{peer_idx + 1}.example.com:{51820 + (peer_idx % 100)}",
                wg_public_key=generate_wg_pubkey(),
                wg_mtu=1420,
                local_link_address="172.24.0.1/32",
                peer_link_address=f"172.24.{peer_idx // 256}.{(peer_idx % 256) + 1}/32",
                peer_dn42_ipv4=f"172.25.{peer_idx % 256}.{(peer_idx % 256) + 1}/32",
                peer_dn42_ipv6=f"fd86:116:{peer_idx}::1/128",
                bgp_extended=True,
                status=cfg["status"],
                deploy_status=cfg["deploy_status"],
                deploy_output="" if cfg["deploy_status"] == "deployed" else f"Error: connection timed out to {cfg['node'].url}" if cfg["deploy_status"] == "failed" else "",
                deployed_at=created_at if cfg["deploy_status"] == "deployed" else None,
                created_at=created_at,
                updated_at=created_at + timedelta(days=random.randint(0, days_ago)),
            )
            db.add(peer)
            created_peers += 1

            if created_peers % 25 == 0:
                db.commit()
                print(f"  Progress: {created_peers} peers...")

        db.commit()
        print(f"  ✓ Created {created_peers} peers")

        # ── Intra Links ──
        print("\nCreating intra links...")
        intra_pairs = []
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                if len(intra_pairs) >= 15:
                    break
                intra_pairs.append((nodes[i], nodes[j]))
            if len(intra_pairs) >= 15:
                break

        created_links = 0
        used_ports: set[int] = set()
        used_names: set[str] = set()

        for src_node, dst_node in intra_pairs:
            # Forward direction
            for _ in range(2):  # 2 links per pair
                for attempt in range(5):
                    link_id = new_uuid()
                    protocol_name = intra_protocol_name(link_id)
                    if protocol_name not in used_names:
                        used_names.add(protocol_name)
                        break
                else:
                    continue

                for attempt in range(10):
                    port = generate_listen_port()
                    if port not in used_ports:
                        used_ports.add(port)
                        break
                else:
                    continue

                direction = "forward" if _ == 0 else "reverse"
                link = IntraLink(
                    id=link_id,
                    node_id=src_node.id,
                    remote_node_id=dst_node.id,
                    label=f"{src_node.name}-{dst_node.name}-{direction}",
                    protocol_name=protocol_name,
                    remote_public_key=dst_node.wg_public_key or generate_wg_pubkey(),
                    remote_endpoint=dst_node.url,
                    listen_port=port,
                    link_local_address=generate_link_local_address(),
                    deploy_status="deployed",
                    deploy_output="OK",
                    deployed_at=utcnow() - timedelta(days=random.randint(1, 60)),
                )
                db.add(link)
                created_links += 1

        # Also add some failed intra links
        for i in range(3):
            src_node = nodes[i]
            dst_node = nodes[(i + 3) % len(nodes)]
            for attempt in range(5):
                link_id = new_uuid()
                protocol_name = intra_protocol_name(link_id)
                if protocol_name not in used_names:
                    used_names.add(protocol_name)
                    break
            else:
                continue
            for attempt in range(10):
                port = generate_listen_port()
                if port not in used_ports:
                    used_ports.add(port)
                    break
            else:
                continue

            link = IntraLink(
                id=link_id,
                node_id=src_node.id,
                remote_node_id=dst_node.id,
                label=f"{src_node.name}-{dst_node.name}-fail",
                protocol_name=protocol_name,
                remote_public_key=dst_node.wg_public_key or generate_wg_pubkey(),
                remote_endpoint=dst_node.url,
                listen_port=port,
                link_local_address=generate_link_local_address(),
                deploy_status="failed",
                deploy_output=f"Error: cannot reach {dst_node.url}: connection refused",
            )
            db.add(link)
            created_links += 1

        db.commit()
        print(f"  ✓ Created {created_links} intra links")

        # ── LG Queries ──
        print("\nCreating LG query audit log...")
        query_types = ["ping", "trace", "route", "bird_protocols", "bird_route", "bgp_summary"]
        query_targets = [
            "wiki.dn42", "172.20.0.1", "1.1.1.0/24", "ibgp_0a1b2c3d",
            "4242420000", "fd00::1::1/128", "AS65000",
        ]

        created_queries = 0
        for i in range(40):
            node = nodes[i % len(nodes)]
            qtype = query_types[i % len(query_types)]
            target = query_targets[i % len(query_targets)]
            qok = random.random() > 0.2
            days_ago = random.randint(0, 30)

            q = LGQuery(
                user_id=admin_user.id if random.random() > 0.3 else None,
                node_id=node.id,
                query_type=qtype,
                target=target,
                ok=qok,
                result=f"Query {'succeeded' if qok else 'failed'} for {qtype} {target} on {node.name}",
                created_at=utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23)),
            )
            db.add(q)
            created_queries += 1

            if created_queries % 20 == 0:
                db.commit()

        db.commit()
        print(f"  ✓ Created {created_queries} LG queries")

        # ── Verification ──
        print("\n" + "=" * 60)
        print("VERIFICATION")
        print("=" * 60)

        counts = {
            "Users": db.query(func.count(User.id)).scalar(),
            "Admin users": db.query(func.count(User.id)).filter(User.is_admin == True).scalar(),
            "Nodes": db.query(func.count(Node.id)).scalar(),
            "Nodes enabled": db.query(func.count(Node.id)).filter(Node.enabled == True).scalar(),
            "Peers": db.query(func.count(PeerRequest.id)).scalar(),
            "Peers deployed": db.query(func.count(PeerRequest.id)).filter(PeerRequest.deploy_status == "deployed").scalar(),
            "Peers failed": db.query(func.count(PeerRequest.id)).filter(PeerRequest.deploy_status == "failed").scalar(),
            "Peers pending": db.query(func.count(PeerRequest.id)).filter(PeerRequest.deploy_status == "not_deployed").scalar(),
            "Intra links": db.query(func.count(IntraLink.id)).scalar(),
            "Intra deployed": db.query(func.count(IntraLink.id)).filter(IntraLink.deploy_status == "deployed").scalar(),
            "Intra failed": db.query(func.count(IntraLink.id)).filter(IntraLink.deploy_status == "failed").scalar(),
            "LG queries": db.query(func.count(LGQuery.id)).scalar(),
            "LG queries ok": db.query(func.count(LGQuery.id)).filter(LGQuery.ok == True).scalar(),
            "LG queries failed": db.query(func.count(LGQuery.id)).filter(LGQuery.ok == False).scalar(),
        }

        for label, count in counts.items():
            print(f"  {label}: {count}")

        # Check for duplicate ports
        port_counts = db.query(IntraLink.listen_port, func.count(IntraLink.id)).group_by(IntraLink.listen_port).having(func.count(IntraLink.id) > 1).all()
        if port_counts:
            print(f"\n  ⚠ DUPLICATE PORTS: {len(port_counts)} ports reused!")
        else:
            print(f"\n  ✓ All intra link ports are unique")

        # Per-node distribution
        print("\nPer-node distribution:")
        for node in nodes:
            peer_count = db.query(func.count(PeerRequest.id)).filter(PeerRequest.node_id == node.id).scalar() or 0
            link_count = db.query(func.count(IntraLink.id)).filter(IntraLink.node_id == node.id).scalar() or 0
            if node.last_seen_at:
                last_seen_dt = node.last_seen_at
                if last_seen_dt.tzinfo is None:
                    last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
                delta = utcnow() - last_seen_dt
                last_seen = "online" if delta.total_seconds() < 3600 else "offline"
            else:
                last_seen = "offline"
            print(f"  {node.name:12s} | {node.location:20s} | {last_seen:7s} | peers: {peer_count:3d} | links: {link_count:2d}")

    finally:
        db.close()


if __name__ == "__main__":
    clear_existing = "--clear-existing" in sys.argv
    seed_database(clear_existing=clear_existing)
