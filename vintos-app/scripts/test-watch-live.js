#!/usr/bin/env node
// Offline tests: execute the shipped Tune handlers with a stub transport/native bridge.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(path.join(__dirname,'../src/index.html'),'utf8');
const code=html.slice(html.indexOf('let _watchLiveRefresh;'),html.indexOf('let _agentsDurationRestored'));
const elements={'watch-live-duration':{value:'60'},'watch-live-status':{textContent:''}};
let state={on:true,minutes_left:59},fail=false,nativeFail=false,opens=0,calls=[];
const context=vm.createContext({document:{getElementById:id=>elements[id]},CONFIG:{secret:'offline-test'},API:'https://offline.invalid',
 setTimeout:()=>1,clearTimeout:()=>{},window:{Capacitor:{Plugins:{VintosHealth:{startWatchApp:async()=>{opens++;if(nativeFail)throw Error('unreachable');}}}}},
 VintosUI:{request:async(url,options)=>{calls.push({url,...options});return {ok:!fail,json:async()=>state};}}});
vm.runInContext(code,context);
(async()=>{
 await context.setWatchLive();assert.equal(opens,1);assert.deepEqual(JSON.parse(calls[0].body),{minutes:60});assert.equal(calls[0].headers['X-Vintos-Secret'],'offline-test');assert.equal(elements['watch-live-status'].textContent,'on, 59 min left');
 elements['watch-live-duration'].value='0';state={on:false};await context.setWatchLive();assert.equal(opens,1);assert.deepEqual(JSON.parse(calls.at(-1).body),{minutes:0});assert.equal(elements['watch-live-status'].textContent,'off');
 state={on:true,minutes_left:42};await context.loadWatchLive();assert.equal(calls.at(-1).method,undefined);assert.equal(elements['watch-live-status'].textContent,'on, 42 min left');
 fail=true;await context.setWatchLive();assert.equal(opens,1);assert.match(elements['watch-live-status'].textContent,/could not change/);assert.equal(elements['watch-live-duration'].disabled,false);
 fail=false;nativeFail=true;await context.setWatchLive();assert.match(elements['watch-live-status'].textContent,/Watch could not open: unreachable/);
 context.window.Capacitor=undefined;await context.setWatchLive();assert.match(elements['watch-live-status'].textContent,/open Vintos on your Watch/);
 console.log('PASS live-heart-rate POST/GET, headers, duration, Off, server failure, native failure and browser fallback');
})().catch(error=>{console.error(error);process.exitCode=1;});
