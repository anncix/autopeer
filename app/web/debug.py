"""Debug routes for local development and testing.

Provides admin login bypass and test data seeding endpoints.
These routes are ONLY for development/debugging and should NEVER be exposed in production.
"""

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.session import login_user
from app.config import get_settings
from app.db.models import (
    ASNIdentity,
    IntraLink,
    LGQuery,
    Node,
    PeerRequest,
    User,
    utcnow,
)
from app.db.session import get_db

router = APIRouter()

settings = get_settings()

NODE_SEED_CONFIGS = [
    {"name": "fra-01", "location": "Frankfurt, DE", "url": "fra01.autopeer.dev", "asn": "AS65001"},
    {"name": "nld-01", "location": "Amsterdam, NL", "url": "nld01.autopeer.dev", "asn": "AS65002"},
    {"name": "usa-01", "location": "New York, US", "url": "usa01.autopeer.dev", "asn": "AS65003"},
    {"name": "usa-02", "location": "Los Angeles, US", "url": "usa02.autopeer.dev", "asn": "AS65004"},
    {"name": "jpn-01", "location": "Tokyo, JP", "url": "jpn01.autopeer.dev", "asn": "AS65005"},
    {"name": "sgp-01", "location": "Singapore", "url": "sgp01.autopeer.dev", "asn": "AS65006"},
    {"name": "gbr-01", "location": "London, UK", "url": "gbr01.autopeer.dev", "asn": "AS65007"},
    {"name": "fra-02", "location": "Paris, FR", "url": "fra02.autopeer.dev", "asn": "AS65008"},
    {"name": "deu-01", "location": "Berlin, DE", "url": "deu01.autopeer.dev", "asn": "AS65009"},
    {"name": "can-01", "location": "Toronto, CA", "url": "can01.autopeer.dev", "asn": "AS65010"},
]


@router.get("/debug/admin-login")
def debug_admin_login(
    request: Request,
    asn: str = "AS65000",
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """Debug endpoint: create (or reuse) an admin user with the given ASN and log them in.

    Bypasses the normal Kioubit/Telegram auth flow. Useful for UI development
    without needing a real dn42 ASN. Defaults to AS65000 in the private ASN range.
    """
    user = db.query(User).filter(User.primary_asn == asn).one_or_none()
    if user is None:
        user = User(primary_asn=asn, is_admin=True)
        db.add(user)
        db.flush()
    else:
        user.is_admin = True

    user.first_email = user.first_email or f"debug@{asn.lower()}.dn42"
    user.last_login_at = utcnow()

    identity = ASNIdentity(
        user_id=user.id,
        asn=asn,
        mnt_json='["DEMO-AS"]',
        effective_mnt="DEMO-AS",
        allowed4_json='["10.0.0.0/8"]',
        allowed6_json='["fd00::/8"]',
        authtype="debug",
    )
    db.add(identity)
    db.commit()
    db.refresh(user)

    login_user(request, user)

    _ensure_seed_data(db)

    return RedirectResponse("/portal", status_code=303)


@router.post("/debug/seed")
def debug_seed(request: Request, db: Session = Depends(get_db)) -> RedirectResponse:
    """Populate the database with 10 sample nodes, users, and peer relationships for testing.

    Safe to call multiple times — existing records are reused (matched by name).
    """
    _ensure_seed_data(db)
    return RedirectResponse("/", status_code=303)


def _ensure_seed_data(db: Session) -> None:
    """Create 10 sample nodes, demo users, and peer relationships if they don't already exist."""

    admin_user = db.query(User).filter(User.primary_asn == "AS65000").one_or_none()
    if admin_user is None:
        admin_user = User(primary_asn="AS65000", is_admin=True, first_email="admin@autopeer.dev")
        db.add(admin_user)
        db.flush()

    peer_user = db.query(User).filter(User.primary_asn == "AS650011").one_or_none()
    if peer_user is None:
        peer_user = User(primary_asn="AS650011", is_admin=False, first_email="peer@autopeer.dev")
        db.add(peer_user)
        db.flush()

    db.add(ASNIdentity(user_id=admin_user.id, asn="AS65000", authtype="debug"))
    db.add(ASNIdentity(user_id=peer_user.id, asn="AS650011", authtype="debug"))

    nodes = []
    for idx, cfg in enumerate(NODE_SEED_CONFIGS):
        node = db.query(Node).filter(Node.name == cfg["name"]).one_or_none()
        if node is None:
            node = Node(
                name=cfg["name"],
                location=cfg["location"],
                url=cfg["url"],
                token=secrets.token_urlsafe(32),
                wg_public_key="debug-wg-pub-" + cfg["name"],
                asn=cfg["asn"],
                dn42_ipv4=f"172.20.{idx + 1}.1/32",
                dn42_ipv6=f"fd00::{idx + 1}::1/128",
                enabled=True,
                last_seen_at=utcnow(),
                system_status_json='{"cpu":"2%","mem":"1.2GB","uptime":"15d"}',
            )
            db.add(node)
        nodes.append(node)

    db.commit()

    sample_statuses = ["active", "active", "pending", "disabled"]
    sample_deploy_statuses = ["deployed", "deployed", "not_deployed", "failed"]
    peer_wg_keys = [
        "yGPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhg=",
        "xHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhx=",
        "zHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhz=",
        "aHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqha=",
        "bHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhb=",
        "cHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhc=",
    ]

    for i, node in enumerate(nodes[:6]):
        existing = db.query(PeerRequest).filter(
            PeerRequest.user_id == peer_user.id,
            PeerRequest.node_id == node.id,
        ).one_or_none()
        if existing is None:
            idx = i % len(sample_statuses)
            peer_req = PeerRequest(
                user_id=peer_user.id,
                asn="AS650011",
                node_id=node.id,
                endpoint=f"peer-{i}.autopeer.dev:51820",
                wg_public_key=peer_wg_keys[i],
                wg_mtu=1420,
                local_link_address="fe80::1260",
                peer_link_address="fe80::1234",
                peer_dn42_ipv4=f"172.20.{i + 100}.4/32",
                peer_dn42_ipv6=f"fd42:{i + 1}::1/128",
                bgp_extended=True,
                status=sample_statuses[idx],
                deploy_status=sample_deploy_statuses[idx],
                deploy_output="wg-quick up: OK\nbirdc configure: OK" if sample_deploy_statuses[idx] == "deployed" else "",
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(peer_req)

    for i, node in enumerate(nodes[:3]):
        existing = db.query(PeerRequest).filter(
            PeerRequest.user_id == admin_user.id,
            PeerRequest.node_id == node.id,
        ).one_or_none()
        if existing is None:
            admin_peer = PeerRequest(
                user_id=admin_user.id,
                asn="AS65000",
                node_id=node.id,
                endpoint=f"admin-peer-{i}.autopeer.dev:51820",
                wg_public_key=peer_wg_keys[i + 3] if i + 3 < len(peer_wg_keys) else peer_wg_keys[0],
                wg_mtu=1420,
                local_link_address="fe80::2468",
                peer_link_address="fe80::9999",
                peer_dn42_ipv4=f"172.30.{i + 1}.1/32",
                peer_dn42_ipv6=f"fd99:{i + 1}::1/128",
                bgp_extended=False,
                status="active",
                deploy_status="deployed",
                deploy_output="wg-quick up: OK\nbirdc configure: OK",
                created_at=utcnow(),
                updated_at=utcnow(),
            )
            db.add(admin_peer)

    db.add_all([
        LGQuery(node_id=nodes[0].id, user_id=peer_user.id, query_type="ping", target="172.20.0.1", ok=True, result="4 packets received, 0% loss"),
        LGQuery(node_id=nodes[1].id, user_id=peer_user.id, query_type="route", target="1.1.1.0/24", ok=True, result="1.1.1.0/24 via 172.20.0.1 on direct"),
        LGQuery(node_id=nodes[0].id, user_id=None, query_type="trace", target="wiki.dn42", ok=True, result="traceroute complete"),
        LGQuery(node_id=nodes[0].id, user_id=None, query_type="ping", target="8.8.8.8", ok=False, result="node is busy"),
    ])

    intra_link_configs = [
        {"label": "can-fra", "local_idx": 9, "remote_idx": 0, "protocol": "ibgp_can_fra", "port": 41401, "lla": "fe80::14:0001/64", "pubkey": "yGPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhg=", "deploy": "deployed", "output": "wg-quick up: OK\nbirdc configure: OK\nOSPF adjacency FULL"},
        {"label": "fra-nld", "local_idx": 0, "remote_idx": 1, "protocol": "ibgp_fra_nld", "port": 41402, "lla": "fe80::14:0002/64", "pubkey": "xHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhx=", "deploy": "deployed", "output": "wg-quick up: OK\nbirdc configure: OK"},
        {"label": "fra-gbr", "local_idx": 0, "remote_idx": 6, "protocol": "ibgp_fra_gbr", "port": 41403, "lla": "fe80::14:0003/64", "pubkey": "zHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhz=", "deploy": "failed", "output": "wg-quick up: FAIL\nwireguard: interface already exists"},
        {"label": "nld-usa1", "local_idx": 1, "remote_idx": 2, "protocol": "ibgp_nld_usa1", "port": 41404, "lla": "fe80::14:0004/64", "pubkey": "aHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqha=", "deploy": "not_deployed", "output": ""},
        {"label": "jpn-sgp", "local_idx": 4, "remote_idx": 5, "protocol": "ibgp_jpn_sgp", "port": 41405, "lla": "fe80::14:0005/64", "pubkey": "bHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhb=", "deploy": "deployed", "output": "wg-quick up: OK\nbirdc configure: OK"},
        {"label": "deu-fra2", "local_idx": 8, "remote_idx": 7, "protocol": "ibgp_deu_fra2", "port": 41406, "lla": "fe80::14:0006/64", "pubkey": "cHPtJlZW25oRZVqcRrMbjnNIQXe1Fz3wMgRQY7jWqhc=", "deploy": "deployed", "output": "wg-quick up: OK\nbirdc configure: OK\nOSPF adjacency FULL"},
    ]

    for cfg in intra_link_configs:
        existing = db.query(IntraLink).filter(IntraLink.protocol_name == cfg["protocol"]).one_or_none()
        if existing is None:
            local_node = nodes[cfg["local_idx"]]
            remote_node = nodes[cfg["remote_idx"]]
            link = IntraLink(
                node_id=local_node.id,
                remote_node_id=remote_node.id,
                label=cfg["label"],
                protocol_name=cfg["protocol"],
                remote_public_key=cfg["pubkey"],
                remote_endpoint=f"{remote_node.url}:{cfg['port']}",
                listen_port=cfg["port"],
                link_local_address=cfg["lla"],
                deploy_status=cfg["deploy"],
                deploy_output=cfg["output"],
                deployed_at=utcnow() if cfg["deploy"] == "deployed" else None,
            )
            db.add(link)

    db.commit()
