"""Condense verbose ``birdc``/``wg`` status output into one or two lines of key info.

These run server-side so the web looking glass and the Telegram bot show the same concise
summaries — is the BGP session up? if not, why? is the WireGuard tunnel handshaking? — instead of
the full raw command dumps. If the output does not match the expected shape (an error string, an
empty body, an unfamiliar format), the original text is returned capped to a few lines so the
reason something is down is never hidden.

將冗長的 birdc／wg 狀態輸出濃縮為一兩行關鍵資訊(BGP 是否建立?否則原因為何?WireGuard 是否有
握手?),於伺服器端執行,使網頁 looking glass 與 Telegram bot 顯示一致的精簡摘要。當輸出不符
預期格式時(錯誤訊息、空白、未知格式),回傳裁切後的原文,避免隱藏異常原因。
"""

import json
import logging
import re
import sys
import time
import traceback
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Production toggle: set BIRD_PROTO_LOG_LEVEL=INFO to disable detailed DEBUG logs.
# When False, only WARNING/ERROR level events are logged.
_PROTO_LOG_DEBUG = True

# ---------------------------------------------------------------------------
# Log helper: generates a structured debug payload for each parsing step.
# ---------------------------------------------------------------------------
def _log_step(step: int, label: str, *, before: Optional[dict] = None,
              after: Optional[dict] = None, success: bool = True,
              note: str = "") -> None:
    """Emit a structured DEBUG log line for one parsing step.

    Parameters
    ----------
    step : int
        Monotonically increasing step number (1-based).
    label : str
        Human-readable description of the step.
    before : dict or None
        Snapshot of relevant input *before* the step.
    after : dict or None
        Snapshot of relevant output *after* the step.
    success : bool
        True if the step produced the expected result.
    note : str
        Free-form annotation (e.g. "regex did not match", "empty channel list").
    """
    if not _PROTO_LOG_DEBUG:
        return
    payload = {
        "step": step,
        "label": label,
        "success": success,
    }
    if before is not None:
        payload["before"] = before
    if after is not None:
        payload["after"] = after
    if note:
        payload["note"] = note
    logger.debug("[BIRD_PROTO] %s", json.dumps(payload, ensure_ascii=False, default=str))

# A channel's "Routes: X imported, Y filtered, Z exported, W preferred" line.
_ROUTES_RE = re.compile(r"(\d+)\s+imported.*?(\d+)\s+exported")


def _capped(text: str, *, max_lines: int = 6, max_chars: int = 400) -> str:
    """The trimmed text capped to a few lines/chars — the fallback when parsing fails."""
    text = (text or "").strip()
    if not text:
        return "(no output)"
    lines = text.splitlines()
    clipped = "\n".join(lines[:max_lines])
    if len(lines) > max_lines or len(clipped) > max_chars:
        clipped = clipped[:max_chars].rstrip() + " …"
    return clipped


def summarize_peer_bird(output: str) -> str:
    """Summarize ``birdc show protocols all <name>`` for one peer: state + routes, or the reason.

    Established → ``Established · routes <imp> in / <exp> out`` (summed across channels); otherwise
    ``<state> — <Last error>`` so a down session shows why.
    """
    text = output or ""
    state_match = re.search(r"BGP state:\s*(\S+)", text)
    if not state_match:
        return _capped(text)
    state = state_match.group(1)
    if state.lower() == "established":
        pairs = _ROUTES_RE.findall(text)
        if pairs:
            imported = sum(int(imp) for imp, _ in pairs)
            exported = sum(int(exp) for _, exp in pairs)
            return f"Established · routes {imported} in / {exported} out"
        return "Established"
    error = re.search(r"Last error:\s*(.+)", text)
    reason = error.group(1).strip() if error else ""
    return f"{state} — {reason}" if reason else state


def parse_bird_protocols_all(output: str) -> dict:
    """Parse ``birdc show protocols all <name>`` output into structured data.
    
    Returns a dict with keys: protocol_name, description, state, bgp_state,
    bgp_last_state, bgp_last_error, neighbor_id, connect_time, last_change,
    channels (list of v4/v6 channel dicts with their bgp_state and routes),
    routes_imported, routes_exported, routes_filtered, raw.
    
    Logging: Debug-level logs are emitted for each parsing step when
    ``_PROTO_LOG_DEBUG`` is True (default).  Each step logs:
      - step number and label
      - before/after snapshots of relevant data
      - success flag and optional note
    WARNING / ERROR level logs are always emitted for failures.
    Performance timing (elapsed_ms) is included in the final step log.
    """
    _start_time = time.perf_counter()

    # ── Step 0: Input validation & logging ──────────────────────────────
    _log_step(
        0, "input_validation",
        before={
            "output_length": len(output or ""),
            "has_content": bool((output or "").strip()),
        },
        note=f"output_preview={(output or '')[:150]!r}",
    )

    try:
        text = (output or "").strip()
        if not text:
            _log_step(
                1, "empty_input_check",
                success=False,
                note="Input is empty or only whitespace — returning error",
            )
            return {"error": "empty output", "raw": ""}

        # Split lines once for multi-line analysis
        lines = text.splitlines()
        _log_step(
            1, "input_preprocessing",
            after={
                "char_count": len(text),
                "line_count": len(lines),
                "first_line": lines[0][:120] if lines else "",
                "has_protocol_header": "protocol" in (lines[0] if lines else ""),
            },
        )

        # ── Step 2: Initialise result dict ───────────────────────────
        result: dict = {
            "protocol_name": "",
            "description": "",
            "state": "",
            "bgp_state": "",
            "bgp_last_state": "",
            "bgp_last_error": "",
            "neighbor_id": "",
            "connect_time": "",
            "last_change": "",
            "channels": [],
            "routes_imported": 0,
            "routes_exported": 0,
            "routes_filtered": 0,
            "raw": text,
        }
        _log_step(2, "result_dict_initialized", after={"keys": list(result.keys())})

        # ── Step 3: Extract protocol name ───────────────────────────
        before = {"first_line": lines[0][:100] if lines else ""}
        m = re.match(r'protocol\s+(\S+)', text)
        if m:
            result["protocol_name"] = m.group(1)
        _log_step(
            3, "protocol_name_extraction",
            before=before,
            after={"protocol_name": result["protocol_name"]},
            success=bool(result["protocol_name"]),
            note="regex matched" if result["protocol_name"] else "regex did not match",
        )

        # ── Step 4: Extract description ─────────────────────────────
        before = {"search_pattern": "Description:\\s*(.+)"}
        m = re.search(r'Description:\s*(.+)', text)
        if m:
            result["description"] = m.group(1).strip()
        _log_step(
            4, "description_extraction",
            before=before,
            after={"description": result["description"][:100]},
            success=bool(result["description"]),
            note="regex matched" if result["description"] else "description not found",
        )

        # ── Step 5: Extract BGP state ───────────────────────────────
        before = {"search_pattern": "BGP state:\\s*(\\S+)"}
        m = re.search(r'BGP state:\s*(\S+)', text)
        if m:
            result["bgp_state"] = m.group(1)
            result["state"] = m.group(1).lower()
        _log_step(
            5, "bgp_state_extraction",
            before=before,
            after={"bgp_state": result["bgp_state"], "state": result["state"]},
            success=bool(result["bgp_state"]),
            note="established_connection" if result["bgp_state"].lower() == "established"
                 else ("non_established" if result["bgp_state"] else "not_found"),
        )

        # ── Step 6: Extract BGP last state ──────────────────────────
        before = {"search_pattern": "BGP last state:\\s*(.+)"}
        m = re.search(r'BGP last state:\s*(.+)', text)
        if m:
            result["bgp_last_state"] = m.group(1).strip()
        _log_step(
            6, "bgp_last_state_extraction",
            before=before,
            after={"bgp_last_state": result["bgp_last_state"]},
            success=bool(result["bgp_last_state"]),
            note="found" if result["bgp_last_state"] else "field missing",
        )

        # ── Step 7: Extract BGP last error ──────────────────────────
        before = {"search_pattern": "BGP last error:\\s*(.+)"}
        m = re.search(r'BGP last error:\s*(.+)', text)
        if m:
            result["bgp_last_error"] = m.group(1).strip()
        _log_step(
            7, "bgp_last_error_extraction",
            before=before,
            after={"bgp_last_error": result["bgp_last_error"]},
            success=bool(result["bgp_last_error"]),
            note="error_found" if result["bgp_last_error"] and result["bgp_last_error"].lower() != "none"
                 else ("no_error" if result["bgp_last_error"].lower() == "none" else "field missing"),
        )

        # ── Step 8: Extract neighbor ID ─────────────────────────────
        before = {"search_pattern": "BGP neighbor ID:\\s*(\\S+)"}
        m = re.search(r'BGP neighbor ID:\s*(\S+)', text)
        if m:
            result["neighbor_id"] = m.group(1)
        _log_step(
            8, "neighbor_id_extraction",
            before=before,
            after={"neighbor_id": result["neighbor_id"]},
            success=bool(result["neighbor_id"]),
            note="found" if result["neighbor_id"] else "field missing",
        )

        # ── Step 9: Extract connect time ────────────────────────────
        before = {"search_pattern": "Connect time:\\s*(.+)"}
        m = re.search(r'Connect time:\s*(.+)', text)
        if m:
            result["connect_time"] = m.group(1).strip()
        _log_step(
            9, "connect_time_extraction",
            before=before,
            after={"connect_time": result["connect_time"]},
            success=bool(result["connect_time"]),
            note="found" if result["connect_time"] else "field missing",
        )

        # ── Step 10: Extract last state change ───────────────────────
        before = {"search_pattern": "Last state change:\\s*(.+)"}
        m = re.search(r'Last state change:\s*(.+)', text)
        if m:
            result["last_change"] = m.group(1).strip()
        _log_step(
            10, "last_state_change_extraction",
            before=before,
            after={"last_change": result["last_change"]},
            success=bool(result["last_change"]),
            note="found" if result["last_change"] else "field missing",
        )

        # ── Step 11: Extract route statistics ────────────────────────
        routes_imported = 0
        routes_exported = 0
        routes_filtered = 0

        routes_section = re.search(r'Route statistics:(.+?)(?:Channel|$)', text, re.DOTALL)
        if routes_section:
            section = routes_section.group(1)
            m = re.search(r'Received:\s*(\d+)\s*imported,\s*(\d+)\s*filtered', section)
            if m:
                routes_imported = int(m.group(1))
                routes_filtered = int(m.group(2))
            m = re.search(r'Exported:\s*(\d+)\s*exported,\s*(\d+)\s*preferred', section)
            if m:
                routes_exported = int(m.group(1))

        result["routes_imported"] = routes_imported
        result["routes_exported"] = routes_exported
        result["routes_filtered"] = routes_filtered
        _log_step(
            11, "route_statistics_extraction",
            after={
                "routes_imported": routes_imported,
                "routes_exported": routes_exported,
                "routes_filtered": routes_filtered,
            },
            note=f"total_net={routes_imported - routes_filtered} imported, {routes_exported} exported",
        )

        # ── Step 12: Extract channels (IPv4 and IPv6) ───────────────
        # BIRD output format: "Channel IPv4" or "Channel IPv6" (no colon, case-insensitive)
        # The channel content includes "BGP state:" and "Routes:" lines
        channel_pattern = r'Channel\s+(IPv[46])\s*\n(.*?)(?=Channel\s+IPv[46]\s*\n|$)'
        channel_count = 0
        channels_found = []
        for match in re.finditer(channel_pattern, text, re.DOTALL | re.IGNORECASE):
            channel = {
                "type": match.group(1),
                "bgp_state": "",
                "routes_imported": 0,
                "routes_exported": 0,
            }
            channel_text = match.group(2)

            m = re.search(r'BGP state:\s*(\S+)', channel_text)
            if m:
                channel["bgp_state"] = m.group(1)

            m = re.search(r'(\d+)\s*imported', channel_text)
            if m:
                channel["routes_imported"] = int(m.group(1))
            m = re.search(r'(\d+)\s*exported', channel_text)
            if m:
                channel["routes_exported"] = int(m.group(1))

            result["channels"].append(channel)
            channels_found.append(channel["type"])
            channel_count += 1
            _log_step(
                12 + channel_count - 1, f"channel_{channel_count}_extraction",
                before={"channel_header": f"Channel {match.group(1)}"},
                after={
                    "channel_type": channel["type"],
                    "channel_bgp_state": channel["bgp_state"],
                    "channel_routes_imported": channel["routes_imported"],
                    "channel_routes_exported": channel["routes_exported"],
                },
                success=True,
            )

        if channel_count == 0:
            _log_step(
                12, "channel_extraction",
                success=False,
                note="No Channel blocks found in output — protocol may not have channels",
            )

        # ── Step 13: Final result validation & return ─────────────────
        elapsed_ms = round((time.perf_counter() - _start_time) * 1000, 2)
        return_summary = {k: v for k, v in result.items() if k != "raw"}

        # Check data integrity
        required_fields = ["protocol_name", "state", "bgp_state"]
        missing_fields = [f for f in required_fields if not result.get(f)]
        has_channels = len(result["channels"]) > 0

        _log_step(
            13, "final_validation",
            before={"required_fields": required_fields},
            after={
                "protocol_name": result["protocol_name"],
                "state": result["state"],
                "bgp_state": result["bgp_state"],
                "neighbor_id": result["neighbor_id"],
                "connect_time": result["connect_time"],
                "channels_count": len(result["channels"]),
                "routes_total": {
                    "imported": result["routes_imported"],
                    "exported": result["routes_exported"],
                    "filtered": result["routes_filtered"],
                },
                "elapsed_ms": elapsed_ms,
            },
            success=len(missing_fields) == 0,
            note=f"missing_fields={missing_fields}" if missing_fields
                 else f"all_required_present · channels_found={has_channels} · parsed_in={elapsed_ms}ms",
        )

        # Type verification log
        _log_step(
            13, "type_verification",
            after={
                "protocol_name_type": type(result["protocol_name"]).__name__,
                "state_type": type(result["state"]).__name__,
                "bgp_state_type": type(result["bgp_state"]).__name__,
                "channels_type": type(result["channels"]).__name__,
                "channels_count": len(result["channels"]),
                "routes_imported_type": type(result["routes_imported"]).__name__,
                "routes_exported_type": type(result["routes_exported"]).__name__,
                "routes_filtered_type": type(result["routes_filtered"]).__name__,
            },
            note="type_check_complete",
        )

        if _PROTO_LOG_DEBUG:
            logger.debug(
                "[BIRD_PROTO] PARSING COMPLETE — Elapsed: %.2fms. "
                "Protocol: %s, State: %s, Channels: %d, Routes: %d in / %d out",
                elapsed_ms,
                result["protocol_name"],
                result["bgp_state"] or result["state"],
                len(result["channels"]),
                result["routes_imported"],
                result["routes_exported"],
            )

        return result

    except Exception:
        exc_type, exc_value, exc_tb = sys.exc_info()
        elapsed_ms = round((time.perf_counter() - _start_time) * 1000, 2)
        logger.error(
            "[BIRD_PROTO] parse_bird_protocols_all FAILED — "
            "Type: %s, Message: %s, Elapsed: %.2fms\n"
            "Stack trace:\n%s",
            exc_type.__name__,
            str(exc_value),
            elapsed_ms,
            "".join(traceback.format_exception(exc_type, exc_value, exc_tb)),
        )
        _log_step(
            99, "parsing_exception",
            success=False,
            after={
                "exception_type": exc_type.__name__,
                "exception_message": str(exc_value),
                "elapsed_ms": elapsed_ms,
            },
            note="parsing_failed",
        )
        return {"error": f"parse failed: {exc_type.__name__}: {exc_value}", "raw": (output or "")}


def parse_bird_protocols_list(output: str) -> list:
    """Parse ``birdc show protocols`` (overview, not 'all' detail) into a list of protocol summaries.
    
    Returns a list of dicts with keys: name, type, state, bgp_state, last_error, route_count.
    
    Handles multiple whitespace separators gracefully — BIRD's column layout often
    uses variable-width spacing (single or multiple spaces) between fields.
    """
    text = (output or "").strip()
    if not text:
        return []

    protocols = []

    lines = text.splitlines()
    for line in lines:
        if not line.strip():
            continue

        # Skip header / separator lines
        lower = line.lower()
        if ('name' in lower and 'proto' in lower) or line.startswith('-') or line.startswith('='):
            continue

        # Strategy: first try splitting on 2+ consecutive spaces (column-based layout).
        # If that yields too few fields, fall back to splitting on any whitespace and
        # re-assembling columns by content heuristics.
        tight_parts = re.split(r'\s{2,}', line.strip())

        if len(tight_parts) >= 4:
            name = tight_parts[0]
            proto_type = tight_parts[1] if len(tight_parts) > 1 else ""
            state = tight_parts[2] if len(tight_parts) > 2 else ""
            remaining = tight_parts[3:] if len(tight_parts) > 3 else []
        else:
            # Fallback: split on any whitespace, then use heuristics to identify fields
            all_parts = line.strip().split()
            if len(all_parts) < 3:
                continue

            # Field 0: protocol name (may contain _ but typically no spaces)
            name = all_parts[0]

            # Find the type field: known protocol types
            known_types = {"BGP", "OSPF", "Kernel", "Device", "Pipe", "Radar", "Static", "Direct", "BFD"}
            type_idx = -1
            for i, p in enumerate(all_parts[1:], 1):
                if p.upper() in known_types:
                    type_idx = i
                    break
            if type_idx == -1:
                type_idx = 1  # assume second token is the type

            proto_type = all_parts[type_idx]
            state = all_parts[type_idx + 1] if type_idx + 1 < len(all_parts) else ""
            remaining = all_parts[type_idx + 2:] if type_idx + 2 < len(all_parts) else []

        # Extract BGP state from remaining fields
        bgp_state = ""
        route_count = 0

        bgp_pattern = r'(Established|Open\s*\(.*?\)|Idle|Connect|Active|BGP_IDLE|BGP_CONNECT|BGP_ACTIVE|BGP_OPEN|BGP_UP|BGP_DOWN)'
        for p in remaining:
            m = re.match(bgp_pattern, p, re.IGNORECASE)
            if m:
                bgp_state = p
                break

        # Route count (e.g., "50 imported" or "150 imported, 50 exported")
        route_match = re.search(r'(\d+)\s*imported', line)
        if route_match:
            route_count = int(route_match.group(1))

        if name and proto_type:
            protocols.append({
                "name": name,
                "type": proto_type,
                "state": state,
                "bgp_state": bgp_state,
                "route_count": route_count,
                "raw": line,
            })

    return protocols


def summarize_wireguard(output: str) -> str:
    """Summarize ``wg show <iface>`` for one tunnel: up/stale/down + handshake age and transfer."""
    text = (output or "").strip()
    if not text or "No such device" in text or "Unable to access interface" in text:
        return "interface down"
    if "interface:" not in text and "peer:" not in text:
        return _capped(text)
    endpoint = re.search(r"endpoint:\s*(\S+)", text)
    handshake = re.search(r"latest handshake:\s*(.+)", text)
    transfer = re.search(r"transfer:\s*(.+)", text)
    # No "latest handshake" line (or "(none)") → the tunnel has never completed a handshake.
    age = handshake.group(1).strip() if handshake else ""
    if not age or age.lower() == "(none)":
        suffix = f" · endpoint {endpoint.group(1)}" if endpoint else ""
        return f"no handshake yet{suffix}"
    # A handshake measured in hours/days means keepalive has lapsed — flag it as stale.
    state = "stale" if re.search(r"\b(hour|day)", age) else "up"
    parts = [f"{state} · handshake {age}"]
    if transfer:
        xfer = transfer.group(1).strip()
        amounts = re.match(r"(.+?)\s+received,\s*(.+?)\s+sent", xfer)
        parts.append(f"{amounts.group(1)} rx / {amounts.group(2)} sent" if amounts else xfer)
    return " · ".join(parts)
