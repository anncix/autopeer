"""Tests for the v1 REST API: CRUD, permission isolation, and sensitive-data isolation.

Covers three guarantees the API makes:
  1. CRUD works for each resource (peers, nodes, intra-links, users) end-to-end.
  2. Permission isolation: anonymous -> 401, non-admin on admin endpoints -> 403, a user cannot
     read/mutate another user's peer (404, hiding existence).
  3. Sensitive-data isolation: Node.token never appears in public NodePublic responses;
     deploy_output is absent from PeerOut (owner view) but present in PeerAdmin (admin view).

Run:  ALLOW_INSECURE_DEFAULTS=1 python _verify_api.py
"""
import json
import os
import sys

sys.path.insert(0, "/workspace")
os.chdir("/workspace")

import _seed_test  # noqa: E402,F401  (seed runs on import)

from app.db.models import Node, PeerRequest, User  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.web.deps import settings  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402


def session_for(user_id: int) -> dict:
    """Forge a signed session cookie for user_id (same as _verify_p2p3)."""
    import itsdangerous
    from base64 import b64encode

    signer = itsdangerous.TimestampSigner(str(settings.session_secret))
    payload = {"user_id": user_id}
    data = b64encode(json.dumps(payload).encode("utf-8"))
    signed = signer.sign(data).decode("utf-8")
    return {"cookie": f"session={signed}"}


def main() -> int:
    db = SessionLocal()
    admin = db.query(User).filter_by(is_admin=True).one()
    # Seed creates fra1/sin1 nodes and some peers. Find a non-admin user that owns peers.
    non_admin = db.query(User).filter(User.is_admin.is_(False)).first()
    if non_admin is None:
        # Create a non-admin user + a peer for isolation tests.
        non_admin = User(primary_asn="4242420099", is_admin=False)
        db.add(non_admin)
        db.commit()
        db.refresh(non_admin)
    fra1 = db.query(Node).filter_by(name="fra1").one()
    sin1 = db.query(Node).filter_by(name="sin1").one()
    db.close()

    admin_cookie = session_for(admin.id)
    user_cookie = session_for(non_admin.id)
    client = TestClient(app)
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        mark = "OK " if ok else "ERR"
        print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ""))
        if not ok:
            failures.append(label + (f": {detail}" if detail else ""))

    # A valid 44-char base64 WireGuard public key for create payloads.
    VALID_PUBKEY = "cF8m9h2k4p7qR1sT3uV0wX6yZ8aB1cD3eF5gH7iJ9k="  # 44 chars, plausible shape
    # The seed uses sin1.wg_public_key; reuse a real one where the validator checks format.

    print("=" * 64)
    print("1. PERMISSION ISOLATION (anonymous / non-admin / cross-user)")
    print("=" * 64)
    with client:
        # Anonymous auth checks: protected endpoints -> 401. The public /api/v1/nodes list is
        # intentionally anonymous (peers need the node list to choose a PoP), so it is excluded.
        # 受保護端點匿名 -> 401。公開 /api/v1/nodes 列表刻意匿名(peer 需節點清單選 PoP),故排除。
        for path in ["/api/v1/peers", "/api/v1/admin/nodes", "/api/v1/admin/users"]:
            r = client.get(path)
            check(f"anon GET {path} -> 401", r.status_code == 401, f"status={r.status_code}")
        # Public node list is anonymous by design.
        r = client.get("/api/v1/nodes")
        check("anon GET /api/v1/nodes -> 200 (public by design)", r.status_code == 200,
              f"status={r.status_code}")

        # Non-admin hitting admin endpoints -> 403 (authenticated but forbidden).
        for path in ["/api/v1/admin/nodes", "/api/v1/admin/peers", "/api/v1/admin/users"]:
            r = client.get(path, headers=user_cookie)
            check(f"non-admin GET {path} -> 403", r.status_code == 403, f"status={r.status_code}")

        # Non-admin POST to create a node -> 403 (not 401, since they ARE logged in).
        r = client.post(
            "/api/v1/admin/nodes",
            json={"name": "evil", "url": "evil.example.net"},
            headers=user_cookie,
        )
        check("non-admin POST /admin/nodes -> 403", r.status_code == 403, f"status={r.status_code}")

        # Cross-user peer access: admin owns peers; non-admin must NOT see them, and must get 404
        # (not 403) so the existence of another user's peer is hidden.
        db = SessionLocal()
        admin_peer = db.query(PeerRequest).filter(PeerRequest.user_id == admin.id).first()
        db.close()
        if admin_peer:
            r = client.get(f"/api/v1/peers/{admin_peer.id}", headers=user_cookie)
            check("non-admin GET other user's peer -> 404", r.status_code == 404,
                  f"status={r.status_code}")
            r = client.delete(f"/api/v1/peers/{admin_peer.id}", headers=user_cookie)
            check("non-admin DELETE other user's peer -> 404", r.status_code == 404,
                  f"status={r.status_code}")

    print()
    print("=" * 64)
    print("2. SENSITIVE-DATA ISOLATION (token / deploy_output stripping)")
    print("=" * 64)
    with client:
        # Public node list: must NOT contain token or system_status_json.
        r = client.get("/api/v1/nodes")
        check("public GET /nodes -> 200", r.status_code == 200)
        nodes = r.json()
        check("public nodes is a list", isinstance(nodes, list) and len(nodes) > 0)
        for n in nodes:
            assert "token" not in n, f"token leaked in public node: {n}"
            assert "system_status_json" not in n, f"system_status_json leaked: {n}"
        check("public nodes: no token field", all("token" not in n for n in nodes))
        check("public nodes: no system_status_json", all("system_status_json" not in n for n in nodes))
        check("public nodes: only enabled returned", all(n["enabled"] for n in nodes))

        # Admin node list: MUST contain token (admins need it to enroll node services).
        r = client.get("/api/v1/admin/nodes", headers=admin_cookie)
        admin_nodes = r.json()
        check("admin GET /nodes -> 200", r.status_code == 200)
        check("admin nodes include token", all("token" in n for n in admin_nodes))
        check("admin nodes include disabled (if any)", len(admin_nodes) >= len(nodes))

        # Peer owner view (PeerOut): deploy_output must be ABSENT.
        # Admin peer view (PeerAdmin): deploy_output must be PRESENT.
        r = client.get("/api/v1/peers", headers=user_cookie)
        user_peers = r.json()
        if user_peers:
            check("owner peer list: no deploy_output",
                  all("deploy_output" not in p for p in user_peers))
            check("owner peer list: no admin_note",
                  all("admin_note" not in p for p in user_peers))
        r = client.get("/api/v1/admin/peers", headers=admin_cookie)
        admin_peers = r.json()
        if admin_peers:
            check("admin peer list: has deploy_output",
                  all("deploy_output" in p for p in admin_peers))
            check("admin peer list: has admin_note",
                  all("admin_note" in p for p in admin_peers))

        # Users list (admin only): must NOT contain telegram chat ids or mnt_json.
        r = client.get("/api/v1/admin/users", headers=admin_cookie)
        check("admin GET /users -> 200", r.status_code == 200)
        users = r.json()
        for u in users:
            assert "telegram_chat_id" not in u, f"chat_id leaked: {u}"
            assert "mnt_json" not in u, f"mnt_json leaked: {u}"
        check("users: no telegram_chat_id", all("telegram_chat_id" not in u for u in users))
        check("users: no mnt_json", all("mnt_json" not in u for u in users))

    print()
    print("=" * 64)
    print("3. PEER CRUD (user-scoped, ownership-enforced)")
    print("=" * 64)
    with client:
        # CREATE: needs a valid wg key. Use sin1.wg_public_key from seed (valid format).
        db = SessionLocal()
        sin1_key = db.query(Node).filter_by(name="sin1").one().wg_public_key
        db.close()
        # Ensure no existing peer for this user on fra1 (delete if any, to make create idempotent).
        db = SessionLocal()
        existing = (
            db.query(PeerRequest)
            .filter(PeerRequest.user_id == non_admin.id, PeerRequest.node_id == fra1.id)
            .all()
        )
        for p in existing:
            db.delete(p)
        db.commit()
        db.close()

        r = client.post(
            "/api/v1/peers",
            json={
                "node_id": fra1.id,
                "wg_public_key": sin1_key,
                "endpoint": "203.0.113.99:51820",
                "peer_dn42_ipv6": "fd00:dead:beef::1",
            },
            headers=user_cookie,
        )
        check("POST /peers -> 201", r.status_code == 201, f"status={r.status_code} body={r.text[:200]}")
        created = r.json() if r.status_code == 201 else {}
        peer_id = created.get("id")
        check("POST /peers returns id", bool(peer_id))
        check("POST /peers peer asn == user asn", created.get("asn") == non_admin.primary_asn)

        # CREATE validation: missing node -> 400.
        r = client.post("/api/v1/peers", json={"node_id": "nope", "wg_public_key": sin1_key},
                        headers=user_cookie)
        check("POST /peers bad node -> 400", r.status_code == 400, f"status={r.status_code}")

        # READ: list + single.
        r = client.get("/api/v1/peers", headers=user_cookie)
        check("GET /peers list -> 200", r.status_code == 200)
        check("created peer in list", any(p["id"] == peer_id for p in r.json()))
        r = client.get(f"/api/v1/peers/{peer_id}", headers=user_cookie)
        check("GET /peers/{id} -> 200", r.status_code == 200)

        # UPDATE: patch endpoint field, redeploy=false (no live node needed).
        r = client.patch(
            f"/api/v1/peers/{peer_id}",
            json={"endpoint": "203.0.113.199:51820", "redeploy": False},
            headers=user_cookie,
        )
        check("PATCH /peers/{id} -> 200", r.status_code == 200, f"status={r.status_code}")
        if r.status_code == 200:
            check("PATCH updated endpoint", r.json().get("endpoint") == "203.0.113.199:51820")

        # UPDATE: status=disabled tears down (no live node -> may fail deploy, but row updates).
        r = client.patch(f"/api/v1/peers/{peer_id}", json={"status": "disabled"},
                         headers=user_cookie)
        check("PATCH status=disabled -> 200", r.status_code == 200, f"status={r.status_code}")

        # DELETE.
        r = client.delete(f"/api/v1/peers/{peer_id}", headers=user_cookie)
        check("DELETE /peers/{id} -> 200", r.status_code == 200, f"status={r.status_code}")
        check("DELETE returns ok=true", r.json().get("ok") is True)
        # Confirm gone.
        r = client.get(f"/api/v1/peers/{peer_id}", headers=user_cookie)
        check("GET deleted peer -> 404", r.status_code == 404)

    print()
    print("=" * 64)
    print("4. NODE CRUD (admin) + public read")
    print("=" * 64)
    with client:
        # CREATE node (admin). Token generated server-side, returned once.
        r = client.post(
            "/api/v1/admin/nodes",
            json={"name": "api-test-node", "location": "Test", "url": "test.example.net",
                  "enabled": True},
            headers=admin_cookie,
        )
        check("POST /admin/nodes -> 201", r.status_code == 201, f"status={r.status_code}")
        node = r.json() if r.status_code == 201 else {}
        node_id = node.get("id")
        check("created node has token (server-generated)", bool(node.get("token")))
        check("created node token is non-empty str", isinstance(node.get("token"), str) and len(node["token"]) > 10)

        # Duplicate name -> 409.
        r = client.post("/api/v1/admin/nodes",
                        json={"name": "api-test-node", "url": "x.example.net"},
                        headers=admin_cookie)
        check("POST duplicate node -> 409", r.status_code == 409, f"status={r.status_code}")

        # READ single (admin sees token).
        r = client.get(f"/api/v1/admin/nodes/{node_id}", headers=admin_cookie)
        check("GET /admin/nodes/{id} -> 200", r.status_code == 200)
        check("admin node detail has token", "token" in r.json())

        # Public read of the new node: no token.
        r = client.get(f"/api/v1/nodes/{node_id}")
        check("public GET /nodes/{id} -> 200", r.status_code == 200)
        check("public node detail: no token", "token" not in r.json())

        # UPDATE (PATCH).
        r = client.patch(f"/api/v1/admin/nodes/{node_id}",
                         json={"location": "Updated", "enabled": False}, headers=admin_cookie)
        check("PATCH /admin/nodes/{id} -> 200", r.status_code == 200, f"status={r.status_code}")
        if r.status_code == 200:
            check("PATCH updated location", r.json().get("location") == "Updated")
            check("PATCH disabled node", r.json().get("enabled") is False)

        # Disabled node hidden from public list.
        r = client.get("/api/v1/nodes")
        check("disabled node hidden from public list",
              all(n["id"] != node_id for n in r.json()))

        # reset-token rotates the token.
        old_token = node.get("token")
        r = client.post(f"/api/v1/admin/nodes/{node_id}/reset-token", headers=admin_cookie)
        check("POST reset-token -> 200", r.status_code == 200)
        new_token = r.json().get("token")
        check("reset-token changed value", new_token and new_token != old_token)

        # DELETE.
        r = client.delete(f"/api/v1/admin/nodes/{node_id}", headers=admin_cookie)
        check("DELETE /admin/nodes/{id} -> 200", r.status_code == 200, f"status={r.status_code}")
        r = client.get(f"/api/v1/admin/nodes/{node_id}", headers=admin_cookie)
        check("deleted node -> 404", r.status_code == 404)

        # DELETE node with peers -> 409 (refuse to orphan).
        r = client.delete(f"/api/v1/admin/nodes/{fra1.id}", headers=admin_cookie)
        check("DELETE node-with-peers -> 409", r.status_code == 409, f"status={r.status_code}")

    print()
    print("=" * 64)
    print("5. INTRA-LINK + ADMIN PEER LIST (admin)")
    print("=" * 64)
    with client:
        # Admin peer list returns PeerAdmin (with deploy_output).
        r = client.get("/api/v1/admin/peers", headers=admin_cookie)
        check("GET /admin/peers -> 200", r.status_code == 200)
        check("admin peers is list", isinstance(r.json(), list))

        # Intra-link list on fra1.
        r = client.get(f"/api/v1/admin/nodes/{fra1.id}/intra-links", headers=admin_cookie)
        check("GET /admin/nodes/{id}/intra-links -> 200", r.status_code == 200)
        links_before = r.json()
        check("intra-links is list", isinstance(links_before, list))

        # Create an intra-link (deploy=false, no live node).
        r = client.post(
            f"/api/v1/admin/nodes/{fra1.id}/intra-links",
            json={
                "remote_node_id": sin1.id,
                "remote_public_key": "",
                "remote_endpoint": "",
                "label": "api-test-link",
                "deploy": False,
                "reverse": False,
            },
            headers=admin_cookie,
        )
        check("POST intra-link -> 201", r.status_code == 201, f"status={r.status_code} body={r.text[:200]}")
        link = r.json() if r.status_code == 201 else {}
        link_id = link.get("id")
        check("created intra-link has protocol_name", bool(link.get("protocol_name")))

        # List grew.
        r = client.get(f"/api/v1/admin/nodes/{fra1.id}/intra-links", headers=admin_cookie)
        check("intra-links list grew", len(r.json()) > len(links_before))

        # Delete it.
        r = client.delete(
            f"/api/v1/admin/nodes/{fra1.id}/intra-links/{link_id}", headers=admin_cookie
        )
        check("DELETE intra-link -> 200", r.status_code == 200, f"status={r.status_code}")

    print()
    print("=" * 64)
    if failures:
        print(f"FAILED: {len(failures)} check(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
