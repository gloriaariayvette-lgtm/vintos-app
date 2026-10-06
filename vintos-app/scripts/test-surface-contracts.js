#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const page = fs.readFileSync(path.join(__dirname, '..', 'src', 'index.html'), 'utf8');
const watch = fs.readFileSync(path.join(__dirname, '..', 'ios', 'VintosWatch', 'ContentView.swift'), 'utf8');
const moment = fs.readFileSync(path.join(__dirname, '..', 'ios', 'VintosWatch', 'SharedMoment.swift'), 'utf8');

const checks = [
  ['private journal is not exposed as an app tab', !page.includes('data-tab="journal"') && !page.includes('id="pane-journal"')],
  ['journal loader is absent from the shipped surface', !page.includes('loadJournal()') && !page.includes('_journalToggle')],
  ['thread reads bypass WebView and proxy caches', /\/api\/threads\?_=`?\$\{nonce\}/.test(page) && page.includes("cache:'no-store'") && page.includes("'Cache-Control':'no-cache'")],
  ['thread API failures do not render as an empty ledger', page.includes("if (!tr.success) throw new Error")],
  ['landings remain available', page.includes('data-tab="landings"') && page.includes('async function loadLandings()')],
  ['Lab shows intermediate activity on its 15-second refresh', page.includes('activity?limit=12') && page.includes('LIVE ACTIVITY · REFRESHES EVERY 15 SECONDS') && page.includes('function _labActivityRow')],
  ['avatar chat polling preserves the reader position', page.includes('function _avChatAtBottom') && page.includes('if(JSON.stringify(incoming)===JSON.stringify(_avChatHistory.slice(-60))) return;') && page.includes('_avLogMsg(\'user\',text,true)')],
  ['Watch shows at most the latest five Landings', watch.includes('Array(fresh.prefix(5))')],
  ['Watch explains that replies use its private inbox', watch.includes('Saved in his private Watch inbox.') && !watch.includes('dictate or Scribble')],
  ['Watch has a visible ember presence', watch.includes('struct VintosOrbView') && watch.includes('Vintos, a warm ember')],
  ['shared moments record start and end outside Avatar chat', moment.includes('moment("started")') && moment.includes('moment("ended")') && moment.includes('never enters Avatar chat')],
];

let failed = 0;
for (const [name, ok] of checks) {
  console.log(`${ok ? 'PASS' : 'FAIL'} ${name}`);
  if (!ok) failed += 1;
}
console.log(`\n${checks.length} checks, ${failed} failed`);
process.exit(failed ? 1 : 0);
