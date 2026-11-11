const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'sw.js'), 'utf8');
const handlers = {};
const shell = [];
const deleted = [];
let claimed = false;
let networkOffline = false;
const hostCache = { addAll: async items => shell.push(...items), put: async () => {} };
const sandbox = {
  self: {
    location: { origin: 'https://johnny-bui.github.io' },
    clients: { claim: async () => { claimed = true; } },
    addEventListener: (name, callback) => { handlers[name] = callback; },
    skipWaiting: async () => {}
  },
  caches: {
    open: async () => hostCache,
    keys: async () => ['tomeng-v15-native', 'tomenghost-v0', 'tomenghost-v1', 'tomenghost-v2', 'another-app-cache'],
    delete: async key => { deleted.push(key); return true; },
    match: async key => key === './index.html' ? { offlineShell: true } : null
  },
  URL,
  fetch: async () => { if (networkOffline) throw new Error('offline'); return { ok: true, clone() { return this; } }; },
  Response: { error: () => ({ error: true }) }
};
vm.runInNewContext(source, sandbox);

(async () => {
  let pending;
  handlers.install({ waitUntil: promise => { pending = promise; } });
  await pending;
  assert.ok(shell.includes('./data.js') && shell.includes('./meta.js') && shell.includes('./app.js'));
  assert.ok(shell.includes('./host-icon-192.png') && shell.includes('./host-icon-512.png'));
  for (const file of shell) assert.ok(fs.existsSync(path.join(root, file.replace(/^\.\//, ''))), `precache file exists: ${file}`);

  handlers.activate({ waitUntil: promise => { pending = promise; } });
  await pending;
  assert.deepEqual(deleted, ['tomenghost-v0', 'tomenghost-v1', 'tomenghost-v2'], 'Host worker deletes only its own previous cache family');
  assert.ok(claimed);

  networkOffline = true;
  let response;
  handlers.fetch({
    request: { method: 'GET', mode: 'navigate', url: 'https://johnny-bui.github.io/TomEng-Host/' },
    respondWith(promise) { response = promise; }
  });
  assert.deepEqual(await response, { offlineShell: true }, 'offline navigation falls back to the Host app shell');

  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'manifest.webmanifest'), 'utf8'));
  assert.equal(manifest.scope, './');
  assert.equal(manifest.id, './');
  assert.match(manifest.name, /^TomEng Host/);
  const index = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert.match(index, /sw\.js\?v=1\.0\.2-host/);
  assert.doesNotMatch(index, /legacy-lesson-plan|legacy-v2-fingerprint/);
  assert.match(source, /const CACHE = 'tomenghost-v3'/);
  assert.match(source, /key\.startsWith\('tomenghost-'\)/);
  assert.ok(fs.existsSync(path.join(root, 'logo-host.svg')));
  console.log('PASS: unique PWA identity, shell assets, offline fallback, update version and cross-app cache isolation');
})().catch(error => { console.error(error); process.exitCode = 1; });
