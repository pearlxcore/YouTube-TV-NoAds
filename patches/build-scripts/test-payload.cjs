const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const payload = fs.readFileSync(path.join(root,'patches/patch-source/response-filter.js'),'utf8');
const context = vm.createContext({});
vm.runInContext('this.originalParser = JSON.parse', context);
vm.runInContext(payload, context);
let count = 0;
function test(name, code) {
  assert.equal(vm.runInContext(code, context), true, name);
  console.log('PASS '+name); count++;
}
test('root player ad metadata removed; content streams preserved', `(() => {
  const r=JSON.parse('{"adPlacements":[1],"adSlots":[2],"playerAds":[3],"streamingData":{"formats":[{"url":"fixture-content"}]},"videoDetails":{"videoId":"fixture"}}');
  return r.adPlacements.length===0 && r.adSlots.length===0 && r.playerAds===false && r.streamingData.formats[0].url==='fixture-content' && r.videoDetails.videoId==='fixture';
})()`);
test('homepage and shelf ad renderer filtering', `(() => {
 const items=[{adSlotRenderer:{}},{tileRenderer:{id:'content'}}];
 const contents=[{adSlotRenderer:{}},{shelfRenderer:{content:{horizontalListRenderer:{items}}}}];
 const fixture={contents:{tvBrowseRenderer:{content:{tvSurfaceContentRenderer:{content:{sectionListRenderer:{contents}}}}}}};
 const r=JSON.parse(JSON.stringify(fixture));
 const a=r.contents.tvBrowseRenderer.content.tvSurfaceContentRenderer.content.sectionListRenderer.contents;
 return a.length===1 && a[0].shelfRenderer.content.horizontalListRenderer.items.length===1;
})()`);
test('unrelated structures unchanged', `JSON.stringify(JSON.parse('{"settings":{"playerAds":true},"array":[1,2],"text":"adSlots"}'))==='{"settings":{"playerAds":true},"array":[1,2],"text":"adSlots"}'`);
test('null, scalars and root arrays preserved', `JSON.parse('null')===null && JSON.parse('17')===17 && JSON.parse('"x"')==='x' && JSON.parse('[1,2]').length===2`);
test('reviver semantics preserved', `JSON.parse('{"n":2}',(k,v)=>k==='n'?v*3:v).n===6`);
test('syntax errors still propagate', `(() => {try {JSON.parse('{');return false;} catch(e){return e instanceof SyntaxError;}})()`);
test('frozen reviver does not add a parser error', `Object.isFrozen(JSON.parse('{"adSlots":[1]}',(k,v)=>k===''?Object.freeze(v):v))`);
vm.runInContext('this.installedParser = JSON.parse',context);
vm.runInContext(payload,context);
test('installation is idempotent per realm', 'JSON.parse===installedParser');
const fresh=vm.createContext({}); vm.runInContext(payload,fresh);
assert.equal(vm.runInContext('JSON.parse.__x90hResponseFilterV1===true',fresh),true);
console.log('PASS fresh realm installation'); count++;
console.log(JSON.stringify({passed:count,scope:'synthetic fixtures only; no TV or real frontend proof'}));
