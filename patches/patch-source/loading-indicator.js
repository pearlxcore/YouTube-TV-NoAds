/* Playback feedback only: never changes playback, networking or DRM. */
(function () {
  'use strict';
  try {
    if (JSON.__noadsLoadingV1) return;
    var started = false;
    JSON.__noadsLoadingV1 = function () {
      if (started) return;
      /* Native Window/DOM wrappers are unsafe during early evaluation. Start
         only when response-filter sees a playable frontend response. */
      try {
        if (typeof document === 'undefined' || !document.body ||
            typeof setInterval !== 'function' || typeof clearInterval !== 'function') return;
        started = true;
        var video = null;
        var label = null;
        var waiting = false;
        var since = null;
        var timer = null;
        var handlers = {};
        function hide() {
          if (label && label.parentNode) label.parentNode.removeChild(label);
          label = null;
        }
        function reset() {
          waiting = false;
          since = null;
          hide();
        }
        function bind(next) {
          if (video === next) return;
          if (video && typeof video.removeEventListener === 'function') {
            for (var name in handlers) video.removeEventListener(name, handlers[name], false);
          }
          video = next;
          handlers = {};
          reset();
          if (!video || typeof video.addEventListener !== 'function') return;
          function wait() {
            if (!waiting) since = Date.now();
            waiting = true;
          }
          handlers.waiting = wait;
          handlers.waitingforkey = wait;
          handlers.loadstart = reset;
          handlers.emptied = reset;
          handlers.playing = reset;
          handlers.pause = reset;
          handlers.ended = reset;
          handlers.error = reset;
          for (var event in handlers) video.addEventListener(event, handlers[event], false);
        }
        function tick() {
          try {
            var route = typeof location === 'undefined' ? '' :
              String(location.hash || location.pathname || '');
            if (!/(^|[#/])watch(?:[/?&]|$)/.test(route)) { bind(null); hide(); return; }
            var videos = document.getElementsByTagName('video');
            bind(videos.length === 1 ? videos[0] : null);
            if (!video || video.error || video.ended) { reset(); return; }
            var initial = !(video.currentTime > 0);
            /* A normal paused frame is not a loading failure. Initial startup
               can be paused while the app prepares its media source. */
            var loading = (initial || !video.paused) &&
              (waiting || video.readyState < 2 || initial);
            if (!loading) { since = null; hide(); return; }
            if (since === null) since = Date.now();
            var age = Date.now() - since;
            /* A bounded message cannot stay over the app's error UI forever.
               A subsequent playing/loadstart event starts a new episode. */
            if (age < 600 || age >= 30000) { hide(); return; }
            if (!label) {
              label = document.createElement('div');
              label.style.cssText = 'position:absolute;left:5%;bottom:12%;' +
                'padding:16px 24px;background:#202020;color:#ffffff;' +
                'font-size:28px;z-index:2147483647;pointer-events:none;';
              document.body.appendChild(label);
            }
            label.textContent = 'Video is loading...';
          } catch (ignored) {
            if (timer !== null) clearInterval(timer);
            try { bind(null); hide(); } catch (cleanupIgnored) {}
          }
        }
        timer = setInterval(tick, 250);
        tick();
      } catch (ignored) {}
    };
  } catch (ignored) {}
}());
