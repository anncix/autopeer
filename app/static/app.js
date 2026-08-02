/* dn42 Autopeer WebUI — progressive enhancement. No framework, no build step.
   Everything here is optional sugar: with JS disabled the forms still POST and pages still work. */
(function () {
  "use strict";

  // ---------- copy to clipboard ----------
  function writeClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    // Fallback for non-secure contexts (plain http on a LAN IP).
    return new Promise(function (resolve, reject) {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      try {
        document.execCommand("copy");
        resolve();
      } catch (err) {
        reject(err);
      } finally {
        document.body.removeChild(ta);
      }
    });
  }

  function flashButton(btn, label) {
    var original = btn.dataset.label || btn.textContent;
    btn.dataset.label = original;
    btn.textContent = label;
    setTimeout(function () {
      btn.textContent = btn.dataset.label;
    }, 1400);
  }

  // ---------- async looking glass result rendering ----------
  function renderLgResult(container, data) {
    var ok = !!data.ok;
    var text =
      data.output != null ? data.output : data.detail != null ? data.detail : (window.getTranslation ? window.getTranslation('flash.query_failed') : "Query failed");
    if (!text) text = (window.getTranslation ? window.getTranslation('flash.no_output') : "(no output)");
    container.innerHTML = "";
    var wrap = document.createElement("div");
    wrap.className = "codewrap";
    var copy = document.createElement("button");
    copy.type = "button";
    copy.className = "copy-btn";
    copy.textContent = window.getTranslation ? window.getTranslation('common.copy') : "Copy";
    var pre = document.createElement("pre");
    pre.className = "terminal " + (ok ? "ok" : "bad");
    pre.textContent = text;
    wrap.appendChild(copy);
    wrap.appendChild(pre);
    container.appendChild(wrap);
  }

  function fadeRemove(el) {
    if (!el) return;
    el.style.transition = "opacity 0.3s";
    el.style.opacity = "0";
    setTimeout(function () {
      el.remove();
    }, 300);
  }

  function peerLinkLocalFromAsn(value) {
    var asn = (value || "").trim().toUpperCase();
    if (asn.indexOf("AS") === 0) asn = asn.slice(2);
    if (!/^\d+$/.test(asn)) return "";
    var suffix;
    if (asn.length < 4) {
      suffix = asn;
    } else if (asn.indexOf("424242") === 0) {
      suffix = asn.slice(6);
    } else {
      suffix = asn.slice(-4);
    }
    suffix = suffix.replace(/^0+/, "") || "0";
    return "fe80::" + suffix.toLowerCase();
  }

  // Adaptive target placeholder for the looking glass: `bird` takes a BIRD protocol name, not an
  // IP/host/prefix, so swap the placeholder (and its i18n key) when that query type is chosen.
  function setupLgTargetPlaceholder() {
    var select = document.getElementById("lg-query-type");
    var input = document.getElementById("lg-target");
    if (!select || !input) return;
    var defaultKey = "lg.target_placeholder";
    var birdKey = "lg.target_placeholder_bird";
    function sync() {
      var isBird = select.value === "bird";
      var key = isBird ? birdKey : defaultKey;
      input.setAttribute("data-i18n-placeholder", key);
      var text = window.getTranslation ? window.getTranslation(key, {}) : null;
      if (text && text !== key) {
        input.setAttribute("placeholder", text);
      }
    }
    select.addEventListener("change", sync);
    sync();
  }

  function setupAdminPeerForm() {
    var asnInput = document.getElementById("admin-peer-asn");
    var addrInput = document.getElementById("admin-peer-link-address");
    if (!asnInput || !addrInput) return;

    function maybeFillPeerAddress() {
      var next = peerLinkLocalFromAsn(asnInput.value);
      var previous = addrInput.dataset.autofilledValue || "";
      if (!next) return;
      if (!addrInput.value.trim() || addrInput.value.trim() === previous) {
        addrInput.value = next;
        addrInput.dataset.autofilledValue = next;
      }
    }

    asnInput.addEventListener("input", maybeFillPeerAddress);
    asnInput.addEventListener("change", maybeFillPeerAddress);
    maybeFillPeerAddress();
  }

  // ---------- intra links tab: progressive-enhancement (create via fetch, refresh list in place) ----------
  // The links form keeps its native action= POST for no-JS fallback. When JS is on we intercept
  // submit, POST JSON to the /api variant, then re-fetch the /json list and re-render the table
  // body — no full page reload, the tab stays put.
  // 鏈路表單保留原生 action= POST 供無 JS 回退。JS 啟用時攔截 submit,POST JSON 到 /api 變體,
  // 再重新抓取 /json 列表並重渲染表格 body——不整頁重載,頁籤保持不動。
  function deployBadge(status) {
    var tones = { deployed: "ok", failed: "bad", deploying: "warn" };
    var tone = tones[status] || "neutral";
    var text = (status || "").replace(/_/g, " ");
    return '<span class="badge badge-' + tone + '" data-i18n="status.' + status + '">' + text + "</span>";
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function renderIntraLinksTable(tbody, links) {
    tbody.innerHTML = "";
    if (!links.length) {
      var tr = document.createElement("tr");
      tr.innerHTML =
        '<td colspan="5" class="empty-state" data-i18n="admin.no_intra_links">No internal links on this node yet.</td>';
      tbody.appendChild(tr);
      return;
    }
    links.forEach(function (l) {
      var tr = document.createElement("tr");
      var remote = l.remote_name ? esc(l.remote_name) : "—";
      tr.innerHTML =
        '<td class="mono nowrap">' + remote + "</td>" +
        '<td class="mono nowrap">' + esc(l.link_local_address) + "</td>" +
        '<td class="mono nowrap latency-cell" data-link-id="' + esc(l.id) + '">' +
          '<span class="latency-placeholder" data-i18n="admin.latency_checking">Checking…</span>' +
        "</td>" +
        '<td class="nowrap">' + deployBadge(l.deploy_status) + "</td>" +
        '<td class="nowrap">' +
          '<form method="post" action="/admin/nodes/' + esc(nodeIdFromTable(tbody)) + "/intra-links/" + esc(l.id) + '/deploy" style="display:inline">' +
            '<button type="submit" class="btn btn-secondary btn-sm" data-i18n="admin.redeploy">Redeploy</button>' +
          "</form>" +
          '<form method="post" action="/admin/nodes/' + esc(nodeIdFromTable(tbody)) + "/intra-links/" + esc(l.id) + '/delete" style="display:inline" data-confirm="Delete intra link ' + esc(l.protocol_name) + "? This tears down the tunnel on the node.\">" +
            '<button type="submit" class="btn-danger btn-sm" data-i18n="admin.delete_peer">Delete</button>' +
          "</form>" +
        "</td>";
      tbody.appendChild(tr);
    });
  }

  function checkLatency(nodeId, linkId, cell) {
    cell.innerHTML = '<span class="latency-placeholder" data-i18n="admin.latency_checking">Checking…</span>';
    fetch("/admin/nodes/" + encodeURIComponent(nodeId) + "/intra-links/" + encodeURIComponent(linkId) + "/latency", {
      headers: { Accept: "application/json" },
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        if (data.ok && data.latency_ms != null) {
          var cls = data.latency_ms < 10 ? "latency-good" : data.latency_ms < 50 ? "latency-warn" : "latency-bad";
          cell.innerHTML = '<span class="latency-value ' + cls + '">' + esc(data.latency_ms.toFixed(1)) + ' ms</span>';
        } else {
          cell.innerHTML = '<span class="latency-value latency-bad">—</span>';
        }
      })
      .catch(function () {
        cell.innerHTML = '<span class="latency-value latency-bad">—</span>';
      });
  }

  function refreshLatencyForAll(nodeId) {
    var cells = document.querySelectorAll(".latency-cell");
    cells.forEach(function (cell) {
      var linkId = cell.getAttribute("data-link-id");
      if (linkId) checkLatency(nodeId, linkId, cell);
    });
  }

  // The links table sits under /admin/nodes/{node_id}/edit; we extract node_id from the table's
  // data-node-id attribute (set in the template) rather than parsing the URL.
  function nodeIdFromTable(tbody) {
    return tbody.getAttribute("data-node-id") || "";
  }

  function setupIntraLinks() {
    var form = document.getElementById("intra-link-form");
    var tbody = document.getElementById("intra-links-tbody");
    if (!tbody) return;
    var nodeId = nodeIdFromTable(tbody);
    var flashBox = document.getElementById("intra-link-flash");

    function refresh() {
      return fetch("/admin/nodes/" + encodeURIComponent(nodeId) + "/intra-links/json", {
        headers: { Accept: "application/json" },
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          renderIntraLinksTable(tbody, data.links || []);
          var badge = document.querySelector('[data-tab="links"] .tab-count');
          if (badge) badge.textContent = String(data.count || 0);
          refreshLatencyForAll(nodeId);
        })
        .catch(function () { /* network error — leave the existing table in place */ });
    }

    function showIntraFlash(container, message, ok) {
      if (!container) return;
      var div = document.createElement("div");
      div.className = "flash flash-" + (ok ? "success" : "error");
      div.innerHTML =
        '<span>' + esc(message) + "</span>" +
        '<button type="button" class="flash-close" aria-label="close">×</button>';
      container.innerHTML = "";
      container.appendChild(div);
      if (ok) {
        setTimeout(function () {
          if (div.parentNode) div.remove();
        }, 6000);
      }
    }

    refresh();

    // Event-delegated submit handler for the per-row redeploy / delete forms.
    tbody.addEventListener("submit", function (e) {
      var f = e.target;
      if (!f || f.tagName !== "FORM") return;
      var action = f.getAttribute("action") || "";
      var isDeploy = /\/intra-links\/[^/]+\/deploy$/.test(action);
      var isDelete = /\/intra-links\/[^/]+\/delete$/.test(action);
      if (!isDeploy && !isDelete) return;

      e.stopPropagation();
      var confirmMsg = f.getAttribute("data-confirm");
      if (confirmMsg && !window.confirm(confirmMsg)) {
        e.preventDefault();
        return;
      }
      e.preventDefault();

      var btn = f.querySelector('button[type="submit"]');
      var prev = btn ? btn.textContent : "";
      var workingLabel = isDeploy
        ? (window.getTranslation ? window.getTranslation("admin.redeployding") : "Redeploying…")
        : (window.getTranslation ? window.getTranslation("admin.deleting") : "Deleting…");
      if (btn) { btn.disabled = true; btn.textContent = workingLabel; }

      fetch(action + "/api", {
        method: "POST",
        headers: { Accept: "application/json" },
      })
        .then(function (r) { return r.json().catch(function () { return { ok: false, message: "HTTP " + r.status }; }); })
        .then(function (data) {
          showIntraFlash(flashBox, data.message || "", data.ok);
          if (data.ok) {
            refresh();
          } else if (btn) {
            btn.disabled = false;
            btn.textContent = prev;
          }
        })
        .catch(function (err) {
          showIntraFlash(flashBox, "Request failed: " + err, false);
          if (btn) { btn.disabled = false; btn.textContent = prev; }
        });
    });

    // Form handling (only when form exists — i.e. on the separate create-link page)
    if (!form) return;

    var selfNodeName = form.getAttribute("data-node-name") || "";
    var remoteSelect = form.querySelector('[name="remote_node_id"]');
    var pubkeyInput = form.querySelector('[name="remote_public_key"]');
    var endpointInput = form.querySelector('[name="remote_endpoint"]');
    var labelInput = form.querySelector('[name="label"]');

    var lastAutoFilledPubkey = "";
    var lastAutoFilledEndpoint = "";

    function generateLabel(remoteName) {
      if (!selfNodeName || !remoteName) return "";
      return selfNodeName + "_" + remoteName;
    }

    function autoFillFromNode(nodeData, remoteName) {
      if (!nodeData) return;
      if (pubkeyInput && nodeData.wg_public_key && (pubkeyInput.value === lastAutoFilledPubkey || !lastAutoFilledPubkey)) {
        pubkeyInput.value = nodeData.wg_public_key;
        lastAutoFilledPubkey = nodeData.wg_public_key;
      }
      if (endpointInput && nodeData.url && (endpointInput.value === lastAutoFilledEndpoint || !lastAutoFilledEndpoint)) {
        endpointInput.value = nodeData.url;
        lastAutoFilledEndpoint = nodeData.url;
      }
      if (labelInput && remoteName) {
        labelInput.value = generateLabel(remoteName);
      }
    }

    if (remoteSelect) {
      remoteSelect.addEventListener("change", function () {
        var val = remoteSelect.value;
        if (!val) {
          lastAutoFilledPubkey = "";
          lastAutoFilledEndpoint = "";
          if (labelInput) labelInput.value = "";
          return;
        }
        var opt = remoteSelect.options[remoteSelect.selectedIndex];
        var remoteName = opt.getAttribute("data-name") || "";
        var cachedData = {
          wg_public_key: opt.getAttribute("data-pubkey") || "",
          url: opt.getAttribute("data-url") || "",
        };
        if (cachedData.wg_public_key || cachedData.url) {
          autoFillFromNode(cachedData, remoteName);
        } else {
          fetch("/admin/nodes/" + encodeURIComponent(val) + "/info", {
            headers: { Accept: "application/json" },
          })
            .then(function (r) { return r.json(); })
            .then(function (data) { autoFillFromNode(data, remoteName); })
            .catch(function () { /* silently ignore */ });
        }
      });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = form.querySelector('button[type="submit"]');
      var prev = btn ? btn.textContent : "";
      var creating = window.getTranslation ? window.getTranslation("admin.intra_creating") : "Creating…";
      if (btn) { btn.disabled = true; btn.textContent = creating; }
      var payload = {
        remote_node_id: (form.querySelector('[name="remote_node_id"]') || {}).value || "",
        remote_public_key: (form.querySelector('[name="remote_public_key"]') || {}).value || "",
        remote_endpoint: (form.querySelector('[name="remote_endpoint"]') || {}).value || "",
        label: (form.querySelector('[name="label"]') || {}).value || "",
        deploy: !!(form.querySelector('[name="deploy"]') || {}).checked,
        reverse: !!(form.querySelector('[name="reverse"]') || {}).checked,
      };
      fetch("/admin/nodes/" + encodeURIComponent(nodeId) + "/intra-links/api", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json().catch(function () { return { ok: false, message: "HTTP " + r.status }; }); })
        .then(function (data) {
          showIntraFlash(flashBox, data.message || "", data.ok);
          if (data.reverse_message) {
            showIntraFlash(flashBox, data.reverse_message, !!data.reverse_ok);
          }
          if (data.ok) {
            form.querySelector('[name="remote_public_key"]').value = "";
            form.querySelector('[name="remote_endpoint"]').value = "";
            if (labelInput) labelInput.value = "";
            if (remoteSelect) remoteSelect.value = "";
            lastAutoFilledPubkey = "";
            lastAutoFilledEndpoint = "";
            refresh();
          }
        })
        .catch(function (err) {
          showIntraFlash(flashBox, "Network error: " + err.message, false);
        })
        .finally(function () {
          if (btn) { btn.disabled = false; btn.textContent = prev; }
        });
    });
  }

  // ---------- OSPF / BIRD-base / Flap tab inline loading ----------
  var tabDataLoaded = { ospf: false, "bird-base": false, flap: false };

  function tabNodeId() {
    var tbody = document.getElementById("intra-links-tbody");
    return tbody ? tbody.getAttribute("data-node-id") : "";
  }

  function loadOspfTab() {
    var nodeId = tabNodeId();
    var box = document.getElementById("ospf-content");
    if (!box || !nodeId || tabDataLoaded.ospf) return;
    box.innerHTML = '<div class="loading" data-i18n="admin.loading">Loading…</div>';
    fetch("/admin/nodes/" + encodeURIComponent(nodeId) + "/ospf/json", {
      headers: { Accept: "application/json" },
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        tabDataLoaded.ospf = true;
        if (data.ok && data.neighbors) {
          box.innerHTML =
            '<div class="status-label" data-i18n="admin.ospf_neighbors">OSPF neighbors (birdc show ospf neighbor — v4 + v6)</div>' +
            '<pre class="terminal">' + esc(data.neighbors) + "</pre>";
        } else {
          box.innerHTML =
            '<pre class="terminal bad">' + esc(data.error || "No OSPF neighbor output.") + "</pre>";
        }
      })
      .catch(function (err) {
        box.innerHTML = '<pre class="terminal bad">' + esc("Failed: " + err.message) + "</pre>";
      });
  }

  function loadBirdBaseTab() {
    var nodeId = tabNodeId();
    var box = document.getElementById("bird-base-content");
    if (!box || !nodeId || tabDataLoaded["bird-base"]) return;
    box.innerHTML = '<div class="loading" data-i18n="admin.loading">Loading…</div>';
    fetch("/admin/nodes/" + encodeURIComponent(nodeId) + "/bird-base/json", {
      headers: { Accept: "application/json" },
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        tabDataLoaded["bird-base"] = true;
        if (data.ok) {
          box.innerHTML =
            '<div class="status-label">DN42 BIRD2 base config</div>' +
            '<pre class="terminal">' + esc(data.bird_base) + "</pre>" +
            '<div class="status-label" style="margin-top:16px">ROA refresh cron script</div>' +
            '<pre class="terminal">' + esc(data.roa_script) + "</pre>";
        } else {
          box.innerHTML = '<pre class="terminal bad">' + esc(data.error || "Failed to generate.") + "</pre>";
        }
      })
      .catch(function (err) {
        box.innerHTML = '<pre class="terminal bad">' + esc("Failed: " + err.message) + "</pre>";
      });
  }

  function loadFlapTab() {
    var nodeId = tabNodeId();
    var box = document.getElementById("flap-content");
    if (!box || !nodeId || tabDataLoaded.flap) return;
    box.innerHTML = '<div class="loading" data-i18n="admin.loading">Loading…</div>';
    fetch("/admin/nodes/" + encodeURIComponent(nodeId) + "/flap/json", {
      headers: { Accept: "application/json" },
    })
      .then(function (r) { return r.json().catch(function () { return { ok: false }; }); })
      .then(function (data) {
        tabDataLoaded.flap = true;
        if (data.ok) {
          var html = "";
          if (data.current_states && Object.keys(data.current_states).length) {
            html += '<div class="status-label" style="margin-bottom:8px">Current BGP states</div><table class="data-table"><thead><tr><th>Protocol</th><th>State</th></tr></thead><tbody>';
            for (var proto in data.current_states) {
              var state = data.current_states[proto];
              var cls = state === "up" ? "badge-active" : state === "start" ? "badge-warn" : "badge-error";
              html += '<tr><td class="mono nowrap">' + esc(proto) + '</td><td><span class="badge ' + cls + '">' + esc(state) + "</span></td></tr>";
            }
            html += "</tbody></table>";
          }
          if (data.events && data.events.length) {
            html += '<div class="status-label" style="margin:12px 0 8px">Recent flap events</div><table class="data-table"><thead><tr><th>Time</th><th>Protocol</th><th>From</th><th>To</th></tr></thead><tbody>';
            data.events.slice(-20).reverse().forEach(function (ev) {
              html += "<tr><td class=\"mono nowrap\">" + esc(ev.time || "") + "</td><td class=\"mono nowrap\">" + esc(ev.protocol || "") + "</td><td>" + esc(ev.from || "") + "</td><td>" + esc(ev.to || "") + "</td></tr>";
            });
            html += "</tbody></table>";
          }
          if (!html) {
            html = '<div class="empty-state" data-i18n="admin.no_flap_events">No flap events recorded yet.</div>';
          }
          box.innerHTML = html;
        } else {
          box.innerHTML = '<pre class="terminal bad">' + esc(data.error || "Failed to fetch flap data.") + "</pre>";
        }
      })
      .catch(function (err) {
        box.innerHTML = '<pre class="terminal bad">' + esc("Failed: " + err.message) + "</pre>";
      });
  }

  // ---------- tab switching ----------
  function setupTabs() {
    var tabBtns = document.querySelectorAll(".tab-btn");
    if (!tabBtns.length) return;

    function activateTab(tabName) {
      tabBtns.forEach(function (btn) {
        var isActive = btn.getAttribute("data-tab") === tabName;
        btn.classList.toggle("is-active", isActive);
        btn.setAttribute("aria-selected", isActive ? "true" : "false");
      });
      var panels = document.querySelectorAll(".tab-panel");
      panels.forEach(function (panel) {
        var isActive = panel.getAttribute("data-panel") === tabName;
        panel.classList.toggle("is-active", isActive);
        if (isActive) {
          panel.removeAttribute("hidden");
        } else {
          panel.setAttribute("hidden", "");
        }
      });
      // Update URL hash without triggering scroll
      if (history.replaceState) {
        history.replaceState(null, "", "#" + tabName);
      }
      // Lazy-load tab content
      if (tabName === "ospf") loadOspfTab();
      if (tabName === "bird-base") loadBirdBaseTab();
      if (tabName === "flap") loadFlapTab();
    }

    tabBtns.forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var tabName = btn.getAttribute("data-tab");
        if (tabName) activateTab(tabName);
      });
    });

    // Activate tab from URL hash (e.g. #peers, #links)
    var hash = window.location.hash.replace("#", "");
    if (hash) {
      var exists = Array.prototype.some.call(tabBtns, function (b) {
        return b.getAttribute("data-tab") === hash;
      });
      if (exists) activateTab(hash);
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Copy buttons: literal `data-copy`, or the <pre> inside the button's `.codewrap`.
    document.addEventListener("click", function (e) {
      var btn = e.target.closest && e.target.closest(".copy-btn");
      if (!btn) return;
      var text = btn.getAttribute("data-copy");
      if (text === null) {
        var wrap = btn.closest(".codewrap");
        var pre = wrap
          ? wrap.querySelector("pre")
          : document.querySelector(btn.getAttribute("data-copy-target") || "pre");
        text = pre ? pre.innerText : "";
      }
      var copiedLabel = window.getTranslation ? window.getTranslation('flash.copied') : "Copied!";
      var pressCtrlLabel = window.getTranslation ? window.getTranslation('flash.press_ctrl_c') : "Press Ctrl+C";
      writeClipboard(text).then(
        function () {
          flashButton(btn, copiedLabel);
        },
        function () {
          flashButton(btn, pressCtrlLabel);
        }
      );
    });

    // User menu dropdown
    var avatarBtn = document.querySelector(".user-avatar-btn");
    var userMenu = document.querySelector(".user-menu");
    if (avatarBtn && userMenu) {
      avatarBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        var isHidden = userMenu.hasAttribute("hidden");
        if (isHidden) {
          userMenu.removeAttribute("hidden");
          avatarBtn.setAttribute("aria-expanded", "true");
        } else {
          userMenu.setAttribute("hidden", "");
          avatarBtn.setAttribute("aria-expanded", "false");
        }
      });

      // Close menu on outside click
      document.addEventListener("click", function (e) {
        if (!userMenu.hasAttribute("hidden") && !userMenu.contains(e.target) && !avatarBtn.contains(e.target)) {
          userMenu.setAttribute("hidden", "");
          avatarBtn.setAttribute("aria-expanded", "false");
        }
      });

      // Close on Escape
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && !userMenu.hasAttribute("hidden")) {
          userMenu.setAttribute("hidden", "");
          avatarBtn.setAttribute("aria-expanded", "false");
          avatarBtn.focus();
        }
      });

      // Prevent clicks inside menu from closing it
      userMenu.addEventListener("click", function (e) {
        e.stopPropagation();
      });
    }

    // Theme toggle with smooth transition
    var themeBtn = document.getElementById("theme-toggle");
    if (themeBtn) {
      themeBtn.addEventListener("click", function () {
        var current = document.documentElement.getAttribute("data-theme") || "dark";
        var next = current === "dark" ? "light" : "dark";
        
        // Add transition class for smooth theme change
        document.documentElement.classList.add("theme-transition");
        
        document.documentElement.setAttribute("data-theme", next);
        localStorage.setItem("theme", next);
        
        // Update icon title
        var label = next === "dark" ? "暗色模式" : "Light mode";
        themeBtn.setAttribute("title", label);
        themeBtn.setAttribute("aria-label", label);
        
        // Remove transition class after animation completes
        setTimeout(function () {
          document.documentElement.classList.remove("theme-transition");
        }, 300);
      });
    }

    // Language toggle
    var langBtn = document.getElementById("lang-toggle");
    if (langBtn) {
      langBtn.addEventListener("click", function () {
        var current = localStorage.getItem("lang") || "en";
        var next = current === "en" ? "zh-CN" : "en";
        localStorage.setItem("lang", next);
        window.location.reload();
      });
    }

    // Confirm dialogs for destructive actions (data-confirm on the button or its form).
    document.addEventListener("submit", function (e) {
      var form = e.target;
      var trigger = e.submitter;
      var msg =
        (trigger && trigger.getAttribute("data-confirm")) || form.getAttribute("data-confirm");
      if (msg && !window.confirm(msg)) {
        e.preventDefault();
      }
    });

    // Async looking glass: swap the result in place instead of a full page reload.
    var lgForm = document.getElementById("lg-form");
    var lgResult = document.getElementById("lg-result");
    if (lgForm && lgResult) {
      lgForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var btn = lgForm.querySelector('button[type="submit"]');
        var prev = btn ? btn.textContent : "";
        var runningText = window.getTranslation ? window.getTranslation('flash.running') : "Running…";
        if (btn) {
          btn.disabled = true;
          btn.textContent = runningText;
        }
        fetch("/lg", {
          method: "POST",
          body: new FormData(lgForm),
          headers: { "X-Requested-With": "fetch", Accept: "application/json" },
        })
          .then(function (resp) {
            var unexpectedText = window.getTranslation ? window.getTranslation('flash.unexpected_response', {code: resp.status}) : "Unexpected response (HTTP " + resp.status + ")";
            return resp.json().catch(function () {
              return { ok: false, output: unexpectedText };
            });
          })
          .then(function (data) {
            renderLgResult(lgResult, data);
          })
          .catch(function (err) {
            var errorText = window.getTranslation ? window.getTranslation('flash.request_failed', {error: err}) : "Request failed: " + err;
            renderLgResult(lgResult, { ok: false, output: errorText });
          })
          .finally(function () {
            if (btn) {
              btn.disabled = false;
              btn.textContent = prev;
            }
          });
      });
    }

    setupAdminPeerForm();
    setupLgTargetPlaceholder();
    setupIntraLinks();
    setupTabs();

    // OSPF refresh button
    var ospfRefreshBtn = document.getElementById("ospf-refresh");
    if (ospfRefreshBtn) {
      ospfRefreshBtn.addEventListener("click", function () {
        tabDataLoaded.ospf = false;
        loadOspfTab();
      });
    }

    // Flash banners: close button always; auto-dismiss non-errors after a few seconds.
    document.addEventListener("click", function (e) {
      if (e.target.classList && e.target.classList.contains("flash-close")) {
        fadeRemove(e.target.closest(".flash"));
      }
    });
    document.querySelectorAll(".flash:not(.flash-error)").forEach(function (el) {
      setTimeout(function () {
        fadeRemove(el);
      }, 6000);
    });
  });
})();
