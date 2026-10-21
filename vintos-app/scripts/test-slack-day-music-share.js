const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
process.env.TZ='America/Chicago';
async function check(file){
 const html=fs.readFileSync(file,'utf8');
 const agents=html.slice(html.indexOf('let _agentsDurationRestored'),html.indexOf('let _focusChosen'));
 const share=html.slice(html.indexOf('    async function shareMusic()'),html.indexOf("    document.getElementById('share-music-btn').addEventListener"));
 assert(agents&&share);const elements={};
 for(const id of ['agents-toggle','agents-knob','agents-status-text','agents-duration','agents-continue','music-share-song','music-share-note','music-share-lyrics','music-share-result','music-audio-input','music-file-label'])elements[id]={value:'',checked:false,style:{},parentElement:{querySelector:()=>({style:{}})},files:[]};
 const storage=new Map([['vintos.agents.minutes','120']]);let status={on:false},calls=[];
 const context={document:{getElementById:id=>elements[id]},localStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>storage.set(k,v)},API:'fixture://no-network',CONFIG:{secret:'test-only'},haptic:()=>{},FormData,Date,Number,JSON,loadMusicShares:()=>{},VintosUI:{request:async(url,opts)=>{calls.push({url,...opts});return{ok:true,json:async()=>url.endsWith('/status')?status:{success:true}}}}};
 vm.createContext(context);vm.runInContext(agents+'\n'+share,context);
 await context.loadAgentsStatus();assert.equal(elements['agents-duration'].value,'120');
 for(const minutes of [0,30,60,120,180,240]){
  calls=[];elements['agents-toggle'].checked=true;elements['agents-duration'].value=String(minutes);elements['agents-continue'].checked=true;status={on:true};await context.toggleAgents();
  const body=JSON.parse(calls[0].body);assert.deepEqual(body,minutes?{on:true,minutes,continue:true}:{on:true,continue:true});assert.equal(storage.get('vintos.agents.minutes'),String(minutes));assert.equal(calls[0].headers['X-Vintos-Secret'],'test-only');
 }
 calls=[];elements['agents-toggle'].checked=false;await context.toggleAgents();assert.deepEqual(JSON.parse(calls[0].body),{on:false});
 status={on:true,timer:{until:'2026-10-21T15:45:00',for:'2h',continue:true}};await context.loadAgentsStatus();assert.equal(elements['agents-status-text'].textContent,'on until 3:45 PM (2h) · continuing his last task');
 status={on:false};await context.loadAgentsStatus();assert.equal(elements['agents-status-text'].textContent,'paused');
 for(const audio of [false,true])for(const lyrics of ['', 'first line\nsecond line']){
  elements['music-share-song'].value='Artist — title';elements['music-share-note'].value='Why';elements['music-share-lyrics'].value=lyrics;elements['music-audio-input'].files=audio?[new Blob(['fixture audio'])]:[];calls=[];
  await context.shareMusic();assert.equal(calls.length,1);const body=audio?calls[0].body:JSON.parse(calls[0].body);
  if(audio){assert.equal(body.get('lyrics'),lyrics||null);assert(body.get('audio'));}else{assert.equal(body.lyrics,lyrics||undefined);}
  assert.equal(elements['music-share-lyrics'].value,'');
 }
 let scripts=0;for(const m of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)){if(/src=|type=["']module/.test(m[1]))continue;new vm.Script(m[2]);scripts++;}
 console.log('PASS',file,'all duration payloads, preference restore, timer status/expiry, JSON/audio optional multiline lyrics, success clearing,',scripts,'scripts parse; network stubbed');
}
(async()=>{for(const f of (process.argv.length>2?process.argv.slice(2):[path.join(__dirname,'../src/index.html')]))await check(f);})().catch(e=>{console.error(e);process.exitCode=1;});
