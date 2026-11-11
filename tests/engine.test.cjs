const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const sources = ['data.js', 'meta.js', 'app.js'].map(name => fs.readFileSync(path.join(root, name), 'utf8'));

function boot(seed = {}, day = '2026-11-11', options = {}) {
  const storage = new Map(Object.entries(seed));
  const handlers = {};
  const elements = new Map();
  let today = day;
  let downloaded = '';
  class ClockDate extends Date {
    constructor(...args) { super(...(args.length ? args : [`${today}T12:00:00`])); }
    static now() { return new Date(`${today}T12:00:00`).getTime(); }
  }
  const makeElement = () => ({
    innerHTML: '', textContent: '', value: '', classList: { add() {}, remove() {} },
    focus() {}, setSelectionRange() {}, querySelector() { return null; },
    querySelectorAll() { return []; }, getClientRects() { return []; }, click() {},
    set href(value) { this._href = value; }, set download(value) { this._download = value; }
  });
  const document = {
    activeElement: null,
    querySelector(selector) { if (!elements.has(selector)) elements.set(selector, makeElement()); return elements.get(selector); },
    addEventListener(type, callback) { handlers[type] = callback; },
    createElement() { return makeElement(); }
  };
  const sandbox = {
    document, localStorage: {
      getItem(key) { return storage.has(key) ? storage.get(key) : null; },
      setItem(key, value) { if (options.failPlanBackup && key.startsWith('tomeng_host_plan_migration_backup_')) throw new Error('quota'); storage.set(key, String(value)); },
      removeItem(key) { storage.delete(key); }
    },
    navigator: {}, location: { protocol: 'file:', reload() { this.reloaded = true; } },
    console, setTimeout, clearTimeout, Intl, Date: ClockDate,
    Blob: class { constructor(parts) { downloaded = parts.join(''); } },
    FileReader: class { readAsText(file) { this.result = file.text; this.onload(); } },
    URL: { createObjectURL() { return 'blob:test'; }, revokeObjectURL() {} },
    window: null, scrollTo() {}, confirm() { return true; }
  };
  sandbox.window = sandbox;
  sandbox.addEventListener = (type, callback) => { handlers[`window:${type}`] = callback; };
  vm.createContext(sandbox);
  sources.forEach(source => vm.runInContext(source, sandbox));
  function click(dataset) {
    const target = { dataset, tagName: 'BUTTON', closest() { return this; }, focus() {} };
    handlers.click?.({ target, stopPropagation() {}, preventDefault() {} });
  }
  return {
    app: sandbox.TomEngHost, storage, click, handlers, setDate(value) { today = value; },
    html() { return document.querySelector('#app').innerHTML; },
    modal() { return document.querySelector('#modal-root').innerHTML; },
    toast() { return document.querySelector('#toast').textContent; },
    exportText() { return downloaded; },
    importText(text) { handlers.change?.({ target: { id: 'import-file', files: [{ text }] } }); }
  };
}

const coreKeys = {
  tomeng_native_v3: JSON.stringify({ saved: ['p001'], marker: 'core-v3' }),
  tomeng_data_v2: JSON.stringify({ saved: ['p151'], marker: 'core-v2' })
};
const app = boot(coreKeys);
assert.equal(app.app.phraseCount, 1200);
assert.equal(app.app.storageKey, 'tomeng_host_store_v1');
assert.equal(app.app.getState().contentVersion, 'host-v1.0.0');
assert.equal(app.app.getState().activeSession.phase, 'learn');
assert.deepEqual([...app.app.getState().introducedPhraseIds], []);
assert.equal(app.storage.get('tomeng_native_v3'), coreKeys.tomeng_native_v3, 'TomEng core storage is untouched');
assert.equal(app.storage.get('tomeng_data_v2'), coreKeys.tomeng_data_v2, 'legacy core storage is untouched');

const ids = [...app.app.getState().activeSession.phraseIds];
assert.equal(ids.length, 5);
app.click({ action: 'continue' });
for (const id of ids) {
  app.click({ action: 'reveal' });
  app.click({ id, mark: 'ready' });
}
assert.equal(app.app.getState().activeSession.phase, 'quick', 'Learn advances to Recall after five phrases');
for (const id of ids) {
  app.click({ action: 'quick-reveal' });
  app.click({ id, newRating: 'good' });
}
assert.equal(app.app.getState().activeSession.phase, 'apply', 'five recalls lead to the scenario task');
app.click({ action: 'scenario-complete' });
assert.equal(app.app.getState().activeSession, null);
assert.deepEqual([...app.app.getState().introducedPhraseIds], ids, 'only completed new IDs enter unique progress');
assert.equal(app.app.getState().sessions.length, 1);
assert.equal(app.app.getState().sessions[0].newPhraseIds.length, 5);

const savedHost = app.storage.get('tomeng_host_store_v1');
const resumed = boot({ ...coreKeys, tomeng_host_store_v1: savedHost }, '2026-11-12');
assert.deepEqual([...resumed.app.getState().introducedPhraseIds], ids, 'refresh preserves Host progress');
assert.deepEqual([...resumed.app.getState().activeSession.reviewPhraseIds], ids, 'next session reviews the phrases from the actual prior session');
assert.equal(resumed.app.getState().activeSession.phase, 'review');
resumed.click({ action: 'continue' });
for (const id of ids) {
  resumed.click({ action: 'reveal' });
  resumed.click({ id, rating: 'good' });
}
assert.equal(resumed.app.getState().activeSession.phase, 'learn', 'new learning starts after the required review');

resumed.click({ action: 'backup' });
const backup = JSON.parse(resumed.exportText());
assert.equal(backup.app, 'TomEngHost');
assert.equal(backup.contentVersion, 'host-v1.0.0');
assert.match(backup.data.contentVersion, /^host-v1/);

const priorHostState = resumed.storage.get('tomeng_host_store_v1');
resumed.importText(JSON.stringify({ app: 'TomEng', schemaVersion: 7, contentVersion: 'native-v3.4', data: backup.data }));
assert.equal(resumed.storage.get('tomeng_host_store_v1'), priorHostState, 'core-branded backups are rejected without touching Host data');
assert.match(resumed.toast(), /không phải bản sao lưu TomEng Host/i);

const valid = boot();
valid.importText(JSON.stringify(backup));
assert.deepEqual([...valid.app.getState().introducedPhraseIds], ids, 'Host backup restores Host progress');
assert.equal(valid.app.getState().activeSession.phase, 'learn');
const previousHostBackup = { ...backup, contentVersion: 'host-v0.9.0', data: { ...backup.data, contentVersion: 'host-v0.9.0' } };
const previousHostRestore = boot();
previousHostRestore.importText(JSON.stringify(previousHostBackup));
assert.deepEqual([...previousHostRestore.app.getState().introducedPhraseIds], ids, 'prior Host backup version restores by stable phrase IDs');
assert.equal(previousHostRestore.app.getState().contentVersion, 'host-v1.0.0');

const oldHostData = { schemaVersion: 7, contentVersion: 'host-v0.9.0', saved: ['p011'], learned: ['p012'], introducedPhraseIds: ['p012'], reviews: { p012: { dueDate: '2026-11-13', interval: 2, repetitions: 1 } }, completions: {}, sessions: [], activityDates: [], activeSession: null };
const migratedHost = boot({ tomeng_host_store_v1: JSON.stringify(oldHostData) });
assert.equal(migratedHost.app.getState().contentVersion, 'host-v1.0.0');
assert.deepEqual([...migratedHost.app.getState().saved], ['p011']);
assert.deepEqual([...migratedHost.app.getState().introducedPhraseIds], ['p012']);
assert.equal(migratedHost.app.getState().reviews.p012.interval, 2);
assert.equal(migratedHost.app.getState().migration.contentPlanUpdatedFrom, 'host-v0.9.0');
assert.ok(migratedHost.storage.has(migratedHost.app.getState().migration.planMigrationBackupKey), 'Host catalog migration keeps a verified rollback snapshot');

const oldHostRaw = JSON.stringify(oldHostData);
const blockedHostMigration = boot({ tomeng_host_store_v1: oldHostRaw }, '2026-11-11', { failPlanBackup: true });
assert.equal(blockedHostMigration.storage.get('tomeng_host_store_v1'), oldHostRaw, 'migration cannot overwrite Host progress if backup creation fails');
assert.match(blockedHostMigration.html(), /Chưa thể cập nhật sổ tay/);

const lib = boot();
lib.click({ page:'library' });
let libHtml=lib.html();
assert.match(libHtml,/12 chuyên mục/,'Host Library reports all twelve sections');
assert.equal((libHtml.match(/class="category-tab /g)||[]).length,12,'all twelve main categories rendered as visible choices');
assert.doesNotMatch(libHtml,/data-filter="all"/,'main category All tab removed');
assert.match(libHtml,/class="category-tab selected" data-filter="rooms"/,'Library defaults to first real category');
assert.equal((libHtml.match(/class="subcategory-group"/g)||[]).length,1,'only the chosen category child group is shown');
assert.ok(libHtml.indexOf('class="library-results-toolbar"')>libHtml.indexOf('class="category-filter"'),'view-mode control belongs to card results');
assert.ok(libHtml.indexOf('class="view-switch"')>libHtml.indexOf('class="library-results-toolbar"'),'segmented display selector renders with cards');
assert.match(libHtml,/class="import-short">Nhập<\/span>/,'mobile import has compact caption');
assert.match(libHtml,/data-action="export"/,'backup remains available');
lib.click({ filter:'booking' });
libHtml=lib.html();
assert.match(libHtml,/class="category-tab selected" data-filter="booking"/,'changing category selects Booking');
assert.equal((libHtml.match(/class="subcategory-chip /g)||[]).length,3,'Booking shows exactly three subgroup options');
lib.click({ viewMode:'patterns' });
assert.match(lib.html(),/data-view-mode="patterns" aria-pressed="true"/,'view switch toggles the card presentation');
lib.handlers.input({target:{id:'global-search',value:'air conditioner'}});
lib.click({viewMode:'phrases'});
libHtml=lib.html();
assert.match(libHtml,/Kết quả tìm kiếm/,'search returns results across categories');
assert.match(libHtml,/air conditioner/i,'search reaches Maintenance while previously in Booking');
assert.doesNotMatch(libHtml,/class="subcategory-panel"/,'search does not display the full hierarchy of subgroups');
lib.handlers.input({target:{id:'global-search',value:''}});
lib.click({viewMode:'phrases'});
assert.match(lib.html(),/class="category-tab selected" data-filter="rooms"/,'clear search restores first real category');
const responsiveCss=fs.readFileSync(path.join(root,'style.css'),'utf8');
assert.match(responsiveCss,/\.category-grid,\.more-grid,\.grammar-grid,\.phrase-grid,\.pattern-grid,\.progress-cards,\.quick-stats/,'mobile content grids consistently use one card per row');
assert.match(responsiveCss,/\.topbar \.search input\{min-width:0;flex:1;width:100%;font-size:16px/,'iPhone search input avoids zoom and fills row');

console.log('PASS: isolated storage, learning/recall/application flow, persistence, next-day review, Host-only backup import and rollback-safe Host catalog migration');
