"""Public pages and auth callbacks: fullscreen map, login/logout, Kioubit + Telegram auth."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.kioubit import KioubitAuthError, KioubitVerifier
from app.auth.service import consume_challenge, create_challenge, upsert_user_from_kioubit
from app.auth.session import current_user, login_user, logout_user
from app.db.session import get_db
from app.web.deps import build_map_data, render, settings

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Fullscreen network topology map — the sole public page.

    Pass ?demo=1 to force all enabled nodes online with mock latency for preview/testing.
    """
    demo = request.query_params.get("demo") in ("1", "true", "yes")
    mock = request.query_params.get("mock") in ("1", "true", "yes")
    map_data = build_map_data(db, demo=demo, mock=mock)
    return render(
        request,
        "map.html",
        map_data,
        user=current_user(request, db),
        active="map",
    )


@router.get("/map", response_class=HTMLResponse)
def map_page(request: Request) -> RedirectResponse:
    """Redirect /map to / (canonical URL for the fullscreen map)."""
    qs = request.url.query
    target = "/" + ("?" + qs if qs else "")
    return RedirectResponse(target, status_code=302)


@router.get("/nodes", response_class=HTMLResponse)
def nodes_page(request: Request) -> RedirectResponse:
    """Redirect /nodes to / (node directory removed)."""
    return RedirectResponse("/", status_code=302)


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
