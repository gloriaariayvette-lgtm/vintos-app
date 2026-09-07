const {chromium}=require('playwright'); const http=require('http'); const fs=require('fs'); const path=require('path');
const srv=http.createServer((rq,rs)=>{const p=path.join(__dirname,decodeURIComponent(rq.url.split('?')[0])); fs.readFile(p,(e,d)=>{if(e){rs.writeHead(404);rs.end();return} rs.writeHead(200,{'content-type':p.endsWith('.js')?'text/javascript':p.endsWith('.html')?'text/html':'application/octet-stream'}); rs.end(d)})}).listen(8795);
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const pg=await b.newPage(); pg.on('pageerror',e=>console.log('pageerror',String(e).slice(0,200)));
 await pg.goto('http://127.0.0.1:8795/convert.html'); await pg.waitForFunction(()=>window.__done,null,{timeout:900000});
 console.log((await pg.evaluate(()=>window.__log)).join('\n'));
 const out=await pg.evaluate(()=>window.__out);
 fs.mkdirSync('clips',{recursive:true}); const meta={};
 for(const [k,v] of Object.entries(out)){ if(v.b64){ fs.writeFileSync(`clips/${k}.glb`, Buffer.from(v.b64,'base64')); } const {b64,...rest}=v; meta[k]=rest; }
 fs.writeFileSync('clips/clips.json', JSON.stringify(meta,null,1));
 console.log('wrote', Object.keys(out).length, 'clips');
 await b.close(); srv.close();})().catch(e=>{console.error(e);process.exit(1)});
