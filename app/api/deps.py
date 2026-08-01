"""Authentication dependencies for the JSON REST API (``/api/v1/*``).

These mirror the web (HTML) dependencies in ``app/web/deps.py`` but return JSON-friendly
errors instead of redirecting to /login or rendering an HTML error page. They reuse the
same session-backed ``current_user`` so a logged-in browser session works for the API too
(no separate token model needed yet); a future user-scoped API token can be added here
without touching the route handlers.

权限依赖: 与 HTML 端的 require_admin 对应,但回传 JSON 而非重定向/HTML。复用同一 session 的
current_user,故已登录的浏览器会话即可调用 API;未来如需 user-scoped API token,在此扩展即可,
无需改动路由处理器。
"""

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.auth.session import current_user
from app.db.models import User
from app.db.session import get_db


def require_api_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Any authenticated user. Raises 401 (not 403) when unauthenticated, because 401 is the
    HTTP-standard signal for "send credentials" — programmatic clients key off it to know whether
    to retry with auth. Browser sessions already carry the cookie, so this mainly affects curl/etc.
    任意已登录用户。未认证时回 401(而非 403),因为 401 是「请提供凭据」的标准信号——
    程序化客户端据此判断是否需重试带凭据。浏览器会话已带 cookie,主要影响 curl 等。
    """
    user = current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_api_admin(request: Request, db: Session = Depends(get_db)) -> User:
    """An admin user. Raises 403 with a JSON body — distinct from require_api_user's 401 so a
    client can tell "not logged in" (401) from "logged in but not allowed" (403).
    管理员。回 403 JSON——与 require_api_user 的 401 区分,让客户端能分辨
    「未登录」与「已登录但无权」。"""
    user = current_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
