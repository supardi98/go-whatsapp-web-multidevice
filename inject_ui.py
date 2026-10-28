import re
import os

html_path = 'storages/ui/index.html'

# Always restore clean from src/storages/ui/index.html first
with open('src/storages/ui/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Webhook Routes to Sidebar Navigation in compiled React bundle
sidebar_target = '{to:`/misc`,label:`Channels & Calls`,icon:Vo},{to:`/settings`,label:`Settings`,icon:xo}'
sidebar_replacement = '{to:`/misc`,label:`Channels & Calls`,icon:Vo},{to:`/webhook-routes`,label:`Webhook Routes`,icon:Bo},{to:`/settings`,label:`Settings`,icon:xo}'
assert sidebar_target in content, "sidebar_target not found in index.html"
content = content.replace(sidebar_target, sidebar_replacement, 1)
print("1. Added Webhook Routes to sidebar navigation array")

# 2. Add WebhookRoutesPage React Component
# Uses React hook L.useEffect and WO() (active device ID hook)
page_comp_def = 'function WebhookRoutesPage(){let e=WO();(0,L.useEffect)(()=>{window.mountWebhookRoutesPage&&window.mountWebhookRoutesPage(e)},[e]);return(0,R.jsx)(`div`,{id:`webhook-routes-page-root`,className:`flex flex-col gap-4`})}'
target_fn = 'function YR(){'
assert target_fn in content, "target_fn not found in index.html"
content = content.replace(target_fn, page_comp_def + target_fn, 1)
print("2. Added WebhookRoutesPage React component")

# 3. Add /webhook-routes Path to React Router
router_target = '(0,R.jsx)(jr,{path:`/misc`,element:(0,R.jsx)(YR,{})}),(0,R.jsx)(jr,{path:`/settings`,element:(0,R.jsx)(XR,{})})'
router_replacement = '(0,R.jsx)(jr,{path:`/misc`,element:(0,R.jsx)(YR,{})}),(0,R.jsx)(jr,{path:`/webhook-routes`,element:(0,R.jsx)(WebhookRoutesPage,{})}),(0,R.jsx)(jr,{path:`/settings`,element:(0,R.jsx)(XR,{})})'
assert router_target in content, "router_target not found in index.html"
content = content.replace(router_target, router_replacement, 1)
print("3. Added /webhook-routes route to React Router")

# 4. Script Tag that mounts the full page into #webhook-routes-page-root and provides Add/Edit modal
script_tag = """
<!-- CUSTOM WEBHOOK ROUTING NATIVE PAGE EXTENSION -->
<style id="custom-webhook-routes-styles">
  .gowa-card {
    border: 1px solid hsl(var(--border, 217 33% 18%));
    border-radius: 0.75rem;
    background-color: hsl(var(--card, 222 47% 11%));
    color: hsl(var(--card-foreground, 210 40% 98%));
    overflow: hidden;
  }
  .gowa-card-header {
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid hsl(var(--border, 217 33% 18%));
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    background-color: hsl(var(--muted, 217 33% 14%) / 0.2);
  }
  .gowa-card-body {
    padding: 1.25rem 1.5rem;
  }
  .gowa-table-wrap {
    border: 1px solid hsl(var(--border, 217 33% 18%));
    border-radius: 0.5rem;
    overflow: hidden;
    background-color: hsl(var(--background, 222 47% 7%));
  }
  .gowa-table {
    width: 100%;
    border-collapse: collapse;
    text-align: left;
    font-size: 0.8125rem;
  }
  .gowa-table th {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid hsl(var(--border, 217 33% 18%));
    background-color: hsl(var(--muted, 217 33% 14%) / 0.5);
    color: hsl(var(--muted-foreground, 215 20% 65%));
    font-size: 0.6875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .gowa-table td {
    padding: 0.875rem 1rem;
    border-bottom: 1px solid hsl(var(--border, 217 33% 18%) / 0.6);
    color: hsl(var(--card-foreground, 210 40% 98%));
    vertical-align: middle;
  }
  .gowa-table tr:last-child td {
    border-bottom: none;
  }
  .gowa-table tr:hover td {
    background-color: hsl(var(--muted, 217 33% 14%) / 0.3);
  }
  .gowa-input {
    width: 100%;
    height: 2.125rem;
    padding: 0 0.625rem;
    border-radius: 0.375rem;
    border: 1px solid hsl(var(--input, 217 33% 20%));
    background-color: hsl(var(--background, 222 47% 7%));
    color: hsl(var(--foreground, 210 40% 98%));
    font-size: 0.75rem;
    outline: none;
    box-sizing: border-box;
    transition: border-color 0.15s ease;
  }
  .gowa-input:focus {
    border-color: hsl(var(--primary, 210 40% 98%));
  }
  .gowa-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    font-weight: 500;
    height: 2.125rem;
    padding: 0 0.875rem;
    cursor: pointer;
    transition: all 0.15s ease;
    border: none;
    box-sizing: border-box;
  }
  .gowa-btn-primary {
    background-color: hsl(var(--primary, 210 40% 98%));
    color: hsl(var(--primary-foreground, 222 47% 11%));
  }
  .gowa-btn-primary:hover {
    opacity: 0.9;
  }
  .gowa-btn-outline {
    background-color: transparent;
    border: 1px solid hsl(var(--border, 217 33% 22%));
    color: hsl(var(--foreground, 210 40% 98%));
  }
  .gowa-btn-outline:hover {
    background-color: hsl(var(--muted, 217 33% 15%));
  }
  .gowa-btn-danger {
    background-color: rgba(153, 27, 27, 0.4);
    border: 1px solid rgba(220, 38, 38, 0.4);
    color: #fca5a5;
  }
  .gowa-btn-danger:hover {
    background-color: rgba(185, 28, 28, 0.6);
  }
  .gowa-btn-sm {
    height: 1.625rem;
    padding: 0 0.5rem;
    font-size: 0.6875rem;
  }
  .gowa-badge {
    display: inline-flex;
    align-items: center;
    border-radius: 0.25rem;
    padding: 0.125rem 0.375rem;
    font-size: 0.6875rem;
    font-weight: 500;
    line-height: 1;
    border: 1px solid transparent;
  }
  .gowa-badge-active {
    background-color: rgba(16, 185, 129, 0.15);
    border-color: rgba(16, 185, 129, 0.3);
    color: #34d399;
  }
  .gowa-badge-disabled {
    background-color: rgba(71, 85, 105, 0.3);
    border-color: rgba(71, 85, 105, 0.4);
    color: #94a3b8;
  }
  .gowa-badge-group {
    background-color: rgba(99, 102, 241, 0.15);
    border-color: rgba(99, 102, 241, 0.3);
    color: #818cf8;
    font-family: monospace;
  }
  .gowa-badge-exclusive {
    background-color: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.3);
    color: #fbbf24;
  }
  .gowa-badge-meta {
    background-color: rgba(51, 65, 85, 0.4);
    border-color: rgba(71, 85, 105, 0.3);
    color: #cbd5e1;
    font-size: 0.6875rem;
  }

  /* Form Modal */
  .gowa-modal-backdrop {
    position: fixed;
    inset: 0;
    z-index: 99999;
    background-color: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1.25rem;
    box-sizing: border-box;
  }
  .gowa-modal-panel {
    background-color: hsl(var(--card, 222 47% 11%));
    color: hsl(var(--card-foreground, 210 40% 98%));
    border: 1px solid hsl(var(--border, 217 33% 18%));
    border-radius: 0.75rem;
    width: 100%;
    max-width: 32rem;
    max-height: 92vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
    overflow: hidden;
    box-sizing: border-box;
  }
</style>

<div id="webhook-routes-modal-root"></div>

<script>
(function() {
  console.log('[GOWA] Initializing Custom Webhook Routes Native Page Extension...');

  var activeDevId = null;
  var allDevices = [];
  window.currentDeviceRoutes = [];

  function getAuthHeader() {
    try {
      var auth = localStorage.getItem('gowa-ui.auth.v1');
      if (auth) {
        var parsed = JSON.parse(auth);
        var u = parsed.state && parsed.state.username;
        var p = parsed.state && parsed.state.password;
        if (u && p) return 'Basic ' + btoa(u + ':' + p);
      }
    } catch(e) {}
    return 'Basic ' + btoa('admin:admin');
  }

  async function api(path, options) {
    options = options || {};
    var headers = options.headers || {};
    headers['Authorization'] = getAuthHeader();
    if (options.body && typeof options.body === 'object') {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }
    options.headers = headers;
    var res = await fetch(path, options);
    if (!res.ok) {
      var errText = await res.text();
      throw new Error(errText || ('HTTP ' + res.status));
    }
    return res.json();
  }

  function showToast(msg, isError) {
    var toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;bottom:20px;right:20px;z-index:999999;padding:10px 16px;border-radius:8px;font-size:12px;font-weight:500;box-shadow:0 10px 25px rgba(0,0,0,0.5);transition:opacity 0.3s ease;' +
      (isError ? 'background:#450a0a;border:1px solid #991b1b;color:#fecaca;' : 'background:#0f172a;border:1px solid #334155;color:#f8fafc;');
    toast.innerHTML = (isError ? '⚠️ ' : '✅ ') + msg;
    document.body.appendChild(toast);
    setTimeout(function() {
      toast.style.opacity = '0';
      setTimeout(function() { toast.remove(); }, 300);
    }, 3500);
  }

  function getActiveDeviceId() {
    try {
      var saved = localStorage.getItem('gowa-ui.device.v1');
      if (saved) {
        var parsed = JSON.parse(saved);
        if (parsed.state && parsed.state.selectedDeviceId) return parsed.state.selectedDeviceId;
      }
    } catch(e) {}
    if (allDevices.length > 0) return allDevices[0].id;
    return null;
  }

  // Mount page handler called by React WebhookRoutesPage component
  window.mountWebhookRoutesPage = async function(deviceId) {
    var container = document.getElementById('webhook-routes-page-root');
    if (!container) return;

    activeDevId = deviceId || getActiveDeviceId();

    container.innerHTML = '<div style="padding:4rem 1rem;text-align:center;color:hsl(var(--muted-foreground));">' +
      '<div style="font-size:2rem;margin-bottom:0.75rem;">🌀</div>' +
      '<div style="font-size:0.875rem;">Loading webhook routes...</div>' +
      '</div>';

    try {
      var devResp = await api('/devices');
      allDevices = (devResp && devResp.results) ? devResp.results : [];
    } catch(e) {
      console.warn('Could not list devices:', e);
    }

    if (!activeDevId) {
      activeDevId = getActiveDeviceId();
    }

    var routes = [];
    var loadErr = null;
    if (activeDevId) {
      try {
        var res = await api('/devices/' + activeDevId + '/webhook/routes');
        routes = (res && res.results) ? res.results : [];
      } catch(e) {
        loadErr = e.message;
      }
    }
    window.currentDeviceRoutes = routes;

    var devOptions = allDevices.map(function(d) {
      return '<option value="' + d.id + '" ' + (d.id === activeDevId ? 'selected' : '') + '>' +
        (d.name || d.device || d.id) + ' (' + (d.phone_number || d.id) + ')' +
      '</option>';
    }).join('');

    var tableRows = '';
    if (!activeDevId) {
      tableRows = '<tr><td colspan="5" style="text-align:center;padding:3rem 1rem;color:hsl(var(--muted-foreground));font-size:0.8125rem;">' +
        'No WhatsApp device selected or paired. Please select or add a device in <a href="/settings" style="color:#22d3ee;text-decoration:underline;">Settings</a>.' +
      '</td></tr>';
    } else if (routes.length === 0) {
      tableRows = '<tr><td colspan="5" style="text-align:center;padding:3rem 1rem;color:hsl(var(--muted-foreground));font-size:0.8125rem;">' +
        (loadErr ? '<div style="color:#f87171;margin-bottom:0.375rem;">Error: ' + loadErr + '</div>' : 'No custom webhook routes configured for this device yet.<br><span style="opacity:0.7;">Events fall back to default device webhook.</span>') +
      '</td></tr>';
    } else {
      tableRows = routes.map(function(r) {
        var isGroup = r.match_jid && (r.match_jid.includes('@g.us') || r.match_jid === '@g.us');
        var badgeClass = isGroup ? 'gowa-badge gowa-badge-group' : 'gowa-badge gowa-badge-active';
        var exclusiveBadge = r.exclusive ? '<span class="gowa-badge gowa-badge-exclusive" style="margin-left:0.5rem;" title="Exclusive: suppresses default webhook">Exclusive</span>' : '';
        var enabledBadge = r.enabled ? '<span class="gowa-badge gowa-badge-active">Active</span>' : '<span class="gowa-badge gowa-badge-disabled">Disabled</span>';

        var paramsCount = r.custom_params ? Object.keys(r.custom_params).length : 0;
        var headersCount = r.custom_headers ? Object.keys(r.custom_headers).length : 0;
        var metaTags = [];
        if (paramsCount > 0) metaTags.push('<span class="gowa-badge gowa-badge-meta">' + paramsCount + ' param(s)</span>');
        if (headersCount > 0) metaTags.push('<span class="gowa-badge gowa-badge-meta">' + headersCount + ' header(s)</span>');
        if (r.webhook_events) metaTags.push('<span class="gowa-badge gowa-badge-meta">' + r.webhook_events + '</span>');

        return '<tr>' +
          '<td><div style="font-weight:600;display:flex;align-items:center;">' + (r.name || 'Unnamed Route') + exclusiveBadge + '</div></td>' +
          '<td><span class="' + badgeClass + '">' + (r.match_jid || '*') + '</span></td>' +
          '<td><div style="max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:monospace;" title="' + r.webhook_url + '">' + r.webhook_url + '</div><div style="display:flex;gap:0.375rem;margin-top:0.375rem;flex-wrap:wrap;">' + metaTags.join(' ') + '</div></td>' +
          '<td>' + enabledBadge + '</td>' +
          '<td style="text-align:right;">' +
            '<div style="display:inline-flex;gap:0.375rem;">' +
              '<button data-route-id="' + r.id + '" onclick="window.openEditRouteModal(this.dataset.routeId)" class="gowa-btn gowa-btn-outline gowa-btn-sm">Edit</button>' +
              '<button data-route-id="' + r.id + '" onclick="window.deleteWebhookRoute(this.dataset.routeId)" class="gowa-btn gowa-btn-danger gowa-btn-sm">Delete</button>' +
            '</div>' +
          '</td>' +
        '</tr>';
      }).join('');
    }

    container.innerHTML = '<div style="display:flex;flex-direction:column;gap:1.25rem;">' +
      '<!-- Page Header -->' +
      '<div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem;">' +
        '<div>' +
          '<h1 style="font-size:1.5rem;font-weight:700;display:flex;align-items:center;gap:0.625rem;color:hsl(var(--foreground));margin:0;">' +
            'Webhook Routes' +
            '<span class="gowa-badge" style="background:rgba(6,182,212,0.15);color:#22d3ee;border:1px solid rgba(6,182,212,0.3);">Multi-Destination</span>' +
          '</h1>' +
          '<p style="font-size:0.875rem;color:hsl(var(--muted-foreground));margin:0.25rem 0 0 0;">Route incoming WhatsApp events per sender JID or group to specific external webhooks with custom parameters & headers.</p>' +
        '</div>' +
        '<div style="display:flex;align-items:center;gap:0.75rem;">' +
          '<div style="display:flex;align-items:center;gap:0.5rem;font-size:0.75rem;color:hsl(var(--muted-foreground));">' +
            '<span>Device:</span>' +
            '<select onchange="window.mountWebhookRoutesPage(this.value)" class="gowa-input" style="width:auto;height:2.25rem;padding-right:1.5rem;">' +
              devOptions +
            '</select>' +
          '</div>' +
          '<button onclick="window.openAddRouteModal()" class="gowa-btn gowa-btn-primary" style="height:2.25rem;gap:0.375rem;">' +
            '<span style="font-weight:700;font-size:0.875rem;">+</span> Add Route' +
          '</button>' +
        '</div>' +
      '</div>' +

      '<!-- Table Card -->' +
      '<div class="gowa-card">' +
        '<div class="gowa-table-wrap" style="border:none;border-radius:0;">' +
          '<table class="gowa-table">' +
            '<thead>' +
              '<tr>' +
                '<th>Route Name</th>' +
                '<th>Match Pattern (JID)</th>' +
                '<th>Destination Webhook URL</th>' +
                '<th>Status</th>' +
                '<th style="text-align:right;">Actions</th>' +
              '</tr>' +
            '</thead>' +
            '<tbody>' + tableRows + '</tbody>' +
          '</table>' +
        '</div>' +
      '</div>' +

      '<!-- Pattern Guide Card -->' +
      '<div class="gowa-card" style="padding:1rem 1.25rem;font-size:0.75rem;color:hsl(var(--muted-foreground));display:flex;align-items:flex-start;gap:0.75rem;">' +
        '<div style="color:#22d3ee;font-size:1.125rem;line-height:1;margin-top:0.125rem;">ℹ️</div>' +
        '<div style="line-height:1.5;">' +
          '<div style="font-weight:600;color:hsl(var(--foreground));margin-bottom:0.25rem;">Matching Pattern Guide:</div>' +
          '<ul style="margin:0;padding-left:1.25rem;list-style-type:disc;">' +
            '<li><code style="color:#22d3ee;background:rgba(6,182,212,0.1);padding:0.125rem 0.25rem;border-radius:0.25rem;">120363429795720905@g.us</code> — Matches that specific group only.</li>' +
            '<li><code style="color:#22d3ee;background:rgba(6,182,212,0.1);padding:0.125rem 0.25rem;border-radius:0.25rem;">@g.us</code> — Wildcard: matches all WhatsApp group messages.</li>' +
            '<li><code style="color:#22d3ee;background:rgba(6,182,212,0.1);padding:0.125rem 0.25rem;border-radius:0.25rem;">628123456789@s.whatsapp.net</code> — Matches a specific individual contact.</li>' +
            '<li><code style="color:#22d3ee;background:rgba(6,182,212,0.1);padding:0.125rem 0.25rem;border-radius:0.25rem;">@s.whatsapp.net</code> — Wildcard: matches all 1:1 direct chats.</li>' +
            '<li><code style="color:#22d3ee;background:rgba(6,182,212,0.1);padding:0.125rem 0.25rem;border-radius:0.25rem;">*</code> — Matches all events.</li>' +
          '</ul>' +
        '</div>' +
      '</div>' +
    '</div>';
  };

  window.openEditRouteModal = function(routeId) {
    var route = window.currentDeviceRoutes.find(function(r) { return r.id === routeId; });
    window.renderRouteFormModal(route);
  };

  window.openAddRouteModal = function() {
    window.renderRouteFormModal(null);
  };

  window.closeRouteFormModal = function() {
    var modal = document.getElementById('route-form-modal-wrap');
    if (modal) modal.remove();
  };

  window.renderRouteFormModal = function(existingRoute) {
    var isEdit = !!existingRoute;
    var initialParams = existingRoute && existingRoute.custom_params ? Object.entries(existingRoute.custom_params) : [['token', '']];
    var initialHeaders = existingRoute && existingRoute.custom_headers ? Object.entries(existingRoute.custom_headers) : [['Authorization', 'Bearer ']];

    var paramRows = initialParams.map(function(pair, i) {
      return '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem;" class="param-row">' +
        '<input type="text" placeholder="Key (e.g. token)" value="' + pair[0] + '" class="p-key gowa-input" style="flex:1;font-family:monospace;">' +
        '<input type="text" placeholder="Value" value="' + pair[1] + '" class="p-val gowa-input" style="flex:1;font-family:monospace;">' +
        '<button type="button" onclick="this.parentElement.remove()" style="background:none;border:none;color:hsl(var(--muted-foreground));cursor:pointer;font-size:1.125rem;padding:0 0.25rem;">&times;</button>' +
      '</div>';
    }).join('');

    var headerRows = initialHeaders.map(function(pair, i) {
      return '<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem;" class="header-row">' +
        '<input type="text" placeholder="Header Name" value="' + pair[0] + '" class="h-key gowa-input" style="flex:1;font-family:monospace;">' +
        '<input type="text" placeholder="Header Value" value="' + pair[1] + '" class="h-val gowa-input" style="flex:1;font-family:monospace;">' +
        '<button type="button" onclick="this.parentElement.remove()" style="background:none;border:none;color:hsl(var(--muted-foreground));cursor:pointer;font-size:1.125rem;padding:0 0.25rem;">&times;</button>' +
      '</div>';
    }).join('');

    var formModal = document.createElement('div');
    formModal.id = 'route-form-modal-wrap';
    formModal.className = 'gowa-modal-backdrop';
    formModal.innerHTML = '<div class="gowa-modal-panel">' +
      '<div class="gowa-card-header">' +
        '<div>' +
          '<div style="font-size:0.9375rem;font-weight:600;">' + (isEdit ? 'Edit Webhook Route' : 'Add Webhook Route') + '</div>' +
          '<div style="font-size:0.6875rem;color:hsl(var(--muted-foreground));margin-top:0.125rem;">Device: <code style="color:#22d3ee;">' + activeDevId + '</code></div>' +
        '</div>' +
        '<button onclick="window.closeRouteFormModal()" class="gowa-btn gowa-btn-outline gowa-btn-sm" style="font-size:1.125rem;line-height:1;width:1.75rem;height:1.75rem;padding:0;">&times;</button>' +
      '</div>' +

      '<form id="route-form" style="padding:1.25rem;overflow-y:auto;display:flex;flex-direction:column;gap:0.875rem;font-size:0.75rem;" data-route-id="' + (existingRoute ? existingRoute.id : '') + '" onsubmit="window.handleSaveRoute(event, this.dataset.routeId)">' +
        '<div>' +
          '<label style="display:block;font-weight:600;margin-bottom:0.375rem;color:hsl(var(--foreground));">Route Name</label>' +
          '<input type="text" id="rf-name" value="' + (existingRoute ? (existingRoute.name || '') : '') + '" placeholder="e.g. Windmill Group Agent" class="gowa-input" required>' +
        '</div>' +

        '<div>' +
          '<div style="display:flex;justify-content:space-between;margin-bottom:0.375rem;">' +
            '<label style="font-weight:600;color:hsl(var(--foreground));">Match Pattern (JID / Group)</label>' +
            '<span style="font-size:0.6875rem;color:#22d3ee;">exact JID or @g.us</span>' +
          '</div>' +
          '<input type="text" id="rf-jid" value="' + (existingRoute ? (existingRoute.match_jid || '') : '') + '" placeholder="e.g. 120363429795720905@g.us" class="gowa-input" style="font-family:monospace;" required>' +
        '</div>' +

        '<div>' +
          '<label style="display:block;font-weight:600;margin-bottom:0.375rem;color:hsl(var(--foreground));">Destination Webhook URL</label>' +
          '<input type="url" id="rf-url" value="' + (existingRoute ? (existingRoute.webhook_url || '') : '') + '" placeholder="http://localhost:8000/api/w/admins/jobs/run/..." class="gowa-input" style="font-family:monospace;" required>' +
        '</div>' +

        '<!-- Custom Params -->' +
        '<div style="padding-top:0.625rem;border-top:1px solid hsl(var(--border, 217 33% 18%));">' +
          '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.375rem;">' +
            '<label style="font-weight:600;color:hsl(var(--foreground));">Custom Query Parameters (?key=value)</label>' +
            '<button type="button" onclick="window.addParamRow()" style="background:none;border:none;color:#22d3ee;cursor:pointer;font-size:0.6875rem;">+ Add Param</button>' +
          '</div>' +
          '<div id="param-rows-container">' + paramRows + '</div>' +
        '</div>' +

        '<!-- Custom Headers -->' +
        '<div style="padding-top:0.625rem;border-top:1px solid hsl(var(--border, 217 33% 18%));">' +
          '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.375rem;">' +
            '<label style="font-weight:600;color:hsl(var(--foreground));">Custom HTTP Headers (Authorization, etc.)</label>' +
            '<button type="button" onclick="window.addHeaderRow()" style="background:none;border:none;color:#22d3ee;cursor:pointer;font-size:0.6875rem;">+ Add Header</button>' +
          '</div>' +
          '<div id="header-rows-container">' + headerRows + '</div>' +
        '</div>' +

        '<!-- Options -->' +
        '<div style="padding-top:0.625rem;border-top:1px solid hsl(var(--border, 217 33% 18%));display:flex;flex-direction:column;gap:0.5rem;">' +
          '<label style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;">' +
            '<input type="checkbox" id="rf-exclusive" ' + (existingRoute && existingRoute.exclusive ? 'checked' : '') + ' style="accent-color:#06b6d4;">' +
            '<span style="font-weight:500;">Exclusive Route</span>' +
            '<span style="color:hsl(var(--muted-foreground));font-size:0.6875rem;">(Suppresses default webhook)</span>' +
          '</label>' +
          '<label style="display:flex;align-items:center;gap:0.5rem;cursor:pointer;">' +
            '<input type="checkbox" id="rf-enabled" ' + (existingRoute ? (existingRoute.enabled ? 'checked' : '') : 'checked') + ' style="accent-color:#06b6d4;">' +
            '<span style="font-weight:500;">Route Enabled</span>' +
          '</label>' +
        '</div>' +

        '<div style="padding-top:1rem;border-top:1px solid hsl(var(--border, 217 33% 18%));display:flex;justify-content:flex-end;gap:0.5rem;">' +
          '<button type="button" onclick="window.closeRouteFormModal()" class="gowa-btn gowa-btn-outline">Cancel</button>' +
          '<button type="submit" class="gowa-btn gowa-btn-primary">Save Route</button>' +
        '</div>' +
      '</form>' +
    '</div>';

    document.body.appendChild(formModal);
  };

  window.addParamRow = function() {
    var c = document.getElementById('param-rows-container');
    if (!c) return;
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem;';
    row.className = 'param-row';
    row.innerHTML = '<input type="text" placeholder="Key" class="p-key gowa-input" style="flex:1;font-family:monospace;">' +
      '<input type="text" placeholder="Value" class="p-val gowa-input" style="flex:1;font-family:monospace;">' +
      '<button type="button" onclick="this.parentElement.remove()" style="background:none;border:none;color:hsl(var(--muted-foreground));cursor:pointer;font-size:1.125rem;padding:0 0.25rem;">&times;</button>';
    c.appendChild(row);
  };

  window.addHeaderRow = function() {
    var c = document.getElementById('header-rows-container');
    if (!c) return;
    var row = document.createElement('div');
    row.style.cssText = 'display:flex;align-items:center;gap:0.5rem;margin-bottom:0.375rem;';
    row.className = 'header-row';
    row.innerHTML = '<input type="text" placeholder="Header Name" class="h-key gowa-input" style="flex:1;font-family:monospace;">' +
      '<input type="text" placeholder="Header Value" class="h-val gowa-input" style="flex:1;font-family:monospace;">' +
      '<button type="button" onclick="this.parentElement.remove()" style="background:none;border:none;color:hsl(var(--muted-foreground));cursor:pointer;font-size:1.125rem;padding:0 0.25rem;">&times;</button>';
    c.appendChild(row);
  };

  window.handleSaveRoute = async function(e, existingRouteId) {
    e.preventDefault();
    var name = document.getElementById('rf-name').value.trim();
    var matchJid = document.getElementById('rf-jid').value.trim();
    var url = document.getElementById('rf-url').value.trim();
    var exclusive = document.getElementById('rf-exclusive').checked;
    var enabled = document.getElementById('rf-enabled').checked;

    var customParams = {};
    document.querySelectorAll('.param-row').forEach(function(r) {
      var k = r.querySelector('.p-key').value.trim();
      var v = r.querySelector('.p-val').value.trim();
      if (k) customParams[k] = v;
    });

    var customHeaders = {};
    document.querySelectorAll('.header-row').forEach(function(r) {
      var k = r.querySelector('.h-key').value.trim();
      var v = r.querySelector('.h-val').value.trim();
      if (k) customHeaders[k] = v;
    });

    var payload = {
      name: name,
      match_jid: matchJid,
      webhook_url: url,
      webhook_events: 'message',
      custom_params: customParams,
      custom_headers: customHeaders,
      exclusive: exclusive,
      enabled: enabled
    };

    try {
      if (existingRouteId) {
        await api('/devices/' + activeDevId + '/webhook/routes/' + existingRouteId, {
          method: 'PUT',
          body: payload
        });
        showToast('Route updated successfully');
      } else {
        await api('/devices/' + activeDevId + '/webhook/routes', {
          method: 'POST',
          body: payload
        });
        showToast('New route added successfully');
      }
      var modalWrap = document.getElementById('route-form-modal-wrap');
      if (modalWrap) modalWrap.remove();
      window.mountWebhookRoutesPage(activeDevId);
    } catch(err) {
      showToast('Failed to save route: ' + err.message, true);
    }
  };

  window.deleteWebhookRoute = async function(routeId) {
    if (!confirm('Are you sure you want to delete this webhook route?')) return;
    try {
      await api('/devices/' + activeDevId + '/webhook/routes/' + routeId, {
        method: 'DELETE'
      });
      showToast('Route deleted');
      window.mountWebhookRoutesPage(activeDevId);
    } catch(err) {
      showToast('Failed to delete: ' + err.message, true);
    }
  };

  // Fallback: If user directly navigates to /webhook-routes, ensure page mounts
  function checkUrlAndMount() {
    if (window.location.pathname === '/webhook-routes' && document.getElementById('webhook-routes-page-root')) {
      if (!document.getElementById('webhook-routes-page-root').hasChildNodes()) {
        window.mountWebhookRoutesPage();
      }
    }
  }

  setInterval(checkUrlAndMount, 500);

})();
</script>
"""

# Inject before </body>
content = content.replace('</body>', script_tag + '\n</body>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: index.html fully configured with native React page at /webhook-routes!")
