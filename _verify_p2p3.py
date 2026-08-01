"""Focused tests for the P2/P3 features added to admin.py:

  - P2: BGP flap detection page (`/admin/nodes/{id}/flap`) — renders even when the node agent is
    unreachable (the common case in CI), surfacing the error rather than 500-ing.
  - P2: bidirectional intra-link creation — `_provision_intra_link` is the shared helper used by
    both the forward and reverse directions; we exercise it directly to confirm validation +
    DB persistence + identical behaviour for both directions.
  - P3: progressive-enhancement JSON endpoints — `GET .../intra-links/json` returns the link list
    as JSON the frontend can re-render from, and `POST .../intra-links/api` accepts the same
    fields as the HTML form and returns `{ok, message, count}`. Validation failures return 400
    with a structured message instead of crashing.

Run:  ALLOW_INSECURE_DEFAULTS=1 python _verify_p2p3.py
"""
import json
import os
import sys

sys.path.insert(0, "/workspace")
os.chdir("/workspace")

from starlette.testclient import TestClient

# Seed first so the DB has nodes/users to test against. _seed_test runs at import time (it has no
# main() — the seed logic is module-level), so importing it side-effects the seed.
import _seed_test  # noqa: E402,F401  (seed runs on import)

from app.db.models import IntraLink, Node  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.web.deps import settings  # noqa: E402


def session_for(user_id: int) -> dict:
    """Forge a signed session cookie matching Starlette SessionMiddleware's format."""
    import itsdangerous
    from base64 import b64encode

    signer = itsdangerous.TimestampSigner(str(settings.session_secret))
    payload = {"user_id": user_id}
    data = b64encode(json.dumps(payload).encode("utf-8"))
    signed = signer.sign(data).decode("utf-8")
    return {"cookie": f"session={signed}"}


def main() -> int:
    db = SessionLocal()
    admin = db.query(__import__("app.db.models", fromlist=["User"]).User).filter_by(is_admin=True).one()
    fra1 = db.query(Node).filter_by(name="fra1").one()
    sin1 = db.query(Node).filter_by(name="sin1").one()
    db.close()

    admin_cookie = session_for(admin.id)
    client = TestClient(app)
    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        mark = "OK " if ok else "ERR"
        print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ""))
        if not ok:
            failures.append(label + (f": {detail}" if detail else ""))

    print("=" * 60)
    print("P2 — BGP flap detection page")
    print("=" * 60)
    with client:
        # Node agent is offline in CI — the page must render (200) and surface the connection
        # error rather than 500-ing. The template's `error` block handles this gracefully.
        resp = client.get(f"/admin/nodes/{fra1.id}/flap", headers=admin_cookie, follow_redirects=False)
        body = resp.text
        body_err = "Internal Server Error" in body or "Traceback" in body
        check("GET /flap returns < 500", resp.status_code < 500, f"status={resp.status_code}")
        check("GET /flap has no body traceback", not body_err)
        # The flap template's signature elements should be present (i18n keys for the summary).
        check("flap page renders summary", "admin.flap_total" in body or "Total events buffered" in body)

        # Non-existent node -> 404 (not 500).
        resp = client.get("/admin/nodes/does-not-exist/flap", headers=admin_cookie, follow_redirects=False)
        check("GET /flap unknown node -> 404", resp.status_code == 404, f"status={resp.status_code}")

        # Non-admin (anonymous) -> 403 (require_admin denies without redirecting to login).
        resp = client.get(f"/admin/nodes/{fra1.id}/flap", follow_redirects=False)
        check("GET /flap anonymous -> denied (403/redirect)",
              resp.status_code in (301, 302, 303, 403), f"status={resp.status_code}")

    print()
    print("=" * 60)
    print("P3 — intra-links JSON list endpoint")
    print("=" * 60)
    with client:
        # Empty list initially (seed does not create intra links). Must be JSON with `links` array
        # and `count` int — the frontend's refresh() depends on this exact shape.
        resp = client.get(f"/admin/nodes/{fra1.id}/intra-links/json", headers=admin_cookie)
        check("GET /intra-links/json -> 200", resp.status_code == 200, f"status={resp.status_code}")
        try:
            data = resp.json()
        except Exception as exc:  # noqa: BLE001
            check("GET /intra-links/json returns JSON", False, str(exc))
            data = {}
        else:
            check("JSON has links array", isinstance(data.get("links"), list))
            check("JSON has count int", isinstance(data.get("count"), int))
            check("count matches links length", data.get("count") == len(data.get("links") or []))

        # Unknown node -> 404.
        resp = client.get("/admin/nodes/nope/intra-links/json", headers=admin_cookie)
        check("GET /intra-links/json unknown node -> 404", resp.status_code == 404, f"status={resp.status_code}")

        # Anonymous -> denied (403, not 200 and not a JSON leak).
        resp = client.get(f"/admin/nodes/{fra1.id}/intra-links/json", follow_redirects=False)
        check("GET /intra-links/json anonymous -> denied (403/redirect)",
              resp.status_code in (301, 302, 303, 403), f"status={resp.status_code}")

    print()
    print("=" * 60)
    print("P3 — intra-links create API (validation + persistence)")
    print("=" * 60)
    # fra1 and sin1 both have wg_public_key in the seed, so a reverse link is possible.
    valid_pubkey = sin1.wg_public_key  # 44-char base64 from seed
    with client:
        # 1) Invalid: missing remote_public_key (and no remote_node_id to auto-fill from).
        resp = client.post(
            f"/admin/nodes/{fra1.id}/intra-links/api",
            json={"remote_node_id": "", "remote_public_key": "", "remote_endpoint": "",
                  "label": "", "deploy": False, "reverse": False},
            headers=admin_cookie,
        )
        check("POST /api missing pubkey -> 400", resp.status_code == 400, f"status={resp.status_code}")
        body = resp.json()
        check("POST /api missing pubkey returns ok=false", body.get("ok") is False)

        # 2) Valid: forward link only (no reverse). deploy=False so we don't need a live node agent.
        before = db.query(IntraLink).filter_by(node_id=fra1.id).count()
        resp = client.post(
            f"/admin/nodes/{fra1.id}/intra-links/api",
            json={"remote_node_id": "", "remote_public_key": valid_pubkey,
                  "remote_endpoint": "203.0.113.20:51820", "label": "fra1-sin1-test",
                  "deploy": False, "reverse": False},
            headers=admin_cookie,
        )
        check("POST /api valid forward -> 200", resp.status_code == 200, f"status={resp.status_code}")
        body = resp.json()
        check("POST /api valid forward returns ok=true", body.get("ok") is True, str(body.get("message")))
        check("POST /api valid forward returns count", isinstance(body.get("count"), int))
        after = db.query(IntraLink).filter_by(node_id=fra1.id).count()
        check("forward link persisted to DB", after == before + 1, f"before={before} after={after}")

        # 3) Bidirectional: forward on fra1 + reverse on sin1. deploy=False so no node agent needed.
        fra_before = db.query(IntraLink).filter_by(node_id=fra1.id).count()
        sin_before = db.query(IntraLink).filter_by(node_id=sin1.id).count()
        resp = client.post(
            f"/admin/nodes/{fra1.id}/intra-links/api",
            json={"remote_node_id": sin1.id, "remote_public_key": "",
                  "remote_endpoint": "", "label": "fra-sin-bidir",
                  "deploy": False, "reverse": True},
            headers=admin_cookie,
        )
        check("POST /api bidirectional -> 200", resp.status_code == 200, f"status={resp.status_code}")
        body = resp.json()
        check("bidirectional forward ok=true", body.get("ok") is True, str(body.get("message")))
        check("bidirectional has reverse_message", "reverse_message" in body)
        check("bidirectional reverse ok=true", body.get("reverse_ok") is True, str(body.get("reverse_message")))
        fra_after = db.query(IntraLink).filter_by(node_id=fra1.id).count()
        sin_after = db.query(IntraLink).filter_by(node_id=sin1.id).count()
        check("forward link created on fra1", fra_after == fra_before + 1,
              f"before={fra_before} after={fra_after}")
        check("reverse link created on sin1", sin_after == sin_before + 1,
              f"before={sin_before} after={sin_after}")

        # 4) Auto-fill from remote_node_id: the API should pull sin1's pubkey/endpoint when the
        # operator selects a remote node but leaves the manual fields blank.
        resp = client.post(
            f"/admin/nodes/{fra1.id}/intra-links/api",
            json={"remote_node_id": sin1.id, "remote_public_key": "",
                  "remote_endpoint": "", "label": "auto-fill-test",
                  "deploy": False, "reverse": False},
            headers=admin_cookie,
        )
        check("POST /api auto-fill from remote node -> 200", resp.status_code == 200,
              f"status={resp.status_code}")
        check("POST /api auto-fill ok=true", resp.json().get("ok") is True)

        # 5) Unknown node -> 404 (not 500).
        resp = client.post(
            "/admin/nodes/nope/intra-links/api",
            json={"remote_node_id": "", "remote_public_key": valid_pubkey,
                  "remote_endpoint": "", "label": "", "deploy": False, "reverse": False},
            headers=admin_cookie,
        )
        check("POST /api unknown node -> 404", resp.status_code == 404, f"status={resp.status_code}")

        # 6) JSON list now reflects the created links (count >= 2).
        resp = client.get(f"/admin/nodes/{fra1.id}/intra-links/json", headers=admin_cookie)
        data = resp.json()
        check("JSON list grew after creates", data.get("count", 0) >= 2, f"count={data.get('count')}")
        # Each serialised link must have the fields the frontend's renderIntraLinksTable reads.
        if data.get("links"):
            l = data["links"][0]
            expected = {"id", "protocol_name", "label", "remote_name",
                        "remote_endpoint", "listen_port", "link_local_address", "deploy_status"}
            missing = expected - set(l.keys())
            check("serialised link has all frontend fields", not missing, f"missing={missing}")

    print()
    print("=" * 60)
    print("P3 — _provision_intra_link shared helper (direct unit test)")
    print("=" * 60)
    # Confirm the shared helper produces identical validation for forward and reverse by calling it
    # directly — this is the contract that makes bidirectional creation safe.
    from app.web.admin import _provision_intra_link

    db = SessionLocal()
    try:
        # Invalid pubkey -> (None, False, msg)
        link, ok, msg = _provision_intra_link(
            db, settings, fra1, None, "not-a-valid-key", "", "bad", deploy=False
        )
        check("helper rejects invalid pubkey", link is None and ok is False, msg)
        # Valid forward
        link, ok, msg = _provision_intra_link(
            db, settings, fra1, sin1.id, valid_pubkey, "203.0.113.20:51820",
            "helper-forward", deploy=False
        )
        check("helper creates valid forward link", ok and link is not None, msg)
        check("helper assigns protocol_name", bool(link and link.protocol_name))
        check("helper assigns listen_port", bool(link and link.listen_port))
        check("helper assigns link_local_address", bool(link and link.link_local_address))
        # Valid reverse (same helper, swapped roles) — proves identical validation.
        rev_link, rev_ok, rev_msg = _provision_intra_link(
            db, settings, sin1, fra1.id, fra1.wg_public_key, fra1.url,
            "helper-reverse", deploy=False
        )
        check("helper creates valid reverse link", rev_ok and rev_link is not None, rev_msg)
        check("reverse link is on sin1", rev_link and rev_link.node_id == sin1.id)
    finally:
        db.close()

    print()
    print("=" * 60)
    if failures:
        print(f"FAILED: {len(failures)} check(s)")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
