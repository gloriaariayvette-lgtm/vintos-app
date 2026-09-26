#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const page = fs.readFileSync(path.join(__dirname, '..', 'src', 'index.html'), 'utf8');

const checks = [
  ['private journal is not exposed as an app tab', !page.includes('data-tab="journal"') && !page.includes('id="pane-journal"')],
  ['journal loader is absent from the shipped surface', !page.includes('loadJournal()') && !page.includes('_journalToggle')],
  ['thread reads bypass WebView and proxy caches', /\/api\/threads\?_=`?\$\{nonce\}/.test(page) && page.includes("cache:'no-store'") && page.includes("'Cache-Control':'no-cache'")],
  ['thread API failures do not render as an empty ledger', page.includes("if (!tr.success) throw new Error")],
  ['landings remain available', page.includes('data-tab="landings"') && page.includes('async function loadLandings()')],
];

let failed = 0;
for (const [name, ok] of checks) {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`);
  if (!ok) failed += 1;
}
console.log(`\n${checks.length} checks, ${failed} failed`);
process.exit(failed ? 1 : 0);
