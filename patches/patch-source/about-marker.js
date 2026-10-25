/* Local build identification, restricted to the About > App version panel. */
(function () {
  'use strict';
  try {
    /* The evaluator also runs before Cobalt's native Window wrapper is bound.
       Register on the pure JS JSON object; touch DOM only after a parsed
       frontend response calls this bootstrap from response-filter.js. */
    if (JSON.__x90hAboutBootstrapV1) return;
    var marker = 'pearlxcore was here';
    var started = false;
    function updateAbout() {
      try {
        var body = document.body;
        if (!body) return;
        var text = body.textContent || '';
        if (text.indexOf('App version') < 0 || text.indexOf('Device') < 0 ||
            text.indexOf('Client') < 0) return;
        var nodes = [body];
        var visited = 0;
        while (nodes.length && visited++ < 4096) {
          var node = nodes.pop();
          if (node.nodeType === 3) {
            var value = node.nodeValue || '';
            if (/^\s*5\.30\.320\/web_[A-Za-z0-9_.-]+\s*$/.test(value)) {
              var parent = node.parentNode;
              if (!parent || !parent.style) return;
              parent.style.whiteSpace = 'pre-line';
              node.nodeValue = value.replace(/\s+$/, '') + '\n' + marker;
              return;
            }
          } else {
            var children = node.childNodes;
            if (children) {
              for (var i = children.length - 1; i >= 0; i--) nodes.push(children[i]);
            }
          }
        }
      } catch (ignored) { /* Identification must not interrupt normal UI. */ }
    }
    JSON.__x90hAboutBootstrapV1 = function () {
      if (started) return;
      try {
        if (typeof document === 'undefined' || typeof setInterval !== 'function' ||
            !document.body) return;
        setInterval(updateAbout, 1000);
        started = true;
        updateAbout();
      } catch (ignored) {}
    };
  } catch (ignored) {}
}());
