from typing import Any

from app.db.models import Node
from app.lg.validation import validate_query_type, validate_target
from app.node_ws import request_node


class NodeClient:
    def __init__(self, timeout: float = 12.0) -> None:
        self.timeout = timeout

    async def query(self, node: Node, query_type: str, target: str = "") -> dict[str, Any]:
        if not node.enabled:
            raise ValueError("Node is disabled")
        query_type = validate_query_type(query_type)
        target = validate_target(query_type, target)
        return await request_node(node, f"lg.{query_type}", {"target": target}, self.timeout)

    async def peer_status(self, node: Node, protocol_name: str) -> dict[str, Any]:
        """Fetch one peer's full, unmodified BIRD and WireGuard state.

        Returned verbatim — the admin live-status page shows the complete command output. The
        portal peer-detail page and the bot's ``/listpeers`` condense it to key info at their own
        call sites via ``summarize_peer_bird`` / ``summarize_wireguard``.
        """
        if not node.enabled:
            raise ValueError("Node is disabled")
        return await request_node(
            node,
            "peers.status",
            {"protocol_name": protocol_name},
            self.timeout,
        )

    async def ospf_neighbors(self, node: Node) -> dict[str, Any]:
        """Fetch OSPF neighbor sessions via ``birdc show ospf neighbor`` (the "birdc s o n" form).

        BIRD2 unifies IPv4/IPv6 OSPF into one instance, so a single call surfaces both v4 and v6
        neighbors. Output is returned verbatim for the intra-link UI to render.
        """
        if not node.enabled:
            raise ValueError("Node is disabled")
        return await request_node(node, "intra.ospf.neighbors", {}, self.timeout)

    async def ospf_configs(self, node: Node) -> dict[str, Any]:
        """Read back the OSPF area snippet files (/etc/bird/ospf/*.conf) from the node.

        Returns ``{"ok": bool, "files": [{"name", "content"}], "error": str}``. Read-only on the
        agent side; the UI displays the area/interface topology (dummy stub, wg cost/type ptp).
        """
        if not node.enabled:
            raise ValueError("Node is disabled")
        return await request_node(node, "intra.ospf.configs", {}, self.timeout)

    async def dummy_interfaces(self, node: Node) -> dict[str, Any]:
        """List dummy network interfaces via ``ip -o -d addr show type dummy``.

        The dn42 dummy interface (carrying the node's own dn42 IPs) is typically referenced as a
        stub in the OSPF area config; the UI shows it for context.
        """
        if not node.enabled:
            raise ValueError("Node is disabled")
        return await request_node(node, "intra.dummy", {}, self.timeout)

    async def flap_check(self, node: Node) -> dict[str, Any]:
        """Poll ``birdc show protocols`` and diff against the agent's last snapshot.

        The agent keeps an in-memory map of BGP protocol states; each call records any transitions
        (up<->start/down, appeared, gone) into a ring buffer and returns the new events plus current
        states. The backend calls this on demand (admin opens the flap page) — there is no
        background poller, so detection granularity depends on how often this is invoked.
        """
        if not node.enabled:
            raise ValueError("Node is disabled")
        return await request_node(node, "flap.check", {}, self.timeout)

    async def flap_events(self, node: Node) -> dict[str, Any]:
        """Return the agent's buffered BGP flap history (no birdc call, just a memory read)."""
        if not node.enabled:
            raise ValueError("Node is disabled")
        return await request_node(node, "flap.events", {}, self.timeout)
