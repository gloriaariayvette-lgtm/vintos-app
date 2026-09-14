const test = require('node:test');
const assert = require('node:assert/strict');
const {create} = require('../src/client_lifecycle.js');
test('HTTP and application failures reject and surface an error', async()=>{
  const messages=[];
  for(const response of [new Response('{}',{status:503}),new Response('{"success":false}',{headers:{'content-type':'application/json'}})]){
    const ui=create({fetch:async()=>response,notify:m=>messages.push(m)});
    await assert.rejects(ui.request('/fixture',{method:'POST'}));
  }
  assert.equal(messages.length,2);
});
test('one pending turn, invalidation rejects old callbacks and finish cannot release a newer turn',()=>{
  const ui=create({fetch:()=>{throw Error('no network')}});
  const a=ui.begin('text');assert.ok(a);assert.equal(ui.begin('voice'),null);
  ui.invalidate();assert.equal(ui.current(a),false);ui.finish(a);
  const b=ui.begin('voice');ui.finish(a);assert.equal(ui.current(b),true);
});
test('acknowledgement clears only the exact submitted draft',()=>{
  const ui=create({fetch:()=>{throw Error('no network')}});let events=0;
  const input={value:'new draft',dispatchEvent:()=>events++};
  ui.ack(input,'old draft');assert.equal(input.value,'new draft');assert.equal(events,0);
  ui.ack(input,'new draft');assert.equal(input.value,'');assert.equal(events,1);
});
test('text encoding preserves zero and quotes as text',()=>{
  const ui=create({fetch:()=>{throw Error('no network')}});
  assert.equal(ui.text(0),'0');assert.equal(ui.text('<img onerror="x">'), '&lt;img onerror=&quot;x&quot;&gt;');
});
test('auxiliary media carries no conversational turn authority',async()=>{
  const seen=[];
  const ui=create({fetch:async(url,init)=>{seen.push([url,new Headers(init.headers||{})]);return new Response('{}');}});
  const turn=ui.begin('avatar');
  await ui.request('/reply');
  await ui.auxiliary('/stage',{},100);
  assert.equal(seen[0][1].get('X-Client-Turn-Id'),turn.id);
  assert.equal(seen[1][1].get('X-Client-Turn-Id'),null);
  ui.finish(turn);
});
test('a slow auxiliary clip times out without holding the controls',async()=>{
  const ui=create({fetch:async(_url,init)=>await new Promise((resolve,reject)=>{
    init.signal.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')),{once:true});
  })});
  const turn=ui.begin('avatar');
  const bubble={text:'his reply'};             // reply has already rendered
  ui.finish(turn);                             // exact ordering used by avSendChat
  const delayed=ui.auxiliary('/slow-stage',{},25).catch(e=>e.name);
  const next=ui.begin('button');               // controls remain live immediately
  assert.equal(bubble.text,'his reply');
  assert.ok(next);
  assert.equal(await delayed,'AbortError');
  ui.finish(next);
});
