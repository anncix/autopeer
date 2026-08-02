"""Service for managing system settings."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.db.models import SystemSetting


# Default settings with descriptions
DEFAULT_SETTINGS = {
    # LLA (Link-Local Address) rules
    "lla_base_network": {
        "value": "172.24.0.0",
        "description": "Base network for generating link-local addresses (LLA). Peers get /32 from this range.",
    },
    "lla_subnet_prefix": {
        "value": "24",
        "description": "Subnet prefix for LLA. Each peer gets a /32 from a /24 subnet derived from the ASN.",
    },

    # Intra link port range
    "intra_port_base": {
        "value": "41400",
        "description": "Base port for auto-assigned intra link listen ports.",
    },
    "intra_port_max": {
        "value": "44399",
        "description": "Maximum port for auto-assigned intra link listen ports.",
    },

    # ASN settings
    "default_asn": {
        "value": "",
        "description": "Default ASN for nodes when not individually set. Empty = use env LOCAL_ASN.",
    },
    "asn_range_start": {
        "value": "4242430000",
        "description": "Start of ASN range for auto-assigned peer ASNs.",
    },
    "asn_range_end": {
        "value": "4242439999",
        "description": "End of ASN range for auto-assigned peer ASNs.",
    },

    # Self-owned network blocks
    "owned_networks_v4": {
        "value": "[]",
        "description": "JSON array of self-owned IPv4 network blocks, e.g. [\"172.23.0.0/16\"].",
    },
    "owned_networks_v6": {
        "value": "[]",
        "description": "JSON array of self-owned IPv6 network blocks, e.g. [\"fd86:115::/48\"].",
    },

    # Peer settings
    "peer_wg_mtu": {
        "value": "1420",
        "description": "Default WireGuard MTU for new peers.",
    },
    "peer_bgp_extended": {
        "value": "true",
        "description": "Enable extended BGP communities by default for new peers.",
    },

    # Node settings
    "node_wg_key_required": {
        "value": "false",
        "description": "Require nodes to have a valid WireGuard public key before accepting peer requests.",
    },

    # Rate limiting
    "lg_rate_limit": {
        "value": "20",
        "description": "Max looking-glass queries per window per user.",
    },
    "lg_rate_window": {
        "value": "60",
        "description": "Rate limiting window in seconds for looking-glass queries.",
    },
}


def ensure_default_settings(db: Session) -> None:
    """Ensure all default settings exist in the database."""
    for key, config in DEFAULT_SETTINGS.items():
        existing = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if existing is None:
            db.add(SystemSetting(
                key=key,
                value=config["value"],
                description=config["description"],
            ))
    db.commit()


def get_setting(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a single setting value."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting is None:
        return default
    return setting.value


def get_setting_int(db: Session, key: str, default: int = 0) -> int:
    """Get a setting value as integer."""
    value = get_setting(db, key)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_setting_bool(db: Session, key: str, default: bool = False) -> bool:
    """Get a setting value as boolean."""
    value = get_setting(db, key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def get_setting_list(db: Session, key: str, default: Optional[list] = None) -> list:
    """Get a setting value as a list (stored as JSON)."""
    if default is None:
        default = []
    value = get_setting(db, key)
    if value is None:
        return default
    try:
        result = json.loads(value)
        if isinstance(result, list):
            return result
        return default
    except (json.JSONDecodeError, TypeError):
        return default


def get_all_settings(db: Session) -> list[dict[str, Any]]:
    """Get all settings, including defaults for missing ones."""
    ensure_default_settings(db)
    settings = db.query(SystemSetting).order_by(SystemSetting.key).all()
    return [
        {
            "key": s.key,
            "value": s.value,
            "description": s.description,
        }
        for s in settings
    ]


def update_setting(db: Session, key: str, value: str) -> SystemSetting:
    """Update or create a setting."""
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if setting is None:
        setting = SystemSetting(
            key=key,
            value=value,
            description=DEFAULT_SETTINGS.get(key, {}).get("description", ""),
        )
        db.add(setting)
    else:
        setting.value = value
    db.commit()
    db.refresh(setting)
    return setting


def update_settings_batch(db: Session, updates: dict[str, str]) -> None:
    """Update multiple settings at once."""
    for key, value in updates.items():
        update_setting(db, key, value)
