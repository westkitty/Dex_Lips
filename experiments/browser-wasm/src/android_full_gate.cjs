'use strict';
const cp=require('node:child_process'),fs=require('node:fs'),http=require('node:http'),path=require('node:path');
const ROOT=__dirname,SERIAL=process.env.DEX_LIPS_ADB_SERIAL||'',ORIGINAL='wasm_mp4_mobile.html';
const mime={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.wasm':'application/wasm','.data':'application/octet-stream','.wav':'audio/wav','.mp4':'video/mp4','.png':'image/png'};
const reqs=[];const sleep=ms=>new Promise(f=>setTimeout(f,ms));const exec=(args)=>cp.execFileSync('adb',['-s',SERIAL,...args],{encoding:'utf8',timeout:9000}).trim();
let server,debugPort,reversePort,browserWs,pageWs,createdTarget;
function call(ws,method,params={}){return new Promise((res,rej)=>{const id=Date.now()+Math.floor(Math.random()*100000);const handle=(e)=>{let m;try{m=JSON.parse(e.data)}catch{return}if(m.id!==id)return;ws.removeEventListener('message',handle);clearTimeout(timer);m.error?rej(Error(m.error.message)):res(m.result)};const timer=setTimeout(()=>{ws.removeEventListener('message',handle);rej(Error(`CDP_TIMEOUT ${method}`))},12000);ws.addEventListener('message',handle);ws.send(JSON.stringify({id,method,params}))})}
async function main(){const info={status:'MOBILE_TEST_UNVERIFIED',device:'SM-X910',mode:'still',mediaLocalOnly:true};try{
  const source=fs.readFileSync(path.join(ROOT,'wasm_mp4.html'),'utf8');const needle="link.download='wasm_'+mode+'.mp4';link.click();";if(!source.includes(needle))throw Error('HTML source mismatch');
  fs.writeFileSync(path.join(ROOT,ORIGINAL),source.replace(needle,"link.download='wasm_'+mode+'.mp4';if(!new URLSearchParams(location.search).has('noDownload'))link.click();"));
  server=http.createServer((req,res)=>{const file=decodeURIComponent(new URL(req.url,'http://localhost').pathname);const p=path.resolve(ROOT,'.'+file);if(!p.startsWith(ROOT+path.sep)){res.writeHead(403).end();return}fs.stat(p,(err,st)=>{if(err||!st.isFile()){res.writeHead(404).end();return}reqs.push({file,bytes:st.size});res.setHeader('Content-Type',mime[path.extname(p)]||'application/octet-stream');res.setHeader('Content-Length',st.size);fs.createReadStream(p).pipe(res)})});await new Promise(ok=>server.listen(0,'127.0.0.1',ok));reversePort=server.address().port;
  exec(['reverse',`tcp:${reversePort}`,`tcp:${reversePort}`]);debugPort=Number(exec(['forward','tcp:0','localabstract:chrome_devtools_remote']));if(!debugPort)throw Error('NO_ADB_DEBUG_PORT');
  const version=await (await fetch(`http://127.0.0.1:${debugPort}/json/version`,{signal:AbortSignal.timeout(7000)})).json();browserWs=new WebSocket(version.webSocketDebuggerUrl);await new Promise((ok,bad)=>{browserWs.addEventListener('open',ok,{once:true});browserWs.addEventListener('error',bad,{once:true})});
  const existing=(await call(browserWs,'Target.getTargets')).targetInfos.filter(t=>t.type==='page').map(t=>t.targetId);
  const url=`http://127.0.0.1:${reversePort}/${ORIGINAL}?mode=still&noDownload=1`;
  const target=await call(browserWs,'Target.createTarget',{url,background:true});createdTarget=target.targetId;if(existing.includes(createdTarget))throw Error('TARGET_COLLISION');
  let page;for(let i=0;i<50;i++){const arr=await(await fetch(`http://127.0.0.1:${debugPort}/json/list`,{signal:AbortSignal.timeout(7000)})).json();page=arr.find(x=>x.id===createdTarget&&x.webSocketDebuggerUrl);if(page)break;await sleep(180)}if(!page)throw Error('NO_CREATED_PAGE');
  pageWs=new WebSocket(page.webSocketDebuggerUrl);await new Promise((ok,bad)=>{pageWs.addEventListener('open',ok,{once:true});pageWs.addEventListener('error',bad,{once:true})});await call(pageWs,'Runtime.enable');
  let last={};for(let i=0;i<160;i++){const evaled=await call(pageWs,'Runtime.evaluate',{expression:"({title:document.title,txt:document.getElementById('result')?.textContent??'',heap:performance.memory?.usedJSHeapSize??null})",returnByValue:true});last=evaled.result?.value||{};if(last.title==='MP4_PROBE_FINISHED'||last.title==='MP4_PROBE_FAILED')break;await sleep(220)}
  let report={};try{report=JSON.parse(last.txt)}catch{};
  Object.assign(info,{status:last.title==='MP4_PROBE_FINISHED'&&report.status==='PASS_RENDERED'?'PASS_MOBILE_RENDER':'MOBILE_RENDER_FAILED',realWasmReportedCues:report.cues||null,aacPolyfillUsed:report.polyfill??null,mp4Sha256:report.mp4Sha256||null,mp4Bytes:report.mp4Bytes||null,frames:report.frames||null,videoFrames:report.sourceVideoFrames||null,analysisMs:report.analysisMs||null,encodeMs:report.renderMs||null,totalMs:report.totalMs||null,jsHeapSnapshot:report.jsHeapBytes||last.heap||null,codecs:report.codecs||null,stage:report.stage||null,error:report.error||null,downloadTriggered:false,requests:reqs});
}catch(e){info.status='MOBILE_TEST_BLOCKED';info.error=String(e);info.requests=reqs}finally{
  try{pageWs?.close()}catch{};if(createdTarget&&browserWs){try{await call(browserWs,'Target.closeTarget',{targetId:createdTarget});info.tabClosed=true}catch(e){info.tabClosed=false;info.closeError=String(e)}}try{browserWs?.close()}catch{};
  if(debugPort){try{exec(['forward','--remove',`tcp:${debugPort}`]);info.debugForwardRemoved=true}catch(e){info.debugForwardRemoved=false}}
  if(reversePort){try{exec(['reverse','--remove',`tcp:${reversePort}`]);info.reverseRemoved=true}catch(e){info.reverseRemoved=false}}
  try{server?.close()}catch{};
  const out=path.join(ROOT,'android_real_wasm_render_result.json');fs.writeFileSync(out,JSON.stringify(info,null,2));console.log(JSON.stringify(info).slice(0,6500));
}}
main();
