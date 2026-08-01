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
        '<td colspan="6" class="empty-state" data-i18n="admin.no_intra_links">No internal links on this node yet.</td>';
      tbody.appendChild(tr);
      return;
    }
    links.forEach(function (l) {
      var tr = document.createElement("tr");
      var remote = esc(l.remote_name);
      if (l.remote_endpoint) remote += (remote ? "<br>" : "") + '<span class="faint">' + esc(l.remote_endpoint) + "</span>";
      tr.innerHTML =
        '<td class="mono nowrap">' + esc(l.protocol_name) + (l.label ? '<br><span class="faint">' + esc(l.label) + "</span>" : "") + "</td>" +
        '<td class="mono">' + remote + "</td>" +
        '<td class="mono nowrap">' + esc(l.listen_port) + "</td>" +
        '<td class="mono nowrap">' + esc(l.link_local_address) + "</td>" +
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

  // The links table sits under /admin/nodes/{node_id}/edit; we extract node_id from the table's
  // data-node-id attribute (set in the template) rather than parsing the URL.
  function nodeIdFromTable(tbody) {
    return tbody.getAttribute("data-node-id") || "";
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

  function setupIntraLinks() {
    var form = document.getElementById("intra-link-form");
    var tbody = document.getElementById("intra-links-tbody");
    if (!form || !tbody) return;
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
        })
        .catch(function () { /* network error — leave the existing table in place */ });
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
            // Reset only the manual fields; keep remote_node selection for convenience.
            form.querySelector('[name="remote_public_key"]').value = "";
            form.querySelector('[name="remote_endpoint"]').value = "";
            form.querySelector('[name="label"]').value = "";
            refresh();
          }
        })
        .catch(function (err) {
          showIntraFlash(flashBox, "Request failed: " + err, false);
        })
        .finally(function () {
          if (btn) { btn.disabled = false; btn.textContent = prev; }
        });
    });

    // Refresh once on load so the table reflects any out-of-band changes (e.g. reverse link created
    // on the remote that this page doesn't know about yet).
    refresh();

    // Event-delegated submit handler for the per-row redeploy / delete forms. The table body is
    // re-rendered by refresh() (innerHTML replaced), so we cannot attach listeners to the forms
    // directly — delegating on the stable <tbody> survives re-renders. Each form's native action=
    // POST is the no-JS fallback; with JS on we POST to the /api variant and refresh in place.
    // 逐行 redeploy / delete 表單的事件委派 submit 處理。表格 body 由 refresh() 重渲染(innerHTML
    // 替換),故無法直接在 form 上掛監聽器——委派到穩定的 <tbody> 才能在重渲染後存活。每個 form
    // 的原生 action= POST 是無 JS 回退;JS 啟用時改 POST 到 /api 變體並就地刷新。
    tbody.addEventListener("submit", function (e) {
      var f = e.target;
      if (!f || f.tagName !== "FORM") return;
      var action = f.getAttribute("action") || "";
      var isDeploy = /\/intra-links\/[^/]+\/deploy$/.test(action);
      var isDelete = /\/intra-links\/[^/]+\/delete$/.test(action);
      if (!isDeploy && !isDelete) return;

      // Stop propagation so the document-level confirm handler (which would re-prompt) does not
      // fire for a form we have taken over. We run our own confirm check below for delete.
      // 停止冒泡,讓 document 級的 confirm 處理器(會重複彈框)不對我們接管的 form 觸發。
      // delete 的 confirm 檢查在下方自行處理。
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
            // Deploy/delete failed — restore the button so the operator can retry without a reload.
            // 部署/刪除失敗——還原按鈕讓操作者無需重載即可重試。
            btn.disabled = false;
            btn.textContent = prev;
          }
        })
        .catch(function (err) {
          showIntraFlash(flashBox, "Request failed: " + err, false);
          if (btn) { btn.disabled = false; btn.textContent = prev; }
        });
        // No finally(): on success the button's row is replaced by refresh(), so restoring it
        // would clobber a row that no longer exists (e.g. after a successful delete). We restore
        // the button only on failure, handled in the then/catch branches above.
        // 不用 finally():成功時按鈕所在列已被 refresh() 替換,還原它會操作一個已不存在的列
        // (例如刪除成功後)。僅在失敗時還原按鈕,於上方 then/catch 分支處理。
    });
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
