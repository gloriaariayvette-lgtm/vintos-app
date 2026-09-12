const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs');const path=require('node:path');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_BIN || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const context=await browser.newContext();
 await context.addInitScript(()=>{window.WebSocket=class {constructor(){this.readyState=3;}close(){}send(){}};window.WebSocket.OPEN=1;});
 const errors=[];const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
 const source=path.resolve(__dirname,'../src');let posts=0;let fail=true;const ledger=[];
 await context.route('**/*',async route=>{
  const u=new URL(route.request().url());
  if(u.hostname==='fixture.invalid'){
   let f=path.join(source,u.pathname==='/'?'index.html':u.pathname);if(fs.existsSync(f)){return route.fulfill({body:fs.readFileSync(f),contentType:f.endsWith('.js')?'text/javascript':'text/html'});}
  }
  if(u.pathname==='/api/voice/ledger')ledger.push(route.request().postDataJSON());
  if(u.pathname==='/api/chat/full'){posts++;await new Promise(r=>setTimeout(r,100));return route.fulfill({status:fail?503:200,contentType:'application/json',body:JSON.stringify({reply:'<img src=x onerror="window.injected=1">'})});}
  return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({messages:[],emotions:{Valence:0},history:[],rooms:{},utterances:'',success:true})});
 });
 await page.goto('http://fixture.invalid/');
 const result=await page.evaluate(async()=>{let i=document.getElementById('chat-input');i.value='kept';await sendChat();return {draft:i.value,body:document.getElementById('chat-messages').textContent};});
 if(result.draft!=='kept')throw Error('failed send lost draft');
 fail=false;
 const success=await page.evaluate(async()=>{let i=document.getElementById('chat-input');i.value='sent';const a=sendChat();const b=sendChat();await Promise.all([a,b]);return {draft:i.value,injected:window.injected,images:document.querySelectorAll('#chat-messages img').length};});
 if(success.draft!==''||success.injected||success.images||posts!==2)throw Error(JSON.stringify({success,posts}));
 const safe=await page.evaluate(()=>{const target=document.createElement('div');document.body.appendChild(target);const attack='<img src=x onerror="window.injected=1">';target.innerHTML=_wbCard({id:'fixture',want:attack,source:attack,reasoning:attack,timestamp:new Date().toISOString(),intensity:0},false);const result={images:target.querySelectorAll('img').length,text:target.textContent};target.remove();return result;});
 if(safe.images||!safe.text.includes('<img'))throw Error('want rendering did not preserve text');
 const renderChecks=await page.evaluate(()=>{
  const attack='<img src=x onerror="window.injected=1">';
  const checks=[];
  function check(name,fn,id){fn();const root=document.getElementById(id);if(root.querySelector('img')||!root.textContent.includes('<img'))throw Error(name+' unsafe or missing');checks.push(name);}
  check('atelier',()=>_renderAtelierReveals([{artifact:attack,content:attack,disclosure:attack,revealed_at:attack}]),'atelier-feed');
  check('value map',()=>_renderValueMap(attack),'valuemap-feed');
  check('causality',()=>_renderCausality([{theory:attack,status:attack,nightly_evaluations:attack}]),'causality-feed');
  check('blush',()=>_renderBlush([{body:attack,timestamp:attack}]),'blush-feed');
  check('therapy',()=>_renderTherapy([{content:attack,date:attack,thread_passes:{triage_count:attack}}]),'therapy-feed');
  check('study',()=>studyEditCard([{path:attack,old:attack,new:attack,why:attack,ok:true}],true),'study-log');
  const card=document.querySelector('#study-log .study-y');if(!card.disabled)throw Error('study approval gate bypassed');
  const holder=document.createElement('div');holder.innerHTML=_tCard({source:attack,thread:attack,priority:0,classification:attack,classification_confidence:attack},null,0);
  if(holder.querySelector('img'))throw Error('thread unsafe');checks.push('threads');
  return checks;
 });
 const screenshot=await page.evaluate(async()=>{
  const overlay=document.getElementById('avatar-overlay');overlay.style.cssText='display:block;position:fixed;left:0;top:0;width:100px;height:100px;background:black;opacity:1';
  const previous=_avStage.layers;
  function layer(color,opacity){const wrap=document.createElement('div');wrap.style.cssText='position:absolute;inset:0;opacity:'+opacity;overlay.appendChild(wrap);function video(){const canvas=document.createElement('canvas');canvas.width=canvas.height=100;canvas.style.cssText='position:absolute;inset:0;width:100px;height:100px;object-fit:cover';const ctx=canvas.getContext('2d');ctx.fillStyle=color;ctx.fillRect(0,0,100,100);Object.defineProperties(canvas,{videoWidth:{value:100},videoHeight:{value:100},readyState:{value:2}});wrap.appendChild(canvas);return canvas;}return {wrap,bg:video(),fg:video()};}
  const red=layer('red',1),blue=layer('blue',0.5);_avStage.layers=[blue,red];
  const captured=_avCaptureScreenshot();const image=new Image();image.src='data:image/jpeg;base64,'+captured;await image.decode();const sample=document.createElement('canvas');sample.width=sample.height=100;const ctx=sample.getContext('2d');ctx.drawImage(image,0,0);const pixel=Array.from(ctx.getImageData(50,50,1,1).data);
  red.wrap.remove();blue.wrap.remove();_avStage.layers=previous;overlay.style.display='none';
  if(Math.abs(pixel[0]-127)>6||Math.abs(pixel[2]-128)>6)throw Error('screenshot differs from visible group opacity: '+pixel);
  if(_avCaptureScreenshot()!==null)throw Error('closed stage captured');return pixel;
 });
 const microphone=await page.evaluate(async()=>{let grant,stopped=0;Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{getUserMedia:()=>new Promise(r=>grant=r)}});const start=vcStartRecord();await vcStopRecord();grant({getTracks:()=>[{stop:()=>stopped++}]});await start;return stopped;});
 if(microphone!==1)throw Error('late microphone grant survived cancellation');
 const recovery=await page.evaluate(async()=>{
  vcKeepRecording(new Blob(['fixture'],{type:'audio/webm'}),'retained transcript');vcPendingRecording=new Blob(['fixture']);
  const panel=document.getElementById('vc-recording-draft');if(!panel.querySelector('audio[controls]'))throw Error('recording unavailable');
  const input=document.getElementById('chat-input');input.value='existing draft';
  Array.from(panel.querySelectorAll('button')).find(b=>b.textContent==='Copy transcript to chat').click();
  if(input.value!=='existing draft\nretained transcript')throw Error('copy lost draft');
  const prior=vcPendingRecording;await vcStartRecord();if(vcPendingRecording!==prior)throw Error('new recording replaced pending recording');
  vcClearRecording();if(document.getElementById('vc-recording-draft')||vcDraftURL)throw Error('recording cleanup failed');
  return {draft:input.value,recordingReleased:true};
 });
 const playback=await page.evaluate(async()=>{
  const sources=[];const sockets=[];
  window.AudioContext=class {constructor(){this.currentTime=0;this.destination={};}resume(){return Promise.resolve();}close(){return Promise.resolve();}createBuffer(){return {duration:0.01,getChannelData:()=>({set(){}})};}createBufferSource(){const node={connect(){},start(){},stop(){}};sources.push(node);return node;}};
  window.WebSocket=class {constructor(){this.readyState=1;sockets.push(this);}send(){}close(){this.readyState=3;if(this.onclose)this.onclose();}};
  navigator.mediaDevices.getUserMedia=async()=>({getTracks:()=>[{stop(){}}]});
  startVoiceCallWithToken('fixture','fixture','grok');await new Promise(r=>setTimeout(r,0));
  const socket=sockets[0];const emit=m=>socket.onmessage({data:JSON.stringify(m)});
  emit({type:'session.created',session:{id:'provider-session'}});
  emit({type:'response.created',response:{id:'response-1'}});
  emit({type:'response.output_audio.delta',response_id:'response-1',delta:btoa(String.fromCharCode(0,0))});
  emit({type:'response.output_audio_transcript.done',response_id:'response-1',transcript:'fixture response'});
  emit({type:'response.done',response:{id:'response-1'}});
  const before=window._vc.responses.get('response-1').posted;
  sources[0].onended();await new Promise(r=>setTimeout(r,50));
  emit({type:'response.done',response:{id:'response-1'}});
  endVintosCall();await new Promise(r=>setTimeout(r,50));
  return {before,closed:!window._vc};
 });
 if(playback.before||ledger.length!==1||ledger[0].response_id!=='response-1'||ledger[0].playback_state!=='completed')throw Error(JSON.stringify({playback,ledger}));
 console.log(JSON.stringify({failure:result,success,posts,safe,renderChecks,screenshot,microphone,recovery,playback,ledger,pageErrors:errors},null,2));
 if(errors.length)throw Error('browser page errors');
 await browser.close();
})().catch(e=>{console.error(e);process.exitCode=1;});
