'use strict';
const http=require('node:http'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=__dirname;
const MAP={'.html':'text/html','.mjs':'text/javascript','.js':'text/javascript','.wasm':'application/wasm','.data':'application/octet-stream','.wav':'audio/wav','.mp4':'video/mp4','.png':'image/png'};
const sleep=ms=>new Promise(ok=>setTimeout(ok,ms));const requests=[];
const server=http.createServer((req,res)=>{const name=decodeURIComponent(req.url.split('?')[0]);const safe=path.resolve(root,'.'+name);if(!safe.startsWith(root+path.sep)){res.writeHead(403).end();return}const st=fs.existsSync(safe)?fs.statSync(safe):null;if(!st?.isFile()){res.writeHead(404).end();return}requests.push({file:name,size:st.size});res.setHeader('Content-Type',MAP[path.extname(safe)]||'application/octet-stream');res.setHeader('Content-Length',st.size);fs.createReadStream(safe).pipe(res)});
async function main(){await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const port=server.address().port;
 const profile=path.join(root,'chrome-cdp-profile');const chrome='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';const t0=Date.now();let stderr='';
 const child=cp.spawn(chrome,['--headless=new','--disable-gpu','--disable-background-networking','--disable-extensions','--no-first-run','--no-default-browser-check','--no-proxy-server','--remote-debugging-port=0','--user-data-dir='+profile,'http://127.0.0.1:'+port+'/wasm_probe_v2.html'],{stdio:['ignore','ignore','pipe']});child.stderr.on('data',x=>{if(stderr.length<10000)stderr+=x.toString()});
 let ws=null;
 try{
  let debugPort;for(let i=0;i<100;i++){let f=path.join(profile,'DevToolsActivePort');if(fs.existsSync(f)){debugPort=Number(fs.readFileSync(f,'utf8').split('\n')[0]);break}await sleep(120)}
  if(!debugPort)throw Error('NO_CDP_PORT');
  let target;for(let i=0;i<80;i++){try{const arr=await(await fetch(`http://127.0.0.1:${debugPort}/json/list`)).json();target=arr.find(t=>t.url.includes('wasm_probe_v2.html'));if(target)break}catch(e){}await sleep(120)}
  if(!target)throw Error('NO_CDP_TARGET');
  ws=new WebSocket(target.webSocketDebuggerUrl);await new Promise((resolve,reject)=>{ws.addEventListener('open',resolve,{once:true});ws.addEventListener('error',reject,{once:true})});
  let serial=0;const pending=new Map;
  ws.addEventListener('message',e=>{let m;try{m=JSON.parse(e.data)}catch(_){return}if(pending.has(m.id)){const [resolve,reject]=pending.get(m.id);pending.delete(m.id);if(m.error)reject(Error(m.error.message));else resolve(m.result)}});
  const cdp=(method,params={})=>new Promise((resolve,reject)=>{const id=++serial;pending.set(id,[resolve,reject]);ws.send(JSON.stringify({id,method,params}));setTimeout(()=>{if(pending.has(id)){pending.delete(id);reject(Error('CDP_RESPONSE_TIMEOUT '+method))}},10000)});
  await cdp('Runtime.enable');await cdp('Performance.enable');
  let state={};for(let n=0;n<115;n++){
    const r=await cdp('Runtime.evaluate',{expression:'({title:document.title,body:document.querySelector("#result")?.textContent,heap:performance.memory?.usedJSHeapSize||null})',returnByValue:true,awaitPromise:true});state=r.result?.value??{};
    if(state.title==='WASM_PROBE_FINISHED'||state.title==='WASM_PROBE_FAILED')break;
    await sleep(250);
  }
  let result;try{result=JSON.parse(state.body)}catch(e){result={status:'TIMEOUT_OR_UNREADABLE',lastState:state}}
  const perf=await cdp('Performance.getMetrics');result.chromeMetrics=perf.metrics?.filter(x=>['JSHeapUsedSize','JSHeapTotalSize','Nodes','Documents','TaskDuration'].includes(x.name))??[];
  result.chromeMemory=state.heap;result.chromeWallMs=Date.now()-t0;result.chromeExitPending=true;result.requests=requests;
  fs.writeFileSync(path.join(root,'wasm_cdp_result.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({status:result.status,error:result.error,initMs:result.initMs,analysisMs:result.analysisMs,cues:result.cueCount,shapes:result.shapes,capabilities:result.capabilities,chromeWallMs:result.chromeWallMs,requestCount:requests.length,chromeMemory:state.heap}).slice(0,3600));
 }catch(err){const obj={status:'RUNNER_ERROR',error:String(err),chromeWallMs:Date.now()-t0,requests,stderr:stderr.slice(-700)};fs.writeFileSync(path.join(root,'wasm_cdp_result.json'),JSON.stringify(obj,null,2));console.log(JSON.stringify(obj).slice(0,2600))}finally{if(ws)ws.close();child.kill('SIGTERM');await sleep(200);server.close()}}
main().catch(e=>{console.error('FATAL',e);process.exitCode=1});
