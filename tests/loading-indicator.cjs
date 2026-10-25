const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const source = ['response-filter.js', 'about-marker.js', 'loading-indicator.js']
  .map(name => fs.readFileSync(path.join(root, 'patches/patch-source', name), 'utf8')).join('\n');
const player = {responseContext: {}, streamingData: {}, videoDetails: {},
  playabilityStatus: {status: 'OK'}};
function makeVideo() {
  const state = {readyState: 0, currentTime: 0, paused: true, error: null, ended: false};
  const listeners = new Map();
  const media = {addEventListener(name, fn) {
    if (!listeners.has(name)) listeners.set(name, new Set());
    listeners.get(name).add(fn);
  }, removeEventListener(name, fn) {listeners.get(name)?.delete(fn);}};
  for (const name of Object.keys(state)) Object.defineProperty(media, name, {get: () => state[name]});
  Object.freeze(media); // No setter or playback/seek/DRM/network methods available.
  return {state, media, listeners,
    emit(name) {for (const fn of listeners.get(name) || []) fn();},
    count() {return [...listeners.values()].reduce((sum, set) => sum + set.size, 0);}};
}
function fixture(route = '#/watch?v=fixture') {
  let now = 0, id = 0, accesses = 0;
  const timers = new Map();
  const video = makeVideo();
  let videos = [video.media];
  const body = {childNodes: [], textContent: '',
    appendChild(node) {this.childNodes.push(node); node.parentNode = this;},
    removeChild(node) {this.childNodes.splice(this.childNodes.indexOf(node), 1); node.parentNode = null;}};
  const context = vm.createContext({Date: {now: () => now}, location: {hash: route},
    setInterval(fn, ms) {timers.set(++id, {fn, ms}); return id;},
    clearInterval(handle) {timers.delete(handle);}});
  Object.defineProperty(context, 'document', {configurable: true, get() {
    accesses++; throw Error('native DOM not ready');
  }});
  vm.runInContext(source, context);
  assert.equal(accesses, 0, 'early injection must not access native DOM');
  Object.defineProperty(context, 'document', {configurable: true, value: {body,
    getElementsByTagName(tag) {assert.equal(tag, 'video'); return videos;},
    createElement(tag) {assert.equal(tag, 'div'); return {style: {}, textContent: ''};}}});
  return {body, context, video, timers,
    parse(value = player) {context.input = JSON.stringify(value); return vm.runInContext('JSON.parse(input)', context);},
    tick(time) {now = time; for (const item of [...timers.values()]) item.fn();},
    videos(value) {videos = value;},
    active() {return [...timers.values()].filter(item => item.ms === 250).length;}};
}
const f = fixture('#/');
f.parse({responseContext: {}});
f.parse({...player, playabilityStatus: {status: 'ERROR'}});
assert.equal(f.active(), 0, 'only playable response arms feedback');
assert.equal(JSON.stringify(f.parse()), JSON.stringify(player), 'response unchanged');
f.tick(1000);
assert.equal(f.body.childNodes.length, 0, 'Home never shows video feedback');
assert.equal(f.video.count(), 0);
f.context.location.hash = '#/watch?v=fixture';
f.tick(1250); f.tick(1500);
assert.equal(f.body.childNodes.length, 0, 'short loads do not flash a message');
f.tick(2000);
assert.equal(f.body.childNodes[0].textContent, 'Video is loading...');
assert.match(f.body.childNodes[0].style.cssText, /pointer-events:none/);
const listenerCount = f.video.count();
vm.runInContext(source, f.context); f.parse(); f.tick(2250);
assert.equal(f.active(), 1, 'injection and responses do not duplicate timers');
assert.equal(f.video.count(), listenerCount, 'listeners are not duplicated');
Object.assign(f.video.state, {readyState: 4, currentTime: 1, paused: false});
f.video.emit('playing');
assert.equal(f.body.childNodes.length, 0, 'playing removes message immediately');
for (const event of ['waiting', 'waitingforkey']) {
  f.tick(3000); f.video.emit(event); f.tick(3750);
  assert.equal(f.body.childNodes.length, 1, event + ' shows message during later playback');
  f.video.emit('playing'); f.tick(4000);
  assert.equal(f.body.childNodes.length, 0);
}
f.video.emit('waiting'); f.tick(5000);
f.video.state.paused = true; f.video.emit('pause'); f.tick(6000); f.tick(7000);
assert.equal(f.body.childNodes.length, 0, 'manual pause is not reported as buffering');
f.video.state.paused = false; f.video.state.readyState = 1;
f.tick(8000); f.tick(9000);
assert.equal(f.body.childNodes.length, 1, 'missing media data detected without events');
f.context.location.hash = '#/settings'; f.tick(9250);
assert.equal(f.body.childNodes.length, 0);
assert.equal(f.video.count(), 0, 'navigation removes media listeners');
f.context.location.hash = '#/watch?v=second'; f.tick(10000); f.tick(11000);
assert.equal(f.body.childNodes.length, 1, 'another video can show loading feedback');
const replacement = makeVideo();
f.videos([replacement.media]); f.tick(11500);
assert.equal(f.video.count(), 0, 'replaced video releases listeners');
assert.equal(replacement.count(), listenerCount);
f.videos([replacement.media, f.video.media]); f.tick(12000);
assert.equal(f.body.childNodes.length, 0, 'ambiguous media elements fail closed');
assert.equal(replacement.count(), 0);
for (const condition of ['error', 'ended', 'timeout']) {
  const g = fixture(); g.parse(); g.tick(750);
  assert.equal(g.body.childNodes.length, 1);
  if (condition === 'error') {g.video.state.error = {code: 3}; g.video.emit('error');}
  if (condition === 'ended') {g.video.state.ended = true; g.video.emit('ended');}
  g.tick(condition === 'timeout' ? 30000 : 1000);
  assert.equal(g.body.childNodes.length, 0, condition + ' removes feedback');
  if (condition === 'timeout') {
    g.tick(31000); assert.equal(g.body.childNodes.length, 0, 'timeout stays hidden');
    g.video.state.currentTime = 1; g.video.state.readyState = 4; g.video.state.paused = false;
    g.video.emit('playing'); g.tick(32000); g.video.emit('waiting'); g.tick(33000);
    assert.equal(g.body.childNodes.length, 1, 'new waiting episode after recovery is supported');
  }
}
const broken = fixture(); broken.parse(); broken.tick(750);
broken.context.document.getElementsByTagName = () => {throw Error('DOM lost');};
broken.tick(1000);
assert.equal(broken.body.childNodes.length, 0);
assert.equal(broken.video.count(), 0);
assert.equal(broken.active(), 0, 'DOM failures remove UI, listeners and timer');
console.log('PASS loading feedback: deferred DOM, repeated waits, pause, navigation, error, deadline and cleanup');
