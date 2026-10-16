const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
for(const file of process.argv.slice(2).length?process.argv.slice(2):[path.join(__dirname,'../src/index.html')]){
 const html=fs.readFileSync(file,'utf8');let writes=0,now=1000;
 class El{
  constructor(){this.style={};this.attrs={};this.listeners={};this.offsetHeight=300;this.captured=null;}
  setAttribute(k,v){this.attrs[k]=v;}getAttribute(k){return this.attrs[k];}
  addEventListener(k,f){this.listeners[k]=f;}
  setPointerCapture(id){this.captured=id;}hasPointerCapture(id){return this.captured===id;}releasePointerCapture(){this.captured=null;}
 }
 const nodes=Object.fromEntries(['av-drawer','av-drawer-handle','av-drawer-body','av-drawer-chev'].map(x=>[x,new El()]));
 const ctx=vm.createContext({document:{getElementById:id=>nodes[id]},window:{innerHeight:800,innerWidth:400,addEventListener(){}},localStorage:{getItem:()=>null,setItem(){writes++;}},Date:{now:()=>now},Math,console});
 let start=html.indexOf('var _avDrawerDock ='),end=html.indexOf("if (document.readyState === 'loading')",start);assert(start>0&&end>start);vm.runInContext(html.slice(start,end)+'\n_avDrawerInit();',ctx);
 const h=nodes['av-drawer-handle'],d=nodes['av-drawer'];
 function event(type,x=380,y=500,id=1){const e={type,clientX:x,clientY:y,pointerId:id,pointerType:'touch',isPrimary:true,button:0,preventDefault(){}};h.listeners[type](e);}
 function open(){return d.getAttribute('data-open')==='1';}
 assert.match(html,/id="av-drawer-handle"[^>]*min-width:48px/);assert.match(d.style.transform,/48px/);assert.equal(h.attrs['aria-expanded'],'false');
 event('pointerdown');event('pointermove',389,507);event('pointerup',389,507);assert(open(),'normal finger jitter must still tap open');event('click');assert(open(),'synthetic click must not double-toggle');
 event('pointerdown');event('pointercancel');assert(open(),'cancel must never toggle');event('pointerdown');event('lostpointercapture');assert(open(),'lost capture must never toggle');
 event('pointerdown');const before=writes;event('pointermove',380,450);assert.equal(writes,before,'no storage writes during drag');event('pointermove',380,10,2);assert.equal(vm.runInContext('_avDrawerDock.bottom',ctx),160,'ignore other fingers');event('pointerup',380,450);assert(open(),'drag must not toggle');assert(writes>before,'save final dock');
 event('pointerdown');event('pointermove',195,400);assert.equal(vm.runInContext('_avDrawerDock.side',ctx),'right','centre dead zone prevents flipping');event('pointermove',150,400);assert.equal(vm.runInContext('_avDrawerDock.side',ctx),'left');event('pointerup',150,400);assert.equal(d.style.left,'calc(6px + env(safe-area-inset-left, 0px))');
 now+=1000;event('click');assert(!open(),'keyboard/VoiceOver click closes');event('pointerdown',20,400);event('pointerup',20,400);assert(open(),'tap opens from left edge');
 event('pointerdown',20,400);event('pointermove',20,-1000);event('pointerup',20,-1000);assert.equal(vm.runInContext('_avDrawerDock.bottom',ctx),484,'clamp actual panel to viewport');
 assert.match(html,/min-height:44px;touch-action:manipulation;padding:8px 12px/);
 console.log('PASS',file,'48px hit target, jitter taps, no double toggle, cancel, capture loss, drag persistence, second finger, both edges, keyboard, viewport clamp; no network');
}
