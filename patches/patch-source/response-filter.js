/* Local response filter. Synthetic checks do not establish TV compatibility. */
(function () {
  'use strict';
  try {
    var parser = JSON.parse;
    if (parser.__x90hResponseFilterV1) return;
    var owns = Object.prototype.hasOwnProperty;
    var reportedPlayer = false;
    function notice(message) {
      try { if (typeof console !== 'undefined' && console.log) console.log('X90H_RE_FILTER ' + message); } catch (ignored) {}
    }
    function filter(items) {
      if (!Array.isArray(items)) return items;
      return items.filter(function (item) {
        return !item || typeof item !== 'object' || !owns.call(item, 'adSlotRenderer');
      });
    }
    function parse() {
      var result = parser.apply(this, arguments);
      try {
        if (!result || typeof result !== 'object' || Array.isArray(result)) return result;
        if (owns.call(result, 'responseContext') && result.responseContext &&
            typeof JSON.__x90hAboutBootstrapV1 === 'function') {
          JSON.__x90hAboutBootstrapV1();
        }
        var playerMetadata = result.adPlacements || result.adSlots || result.playerAds;
        if (owns.call(result, 'adPlacements')) result.adPlacements = [];
        if (owns.call(result, 'adSlots')) result.adSlots = [];
        if (owns.call(result, 'playerAds')) result.playerAds = false;
        if (playerMetadata && !reportedPlayer) {
          reportedPlayer = true;
          notice('player metadata filter reached');
        }
        var browse = result.contents && result.contents.tvBrowseRenderer;
        var surface = browse && browse.content && browse.content.tvSurfaceContentRenderer;
        var list = surface && surface.content && surface.content.sectionListRenderer;
        if (list && Array.isArray(list.contents)) {
          list.contents = filter(list.contents);
          list.contents.forEach(function (entry) {
            var shelf = entry && entry.shelfRenderer;
            var horizontal = shelf && shelf.content && shelf.content.horizontalListRenderer;
            if (horizontal && Array.isArray(horizontal.items)) horizontal.items = filter(horizontal.items);
          });
        }
      } catch (ignored) { /* Retain the parsed result if a reviver made it immutable. */ }
      return result;
    }
    Object.defineProperty(parse, '__x90hResponseFilterV1', { value: true });
    JSON.parse = parse;
    if (JSON.parse === parse) notice('installed v1');
  } catch (ignored) { /* Leave normal evaluation available if injection fails. */ }
}());
