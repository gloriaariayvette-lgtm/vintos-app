const {chromium}=require('playwright'); const http=require('http'); const fs=require('fs'); const path=require('path');
const srv=http.createServer((rq,rs)=>{const p=path.join(__dirname,decodeURIComponent(rq.url.split('?')[0])); fs.readFile(p,(e,d)=>{if(e){rs.writeHead(404);rs.end();return} rs.writeHead(200,{'content-type':p.endsWith('.js')?'text/javascript':p.endsWith('.html')?'text/html':p.endsWith('.png')?'image/png':'application/octet-stream'}); rs.end(d)})}).listen(8781);
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']}); const pg=await b.newPage(); pg.on('console',m=>console.log('console:',m.text().slice(0,300)));
 await pg.goto('http://127.0.0.1:8781/transplant.html'); await pg.waitForFunction(()=>window.__done,null,{timeout:900000});
 console.log((await pg.evaluate(()=>window.__log)).join('\n'));
 const glb=await pg.evaluate(()=>window.__glb); const atlas=await pg.evaluate(()=>window.__atlas);
 if(glb){ fs.writeFileSync('models/vintos-barehands.glb',Buffer.from(glb,'base64')); fs.writeFileSync('models/atlas-barehands.png',Buffer.from(atlas,'base64')); console.log('wrote glb',fs.statSync('models/vintos-barehands.glb').size,'atlas',fs.statSync('models/atlas-barehands.png').size); }
 await b.close(); srv.close();})().catch(e=>{console.error(e);process.exit(1)});
