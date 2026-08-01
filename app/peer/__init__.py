"""Peer lifecycle management package.

Exports the main entry points used by the web routes, admin panel, and Telegram bot.

These re-exports are loaded lazily (PEP 562) so that importing a leaf submodule such as
``app.peer.validation`` does not eagerly pull in ``app.peer.service`` — which would otherwise
create a circular import (``app.db.models`` -> ``app.peer.validation`` -> ``app.peer.__init__``
-> ``app.peer.service`` -> ``app.db.models``). Callers using ``from app.peer import create_peer``
are unaffected.
"""

__all__ = [
    "create_peer",
    "delete_peer",
    "deploy_peer_request",
    "find_peer_on_node",
    "preview_peer",
    "teardown_peer_request",
    "update_peer",
]


def __getattr__(name: str):
    if name in __all__:
        from app.peer import service  # local import breaks the cycle at module load time
        return getattr(service, name)
    raise AttributeError(f"module 'app.peer' has no attribute {name!r}")

