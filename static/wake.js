/*!
 * wake.js: a bar at the bottom of the page while a free Render server wakes up.
 *
 * Render's free plan puts a web service to sleep after 15 minutes without requests. The next
 * request starts it again, which takes 30 to 60 seconds. This script:
 *   1. asks the API's health URL as soon as the page opens, so the server starts waking at once;
 *   2. shows the bar, with a running count of seconds, if the server has not answered in 3 seconds;
 *   3. watches the page's own API calls: when one is slow, it asks the health URL again, and shows
 *      the bar only if that is slow too (a slow AI answer from an awake server shows nothing).
 *
 * Usage, in index.html (before the app's own script):
 *   <script src="/wake.js" data-api="https://my-api.onrender.com" data-health="/api/health"></script>
 *
 *   data-api      the API's base URL. Leave it empty when the API is on the same site.
 *   data-health   a cheap GET route on the API. Any answer counts, even a 404.
 *   data-text     optional: your own wording for the bar.
 *
 * No dependencies, no cookies, no storage. Works with React, Vue, plain HTML or anything else.
 */
(function () {
  "use strict";
  if (window.__wakeBar) return;
  window.__wakeBar = true;

  var me = document.currentScript;
  var attr = function (name, fallback) {
    var v = me && me.getAttribute(name);
    // A build tool that had no value leaves its placeholder, e.g. %VITE_API_URL%.
    return v && !/^%.*%$/.test(v.trim()) ? v.trim() : fallback;
  };
  var api = (attr("data-api", "") || window.API_URL || "").replace(/\/+$/, "");
  var healthUrl = api + attr("data-health", "/api/health");
  var TEXT = attr("data-text",
    "Waking up the free server. Render's free plan puts it to sleep after 15 quiet minutes; it is back in 30 to 60 seconds.");
  var SLOW_MS = 3500;

  // ------------------------------------------------------------------ the bar
  var css =
    ".wkb{position:fixed;left:0;right:0;bottom:16px;z-index:2147483000;margin:0 auto;width:min(720px,calc(100vw - 32px));" +
    "display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:12px;box-sizing:border-box;" +
    "background:rgba(17,24,39,.96);color:#f9fafb;font:14px/1.45 system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;" +
    "box-shadow:0 14px 36px -12px rgba(0,0,0,.55)}" +
    ".wkb__dot{width:9px;height:9px;border-radius:50%;background:#fbbf24;flex:none;animation:wkb 1s ease-in-out infinite alternate}" +
    ".wkb__text{flex:1}.wkb__secs{font-weight:700;font-variant-numeric:tabular-nums;min-width:3ch;text-align:right;color:#fde68a}" +
    ".wkb--ready{background:rgba(6,95,70,.96)}.wkb--failed{background:rgba(153,27,27,.96)}" +
    ".wkb button{font:inherit;color:inherit;background:none;border:1px solid rgba(255,255,255,.45);border-radius:6px;padding:4px 10px;cursor:pointer}" +
    "@keyframes wkb{from{opacity:.3}to{opacity:1}}" +
    "@media (prefers-reduced-motion:reduce){.wkb__dot{animation:none}}" +
    "@media print{.wkb{display:none}}";
  var bar = null, secsEl = null, since = 0, ticker = null, hideTimer = null;

  function ensureBar() {
    if (bar) return bar;
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);
    bar = document.createElement("div");
    bar.setAttribute("role", "status");
    bar.setAttribute("aria-live", "polite");
    document.body.appendChild(bar);
    return bar;
  }

  function render(state) {
    clearInterval(ticker);
    clearTimeout(hideTimer);
    if (state === "hidden") {
      if (bar) bar.style.display = "none";
      return;
    }
    ensureBar();
    bar.style.display = "flex";
    bar.className = "wkb wkb--" + state;
    bar.textContent = "";
    if (state === "waking") {
      bar.appendChild(el("span", "wkb__dot"));
      bar.appendChild(el("span", "wkb__text", TEXT));
      secsEl = bar.appendChild(el("span", "wkb__secs"));
      secsEl.setAttribute("aria-hidden", "true");
      var tick = function () { secsEl.textContent = Math.round((Date.now() - since) / 1000) + "s"; };
      tick();
      ticker = setInterval(tick, 1000);
    } else if (state === "ready") {
      bar.appendChild(el("span", "wkb__text", "The server is awake."));
      hideTimer = setTimeout(function () { render("hidden"); }, 2500);
    } else if (state === "failed") {
      bar.appendChild(el("span", "wkb__text", "The server is not answering. Check your connection, then try again."));
      var retry = el("button", null, "Try again");
      retry.onclick = function () { render("hidden"); probe(3000); };
      bar.appendChild(retry);
    }
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text) n.textContent = text;
    return n;
  }

  // ------------------------------------------------------------------ asking the server
  var probing = false;
  function probe(showAfterMs, waitingSince) {
    if (probing) return;
    probing = true;
    var shown = false;
    var started = waitingSince || Date.now();
    var show = setTimeout(function () {
      shown = true;
      since = started;
      whenBody(function () { render("waking"); });
    }, showAfterMs);
    // no-cors: any answer from the server counts, whatever its CORS settings or status code.
    realFetch(healthUrl, { mode: "no-cors", cache: "no-store" }).then(function () {
      clearTimeout(show);
      probing = false;
      if (shown) render("ready");
    }, function () {
      clearTimeout(show);
      probing = false;
      whenBody(function () { render("failed"); });
    });
  }

  function whenBody(fn) {
    if (document.body) fn();
    else document.addEventListener("DOMContentLoaded", fn);
  }

  // ------------------------------------------------------------------ watching the page's own calls
  var realFetch = window.fetch.bind(window);
  function isApiCall(url) {
    try {
      var u = new URL(url, location.href);
      return api ? u.href.indexOf(api) === 0 : u.origin === location.origin && u.pathname.indexOf("/api") === 0;
    } catch (e) {
      return false;
    }
  }
  function watch(promise) {
    var t = setTimeout(function () { probe(2000, Date.now() - SLOW_MS); }, SLOW_MS);
    var done = function () { clearTimeout(t); };
    promise.then(done, done);
    return promise;
  }
  window.fetch = function (input, init) {
    var p = realFetch(input, init);
    var url = typeof input === "string" ? input : input && (input.url || String(input));
    return isApiCall(url) ? watch(p) : p;
  };
  var open = XMLHttpRequest.prototype.open;
  var send = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (method, url) {
    this.__wakeUrl = url;
    return open.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function () {
    if (isApiCall(this.__wakeUrl)) {
      var xhr = this;
      var t = setTimeout(function () { probe(2000, Date.now() - SLOW_MS); }, SLOW_MS);
      xhr.addEventListener("loadend", function () { clearTimeout(t); });
    }
    return send.apply(this, arguments);
  };

  probe(3000);
})();
