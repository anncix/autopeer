"""Public pages and auth callbacks: home, nodes, login/logout, Kioubit + Telegram auth."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.kioubit import KioubitAuthError, KioubitVerifier
from app.auth.service import consume_challenge, create_challenge, upsert_user_from_kioubit
from app.auth.session import current_user, login_user, logout_user
from app.db.models import Node, PeerRequest
from app.db.session import get_db
from app.node_ws import node_runtime_context
from app.web.deps import query_enabled_nodes, render, settings

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Landing page: intro, a peering guide, and the live status of every enabled node."""
    node_count = db.query(func.count(Node.id)).scalar() or 0
    peer_count = db.query(func.count(PeerRequest.id)).scalar() or 0
    deployed_count = db.query(func.count(PeerRequest.id)).filter(PeerRequest.deploy_status == "deployed").scalar() or 0
    return render(
        request,
        "home.html",
        {
            "stats_nodes": node_count,
            "stats_peers": peer_count,
            "stats_deployed": deployed_count,
        },
        user=current_user(request, db),
        active="home",
    )


@router.get("/nodes", response_class=HTMLResponse)
def nodes_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Public node directory: all nodes with their live status."""
    nodes = db.query(Node).order_by(Node.name).all()
    runtime = node_runtime_context(nodes)
    nodes_online = sum(1 for item in runtime.values() if item["online"])
    nodes_total = len(nodes)
    nodes_enabled = sum(1 for n in nodes if n.enabled)
    return render(
        request,
        "nodes.html",
        {
            "nodes": nodes,
            "node_runtime": runtime,
            "nodes_online": nodes_online,
            "nodes_total": nodes_total,
            "nodes_enabled": nodes_enabled,
        },
        user=current_user(request, db),
        active="nodes",
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    challenge = create_challenge(db, purpose="web")
    return render(
        request,
        "login.html",
        {
            "return_url": f"{settings.base_url}/auth/kioubit/callback",
            "token": challenge.token,
        },
        user=current_user(request, db),
    )


@router.get("/logout")
def logout(request: Request) -> RedirectResponse:
    logout_user(request)
    return RedirectResponse("/", status_code=303)


@router.get("/auth/kioubit/callback")
def kioubit_callback(
    request: Request,
    params: str,
    signature: str,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    verifier = KioubitVerifier(settings.kioubit_public_key_path, settings.auth_domain)
    try:
        data = verifier.verify(params=params, signature=signature)
        consume_challenge(db, data.get("user_token", ""), purpose="web")
        user = upsert_user_from_kioubit(db, data, settings)
    except (KioubitAuthError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    login_user(request, user)
    return RedirectResponse("/portal", status_code=303)


@router.get("/telegram/auth", response_class=HTMLResponse)
def telegram_auth_page(
    request: Request,
    token: str,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return render(
        request,
        "telegram_auth.html",
        {
            "return_url": f"{settings.base_url}/telegram/auth?token={token}",
            "token": token,
        },
        user=current_user(request, db),
    )
