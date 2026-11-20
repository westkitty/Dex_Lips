'use strict';

// Dex_Lips Rig Lab. No network calls, model weights, tracking or canon approval.
(() => {
  const $ = (id) => document.getElementById(id);
  const SHAPES = 'XABCDEFGH';
  // Pose ratio tables live in trace_core.js (shared with Python via parity test).
  const CAPTIONS = {X:['Rest','Transparent — retain the original closed-mouth artwork'],A:['Closed pressure','Flattened source articulation'],B:['Small opening','Compact source-derived opening'],C:['Medium opening','Broader source-derived articulation'],D:['Open','Wide source-derived articulation'],E:['Rounded','Narrower rounded opening'],F:['Tight round','Small rounded articulation'],G:['Teeth variant','Compressed vertical expression; no teeth are invented'],H:['Narrow hold','Short horizontal hold']};
  const PROTECTED = new Set(['098e017a4960e7eeda634ac58c3b2dafc7097f8af87cab439bfbb88d4c87d1e2','03fd4f144ebc005e70ce8e9e906da9979a94ebe1a6344982e49fcf2441e5a8b3']);
  const state = {file:null,source:null,sourceHash:'',isVideo:false,videoUrl:null,audioUrl:null,sprites:null,trace:null,pose:'D',cues:null,playRaf:null};
  const pos = {x:.5,y:.6};
  const dim = {w:.13,h:.065};
  const stage = $('stageCanvas'); const stageCtx = stage.getContext('2d');
  const poseCanvas = $('poseCanvas'); const poseCtx = poseCanvas.getContext('2d');
  const traceCanvas = $('traceCanvas'); const traceCtx = traceCanvas.getContext('2d');
  const rail = $('poseRail');

  function say(message, type='neutral') { const el=$('message'); el.textContent=message; el.dataset.type=type; }
  function fail(message) { say(message,'error'); $('traceState').textContent='BLOCKED'; }
  function setDisabled() { $('generate').disabled=!state.source || PROTECTED.has(state.sourceHash); const enabled=!!state.sprites && $('reviewed').checked; $('downloadZip').disabled=!enabled; $('downloadPng').disabled=!enabled; }
  function invalidate() {state.sprites=null;state.trace=null;$('reviewed').checked=false;$('traceReview').hidden=true;$('traceState').textContent='NOT GENERATED';setDisabled();paintStage();paintPose();}
  const percent = (value) => `${Number(value).toFixed(1).replace(/\.0$/,'')}%`;
  function syncControls() {
    $('mouthX').value=(pos.x*100).toString();$('mouthY').value=(pos.y*100).toString();
    $('mouthXValue').textContent=percent(pos.x*100);$('mouthYValue').textContent=percent(pos.y*100);
    $('mouthWValue').textContent=percent(dim.w*100);$('mouthHValue').textContent=percent(dim.h*100);
  }
  const limit=(n,a,b)=>Math.min(b,Math.max(a,n));
  function newCanvas(w,h) {let c=document.createElement('canvas');c.width=w;c.height=h;return c;}
  function rgba(c){return c.getContext('2d',{willReadFrequently:true});}
  async function fileHash(file){if(!crypto?.subtle)throw Error('Secure browser context is needed for source hashing. Open from HTTPS or localhost.');const buffer=await file.arrayBuffer();const digest=await crypto.subtle.digest('SHA-256',buffer);return [...new Uint8Array(digest)].map(b=>b.toString(16).padStart(2,'0')).join('');}
  const MAX=40*1024*1024;
  async function loadFile(file) {
    if(!file)return;
    if(file.size<1||file.size>MAX){fail('Source must be between 1 byte and 40 MB.');return;}
    const video = /^video\//.test(file.type)||/\.(mp4|webm|mov)$/i.test(file.name);
    const image = /^image\//.test(file.type)||/\.(png|jpe?g|webp)$/i.test(file.name);
    if(!video&&!image){fail('Use a PNG, JPEG, WEBP, MP4, WEBM or MOV source.');return;}
    $('generate').disabled=true;
    say('Reading the selected file and verifying its original SHA-256…');
    try {
      const hash=await fileHash(file);
      revokeUrl('videoUrl');state.file=file;state.sourceHash=hash;state.isVideo=video;
      $('fileLabel').textContent=file.name;$('hashPreview').textContent=hash.slice(0,12)+'…';$('hashPreview').title=hash;
      if(video){
        state.source=null;invalidate();$('videoTools').hidden=false;
        const media=$('videoInput');const url=URL.createObjectURL(file);state.videoUrl=url;media.src=url;media.load();
        await new Promise((resolve,reject)=>{const done=()=>{media.removeEventListener('loadeddata',done);media.removeEventListener('error',bad);resolve()};const bad=()=>{media.removeEventListener('loadeddata',done);media.removeEventListener('error',bad);reject(Error('This browser could not decode the video. Try another supported format.'))};media.addEventListener('loadeddata',done);media.addEventListener('error',bad);});
        captureVideoFrame();
      }else{
        $('videoTools').hidden=true;
        const url=URL.createObjectURL(file);const photo=new Image();
        try {photo.src=url;await photo.decode();}finally{URL.revokeObjectURL(url);}
        if(photo.naturalWidth<2||photo.naturalHeight<2||photo.naturalWidth*photo.naturalHeight>35e6)throw Error('Source dimensions are outside the 35-million-pixel safety limit.');
        const c=newCanvas(photo.naturalWidth,photo.naturalHeight);rgba(c).drawImage(photo,0,0);setSource(c);
      }
      if(PROTECTED.has(hash)) {invalidate();fail('This exact canonical/provisional reference is protected. Draft generation and export are blocked.');}
      else say('Source loaded. Click the visible mouth, adjust the region box, then generate draft poses.','success');
    }catch(err){state.source=null;state.file=null;invalidate();fail(err.message||'Unable to load source.');}
  }
  function setSource(canvas){state.source=canvas;$('originalSize').textContent=`${canvas.width} × ${canvas.height}`;$('emptyState').hidden=true;invalidate();setDisabled();}
  function captureVideoFrame(){const media=$('videoInput');if(!media.videoWidth||!media.videoHeight){fail('Video frame unavailable. Select a moment with visible character artwork.');return;}if(media.videoWidth*media.videoHeight>35e6){fail('Video frame exceeds the 35-million-pixel limit.');return;}const c=newCanvas(media.videoWidth,media.videoHeight);rgba(c).drawImage(media,0,0);setSource(c);say('Reference frame captured. Source video remains unchanged.','success');}
  function posFromCanvas(clientX,clientY){const rect=stage.getBoundingClientRect();pos.x=limit((clientX-rect.left)/rect.width,.03,.97);pos.y=limit((clientY-rect.top)/rect.height,.03,.97);syncControls();invalidate();}
  function paintStage(){
    if(!state.source){stage.width=640;stage.height=420;stageCtx.clearRect(0,0,640,420);return;}
    const source=state.source;stage.width=source.width;stage.height=source.height;stageCtx.drawImage(source,0,0);
    if(state.sprites){const sprite=state.sprites[state.pose];stageCtx.drawImage(sprite,Math.round(pos.x*stage.width-sprite.width/2),Math.round(pos.y*stage.height-sprite.height/2));}
    const cw=dim.w*stage.width,ch=dim.h*stage.height;
    stageCtx.save();stageCtx.strokeStyle='#b4f4d0';stageCtx.lineWidth=Math.max(1,Math.min(stage.width,stage.height)*.002);stageCtx.setLineDash([10,7]);stageCtx.strokeRect(pos.x*stage.width-cw/2,pos.y*stage.height-ch/2,cw,ch);stageCtx.setLineDash([]);stageCtx.fillStyle='#b4f4d0';const dot=Math.max(2,stage.width*.004);stageCtx.fillRect(pos.x*stage.width-dot/2,pos.y*stage.height-dot/2,dot,dot);stageCtx.restore();
  }
  function selectPose(shape){state.pose=shape;for(const button of rail.querySelectorAll('button'))button.setAttribute('aria-pressed',String(button.dataset.pose===shape));$('poseLabel').textContent=shape+' / '+CAPTIONS[shape][0].toUpperCase();$('poseTitle').textContent=CAPTIONS[shape][0];$('poseDescription').textContent=CAPTIONS[shape][1];paintPose();paintStage();}
  function paintPose(){poseCtx.clearRect(0,0,poseCanvas.width,poseCanvas.height);if(!state.sprites)return;const sprite=state.sprites[state.pose];const factor=Math.min(180/sprite.width,108/sprite.height,1.5);const w=sprite.width*factor,h=sprite.height*factor;poseCtx.imageSmoothingEnabled=$('mode').value!=='source-faceted';poseCtx.drawImage(sprite,(poseCanvas.width-w)/2,(poseCanvas.height-h)/2,w,h);}
  function ringPalette(source){const w=source.width,h=source.height,cx=Math.round(pos.x*w),cy=Math.round(pos.y*h),rx=dim.w*w/2,ry=dim.h*h/2;const ctx=rgba(source);const samples=[];for(const [dx,dy] of [[-1.3,-1],[0,-1.35],[1.3,-1],[-1.45,0],[1.45,0],[-1.3,1],[0,1.35],[1.3,1]]){const x=limit(Math.round(cx+dx*rx),0,w-1),y=limit(Math.round(cy+dy*ry),0,h-1);samples.push([...ctx.getImageData(x,y,1,1).data].slice(0,3));}const bins=new Map();for(const p of samples){const b=p.map(v=>Math.floor(v/24)*24).join(',');bins.set(b,(bins.get(b)||0)+1);}const best=[...bins].sort((a,b)=>b[1]-a[1])[0][0].split(',').map(Number);const group=samples.filter(p=>p.every((v,i)=>Math.abs(v-best[i])<24));return [0,1,2].map(i=>(group.length?group:samples).map(p=>p[i]).sort((a,b)=>a-b)[Math.floor((group.length||samples.length)/2)]);}
  function graphicSprites(source,mode,width,height,jaw){const base=ringPalette(source),edge=base.map(x=>Math.round(limit(x*.48,4,255))),fill=base.map(x=>Math.round(limit(x*.18,0,255)));const sprites={};const mj=globalThis.DexTraceCore.JAW_MODES[jaw||'human'];for(const shape of SHAPES){const c=newCanvas(width,height);const ctx=rgba(c);if(shape!=='X'){const [wr,hr]=mj.ratios[shape],halfW=Math.max(2,width*wr*.46),halfH=Math.max(1,height*hr*.43),cx=width/2,cy=mj.anchor==='top'?Math.min(height/2,height*.05+halfH):height/2;ctx.fillStyle=`rgb(${fill.join(',')})`;ctx.strokeStyle=`rgb(${edge.join(',')})`;ctx.lineWidth=Math.max(1,Math.min(5,Math.round(Math.min(width,height)*.035)));ctx.beginPath();if(mode==='faceted'){const pts=[[cx-halfW,cy],[cx-.7*halfW,cy-halfH],[cx,cy-.92*halfH],[cx+.75*halfW,cy-halfH],[cx+halfW,cy],[cx+.65*halfW,cy+halfH],[cx,cy+.84*halfH],[cx-.75*halfW,cy+halfH]];pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();}else{ctx.ellipse(cx,cy,halfW,halfH,0,0,Math.PI*2)}ctx.fill();ctx.stroke();}sprites[shape]=c;}return{sprites,trace:null};}
  const Core = globalThis.DexTraceCore;
  function sourceSprites(source,mode,contrast,outW,outH,jaw){
    const w=source.width,h=source.height;const {regionW,regionH,left,top,sw,sh}=Core.regionBox(w,h,pos,dim);
    const search=newCanvas(sw,sh);rgba(search).drawImage(source,left,top,regionW,regionH,0,0,sw,sh);
    const pix=rgba(search).getImageData(0,0,sw,sh).data,lum=new Float64Array(sw*sh);
    for(let i=0;i<lum.length;i++){const k=i*4;lum[i]=Core.luma(pix[k],pix[k+1],pix[k+2]);}
    const winner=Core.selectComponent(lum,sw,sh,contrast),mark=new Uint8Array(sw*sh);for(const index of winner.component)mark[index]=1;const holes=Core.fillHoles(mark,sw,sh);
    const original=rgba(source).getImageData(left,top,regionW,regionH),masked=newCanvas(regionW,regionH),id=rgba(masked).createImageData(regionW,regionH);let minX=regionW,minY=regionH,maxX=-1,maxY=-1;
    for(let y=0;y<regionH;y++)for(let x=0;x<regionW;x++){const si=Core.upsampleIndex(x,y,regionW,regionH,sw,sh);if(!holes[si])continue;const p=(y*regionW+x)*4;id.data[p]=original.data[p];id.data[p+1]=original.data[p+1];id.data[p+2]=original.data[p+2];id.data[p+3]=255;minX=Math.min(minX,x);minY=Math.min(minY,y);maxX=Math.max(maxX,x);maxY=Math.max(maxY,y);}
    if(maxX<0)throw Error('Source trace contained no retained pixels.');rgba(masked).putImageData(id,0,0);
    const observed=newCanvas(maxX-minX+1,maxY-minY+1);rgba(observed).drawImage(masked,minX,minY,observed.width,observed.height,0,0,observed.width,observed.height);
    const sprites={X:newCanvas(outW,outH)};for(const shape of SHAPES.slice(1)){const [px,py,tw,th]=Core.poseBox(outW,outH,shape,jaw);const c=newCanvas(outW,outH),ctx=rgba(c);ctx.imageSmoothingEnabled=mode!=='source-faceted';ctx.drawImage(observed,px,py,tw,th);sprites[shape]=c;}
    const maskCanvas=newCanvas(w,h),traceCtx=rgba(maskCanvas);traceCtx.drawImage(source,0,0);
    const tint=traceCtx.getImageData(left,top,regionW,regionH);for(let y=0;y<regionH;y++)for(let x=0;x<regionW;x++){const si=Core.upsampleIndex(x,y,regionW,regionH,sw,sh);if(!holes[si])continue;const k=(y*regionW+x)*4;tint.data[k]=Math.round(tint.data[k]*.38);tint.data[k+1]=Math.round(tint.data[k+1]*.38+255*.62);tint.data[k+2]=Math.round(tint.data[k+2]*.38+188*.62);}
    traceCtx.putImageData(tint,left,top);traceCtx.strokeStyle='#e6bd77';traceCtx.lineWidth=Math.max(1,Math.round(w*.002));traceCtx.strokeRect(left,top,regionW,regionH);
    return{sprites,trace:{canvas:maskCanvas,score:winner.score,polarity:winner.polarity,bbox:[left,top,regionW,regionH]}};
  }
  function generate(){
    if(!state.source||!state.file){fail('Load artwork first.');return;}
    if(PROTECTED.has(state.sourceHash)){fail('This exact canonical reference is protected; no draft may be created.');return;}
    try {
      const src=state.source,width=Math.max(8,Math.round(dim.w*src.width)),height=Math.max(8,Math.round(dim.h*src.height));
      if(width>1024||height>1024||width*height>1024*1024)throw Error('Sprite dimensions exceed 1024px limit. Reduce the region size.');
      if(pos.x-dim.w/2<0||pos.x+dim.w/2>1||pos.y-dim.h/2<0||pos.y+dim.h/2>1)throw Error('The mouth region must fit fully within the artwork.');
      const mode=$('mode').value,jaw=$('jaw').value;const result=mode.startsWith('source-')?sourceSprites(src,mode,$('contrast').value,width,height,jaw):graphicSprites(src,mode,width,height,jaw);
      state.sprites=result.sprites;state.trace=result.trace;$('reviewed').checked=false;$('traceReview').hidden=!result.trace;
      if(result.trace){const canvas=result.trace.canvas;traceCanvas.width=canvas.width;traceCanvas.height=canvas.height;traceCtx.drawImage(canvas,0,0);$('traceScore').textContent=`${result.trace.polarity.toUpperCase()} · ${result.trace.score.toFixed(3)} DIAGNOSTIC`;$('traceState').textContent='SOURCE TRACE';}
      else{$('traceState').textContent='GRAPHIC PRESET';}
      setDisabled();selectPose('D');say('Nine separate mouth sprites generated as an unapproved draft. Inspect each shape; check the review box before export.','success');
    }catch(e){state.sprites=null;state.trace=null;$('traceReview').hidden=true;setDisabled();fail(e.message||'Could not generate draft.');paintStage();paintPose();}
  }
  const encoder=new TextEncoder();
  const crcTable=(()=>{const table=new Uint32Array(256);for(let n=0;n<256;n++){let c=n;for(let i=0;i<8;i++)c=c&1?0xedb88320^(c>>>1):c>>>1;table[n]=c>>>0;}return table;})();
  function crc32(bytes){let crc=-1;for(const b of bytes)crc=(crc>>>8)^crcTable[(crc^b)&255];return(crc^-1)>>>0;}
  function zipBytes(entries){
    const local=[],central=[];let offset=0;
    for(const {name,data} of entries){const nameBytes=encoder.encode(name),crc=crc32(data),size=data.byteLength;const h=new Uint8Array(30+nameBytes.length);let v=new DataView(h.buffer);v.setUint32(0,0x04034b50,true);v.setUint16(4,20,true);v.setUint16(8,0,true);v.setUint32(14,crc,true);v.setUint32(18,size,true);v.setUint32(22,size,true);v.setUint16(26,nameBytes.length,true);h.set(nameBytes,30);local.push(h,data);
      const c=new Uint8Array(46+nameBytes.length);v=new DataView(c.buffer);v.setUint32(0,0x02014b50,true);v.setUint16(4,20,true);v.setUint16(6,20,true);v.setUint32(16,crc,true);v.setUint32(20,size,true);v.setUint32(24,size,true);v.setUint16(28,nameBytes.length,true);v.setUint32(42,offset,true);c.set(nameBytes,46);central.push(c);offset+=h.length+size;
    }
    const centralSize=central.reduce((n,b)=>n+b.length,0),end=new Uint8Array(22),v=new DataView(end.buffer);v.setUint32(0,0x06054b50,true);v.setUint16(8,entries.length,true);v.setUint16(10,entries.length,true);v.setUint32(12,centralSize,true);v.setUint32(16,offset,true);return new Blob([...local,...central,end],{type:'application/zip'});
  }
  function download(blob,name){const url=URL.createObjectURL(blob),anchor=document.createElement('a');anchor.href=url;anchor.download=name;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),3000);}
  const toPng=(canvas)=>new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(Error('PNG encoding failed.')),'image/png'));
  function exportName(){return(state.file?.name||'character').replace(/\.[^.]*$/,'').replace(/[^a-zA-Z0-9_-]/g,'_').slice(0,36)||'character';}
  async function exportRig(){
    if(!state.sprites||!$('reviewed').checked){fail('Inspect the draft and check job-specific review before export.');return;}
    try { $('downloadZip').disabled=true;say('Packing nine separate PNGs with original source hash…');
      const entries=[];for(const shape of SHAPES){const blob=await toPng(state.sprites[shape]);entries.push({name:shape+'.png',data:new Uint8Array(await blob.arrayBuffer())});}
      const rig={schema_version:1,character_id:'generated-browser-draft-review-required',source_path:state.file.name,source_sha256:state.sourceHash,authority:'generated_draft',approved:false,mouth_anchor:{x:pos.x,y:pos.y,scale:1,rotation_deg:0},shapes:Object.fromEntries([...SHAPES].map(s=>[s,s+'.png'])),jaw_mode:$('jaw').value,notes:'Unapproved source-aware browser draft. User-reviewed for this job only. Source tracing is not automatic character identity recognition or canonical approval. Use with the full Dex_Lips local compositor.'};
      entries.push({name:'rig.json',data:encoder.encode(JSON.stringify(rig,null,2))});
      const bytes=entries.reduce((sum,e)=>sum+e.data.byteLength,0);if(bytes>10*1024*1024)throw Error('Rig exceeds the 10 MiB import budget; reduce region dimensions.');
      download(zipBytes(entries),'Dex_Lips_'+exportName()+'_draft.zip');say('ZIP exported: X/A–H transparent PNGs + source-bound unapproved rig.json. The original file was not changed.','success');
    }catch(e){fail(e.message||'ZIP export failed.');}finally{setDisabled();}
  }
  async function exportPose(){if(!state.sprites||!$('reviewed').checked){fail('Review the draft first.');return;}try{download(await toPng(state.sprites[state.pose]),'Dex_Lips_'+exportName()+'_'+state.pose+'.png');say(`Saved ${state.pose}.png as a separate transparent sprite.`,'success');}catch(e){fail(e.message);}}
  function revokeUrl(which){if(state[which]){URL.revokeObjectURL(state[which]);state[which]=null;}}
  function validatedCues(){let json;try{json=JSON.parse($('cueInput').value);}catch{throw Error('Cue JSON is not valid.');}const cues=json?.mouthCues;if(!Array.isArray(cues)||!cues.length||cues.length>10000)throw Error('Provide 1–10,000 mouthCues entries.');let previous=0;return cues.map(c=>{const a=Number(c.start),b=Number(c.end);if(!SHAPES.includes(c.value)||c.value.length!==1||!Number.isFinite(a)||!Number.isFinite(b)||a<previous-1e-8||b<=a||a<0||b>30.06)throw Error('Cues must have ordered positive times (up to 30s), and values X/A–H.');previous=b;return{start:a,end:b,value:c.value};});}
  function syncCuePose(){const audio=$('speechPlayer');if(!state.cues||!state.sprites){stopCueLoop();return;}const t=audio.currentTime;let pose='X';for(const cue of state.cues){if(cue.start<=t&&t<cue.end){pose=cue.value;break;}}if(state.pose!==pose)selectPose(pose);if(!audio.paused&&!audio.ended)state.playRaf=requestAnimationFrame(syncCuePose);else state.playRaf=null;}
  function stopCueLoop(){if(state.playRaf!==null){cancelAnimationFrame(state.playRaf);state.playRaf=null;}}
  function init(){
    for(const shape of SHAPES){const button=document.createElement('button');button.type='button';button.textContent=shape;button.dataset.pose=shape;button.setAttribute('aria-pressed','false');button.addEventListener('click',()=>{stopCueLoop();selectPose(shape);});rail.append(button);}
    syncControls();selectPose('D');
    $('sourceInput').addEventListener('change',(e)=>loadFile(e.target.files?.[0]));
    for(const [id,key,scale] of [['mouthW','w',100],['mouthH','h',100],['mouthX','x',100],['mouthY','y',100]])$(''+id).addEventListener('input',(e)=>{if(key==='x'||key==='y')pos[key]=Number(e.target.value)/scale;else dim[key]=Number(e.target.value)/scale;syncControls();invalidate();});
    for(const id of ['mode','contrast','jaw'])$(id).addEventListener('change',invalidate);
    stage.addEventListener('pointerdown',(e)=>{if(state.source)posFromCanvas(e.clientX,e.clientY);});
    stage.addEventListener('keydown',(e)=>{if(!state.source||!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key))return;e.preventDefault();const step=e.shiftKey?.025:.005;pos.x=limit(pos.x+(e.key==='ArrowRight'?step:e.key==='ArrowLeft'?-step:0),.03,.97);pos.y=limit(pos.y+(e.key==='ArrowDown'?step:e.key==='ArrowUp'?-step:0),.03,.97);syncControls();invalidate();});
    $('captureVideo').addEventListener('click',captureVideoFrame);$('generate').addEventListener('click',generate);$('reviewed').addEventListener('change',setDisabled);$('downloadZip').addEventListener('click',exportRig);$('downloadPng').addEventListener('click',exportPose);
    const drop=$('fileDrop');drop.addEventListener('dragover',(e)=>{e.preventDefault();drop.classList.add('drag')});drop.addEventListener('dragleave',()=>drop.classList.remove('drag'));drop.addEventListener('drop',(e)=>{e.preventDefault();drop.classList.remove('drag');if(e.dataTransfer.files?.length)loadFile(e.dataTransfer.files[0]);});
    $('audioInput').addEventListener('change',(e)=>{revokeUrl('audioUrl');state.cues=null;stopCueLoop();const f=e.target.files?.[0];if(!f){$('speechPlayer').removeAttribute('src');return;}if(f.size>40*1024*1024){fail('Audio is larger than 40 MB.');return;}state.audioUrl=URL.createObjectURL(f);$('speechPlayer').src=state.audioUrl;say('Audio loaded locally. Paste reviewed cue JSON and validate it before preview.');});
    $('applyCues').addEventListener('click',()=>{try{state.cues=validatedCues();say(`${state.cues.length} reviewed cue events ready for local playback; this is not speech recognition.`,'success');}catch(e){state.cues=null;fail(e.message);}});
    $('speechPlayer').addEventListener('play',()=>{stopCueLoop();syncCuePose()});$('speechPlayer').addEventListener('pause',stopCueLoop);$('speechPlayer').addEventListener('ended',()=>{stopCueLoop();selectPose('X');});$('speechPlayer').addEventListener('seeked',()=>{if(state.cues&&state.sprites)syncCuePose();});
    window.addEventListener('pagehide',()=>{stopCueLoop();revokeUrl('videoUrl');revokeUrl('audioUrl');});
  }
  init();
})();