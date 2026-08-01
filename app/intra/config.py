"""Configuration generation for internal (iBGP/OSPF backbone) WireGuard links.

An intra link tunnels between two of our own nodes. Unlike a dn42 peer (app.peer.config), an intra
link has no per-peer BGP snippet: routing between the linked nodes is handled by OSPF, whose area
config lives under /etc/bird/ospf/*.conf on the node (read back by the agent, not generated here).

Naming convention: ``ibgp_<4-hex>`` (9 chars) — within the 15-char Linux IFNAMSIZ limit, matches
the agent's safeNameRE, and distinct from the ``DN42_<4>_<4>`` dn42-peer names so the two never
collide on a node.

Port convention: ``414xx`` — base 41400 plus a random two-digit suffix (00–99).

Link-local address: ``fe80::14:<4-hex>/64`` — the ``14`` is fixed, the last 16 bits are random.

The private key never leaves the node: the generated config carries the
``{{WIREGUARD_PRIVATE_KEY}}`` placeholder, substituted by the agent at deploy time (same pattern as
dn42 peer deployment).
"""
from __future__ import annotations

import re
import secrets
from ipaddress import IPv6Address, ip_address

from app.config import Settings
from app.db.models import IntraLink, Node

# Base for the 414xx listen-port range; the last two digits are random.
INTRA_LISTEN_PORT_BASE = 41400
# Fixed prefix of the link-local host part: fe80::14:<random>.
INTRA_LLA_PREFIX = "fe80::14:"

# Hostname label per RFC 1123 (simplified): letters/digits/hyphens, not all-numeric-first/last.
_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)([A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)(\.[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$"
)


def intra_protocol_name(link_id: str) -> str:
    """Derive the ``ibgp_<4-hex>`` protocol/interface/file name from a link UUID.

    Uses the last 4 hex chars of the UUID (8 hex chars → first 4), lowercased, to stay short and
    stable across regenerations of the same link. Falls back to random hex if the id is too short.
    """
    hex_chars = "".join(c for c in link_id.lower() if c in "0123456789abcdef")
    suffix = hex_chars[:4] if len(hex_chars) >= 4 else secrets.token_hex(2)
    return f"ibgp_{suffix}"


def generate_listen_port() -> int:
    """Return a random port in the 41400–41499 range (414xx convention)."""
    return INTRA_LISTEN_PORT_BASE + secrets.randbelow(100)


def generate_link_local_address() -> str:
    """Return a random IPv6 link-local address ``fe80::14:<4-hex>/64``."""
    return f"{INTRA_LLA_PREFIX}{secrets.token_hex(2)}/64"


def normalize_intra_endpoint(value: str) -> str:
    """Validate an intra-link WireGuard endpoint.

    Unlike a dn42 peer endpoint (which may be blank — the peer dials us), an intra link endpoint
    is auto-filled from the remote node's bare public address (no port, since the node stores only
    a host). So this accepts three forms:

    * blank → "" (the rendered config then omits the ``Endpoint`` line)
    * bare host (IPv4 / IPv6 / domain) — as stored on a Node
    * ``host:port`` (or ``[ipv6]:port``) — the full WireGuard endpoint form

    In all non-blank cases it rejects control characters and whitespace so a pasted value can never
    inject extra wg-quick directives (e.g. a newline + ``PostUp``) into the generated config.
    """
    value = (value or "").strip()
    if not value:
        return ""
    if len(value) > 255:
        raise ValueError("Endpoint is too long")
    for ch in value:
        if ord(ch) < 33 or ord(ch) > 126:
            raise ValueError("Endpoint must not contain spaces or control characters")

    # Bracketed IPv6 literal, optionally with :port — e.g. [2001:db8::1] or [2001:db8::1]:51820.
    if value.startswith("[") and "]" in value:
        host, _, rest = value[1:].partition("]")
        try:
            IPv6Address(host)
        except ValueError as exc:
            raise ValueError("Endpoint IPv6 address is invalid") from exc
        if rest:
            if not rest.startswith(":"):
                raise ValueError("Endpoint must be in [ipv6]:port form")
            port = rest[1:]
            if not port.isdigit() or not 1 <= int(port) <= 65535:
                raise ValueError("Endpoint port must be between 1 and 65535")
        return value

    # host:port (exactly one colon, and it's not a bare IPv6 which has ≥2 colons).
    if value.count(":") == 1:
        host, _, port = value.rpartition(":")
        if not host or not port:
            raise ValueError("Endpoint must be in host:port form")
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("Endpoint port must be between 1 and 65535")
        _validate_host(host)
        return value

    # Bare host (no port): IPv4, IPv6, or domain — matches the Node.url storage form.
    _validate_host(value)
    return value


def _validate_host(host: str) -> None:
    """Raise ValueError unless ``host`` is a valid IPv4, IPv6, or domain name."""
    try:
        ip_address(host)  # accepts IPv4 and IPv6
        return
    except ValueError:
        pass
    if not _HOSTNAME_RE.fullmatch(host):
        raise ValueError("Endpoint host must be a valid IPv4, IPv6, or domain")


def render_intra_wireguard_config(
    link: IntraLink,
    node: Node,
    private_key_placeholder: str,
) -> str:
    """Render the wg-quick config for an intra link, deployed on ``node`` (node A).

    Follows the operator-specified template: [Interface] carries the local private key (as a
    placeholder substituted by the agent), the listen port, Table=off, the link-local Address, and
    a PostUp that disables IPv6 autoconf on the interface. [Peer] carries the remote public key,
    the remote endpoint, and the dn42 + link-local AllowedIPs.
    """
    endpoint_line = f"Endpoint = {link.remote_endpoint}\n" if link.remote_endpoint.strip() else ""
    return f"""# Generated by dn42 Autopeer for intra link {link.id}
# Node A: {node.name} -> remote {link.remote_endpoint or '(manual)'}
# Interface: {link.protocol_name}  ListenPort: {link.listen_port}

[Interface]
PrivateKey = {private_key_placeholder}
ListenPort = {link.listen_port}
Table = off
Address = {link.link_local_address}
PostUp = sysctl -w net.ipv6.conf.%i.autoconf=0

[Peer]
{endpoint_line}PublicKey = {link.remote_public_key}
AllowedIPs = 10.0.0.0/8, 172.20.0.0/14, 172.31.0.0/16, fd00::/8, fe00::/8, ff02::5
"""


def build_intra_deploy_payload(
    link: IntraLink, node: Node, settings: Settings
) -> dict[str, str]:
    """Assemble the ``intra.deploy`` payload sent to the node agent.

    Mirrors app.peer.deploy.build_deploy_payload but carries only the WireGuard config (no BIRD
    snippet), matching the agent's IntraDeployRequest shape.
    """
    return {
        "request_id": link.id,
        "protocol_name": link.protocol_name,
        "wireguard_config": render_intra_wireguard_config(
            link, node, settings.wireguard_private_key_placeholder
        ),
    }
