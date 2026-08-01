"""Versioned REST API surface (``/api/v1/*``).

Aggregates the resource routers into one v1 APIRouter that main.py mounts. Keeping the v1 routers
in a subpackage lets a future v2 coexist without touching v1 handlers.

版本化 REST API 表面。将各资源 router 聚合成一个 v1 APIRouter 供 main.py 挂载。把 v1 router 放在
子套件中,未来 v2 可并存而不动 v1 处理器。
"""

from fastapi import APIRouter

from app.api.v1.admin import router as admin_router
from app.api.v1.nodes import admin_router as nodes_admin_router
from app.api.v1.nodes import public_router as nodes_public_router
from app.api.v1.peers import router as peers_router

router = APIRouter()
router.include_router(peers_router)
router.include_router(nodes_public_router)
router.include_router(nodes_admin_router)
router.include_router(admin_router)
