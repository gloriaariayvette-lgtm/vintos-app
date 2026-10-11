#!/usr/bin/env node
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const page=fs.readFileSync(process.argv[2]||path.join(__dirname,'../src/index.html'),'utf8');
assert(page.includes('#lab-grid { min-width: 0; grid-template-columns: minmax(0, 1fr); }'));
assert(page.includes('.lab-activity-text { flex: 1; min-width: 0; overflow-wrap: anywhere; }'));
assert(page.includes('<div id="lab-structures"></div>'));
const load=page.slice(page.indexOf('async function loadLab()'),page.indexOf('async function loadParams()'));
assert(!load.includes('_labStopStructure()'),'activity refresh must not destroy the viewer');
assert(load.includes("_labLoadStructures(document.getElementById('lab-structures'))"));
let renderers=0,renders=0,frame=0,active=true,disposals=0,reads=0;
const canvas={clientWidth:358,setPointerCapture(){}};const note={};
class Geometry{setAttribute(){}dispose(){disposals++;}}
class Material{dispose(){disposals++;}}
class Group{constructor(){this.rotation={x:0,y:0};this.children=[];}add(o){this.children.push(o);}}
class Scene extends Group{traverse(fn){function walk(x){fn(x);for(const c of x.children||[])walk(c);}walk(this);}}
class Renderer{constructor(){renderers++;}setPixelRatio(){}setSize(w,h){assert(w<=358);assert.equal(h,250);}setClearColor(){}render(){renders++;}dispose(){}}
class Camera{constructor(){this.position={set(){}};}updateProjectionMatrix(){}}
class Colour{constructor(){this.r=this.g=this.b=.5;}}
class Vector{constructor(x,y,z){this.x=x;this.y=y;this.z=z;}}
class Object3D{constructor(geometry,material){this.geometry=geometry;this.material=material;}}
const THREE={WebGLRenderer:Renderer,Scene,PerspectiveCamera:Camera,Group,Color:Colour,Vector3:Vector,BufferGeometry:Geometry,BufferAttribute:class{},Float32BufferAttribute:class{},Points:Object3D,PointsMaterial:Material,LineSegments:Object3D,LineBasicMaterial:Material};
const host={isConnected:true,closest:()=>true,querySelector:s=>s==='#lab-structure-canvas'?canvas:null};
const context=vm.createContext({console,THREE,window:{THREE,devicePixelRatio:3},document:{getElementById:id=>id==='lab-structure-canvas'?canvas:id==='lab-structure-note'?note:id==='pane-lab'?{classList:{contains:()=>active}}:null},requestAnimationFrame:()=>++frame,cancelAnimationFrame(){},_esc:s=>String(s),API:'http://test.invalid',CONFIG:{secret:'test-only'},fetch:()=>{reads++;throw Error('network forbidden');}});
vm.runInContext(page.slice(page.indexOf('let _labStructureView = null'),page.indexOf('function _labReviewCard')),context);
vm.runInContext(page.slice(page.indexOf('async function _labLoadStructures'),page.indexOf('function _labSetRefresh')),context);
const payload={ok:true,name:'source.pdb',atom_count:3,atoms:[{name:'CA',chain:'A',element:'C',x:0,y:0,z:0},{name:'CA',chain:'A',element:'C',x:1,y:2,z:3},{name:'O',chain:'A',element:'O',x:3,y:1,z:2}]};
context.payload=payload;vm.runInContext('_labDrawStructure(payload)',context);assert.equal(renderers,1);assert(renders>0);assert(note.textContent.includes('3 atoms'));
canvas.onpointerdown({clientX:0,clientY:0,pointerId:1});canvas.onpointermove({clientX:30,clientY:10});canvas.onpointerup();assert(vm.runInContext('_labStructureView.scene.children[0].rotation.x',context)>0);
context.host=host;context._labGet=async()=>({structures:[{artifact_id:'one',name:'source.pdb'}],renders:[]});
(async()=>{
 for(let i=0;i<30;i++)await vm.runInContext('_labLoadStructures(host)',context);
 assert.equal(renderers,1);assert.equal(reads,0,'refresh must keep the existing canvas without sending real requests');
 active=false;vm.runInContext('_labPauseStructure()',context);assert.equal(vm.runInContext('_labStructureView.frame',context),0);
 active=true;vm.runInContext('_labResumeStructure()',context);assert(vm.runInContext('_labStructureView.frame',context)>0);assert.equal(renderers,1);
 vm.runInContext('_labDrawStructure(payload)',context);assert.equal(renderers,1,'selecting another structure must reuse the context');assert(disposals>0,'old geometry must be released');
 let prevented=false;canvas.onwebglcontextlost({preventDefault(){prevented=true;}});assert(prevented);canvas.onwebglcontextrestored();assert(vm.runInContext('_labStructureView.frame',context)>0);
 console.log('PASS Lab width containment, wrapped activity text, persistent viewer over 30 refreshes, drag, pause/resume, renderer reuse and context recovery; no network');
})().catch(e=>{console.error(e);process.exit(1);});
