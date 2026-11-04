#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../src/index.html'), 'utf8');
function fn(name) {
  const start = html.search(new RegExp('(?:async )?function ' + name + '\\('));
  assert(start >= 0, name + ' exists');
  return html.slice(start, html.indexOf('\n}\n', start) + 3);
}
const elements = new Map();
function element() {
  return { id: '', textContent: '', style: {}, children: [], scrollHeight: 20, clientHeight: 20, scrollTop: 0,
    get firstChild() { return this.children[0]; },
    appendChild(child) { this.children.push(child); child.parentNode=this; if(child.id)elements.set(child.id,child); },
    removeChild(child) { this.children.splice(this.children.indexOf(child),1); }
  };
}
for(const id of ['avatar-overlay', 'av-chat-message', 'avatar-reason']) { const e=element();e.id=id;elements.set(id,e); }
elements.get('avatar-reason').textContent='His private state explanation';
let failPlayback=false, played=0;
class AudioFake {
  constructor(){Object.assign(this,element());}
  play(){played++;return failPlayback ? Promise.reject(new Error('offline playback fixture')) : Promise.resolve();}
}
const context=vm.createContext({
  document:{hidden:false,getElementById:id=>elements.get(id),createElement:()=>element()},
  Audio:AudioFake, API:'https://offline.invalid',CONFIG:{secret:'test-only'},
  _avOverlayGeneration:1,_avLastCmdTs:0,_avChatHistory:[],_avAudioEl:null,
  _avParseReply:raw=>({text:raw,gestures:[],holds:[],spawns:[]}),_avSaveHistory:()=>{},
  VintosUI:{request:async url=>({json:async()=>url.endsWith('/api/command-bubble') ?
    {ts:Date.now()/1000,type:'command',text:'His command text'} : {audio_url:'offline-audio-fixture'}})}
});
vm.runInContext(['_avChatAtBottom','_avLogMsg','_avCheckCommandBubble','_avSpeakAndShow'].map(fn).join('\n'),context);
(async()=>{
  await context._avSpeakAndShow('His normal spoken reply');
  await new Promise(setImmediate);
  assert.equal(elements.get('av-chat-message').children[0].textContent,'His normal spoken reply');
  assert.equal(elements.has('av-bubble'),false);
  const command=elements.get('av-cmd-bubble');
  assert.equal(command.textContent,'HIS COMMAND — His command text');
  assert.match(command.style.cssText,/right:3%/);
  assert.equal(played,1);
  failPlayback=true;
  await context._avSpeakAndShow('His second reply');
  await new Promise(setImmediate);
  assert.equal(context._avAudioEl.controls,true);
  assert.equal(elements.get('av-chat-message').children.at(-1).textContent,'Playback failed. Use the audio controls to retry.');
  assert.equal(elements.has('av-bubble'),false);
  assert(!html.includes('_avShowBubble')&&!html.includes('_avPollReason'));
  let scripts=0;
  for(const [,attrs,body] of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    if(/\bsrc=|type\s*=\s*["']module["']/i.test(attrs)||!body.trim())continue;
    new vm.Script(body);scripts++;
  }
  console.log('PASS spoken replies use normal chat text; no left thought overlay; right command box and audio preserved; playback failure stays visible; '+scripts+' inline scripts parse');
})().catch(error=>{console.error(error);process.exitCode=1;});
