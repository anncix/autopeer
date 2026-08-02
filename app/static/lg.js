/**
 * Shared Looking-Glass helpers.
 *
 * Exposed on `window.LG` so both the public LG page (lg.html) and the admin
 * Network Search page (network_search.html) can render BIRD protocol data
 * without duplicating the parser logic.
 */
(function (global) {
  "use strict";

  function escapeHtml(text) {
    if (text === null || text === undefined) return "";
    var div = document.createElement("div");
    div.textContent = String(text);
    return div.innerHTML;
  }

  /**
   * Format duration string from BIRD output (e.g. "1d 9h", "22h 33m", "3m 30s")
   */
  function formatDuration(duration) {
    if (!duration) return "—";
    return duration.trim();
  }

  /**
   * Render a single channel status (IPv4 or IPv6) as a dot + duration
   */
  function renderChannelStatus(channel) {
    if (!channel) return '<span class="lg-channel-muted">—</span>';
    var state = channel.bgp_state || channel.state || "";
    var isUp = state.toLowerCase() === "established";
    var dotClass = isUp ? "dot-online" : (state ? "dot-offline" : "dot-unknown");
    var duration = channel.connect_time || channel.duration || "";
    var bgpClass = isUp ? "ok" : (state ? "warn" : "muted");
    
    var html = '<span class="lg-channel-status ' + bgpClass + '">';
    html += '<span class="lg-status-dot ' + dotClass + '"></span>';
    html += '<span class="lg-channel-type">' + escapeHtml((channel.type || "").toUpperCase()) + '</span>';
    if (duration) {
      html += '<span class="lg-channel-duration">' + escapeHtml(duration) + '</span>';
    }
    html += '</span>';
    return html;
  }

  /**
   * Render the parsed output of `birdc show protocols all <name>` or
   * `birdc show protocols` into a rich, interactive view.
   *
   * @param {object} data - Parsed payload from the backend.
   *   - mode === "list"   -> { mode, protocols: [{name,type,state,bgp_state,route_count}] }
   *   - mode === "detail" -> { mode, protocol_name, description, state, bgp_state, neighbor_id,
   *                            connect_time, last_change, bgp_last_error, routes_imported,
   *                            routes_exported, routes_filtered, channels:[{type,bgp_state,
   *                            routes_imported,routes_exported}], raw }
   * @returns {string} HTML string ready to be injected with innerHTML.
   */
  function renderBirdProtocols(data) {
    if (!data) return '<p class="lg-empty" style="color:var(--text-3)">No parsed data</p>';

    if (data.mode === "list" && Array.isArray(data.protocols)) {
      var protos = data.protocols;
      if (protos.length === 0) {
        return '<div class="lg-empty-state"><p>No BIRD protocols returned. Run a query with an empty target to list all protocols.</p></div>';
      }

      var html = '<div class="lg-proto-list">';
      for (var i = 0; i < protos.length; i++) {
        var p = protos[i] || {};
        var stateClass = p.state === "up" ? "ok" : (p.state === "down" ? "err" : "warn");
        var bgpClass = p.bgp_state === "Established" ? "ok" : (p.bgp_state ? "warn" : "muted");
        var isExpanded = false;

        html += '<div class="lg-proto-row">';
        html += '<div class="lg-proto-main">';
        // Protocol name (ASN-like)
        html += '<div class="lg-proto-name">' + escapeHtml(p.name || "") + '</div>';
        
        // Channel statuses (IPv4/IPv6)
        html += '<div class="lg-proto-channels">';
        html += '<div class="lg-channel ' + bgpClass + '">';
        html += '<span class="lg-status-dot ' + (p.bgp_state === "Established" ? "dot-online" : "dot-offline") + '"></span>';
        html += '<span class="lg-channel-label">BGP</span>';
        html += '</div>';
        html += '</div>';
        
        // Protocol type
        html += '<div class="lg-proto-type">' + escapeHtml(p.type || "—") + '</div>';
        
        // State
        html += '<div class="lg-proto-state ' + stateClass + '">';
        html += escapeHtml(p.state || "—");
        html += '</div>';
        
        // Route count
        if (p.route_count) {
          html += '<div class="lg-proto-routes">' + escapeHtml(String(p.route_count)) + ' imported</div>';
        }
        
        // Expand toggle
        html += '<button class="lg-proto-toggle" onclick="this.closest(\'.lg-proto-row\').classList.toggle(\'expanded\')">';
        html += '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>';
        html += '</button>';
        html += '</div>';
        
        // Expanded detail
        html += '<div class="lg-proto-detail">';
        html += '<div class="lg-detail-row"><span class="lg-detail-label">Name</span><span class="lg-detail-value mono">' + escapeHtml(p.name || "") + '</span></div>';
        html += '<div class="lg-detail-row"><span class="lg-detail-label">Type</span><span class="lg-detail-value">' + escapeHtml(p.type || "—") + '</span></div>';
        html += '<div class="lg-detail-row"><span class="lg-detail-label">State</span><span class="lg-detail-value">' + escapeHtml(p.state || "—") + '</span></div>';
        html += '<div class="lg-detail-row"><span class="lg-detail-label">BGP State</span><span class="lg-detail-value">' + escapeHtml(p.bgp_state || "—") + '</span></div>';
        html += '<div class="lg-detail-row"><span class="lg-detail-label">Routes</span><span class="lg-detail-value">' + escapeHtml(String(p.route_count || 0)) + '</span></div>';
        html += '</div>';
        
        html += '</div>';
      }
      html += '</div>';
      return html;
    }

    if (data.mode === "detail") {
      var d = data;
      var out = '<div class="lg-proto-detail-view">';

      // Header
      out += '<div class="lg-detail-header">';
      out += '<h3 class="lg-detail-title">' + escapeHtml(d.protocol_name || "Unknown") + "</h3>";
      if (d.description) out += '<span class="lg-detail-desc">' + escapeHtml(d.description) + "</span>";
      out += "</div>";

      // Status cards
      var bgpClass = d.bgp_state === "Established" ? "ok" : (d.bgp_state ? "warn" : "err");
      out += '<div class="lg-status-row">';
      
      out += '<div class="lg-status-card ' + bgpClass + '">';
      out += '<span class="lg-status-label">BGP State</span>';
      out += '<span class="lg-status-value">' + escapeHtml(d.bgp_state || "—") + "</span>";
      if (d.bgp_last_error) out += '<span class="lg-status-sub err">' + escapeHtml(d.bgp_last_error) + "</span>";
      out += "</div>";

      out += '<div class="lg-status-card">';
      out += '<span class="lg-status-label">Neighbor ID</span>';
      out += '<span class="lg-status-value mono">' + escapeHtml(d.neighbor_id || "—") + "</span>";
      out += "</div>";

      out += '<div class="lg-status-card">';
      out += '<span class="lg-status-label">Connect Time</span>';
      out += '<span class="lg-status-value">' + escapeHtml(d.connect_time || "—") + "</span>";
      out += "</div>";

      out += '<div class="lg-status-card">';
      out += '<span class="lg-status-label">State</span>';
      out += '<span class="lg-status-value">' + escapeHtml(d.state || "—") + "</span>";
      if (d.last_change) out += '<span class="lg-status-sub">' + escapeHtml(d.last_change) + "</span>";
      out += "</div>";
      out += "</div>";

      // Route statistics
      if (d.routes_imported || d.routes_exported || d.routes_filtered) {
        out += '<div class="lg-route-stats">';
        out += '<div class="lg-route-stat">';
        out += '<span class="lg-route-num">' + escapeHtml(String(d.routes_imported || 0)) + '</span>';
        out += '<span class="lg-route-label">Imported</span>';
        out += '</div>';
        out += '<div class="lg-route-stat">';
        out += '<span class="lg-route-num">' + escapeHtml(String(d.routes_filtered || 0)) + '</span>';
        out += '<span class="lg-route-label">Filtered</span>';
        out += '</div>';
        out += '<div class="lg-route-stat">';
        out += '<span class="lg-route-num">' + escapeHtml(String(d.routes_exported || 0)) + '</span>';
        out += '<span class="lg-route-label">Exported</span>';
        out += '</div>';
        out += "</div>";
      }

      // Channel details (IPv4/IPv6)
      if (Array.isArray(d.channels) && d.channels.length > 0) {
        out += '<div class="lg-channels-section">';
        out += '<h4>Channels</h4>';
        out += '<div class="lg-channel-cards">';
        for (var ci = 0; ci < d.channels.length; ci++) {
          var ch = d.channels[ci] || {};
          var chClass = ch.bgp_state === "Established" ? "ok" : (ch.bgp_state ? "warn" : "muted");
          out += '<div class="lg-channel-card ' + chClass + '">';
          out += '<div class="lg-channel-card-header">';
          out += '<span class="lg-channel-type-label">' + escapeHtml(ch.type || "") + "</span>";
          out += '<span class="lg-channel-state">' + escapeHtml(ch.bgp_state || "—") + "</span>";
          out += "</div>";
          out += '<div class="lg-channel-card-routes">';
          out += '<span>' + escapeHtml(String(ch.routes_imported || 0)) + ' imported</span>';
          out += '<span>' + escapeHtml(String(ch.routes_exported || 0)) + ' exported</span>';
          out += "</div>";
          out += "</div>";
        }
        out += "</div>";
        out += "</div>";
      }

      // Raw output
      if (d.raw) {
        out += '<details class="lg-raw-toggle"><summary>Raw Output</summary><pre>' + escapeHtml(d.raw) + "</pre></details>";
      }

      out += "</div>";
      return out;
    }

    return '<p class="lg-empty" style="color:var(--text-3)">Unknown BIRD data format</p>';
  }

  global.LG = {
    escapeHtml: escapeHtml,
    renderBirdProtocols: renderBirdProtocols,
  };
})(window);
