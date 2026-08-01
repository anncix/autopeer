"""Intra-link deployment: build the WireGuard config and dispatch it to the node agent.

Mirrors app.peer.deploy but for internal (iBGP/OSPF backbone) links: only a WireGuard config is
sent (no BIRD snippet), via the ``intra.deploy`` / ``intra.remove`` commands.
"""
from typing import Any

from app.config import Settings
from app.db.models import IntraLink, Node, utcnow
from app.intra.config import build_intra_deploy_payload
from app.node_ws import NodeRequestError, request_node_sync


class IntraDeployError(Exception):
    """Raised when intra-link deployment prerequisites are missing or the node rejects config."""


def deploy_intra_link(
    link: IntraLink, node: Node, settings: Settings, timeout: float = 20.0
) -> dict[str, Any]:
    """Send an ``intra.deploy`` command to the node agent and return its response."""
    if not node.enabled:
        raise IntraDeployError("Node is disabled")
    if not link.remote_public_key.strip():
        raise IntraDeployError("Remote WireGuard public key is required before deployment")
    payload = build_intra_deploy_payload(link, node, settings)
    return request_node_sync(node, "intra.deploy", payload, timeout)


def remove_intra_link(link: IntraLink, node: Node, timeout: float = 20.0) -> dict[str, Any]:
    """Ask the node to tear down an intra link: bring the tunnel down and delete its config file."""
    payload = {"request_id": link.id, "protocol_name": link.protocol_name}
    return request_node_sync(node, "intra.remove", payload, timeout)


def apply_deploy_result(link: IntraLink, result: dict[str, Any]) -> None:
    """Write the deployment result back onto the link row in the current session."""
    ok = bool(result.get("ok", False))
    link.deploy_output = str(result.get("output", result))
    if ok:
        link.deploy_status = "deployed"
        link.deployed_at = utcnow()
    else:
        link.deploy_status = "failed"
        link.deployed_at = None
    link.updated_at = utcnow()
