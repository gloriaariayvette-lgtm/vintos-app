const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const html=fs.readFileSync(__dirname+'/../src/index.html','utf8');
const start=html.indexOf('var _avStage = {'),end=html.indexOf('\nasync function _avShowLive',start);
assert(end>start);let canvas={style:{display:'block'}},hide=0;
const ctx=vm.createContext({document:{getElementById:()=>canvas},console:{log(){}},setTimeout:()=>{},URL:{revokeObjectURL(){}},VintosUI:{},API:'',CONFIG:{secret:'fixture'}});
vm.runInContext(html.slice(start,end),ctx);const stage=ctx._avStage;
stage._hideCanvas=()=>{hide++;canvas.style.display='none';};
function layer(reject=false){return {wrap:{style:{opacity:'0'}},fg:{readyState:0,play:async()=>{if(reject)throw Error('blocked');},pause(){}},bg:{play:async()=>{},pause(){}}};}
(async()=>{
 let L=layer(true);stage.layers=[null,L];stage._el=()=>L;stage.front=0;
 await stage._show('fixture',{muted:true,loop:true,lightweight:false});assert.equal(hide,0,'must not hide before playback');await L.fg.oncanplay();assert.equal(hide,0);assert.equal(canvas.style.display,'block');assert.equal(stage.front,0,'failed layer must not replace current layer');
 L=layer();stage.layers=[null,L];stage._el=()=>L;await stage._show('fixture2',{muted:true,loop:true});assert.equal(hide,0);await L.fg.oncanplay();assert.equal(hide,1);assert.equal(L.wrap.style.opacity,'1');
 const load=html.slice(html.indexOf('  load: async function(){',start),html.indexOf('  _show: async function',start));assert(!load.includes('_hideCanvas()'),'manifest alone must not hide fallback');
 console.log('PASS failed playback keeps fallback; successful playback reveals frame; failed layer rolls back; manifest never blanks canvas; no network');
})().catch(e=>{console.error(e);process.exitCode=1;});
