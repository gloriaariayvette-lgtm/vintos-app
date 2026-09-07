import fs from 'node:fs/promises';
import path from 'node:path';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';
import {VRMLoaderPlugin} from '@pixiv/three-vrm';
import validator from 'gltf-validator';
import sharp from 'sharp';
const root=path.resolve(import.meta.dirname,'../..');
globalThis.self=globalThis;globalThis.window={URL};
globalThis.ProgressEvent=class{constructor(type,props){this.type=type;Object.assign(this,props);}};
globalThis.createImageBitmap=async blob=>{const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});return {data:new Uint8Array(data),width:info.width,height:info.height,close(){}};};
// Image decoding bridge only. Model parsing, skinning and VRM mapping use the real loaders.
THREE.TextureLoader.prototype.load=function(url,onLoad,onProgress,onError){const tex=new THREE.DataTexture();this.manager.itemStart(url);fetch(url).then(r=>r.blob()).then(createImageBitmap).then(image=>{tex.image=image;tex.needsUpdate=true;tex.flipY=true;onLoad?.(tex);this.manager.itemEnd(url);}).catch(e=>{onError?.(e);this.manager.itemError(url);this.manager.itemEnd(url);});return tex;};
const report=JSON.parse(await fs.readFile(path.join(root,'baseline/exports-verification.json'),'utf8'));
report.loaders={};
for(const file of ['vintos.glb','vintos.vrm','source-v2.fbx']){
 const bytes=await fs.readFile(path.join(root,file));let scene,vrm,clips;
 if(file.endsWith('.fbx')){
  let resolve;const done=new Promise(r=>resolve=r);const manager=new THREE.LoadingManager(resolve);scene=new FBXLoader(manager).parse(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.length),'');await done;clips=scene.animations;
 }else{
  const validation=await validator.validateBytes(new Uint8Array(bytes),{uri:file,maxIssues:50});await fs.writeFile(path.join(root,'baseline',file+'.validation.json'),JSON.stringify(validation,null,2));if(validation.issues.numErrors)throw Error(file+' validator errors '+JSON.stringify(validation.issues.messages));
  const loader=new GLTFLoader();if(file.endsWith('.vrm'))loader.register(parser=>new VRMLoaderPlugin(parser));const result=await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.length),'');scene=result.scene;vrm=result.userData.vrm;clips=result.animations;
  if(file.endsWith('.vrm')&&!vrm)throw Error('VRM plugin did not return a VRM');
 }
 scene.updateMatrixWorld(true);const bones=[];const meshes=[];scene.traverse(n=>{if(n.name.startsWith('mixamorig'))bones.push(n.name);if(n.isSkinnedMesh)meshes.push(n);});
 if(new Set(bones).size!==65)throw Error(file+' bone count '+new Set(bones).size);
 const prefix=file.replaceAll('.','-');const outDir=path.join(root,'tools/runtime/qa',prefix);await fs.mkdir(outDir,{recursive:true});const meta={meshes:[],file};
 let total=0,textureDecoded=true,bindError=0;
 for(let mi=0;mi<meshes.length;mi++){
  const m=meshes[mi],g=m.geometry,p=g.getAttribute('position'),uv=g.getAttribute('uv'),normal=g.getAttribute('normal');m.skeleton.update();const pp=new Float32Array(p.count*3),nn=new Float32Array(p.count*3),uu=new Float32Array(p.count*2);const v=new THREE.Vector3(),n=new THREE.Vector3();const normalMatrix=new THREE.Matrix3().getNormalMatrix(m.matrixWorld);
  for(let i=0;i<p.count;i++){v.fromBufferAttribute(p,i);const before=v.clone();m.applyBoneTransform(i,v);bindError=Math.max(bindError,v.distanceTo(before));v.applyMatrix4(m.matrixWorld).toArray(pp,i*3);n.fromBufferAttribute(normal,i).applyMatrix3(normalMatrix).normalize().toArray(nn,i*3);uu[i*2]=uv.getX(i);uu[i*2+1]=uv.getY(i);}
  const index=g.index?Uint32Array.from(g.index.array):Uint32Array.from({length:p.count},(_,i)=>i);total+=index.length/3;
  for(const [label,array] of Object.entries({positions:pp,normals:nn,uv:uu,indices:index}))await fs.writeFile(path.join(outDir,mi+'-'+label+'.bin'),Buffer.from(array.buffer));
  const material=Array.isArray(m.material)?m.material[0]:m.material;const im=material.map?.image;if(!im?.data)textureDecoded=false;else await sharp(Buffer.from(im.data),{raw:{width:im.width,height:im.height,channels:4}}).png().toFile(path.join(outDir,mi+'-texture.png'));
  meta.meshes.push({prefix:String(mi),vertices:p.count,indices:index.length,flipY:material.map?.flipY,textureSize:im?[im.width,im.height]:null});
 }
 await fs.writeFile(path.join(outDir,'meta.json'),JSON.stringify(meta));
 const humanoid=vrm?Object.fromEntries(Object.keys(report.human_bones).map(role=>[role,vrm.humanoid.getRawBoneNode(role)?.name])):undefined;
 if(vrm)for(const [role,name] of Object.entries(report.human_bones))if(humanoid[role]!==name)throw Error('Humanoid mismatch '+role);
 if(!textureDecoded||total!==266579||bindError>1e-5)throw Error(file+' failed texture/triangle/bind check '+JSON.stringify({textureDecoded,total,bindError}));
 const armAngles={};
 for(const side of ['Left','Right']){const upper=scene.getObjectByName('mixamorig'+side+'Arm').getWorldPosition(new THREE.Vector3());const wrist=scene.getObjectByName('mixamorig'+side+'Hand').getWorldPosition(new THREE.Vector3());const delta=wrist.sub(upper);armAngles[side]=Math.atan2(Math.abs(delta.y),Math.hypot(delta.x,delta.z))*180/Math.PI;if(armAngles[side]>10)throw Error('Not T-pose '+side);}
 report.loaders[file]={restPose:'T-pose',armDegreesFromHorizontal:armAngles,namedBones:[...new Set(bones)],triangles:total,textureDecoded,bindPoseMaxDisplacement:bindError,humanoid,animationClips:clips?.length,meshes:meshes.length};console.log(file,JSON.stringify({total,bindError,textureDecoded,vrm:!!vrm}));
}
report.threeVersion=THREE.REVISION;report.threeVrmVersion=JSON.parse(await fs.readFile(path.join(import.meta.dirname,'node_modules/@pixiv/three-vrm/package.json'))).version;
await fs.writeFile(path.join(root,'baseline/exports-verification.json'),JSON.stringify(report,null,2)+'\n');
