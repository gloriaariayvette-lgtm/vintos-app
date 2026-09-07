import fs from 'node:fs/promises';
import path from 'node:path';
import http from 'node:http';
import {chromium} from 'playwright';
import serverChromium from '@sparticuz/chromium';
import validator from 'gltf-validator';
import {brotliDecompressSync} from 'node:zlib';
import {execFileSync} from 'node:child_process';
const root=path.resolve(import.meta.dirname,'../..');
const server=http.createServer(async(req,res)=>{try{const p=path.resolve(root,'.'+decodeURIComponent(new URL(req.url,'http://localhost').pathname));if(!p.startsWith(root+path.sep))throw Error('invalid path');const b=await fs.readFile(p);res.setHeader('Content-Type',({'.js':'text/javascript','.html':'text/html','.jpg':'image/jpeg','.json':'application/json','.glb':'model/gltf-binary'})[path.extname(p)]||'application/octet-stream');res.end(b);}catch{res.statusCode=404;res.end();}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));
let browser;
try{
 // Extract without chown: managed workspace filesystems reject archive UID changes.
 const tmp=path.join(import.meta.dirname,'qa/tmp');await fs.mkdir(tmp,{recursive:true});
 const executablePath=path.join(tmp,'chromium');
 if(!await fs.stat(executablePath).then(s=>s.size>100000000).catch(()=>false)){
  const bin=path.join(import.meta.dirname,'node_modules/@sparticuz/chromium/bin');
  await fs.writeFile(executablePath,brotliDecompressSync(await fs.readFile(path.join(bin,'chromium.br'))));await fs.chmod(executablePath,0o755);
  for(const name of ['swiftshader','fonts'])execFileSync('tar',['--no-same-owner','-xf','-','-C',tmp],{input:brotliDecompressSync(await fs.readFile(path.join(bin,name+'.tar.br')))});
 }
 process.env.FONTCONFIG_PATH=path.join(tmp,'fonts');
 browser=await chromium.launch({executablePath,headless:true,args:[...serverChromium.args,'--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist','--no-sandbox']});
 const page=await browser.newPage({viewport:{width:1200,height:900}});page.on('pageerror',e=>console.error('PAGE',e));page.on('console',m=>{console.log('CONSOLE',m.text());});
 console.log('BROWSER READY'); await page.goto('http://127.0.0.1:'+server.address().port+'/tools/runtime/house.html');console.log('PAGE LOADED');await page.waitForFunction(()=>window.houseReady,null,{timeout:120000});console.log('SCENE READY');
 const rooms=[];
 for(const id of ['livingroom','kitchen']){
  if(!process.argv.includes('--render-only')){
   console.log('BUILDING',id);const result=await page.evaluate(id=>window.buildHouse(id),id);const bytes=Buffer.from(result.bytes,'base64');await fs.writeFile(path.join(root,'house',id+'.glb'),bytes);rooms.push(result.manifest);console.log('EXPORTED',id,bytes.length);
   const report=await validator.validateBytes(bytes,{uri:id+'.glb',maxIssues:100});await fs.writeFile(path.join(root,'baseline',id+'-validation.json'),JSON.stringify(report,null,2)+'\n');if(report.issues.numErrors)throw Error(JSON.stringify(report.issues));
  }
  for(const view of id==='livingroom'?['main','dining','overview','scale']:['main','reverse','overview','scale']){
   const r=await page.evaluate(([id,view])=>window.renderHouse(id,view),[id,view]);await fs.writeFile(path.join(root,'baseline',id+'-'+view+'.png'),Buffer.from(r.url.split(',')[1],'base64'));console.log('RENDERED',id,view,r.renderer);
  }
 }
 if(rooms.length){const source=JSON.parse(await fs.readFile(path.join(root,'house/source-house-map.json'),'utf8'));const manifest={schemaVersion:1,status:'Two-room review; ten rooms pending',units:'meters',up:'+Y',forward:'+Z into room from main doorway',avatarHeightMeters:1.166,scaleBasis:'Estimated household proportions scaled by 1.166/1.75; no measured survey available',source:'https://github.com/gloriaariayvette-lgtm/Vintos-main/blob/main/scripts/house-map.json',portalContract:{trigger:'Transparent box with alpha=0; use geometry bounds for collision',spawn:'Use target portal spawn and inwardNormal, with re-entry cooldown until clear of trigger',pending:'Do not activate a portal whose partnerStatus is pending-review. Reciprocal node names are reserved for later room files.',rotation:'Room-local +Z faces inward. Rotate avatar to target inwardNormal; do not copy source-room coordinates.'},rooms,plannedRooms:source.rooms.filter(r=>!rooms.some(b=>b.id===r.id)).map(r=>({id:r.id.replace('cats room','catsroom'),status:'not-built',photographed:!['laundry','hall','bathroom','closet','stairs','cats room'].includes(r.id),adjacent:r.adjacent.map(x=>x.replace('cats room','catsroom'))}))};await fs.writeFile(path.join(root,'house/house.json'),JSON.stringify(manifest,null,2)+'\n');}
}finally{await browser?.close();server.close();}
