import re

html_path = 'storages/ui/index.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Expose window.gowaApi if not already exposed
if 'window.gowaApi=Y=' not in content:
    content = content.replace('Y=NE.create({timeout:45e3})', 'window.gowaApi=Y=NE.create({timeout:45e3})', 1)
    print("Exposed window.gowaApi")

# 2. Add Webhook Routes to sidebar EO if not already present
sidebar_target = "{to:`/misc`,label:`Channels & Calls`,icon:Vo},{to:`/settings`,label:`Settings`,icon:xo}"
sidebar_replacement = "{to:`/misc`,label:`Channels & Calls`,icon:Vo},{to:`/webhook-routes`,label:`Webhook Routes`,icon:Bo},{to:`/settings`,label:`Settings`,icon:xo}"
if sidebar_target in content:
    content = content.replace(sidebar_target, sidebar_replacement, 1)
    print("Added Webhook Routes to sidebar navigation array")
elif sidebar_replacement in content:
    print("Sidebar navigation already contains Webhook Routes")
else:
    print("WARNING: Sidebar target not found")

# 3. Add WebhookRoutesPage component definition
page_comp_def = "function WebhookRoutesPage(){let e=WO();(0,L.useEffect)(()=>{window.mountWebhookRoutesPage&&window.mountWebhookRoutesPage(e)},[e]);return(0,R.jsx)(`div`,{id:`webhook-routes-page-container`,className:`flex flex-col gap-4`})}"
if 'function WebhookRoutesPage()' not in content:
    content = content.replace('function YR(){', page_comp_def + 'function YR(){', 1)
    print("Added WebhookRoutesPage React component")
else:
    print("WebhookRoutesPage React component already present")

# 4. Add route to React Router
router_target = "(0,R.jsx)(jr,{path:`/misc`,element:(0,R.jsx)(YR,{})}),(0,R.jsx)(jr,{path:`/settings`,element:(0,R.jsx)(XR,{})})"
router_replacement = "(0,R.jsx)(jr,{path:`/misc`,element:(0,R.jsx)(YR,{})}),(0,R.jsx)(jr,{path:`/webhook-routes`,element:(0,R.jsx)(WebhookRoutesPage,{})}),(0,R.jsx)(jr,{path:`/settings`,element:(0,R.jsx)(XR,{})})"
if router_target in content:
    content = content.replace(router_target, router_replacement, 1)
    print("Added /webhook-routes path to React Router")
elif router_replacement in content:
    print("React Router already contains /webhook-routes")
else:
    print("WARNING: Router target not found")

# 5. Inject the client-side JavaScript logic before </body>
script_tag = """
<!-- CUSTOM WEBHOOK ROUTING EXTENSION -->
<script>
(function() {
  console.log('[GOWA] Initializing Custom Webhook Routes Native UI Extension...');

  // SVG Webhook Icon
  const webhookIconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block shrink-0"><path d="M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c0-2.21 1.79-4 4-4h.01"/><path d="M6 13V6a3 3 0 0 1 3-3c1.3 0 2.4.84 2.82 2"/><path d="M12 9.5a3.5 3.5 0 0 1 7 0c0 1.61-.94 3-2.34 3.32"/><circle cx="6" cy="17" r="1"/><circle cx="12" cy="6" r="1"/><circle cx="17" cy="12" r="1"/></svg>';

  let activeDevId = null;
  let cachedDevices = [];

  async function api(path, options = {}) {
    if (window.gowaApi) {
      try {
        const res = await window.gowaApi(path, options);
        return res.data ? (res.data.results !== undefined ? res.data.results : res.data) : res;
      } catch (err) {
        console.error('API Error:', err);
        throw (err.response && err.response.data && err.response.data.message) ? new Error(err.response.data.message) : err;
      }
    }
    const auth = localStorage.getItem('gowa-ui.connection.v1');
    let headers = {'Content-Type': 'application/json'};
    if (auth) {
      try {
        const parsed = JSON.parse(auth);
        if (parsed.state && parsed.state.username && parsed.state.password) {
          headers['Authorization'] = 'Basic ' + btoa(parsed.state.username + ':' + parsed.state.password);
        }
      } catch(e) {}
    }
    const res = await fetch(path, { ...options, headers: { ...headers, ...(options.headers || {}) } });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || 'Request failed');
    return data.results !== undefined ? data.results : data;
  }

  function showToast(msg, isError = false) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-5 right-5 z-[99999] px-4 py-3 rounded-lg shadow-xl text-sm font-medium transition-all duration-300 ' + 
      (isError ? 'bg-red-900 border border-red-700 text-red-100' : 'bg-slate-800 border border-emerald-600/50 text-emerald-200');
    toast.innerHTML = (isError ? '⚠️ ' : '✅ ') + msg;
    document.body.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 3500);
  }

  // Mount Webhook Routes Page inside the container
  window.mountWebhookRoutesPage = async function(deviceId) {
    const container = document.getElementById('webhook-routes-page-container');
    if (!container) return;

    try {
      cachedDevices = (await api('/devices')) || [];
    } catch(e) {
      cachedDevices = [];
    }

    if (!deviceId && cachedDevices.length > 0) {
      const savedDev = localStorage.getItem('gowa-ui.device.v1');
      if (savedDev) {
        try { activeDevId = JSON.parse(savedDev).state.selectedDeviceId; } catch(e){}
      }
      if (!activeDevId || !cachedDevices.some(d => d.id === activeDevId)) {
        activeDevId = cachedDevices[0].id;
      }
    } else if (deviceId) {
      activeDevId = deviceId;
    }

    if (!activeDevId && cachedDevices.length === 0) {
      container.innerHTML = `
        <div class="flex flex-col gap-4">
          <div class="flex flex-wrap items-end justify-between gap-3">
            <div class="flex flex-col gap-1">
              <h1 class="font-heading text-2xl font-semibold tracking-tight text-slate-100 flex items-center gap-2">
                Webhook Routes
              </h1>
              <p class="text-sm text-slate-400">Route incoming WhatsApp events per group or sender JID with custom parameters.</p>
            </div>
          </div>
          <div class="flex flex-col items-center justify-center rounded-lg border border-dashed border-slate-800 p-12 text-center bg-slate-900/30">
            <p class="text-sm text-slate-300 font-medium">No WhatsApp device found.</p>
            <p class="text-xs text-slate-500 mt-1">Please add or pair a device on the <a href="/" class="text-cyan-400 underline hover:text-cyan-300">Overview / Devices</a> page first.</p>
          </div>
        </div>
      `;
      return;
    }

    let routes = [];
    let loadErr = null;
    try {
      routes = (await api('/devices/' + activeDevId + '/webhook/routes')) || [];
    } catch(e) {
      loadErr = e.message;
    }

    window.currentDeviceRoutes = routes;

    const deviceSelectOptions = cachedDevices.map(d => 
      '<option value="' + d.id + '" ' + (d.id === activeDevId ? 'selected' : '') + '>' + 
      (d.display_name ? d.display_name + ' (' + d.id + ')' : d.id) + '</option>'
    ).join('');

    let tableRows = '';
    if (routes.length === 0) {
      tableRows = '<tr><td colspan="5" class="py-12 text-center text-slate-400 text-sm">No webhook routes configured for this device yet.<br><span class="text-xs text-slate-500 mt-1 inline-block">Click <b>"+ Add Webhook Route"</b> above to route messages from specific groups or contacts.</span></td></tr>';
    } else {
      tableRows = routes.map(r => {
        const isGroup = r.match_jid && (r.match_jid.endsWith('@g.us') || r.match_jid === '@g.us');
        const badgeColor = isGroup ? 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30' : (r.match_jid === '*' ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30' : 'bg-slate-700/60 text-slate-300 border-slate-600');
        const exclusiveBadge = r.exclusive ? '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30 ml-2" title="Exclusive: suppresses default device webhook">Exclusive</span>' : '';
        const enabledBadge = r.enabled ? '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Active</span>' : '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-500 border border-slate-700">Disabled</span>';

        let paramsCount = r.custom_params ? Object.keys(r.custom_params).length : 0;
        let headersCount = r.custom_headers ? Object.keys(r.custom_headers).length : 0;
        let metaTags = [];
        if (paramsCount > 0) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700" title="Custom Query Params">' + paramsCount + ' param(s)</span>');
        if (headersCount > 0) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700" title="Custom Headers">' + headersCount + ' header(s)</span>');
        if (r.webhook_events) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 border border-slate-700">' + r.webhook_events + '</span>');

        return '<tr class="border-b border-slate-800/80 hover:bg-slate-800/30 transition-colors text-xs text-slate-300">' +
          '<td class="py-3.5 px-4"><div class="font-medium text-slate-100 text-sm flex items-center">' + (r.name || 'Unnamed Route') + exclusiveBadge + '</div></td>' +
          '<td class="py-3.5 px-4"><span class="px-2.5 py-1 rounded font-mono text-xs border ' + badgeColor + '">' + (r.match_jid || '*') + '</span></td>' +
          '<td class="py-3.5 px-4"><div class="truncate max-w-[320px] font-mono text-slate-300" title="' + r.webhook_url + '">' + r.webhook_url + '</div><div class="flex gap-1.5 mt-1 flex-wrap">' + metaTags.join(' ') + '</div></td>' +
          '<td class="py-3.5 px-4">' + enabledBadge + '</td>' +
          '<td class="py-3.5 px-4 text-right space-x-1.5">' +
            '<button onclick="window.openEditRouteModal(\'' + r.id + '\')" class="px-3 py-1.5 text-xs rounded border border-slate-700 hover:bg-slate-800 text-slate-200 transition-colors">Edit</button>' +
            '<button onclick="window.deleteWebhookRoute(\'' + r.id + '\')" class="px-3 py-1.5 text-xs rounded bg-red-950/40 border border-red-800/50 hover:bg-red-900/60 text-red-300 transition-colors">Delete</button>' +
          '</td>' +
        '</tr>';
      }).join('');
    }

    container.innerHTML = `
      <div class="flex flex-col gap-5">
        <!-- Header -->
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div class="flex flex-col gap-1">
            <h1 class="font-heading text-2xl font-semibold tracking-tight text-slate-100 flex items-center gap-2">
              Webhook Routes
              <span class="text-[11px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-normal">Active</span>
            </h1>
            <p class="text-sm text-slate-400">Route incoming WhatsApp events per group or sender JID to specific webhooks with custom query parameters and HTTP headers.</p>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="window.openAddRouteModal()" class="inline-flex items-center justify-center rounded-md text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow h-9 px-4 transition-colors">
              <span class="mr-1.5 text-base leading-none">+</span> Add Webhook Route
            </button>
          </div>
        </div>

        <!-- Main Card -->
        <div class="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
          <div class="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
            <div>
              <h3 class="text-base font-semibold text-slate-100">Configured Rules</h3>
              <p class="text-xs text-slate-400">Rules are evaluated whenever a WhatsApp message or event is received.</p>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-xs text-slate-400 font-medium">Device:</span>
              <select class="h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500" onchange="window.mountWebhookRoutesPage(this.value)">
                ${deviceSelectOptions}
              </select>
            </div>
          </div>

          ${loadErr ? `<div class="p-3 my-3 rounded bg-red-950/50 border border-red-800 text-red-300 text-xs">${loadErr}</div>` : ''}

          <!-- Routes Table -->
          <div class="overflow-x-auto pt-2">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950/40">
                  <th class="py-3 px-4">Route Name</th>
                  <th class="py-3 px-4">Match Pattern (JID)</th>
                  <th class="py-3 px-4">Destination Webhook URL</th>
                  <th class="py-3 px-4">Status</th>
                  <th class="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${tableRows}
              </tbody>
            </table>
          </div>
        </div>

        <div class="rounded-lg border border-slate-800/80 bg-slate-950/30 p-4 text-xs text-slate-400 flex items-start gap-3">
          <div class="text-cyan-400 text-base mt-0.5">ℹ️</div>
          <div class="space-y-1">
            <p><strong class="text-slate-200">Matching Pattern Guide:</strong></p>
            <ul class="list-disc list-inside space-y-0.5 text-slate-400">
              <li><code class="text-cyan-400">120363429795720905@g.us</code> — Matches that specific group only.</li>
              <li><code class="text-cyan-400">@g.us</code> — Wildcard: matches all WhatsApp group messages.</li>
              <li><code class="text-cyan-400">628123456789@s.whatsapp.net</code> — Matches a specific individual contact.</li>
              <li><code class="text-cyan-400">@s.whatsapp.net</code> — Wildcard: matches all 1:1 direct chats.</li>
              <li><code class="text-cyan-400">*</code> — Matches all events.</li>
            </ul>
          </div>
        </div>
      </div>
    `;
  };

  // Add / Edit Route Form Modal
  window.openAddRouteModal = function() {
    renderRouteFormModal(null);
  };

  window.openEditRouteModal = function(routeId) {
    const route = (window.currentDeviceRoutes || []).find(r => r.id === routeId);
    if (route) renderRouteFormModal(route);
  };

  function renderRouteFormModal(existingRoute) {
    const isEdit = !!existingRoute;
    const initialParams = existingRoute && existingRoute.custom_params ? Object.entries(existingRoute.custom_params) : [['token', '']];
    const initialHeaders = existingRoute && existingRoute.custom_headers ? Object.entries(existingRoute.custom_headers) : [];

    const paramsHtml = initialParams.map(([k, v]) => `
      <div class="flex items-center gap-2 mb-2 param-row">
        <input type="text" placeholder="Param key (e.g. token)" value="${k}" class="param-key h-8 w-1/3 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
        <input type="text" placeholder="Value" value="${v}" class="param-val h-8 flex-1 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
        <button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm font-bold">&times;</button>
      </div>
    `).join('');

    const headersHtml = initialHeaders.map(([k, v]) => `
      <div class="flex items-center gap-2 mb-2 header-row">
        <input type="text" placeholder="Header name (e.g. Authorization)" value="${k}" class="header-key h-8 w-1/3 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
        <input type="text" placeholder="Value (e.g. Bearer xyz)" value="${v}" class="header-val h-8 flex-1 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
        <button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm font-bold">&times;</button>
      </div>
    `).join('');

    const modalContent = `
      <div class="fixed inset-0 z-[10000] flex items-center justify-center bg-black/85 backdrop-blur-sm p-4 overflow-y-auto">
        <div class="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 shadow-2xl relative max-h-[95vh] flex flex-col text-slate-200">
          <!-- Header -->
          <div class="flex items-start justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 class="text-base font-semibold text-slate-100">${isEdit ? 'Edit Webhook Route' : 'Add Webhook Route'}</h3>
              <p class="text-xs text-slate-400">Device: <code class="text-cyan-400">${activeDevId}</code></p>
            </div>
            <button onclick="document.getElementById('route-form-modal-wrap').remove()" class="text-slate-400 hover:text-slate-100 p-1 text-xl">&times;</button>
          </div>

          <!-- Form Body -->
          <form id="route-form" class="flex-1 overflow-y-auto py-4 space-y-4 text-xs" onsubmit="window.handleSaveRoute(event, '${existingRoute ? existingRoute.id : ''}')">
            <!-- Route Name -->
            <div>
              <label class="block font-medium text-slate-300 mb-1">Route Name / Description</label>
              <input type="text" id="rf-name" value="${existingRoute ? (existingRoute.name || '') : ''}" placeholder="e.g. Windmill AI Agent Group" class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-cyan-500" required>
            </div>

            <!-- Match Pattern (JID) -->
            <div>
              <div class="flex justify-between items-center mb-1">
                <label class="font-medium text-slate-300">Match JID / Pattern</label>
                <div class="space-x-1">
                  <button type="button" onclick="document.getElementById('rf-jid').value='@g.us'" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">All Groups (@g.us)</button>
                  <button type="button" onclick="document.getElementById('rf-jid').value='@s.whatsapp.net'" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">All 1:1 Chats</button>
                  <button type="button" onclick="document.getElementById('rf-jid').value='*'" class="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">All (*)</button>
                </div>
              </div>
              <input type="text" id="rf-jid" value="${existingRoute ? (existingRoute.match_jid || '') : ''}" placeholder="e.g. 120363429795720905@g.us or @g.us" class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500" required>
              <p class="text-[11px] text-slate-500 mt-1">Enter exact group JID, contact number (e.g. 628123...), or wildcard (@g.us, @s.whatsapp.net, *).</p>
            </div>

            <!-- Target Webhook URL -->
            <div>
              <label class="block font-medium text-slate-300 mb-1">Destination Webhook URL</label>
              <input type="url" id="rf-url" value="${existingRoute ? (existingRoute.webhook_url || '') : ''}" placeholder="https://windmill.supardi.net/api/w/admins/jobs/run/..." class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500" required>
            </div>

            <!-- Custom Query Params -->
            <div class="border border-slate-800/80 rounded-lg p-3 bg-slate-950/30">
              <div class="flex justify-between items-center mb-2">
                <label class="font-medium text-slate-300">Custom URL Query Parameters (Optional)</label>
                <button type="button" onclick="window.addParamRow()" class="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium">+ Add Param</button>
              </div>
              <div id="params-container">${paramsHtml}</div>
              <p class="text-[10px] text-slate-500">Appended automatically to the webhook URL as ?key=value (e.g. token=xxx).</p>
            </div>

            <!-- Custom Headers -->
            <div class="border border-slate-800/80 rounded-lg p-3 bg-slate-950/30">
              <div class="flex justify-between items-center mb-2">
                <label class="font-medium text-slate-300">Custom HTTP Headers (Optional)</label>
                <button type="button" onclick="window.addHeaderRow()" class="text-[11px] text-cyan-400 hover:text-cyan-300 font-medium">+ Add Header</button>
              </div>
              <div id="headers-container">${headersHtml}</div>
              <p class="text-[10px] text-slate-500">Injected into the outgoing HTTP POST request (e.g. Authorization: Bearer ...).</p>
            </div>

            <!-- Event Whitelist & Options -->
            <div class="grid grid-cols-2 gap-3">
              <div>
                <label class="block font-medium text-slate-300 mb-1">Event Whitelist</label>
                <input type="text" id="rf-events" value="${existingRoute ? (existingRoute.webhook_events || '') : 'message'}" placeholder="message,message.ack" class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-cyan-500">
                <p class="text-[10px] text-slate-500 mt-0.5">Leave empty for all events.</p>
              </div>
              <div>
                <label class="block font-medium text-slate-300 mb-1">Custom Secret (Optional)</label>
                <input type="text" id="rf-secret" value="${existingRoute ? (existingRoute.webhook_secret || '') : ''}" placeholder="HMAC secret override" class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-cyan-500">
              </div>
            </div>

            <!-- Checkboxes -->
            <div class="pt-2 space-y-2">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" id="rf-exclusive" ${existingRoute && existingRoute.exclusive ? 'checked' : ''} class="rounded bg-slate-950 border-slate-700 text-cyan-600 focus:ring-0">
                <span class="text-slate-300 font-medium">Exclusive Routing</span>
                <span class="text-[11px] text-slate-500">(Do NOT send this event to default device webhook)</span>
              </label>

              <label class="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" id="rf-enabled" ${existingRoute ? (existingRoute.enabled ? 'checked' : '') : 'checked'} class="rounded bg-slate-950 border-slate-700 text-cyan-600 focus:ring-0">
                <span class="text-slate-300 font-medium">Route Enabled</span>
              </label>
            </div>

            <!-- Buttons -->
            <div class="pt-4 border-t border-slate-800 flex justify-end gap-2">
              <button type="button" onclick="document.getElementById('route-form-modal-wrap').remove()" class="px-4 py-1.5 rounded border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors">Cancel</button>
              <button type="submit" class="px-5 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium shadow transition-colors">Save Route</button>
            </div>
          </form>
        </div>
      </div>
    `;

    let wrap = document.getElementById('route-form-modal-wrap');
    if (!wrap) {
      wrap = document.createElement('div');
      wrap.id = 'route-form-modal-wrap';
      document.body.appendChild(wrap);
    }
    wrap.innerHTML = modalContent;
  }

  window.addParamRow = function() {
    const div = document.createElement('div');
    div.className = 'flex items-center gap-2 mb-2 param-row';
    div.innerHTML = `
      <input type="text" placeholder="Param key (e.g. token)" class="param-key h-8 w-1/3 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
      <input type="text" placeholder="Value" class="param-val h-8 flex-1 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
      <button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm font-bold">&times;</button>
    `;
    document.getElementById('params-container').appendChild(div);
  };

  window.addHeaderRow = function() {
    const div = document.createElement('div');
    div.className = 'flex items-center gap-2 mb-2 header-row';
    div.innerHTML = `
      <input type="text" placeholder="Header name (e.g. Authorization)" class="header-key h-8 w-1/3 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
      <input type="text" placeholder="Value (e.g. Bearer xyz)" class="header-val h-8 flex-1 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
      <button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm font-bold">&times;</button>
    `;
    document.getElementById('headers-container').appendChild(div);
  };

  window.handleSaveRoute = async function(evt, existingRouteId) {
    evt.preventDefault();
    const name = document.getElementById('rf-name').value.trim();
    const match_jid = document.getElementById('rf-jid').value.trim();
    const webhook_url = document.getElementById('rf-url').value.trim();
    const webhook_events = document.getElementById('rf-events').value.trim();
    const webhook_secret = document.getElementById('rf-secret').value.trim();
    const exclusive = document.getElementById('rf-exclusive').checked;
    const enabled = document.getElementById('rf-enabled').checked;

    const custom_params = {};
    document.querySelectorAll('.param-row').forEach(row => {
      const k = row.querySelector('.param-key').value.trim();
      const v = row.querySelector('.param-val').value.trim();
      if (k) custom_params[k] = v;
    });

    const custom_headers = {};
    document.querySelectorAll('.header-row').forEach(row => {
      const k = row.querySelector('.header-key').value.trim();
      const v = row.querySelector('.header-val').value.trim();
      if (k) custom_headers[k] = v;
    });

    const payload = {
      name,
      match_jid,
      webhook_url,
      webhook_events,
      webhook_secret,
      exclusive,
      enabled,
      custom_params,
      custom_headers
    };

    try {
      if (existingRouteId) {
        await api('/devices/' + activeDevId + '/webhook/routes/' + existingRouteId, {
          method: 'PUT',
          data: payload,
          body: JSON.stringify(payload)
        });
        showToast('Route updated successfully');
      } else {
        await api('/devices/' + activeDevId + '/webhook/routes', {
          method: 'POST',
          data: payload,
          body: JSON.stringify(payload)
        });
        showToast('New route added successfully');
      }
      document.getElementById('route-form-modal-wrap').remove();
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

  // Inject into Device 3-dots Menu
  function injectDeviceMenu() {
    const menus = document.querySelectorAll('[role="menu"]');
    for (const menu of menus) {
      if (menu.querySelector('#menu-webhook-routes')) continue;
      const items = Array.from(menu.querySelectorAll('[role="menuitem"], button'));
      const webhookItem = items.find(it => it.textContent.includes('Webhook'));
      if (webhookItem) {
        const newItem = document.createElement('button');
        newItem.id = 'menu-webhook-routes';
        newItem.setAttribute('role', 'menuitem');
        newItem.className = webhookItem.className;
        newItem.innerHTML = webhookIconSvg + '<span class="ml-2">Webhook Routes</span>';
        newItem.onclick = function(e) {
          e.preventDefault();
          window.location.hash = '';
          window.location.pathname = '/webhook-routes';
        };
        webhookItem.parentElement.insertBefore(newItem, webhookItem.nextSibling);
      }
    }
  }

  setInterval(injectDeviceMenu, 1000);
  const observer = new MutationObserver(injectDeviceMenu);
  observer.observe(document.body, { childList: true, subtree: true });

})();
</script>
"""

# Remove old injected script if any
if '<!-- CUSTOM WEBHOOK ROUTING EXTENSION -->' in content:
    content = content.split('<!-- CUSTOM WEBHOOK ROUTING EXTENSION -->')[0] + '</body>\n</html>'

content = content.replace('</body>', script_tag + '\n</body>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("SUCCESS: index.html fully updated with native Webhook Routes sidebar item, router path, and page component!")
