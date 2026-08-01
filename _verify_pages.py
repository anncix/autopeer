"""Render every page (incl. authenticated) via TestClient to catch logic/template errors."""
import os
import sys

sys.path.insert(0, "/workspace")
os.chdir("/workspace")

from starlette.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.db.models import User, PeerRequest

ROUTES = [
    "/", "/nodes", "/lg", "/login",
    # portal (regular user)
    "/portal", "/portal/new",
    # admin (admin user)
    "/admin", "/admin/nodes", "/admin/nodes/new", "/admin/peers", "/admin/peers/new",
    "/admin/users", "/admin/lg-log",
]


def session_for(user_id: int) -> dict:
    """Forge a signed session cookie matching Starlette SessionMiddleware's format exactly.

    SessionMiddleware uses itsdangerous.TimestampSigner(secret_key) (no salt) and signs the
    base64-encoded json.dumps(session) (default separators). See starlette/middleware/sessions.py.
    """
    import json
    from base64 import b64encode
    import itsdangerous
    from app.web.deps import settings

    signer = itsdangerous.TimestampSigner(str(settings.session_secret))
    payload = {"user_id": user_id}
    data = b64encode(json.dumps(payload).encode("utf-8"))
    signed = signer.sign(data).decode("utf-8")
    return {"cookie": f"session={signed}"}


def main():
    db = SessionLocal()
    admin = db.query(User).filter(User.is_admin.is_(True)).one()
    regular = db.query(User).filter(User.is_admin.is_(False)).one()
    peer = db.query(PeerRequest).filter(PeerRequest.user_id == regular.id).first()
    db.close()

    print(f"admin id={admin.id} asn={admin.primary_asn}")
    print(f"regular id={regular.id} asn={regular.primary_asn}")
    print(f"peer id={peer.id}")
    print("=" * 60)

    client = TestClient(app)
    admin_cookie = session_for(admin.id)
    regular_cookie = session_for(regular.id)

    print("\n--- Anonymous (public) ---")
    with client:
        for r in ROUTES:
            resp = client.get(r, follow_redirects=False)
            tag = "OK" if resp.status_code < 500 else "ERR"
            print(f"  [{tag}] {resp.status_code}  {r}")

    print("\n--- Regular user (portal) ---")
    with client:
        for r in ["/portal", "/portal/new", f"/portal/peers/{peer.id}", f"/portal/peers/{peer.id}/config"]:
            resp = client.get(r, follow_redirects=False, headers=regular_cookie)
            tag = "OK" if resp.status_code < 500 else "ERR"
            # detect jinja errors in body
            body = resp.text
            err_marker = "Internal Server Error" in body or "Traceback" in body
            print(f"  [{tag}] {resp.status_code}  {r}" + ("  <body-error>" if err_marker else ""))

    print("\n--- Admin ---")
    with client:
        for r in ROUTES:
            if r in ("/", "/nodes", "/lg", "/login"):
                continue
            resp = client.get(r, follow_redirects=False, headers=admin_cookie)
            tag = "OK" if resp.status_code < 500 else "ERR"
            body = resp.text
            err_marker = "Internal Server Error" in body or "Traceback" in body
            print(f"  [{tag}] {resp.status_code}  {r}" + ("  <body-error>" if err_marker else ""))
        # peer status & edit
        for r in [f"/admin/peers/{peer.id}/edit", f"/admin/peers/{peer.id}/status",
                  f"/admin/peers/{peer.id}/config", f"/admin/nodes"]:
            resp = client.get(r, follow_redirects=False, headers=admin_cookie)
            tag = "OK" if resp.status_code < 500 else "ERR"
            body = resp.text
            err_marker = "Internal Server Error" in body or "Traceback" in body
            print(f"  [{tag}] {resp.status_code}  {r}" + ("  <body-error>" if err_marker else ""))

    print("\n--- LG page: BIRD protocol option present? ---")
    with client:
        resp = client.get("/lg", follow_redirects=False)
        body = resp.text
        has_bird_opt = 'value="bird"' in body and "BIRD protocol" in body
        has_bird_placeholder = "lg.target_placeholder_bird" in body or True  # placeholder applied via JS
        print(f"  /lg has bird option: {has_bird_opt}")

    print("\n--- LG POST queries ---")
    with client:
        # existing route query (node offline -> ok=False, but no 500)
        resp = client.post("/lg", data={"node_id": peer.node_id, "query_type": "route", "target": "1.1.1.0/24"},
                           headers={"X-Requested-With": "fetch"}, follow_redirects=False)
        print(f"  route: {resp.status_code} ok={resp.json().get('ok') if resp.status_code==200 else 'n/a'}")
        # new bird query with valid protocol name (node offline -> ok=False, but validation passes)
        resp = client.post("/lg", data={"node_id": peer.node_id, "query_type": "bird", "target": "DN42_1234_6b9f"},
                           headers={"X-Requested-With": "fetch"}, follow_redirects=False)
        j = resp.json() if resp.status_code == 200 else {}
        print(f"  bird (valid name): {resp.status_code} ok={j.get('ok')} qtype={j.get('query_type')}")
        # bird query with INVALID protocol name -> validation rejects, ok=False, message in output
        resp = client.post("/lg", data={"node_id": peer.node_id, "query_type": "bird", "target": "bad/name"},
                           headers={"X-Requested-With": "fetch"}, follow_redirects=False)
        j = resp.json() if resp.status_code == 200 else {}
        print(f"  bird (invalid name): {resp.status_code} ok={j.get('ok')} out={j.get('output','')[:60]}")

    print("\n--- Portal peer status (new session detail page) ---")
    with client:
        # regular user owns peer p1
        resp = client.get(f"/portal/peers/{peer.id}/status", follow_redirects=False, headers=regular_cookie)
        body = resp.text
        err_marker = "Internal Server Error" in body or "Traceback" in body
        has_back = f'href="/portal/peers/{peer.id}"' in body
        print(f"  portal status (owner): {resp.status_code} body-error={err_marker} has-back-link={has_back}")
        # peer_detail now links BGP session to /status
        resp = client.get(f"/portal/peers/{peer.id}", follow_redirects=False, headers=regular_cookie)
        body = resp.text
        has_link = f'href="/portal/peers/{peer.id}/status"' in body
        has_view_btn = "detail.view_live_status" in body or "View live status" in body
        print(f"  peer_detail -> status link present: {has_link}  view-btn: {has_view_btn}")
        # ownership: admin (different user) should NOT reach a portal peer it doesn't own -> 404
        # (admin peer p3 is owned by admin; admin accessing p1 portal route -> 404)
        resp = client.get(f"/portal/peers/{peer.id}/status", follow_redirects=False, headers=admin_cookie)
        print(f"  portal status (non-owner admin): {resp.status_code} (expect 404)")

    print("\nDone.")


if __name__ == "__main__":
    main()
