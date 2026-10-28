import os

script_code = """
<!-- CUSTOM WEBHOOK ROUTING UI EXTENSION -->
<script>
(function() {
  console.log('[GOWA] Initializing Custom Webhook Routes UI Extension...');

  // SVG Webhook Icon
  const webhookIconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block shrink-0"><path d="M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c0-2.21 1.79-4 4-4h.01"/><path d="M6 13V6a3 3 0 0 1 3-3c1.3 0 2.4.84 2.82 2"/><path d="M12 9.5a3.5 3.5 0 0 1 7 0c0 1.61-.94 3-2.34 3.32"/><circle cx="6" cy="17" r="1"/><circle cx="12" cy="6" r="1"/><circle cx="17" cy="12" r="1"/></svg>';

  let currentDeviceId = null;
  let allDevices = [];

  // Helper to call GoWA API
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
    // Fallback direct fetch
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

  // Create Modal Container in DOM
  let modalRoot = document.getElementById('webhook-routes-modal-root');
  if (!modalRoot) {
    modalRoot = document.createElement('div');
    modalRoot.id = 'webhook-routes-modal-root';
    document.body.appendChild(modalRoot);
  }

  // Show Toast Message
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

  // Open Webhook Routes Manager
  window.openWebhookRoutesManager = async function(deviceId) {
    try {
      allDevices = (await api('/devices')) || [];
    } catch(e) {
      console.warn('Could not fetch devices:', e);
      allDevices = [];
    }

    if (!deviceId && allDevices.length > 0) {
      const savedDev = localStorage.getItem('gowa-ui.device.v1');
      if (savedDev) {
        try { currentDeviceId = JSON.parse(savedDev).state.selectedDeviceId; } catch(e){}
      }
      if (!currentDeviceId || !allDevices.some(d => d.id === currentDeviceId)) {
        currentDeviceId = allDevices[0].id;
      }
    } else if (deviceId) {
      currentDeviceId = deviceId;
    }

    renderRoutesListModal();
  };

  async function renderRoutesListModal() {
    let routes = [];
    let loadError = null;
    if (currentDeviceId) {
      try {
        routes = (await api('/devices/' + currentDeviceId + '/webhook/routes')) || [];
      } catch(e) {
        loadError = e.message;
      }
    }

    const deviceOptions = allDevices.map(d => 
      '<option value="' + d.id + '" ' + (d.id === currentDeviceId ? 'selected' : '') + '>' + 
      (d.display_name ? d.display_name + ' (' + d.id + ')' : d.id) + '</option>'
    ).join('');

    let routesRowsHtml = '';
    if (routes.length === 0) {
      routesRowsHtml = '<tr><td colspan="5" class="py-8 text-center text-slate-400 text-sm">No webhook routes configured for this device yet.<br><span class="text-xs text-slate-500">Click <b>"+ Add Route"</b> to create custom routing rules per JID or Group.</span></td></tr>';
    } else {
      routesRowsHtml = routes.map(r => {
        const isGroup = r.match_jid && (r.match_jid.endsWith('@g.us') || r.match_jid === '@g.us');
        const badgeColor = isGroup ? 'bg-indigo-500/15 text-indigo-400 border-indigo-500/30' : (r.match_jid === '*' ? 'bg-cyan-500/15 text-cyan-400 border-cyan-500/30' : 'bg-slate-700/60 text-slate-300 border-slate-600');
        const exclusiveBadge = r.exclusive ? '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30 ml-1.5" title="Exclusive: does not trigger default webhook">Exclusive</span>' : '';
        const enabledBadge = r.enabled ? '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Active</span>' : '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-500 border border-slate-700">Disabled</span>';

        let paramsCount = r.custom_params ? Object.keys(r.custom_params).length : 0;
        let headersCount = r.custom_headers ? Object.keys(r.custom_headers).length : 0;
        let metaTags = [];
        if (paramsCount > 0) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700" title="Custom Query Params">' + paramsCount + ' param(s)</span>');
        if (headersCount > 0) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700" title="Custom Headers">' + headersCount + ' header(s)</span>');
        if (r.webhook_events) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 border border-slate-700">' + r.webhook_events + '</span>');

        return '<tr class="border-b border-slate-800/80 hover:bg-slate-800/30 transition-colors text-xs font-normal text-slate-300">' +
          '<td class="py-3 px-3"><div class="font-medium text-slate-100 text-sm">' + (r.name || 'Unnamed Route') + '</div>' + (exclusiveBadge) + '</td>' +
          '<td class="py-3 px-3"><span class="px-2 py-1 rounded font-mono text-xs border ' + badgeColor + '">' + (r.match_jid || '*') + '</span></td>' +
          '<td class="py-3 px-3"><div class="truncate max-w-[280px] font-mono text-slate-300" title="' + r.webhook_url + '">' + r.webhook_url + '</div><div class="flex gap-1 mt-1 flex-wrap">' + metaTags.join(' ') + '</div></td>' +
          '<td class="py-3 px-3">' + enabledBadge + '</td>' +
          '<td class="py-3 px-3 text-right space-x-1">' +
            '<button onclick="window.openEditRouteModal(\'' + r.id + '\')" class="px-2.5 py-1 text-xs rounded border border-slate-700 hover:bg-slate-800 text-slate-200 transition-colors">Edit</button>' +
            '<button onclick="window.deleteWebhookRoute(\'' + r.id + '\')" class="px-2.5 py-1 text-xs rounded bg-red-950/40 border border-red-800/50 hover:bg-red-900/60 text-red-300 transition-colors">Delete</button>' +
          '</td>' +
        '</tr>';
      }).join('');
    }

    modalRoot.innerHTML = `
      <div class="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
        <div class="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full p-6 shadow-2xl relative max-h-[90vh] flex flex-col">
          <!-- Header -->
          <div class="flex items-start justify-between pb-4 border-b border-slate-800">
            <div class="flex items-center gap-3">
              <div class="p-2.5 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400">
                ${webhookIconSvg}
              </div>
              <div>
                <h2 class="text-lg font-semibold text-slate-100 flex items-center gap-2">
                  Multi-Webhook Routing Manager
                  <span class="text-[11px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-normal">Active</span>
                </h2>
                <p class="text-xs text-slate-400 mt-0.5">Route incoming WhatsApp events per group or sender JID to specific webhooks with custom parameters.</p>
              </div>
            </div>
            <button onclick="document.getElementById('webhook-routes-modal-root').innerHTML=''" class="text-slate-400 hover:text-slate-100 p-1 rounded-lg hover:bg-slate-800 text-xl font-semibold leading-none">&times;</button>
          </div>

          <!-- Device Selector & Actions -->
          <div class="flex flex-wrap items-center justify-between gap-3 py-4 border-b border-slate-800/60">
            <div class="flex items-center gap-2">
              <label class="text-xs font-medium text-slate-300 whitespace-nowrap">Target Device:</label>
              <select id="route-device-selector" onchange="currentDeviceId=this.value; window.openWebhookRoutesManager(this.value);" class="h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">
                ${deviceOptions || '<option value="">No devices found</option>'}
              </select>
            </div>
            <div>
              <button onclick="window.openAddRouteModal()" class="h-8 px-3.5 rounded text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white shadow transition-colors flex items-center gap-1.5">
                <span>+</span> Add Webhook Route
              </button>
            </div>
          </div>

          <!-- Routes Table Content -->
          <div class="flex-1 overflow-y-auto py-2">
            ${loadError ? `<div class="p-3 my-2 rounded bg-red-950/50 border border-red-800 text-red-300 text-xs">${loadError}</div>` : ''}
            <table class="w-full text-left border-collapse">
              <thead>
                <tr class="border-b border-slate-800 text-[11px] font-semibold uppercase tracking-wider text-slate-400 bg-slate-950/40">
                  <th class="py-2.5 px-3">Route Name</th>
                  <th class="py-2.5 px-3">Match Pattern (JID)</th>
                  <th class="py-2.5 px-3">Target Webhook URL</th>
                  <th class="py-2.5 px-3">Status</th>
                  <th class="py-2.5 px-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                ${routesRowsHtml}
              </tbody>
            </table>
          </div>

          <!-- Footer -->
          <div class="pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-500">
            <div>
              <span class="text-slate-400">Pro-tip:</span> Use <code class="text-cyan-400">@g.us</code> for all groups, or exact group ID <code class="text-cyan-400">1203...905@g.us</code>.
            </div>
            <button onclick="document.getElementById('webhook-routes-modal-root').innerHTML=''" class="px-4 py-1.5 rounded border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors">Close</button>
          </div>
        </div>
      </div>
    `;

    window.currentDeviceRoutes = routes;
  }

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
              <p class="text-xs text-slate-400">Device: <code class="text-cyan-400">${currentDeviceId}</code></p>
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
        await api('/devices/' + currentDeviceId + '/webhook/routes/' + existingRouteId, {
          method: 'PUT',
          data: payload,
          body: JSON.stringify(payload)
        });
        showToast('Route updated successfully');
      } else {
        await api('/devices/' + currentDeviceId + '/webhook/routes', {
          method: 'POST',
          data: payload,
          body: JSON.stringify(payload)
        });
        showToast('New route added successfully');
      }
      document.getElementById('route-form-modal-wrap').remove();
      renderRoutesListModal();
    } catch(err) {
      showToast('Failed to save route: ' + err.message, true);
    }
  };

  window.deleteWebhookRoute = async function(routeId) {
    if (!confirm('Are you sure you want to delete this webhook route?')) return;
    try {
      await api('/devices/' + currentDeviceId + '/webhook/routes/' + routeId, {
        method: 'DELETE'
      });
      showToast('Route deleted');
      renderRoutesListModal();
    } catch(err) {
      showToast('Failed to delete: ' + err.message, true);
    }
  };

  // Inject into sidebar navigation
  function injectSidebarItem() {
    if (document.getElementById('nav-webhook-routes')) return;

    // Look for sidebar nav container
    const navs = document.querySelectorAll('nav, aside, [class*="sidebar"]');
    for (const nav of navs) {
      const links = Array.from(nav.querySelectorAll('a, button'));
      const sampleItem = links.find(el => el.textContent.includes('Channels & Calls') || el.textContent.includes('Settings') || el.textContent.includes('Devices'));
      if (sampleItem) {
        const newBtn = document.createElement('button');
        newBtn.id = 'nav-webhook-routes';
        newBtn.className = sampleItem.className;
        newBtn.style.cursor = 'pointer';
        newBtn.innerHTML = webhookIconSvg + '<span class="ml-2 font-medium">Webhook Routes</span>';
        newBtn.onclick = function(e) {
          e.preventDefault();
          window.openWebhookRoutesManager();
        };

        if (sampleItem.parentElement) {
          sampleItem.parentElement.appendChild(newBtn);
          console.log('[GOWA] Successfully injected Webhook Routes into sidebar!');
          return;
        }
      }
    }
  }

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
          const savedDev = localStorage.getItem('gowa-ui.device.v1');
          let devId = null;
          if (savedDev) {
            try { devId = JSON.parse(savedDev).state.selectedDeviceId; } catch(err){}
          }
          window.openWebhookRoutesManager(devId);
        };
        webhookItem.parentElement.insertBefore(newItem, webhookItem.nextSibling);
      }
    }
  }

  // Run on interval & mutation observer
  setInterval(() => {
    injectSidebarItem();
    injectDeviceMenu();
  }, 1000);

  const observer = new MutationObserver(() => {
    injectSidebarItem();
    injectDeviceMenu();
  });
  observer.observe(document.body, { childList: true, subtree: true });

})();
</script>
"""

with open('storages/ui/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove old injected script if any
if '<!-- CUSTOM WEBHOOK ROUTING UI EXTENSION -->' in html:
    html = html.split('<!-- CUSTOM WEBHOOK ROUTING UI EXTENSION -->')[0] + '</body>\n</html>'

html = html.replace('</body>', script_code + '\n</body>')

with open('storages/ui/index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('SUCCESS: Webhook Routes UI injected cleanly into storages/ui/index.html')
