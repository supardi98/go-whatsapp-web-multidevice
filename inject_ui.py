import re
import os
import subprocess

html_path = 'storages/ui/index.html'

# Always restore clean from src/storages/ui/index.html first
with open('src/storages/ui/index.html', 'r', encoding='utf-8') as f:
    clean_html = f.read()

# Webhook Routes Modal & Management Script
# This runs completely safely without touching the compiled React bundle
modal_script = """
<!-- CUSTOM WEBHOOK ROUTING MODAL EXTENSION -->
<div id="webhook-routes-modal-root"></div>

<script>
(function() {
  console.log('[GOWA] Initializing Custom Webhook Routes Extension...');

  // SVG Webhook Icon
  var webhookIconSvg = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="inline-block shrink-0"><path d="M18 16.98h-5.99c-1.1 0-1.95.94-2.48 1.9A4 4 0 0 1 2 17c0-2.21 1.79-4 4-4h.01"/><path d="M6 13V6a3 3 0 0 1 3-3c1.3 0 2.4.84 2.82 2"/><path d="M12 9.5a3.5 3.5 0 0 1 7 0c0 1.61-.94 3-2.34 3.32"/><circle cx="6" cy="17" r="1"/><circle cx="12" cy="6" r="1"/><circle cx="17" cy="12" r="1"/></svg>';

  var currentDeviceId = null;
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
    toast.className = 'fixed bottom-5 right-5 z-[999999] px-4 py-2.5 rounded-lg shadow-xl text-xs font-medium transition-all duration-300 flex items-center gap-2 ' +
      (isError ? 'bg-red-950 border border-red-800 text-red-200' : 'bg-slate-900 border border-slate-700 text-slate-100');
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

  window.openWebhookRoutesManager = async function(deviceId) {
    var root = document.getElementById('webhook-routes-modal-root');
    if (!root) return;

    root.innerHTML = '<div class="fixed inset-0 z-[99999] bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">' +
      '<div class="bg-slate-900 border border-slate-800 rounded-xl p-8 text-center text-slate-300 text-sm">' +
      '<div class="inline-block animate-spin text-2xl mb-2">🌀</div><div>Loading webhook routes...</div>' +
      '</div></div>';

    try {
      var devResp = await api('/devices');
      allDevices = (devResp && devResp.results) ? devResp.results : [];
    } catch(e) {
      console.warn('Could not list devices:', e);
    }

    currentDeviceId = deviceId || getActiveDeviceId();
    await renderRoutesListModal();
  };

  window.closeWebhookRoutesManager = function() {
    var root = document.getElementById('webhook-routes-modal-root');
    if (root) root.innerHTML = '';
  };

  window.closeRouteFormModal = function() {
    var modal = document.getElementById('route-form-modal-wrap');
    if (modal) modal.remove();
  };

  async function renderRoutesListModal() {
    var root = document.getElementById('webhook-routes-modal-root');
    if (!root) return;

    var routes = [];
    var loadErr = null;
    if (currentDeviceId) {
      try {
        var res = await api('/devices/' + currentDeviceId + '/webhook/routes');
        routes = (res && res.results) ? res.results : [];
      } catch(e) {
        loadErr = e.message;
      }
    }
    window.currentDeviceRoutes = routes;

    var devOptions = allDevices.map(function(d) {
      return '<option value="' + d.id + '" ' + (d.id === currentDeviceId ? 'selected' : '') + '>' +
        (d.name || d.device || d.id) + ' (' + (d.phone_number || d.id) + ')' +
      '</option>';
    }).join('');

    var tableRows = '';
    if (routes.length === 0) {
      tableRows = '<tr><td colspan="5" class="py-12 text-center text-slate-500 text-xs">' +
        (loadErr ? '<div class="text-red-400 mb-1">Error: ' + loadErr + '</div>' : 'No custom webhook routes configured for this device yet.<br><span class="text-slate-600">Events fall back to device default webhook.</span>') +
      '</td></tr>';
    } else {
      tableRows = routes.map(function(r) {
        var isGroup = r.match_jid && (r.match_jid.includes('@g.us') || r.match_jid === '@g.us');
        var badgeColor = isGroup ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
        var exclusiveBadge = r.exclusive ? '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/15 text-amber-400 border border-amber-500/30 ml-2" title="Exclusive: suppresses default webhook">Exclusive</span>' : '';
        var enabledBadge = r.enabled ? '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">Active</span>' : '<span class="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-500 border border-slate-700">Disabled</span>';

        var paramsCount = r.custom_params ? Object.keys(r.custom_params).length : 0;
        var headersCount = r.custom_headers ? Object.keys(r.custom_headers).length : 0;
        var metaTags = [];
        if (paramsCount > 0) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700">' + paramsCount + ' param(s)</span>');
        if (headersCount > 0) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-300 border border-slate-700">' + headersCount + ' header(s)</span>');
        if (r.webhook_events) metaTags.push('<span class="text-[11px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400 border border-slate-700">' + r.webhook_events + '</span>');

        return '<tr class="border-b border-slate-800/80 hover:bg-slate-800/30 transition-colors text-xs text-slate-300">' +
          '<td class="py-3 px-3"><div class="font-medium text-slate-100 flex items-center">' + (r.name || 'Unnamed Route') + exclusiveBadge + '</div></td>' +
          '<td class="py-3 px-3"><span class="px-2 py-0.5 rounded font-mono text-xs border ' + badgeColor + '">' + (r.match_jid || '*') + '</span></td>' +
          '<td class="py-3 px-3"><div class="truncate max-w-[260px] font-mono text-slate-300" title="' + r.webhook_url + '">' + r.webhook_url + '</div><div class="flex gap-1 mt-1 flex-wrap">' + metaTags.join(' ') + '</div></td>' +
          '<td class="py-3 px-3">' + enabledBadge + '</td>' +
          '<td class="py-3 px-3 text-right space-x-1.5">' +
            '<button data-route-id="' + r.id + '" onclick="window.openEditRouteModal(this.dataset.routeId)" class="px-2.5 py-1 text-xs rounded border border-slate-700 hover:bg-slate-800 text-slate-200 transition-colors">Edit</button>' +
            '<button data-route-id="' + r.id + '" onclick="window.deleteWebhookRoute(this.dataset.routeId)" class="px-2.5 py-1 text-xs rounded bg-red-950/40 border border-red-800/50 hover:bg-red-900/60 text-red-300 transition-colors">Delete</button>' +
          '</td>' +
        '</tr>';
      }).join('');
    }

    root.innerHTML = '<div class="fixed inset-0 z-[99999] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">' +
      '<div class="bg-slate-900 border border-slate-800 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden">' +
        '<!-- Header -->' +
        '<div class="p-5 border-b border-slate-800 flex items-center justify-between">' +
          '<div class="flex items-center gap-3">' +
            '<div class="p-2.5 rounded-lg bg-cyan-950/50 border border-cyan-800/50 text-cyan-400">' + webhookIconSvg + '</div>' +
            '<div>' +
              '<h2 class="text-base font-semibold text-slate-100 flex items-center gap-2">Webhook Routes Manager <span class="text-[11px] px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">Multi-Destination</span></h2>' +
              '<p class="text-xs text-slate-400 mt-0.5">Route incoming WhatsApp events per sender JID/group to external webhooks.</p>' +
            '</div>' +
          '</div>' +
          '<div class="flex items-center gap-3">' +
            '<div class="flex items-center gap-2 text-xs text-slate-400">' +
              '<span>Device:</span>' +
              '<select onchange="window.switchDeviceRoute(this.value)" class="bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500">' +
                devOptions +
              '</select>' +
            '</div>' +
            '<button onclick="window.openAddRouteModal()" class="px-3 py-1.5 text-xs font-medium rounded bg-cyan-600 hover:bg-cyan-500 text-white transition-colors shadow flex items-center gap-1.5">' +
              '<span class="text-sm font-bold">+</span> Add Route' +
            '</button>' +
            '<button onclick="window.closeWebhookRoutesManager()" class="text-slate-400 hover:text-slate-100 p-1.5 rounded hover:bg-slate-800 text-lg">&times;</button>' +
          '</div>' +
        '</div>' +

        '<!-- Body Table -->' +
        '<div class="p-5 overflow-y-auto flex-1">' +
          '<div class="border border-slate-800 rounded-lg overflow-hidden bg-slate-950/50">' +
            '<table class="w-full text-left border-collapse">' +
              '<thead>' +
                '<tr class="border-b border-slate-800 bg-slate-900/80 text-[11px] font-medium text-slate-400 uppercase tracking-wider">' +
                  '<th class="py-2.5 px-3">Route Name</th>' +
                  '<th class="py-2.5 px-3">Match Pattern (JID)</th>' +
                  '<th class="py-2.5 px-3">Target Webhook URL</th>' +
                  '<th class="py-2.5 px-3">Status</th>' +
                  '<th class="py-2.5 px-3 text-right">Actions</th>' +
                '</tr>' +
              '</thead>' +
              '<tbody>' + tableRows + '</tbody>' +
            '</table>' +
          '</div>' +

          '<div class="mt-4 p-3 rounded-lg border border-slate-800/80 bg-slate-950/40 text-[11px] text-slate-400 flex items-start gap-2.5">' +
            '<span class="text-cyan-400">ℹ️</span>' +
            '<div>' +
              '<strong class="text-slate-300">Supported JID Patterns:</strong> ' +
              '<code class="text-cyan-400">120363429795720905@g.us</code> (specific group), ' +
              '<code class="text-cyan-400">@g.us</code> (all groups), ' +
              '<code class="text-cyan-400">628123456789@s.whatsapp.net</code> (single contact), ' +
              '<code class="text-cyan-400">*</code> (wildcard all).' +
            '</div>' +
          '</div>' +
        '</div>' +

        '<!-- Footer -->' +
        '<div class="p-4 border-t border-slate-800 flex justify-end">' +
          '<button onclick="window.closeWebhookRoutesManager()" class="px-4 py-1.5 text-xs rounded border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors">Close</button>' +
        '</div>' +
      '</div>' +
    '</div>';
  }

  window.switchDeviceRoute = function(devId) {
    currentDeviceId = devId;
    renderRoutesListModal();
  };

  window.openEditRouteModal = function(routeId) {
    var route = window.currentDeviceRoutes.find(function(r) { return r.id === routeId; });
    window.renderRouteFormModal(route);
  };

  window.openAddRouteModal = function() {
    window.renderRouteFormModal(null);
  };

  window.renderRouteFormModal = function(existingRoute) {
    var isEdit = !!existingRoute;
    var initialParams = existingRoute && existingRoute.custom_params ? Object.entries(existingRoute.custom_params) : [['token', '']];
    var initialHeaders = existingRoute && existingRoute.custom_headers ? Object.entries(existingRoute.custom_headers) : [['Authorization', 'Bearer ']];

    var paramRows = initialParams.map(function(pair, i) {
      return '<div class="flex items-center gap-2 param-row mb-1.5">' +
        '<input type="text" placeholder="Key (e.g. token)" value="' + pair[0] + '" class="p-key flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
        '<input type="text" placeholder="Value" value="' + pair[1] + '" class="p-val flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
        '<button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm">&times;</button>' +
      '</div>';
    }).join('');

    var headerRows = initialHeaders.map(function(pair, i) {
      return '<div class="flex items-center gap-2 header-row mb-1.5">' +
        '<input type="text" placeholder="Header Name" value="' + pair[0] + '" class="h-key flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
        '<input type="text" placeholder="Header Value" value="' + pair[1] + '" class="h-val flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
        '<button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm">&times;</button>' +
      '</div>';
    }).join('');

    var formModal = document.createElement('div');
    formModal.id = 'route-form-modal-wrap';
    formModal.className = 'fixed inset-0 z-[100000] bg-black/85 backdrop-blur-sm flex items-center justify-center p-4';
    formModal.innerHTML = '<div class="bg-slate-900 border border-slate-800 rounded-xl max-w-lg w-full max-h-[92vh] flex flex-col shadow-2xl p-6">' +
      '<div class="flex items-start justify-between pb-3 border-b border-slate-800">' +
        '<div>' +
          '<h3 class="text-sm font-semibold text-slate-100">' + (isEdit ? 'Edit Webhook Route' : 'Add Webhook Route') + '</h3>' +
          '<p class="text-xs text-slate-400">Device: <code class="text-cyan-400">' + currentDeviceId + '</code></p>' +
        '</div>' +
        '<button onclick="window.closeRouteFormModal()" class="text-slate-400 hover:text-slate-100 text-lg">&times;</button>' +
      '</div>' +

      '<form id="route-form" class="flex-1 overflow-y-auto py-4 space-y-3.5 text-xs" data-route-id="' + (existingRoute ? existingRoute.id : '') + '" onsubmit="window.handleSaveRoute(event, this.dataset.routeId)">' +
        '<div>' +
          '<label class="block font-medium text-slate-300 mb-1">Route Name</label>' +
          '<input type="text" id="rf-name" value="' + (existingRoute ? (existingRoute.name || '') : '') + '" placeholder="e.g. Windmill Group Agent" class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 focus:outline-none focus:border-cyan-500" required>' +
        '</div>' +

        '<div>' +
          '<label class="block font-medium text-slate-300 mb-1 flex justify-between">' +
            '<span>Match Pattern (JID / Group)</span>' +
            '<span class="text-[10px] text-cyan-400">exact JID or @g.us</span>' +
          '</label>' +
          '<input type="text" id="rf-jid" value="' + (existingRoute ? (existingRoute.match_jid || '') : '') + '" placeholder="e.g. 120363429795720905@g.us" class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500" required>' +
        '</div>' +

        '<div>' +
          '<label class="block font-medium text-slate-300 mb-1">Destination Webhook URL</label>' +
          '<input type="url" id="rf-url" value="' + (existingRoute ? (existingRoute.webhook_url || '') : '') + '" placeholder="http://localhost:8000/api/w/admins/jobs/run/..." class="w-full h-8 px-2.5 rounded bg-slate-950 border border-slate-800 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500" required>' +
        '</div>' +

        '<!-- Custom Params -->' +
        '<div class="pt-2 border-t border-slate-800/80">' +
          '<div class="flex items-center justify-between mb-1.5">' +
            '<label class="font-medium text-slate-300">Custom Query Parameters (?key=value)</label>' +
            '<button type="button" onclick="window.addParamRow()" class="text-[11px] text-cyan-400 hover:text-cyan-300">+ Add Param</button>' +
          '</div>' +
          '<div id="param-rows-container">' + paramRows + '</div>' +
        '</div>' +

        '<!-- Custom Headers -->' +
        '<div class="pt-2 border-t border-slate-800/80">' +
          '<div class="flex items-center justify-between mb-1.5">' +
            '<label class="font-medium text-slate-300">Custom HTTP Headers (Authorization, etc.)</label>' +
            '<button type="button" onclick="window.addHeaderRow()" class="text-[11px] text-cyan-400 hover:text-cyan-300">+ Add Header</button>' +
          '</div>' +
          '<div id="header-rows-container">' + headerRows + '</div>' +
        '</div>' +

        '<!-- Options -->' +
        '<div class="pt-2 border-t border-slate-800/80 space-y-2">' +
          '<label class="flex items-center gap-2 cursor-pointer">' +
            '<input type="checkbox" id="rf-exclusive" ' + (existingRoute && existingRoute.exclusive ? 'checked' : '') + ' class="rounded bg-slate-950 border-slate-700 text-cyan-600 focus:ring-0">' +
            '<span class="text-slate-300 font-medium">Exclusive Route</span>' +
            '<span class="text-slate-500 text-[10px]">(Suppresses device default webhook when matched)</span>' +
          '</label>' +
          '<label class="flex items-center gap-2 cursor-pointer">' +
            '<input type="checkbox" id="rf-enabled" ' + (existingRoute ? (existingRoute.enabled ? 'checked' : '') : 'checked') + ' class="rounded bg-slate-950 border-slate-700 text-cyan-600 focus:ring-0">' +
            '<span class="text-slate-300 font-medium">Route Enabled</span>' +
          '</label>' +
        '</div>' +

        '<div class="pt-4 border-t border-slate-800 flex justify-end gap-2">' +
          '<button type="button" onclick="window.closeRouteFormModal()" class="px-3 py-1.5 rounded border border-slate-700 hover:bg-slate-800 text-slate-300 transition-colors">Cancel</button>' +
          '<button type="submit" class="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition-colors shadow">Save Route</button>' +
        '</div>' +
      '</form>' +
    '</div>';

    document.body.appendChild(formModal);
  };

  window.addParamRow = function() {
    var c = document.getElementById('param-rows-container');
    if (!c) return;
    var row = document.createElement('div');
    row.className = 'flex items-center gap-2 param-row mb-1.5';
    row.innerHTML = '<input type="text" placeholder="Key" class="p-key flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
      '<input type="text" placeholder="Value" class="p-val flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
      '<button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm">&times;</button>';
    c.appendChild(row);
  };

  window.addHeaderRow = function() {
    var c = document.getElementById('header-rows-container');
    if (!c) return;
    var row = document.createElement('div');
    row.className = 'flex items-center gap-2 header-row mb-1.5';
    row.innerHTML = '<input type="text" placeholder="Header Name" class="h-key flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
      '<input type="text" placeholder="Header Value" class="h-val flex-1 h-7 px-2 rounded bg-slate-950 border border-slate-800 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-mono">' +
      '<button type="button" onclick="this.parentElement.remove()" class="text-slate-500 hover:text-red-400 px-1 text-sm">&times;</button>';
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
        await api('/devices/' + currentDeviceId + '/webhook/routes/' + existingRouteId, {
          method: 'PUT',
          body: payload
        });
        showToast('Route updated successfully');
      } else {
        await api('/devices/' + currentDeviceId + '/webhook/routes', {
          method: 'POST',
          body: payload
        });
        showToast('New route added successfully');
      }
      var modalWrap = document.getElementById('route-form-modal-wrap');
      if (modalWrap) modalWrap.remove();
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

    var navs = document.querySelectorAll('nav, aside, [class*="sidebar"]');
    for (var i = 0; i < navs.length; i++) {
      var nav = navs[i];
      var links = Array.from(nav.querySelectorAll('a, button'));
      var sampleItem = links.find(function(el) {
        var t = el.textContent || '';
        return t.includes('Channels & Calls') || t.includes('Settings') || t.includes('Devices');
      });
      if (sampleItem) {
        var newBtn = document.createElement('button');
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
    var menus = document.querySelectorAll('[role="menu"]');
    for (var i = 0; i < menus.length; i++) {
      var menu = menus[i];
      if (menu.querySelector('#menu-webhook-routes')) continue;
      var items = Array.from(menu.querySelectorAll('[role="menuitem"], button'));
      var webhookItem = items.find(function(el) { return (el.textContent || '').includes('Webhook'); });
      if (webhookItem && webhookItem.parentElement) {
        var newItem = document.createElement('button');
        newItem.id = 'menu-webhook-routes';
        newItem.className = webhookItem.className;
        newItem.innerHTML = webhookIconSvg + '<span class="ml-2">Webhook Routes</span>';
        newItem.onclick = function(e) {
          e.preventDefault();
          window.openWebhookRoutesManager();
        };
        webhookItem.parentElement.insertBefore(newItem, webhookItem.nextSibling);
      }
    }
  }

  setInterval(function() {
    injectSidebarItem();
    injectDeviceMenu();
  }, 1000);

  var observer = new MutationObserver(function() {
    injectSidebarItem();
    injectDeviceMenu();
  });
  observer.observe(document.body, { childList: true, subtree: true });

})();
</script>
"""

# Inject cleanly before </body> without touching any React bundle line
final_html = clean_html.replace('</body>', modal_script + '\n</body>')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(final_html)

print("SUCCESS: index.html cleanly restored and injected without touching bundle!")
