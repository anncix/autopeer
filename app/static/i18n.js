/* i18n dictionary for AutoPeer UI
   Supports English (en) and Simplified Chinese (zh-CN) */

const I18N = {
  en: {
    // Navigation
    "nav.home": "Home",
    "nav.nodes": "Nodes",
    "nav.looking_glass": "Looking Glass",
    "nav.my_peers": "My Peers",
    "nav.admin": "Admin",
    "nav.logout": "Logout",
    "nav.login": "Login",

    // Footer
    "footer.powered_by": "Powered by",
    "footer.tech_support": "Powered by dn42",

    // Home page
    "home.hero_tagline": "Automated dn42 peering and a public looking glass across our nodes. Bring your ASN, pick a node, and get a ready-to-use WireGuard + BGP config.",
    "home.open_looking_glass": "Open Looking Glass",
    "home.create_peer": "Create a peer",
    "home.peer_with_us": "Peer with us",
    "home.how_to_peer": "How to peer with us",
    "home.step1": "Log in with your dn42 ASN (Kioubit, or the Telegram bot).",
    "home.step2": 'Open <a href="/portal/new">New Peer</a>, pick a node, and paste your <strong>WireGuard public key</strong>. Your endpoint is optional — leave it blank and your side dials us.',
    "home.step3": "Choose your in-tunnel IP. The <strong>link-local</strong> default works out of the box; a <strong>ULA</strong> (fd00::/8) is also accepted.",
    "home.step4": "We validate and <strong>auto-deploy</strong> to the node. Open the peer to copy our endpoint, public key, and BGP neighbor address — then bring up your side.",
    "home.stat_nodes": "Nodes",
    "home.stat_peers": "Peerings",
    "home.stat_deployed": "Deployed",
    "home.step1_title": "Log in",
    "home.step1_desc": "Log in with your dn42 ASN via Kioubit or the Telegram bot.",
    "home.step2_title": "Create peer",
    "home.step2_desc": "Open New Peer, pick a node, and paste your WireGuard public key.",
    "home.step3_title": "Choose IP",
    "home.step3_desc": "Choose tunnel IP. Link-local works out of the box; ULA also accepted.",
    "home.step4_title": "Deploy & Go",
    "home.step4_desc": "We validate and auto-deploy. Copy our config and bring up your side.",
    "home.nodes": "Nodes",
    "home.nodes_online": "{online} / {total} online",
    "home.online": "online",
    "home.offline": "offline",
    "home.last_seen": "Last seen {time} UTC",
    "home.no_heartbeat": "No heartbeat yet",
    "home.no_nodes": "No nodes are configured yet.",
    "home.browse_nodes": "Browse Nodes",

    // Nodes page
    "nodes.title": "Nodes",
    "nodes.subtitle": "Live status of all nodes in the {name} network.",
    "nodes.online_now": "Online now",
    "nodes.total_nodes": "Total nodes",
    "nodes.enabled": "Enabled",
    "nodes.online_rate": "Online rate",
    "nodes.no_nodes": "No nodes are configured yet.",

    // Login page
    "login.title": "Authenticate",
    "login.desc": "Use Kioubit.dn42 to prove control of your dn42 ASN, then you'll be signed in to the portal.",

    // Telegram auth
    "tg_auth.title": "Telegram Verification",
    "tg_auth.desc": "Verify your dn42 ASN to link it with your Telegram account.",
    "tg_auth.sending": "Sending data back to the bot…",

    // Looking Glass
    "lg.title": "Looking Glass",
    "lg.subtitle": "Run ping, traceroute, mtr, and route queries from any node.",
    "lg.node": "Node",
    "lg.query": "Query",
    "lg.target": "Target",
    "lg.target_placeholder": "IP, hostname, or prefix — e.g. 172.20.0.1, wiki.dn42, 1.1.1.0/24",
    "lg.target_placeholder_bird": "BIRD protocol name — e.g. DN42_1234_6b9f",
    "lg.run_query": "Run query",
    "lg.no_nodes": "No looking-glass nodes are configured yet.",

    // Portal (My Peers)
    "portal.title": "My Peers",
    "portal.subtitle": "Signed in as AS{asn}. You have {count} peer(s).",
    "portal.new_peer": "+ New Peer",
    "portal.peer": "Peer",
    "portal.node": "Node",
    "portal.enabled": "Enabled",
    "portal.deploy": "Deploy",
    "portal.manage": "Manage →",
    "portal.no_peers": "You have no peers yet. <a href=\"/portal/new\">Create your first peer →</a>",

    // New Peer
    "new_peer.title": "New Peer",
    "new_peer.subtitle": "Pick a node and paste your WireGuard details. You will confirm the settings before deployment.",
    "new_peer.your_wg_pubkey": "Your WireGuard public key",
    "new_peer.wg_pubkey_placeholder": "44-char base64 key",
    "new_peer.your_endpoint": "Your WireGuard endpoint",
    "new_peer.endpoint_placeholder": "host:port (blank = peer dials us)",
    "new_peer.dn42_ipv4": "DN42 IPv4",
    "new_peer.dn42_ipv4_placeholder": "172.20.x.y or 172.20.x.y/32",
    "new_peer.dn42_ipv6": "DN42 IPv6",
    "new_peer.dn42_ipv6_placeholder": "fd00::1 or fd00::1/128",
    "new_peer.link_local": "Link-local address",
    "new_peer.link_local_placeholder": "{default} or a ULA",
    "new_peer.mtu": "WireGuard MTU",
    "new_peer.bgp_extensions": "BGP extensions",
    "new_peer.review_peer": "Review peer",
    "new_peer.hint": "Enter at least one of DN42 IPv4, DN42 IPv6, or link-local. Blank fields are skipped. BGP extensions enable multiprotocol BGP and extended nexthop.",
    "new_peer.no_nodes": "No nodes are available right now. Please check back later.",

    // Confirm Peer
    "confirm.title": "Confirm Peer",
    "confirm.subtitle": "Review the settings before this peer is deployed.",
    "confirm.interface_helper": "Interface helper",
    "confirm.use_these": "Use these settings to configure your interface.",
    "confirm.asn": "ASN",
    "confirm.ipv4": "IPv4",
    "confirm.ipv6": "IPv6",
    "confirm.link_local": "Link-local",
    "confirm.endpoint": "Endpoint",
    "confirm.wg_pubkey": "WireGuard Public Key",
    "confirm.your_submitted": "Your submitted details",
    "confirm.bgp_neighbor": "BGP neighbor address",
    "confirm.wg_mtu": "WireGuard MTU",
    "confirm.bgp_extensions": "BGP extensions",
    "confirm.enabled": "enabled",
    "confirm.disabled": "disabled",
    "confirm.create_peer": "Create peer",
    "confirm.back": "Back",

    // Peer Detail
    "detail.title": "Peer - AS{asn}",
    "detail.subtitle": "On node {node}.",
    "detail.back_to_peers": "Back to My Peers",
    "detail.peer": "Peer",
    "detail.uuid": "UUID",
    "detail.enabled": "Enabled",
    "detail.deployment": "Deployment",
    "detail.configure_side": "Configure your side",
    "detail.use_our_side": "Use these \"our side\" details in your own WireGuard + BGP config.",
    "detail.view_config": "View full config",
    "detail.node": "Node",
    "detail.name": "Name",
    "detail.dn42_ipv4": "DN42 IPv4",
    "detail.dn42_ipv6": "DN42 IPv6",
    "detail.link_local_our": "Link-local (our side)",
    "detail.live_status": "Live status",
    "detail.wireguard": "WireGuard",
    "detail.bgp_session": "BGP session",
    "detail.refresh": "Refresh",
    "detail.view_live_status": "View live status",
    "detail.your_submitted": "Your submitted details",
    "detail.your_endpoint": "Your endpoint",
    "detail.you_dial_us": "- (you dial us)",
    "detail.your_wg_pubkey": "Your WireGuard public key",
    "detail.your_dn42_ipv4": "Your DN42 IPv4",
    "detail.your_dn42_ipv6": "Your DN42 IPv6",
    "detail.your_bgp_neighbor": "Your BGP neighbor address",
    "detail.danger_zone": "Danger zone",
    "detail.delete_confirm": "Delete this peer? This tears down the tunnel and BGP session on the node.",
    "detail.delete_peer": "Delete this peer",

    // Admin - Overview
    "admin.title": "Admin",
    "admin.dashboard": "Dashboard",
    "admin.control_plane": "Control plane: {url}",
    "admin.nodes_online": "Nodes online",
    "admin.nodes_online_sub": "{enabled} enabled / {total} total",
    "admin.peerings": "Peerings",
    "admin.peerings_sub": "{deployed} deployed",
    "admin.failed_deploys": "Failed deploys",
    "admin.failed_deploys_sub_attention": "need attention",
    "admin.failed_deploys_sub_healthy": "all healthy",
    "admin.members": "Members",
    "admin.members_sub": "{admin} admin",
    "admin.queries": "Queries",
    "admin.queries_sub": "audit log",
    "admin.needs_attention": "Needs attention — failed deploys",
    "admin.manage": "manage →",
    "admin.recent_peerings": "Recent peerings",
    "admin.all": "All",
    "admin.no_peers": "No peers yet.",
    "admin.recent_queries": "Recent queries",
    "admin.no_queries": "No queries yet.",

    // Admin - Nodes
    "admin.nodes": "Nodes",
    "admin.nodes_desc": "Nodes connect back over WSS and deploy WireGuard + BIRD configs as root.",
    "admin.add_node": "Add a node",
    "admin.name": "Name",
    "admin.location": "Location",
    "admin.public_addr": "Public address",
    "admin.asn": "ASN",
    "admin.dn42_ipv4": "DN42 IPv4",
    "admin.dn42_ipv6": "DN42 IPv6",
    "admin.enabled": "Enabled",
    "admin.create_node": "Create node",
    "admin.existing_nodes": "Existing nodes",
    "admin.status": "Status",
    "admin.system": "System",
    "admin.manage": "Manage →",
    "admin.no_nodes": "No nodes yet. Add one above.",
    "admin.online": "online",
    "admin.offline": "offline",
    "admin.on": "on",
    "admin.off": "off",

    // Admin - Node Edit
    "admin.node_desc": "Edit this node, view its status, and manage its credentials.",
    "admin.all_nodes": "← All nodes",
    "admin.details": "Details",
    "admin.save": "Save",
    "admin.peer_dial_hint": "Peers dial this IPv4/IPv6/domain over WireGuard; the listen port is derived from each peer's ASN. A disabled node is hidden from the public site and looking glass.",
    "admin.connection": "Connection",
    "admin.last_seen": "Last seen",
    "admin.credentials": "Credentials",
    "admin.api_token": "API token",
    "admin.wg_pubkey": "WireGuard public key",
    "admin.refresh_key": "Refresh key",
    "admin.reset_token": "Reset token",
    "admin.reset_token_confirm": "Issue a new API token for {node}? The node service must be reconfigured with the new token.",
    "admin.delete_node_confirm": "Delete node {node}? This cannot be undone.",
    "admin.delete_node": "Delete this node",

    // Admin - Node Edit tabs
    "admin.tab_details": "Details",
    "admin.tab_status": "Status",
    "admin.tab_credentials": "Credentials",
    "admin.tab_peers": "Peers",
    "admin.tab_links": "Links",
    "admin.tab_ospf": "OSPF",
    "admin.tab_danger": "Danger zone",
    "admin.peers_on_node": "Peers on this node",
    "admin.no_peers_on_node": "No peers are homed on this node yet.",
    "admin.protocol_name": "Protocol",

    // Admin - Internal links (iBGP/OSPF backbone)
    "admin.intra_links_on_node": "Internal links on this node",
    "admin.intra_links_desc": "iBGP/OSPF backbone WireGuard tunnels between your own nodes. Naming: ibgp_xxx.conf, port 414xx, LLA fe80::14:xxxx/64. The private key is read from the node's config (never transmitted) via the {placeholder} placeholder.",
    "admin.intra_remote_node": "Remote node (auto-fills key + endpoint)",
    "admin.intra_manual": "(manual — enter details below)",
    "admin.intra_remote_pubkey": "Remote WireGuard public key",
    "admin.intra_remote_pubkey_placeholder": "44-char base64 key (auto-filled from remote node)",
    "admin.intra_remote_endpoint": "Remote endpoint",
    "admin.intra_remote_endpoint_placeholder": "host:port (auto-filled from remote node url)",
    "admin.intra_label": "Label",
    "admin.intra_label_placeholder": "frankfurt-amsterdam",
    "admin.intra_deploy_now": "Deploy immediately",
    "admin.intra_create": "Create link",
    "admin.intra_protocol": "Protocol",
    "admin.intra_remote": "Remote",
    "admin.intra_port": "Port",
    "admin.intra_lla": "Link-local",
    "admin.no_intra_links": "No internal links on this node yet.",
    "admin.intra_delete_confirm": "Delete intra link {protocol}? This tears down the tunnel on the node.",

    // Admin - OSPF topology
    "admin.ospf_title": "OSPF topology",
    "admin.ospf_desc": "Reads OSPF neighbors (birdc show ospf neighbor, v4 + v6), OSPF area config files (/etc/bird/ospf/*.conf), and dummy interfaces (ip -o -d addr show type dummy) live from the node agent.",
    "admin.ospf_neighbors": "OSPF neighbors (birdc show ospf neighbor — v4 + v6)",
    "admin.ospf_configs": "OSPF area config files (/etc/bird/ospf/*.conf)",
    "admin.dummy_interfaces": "Dummy interfaces (ip -o -d addr show type dummy)",
    "admin.ospf_no_neighbors": "(no output / no OSPF neighbors)",
    "admin.ospf_no_configs": "(no .conf files found under the node's ospf_config_dir)",
    "admin.ospf_no_dummy": "(no output / no dummy interfaces)",

    // Admin - Peerings
    "admin.peerings_desc": "Create, edit, redeploy, or remove any peer across all nodes.",
    "admin.add_peer": "Add peer",
    "admin.peer_asn": "Peer ASN",
    "admin.peer_endpoint": "WireGuard endpoint",
    "admin.peer_endpoint_placeholder": "host:port (blank = peer dials us)",
    "admin.peer_wg_pubkey": "WireGuard public key",
    "admin.peer_mtu": "WireGuard MTU",
    "admin.peer_dn42_ipv4": "Peer DN42 IPv4",
    "admin.peer_dn42_ipv6": "Peer DN42 IPv6",
    "admin.our_address": "Our address{asn}",
    "admin.our_address_placeholder": "fe80::1260 or a ULA",
    "admin.peer_link_local": "Peer link-local address",
    "admin.peer_link_local_placeholder": "fe80::99 or a ULA",
    "admin.create_peer": "Create peer",
    "admin.no_nodes_configured": "No nodes are configured yet. Create a node first.",
    "admin.all_peerings": "All peerings",
    "admin.status": "Status",
    "admin.manage": "Manage →",
    "admin.no_peers": "No peers yet.",

    // Admin - Peer Edit
    "admin.peer_config": "Configuration",
    "admin.all_peerings_link": "← All peerings",
    "admin.edit_peer_desc": "Edit this peering on {node}.",
    "admin.deployment": "Deployment",
    "admin.redeploy": "Redeploy",
    "admin.view_config": "View config",
    "admin.view_live_status": "View live status",
    "admin.last_deploy_output": "Last deploy output",
    "admin.delete_peer_confirm": "Delete this peer (AS{asn})? This tears it down on the node.",
    "admin.delete_peer": "Delete this peer",

    // Admin - Users
    "admin.members_desc": "Everyone who has authenticated via Kioubit.dn42.",
    "admin.email": "Email",
    "admin.admin_role": "Admin",
    "admin.peers_count": "Peers",
    "admin.telegram": "Telegram",
    "admin.created": "Created",
    "admin.last_login": "Last login",
    "admin.actions": "Actions",
    "admin.admin_user": "admin",
    "admin.demote": "Demote",
    "admin.make_admin": "Make admin",
    "admin.unlink_tg": "Unlink TG",
    "admin.change_admin_confirm": "Change admin status for AS{asn}?",
    "admin.unlink_tg_confirm": "Unlink Telegram from AS{asn}? Their peers are kept.",
    "admin.no_users": "No users yet.",
    "admin.never": "never",

    // Admin - Query Log
    "admin.query_log_desc": "Every query dispatched to a node, with its outcome.",
    "admin.time_utc": "Time (UTC)",
    "admin.requester": "Requester",
    "admin.type": "Type",
    "admin.result": "Result",
    "admin.output": "Output",
    "admin.public": "public",
    "admin.view": "view",
    "admin.no_queries": "No looking-glass queries logged yet.",

    // Status badges
    "status.approved": "approved",
    "status.disabled": "disabled",
    "status.pending": "pending",
    "status.deployed": "deployed",
    "status.failed": "failed",
    "status.deploying": "deploying",

    // Flash messages
    "flash.no_output": "(no output)",
    "flash.copied": "Copied!",
    "flash.press_ctrl_c": "Press Ctrl+C",
    "flash.running": "Running…",
    "flash.query_failed": "Query failed",
    "flash.request_failed": "Request failed: {error}",
    "flash.unexpected_response": "Unexpected response (HTTP {code})",

    // Pagination
    "pagination.prev": "← Prev",
    "pagination.next": "Next →",
    "pagination.page_info": "Page {current} of {total} · {count} total",

    // Common
    "common.confirm_ok": "OK",
    "common.confirm_cancel": "Cancel",
    "common.save": "Save",
    "common.delete": "Delete",
    "common.edit": "Edit",
    "common.back": "← Back",
    "common.loading": "Loading…",
    "common.no_data": "No data",
    "common.dash": "—",
    "common.copy": "Copy",
    "common.optional": "(optional)",
    "common.asn": "ASN",

    // Theme
    "theme.dark": "Dark mode",
    "theme.light": "Light mode",

    // Language
    "lang.switch_to": "中文",
  },

  "zh-CN": {
    // Navigation
    "nav.home": "首页",
    "nav.nodes": "节点",
    "nav.looking_glass": "Looking Glass",
    "nav.my_peers": "我的对等",
    "nav.admin": "管理",
    "nav.logout": "退出登录",
    "nav.login": "登录",

    // Footer
    "footer.powered_by": "技术支持",
    "footer.tech_support": "技术支持 dn42",

    // Home page
    "home.hero_tagline": "自动化 dn42 对等互联，以及跨节点的公共 Looking Glass。带上你的 ASN，选择一个节点，即可获得即用型 WireGuard + BGP 配置。",
    "home.open_looking_glass": "打开 Looking Glass",
    "home.create_peer": "创建对等",
    "home.peer_with_us": "与我们对等",
    "home.how_to_peer": "如何与我们对等",
    "home.step1": "使用你的 dn42 ASN 登录（通过 Kioubit 或 Telegram 机器人）。",
    "home.step2": '打开 <a href="/portal/new">新建对等</a>，选择一个节点，粘贴你的 <strong>WireGuard 公钥</strong>。端点是可选的 — 留空则由你的一侧发起连接。',
    "home.step3": "选择隧道内 IP。默认的 <strong>链路本地地址</strong> 开箱即用；也接受 <strong>ULA</strong> (fd00::/8)。",
    "home.step4": "我们会验证并 <strong>自动部署</strong> 到节点。打开对等页面复制我们的端点、公钥和 BGP 邻居地址 — 然后启动你的一侧。",
    "home.stat_nodes": "节点数",
    "home.stat_peers": "对等数",
    "home.stat_deployed": "已部署",
    "home.step1_title": "登录",
    "home.step1_desc": "通过 Kioubit 或 Telegram 机器人使用你的 dn42 ASN 登录。",
    "home.step2_title": "创建对等",
    "home.step2_desc": "打开新建对等页面，选择节点，粘贴你的 WireGuard 公钥。",
    "home.step3_title": "选择 IP",
    "home.step3_desc": "选择隧道内 IP。链路本地地址开箱即用；也接受 ULA。",
    "home.step4_title": "部署上线",
    "home.step4_desc": "我们验证并自动部署。复制我们的配置并启动你的一侧。",
    "home.nodes": "节点",
    "home.nodes_online": "{online} / {total} 在线",
    "home.online": "在线",
    "home.offline": "离线",
    "home.last_seen": "最后在线 {time} UTC",
    "home.no_heartbeat": "尚无心跳",
    "home.no_nodes": "尚未配置任何节点。",
    "home.browse_nodes": "浏览节点",

    // Nodes page
    "nodes.title": "节点",
    "nodes.subtitle": "{name} 网络中所有节点的实时状态。",
    "nodes.online_now": "当前在线",
    "nodes.total_nodes": "节点总数",
    "nodes.enabled": "已启用",
    "nodes.online_rate": "在线率",
    "nodes.no_nodes": "尚未配置任何节点。",

    // Login page
    "login.title": "认证",
    "login.desc": "使用 Kioubit.dn42 验证你的 dn42 ASN 所有权，验证通过后即可登录门户。",

    // Telegram auth
    "tg_auth.title": "Telegram 验证",
    "tg_auth.desc": "验证你的 dn42 ASN 以将其与 Telegram 账号关联。",
    "tg_auth.sending": "正在向机器人回传数据…",

    // Looking Glass
    "lg.title": "Looking Glass",
    "lg.subtitle": "从任意节点运行 ping、traceroute、mtr 和路由查询。",
    "lg.node": "节点",
    "lg.query": "查询",
    "lg.target": "目标",
    "lg.target_placeholder": "IP、主机名或前缀 — 例如 172.20.0.1、wiki.dn42、1.1.1.0/24",
    "lg.target_placeholder_bird": "BIRD 协定名称 — 例如 DN42_1234_6b9f",
    "lg.run_query": "运行查询",
    "lg.no_nodes": "尚未配置任何 Looking Glass 节点。",

    // Portal (My Peers)
    "portal.title": "我的对等",
    "portal.subtitle": "已登录为 AS{asn}。你有 {count} 个对等。",
    "portal.new_peer": "+ 新建对等",
    "portal.peer": "对等",
    "portal.node": "节点",
    "portal.enabled": "已启用",
    "portal.deploy": "部署",
    "portal.manage": "管理 →",
    "portal.no_peers": "你还没有对等。<a href=\"/portal/new\">创建第一个对等 →</a>",

    // New Peer
    "new_peer.title": "新建对等",
    "new_peer.subtitle": "选择一个节点并粘贴你的 WireGuard 详情。在部署前你将确认这些设置。",
    "new_peer.your_wg_pubkey": "你的 WireGuard 公钥",
    "new_peer.wg_pubkey_placeholder": "44 字符 base64 密钥",
    "new_peer.your_endpoint": "你的 WireGuard 端点",
    "new_peer.endpoint_placeholder": "host:port (留空 = 对等端拨入我们)",
    "new_peer.dn42_ipv4": "DN42 IPv4",
    "new_peer.dn42_ipv4_placeholder": "172.20.x.y 或 172.20.x.y/32",
    "new_peer.dn42_ipv6": "DN42 IPv6",
    "new_peer.dn42_ipv6_placeholder": "fd00::1 或 fd00::1/128",
    "new_peer.link_local": "链路本地地址",
    "new_peer.link_local_placeholder": "{default} 或 ULA",
    "new_peer.mtu": "WireGuard MTU",
    "new_peer.bgp_extensions": "BGP 扩展",
    "new_peer.review_peer": "检查对等",
    "new_peer.hint": "至少输入 DN42 IPv4、DN42 IPv6 或链路本地地址中的一个。留空的字段将被跳过。BGP 扩展启用多协议 BGP 和扩展下一跳。",
    "new_peer.no_nodes": "当前没有可用的节点。请稍后再试。",

    // Confirm Peer
    "confirm.title": "确认对等",
    "confirm.subtitle": "在部署对等之前检查以下设置。",
    "confirm.interface_helper": "接口辅助信息",
    "confirm.use_these": "使用这些配置来配置你的接口。",
    "confirm.asn": "ASN",
    "confirm.ipv4": "IPv4",
    "confirm.ipv6": "IPv6",
    "confirm.link_local": "链路本地地址",
    "confirm.endpoint": "端点",
    "confirm.wg_pubkey": "WireGuard 公钥",
    "confirm.your_submitted": "你提交的详情",
    "confirm.bgp_neighbor": "BGP 邻居地址",
    "confirm.wg_mtu": "WireGuard MTU",
    "confirm.bgp_extensions": "BGP 扩展",
    "confirm.enabled": "已启用",
    "confirm.disabled": "已禁用",
    "confirm.create_peer": "创建对等",
    "confirm.back": "返回",

    // Peer Detail
    "detail.title": "对等 - AS{asn}",
    "detail.subtitle": "位于节点 {node}。",
    "detail.back_to_peers": "返回我的对等",
    "detail.peer": "对等",
    "detail.uuid": "UUID",
    "detail.enabled": "已启用",
    "detail.deployment": "部署状态",
    "detail.configure_side": "配置你的一侧",
    "detail.use_our_side": "在你自己的 WireGuard + BGP 配置中使用这些\"我方\"详情。",
    "detail.view_config": "查看完整配置",
    "detail.node": "节点",
    "detail.name": "名称",
    "detail.dn42_ipv4": "DN42 IPv4",
    "detail.dn42_ipv6": "DN42 IPv6",
    "detail.link_local_our": "链路本地地址（我方）",
    "detail.live_status": "实时状态",
    "detail.wireguard": "WireGuard",
    "detail.bgp_session": "BGP 会话",
    "detail.refresh": "刷新",
    "detail.view_live_status": "查看实时状态",
    "detail.your_submitted": "你提交的详情",
    "detail.your_endpoint": "你的端点",
    "detail.you_dial_us": "- (你拨入我们)",
    "detail.your_wg_pubkey": "你的 WireGuard 公钥",
    "detail.your_dn42_ipv4": "你的 DN42 IPv4",
    "detail.your_dn42_ipv6": "你的 DN42 IPv6",
    "detail.your_bgp_neighbor": "你的 BGP 邻居地址",
    "detail.danger_zone": "危险区域",
    "detail.delete_confirm": "删除此对等？这将拆除节点上的隧道和 BGP 会话。",
    "detail.delete_peer": "删除此对等",

    // Admin - Overview
    "admin.title": "管理",
    "admin.dashboard": "仪表板",
    "admin.control_plane": "控制平面: {url}",
    "admin.nodes_online": "在线节点",
    "admin.nodes_online_sub": "{enabled} 已启用 / {total} 总计",
    "admin.peerings": "对等数",
    "admin.peerings_sub": "{deployed} 已部署",
    "admin.failed_deploys": "部署失败",
    "admin.failed_deploys_sub_attention": "需要关注",
    "admin.failed_deploys_sub_healthy": "全部正常",
    "admin.members": "成员",
    "admin.members_sub": "{admin} 管理员",
    "admin.queries": "查询",
    "admin.queries_sub": "审计日志",
    "admin.needs_attention": "需要关注 — 部署失败",
    "admin.manage": "管理 →",
    "admin.recent_peerings": "最近的对等",
    "admin.all": "全部",
    "admin.no_peers": "暂无对等。",
    "admin.recent_queries": "最近的查询",
    "admin.no_queries": "暂无查询。",

    // Admin - Nodes
    "admin.nodes": "节点",
    "admin.nodes_desc": "节点通过 WSS 回连并以 root 身份部署 WireGuard + BIRD 配置。",
    "admin.add_node": "添加节点",
    "admin.name": "名称",
    "admin.location": "位置",
    "admin.public_addr": "公网地址",
    "admin.asn": "ASN",
    "admin.dn42_ipv4": "DN42 IPv4",
    "admin.dn42_ipv6": "DN42 IPv6",
    "admin.enabled": "已启用",
    "admin.create_node": "创建节点",
    "admin.existing_nodes": "现有节点",
    "admin.status": "状态",
    "admin.system": "系统",
    "admin.manage": "管理 →",
    "admin.no_nodes": "尚无节点。添加一个。",
    "admin.online": "在线",
    "admin.offline": "离线",
    "admin.on": "开",
    "admin.off": "关",

    // Admin - Node Edit
    "admin.node_desc": "编辑此节点、查看其状态并管理其凭据。",
    "admin.all_nodes": "← 所有节点",
    "admin.details": "详情",
    "admin.save": "保存",
    "admin.peer_dial_hint": "对等端通过 WireGuard 拨入此 IPv4/IPv6/域名；监听端口根据每个对等的 ASN 派生。已禁用的节点将在公开站点和 Looking Glass 中隐藏。",
    "admin.connection": "连接状态",
    "admin.last_seen": "最后在线",
    "admin.credentials": "凭据",
    "admin.api_token": "API 令牌",
    "admin.wg_pubkey": "WireGuard 公钥",
    "admin.refresh_key": "刷新密钥",
    "admin.reset_token": "重置令牌",
    "admin.reset_token_confirm": "为 {node} 颁发新的 API 令牌？节点服务需要使用新令牌重新配置。",
    "admin.delete_node_confirm": "删除节点 {node}？此操作无法撤销。",
    "admin.delete_node": "删除此节点",

    // Admin - Node Edit tabs
    "admin.tab_details": "详情",
    "admin.tab_status": "状态",
    "admin.tab_credentials": "凭据",
    "admin.tab_peers": "对等",
    "admin.tab_links": "链路",
    "admin.tab_ospf": "OSPF",
    "admin.tab_danger": "危险区域",
    "admin.peers_on_node": "此节点上的对等",
    "admin.no_peers_on_node": "此节点上尚未承载任何对等。",
    "admin.protocol_name": "协议",

    // Admin - Internal links (iBGP/OSPF backbone)
    "admin.intra_links_on_node": "此节点上的内网链路",
    "admin.intra_links_desc": "你自己的节点之间的 iBGP/OSPF 主干 WireGuard 隧道。命名规则：ibgp_xxx.conf，端口 414xx，LLA fe80::14:xxxx/64。私钥从节点配置中读取（绝不外传），通过 {placeholder} 占位符注入。",
    "admin.intra_remote_node": "对端节点（自动填充密钥和端点）",
    "admin.intra_manual": "（手动 — 在下方填写详情）",
    "admin.intra_remote_pubkey": "对端 WireGuard 公钥",
    "admin.intra_remote_pubkey_placeholder": "44 字符 base64 密钥（从对端节点自动填充）",
    "admin.intra_remote_endpoint": "对端端点",
    "admin.intra_remote_endpoint_placeholder": "host:port（从对端节点 url 自动填充）",
    "admin.intra_label": "标签",
    "admin.intra_label_placeholder": "frankfurt-amsterdam",
    "admin.intra_deploy_now": "立即部署",
    "admin.intra_create": "创建链路",
    "admin.intra_protocol": "协议",
    "admin.intra_remote": "对端",
    "admin.intra_port": "端口",
    "admin.intra_lla": "链路本地",
    "admin.no_intra_links": "此节点上尚未创建内网链路。",
    "admin.intra_delete_confirm": "删除内网链路 {protocol}？这将在节点上拆除该隧道。",

    // Admin - OSPF topology
    "admin.ospf_title": "OSPF 拓扑",
    "admin.ospf_desc": "从节点 agent 实时读取 OSPF 邻居（birdc show ospf neighbor，v4 + v6）、OSPF area 配置文件（/etc/bird/ospf/*.conf）以及 dummy 网卡（ip -o -d addr show type dummy）。",
    "admin.ospf_neighbors": "OSPF 邻居（birdc show ospf neighbor — v4 + v6）",
    "admin.ospf_configs": "OSPF area 配置文件（/etc/bird/ospf/*.conf）",
    "admin.dummy_interfaces": "Dummy 网卡（ip -o -d addr show type dummy）",
    "admin.ospf_no_neighbors": "（无输出 / 无 OSPF 邻居）",
    "admin.ospf_no_configs": "（在节点的 ospf_config_dir 下未找到 .conf 文件）",
    "admin.ospf_no_dummy": "（无输出 / 无 dummy 网卡）",

    // Admin - Peerings
    "admin.peerings_desc": "在所有节点上创建、编辑、重新部署或删除任意对等。",
    "admin.add_peer": "添加对等",
    "admin.peer_asn": "对等 ASN",
    "admin.peer_endpoint": "WireGuard 端点",
    "admin.peer_endpoint_placeholder": "host:port (留空 = 对等端拨入我们)",
    "admin.peer_wg_pubkey": "WireGuard 公钥",
    "admin.peer_mtu": "WireGuard MTU",
    "admin.peer_dn42_ipv4": "对等 DN42 IPv4",
    "admin.peer_dn42_ipv6": "对等 DN42 IPv6",
    "admin.our_address": "我方地址{asn}",
    "admin.our_address_placeholder": "fe80::1260 或 ULA",
    "admin.peer_link_local": "对等链路本地地址",
    "admin.peer_link_local_placeholder": "fe80::99 或 ULA",
    "admin.create_peer": "创建对等",
    "admin.no_nodes_configured": "尚未配置任何节点。请先创建一个节点。",
    "admin.all_peerings": "所有对等",
    "admin.status": "状态",
    "admin.manage": "管理 →",
    "admin.no_peers": "暂无对等。",

    // Admin - Peer Edit
    "admin.peer_config": "配置",
    "admin.all_peerings_link": "← 所有对等",
    "admin.edit_peer_desc": "在 {node} 上编辑此对等。",
    "admin.deployment": "部署",
    "admin.redeploy": "重新部署",
    "admin.view_config": "查看配置",
    "admin.view_live_status": "查看实时状态",
    "admin.last_deploy_output": "上次部署输出",
    "admin.delete_peer_confirm": "删除此对等 (AS{asn})？这将在节点上将其拆除。",
    "admin.delete_peer": "删除此对等",

    // Admin - Users
    "admin.members_desc": "所有通过 Kioubit.dn42 认证的用户。",
    "admin.email": "邮箱",
    "admin.admin_role": "管理员",
    "admin.peers_count": "对等数",
    "admin.telegram": "Telegram",
    "admin.created": "创建时间",
    "admin.last_login": "上次登录",
    "admin.actions": "操作",
    "admin.admin_user": "管理员",
    "admin.demote": "降级",
    "admin.make_admin": "设为管理员",
    "admin.unlink_tg": "解绑 TG",
    "admin.change_admin_confirm": "更改 AS{asn} 的管理员状态？",
    "admin.unlink_tg_confirm": "从 AS{asn} 解绑 Telegram？他们的对等将保留。",
    "admin.no_users": "暂无用户。",
    "admin.never": "从不",

    // Admin - Query Log
    "admin.query_log_desc": "发送到节点的每个查询及其结果。",
    "admin.time_utc": "时间 (UTC)",
    "admin.requester": "请求者",
    "admin.type": "类型",
    "admin.result": "结果",
    "admin.output": "输出",
    "admin.public": "公开",
    "admin.view": "查看",
    "admin.no_queries": "尚无 Looking Glass 查询记录。",

    // Status badges
    "status.approved": "已批准",
    "status.disabled": "已禁用",
    "status.pending": "待处理",
    "status.deployed": "已部署",
    "status.failed": "失败",
    "status.deploying": "部署中",

    // Flash messages
    "flash.no_output": "(无输出)",
    "flash.copied": "已复制！",
    "flash.press_ctrl_c": "请按 Ctrl+C",
    "flash.running": "运行中…",
    "flash.query_failed": "查询失败",
    "flash.request_failed": "请求失败: {error}",
    "flash.unexpected_response": "意外响应 (HTTP {code})",

    // Pagination
    "pagination.prev": "← 上一页",
    "pagination.next": "下一页 →",
    "pagination.page_info": "第 {current} 页 / 共 {total} 页 · {count} 条",

    // Common
    "common.confirm_ok": "确定",
    "common.confirm_cancel": "取消",
    "common.save": "保存",
    "common.delete": "删除",
    "common.edit": "编辑",
    "common.back": "← 返回",
    "common.loading": "加载中…",
    "common.no_data": "无数据",
    "common.dash": "—",
    "common.copy": "复制",
    "common.optional": "（可选）",
    "common.asn": "ASN",

    // Theme
    "theme.dark": "暗色模式",
    "theme.light": "亮色模式",

    // Language
    "lang.switch_to": "English",
  }
};

// Global state
let currentLang = localStorage.getItem('lang') || 'en';
let currentTheme = localStorage.getItem('theme') || 'light';

// Apply translations to elements with data-i18n attribute
function applyTranslations(root = document) {
  const elements = root.querySelectorAll('[data-i18n]');
  elements.forEach(el => {
    const key = el.getAttribute('data-i18n');
    const params = {};
    
    // Check for parameters via data attributes like data-i18n-param-xxx
    if (el.dataset) {
      for (const attr in el.dataset) {
        if (attr.startsWith('i18nParam')) {
          let paramName = attr.replace('i18nParam', '');
          paramName = paramName.charAt(0).toLowerCase() + paramName.slice(1);
          params[paramName] = el.dataset[attr];
        }
      }
    }
    
    const translation = getTranslation(key, params);
    if (translation !== null && translation !== key) {
      // Check if element contains form controls that must be preserved
      const hasFormControls = el.querySelector('select, input, textarea');
      const hasChildren = el.children.length > 0;
      
      if (hasFormControls || hasChildren) {
        // Preserve ALL child elements including form controls - only replace text content
        const directTextNodes = getDirectTextNodes(el);
        if (directTextNodes.length > 0) {
          // Replace first text node with translation, clear the rest
          for (let i = 0; i < directTextNodes.length; i++) {
            if (i === 0) {
              directTextNodes[i].nodeValue = translation;
            } else {
              directTextNodes[i].nodeValue = '';
            }
          }
        } else {
          // No direct text nodes - find first span or text-bearing child and update it
          const textChild = el.querySelector('span:not(.muted)');
          if (textChild && !hasFormControls) {
            if (translation.includes('<') && translation.includes('>')) {
              textChild.innerHTML = translation;
            } else {
              textChild.textContent = translation;
            }
          }
        }
      } else if (translation.includes('<') && translation.includes('>')) {
        el.innerHTML = translation;
      } else {
        el.textContent = translation;
      }
    }
  });

  // Translate placeholder attributes
  const placeholderElements = root.querySelectorAll('[data-i18n-placeholder]');
  placeholderElements.forEach(el => {
    const key = el.getAttribute('data-i18n-placeholder');
    const translation = getTranslation(key, {});
    if (translation !== null && translation !== key) {
      el.setAttribute('placeholder', translation);
    }
  });
}

// Get direct text nodes of an element (not text inside child elements)
function getDirectTextNodes(el) {
  const textNodes = [];
  for (const child of el.childNodes) {
    if (child.nodeType === Node.TEXT_NODE && child.nodeValue.trim()) {
      textNodes.push(child);
    }
  }
  return textNodes;
}

function getTranslation(key, params = {}) {
  const dict = I18N[currentLang] || I18N.en;
  let text = dict[key] || I18N.en[key] || key;
  
  // Replace placeholders
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(`{${k}}`, v);
  }
  
  return text;
}

function setLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);
  document.documentElement.lang = lang === 'zh-CN' ? 'zh-CN' : 'en';
  applyTranslations();
  
  // Update language toggle button
  const langBtn = document.getElementById('lang-toggle');
  if (langBtn) {
    langBtn.innerHTML = lang === 'zh-CN' ? '🇨🇳' : '🇺🇸';
    langBtn.setAttribute('aria-label', I18N[lang]['lang.switch_to']);
    langBtn.title = I18N[lang]['lang.switch_to'];
  }
}

function setTheme(theme) {
  currentTheme = theme;
  localStorage.setItem('theme', theme);
  document.documentElement.setAttribute('data-theme', theme);
  
  // Update theme toggle button
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    themeBtn.innerHTML = theme === 'dark' 
      ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><circle cx="12" cy="12" r="5"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></g></svg>'
      : '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    themeBtn.setAttribute('aria-label', I18N[currentLang][theme === 'dark' ? 'theme.light' : 'theme.dark']);
    themeBtn.title = I18N[currentLang][theme === 'dark' ? 'theme.light' : 'theme.dark'];
  }
}

function initI18n() {
  // Set initial state
  document.documentElement.lang = currentLang === 'zh-CN' ? 'zh-CN' : 'en';
  document.documentElement.setAttribute('data-theme', currentTheme);
  
  // Create toggle buttons if they don't exist
  createToggleButtons();
  
  // Apply translations
  applyTranslations();
  
  // Update button states
  updateButtonStates();
}

function createToggleButtons() {
  const topbar = document.querySelector('.topbar-user');
  if (!topbar) return;
  
  // Theme toggle (icon-only)
  if (!document.getElementById('theme-toggle')) {
    const themeBtn = document.createElement('button');
    themeBtn.id = 'theme-toggle';
    themeBtn.className = 'icon-toggle';
    themeBtn.type = 'button';
    themeBtn.setAttribute('role', 'button');
    themeBtn.setAttribute('tabindex', '0');
    themeBtn.addEventListener('click', () => {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      setTheme(newTheme);
      updateButtonStates();
    });
    topbar.insertBefore(themeBtn, topbar.firstChild);
  }
  
  // Language toggle (icon-only with flag)
  if (!document.getElementById('lang-toggle')) {
    const langBtn = document.createElement('button');
    langBtn.id = 'lang-toggle';
    langBtn.className = 'icon-toggle';
    langBtn.type = 'button';
    langBtn.setAttribute('role', 'button');
    langBtn.setAttribute('tabindex', '0');
    langBtn.addEventListener('click', () => {
      const newLang = currentLang === 'en' ? 'zh-CN' : 'en';
      setLanguage(newLang);
      updateButtonStates();
    });
    topbar.insertBefore(langBtn, topbar.firstChild);
  }
}

function updateButtonStates() {
  const langBtn = document.getElementById('lang-toggle');
  const themeBtn = document.getElementById('theme-toggle');
  
  if (langBtn) {
    langBtn.innerHTML = currentLang === 'zh-CN' ? '🇨🇳' : '🇺🇸';
    langBtn.setAttribute('aria-label', I18N[currentLang]['lang.switch_to']);
    langBtn.title = I18N[currentLang]['lang.switch_to'];
  }
  
  if (themeBtn) {
    themeBtn.innerHTML = currentTheme === 'dark' 
      ? '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><circle cx="12" cy="12" r="5"/><g stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="6.34" y2="6.34"/><line x1="17.66" y1="17.66" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="6.34" y2="17.66"/><line x1="17.66" y1="6.34" x2="19.78" y2="4.22"/></g></svg>'
      : '<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    themeBtn.setAttribute('aria-label', I18N[currentLang][currentTheme === 'dark' ? 'theme.light' : 'theme.dark']);
    themeBtn.title = I18N[currentLang][currentTheme === 'dark' ? 'theme.light' : 'theme.dark'];
  }
}

// Expose for use in app.js
window.I18N = I18N;
window.currentLang = currentLang;
window.currentTheme = currentTheme;
window.applyTranslations = applyTranslations;
window.getTranslation = getTranslation;
window.setLanguage = setLanguage;
window.setTheme = setTheme;
window.initI18n = initI18n;
