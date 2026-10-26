// Reuse the lifecycle suite with the new profile's generated About matcher.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const marker = fs.readFileSync(path.join(root, 'patches/patch-source/about-marker.js'), 'utf8');
assert.equal(marker.split('5\\.30\\.320').length - 1, 1);
const generated = marker.replace('5\\.30\\.320', '7\\.30\\.301');
const wrappedFs = {...fs, readFileSync(name, encoding) {
  return path.basename(String(name)) === 'about-marker.js' ? generated : fs.readFileSync(name, encoding);
}};
const harness = fs.readFileSync(path.join(__dirname, 'about-marker.cjs'), 'utf8').replaceAll('5.30.320', '7.30.301');
vm.runInNewContext(harness, {
  require(name) {return name === 'node:fs' ? wrappedFs : require(name);}, __dirname, console,
});
