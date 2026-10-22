// tvOS-style launcher for VIDAA. Plain ES2017 on purpose: the TV's browser
// engine is old and there is no build step.
(function () {
  'use strict';

  var CONFIG = window.DEVIDA_CONFIG || {};
  var STORE_KEY = 'devida.layout.v1';
  var COLS = 5;
  var ROW_REM = 11.4 + 5;          // --tile-h + --gap-y
  var SCROLL_TARGET_REM = 20;      // where a lower row settles, from the top
  var GRID_TOP_REM = 41;           // .grid-wrap top
  var HOLD_MS = 550;

  // VIDAA reports Back as 8; 461/10009 cover other TV engines, 27 is desktop Esc.
  var KEYS = {
    left: [37], up: [38], right: [39], down: [40],
    ok: [13],
    back: [8, 27, 461, 10009],
    red: [403, 77 /* M on a keyboard */]
  };

  var GLYPHS = {
    play: '<svg viewBox="0 0 48 48"><rect x="3" y="9" width="42" height="30" rx="9" fill="currentColor"/>' +
          '<path d="M20 17.5v13a1 1 0 0 0 1.5.86l11-6.5a1 1 0 0 0 0-1.72l-11-6.5A1 1 0 0 0 20 17.5z" fill="#c4000f"/></svg>',
    stremio: '<svg viewBox="0 0 48 48"><rect x="10" y="10" width="28" height="28" rx="5" transform="rotate(45 24 24)" fill="currentColor"/>' +
             '<path d="M20.5 17.5v13l10.5-6.5z" fill="#4a2bb8"/></svg>',
    jellyfin: '<svg viewBox="0 0 48 48"><path d="M24 6c-4 0-17 23.5-15 27.5S39 37.5 39 33.5 28 6 24 6z" fill="none" stroke="currentColor" stroke-width="3.5" stroke-linejoin="round"/>' +
              '<path d="M24 18c-2 0-8.5 11.5-7.5 13.5s14 2 15 0S26 18 24 18z" fill="currentColor"/></svg>',
    gear: gearSvg()
  };

  function gearSvg() {
    var teeth = '';
    for (var i = 0; i < 8; i++) {
      teeth += '<rect x="21" y="3" width="6" height="9" rx="1.5" transform="rotate(' + (i * 45) + ' 24 24)"/>';
    }
    return '<svg viewBox="0 0 48 48"><g fill="currentColor">' + teeth + '</g>' +
           '<circle cx="24" cy="24" r="12.5" fill="none" stroke="currentColor" stroke-width="5"/></svg>';
  }

  // ---------- DOM ----------

  var $ = function (id) { return document.getElementById(id); };
  var root = $('app');
  var grid = $('grid');
  var shelf = $('shelf');
  var bdLayers = root.querySelectorAll('.bd-layer');
  var sheetEl = $('sheet');

  // ---------- State ----------

  var catalog = [];       // every app that can run on this TV
  var layout = { order: [], hidden: [] };
  var visible = [];       // apps in grid order
  var focus = 0;
  var mode = 'home';      // home | sheet | move
  var sheet = null;       // { items, index, onClose }
  var activeLayer = 0;
  var backdropTimer = null;
  var okTimer = null;
  var okHeld = false;

  // ---------- Persistence ----------

  function loadLayout() {
    try {
      var raw = window.localStorage.getItem(STORE_KEY);
      if (raw) {
        var parsed = JSON.parse(raw);
        if (parsed && Array.isArray(parsed.order) && Array.isArray(parsed.hidden)) layout = parsed;
      }
    } catch (e) { /* private mode or blocked storage: use defaults */ }
  }

  function saveLayout() {
    try { window.localStorage.setItem(STORE_KEY, JSON.stringify(layout)); } catch (e) { /* ignore */ }
  }

  // ---------- Catalog ----------

  function resolveApp(app) {
    if (app.type === 'native' && !CONFIG.showNative) return null;
    if (app.url && app.url.indexOf('{jellyfinUrl}') !== -1) {
      if (!CONFIG.jellyfinUrl) return null;
      app.url = app.url.replace('{jellyfinUrl}', CONFIG.jellyfinUrl.replace(/\/+$/, ''));
    }
    return app;
  }

  function computeVisible() {
    var byId = {};
    catalog.forEach(function (a) { byId[a.id] = a; });
    var ordered = [];
    layout.order.forEach(function (id) { if (byId[id]) { ordered.push(byId[id]); delete byId[id]; } });
    // New apps (not in the saved order yet) go before Settings, which stays last.
    catalog.forEach(function (a) { if (byId[a.id]) ordered.push(a); });
    ordered.sort(function (a, b) { return (a.type === 'settings') - (b.type === 'settings'); });
    visible = ordered.filter(function (a) { return layout.hidden.indexOf(a.id) === -1; });
    layout.order = ordered.map(function (a) { return a.id; });
  }

  // ---------- Rendering ----------

  function faceGradient(app) {
    var c = app.colors || ['#3a3a3c', '#1c1c1e'];
    return 'linear-gradient(135deg, ' + c[0] + ' 0%, ' + c[1] + ' 100%)';
  }

  function glyphHtml(app) {
    if (app.icon) return '<img class="tile-icon" alt="" src="' + escapeAttr(app.icon) + '">';
    if (app.glyph === 'letter') return '<div class="tile-letter">' + escapeHtml(app.letter || app.name.charAt(0)) + '</div>';
    if (app.glyph === 'wordmark') return '<div class="tile-wordmark">' + escapeHtml(app.name) + '</div>';
    var svg = GLYPHS[app.glyph] || GLYPHS.play;
    var withName = app.glyph === 'play' || app.glyph === 'stremio' || app.glyph === 'jellyfin';
    return '<div class="tile-glyph">' + svg + '</div>' +
           (withName ? '<div class="tile-wordmark">' + escapeHtml(app.name) + '</div>' : '');
  }

  function renderGrid() {
    grid.innerHTML = '';
    visible.forEach(function (app, i) {
      var el = document.createElement('div');
      el.className = 'tile';
      el.setAttribute('role', 'gridcell');
      el.setAttribute('aria-label', app.name);
      el.dataset.index = String(i);
      el.innerHTML =
        '<div class="tile-shadow"></div>' +
        '<div class="tile-face" style="background:' + faceGradient(app) + '">' +
          glyphHtml(app) + '<div class="tile-shine"></div>' +
        '</div>' +
        '<div class="tile-label">' + escapeHtml(app.name) + '</div>';
      el.addEventListener('mouseenter', function () { if (mode === 'home') setFocus(i, 0, 0); });
      el.addEventListener('click', function () { if (mode === 'home') { setFocus(i, 0, 0); activate(); } });
      grid.appendChild(el);
    });
  }

  function tiles() { return grid.children; }

  function setFocus(index, dx, dy) {
    if (!visible.length) return;
    index = Math.max(0, Math.min(visible.length - 1, index));
    var prev = tiles()[focus];
    if (prev) prev.classList.remove('is-focused');
    var changed = index !== focus;
    focus = index;
    var el = tiles()[focus];
    if (!el) return;

    // Arrive leaning in the direction of travel, then settle flat.
    el.style.setProperty('--ry', (dx * 7) + 'deg');
    el.style.setProperty('--rx', (-dy * 7) + 'deg');
    el.classList.add('is-focused');
    window.setTimeout(function () {
      el.style.setProperty('--ry', '0deg');
      el.style.setProperty('--rx', '0deg');
    }, 140);

    var row = Math.floor(focus / COLS);
    var shift = row === 0 ? 0 : (SCROLL_TARGET_REM - GRID_TOP_REM - row * ROW_REM);
    grid.style.transform = 'translateY(' + shift + 'rem)';
    root.classList.toggle('is-scrolled', row > 0);

    if (changed || !shelf.textContent.trim()) scheduleBackdrop(visible[focus]);
  }

  function scheduleBackdrop(app) {
    // A short delay keeps fast scrubbing from strobing the whole screen.
    window.clearTimeout(backdropTimer);
    backdropTimer = window.setTimeout(function () { showBackdrop(app); }, 140);
  }

  function showBackdrop(app) {
    var c = app.colors || ['#3a3a3c', '#1c1c1e'];
    var next = bdLayers[1 - activeLayer];
    var art = '';
    if (app.backdrop) {
      art = '<div class="bd-image" style="background-image:url(\'' + escapeAttr(app.backdrop) + '\')"></div>';
    } else if (GLYPHS[app.glyph]) {
      art = '<div class="bd-art">' + GLYPHS[app.glyph] + '</div>';
    } else {
      art = '<div class="bd-art"><div class="bd-letter">' + escapeHtml(app.letter || app.name.charAt(0)) + '</div></div>';
    }
    next.style.background =
      'radial-gradient(70% 90% at 78% 18%, ' + c[0] + ' 0%, rgba(0,0,0,0) 62%),' +
      'radial-gradient(60% 70% at 30% 0%, ' + c[1] + ' 0%, rgba(0,0,0,0) 70%),' +
      '#050507';
    next.innerHTML = art;
    bdLayers[activeLayer].classList.remove('is-active');
    next.classList.add('is-active');
    activeLayer = 1 - activeLayer;

    $('shelf-eyebrow').textContent = app.type === 'native' ? 'Built-in app' : app.type === 'settings' ? 'Launcher' : 'Web app';
    $('shelf-title').textContent = app.name;
    $('shelf-tagline').textContent = app.tagline || '';
    shelf.classList.remove('is-in');
    void shelf.offsetWidth; // restart the entrance animation
    shelf.classList.add('is-in');
  }

  // ---------- Actions ----------

  function activate() {
    var app = visible[focus];
    if (!app) return;
    if (app.type === 'settings') return openSettings();
    if (app.type === 'native') return launchNative(app);
    if (!app.url) return toast('Set this app’s address in config.js');
    root.classList.add('is-launching');
    window.setTimeout(function () { window.location.href = app.url; }, 300);
  }

  function launchNative(app) {
    if (typeof CONFIG.launchNative === 'function') {
      try { CONFIG.launchNative(app); return; } catch (e) { /* fall through */ }
    }
    toast('Open ' + app.name + ' from the VIDAA Home');
  }

  function openTileMenu() {
    var app = visible[focus];
    if (!app) return;
    var items = [{ label: 'Move', action: startMove }];
    if (app.type !== 'settings') items.push({ label: 'Hide', action: function () { hideApp(app); } });
    items.push({ label: 'Cancel', action: closeSheet });
    openSheet(app.name, '', items);
  }

  function openSettings() {
    var hidden = catalog.filter(function (a) { return layout.hidden.indexOf(a.id) !== -1; });
    var items = hidden.map(function (a) {
      return { label: 'Show ' + a.name, action: function () { showApp(a); } };
    });
    items.push({ label: 'Run device probe', action: function () { window.location.href = 'probe.html'; } });
    items.push({ label: 'Reset layout', danger: true, action: resetLayout });
    items.push({ label: 'Close', action: closeSheet });
    openSheet('Settings', hidden.length ? hidden.length + ' hidden app' + (hidden.length > 1 ? 's' : '') : 'Hold OK on any app to move or hide it', items);
  }

  function hideApp(app) {
    layout.hidden.push(app.id);
    saveLayout();
    closeSheet();
    rebuild(Math.min(focus, visible.length - 2));
    toast(app.name + ' hidden — find it again in Settings');
  }

  function showApp(app) {
    layout.hidden = layout.hidden.filter(function (id) { return id !== app.id; });
    saveLayout();
    closeSheet();
    rebuild(focus);
  }

  function resetLayout() {
    layout = { order: [], hidden: [] };
    saveLayout();
    closeSheet();
    rebuild(0);
  }

  function rebuild(focusIndex) {
    computeVisible();
    renderGrid();
    focus = -1;
    setFocus(Math.max(0, focusIndex), 0, 0);
  }

  // ---------- Move mode ----------

  function startMove() {
    closeSheet();
    mode = 'move';
    root.classList.add('is-moving-mode');
    $('hint').textContent = 'Use the arrows to move · OK when done';
    tiles()[focus].classList.add('is-moving');
  }

  function moveBy(delta) {
    var target = focus + delta;
    // Settings stays last.
    var last = visible.length - 1 - (visible[visible.length - 1].type === 'settings' ? 1 : 0);
    if (visible[focus].type === 'settings' || target < 0 || target > last) return;
    var a = visible[focus];
    visible.splice(focus, 1);
    visible.splice(target, 0, a);
    // Map the visible order back onto the full order, keeping hidden apps in place.
    var hiddenIds = layout.hidden;
    var queue = visible.map(function (x) { return x.id; });
    layout.order = layout.order.map(function (id) { return hiddenIds.indexOf(id) !== -1 ? id : queue.shift(); });
    renderGrid();
    focus = -1;
    setFocus(target, delta > 0 ? 1 : -1, 0);
    tiles()[target].classList.add('is-moving');
  }

  function endMove() {
    mode = 'home';
    root.classList.remove('is-moving-mode');
    var el = tiles()[focus];
    if (el) el.classList.remove('is-moving');
    saveLayout();
  }

  // ---------- Sheet ----------

  function openSheet(title, subtitle, items) {
    mode = 'sheet';
    sheet = { items: items, index: 0 };
    $('sheet-title').textContent = title;
    $('sheet-subtitle').textContent = subtitle;
    var list = $('sheet-list');
    list.innerHTML = '';
    items.forEach(function (item, i) {
      var el = document.createElement('div');
      el.className = 'sheet-item' + (item.danger ? ' is-danger' : '');
      el.setAttribute('role', 'menuitem');
      el.textContent = item.label;
      el.addEventListener('mouseenter', function () { setSheetFocus(i); });
      el.addEventListener('click', function () { setSheetFocus(i); item.action(); });
      list.appendChild(el);
    });
    sheetEl.hidden = false;
    setSheetFocus(0);
  }

  function setSheetFocus(i) {
    var els = $('sheet-list').children;
    sheet.index = Math.max(0, Math.min(els.length - 1, i));
    for (var k = 0; k < els.length; k++) els[k].classList.toggle('is-focused', k === sheet.index);
  }

  function closeSheet() {
    sheetEl.hidden = true;
    sheet = null;
    mode = 'home';
  }

  // ---------- Input ----------

  function is(name, code) { return KEYS[name].indexOf(code) !== -1; }

  function onKeyDown(e) {
    var k = e.keyCode;
    var handled = true;

    if (mode === 'sheet') {
      if (is('up', k)) setSheetFocus(sheet.index - 1);
      else if (is('down', k)) setSheetFocus(sheet.index + 1);
      else if (is('ok', k)) { if (!e.repeat) sheet.items[sheet.index].action(); }
      else if (is('back', k) || is('red', k)) closeSheet();
      else handled = false;
    } else if (mode === 'move') {
      if (is('left', k)) moveBy(-1);
      else if (is('right', k)) moveBy(1);
      else if (is('up', k)) moveBy(-COLS);
      else if (is('down', k)) moveBy(COLS);
      else if (is('ok', k) || is('back', k)) { if (!e.repeat) endMove(); }
      else handled = false;
    } else {
      if (is('left', k)) { if (focus % COLS > 0) setFocus(focus - 1, -1, 0); }
      else if (is('right', k)) { if (focus % COLS < COLS - 1) setFocus(focus + 1, 1, 0); }
      else if (is('up', k)) { if (focus >= COLS) setFocus(focus - COLS, 0, -1); }
      else if (is('down', k)) {
        // Like tvOS, a short last row still catches focus coming from further right.
        var lastRow = Math.floor((visible.length - 1) / COLS);
        if (Math.floor(focus / COLS) < lastRow) setFocus(Math.min(focus + COLS, visible.length - 1), 0, 1);
      }
      else if (is('ok', k)) onOkDown(e);
      else if (is('red', k)) openTileMenu();
      else if (is('back', k)) { /* home is the root: nothing to go back to */ }
      else handled = false;
    }

    if (handled) e.preventDefault();
  }

  function onOkDown(e) {
    if (!CONFIG.okLongPress) { if (!e.repeat) activate(); return; }
    if (e.repeat || okTimer) return;
    okHeld = false;
    okTimer = window.setTimeout(function () {
      okTimer = null;
      okHeld = true;
      openTileMenu();
    }, HOLD_MS);
  }

  function onKeyUp(e) {
    if (!is('ok', e.keyCode) || mode !== 'home' || !CONFIG.okLongPress) return;
    if (okTimer) {
      window.clearTimeout(okTimer);
      okTimer = null;
      if (!okHeld) activate();
    }
    e.preventDefault();
  }

  // ---------- Chrome ----------

  var toastTimer = null;
  function toast(msg) {
    var el = $('toast');
    el.textContent = msg;
    el.classList.add('is-shown');
    window.clearTimeout(toastTimer);
    toastTimer = window.setTimeout(function () { el.classList.remove('is-shown'); }, 2800);
  }

  function tickClock() {
    var now = new Date();
    var time, date;
    try {
      time = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit', hour12: !CONFIG.use24h }).format(now);
      date = new Intl.DateTimeFormat(undefined, { weekday: 'long', month: 'long', day: 'numeric' }).format(now);
    } catch (e) {
      time = now.toTimeString().slice(0, 5);
      date = now.toDateString();
    }
    $('clock-time').textContent = time;
    $('clock-date').textContent = date;
    window.setTimeout(tickClock, (60 - now.getSeconds()) * 1000 + 50);
  }

  function relinkNextDns() {
    if (!CONFIG.nextdnsLinkUrl) return;
    // An image request needs no CORS; the response body doesn't matter.
    var img = new Image();
    img.referrerPolicy = 'no-referrer';
    img.src = CONFIG.nextdnsLinkUrl + (CONFIG.nextdnsLinkUrl.indexOf('?') === -1 ? '?' : '&') + 't=' + Date.now();
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (ch) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch];
    });
  }
  function escapeAttr(s) { return escapeHtml(s); }

  // ---------- Boot ----------

  function boot(apps) {
    catalog = apps.map(function (a) { return resolveApp(Object.assign({}, a)); }).filter(Boolean);
    loadLayout();
    computeVisible();
    renderGrid();
    focus = -1;
    setFocus(0, 0, 0);
    root.classList.remove('is-loading');
  }

  document.addEventListener('keydown', onKeyDown, true);
  document.addEventListener('keyup', onKeyUp, true);
  // Coming back from an app via the browser's history restores this page as it was left.
  window.addEventListener('pageshow', function () { root.classList.remove('is-launching'); });

  tickClock();
  relinkNextDns();

  fetch('apps.json', { cache: 'no-cache' })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(boot)
    .catch(function (err) {
      root.classList.remove('is-loading');
      $('shelf-title').textContent = 'Couldn’t load apps';
      $('shelf-tagline').textContent = String(err && err.message || err);
    });
})();
