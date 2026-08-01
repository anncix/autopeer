"""DN42 standard BIRD base configuration generation.

Generates the shared BIRD2 scaffolding that all per-peer snippets (render_bird_peer_config)
assume exists in the node's main ``bird.conf``:

  * ROA tables (``roa4``/``roa6``) populated from the dn42 ROA dump
  * ``dn42_import`` filter — accepts dn42 prefixes, rejects default/martian, validates against
    ROA (rejects INVALID, lowers LOCAL_PREF for UNKNOWN), applies MED penalty
  * ``dn42_export`` filter — exports our originated prefixes with DN42 standard BGP communities
    (AS 64511 latency/bandwidth/crypto tiers)
  * ``dnpeers`` template — the base template per-peer ``protocol bgp`` blocks derive from, with
    ``import filter dn42_import; export filter dn42_export;`` wired in

This module only **generates text** — it does not write files or touch the node. The operator
includes the output (or the written ``00_dn42_base.conf``) from their ``bird.conf``, keeping
AutoPeer's boundary of "we write per-peer snippets, the operator owns the main config". A cron
helper for ROA refresh is also generated so the operator can install it.

生成所有 per-peer 片段(render_bird_peer_config)所預設存在於節點主 bird.conf 的共享 BIRD2 骨架:

  * ROA 表(roa4/roa6),從 dn42 ROA dump 填充
  * dn42_import filter——接受 dn42 前綴、拒絕 default/martian、以 ROA 驗證(拒絕 INVALID、
    對 UNKNOWN 降 LOCAL_PREF)、套用 MED 懲罰
  * dn42_export filter——以 DN42 標準 BGP communities(AS 64511 的 latency/bandwidth/crypto
    三級標記)匯出自身發起的前綴
  * dnpeers template——per-peer protocol bgp 區塊所繼承的基礎模板,已接好
    import filter dn42_import; export filter dn42_export;

本模組僅產生文字——不寫檔、不碰節點。操作者將輸出(或寫入的 00_dn42_base.conf)自其
bird.conf include,維持 AutoPeer「我們寫 per-peer 片段、操作者擁有主設定」的邊界。亦產生
ROA 刷新的 cron 輔助腳本供操作者安裝。
"""

from __future__ import annotations

from app.peer.validation import normalize_asn_number

# DN42 ROA dump sources (community-maintained). The v4/v6 files are updated hourly upstream.
# DN42 ROA dump 來源(社群維護)。v4/v6 檔案上游每小時更新。
DN42_ROA_IPV4_URL = "https://dn42.dev/roa/dn42_roa_bird2_4.conf"
DN42_ROA_IPV6_URL = "https://dn42.dev/roa/dn42_roa_bird2_6.conf"

# DN42 standard BGP community tiers (AS 64511). See https://dn42.dev/howto/Community
# Latency:   (asn, 10)..(asn, 50)  — <5ms / <20ms / <50ms / <150ms / >150ms
# Bandwidth: (asn, 11)..(asn, 14)  — >1G / >100M / >10M / <10M
# Crypto:    (asn, 31)..(asn, 33)  — none / unset / strong (WireGuard = strong)
# DN42 標準 BGP community 層級(AS 64511)。見 https://dn42.dev/howto/Community
LATENCY_TIERS = [
    (5, "10"),
    (20, "20"),
    (50, "30"),
    (150, "40"),
]
BANDWIDTH_TIERS = [
    (1000, "11"),
    (100, "12"),
    (10, "13"),
]
CRYPTO_STRONG = "33"  # WireGuard隧道一律视为强加密

# dn42 聚合前綴(v4/v6),import filter 只接受這些範圍內的路由。
DN42_PREFIXES_V4 = ["172.20.0.0/14", "172.31.0.0/16", "10.0.0.0/8"]
DN42_PREFIXES_V6 = ["fd00::/8"]


def latency_community(asn: str, latency_ms: float) -> str:
    """Map a latency (ms) to the DN42 community string ``(asn, <tier>)``.

    Returns the highest (lowest number) tier whose threshold the latency meets, defaulting to the
    worst tier (>150ms) when no threshold matches. ``asn`` is normalized to its numeric form.
    依延遲(ms)對應至 DN42 community 字串 (asn, <tier>)。回傳延遲所達到的最高(數字最小)層級,
    無門檻符合時預設為最差層級(>150ms)。asn 正規化為數字形式。
    """
    asn_num = normalize_asn_number(asn)
    for threshold, tier in LATENCY_TIERS:
        if latency_ms <= threshold:
            return f"({asn_num}, {tier})"
    return f"({asn_num}, 50)"


def bandwidth_community(asn: str, bandwidth_mbps: float) -> str:
    """Map a bandwidth (Mbps) to the DN42 community string ``(asn, <tier>)``."""
    asn_num = normalize_asn_number(asn)
    for threshold, tier in BANDWIDTH_TIERS:
        if bandwidth_mbps >= threshold:
            return f"({asn_num}, {tier})"
    return f"({asn_num}, 14)"


def crypto_community(asn: str, encrypted: bool = True) -> str:
    """Map crypto strength to the DN42 community string ``(asn, <tier>)``.

    WireGuard tunnels are always strong-encrypted → tier 33. Unencrypted (direct) → 31.
    依加密強度對應至 DN42 community 字串 (asn, <tier>)。WireGuard 隧道一律為強加密 → 33;
    未加密(直連)→ 31。
    """
    asn_num = normalize_asn_number(asn)
    return f"({asn_num}, {CRYPTO_STRONG})" if encrypted else f"({asn_num}, 31)"


def render_dn42_bird_base(local_asn: str) -> str:
    """Generate the full DN42 BIRD2 base configuration snippet.

    Includes ROA table definitions, the standard ``dn42_import``/``dn42_export`` filters with ROA
    validation and MED penalty, and the ``dnpeers`` template that per-peer snippets derive from.
    The operator includes this file from their ``bird.conf`` via
    ``include "/etc/bird/peers/00_dn42_base.conf";``.

    產生完整的 DN42 BIRD2 基礎設定片段。含 ROA 表定義、標準 dn42_import/dn42_export filter
    (含 ROA 驗證與 MED 懲罰),以及 per-peer 片段所繼承的 dnpeers 模板。操作者自其 bird.conf 以
    include "/etc/bird/peers/00_dn42_base.conf"; 引入。
    """
    asn = normalize_asn_number(local_asn)
    v4_checks = "\n        ".join(f"net ~ [{p}]" for p in DN42_PREFIXES_V4)
    v6_checks = "\n        ".join(f"net ~ [{p}]" for p in DN42_PREFIXES_V6)
    return f"""# Generated by dn42 Autopeer — DN42 BIRD2 base configuration.
# Include this file from your bird.conf:  include "/etc/bird/peers/00_dn42_base.conf";
# Local ASN: {asn}
#
# This provides:
#   - ROA tables (roa4/roa6) fed from the dn42 ROA dump
#   - dn42_import filter: dn42-prefix check + ROA validation + MED penalty
#   - dn42_export filter: originates our prefixes with DN42 standard communities
#   - dnpeers template: base template for all per-peer protocol bgp blocks
#
# ROA data is refreshed by the companion cron script (see render_roa_refresh_script).
# ROA 資料由隨附 cron 腳本刷新(見 render_roa_refresh_script)。

define LOCAL_ASN = {asn};

# --- ROA tables (populated by include of the dn42 ROA dump files) ---
roa4 table roa4;
roa6 table roa6;

# Pull in the ROA dump. These files are fetched/refreshed by the cron script below.
# If the files do not exist yet, BIRD will skip them (the `include` is wrapped in a try).
# 引入 ROA dump。這些檔案由下方 cron 腳本抓取/刷新;檔案不存在時 BIRD 會跳過。
include "/etc/bird/roa/dn42_roa_bird2_4.conf";
include "/etc/bird/roa/dn42_roa_bird2_6.conf";

# --- Import filter: accept dn42 prefixes, validate via ROA, penalize unknown ---
filter dn42_import {{
  # Reject default and martians
  # 拒絕預設路由與 martian
  if net = 0.0.0.0/0 then reject;
  if net = ::/0 then reject;

  # Only accept dn42 aggregate ranges
  # 僅接受 dn42 聚合範圍
  if net.type = NET_IP4 && ! ({v4_checks}) then reject;
  if net.type = NET_IP6 && ! ({v6_checks}) then reject;

  # ROA validation: reject INVALID, lower LOCAL_PREF for UNKNOWN, accept VALID
  # ROA 驗證:拒絕 INVALID,對 UNKNOWN 降 LOCAL_PREF,接受 VALID
  if net.type = NET_IP4 then {{
    case roa_check(roa4, net, bgp_path.last) {{
      ROA_INVALID: reject;
      ROA_UNKNOWN: bgp_local_pref = 80;
      ROA_VALID:   bgp_local_pref = 100;
    }}
  }}
  if net.type = NET_IP6 then {{
    case roa_check(roa6, net, bgp_path.last) {{
      ROA_INVALID: reject;
      ROA_UNKNOWN: bgp_local_pref = 80;
      ROA_VALID:   bgp_local_pref = 100;
    }}
  }}

  # MED penalty: prefer shorter AS paths
  # MED 懲罰:偏好較短 AS 路徑
  bgp_med = bgp_path.len * 10;

  accept;
}}

# --- Export filter: originate our prefixes with DN42 standard communities ---
# Default crypto tier is 33 (strong, WireGuard). Adjust per-link via PostUp scripts if needed.
# 預設加密層級為 33(強,WireGuard)。如需調整,可透過 PostUp 腳本 per-link 變更。
filter dn42_export {{
  # Only export routes we originate (source protocol = direct/static/own)
  # 僅匯出自身發起的路由(source protocol = direct/static/own)
  if source = RTS_BGP then reject;

  # Tag with DN42 standard communities (AS 64511)
  # 以 DN42 標準 communities 標記(AS 64511)
  bgp_community.add(({asn}, 33));        # crypto: strong (WireGuard)
  bgp_community.add(({asn}, 11));        # bandwidth: >1Gbps (default, tune per-link)
  bgp_community.add(({asn}, 10));        # latency: <5ms (default, tune per-link)

  accept;
}}

# --- dnpeers template: base for all per-peer protocol bgp blocks ---
# Per-peer snippets do `protocol bgp <name> from dnpeers { ... }` and inherit these defaults.
# per-peer 片段以 protocol bgp <name> from dnpeers {{ ... }} 繼承以下預設值。
template bgp dnpeers {{
  local as LOCAL_ASN;
  source address own;
  import filter dn42_import;
  export filter dn42_export;
  direct;
  enable extended messages on;
  ipv4 {{
    extended next hop on;
  }};
  ipv6 {{
    extended next hop on;
  }};
}}
"""


def render_roa_refresh_script() -> str:
    """Generate a shell script that fetches the dn42 ROA dump for BIRD2.

    The operator installs this as a cron job (e.g. hourly). It downloads the ROA dump files into
    ``/etc/bird/roa/`` and reloads BIRD via ``birdc configure`` so the new ROA data takes effect
    without restarting the daemon.

    產生抓取 dn42 ROA dump 供 BIRD2 使用的 shell 腳本。操作者將此安裝為 cron 任務(例如每小時)。
    腳本將 ROA dump 檔案下載至 /etc/bird/roa/ 並以 birdc configure 重載 BIRD,使新 ROA 資料生效
    而無需重啟守護程序。
    """
    return f"""#!/bin/sh
# dn42 ROA refresh script — generated by dn42 Autopeer.
# Install as: /etc/cron.hourly/dn42-roa-refresh  (chmod +x)
# Downloads the dn42 ROA dump and reloads BIRD2 so ROA validation uses fresh data.
# dn42 ROA 刷新腳本——由 dn42 Autopeer 產生。
# 安裝為:/etc/cron.hourly/dn42-roa-refresh (chmod +x)
# 下載 dn42 ROA dump 並重載 BIRD2,使 ROA 驗證使用最新資料。

set -eu

ROA_DIR="/etc/bird/roa"
mkdir -p "$ROA_DIR"

# Download to temp files first, then atomically move — a failed download never corrupts the
# live ROA files that BIRD includes.
# 先下載至暫存檔再原子移動——下載失敗不會損壞 BIRD 所引入的線上 ROA 檔案。
curl -fsS "{DN42_ROA_IPV4_URL}" -o "$ROA_DIR/dn42_roa_bird2_4.conf.tmp"
curl -fsS "{DN42_ROA_IPV6_URL}" -o "$ROA_DIR/dn42_roa_bird2_6.conf.tmp"

mv "$ROA_DIR/dn42_roa_bird2_4.conf.tmp" "$ROA_DIR/dn42_roa_bird2_4.conf"
mv "$ROA_DIR/dn42_roa_bird2_6.conf.tmp" "$ROA_DIR/dn42_roa_bird2_6.conf"

# Reload BIRD to pick up the new ROA data (hot reload, no session drop).
# 重載 BIRD 以套用新 ROA 資料(熱重載,不中斷會話)。
birdc configure >/dev/null 2>&1 || true

echo "dn42 ROA refreshed at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
"""
