"""Mock BIRD protocol output data for testing parsers.

Contains simulated outputs for:
- birdc show protocols all <name> (detail view)
- birdc show protocols (list view)
Various states: Established, Idle, Connect, Active, Open, plus error scenarios.
"""

# ==================== birdc show protocols all ====================

# Scenario 1: BGP session - Established, both IPv4 and IPv6 channels healthy
BIRD_PROTOCOL_ESTABLISHED = """protocol ibgp_65001
Description: dn42 peer AS65001 - Frankfurt
BGP state: Established
BGP last state: Established
BGP last error: None
BGP neighbor ID: 172.20.1.1
Connect time: 2d12h30m
Last state change: 2024-01-15 08:30:00
Route statistics:
  Received: 150 imported, 5 filtered
  Exported: 80 exported, 0 preferred
Channel IPv4
  BGP state: Established
  Routes: 100 imported, 50 exported, 3 filtered
Channel IPv6
  BGP state: Established
  Routes: 50 imported, 30 exported, 2 filtered"""

# Scenario 2: BGP session - Idle state (down session)
BIRD_PROTOCOL_IDLE = """protocol ibgp_65002
Description: dn42 peer AS65002 - Paris
BGP state: Idle
BGP last state: Active
BGP last error: Connection refused
BGP neighbor ID: 172.20.2.1
Connect time: 0s
Last state change: 2024-01-16 14:20:00
Route statistics:
  Received: 0 imported, 0 filtered
  Exported: 0 exported, 0 preferred"""

# Scenario 3: BGP session - Active state (trying to connect)
BIRD_PROTOCOL_ACTIVE = """protocol ibgp_65003
Description: dn42 peer AS65003 - Amsterdam
BGP state: Active
BGP last state: Connect
BGP last error: Hold time expired
BGP neighbor ID: 172.20.3.1
Connect time: 0s
Last state change: 2024-01-16 15:00:00
Route statistics:
  Received: 0 imported, 0 filtered
  Exported: 0 exported, 0 preferred
Channel IPv4
  BGP state: Idle
  Routes: 0 imported, 0 exported
Channel IPv6
  BGP state: Idle
  Routes: 0 imported, 0 exported"""

# Scenario 4: BGP session - Open state (negotiation)
BIRD_PROTOCOL_OPEN = """protocol ibgp_65004
Description: dn42 peer AS65004 - London
BGP state: Open
BGP last state: Connect
BGP last error: None
BGP neighbor ID: 172.20.4.1
Connect time: 1m30s
Last state change: 2024-01-16 16:00:00
Route statistics:
  Received: 0 imported, 0 filtered
  Exported: 0 exported, 0 preferred
Channel IPv4
  BGP state: Open
  Routes: 0 imported, 0 exported
Channel IPv6
  BGP state: Open
  Routes: 0 imported, 0 exported"""

# Scenario 5: BGP session - Only IPv4 channel (no IPv6)
BIRD_PROTOCOL_IPV4_ONLY = """protocol ibgp_65005
Description: dn42 peer AS65005 - Berlin (IPv4 only)
BGP state: Established
BGP last state: Established
BGP last error: None
BGP neighbor ID: 172.20.5.1
Connect time: 5d3h15m
Last state change: 2024-01-10 05:45:00
Route statistics:
  Received: 250 imported, 10 filtered
  Exported: 120 exported, 5 preferred
Channel IPv4
  BGP state: Established
  Routes: 250 imported, 120 exported, 10 filtered"""

# Scenario 6: BGP session - Large routes volume
BIRD_PROTOCOL_LARGE_ROUTES = """protocol ibgp_65006
Description: dn42 peer AS65006 - Heavy routes peer
BGP state: Established
BGP last state: Established
BGP last error: None
BGP neighbor ID: 172.20.6.1
Connect time: 10d12h0m
Last state change: 2024-01-05 00:00:00
Route statistics:
  Received: 5000 imported, 200 filtered
  Exported: 3000 exported, 150 preferred
Channel IPv4
  BGP state: Established
  Routes: 3000 imported, 1800 exported, 100 filtered
Channel IPv6
  BGP state: Established
  Routes: 2000 imported, 1200 exported, 100 filtered"""

# Scenario 7: BGP session - Channel with filtering
BIRD_PROTOCOL_FILTERING = """protocol ibgp_65007
Description: dn42 peer AS65007 - Filtered routes
BGP state: Established
BGP last state: Established
BGP last error: None
BGP neighbor ID: 172.20.7.1
Connect time: 1d5h0m
Last state change: 2024-01-15 19:00:00
Route statistics:
  Received: 80 imported, 30 filtered
  Exported: 50 exported, 20 preferred
Channel IPv4
  BGP state: Established
  Routes: 50 imported, 30 exported, 20 filtered
Channel IPv6
  BGP state: Established
  Routes: 30 imported, 20 exported, 10 filtered"""

# Scenario 8: OSPF protocol (non-BGP)
BIRD_PROTOCOL_OSPF = """protocol ospf_area0
Description: OSPF area 0 backbone
BGP state: N/A
BGP last state: N/A
BGP last error: N/A
Route statistics:
  Received: 15 imported, 0 filtered
  Exported: 20 exported, 0 preferred"""

# Scenario 9: Static protocol
BIRD_PROTOCOL_STATIC = """protocol static_routes
Description: Static default routes
BGP state: N/A
BGP last state: N/A
BGP last error: N/A
Route statistics:
  Received: 0 imported, 0 filtered
  Exported: 0 exported, 0 preferred"""

# Scenario 10: Connection error - Network unreachable
BIRD_PROTOCOL_NETWORK_ERROR = """protocol ibgp_65008
Description: dn42 peer AS65008 - Network issue
BGP state: Idle
BGP last state: Active
BGP last error: Network is unreachable
BGP neighbor ID: 172.20.8.1
Connect time: 0s
Last state change: 2024-01-16 17:30:00
Route statistics:
  Received: 0 imported, 0 filtered
  Exported: 0 exported, 0 preferred"""

# Scenario 11: Empty output (error handling)
BIRD_PROTOCOL_EMPTY = ""

# Scenario 12: Malformed output (partial data)
BIRD_PROTOCOL_MALFORMED = """protocol ibgp_65009
Description: Partial data
BGP state: Established"""

# Scenario 13: BGP session - With special characters in description
BIRD_PROTOCOL_SPECIAL_CHARS = """protocol ibgp_65010
Description: Peer with special chars: test_peer-01 (prod) [DE]
BGP state: Established
BGP last state: Established
BGP last error: None
BGP neighbor ID: 172.20.10.1
Connect time: 7d0h0m
Last state change: 2024-01-09 12:00:00
Route statistics:
  Received: 100 imported, 2 filtered
  Exported: 60 exported, 0 preferred
Channel IPv4
  BGP state: Established
  Routes: 60 imported, 40 exported, 1 filtered
Channel IPv6
  BGP state: Established
  Routes: 40 imported, 20 exported, 1 filtered"""

# ==================== birdc show protocols (list view) ====================

# Scenario 14: Protocol list - Full output
BIRD_PROTOCOL_LIST = """Name     Proto   State    BGP state      Routes
bgp_65001 BGP    up       Established    100 imported
bgp_65002 BGP    down     Idle            0 imported
bgp_65003 BGP    up       Active         50 imported
bgp_65004 BGP    up       Open            0 imported
ospf_0    OSPF   up       N/A            15 imported
static_1  Static up       N/A             0 imported
kernel_1  Kernel up       N/A             5 imported
bgp_65005 BGP    up       Established   250 imported"""

# Scenario 15: Protocol list - Single protocol
BIRD_PROTOCOL_LIST_SINGLE = """Name     Proto   State    BGP state      Routes
bgp_65001 BGP    up       Established    100 imported"""

# Scenario 16: Protocol list - Empty
BIRD_PROTOCOL_LIST_EMPTY = ""

# ==================== Test data collections ====================

# All detail view scenarios with expected states
DETAIL_TEST_CASES = [
    {
        "name": "established_bgp",
        "output": BIRD_PROTOCOL_ESTABLISHED,
        "expected_state": "Established",
        "expected_protocol": "ibgp_65001",
        "has_channels": True,
        "expected_channels_count": 2,
    },
    {
        "name": "idle_bgp",
        "output": BIRD_PROTOCOL_IDLE,
        "expected_state": "Idle",
        "expected_protocol": "ibgp_65002",
        "has_channels": False,
    },
    {
        "name": "active_bgp",
        "output": BIRD_PROTOCOL_ACTIVE,
        "expected_state": "Active",
        "expected_protocol": "ibgp_65003",
        "has_channels": True,
        "expected_channels_count": 2,
    },
    {
        "name": "open_bgp",
        "output": BIRD_PROTOCOL_OPEN,
        "expected_state": "Open",
        "expected_protocol": "ibgp_65004",
        "has_channels": True,
        "expected_channels_count": 2,
    },
    {
        "name": "ipv4_only",
        "output": BIRD_PROTOCOL_IPV4_ONLY,
        "expected_state": "Established",
        "expected_protocol": "ibgp_65005",
        "has_channels": True,
        "expected_channels_count": 1,
    },
    {
        "name": "large_routes",
        "output": BIRD_PROTOCOL_LARGE_ROUTES,
        "expected_state": "Established",
        "expected_protocol": "ibgp_65006",
        "has_channels": True,
        "expected_channels_count": 2,
    },
    {
        "name": "filtering",
        "output": BIRD_PROTOCOL_FILTERING,
        "expected_state": "Established",
        "expected_protocol": "ibgp_65007",
        "has_channels": True,
        "expected_channels_count": 2,
    },
    {
        "name": "ospf",
        "output": BIRD_PROTOCOL_OSPF,
        "expected_state": "",  # Non-BGP may not have state
        "expected_protocol": "ospf_area0",
        "has_channels": False,
    },
    {
        "name": "static",
        "output": BIRD_PROTOCOL_STATIC,
        "expected_state": "",
        "expected_protocol": "static_routes",
        "has_channels": False,
    },
    {
        "name": "network_error",
        "output": BIRD_PROTOCOL_NETWORK_ERROR,
        "expected_state": "Idle",
        "expected_protocol": "ibgp_65008",
        "has_channels": False,
    },
    {
        "name": "empty",
        "output": BIRD_PROTOCOL_EMPTY,
        "expected_error": True,
    },
    {
        "name": "malformed",
        "output": BIRD_PROTOCOL_MALFORMED,
        "expected_state": "Established",
        "expected_protocol": "ibgp_65009",
        "has_channels": False,
    },
    {
        "name": "special_chars",
        "output": BIRD_PROTOCOL_SPECIAL_CHARS,
        "expected_state": "Established",
        "expected_protocol": "ibgp_65010",
        "has_channels": True,
        "expected_channels_count": 2,
    },
]

# List view test cases
LIST_TEST_CASES = [
    {
        "name": "multiple_protocols",
        "output": BIRD_PROTOCOL_LIST,
        "expected_count": 8,
        "expected_protocols": [
            "bgp_65001", "bgp_65002", "bgp_65003", "bgp_65004",
            "ospf_0", "static_1", "kernel_1", "bgp_65005"
        ],
    },
    {
        "name": "single_protocol",
        "output": BIRD_PROTOCOL_LIST_SINGLE,
        "expected_count": 1,
        "expected_protocols": ["bgp_65001"],
    },
    {
        "name": "empty",
        "output": BIRD_PROTOCOL_LIST_EMPTY,
        "expected_count": 0,
        "expected_protocols": [],
    },
]


def get_mock_data(use_realistic: bool = True) -> dict:
    """Return a dictionary with all mock data for easy access.
    
    Args:
        use_realistic: If True, includes only realistic scenarios.
                       If False, includes edge cases too.
    
    Returns:
        Dict with keys: established, idle, active, open, ipv4_only,
        large_routes, filtering, ospf, static, network_error,
        empty, malformed, special_chars, list, list_single, list_empty
    """
    data = {
        "established": BIRD_PROTOCOL_ESTABLISHED,
        "idle": BIRD_PROTOCOL_IDLE,
        "active": BIRD_PROTOCOL_ACTIVE,
        "open": BIRD_PROTOCOL_OPEN,
        "ipv4_only": BIRD_PROTOCOL_IPV4_ONLY,
        "large_routes": BIRD_PROTOCOL_LARGE_ROUTES,
        "filtering": BIRD_PROTOCOL_FILTERING,
        "ospf": BIRD_PROTOCOL_OSPF,
        "static": BIRD_PROTOCOL_STATIC,
        "network_error": BIRD_PROTOCOL_NETWORK_ERROR,
        "special_chars": BIRD_PROTOCOL_SPECIAL_CHARS,
        "list": BIRD_PROTOCOL_LIST,
        "list_single": BIRD_PROTOCOL_LIST_SINGLE,
        "list_empty": BIRD_PROTOCOL_LIST_EMPTY,
    }
    
    if not use_realistic:
        data["empty"] = BIRD_PROTOCOL_EMPTY
        data["malformed"] = BIRD_PROTOCOL_MALFORMED
    
    return data


# Quick usage example
if __name__ == "__main__":
    from app.lg.summary import parse_bird_protocols_all, parse_bird_protocols_list
    
    print("=" * 60)
    print("Testing BIRD Protocol Parsers with Mock Data")
    print("=" * 60)
    
    # Test detail view parsing
    print("\n--- Detail View Tests ---")
    for case in DETAIL_TEST_CASES[:3]:
        result = parse_bird_protocols_all(case["output"])
        print(f"\nTest: {case['name']}")
        if "error" in result:
            print(f"  Result: ERROR - {result['error']}")
        else:
            print(f"  Protocol: {result['protocol_name']}")
            print(f"  State: {result['bgp_state']}")
            print(f"  Channels: {len(result['channels'])}")
            print(f"  Routes: imported={result['routes_imported']}, exported={result['routes_exported']}")
    
    # Test list view parsing
    print("\n--- List View Tests ---")
    for case in LIST_TEST_CASES[:2]:
        result = parse_bird_protocols_list(case["output"])
        print(f"\nTest: {case['name']}")
        print(f"  Found {len(result)} protocols")
        for proto in result[:3]:
            print(f"    - {proto['name']}: {proto['type']} ({proto['state']})")