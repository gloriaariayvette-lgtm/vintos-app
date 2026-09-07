const {chromium}=require('playwright'); const http=require('http'); const fs=require('fs'); const path=require('path');
const srv=http.createServer((rq,rs)=>{const p=path.join(__dirname,decodeURIComponent(rq.url.split('?')[0])); fs.readFile(p,(e,d)=>{if(e){rs.writeHead(404);rs.end();return} rs.writeHead(200,{'content-type':p.endsWith('.js')?'text/javascript':p.endsWith('.html')?'text/html':'application/octet-stream'}); rs.end(d)})}).listen(8796);
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell',args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 fs.mkdirSync('poses',{recursive:true});
 for(const [clip,t] of process.argv.slice(2).map(x=>x.split(':'))){
  const pg=await b.newPage({viewport:{width:600,height:800}}); pg.on('pageerror',e=>console.log('ERR',clip,String(e).slice(0,120)));
  await pg.goto(`http://127.0.0.1:8796/poses.html?clip=${clip}&t=${t}`); await pg.waitForFunction(()=>window.__done,null,{timeout:300000});
  console.log(clip, JSON.stringify(await pg.evaluate(()=>window.__info)));
  await pg.locator('canvas').screenshot({path:`poses/${clip}.png`}); await pg.close(); }
 await b.close(); srv.close();})().catch(e=>{console.error(e);process.exit(1)});
