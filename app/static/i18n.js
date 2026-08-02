/* i18n dictionary for AutoPeer UI
   Supports English (en) and Simplified Chinese (zh-CN) */

const I18N = {
  en: {
    // Navigation
    "nav.home": "Home",
    "nav.nodes": "Nodes",
    "nav.looking_glass": "LG",
    "nav.my_peers": "Peer",
    "nav.admin": "Admin",
    "nav.logout": "Logout",
    "nav.logout_text": "Logout",
    "nav.login": "Login",
    "nav.role_admin": "Administrator",
    "nav.role_user": "User",
    "nav.map": "Map",

    // Footer
    "footer.powered_by": "Powered by",
    "footer.tech_support": "Powered by dn42",

    // Home page
    "home.kicker": "dn42 · Anycast · Automation",
    "home.hero_tagline": "Automated dn42 peering and a public looking glass across our nodes. Bring your ASN, pick a node, and get a ready-to-use WireGuard + BGP config.",
    "home.open_looking_glass": "Open Looking Glass",
    "home.create_peer": "Create a peer",
    "home.peer_with_us": "Peer with us",
    "home.how_to_peer": "How to peer with us",
    "home.how_to_peer_sub": "Four steps to a deployed dn42 peering.",
    "home.step1": "Log in with your dn42 ASN (Kioubit, or the Telegram bot).",
    "home.step2": 'Open <a href="/portal/new">New Peer</a>, pick a node, and paste your <strong>WireGuard public key</strong>. Your endpoint is optional — leave it blank and your side dials us.',
    "home.step3": "Choose your in-tunnel IP. The <strong>link-local</strong> default works out of the box; a <strong>ULA</strong> (fd00::/8) is also accepted.",
    "home.step4": "We validate and <strong>auto-deploy</strong> to the node. Open the peer to copy our endpoint, public key, and BGP neighbor address — then bring up your side.",
    "home.stat_nodes": "Nodes",
    "home.network_stats": "Network Stats",
    "home.network_nodes": "Network Nodes",
    "home.nodes_search_placeholder": "Search by name or IP...",
    "home.filter_all": "All",
    "home.filter_asia": "East Asia",
    "home.filter_sea": "Southeast Asia",
    "home.filter_europe": "Europe",
    "home.filter_na": "North America",
    "home.filter_other": "Other",
    "home.filter_oceania": "Oceania",
    "home.node_name": "Node",
    "home.node_location": "Location",
    "home.status": "Status",
    "home.open_state": "Open",
    "home.closed_state": "Closed",
    "home.connect": "Connect",
    "home.connect_label": "Connect",
    "home.copy_node_info": "Copy router info",
    "home.direct_ethernet": "Direct Ethernet",
    "home.list_view": "List view",
    "home.grid_view": "Grid view",
    "home.session_capacity": "Session capacity",
    "home.dn42_section": "DN42",
    "home.bgp_nodes": "BGP Network Nodes",
    "home.pick_node_desc": "Pick a BGP router to peer with",
    "home.no_nodes_found": "No nodes found",
    "home.no_nodes_found_desc": "Try adjusting your search or filter criteria.",
    "home.stat_nodes_online": "Nodes online",
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
    "home.nodes_nearby": "Our Nodes",
    "home.nodes_nearby_sub": "Live status across every node.",
    "home.view_all_nodes": "All nodes",
    "home.quick_lg": "Quick Lookup",
    "home.quick_lg_sub": "Search BGP sessions, ping nodes, inspect routes",
    "home.quick_lg_placeholder": "protocol name, IP or prefix",
    "home.quick_lg_go": "Go",
    "home.quick_lg_help": "Tip: leave the target empty to list every BGP session on the node.",
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
    "login.debug_hint": "Development / Testing:",
    "login.debug_admin": "🔓 Admin Debug Login (AS65000)",

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
    "new_peer.your_endpoint_opt": "Your WireGuard endpoint (optional)",
    "new_peer.endpoint_placeholder": "host:port (blank = peer dials us)",
    "new_peer.dn42_ipv4": "DN42 IPv4",
    "new_peer.dn42_ipv4_opt": "DN42 IPv4 (optional)",
    "new_peer.dn42_ipv4_placeholder": "172.20.x.y or 172.20.x.y/32",
    "new_peer.dn42_ipv6": "DN42 IPv6",
    "new_peer.dn42_ipv6_opt": "DN42 IPv6 (optional)",
    "new_peer.dn42_ipv6_placeholder": "fd00::1 or fd00::1/128",
    "new_peer.link_local": "Link-local address",
    "new_peer.link_local_opt": "Link-local address (optional)",
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
    "admin.intra_links": "Intra links",
    "admin.intra_links_sub": "OSPF / iBGP backbone",
    "admin.failed_deploys": "Failed deploys",
    "admin.failed_deploys_sub_attention": "need attention",
    "admin.failed_deploys_sub_healthy": "all healthy",
    "admin.members": "Members",
    "admin.members_sub": "{admin} admin",
    "admin.queries": "Queries",
    "admin.queries_sub": "audit log",
    "admin.needs_attention": "Needs attention — failed deploys",
    "admin.items": "items",
    "admin.review": "Review",
    "admin.nodes_manage": "Manage nodes",
    "admin.view_all": "View all",
    "admin.node_health": "Node health",
    "admin.manage": "Manage",
    "admin.recent_peerings": "Recent peerings",
    "admin.all": "All",
    "admin.no_peers": "No peers yet.",
    "admin.recent_queries": "Recent queries",
    "admin.no_queries": "No queries yet.",

    // Admin - Dashboard (additional keys)
    "admin.dashboard_desc": "Overview of your dn42 network",
    "admin.online_nodes": "Online Nodes",
    "admin.nodes_enabled": "enabled",
    "admin.deployed_peers": "Deployed Peers",
    "admin.active_bgp_sessions": "Active BGP sessions",
    "admin.failed_deployments": "Failed Deployments",
    "admin.view_network_map": "View network map →",
    "admin.network_map": "Network Map",
    "admin.network_map_desc": "Real-time latency across all nodes",
    "admin.network_topology": "Network Topology",
    "admin.network_topology_desc": "Real-time latency across all nodes with interactive world map visualization",
    "admin.open_network_map": "Open Network Map",
    "admin.uptime": "Last Update",
    "admin.avg_latency": "Avg Latency",
    "admin.max_latency": "Max Latency",
    "admin.min_latency": "Min Latency",
    "admin.refresh": "Refresh",
    "admin.auto_refresh": "Auto-refresh",
    "admin.focus_nodes": "Focus nodes",
    "admin.reset_view": "Reset view",
    "admin.jitter": "Network jitter",
    "admin.search_nodes": "Search nodes...",
    "admin.latency_legend": "Latency (ms)",
    "admin.node_latency_list": "Node Latency",
    "admin.trend": "Trend",
    "admin.links": "Links",
    "admin.latency": "Latency",
    "admin.recent_peers": "Recent Peers",
    "admin.looking_glass_activity": "Looking glass activity",
    "admin.no_failed_deployments": "No failed deployments",
    "admin.no_queries_yet": "No queries yet",
    "admin.quick_actions": "Quick Actions",
    "admin.network_search": "Network Search",
    "admin.settings": "Settings",

    // Admin - Nodes
    "admin.nodes": "Nodes",
    "admin.nodes_desc": "Nodes connect back over WSS and deploy WireGuard + BIRD configs as root.",
    "admin.nodes_count": "Nodes",
    "admin.peers_count": "Peers",
    "admin.users_count": "Users",
    "admin.queries_count": "Queries",
    "admin.add_node": "Add a node",
    "admin.name": "Name",
    "admin.location": "Location",
    "admin.public_addr": "Public address",
    "admin.asn": "ASN",
    "admin.asn_opt": "ASN (optional)",
    "admin.dn42_ipv4": "DN42 IPv4",
    "admin.dn42_ipv4_opt": "DN42 IPv4 (optional)",
    "admin.dn42_ipv6": "DN42 IPv6",
    "admin.dn42_ipv6_opt": "DN42 IPv6 (optional)",
    "admin.enabled": "Enabled",
    "admin.wireguard": "WireGuard",
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
    "admin.node": "Node",
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
    "admin.tab_bird_base": "BIRD Base",
    "admin.tab_flap": "Flap",
    "admin.tab_danger": "Danger zone",
    "admin.peers_on_node": "Peers on this node",
    "admin.no_peers_on_node": "No peers are homed on this node yet.",
    "admin.protocol_name": "Protocol",

    // Admin - Internal links (iBGP/OSPF backbone)
    "admin.intra_links_on_node": "Internal links on this node",
    "admin.intra_links_desc": "iBGP/OSPF backbone WireGuard tunnels between your own nodes. Naming: ibgp_xxx.conf, port 414xx-443xx, LLA fe80::14:xxxx/64. The private key is read from the node's config (never transmitted) via the {placeholder} placeholder.",
    "admin.intra_remote_node": "Remote node",
    "admin.intra_search": "Search nodes",
    "admin.intra_search_placeholder": "Type to filter nodes by name or location…",
    "admin.search_results": "{count} nodes found",
    "admin.no_search_results": "No results yet. Select a node and query type to start searching.",
    "admin.intra_manual": "(manual — enter details below)",
    "admin.intra_remote_pubkey": "Public key",
    "admin.intra_remote_pubkey_placeholder": "44-char base64 key (auto-filled from remote node)",
    "admin.intra_remote_endpoint": "Endpoint",
    "admin.intra_remote_endpoint_placeholder": "host:port (auto-filled from remote node url)",
    "admin.intra_label": "Label",
    "admin.intra_label_placeholder": "frankfurt-amsterdam",
    "admin.intra_listen_port": "Listen port",
    "admin.intra_label_show": "Label",
    "admin.auto_generated": "Auto-generated when remote selected",
    "admin.auto_filled": "Auto-filled",
    "admin.intra_deploy_now": "Deploy immediately",
    "admin.intra_reverse": "Also create reverse link on remote node (bi-directional)",
    "admin.intra_create": "Create link",
    "admin.create_intra_link": "Create link",
    "admin.intra_creating": "Creating…",
    "admin.intra_protocol": "Protocol",
    "admin.intra_remote": "Remote",
    "admin.intra_lla": "Link-local",
    "admin.intra_latency": "Latency",
    "admin.latency_checking": "Checking…",
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

    // Admin - DN42 BIRD base config (ROA + filters + dnpeers template)
    "admin.bird_base_title": "DN42 BIRD2 base config",
    "admin.bird_base_desc": "Generates the shared BIRD2 scaffolding (ROA tables, import/export filters with ROA validation, dnpeers template) that per-peer snippets inherit from. Includes a ROA refresh cron script.",
    "admin.bird_base_open": "Export DN42 base config",
    "admin.bird_base_config": "DN42 BIRD2 base configuration",
    "admin.bird_base_install_hint": "Install: save as /etc/bird/peers/00_dn42_base.conf and add include \"/etc/bird/peers/*.conf\"; to your bird.conf. Local ASN: {asn}.",
    "admin.roa_refresh_script": "ROA refresh cron script",
    "admin.roa_refresh_hint": "Install as /etc/cron.hourly/dn42-roa-refresh (chmod +x). Fetches the dn42 ROA dump hourly and hot-reloads BIRD2 so ROA validation uses fresh data.",
    "admin.back_to_node": "Back to node",

    // Admin - BGP flap detection
    "admin.flap_title": "BGP flap detection",
    "admin.flap_desc": "Polls birdc show protocols and records BGP session state transitions (up↔start/down) into a ring buffer. Opening the flap page triggers one poll.",
    "admin.flap_open": "View flap timeline",
    "admin.flap_total": "Total events buffered",
    "admin.flap_new": "New this poll",
    "admin.flap_bgp_sessions": "BGP sessions now",
    "admin.flap_current_states": "Current BGP protocol states (this poll)",
    "admin.flap_protocol": "Protocol",
    "admin.flap_state": "State",
    "admin.flap_timeline": "Transition timeline (newest first, last 200)",
    "admin.flap_time": "Time (UTC)",
    "admin.flap_from": "From",
    "admin.flap_to": "To",
    "admin.flap_new_badge": "new",
    "admin.flap_no_sessions": "(no BGP protocols seen — node may have no peers, or birdc is not configured)",
    "admin.flap_no_events": "(no transitions recorded yet — open this page again after BGP state changes occur)",
    "admin.no_flap_events": "No flap events recorded yet.",
    "admin.loading": "Loading…",

    // Admin - Peerings
    "admin.peerings_desc": "Create, edit, redeploy, or remove any peer across all nodes.",
    "admin.add_peer": "Add peer",
    "admin.peer_asn": "Peer ASN",
    "admin.peer_endpoint": "WireGuard endpoint",
    "admin.peer_endpoint_opt": "WireGuard endpoint (optional)",
    "admin.peer_endpoint_placeholder": "host:port (blank = peer dials us)",
    "admin.peer_wg_pubkey": "WireGuard public key",
    "admin.peer_mtu": "WireGuard MTU",
    "admin.peer_dn42_ipv4": "Peer DN42 IPv4",
    "admin.peer_dn42_ipv4_opt": "Peer DN42 IPv4 (optional)",
    "admin.peer_dn42_ipv6": "Peer DN42 IPv6",
    "admin.peer_dn42_ipv6_opt": "Peer DN42 IPv6 (optional)",
    "admin.our_address": "Our address{asn}",
    "admin.our_address_placeholder": "fe80::1260 or a ULA",
    "admin.peer_link_local": "Peer link-local address",
    "admin.peer_link_local_opt": "Peer link-local address (optional)",
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
    "admin.redeployding": "Redeploying…",
    "admin.deleting": "Deleting…",
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

    // Admin - Network Search
    "admin.search_network": "Network Search",
    "admin.search_network_desc": "Search network information across nodes using looking-glass queries.",
    "admin.select_node": "Node",
    "admin.select_all_nodes": "All Nodes",
    "admin.query_type": "Query Type",
    "admin.query_target": "Target",
    "admin.query_target_placeholder": "AS4242430001 or 172.24.0.1 or protocol name",
    "admin.query_target_help": "Enter ASN, IP address, or protocol name to search",
    "admin.search": "Search",
    "admin.search_results": "Search Results",
    "admin.clear": "Clear",
    "admin.network_stats": "Network Overview",
    "admin.recent_searches": "Recent Searches",
    "admin.no_recent_searches": "No recent searches",
    "admin.unknown_node": "Unknown Node",
    "admin.success": "Success",
    "admin.failed": "Failed",
    "admin.error": "Error",
    "admin.no_output": "No output",
    "admin.searching": "Searching...",
    "admin.protocol_name": "Protocol",
    "admin.protocol_type": "Type",
    "admin.protocol_state": "State",
    "admin.bgp_state": "BGP State",
    "admin.routes": "Routes",
    "admin.neighbor_id": "Neighbor ID",
    "admin.connect_time": "Connect Time",
    "admin.imported": "Imported",
    "admin.filtered": "Filtered",
    "admin.exported": "Exported",
    "admin.channels": "Channels",
    "admin.raw_output": "Raw Output",
    "admin.node_status_ok": "Status: OK",
    "admin.node_status_error": "Status: Error",

    // Query types
    "lg.ping": "Ping",
    "lg.trace": "Traceroute",
    "lg.mtr": "MTR",
    "lg.route": "Route",
    "lg.bird_route": "BIRD Route Table",
    "lg.bird_protocols": "BIRD Protocols",
    "lg.ospf_neighbors": "OSPF Neighbors",
    "lg.peer_status": "Peer Status",
    "lg.birdc": "Custom BIRD Command",
    "lg.bgp_summary": "BGP Summary",
    "lg.ip_route": "IP Route Table",
    "lg.help_default": "Pick a query type to see the accepted target formats.",
    "lg.view_raw": "Raw BIRD output",

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
    "common.actions": "Actions",
    "common.asn": "ASN",
    "common.ipv4": "IPv4",
    "common.ipv6": "IPv6",
    "common.enabled": "Enabled",
    "common.disabled": "Disabled",
    "common.search_placeholder": "Search nodes, peers...",
    "common.quick_search": "Quick search...",

    // Theme
    "theme.dark": "Dark mode",
    "theme.light": "Light mode",

    // Language
    "lang.switch_to": "中文",

    // Admin - Sidebar sections
    "admin.quick_actions": "Quick Actions",
    "admin.add_node": "Add Node",
    "admin.add_peer": "Add Peer",
    "admin.overview": "Overview",
    "admin.manage": "Manage",
    "admin.network": "Network",
    "admin.system": "System",
    "admin.settings": "Settings",
    "admin.settings_desc": "Configure system-wide parameters for LLA rules, port ranges, ASN, and network blocks.",

    // Admin - Settings Page
    "admin.lla_rules": "LLA Rules (Link-Local Address)",
    "admin.lla_rules_short": "LLA",
    "admin.lla_rules_desc": "Configure how link-local addresses are generated for peer connections.",
    "admin.lla_base_network": "Base Network",
    "admin.lla_base_network_placeholder": "172.24.0.0",
    "admin.lla_base_network_desc": "Base network for generating peer link-local addresses",
    "admin.lla_subnet_prefix": "Subnet Prefix",
    "admin.lla_subnet_prefix_placeholder": "24",
    "admin.lla_subnet_prefix_desc": "Subnet prefix for LLA derivation",
    "admin.port_range": "Intra Link Port Range",
    "admin.port_range_short": "Ports",
    "admin.port_range_desc": "Configure the port range for auto-assigned intra-link listen ports.",
    "admin.intra_port_base": "Base Port",
    "admin.intra_port_base_desc": "Start of port range for auto-assigned intra links",
    "admin.intra_port_max": "Max Port",
    "admin.intra_port_max_desc": "End of port range for auto-assigned intra links",
    "admin.asn_settings": "ASN Settings",
    "admin.asn_settings_short": "ASN",
    "admin.asn_settings_desc": "Configure ASN ranges for nodes and peer assignments.",
    "admin.default_asn": "Default ASN",
    "admin.default_asn_placeholder": "AS65000",
    "admin.default_asn_desc": "Default ASN for nodes (empty = use env)",
    "admin.asn_range_start": "ASN Range Start",
    "admin.asn_range_start_desc": "Start of auto-assigned peer ASN range",
    "admin.asn_range_end": "ASN Range End",
    "admin.asn_range_end_desc": "End of auto-assigned peer ASN range",
    "admin.owned_networks": "Self-Owned Network Blocks",
    "admin.owned_networks_short": "Networks",
    "admin.owned_networks_desc": "Define your network blocks for route announcement.",
    "admin.owned_networks_v4": "IPv4 Blocks (JSON)",
    "admin.owned_networks_v4_placeholder": "[\"172.23.0.0/16\"]",
    "admin.owned_networks_v4_desc": "JSON array of IPv4 CIDR blocks",
    "admin.owned_networks_v6": "IPv6 Blocks (JSON)",
    "admin.owned_networks_v6_placeholder": "[\"fd86:115::/48\"]",
    "admin.owned_networks_v6_desc": "JSON array of IPv6 CIDR blocks",
    "admin.peer_settings": "Peer Defaults",
    "admin.peer_settings_short": "Peer & Rate",
    "admin.peer_settings_desc": "Configure defaults for new peers and rate limits.",
    "admin.peer_wg_mtu": "WireGuard MTU",
    "admin.peer_wg_mtu_desc": "Default MTU for new peers",
    "admin.peer_bgp_extended": "Extended BGP Communities",
    "admin.peer_bgp_extended_desc": "Enable extended communities for new peers",
    "admin.rate_limiting": "Rate Limiting",
    "admin.lg_rate_limit": "Max Queries per Window",
    "admin.lg_rate_limit_desc": "Max looking-glass queries per window",
    "admin.lg_rate_window": "Rate Window (seconds)",
    "admin.lg_rate_window_desc": "Rate limiting window in seconds",
    "admin.save_settings": "Save Settings",
    "common.enabled": "Enabled",
    "common.disabled": "Disabled",
  },

  "zh-CN": {
    // Navigation
    "nav.home": "首页",
    "nav.nodes": "节点",
    "nav.looking_glass": "LG",
    "nav.my_peers": "对等",
    "nav.admin": "管理",
    "nav.logout": "退出登录",
    "nav.logout_text": "退出",
    "nav.login": "登录",
    "nav.role_admin": "管理员",
    "nav.role_user": "用户",
    "nav.map": "地图",

    // Footer
    "footer.powered_by": "技术支持",
    "footer.tech_support": "技术支持 dn42",

    // Home page
    "home.kicker": "dn42 · Anycast · 自动化",
    "home.hero_tagline": "自动化 dn42 对等互联，以及跨节点的公共 Looking Glass。带上你的 ASN，选择一个节点，即可获得即用型 WireGuard + BGP 配置。",
    "home.open_looking_glass": "打开 Looking Glass",
    "home.create_peer": "创建对等",
    "home.peer_with_us": "与我们对等",
    "home.how_to_peer": "如何与我们对等",
    "home.how_to_peer_sub": "四步完成 dn42 对等部署。",
    "home.step1": "使用你的 dn42 ASN 登录（通过 Kioubit 或 Telegram 机器人）。",
    "home.step2": '打开 <a href="/portal/new">新建对等</a>，选择一个节点，粘贴你的 <strong>WireGuard 公钥</strong>。端点是可选的 — 留空则由你的一侧发起连接。',
    "home.step3": "选择隧道内 IP。默认的 <strong>链路本地地址</strong> 开箱即用；也接受 <strong>ULA</strong> (fd00::/8)。",
    "home.step4": "我们会验证并 <strong>自动部署</strong> 到节点。打开对等页面复制我们的端点、公钥和 BGP 邻居地址 — 然后启动你的一侧。",
    "home.stat_nodes": "节点数",
    "home.network_stats": "网络统计",
    "home.network_nodes": "网络节点",
    "home.nodes_search_placeholder": "按名称或 IP 搜索...",
    "home.filter_all": "全部",
    "home.filter_asia": "东亚",
    "home.filter_sea": "东南亚",
    "home.filter_europe": "欧洲",
    "home.filter_na": "北美洲",
    "home.filter_other": "其他",
    "home.filter_oceania": "太平洋与大洋洲",
    "home.node_name": "节点",
    "home.node_location": "位置",
    "home.status": "状态",
    "home.open_state": "开放",
    "home.closed_state": "关闭",
    "home.connect": "连接",
    "home.connect_label": "连接",
    "home.copy_node_info": "复制路由器信息",
    "home.direct_ethernet": "直连以太网",
    "home.list_view": "列表视图",
    "home.grid_view": "网格视图",
    "home.session_capacity": "会话容量",
    "home.dn42_section": "DN42",
    "home.bgp_nodes": "BGP 网络节点",
    "home.pick_node_desc": "选择一个 BGP 路由器以建立对等连接",
    "home.no_nodes_found": "未找到节点",
    "home.no_nodes_found_desc": "尝试调整搜索条件或筛选器。",
    "home.stat_nodes_online": "在线节点",
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
    "home.nodes_nearby": "我们的节点",
    "home.nodes_nearby_sub": "每个节点的实时状态。",
    "home.view_all_nodes": "全部节点",
    "home.quick_lg": "快速查询",
    "home.quick_lg_sub": "查询 BGP 会话、ping 节点、检查路由",
    "home.quick_lg_placeholder": "协议名、IP 或前缀",
    "home.quick_lg_go": "查询",
    "home.quick_lg_help": "提示：留空目标可列出该节点上的所有 BGP 会话。",
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
    "login.debug_hint": "开发/测试用：",
    "login.debug_admin": "🔓 管理员调试登录 (AS65000)",

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
    "new_peer.your_endpoint_opt": "你的 WireGuard 端点（可选）",
    "new_peer.endpoint_placeholder": "host:port (留空 = 对等端拨入我们)",
    "new_peer.dn42_ipv4": "DN42 IPv4",
    "new_peer.dn42_ipv4_opt": "DN42 IPv4（可选）",
    "new_peer.dn42_ipv4_placeholder": "172.20.x.y 或 172.20.x.y/32",
    "new_peer.dn42_ipv6": "DN42 IPv6",
    "new_peer.dn42_ipv6_opt": "DN42 IPv6（可选）",
    "new_peer.dn42_ipv6_placeholder": "fd00::1 或 fd00::1/128",
    "new_peer.link_local": "链路本地地址",
    "new_peer.link_local_opt": "链路本地地址（可选）",
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
    "admin.intra_links": "内网链路",
    "admin.intra_links_sub": "OSPF / iBGP 主干",
    "admin.failed_deploys": "部署失败",
    "admin.failed_deploys_sub_attention": "需要关注",
    "admin.failed_deploys_sub_healthy": "全部正常",
    "admin.members": "成员",
    "admin.members_sub": "{admin} 管理员",
    "admin.queries": "查询",
    "admin.queries_sub": "审计日志",
    "admin.needs_attention": "需要关注 — 部署失败",
    "admin.items": "项",
    "admin.review": "检查",
    "admin.nodes_manage": "管理节点",
    "admin.view_all": "查看全部",
    "admin.node_health": "节点健康",
    "admin.manage": "管理",
    "admin.recent_peerings": "最近的对等",
    "admin.all": "全部",
    "admin.no_peers": "暂无对等。",
    "admin.recent_queries": "最近的查询",
    "admin.no_queries": "暂无查询。",

    // Admin - Dashboard (additional keys)
    "admin.dashboard_desc": "你的 dn42 网络概览",
    "admin.online_nodes": "在线节点",
    "admin.nodes_enabled": "已启用",
    "admin.deployed_peers": "已部署对等",
    "admin.active_bgp_sessions": "活动 BGP 会话",
    "admin.failed_deployments": "部署失败",
    "admin.view_network_map": "查看网络地图 →",
    "admin.network_map": "网络地图",
    "admin.network_map_desc": "所有节点的实时延迟",
    "admin.network_topology": "网络拓扑",
    "admin.network_topology_desc": "带有交互式世界地图可视化的跨节点实时延迟",
    "admin.open_network_map": "打开网络地图",
    "admin.uptime": "最后更新",
    "admin.avg_latency": "平均延迟",
    "admin.max_latency": "最大延迟",
    "admin.min_latency": "最小延迟",
    "admin.refresh": "刷新",
    "admin.auto_refresh": "自动刷新",
    "admin.focus_nodes": "聚焦节点",
    "admin.reset_view": "还原视图",
    "admin.jitter": "网络抖动",
    "admin.search_nodes": "搜索节点...",
    "admin.latency_legend": "延迟 (ms)",
    "admin.node_latency_list": "节点延迟",
    "admin.trend": "趋势",
    "admin.links": "链路",
    "admin.latency": "延迟",
    "admin.admin": "管理员",
    "admin.recent_peers": "最近对等",
    "admin.looking_glass_activity": "Looking glass 活动",
    "admin.ok": "正常",
    "admin.no_failed_deployments": "暂无部署失败",
    "admin.no_queries_yet": "暂无查询",
    "admin.quick_actions": "快捷操作",
    "admin.network_search": "网络搜索",
    "admin.settings": "设置",
    "admin.deployed": "已部署",

    // Admin - Nodes
    "admin.nodes": "节点",
    "admin.nodes_desc": "节点通过 WSS 回连并以 root 身份部署 WireGuard + BIRD 配置。",
    "admin.nodes_count": "节点",
    "admin.peers_count": "对等",
    "admin.users_count": "用户",
    "admin.queries_count": "查询",
    "admin.add_node": "添加节点",
    "admin.name": "名称",
    "admin.location": "位置",
    "admin.public_addr": "公网地址",
    "admin.asn": "ASN",
    "admin.asn_opt": "ASN（可选）",
    "admin.dn42_ipv4": "DN42 IPv4",
    "admin.dn42_ipv4_opt": "DN42 IPv4（可选）",
    "admin.dn42_ipv6": "DN42 IPv6",
    "admin.dn42_ipv6_opt": "DN42 IPv6（可选）",
    "admin.enabled": "已启用",
    "admin.wireguard": "WireGuard",
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
    "admin.node": "节点",
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
    "admin.tab_bird_base": "BIRD 基础",
    "admin.tab_flap": "抖动检测",
    "admin.tab_danger": "危险区域",
    "admin.peers_on_node": "此节点上的对等",
    "admin.no_peers_on_node": "此节点上尚未承载任何对等。",
    "admin.protocol_name": "协议",

    // Admin - Internal links (iBGP/OSPF backbone)
    "admin.intra_links_on_node": "此节点上的内网链路",
    "admin.intra_links_desc": "你自己的节点之间的 iBGP/OSPF 主干 WireGuard 隧道。命名规则：ibgp_xxx.conf，端口 414xx-443xx，LLA fe80::14:xxxx/64。私钥从节点配置中读取（绝不外传），通过 {placeholder} 占位符注入。",
    "admin.intra_remote_node": "对端节点",
    "admin.intra_search": "搜索节点",
    "admin.intra_search_placeholder": "按名称或位置筛选节点…",
    "admin.search_results": "找到 {count} 个节点",
    "admin.no_search_results": "暂无结果，请选择节点和查询类型开始搜索",
    "admin.intra_manual": "（手动 — 在下方填写详情）",
    "admin.intra_remote_pubkey": "公钥",
    "admin.intra_remote_pubkey_placeholder": "44 字符 base64 密钥（从对端节点自动填充）",
    "admin.intra_remote_endpoint": "端点",
    "admin.intra_remote_endpoint_placeholder": "host:port（从对端节点 url 自动填充）",
    "admin.intra_label": "标签",
    "admin.intra_label_placeholder": "frankfurt-amsterdam",
    "admin.intra_listen_port": "监听端口",
    "admin.intra_label_show": "标签",
    "admin.auto_generated": "选择对端时自动生成",
    "admin.auto_filled": "已自动填充",
    "admin.intra_deploy_now": "立即部署",
    "admin.intra_reverse": "同时在远端节点创建反向链路（双向）",
    "admin.intra_create": "创建链路",
    "admin.create_intra_link": "创建链路",
    "admin.intra_creating": "创建中…",
    "admin.intra_protocol": "协议",
    "admin.intra_remote": "对端",
    "admin.intra_lla": "链路本地",
    "admin.intra_latency": "延迟",
    "admin.latency_checking": "检测中…",
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

    // Admin - DN42 BIRD 基础配置（ROA + filter + dnpeers 模板）
    "admin.bird_base_title": "DN42 BIRD2 基础配置",
    "admin.bird_base_desc": "生成 per-peer 片段所继承的共享 BIRD2 骨架（ROA 表、带 ROA 验证的 import/export filter、dnpeers 模板）。含 ROA 刷新 cron 脚本。",
    "admin.bird_base_open": "导出 DN42 基础配置",
    "admin.bird_base_config": "DN42 BIRD2 基础配置",
    "admin.bird_base_install_hint": "安装：保存为 /etc/bird/peers/00_dn42_base.conf，并在 bird.conf 中加入 include \"/etc/bird/peers/*.conf\";。本地 ASN：{asn}。",
    "admin.roa_refresh_script": "ROA 刷新 cron 脚本",
    "admin.roa_refresh_hint": "安装为 /etc/cron.hourly/dn42-roa-refresh（chmod +x）。每小时抓取 dn42 ROA dump 并热重载 BIRD2，使 ROA 验证使用最新数据。",
    "admin.back_to_node": "返回节点",

    // Admin - BGP 抖动检测
    "admin.flap_title": "BGP 抖动检测",
    "admin.flap_desc": "轮询 birdc show protocols，将 BGP 会话状态转换（up↔start/down）记录到环形缓冲区。打开抖动页面即触发一次轮询。",
    "admin.flap_open": "查看抖动时间线",
    "admin.flap_total": "缓冲事件总数",
    "admin.flap_new": "本次轮询新增",
    "admin.flap_bgp_sessions": "当前 BGP 会话数",
    "admin.flap_current_states": "当前 BGP 协议状态（本次轮询）",
    "admin.flap_protocol": "协议",
    "admin.flap_state": "状态",
    "admin.flap_timeline": "转换时间线（最新在前，最近 200 条）",
    "admin.flap_time": "时间（UTC）",
    "admin.flap_from": "从",
    "admin.flap_to": "到",
    "admin.flap_new_badge": "新",
    "admin.flap_no_sessions": "（未发现 BGP 协议——节点可能无 peer，或 birdc 未配置）",
    "admin.flap_no_events": "（尚未记录转换——BGP 状态变化后再次打开此页面）",
    "admin.no_flap_events": "尚无抖动事件记录。",
    "admin.loading": "加载中…",

    // Admin - Peerings
    "admin.peerings_desc": "在所有节点上创建、编辑、重新部署或删除任意对等。",
    "admin.add_peer": "添加对等",
    "admin.peer_asn": "对等 ASN",
    "admin.peer_endpoint": "WireGuard 端点",
    "admin.peer_endpoint_opt": "WireGuard 端点（可选）",
    "admin.peer_endpoint_placeholder": "host:port (留空 = 对等端拨入我们)",
    "admin.peer_wg_pubkey": "WireGuard 公钥",
    "admin.peer_mtu": "WireGuard MTU",
    "admin.peer_dn42_ipv4": "对等 DN42 IPv4",
    "admin.peer_dn42_ipv4_opt": "对等 DN42 IPv4（可选）",
    "admin.peer_dn42_ipv6": "对等 DN42 IPv6",
    "admin.peer_dn42_ipv6_opt": "对等 DN42 IPv6（可选）",
    "admin.our_address": "我方地址{asn}",
    "admin.our_address_placeholder": "fe80::1260 或 ULA",
    "admin.peer_link_local": "对等链路本地地址",
    "admin.peer_link_local_opt": "对等链路本地地址（可选）",
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
    "admin.redeployding": "重新部署中…",
    "admin.deleting": "删除中…",
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

    // Admin - Network Search
    "admin.search_network": "网络搜索",
    "admin.search_network_desc": "使用 Looking Glass 查询在节点间搜索网络信息。",
    "admin.select_node": "节点",
    "admin.select_all_nodes": "所有节点",
    "admin.query_type": "查询类型",
    "admin.query_target": "目标",
    "admin.query_target_placeholder": "AS4242430001 或 172.24.0.1 或 协议名称",
    "admin.query_target_help": "输入 ASN、IP 地址或协议名称进行搜索",
    "admin.search": "搜索",
    "admin.search_results": "搜索结果",
    "admin.clear": "清空",
    "admin.network_stats": "网络概览",
    "admin.recent_searches": "最近搜索",
    "admin.no_recent_searches": "暂无最近搜索",
    "admin.unknown_node": "未知节点",
    "admin.success": "成功",
    "admin.failed": "失败",
    "admin.error": "错误",
    "admin.no_output": "无输出",
    "admin.searching": "搜索中...",
    "admin.protocol_name": "协议",
    "admin.protocol_type": "类型",
    "admin.protocol_state": "状态",
    "admin.bgp_state": "BGP 状态",
    "admin.routes": "路由",
    "admin.neighbor_id": "邻居 ID",
    "admin.connect_time": "连接时间",
    "admin.imported": "已导入",
    "admin.filtered": "已过滤",
    "admin.exported": "已导出",
    "admin.channels": "通道",
    "admin.raw_output": "原始输出",
    "admin.node_status_ok": "状态：正常",
    "admin.node_status_error": "状态：错误",

    // Query types
    "lg.ping": "Ping",
    "lg.trace": "Traceroute",
    "lg.mtr": "MTR",
    "lg.route": "路由",
    "lg.bird_route": "BIRD 路由表",
    "lg.bird_protocols": "BIRD 协议",
    "lg.ospf_neighbors": "OSPF 邻居",
    "lg.peer_status": "Peer 状态",
    "lg.birdc": "自定义 BIRD 命令",
    "lg.bgp_summary": "BGP 摘要",
    "lg.ip_route": "IP 路由表",
    "lg.help_default": "选择查询类型以查看可接受的目标格式。",
    "lg.view_raw": "BIRD 原始输出",

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
    "common.actions": "操作",
    "common.asn": "ASN",
    "common.ipv4": "IPv4",
    "common.ipv6": "IPv6",
    "common.enabled": "已启用",
    "common.disabled": "已禁用",
    "common.search_placeholder": "搜索节点、对等...",
    "common.quick_search": "快速搜索...",

    // Theme
    "theme.dark": "暗色模式",
    "theme.light": "亮色模式",

    // Language
    "lang.switch_to": "English",

    // Admin - Sidebar sections
    "admin.quick_actions": "快捷操作",
    "admin.add_node": "添加节点",
    "admin.add_peer": "添加对等",
    "admin.overview": "概览",
    "admin.manage": "管理",
    "admin.network": "网络",
    "admin.system": "系统",
    "admin.settings": "设置",
    "admin.settings_desc": "配置系统范围的 LLA 规则、端口范围、ASN 和网络块等参数。",

    // Admin - Settings Page
    "admin.lla_rules": "LLA 规则（链路本地地址）",
    "admin.lla_rules_short": "LLA",
    "admin.lla_rules_desc": "配置如何为对等连接生成链路本地地址。",
    "admin.lla_base_network": "基础网络",
    "admin.lla_base_network_placeholder": "172.24.0.0",
    "admin.lla_base_network_desc": "用于生成对等链路本地地址的基础网络",
    "admin.lla_subnet_prefix": "子网前缀",
    "admin.lla_subnet_prefix_placeholder": "24",
    "admin.lla_subnet_prefix_desc": "LLA 派生的子网前缀",
    "admin.port_range": "内网链路端口范围",
    "admin.port_range_short": "端口",
    "admin.port_range_desc": "配置自动分配内网链路监听端口的范围。",
    "admin.intra_port_base": "基础端口",
    "admin.intra_port_base_desc": "自动分配内网链路的端口范围起始值",
    "admin.intra_port_max": "最大端口",
    "admin.intra_port_max_desc": "自动分配内网链路的端口范围结束值",
    "admin.asn_settings": "ASN 设置",
    "admin.asn_settings_short": "ASN",
    "admin.asn_settings_desc": "配置节点和对等分配的 ASN 范围。",
    "admin.default_asn": "默认 ASN",
    "admin.default_asn_placeholder": "AS65000",
    "admin.default_asn_desc": "节点的默认 ASN（留空 = 使用环境变量）",
    "admin.asn_range_start": "ASN 范围起始",
    "admin.asn_range_start_desc": "自动分配对等 ASN 范围的起始值",
    "admin.asn_range_end": "ASN 范围结束",
    "admin.asn_range_end_desc": "自动分配对等 ASN 范围的结束值",
    "admin.owned_networks": "自有网络块",
    "admin.owned_networks_short": "网络",
    "admin.owned_networks_desc": "定义您的网络块用于路由公告。",
    "admin.owned_networks_v4": "IPv4 块（JSON）",
    "admin.owned_networks_v4_placeholder": "[\"172.23.0.0/16\"]",
    "admin.owned_networks_v4_desc": "IPv4 CIDR 块的 JSON 数组",
    "admin.owned_networks_v6": "IPv6 块（JSON）",
    "admin.owned_networks_v6_placeholder": "[\"fd86:115::/48\"]",
    "admin.owned_networks_v6_desc": "IPv6 CIDR 块的 JSON 数组",
    "admin.peer_settings": "对等默认设置",
    "admin.peer_settings_short": "对等 & 速率",
    "admin.peer_settings_desc": "配置新对等的默认设置和速率限制。",
    "admin.peer_wg_mtu": "WireGuard MTU",
    "admin.peer_wg_mtu_desc": "新对等的默认 MTU",
    "admin.peer_bgp_extended": "扩展 BGP 社区",
    "admin.peer_bgp_extended_desc": "为新对等启用扩展社区",
    "admin.rate_limiting": "速率限制",
    "admin.lg_rate_limit": "每窗口最大查询数",
    "admin.lg_rate_limit_desc": "每窗口最大 Looking Glass 查询数",
    "admin.lg_rate_window": "速率窗口（秒）",
    "admin.lg_rate_window_desc": "速率限制窗口（秒）",
    "admin.save_settings": "保存设置",
    "common.enabled": "已启用",
    "common.disabled": "已禁用"
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
  
  const langBtn = document.getElementById('lang-toggle');
  if (langBtn) {
    const globeSvg = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>';
    langBtn.innerHTML = globeSvg;
    langBtn.setAttribute('aria-label', I18N[lang]['lang.switch_to']);
    langBtn.title = I18N[lang]['lang.switch_to'];
  }
}

function setTheme(theme) {
  currentTheme = theme;
  localStorage.setItem('theme', theme);
  document.documentElement.setAttribute('data-theme', theme);
  
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn) {
    if (theme === 'dark') {
      themeBtn.innerHTML = '<svg class="icon-sun" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';
    } else {
      themeBtn.innerHTML = '<svg class="icon-moon" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
    }
    themeBtn.setAttribute('aria-label', I18N[currentLang][theme === 'dark' ? 'theme.light' : 'theme.dark']);
    themeBtn.title = I18N[currentLang][theme === 'dark' ? 'theme.light' : 'theme.dark'];
  }
}

function initI18n() {
  document.documentElement.lang = currentLang === 'zh-CN' ? 'zh-CN' : 'en';
  document.documentElement.setAttribute('data-theme', currentTheme);
  
  setupToggleButtons();
  applyTranslations();
  updateButtonStates();
}

function setupToggleButtons() {
  const topbar = document.querySelector('.topbar-user');
  if (!topbar) return;
  
  const themeBtn = document.getElementById('theme-toggle');
  if (themeBtn && !themeBtn._i18nBound) {
    themeBtn._i18nBound = true;
    themeBtn.addEventListener('click', function() {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      setTheme(newTheme);
      updateButtonStates();
    });
  } else if (!themeBtn) {
    const btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.className = 'icon-toggle';
    btn.type = 'button';
    btn._i18nBound = true;
    btn.addEventListener('click', function() {
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      setTheme(newTheme);
      updateButtonStates();
    });
    topbar.insertBefore(btn, topbar.firstChild);
  }
  
  const langBtn = document.getElementById('lang-toggle');
  if (langBtn && !langBtn._i18nBound) {
    langBtn._i18nBound = true;
    langBtn.addEventListener('click', function() {
      const newLang = currentLang === 'en' ? 'zh-CN' : 'en';
      setLanguage(newLang);
      updateButtonStates();
    });
  } else if (!langBtn) {
    const btn = document.createElement('button');
    btn.id = 'lang-toggle';
    btn.className = 'icon-toggle';
    btn.type = 'button';
    btn._i18nBound = true;
    btn.addEventListener('click', function() {
      const newLang = currentLang === 'en' ? 'zh-CN' : 'en';
      setLanguage(newLang);
      updateButtonStates();
    });
    topbar.insertBefore(btn, topbar.firstChild);
  }
}

function updateButtonStates() {
  const langBtn = document.getElementById('lang-toggle');
  const themeBtn = document.getElementById('theme-toggle');
  
  if (langBtn) {
    langBtn.setAttribute('aria-label', I18N[currentLang]['lang.switch_to']);
    langBtn.title = I18N[currentLang]['lang.switch_to'];
  }
  
  if (themeBtn) {
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
