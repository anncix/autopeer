"""Seed the autopeer DB with test data: nodes, users, peers, LG queries. Temporary test script."""
import os
import sys

sys.path.insert(0, "/workspace")
os.chdir("/workspace")

from app.db.init_db import create_schema
from app.db.models import ASNIdentity, LGQuery, Node, PeerRequest, User
from app.db.session import Base, SessionLocal, engine

# Start clean
Base.metadata.drop_all(bind=engine)
create_schema()

with SessionLocal() as db:
    admin = User(primary_asn="4242420000", is_admin=True, first_email="admin@example.org")
    regular = User(primary_asn="4242421234", is_admin=False, first_email="peer@example.org")
    db.add_all([admin, regular])
    db.flush()
    db.add(ASNIdentity(user_id=admin.id, asn="4242420000", authtype="kioubit"))
    db.add(ASNIdentity(user_id=regular.id, asn="4242421234", authtype="kioubit"))

    n1 = Node(
        name="fra1", location="Frankfurt, DE", url="198.51.100.10",
        asn="4242420000", dn42_ipv4="172.20.0.1", dn42_ipv6="fd00::1",
        token="node-fra1-token-1234567890abcdef", enabled=True,
        wg_public_key="yGPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhg=",
    )
    n2 = Node(
        name="sin1", location="Singapore, SG", url="203.0.113.20",
        asn="4242420000", dn42_ipv4="172.20.0.2", dn42_ipv6="fd00::2",
        token="node-sin1-token-abcdef1234567890", enabled=True,
        wg_public_key="xHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhx=",
    )
    n3 = Node(
        name="lax1", location="Los Angeles, US", url="203.0.113.99",
        asn="4242420000", dn42_ipv4="172.20.0.3", dn42_ipv6="fd00::3",
        token="node-lax1-token-0000000000aaaaaaaa", enabled=False,
        wg_public_key="zHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhz=",
    )
    db.add_all([n1, n2, n3])
    db.flush()

    p1 = PeerRequest(
        user_id=regular.id, asn="4242421234", node_id=n1.id,
        endpoint="203.0.113.55:51820", wg_public_key="abc1234567890abcdefghij+klmnopqrstuv+/xyz1234=",
        wg_mtu=1280, local_link_address="fe80::1260", peer_link_address="fe80::1234",
        peer_dn42_ipv4="172.20.123.4", peer_dn42_ipv6="fd42:1234::1", bgp_extended=True,
        status="approved", deploy_status="deployed", deploy_output="wg-quick up: OK\nbirdc configure: OK",
    )
    p2 = PeerRequest(
        user_id=regular.id, asn="4242421234", node_id=n2.id, endpoint="",
        wg_public_key="def1234567890abcdefghij+klmnopqrstuv+/xyz1234=", wg_mtu=1280,
        local_link_address="fe80::1260", peer_link_address="fe80::5678",
        peer_dn42_ipv4="172.20.123.4", peer_dn42_ipv6="fd42:1234::1", bgp_extended=True,
        status="pending", deploy_status="not_deployed", deploy_output="",
    )
    p3 = PeerRequest(
        user_id=admin.id, asn="4242420000", node_id=n1.id,
        endpoint="203.0.113.66:51820", wg_public_key="ghi1234567890abcdefghij+klmnopqrstuv+/xyz1234=",
        wg_mtu=1280, local_link_address="fe80::1260", peer_link_address="fe80::9999",
        peer_dn42_ipv4="172.20.99.99", peer_dn42_ipv6="fd42:99::1", bgp_extended=False,
        status="approved", deploy_status="failed", deploy_output="wg-quick up failed: exit status 1",
    )
    db.add_all([p1, p2, p3])
    db.flush()

    db.add_all([
        LGQuery(node_id=n1.id, user_id=regular.id, query_type="ping", target="172.20.0.1", ok=True, result="4 packets received, 0% loss"),
        LGQuery(node_id=n2.id, user_id=regular.id, query_type="route", target="1.1.1.0/24", ok=True, result="1.1.1.0/24 via 172.20.0.1 on direct"),
        LGQuery(node_id=n1.id, user_id=None, query_type="trace", target="wiki.dn42", ok=True, result="traceroute complete"),
        LGQuery(node_id=n1.id, user_id=None, query_type="ping", target="8.8.8.8", ok=False, result="node is busy"),
    ])
    db.commit()

    print("Seed complete")
    print(f"  users: {db.query(User).count()}")
    print(f"  nodes: {db.query(Node).count()}")
    print(f"  peers: {db.query(PeerRequest).count()}")
    print(f"  lg_queries: {db.query(LGQuery).count()}")
    print(f"  peer p1 id: {p1.id}")
    print(f"  protocol_name p1: DN42_1234_{p1.id[-4:]}")
