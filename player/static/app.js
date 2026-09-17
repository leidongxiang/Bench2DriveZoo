const state={routes:[],runs:[],trash:[],system:null,selected:null,index:null,frame:0,playing:false,timer:null,mode:'preset',deleteId:null,map:null,mapTown:null,mapRequestToken:0,customPoints:[],customValidation:null,validationToken:0,presetGeometry:null,currentData:null,evaluationStatuses:{},performance:{}};
const $=id=>document.getElementById(id);
const cameraNames={rgb_front_left:'前左',rgb_front:'前视',rgb_front_right:'前右',rgb_back_left:'后左',rgb_back:'后视',rgb_back_right:'后右'};
const cameraOrder=['rgb_front_left','rgb_front','rgb_front_right','rgb_back_left','rgb_back','rgb_back_right'];
const commandNames=['左转','右转','直行','保持车道','向左变道','向右变道'];

async function api(path,options={}){const response=await fetch(path,{headers:{'Content-Type':'application/json'},...options});const body=await response.json().catch(()=>({}));if(!response.ok)throw new Error(body.error||`HTTP ${response.status}`);return body}
function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))}
function formatSize(bytes=0){if(!bytes)return '—';const units=['B','KB','MB','GB','TB'];let value=bytes,index=0;while(value>=1024&&index<units.length-1){value/=1024;index++}return `${value.toFixed(index>1?1:0)} ${units[index]}`}
function statusName(status){return ({ready:'可播放',running:'推理中',queued:'排队中',finalizing:'整理中',failed:'失败',incomplete:'未完成',interrupted:'已中断'})[status]||status}
function setConnection(text,error=false){$('connection').textContent=text;$('connection').classList.toggle('error',error)}

async function loadProgress(){try{const response=await fetch('/progress.json',{cache:'no-store'});if(!response.ok)return {};const data=await response.json();return Date.now()/1000-data.updatedAt<30?data.runs||{}:{}}catch(error){return {}}}
async function loadData(){try{const [routeData,runData,trashData,systemData,progress]=await Promise.all([api('/api/routes'),api('/api/runs'),api('/api/trash'),api('/api/system'),loadProgress()]);state.routes=routeData.routes;state.runs=runData.runs.map(run=>({...run,...(progress[run.id]||{})}));await Promise.all(state.runs.filter(run=>run.status==='ready'&&!(run.id in state.evaluationStatuses)).map(async run=>{try{const index=await api(`/api/runs/${encodeURIComponent(run.id)}/index`);state.evaluationStatuses[run.id]=index.result||null;if(index.frameCount){const last=await api(`/api/runs/${encodeURIComponent(run.id)}/frame/${index.frameCount-1}.json`);state.performance[run.id]=Number(last.modelFpsAvg)||null}}catch(error){state.evaluationStatuses[run.id]=null}}));state.trash=trashData.trash;state.system=systemData;renderTownOptions();renderRoutes();renderRuns();renderTrash();renderSystem();setConnection('服务已连接');}catch(error){setConnection(error.message,true)}}
function renderTownOptions(){const towns=[...new Set(state.routes.map(route=>route.town))].sort();const routeTown=$('route-town'),mapTown=$('town');const selectedFilter=routeTown.value,selectedMap=mapTown.value;routeTown.innerHTML='<option value="">全部 Town</option>'+towns.map(town=>`<option>${escapeHtml(town)}</option>`).join('');mapTown.innerHTML=towns.map(town=>`<option>${escapeHtml(town)}</option>`).join('');if(towns.includes(selectedFilter))routeTown.value=selectedFilter;if(towns.includes(selectedMap))mapTown.value=selectedMap;else if(towns.includes('Town12'))mapTown.value='Town12'}
function renderRoutes(){const select=$('route-select');const previous=select.value,town=$('route-town').value,query=$('route-search').value.trim().toLowerCase();const routes=state.routes.filter(route=>(!town||route.town===town)&&(!query||`${route.id} ${route.town} ${route.scenarios.join(' ')}`.toLowerCase().includes(query)));select.innerHTML=routes.map(route=>`<option value="${escapeHtml(route.id)}">${escapeHtml(route.town)} · Route ${escapeHtml(route.id)} · ${escapeHtml(route.scenarios.join(', ')||'无场景')}</option>`).join('');if(routes.some(route=>route.id===previous))select.value=previous;renderRouteFacts()}
function renderRouteFacts(){const route=state.routes.find(item=>item.id===$('route-select').value);$('route-facts').innerHTML=route?`<strong>${escapeHtml(route.town)}</strong><br>${route.waypointCount} 个路径点<br>${escapeHtml(route.scenarios.join(' · ')||'无注入场景')}`:'没有可用路线';if(route)loadPresetMap(route.id);else clearPresetMap()}
function renderSystem(){const info=state.system;if(!info)return;$('system-status').textContent=`Web ${info.web.port} · CARLA ${info.carla.port} · ${info.routeCount} 路线`;const disk=info.disk,used=disk.total-disk.free;$('disk-status').textContent=`磁盘 ${formatSize(disk.free)} 可用 / ${formatSize(disk.total)} 总量（已用 ${Math.round(used/disk.total*100)}%）`}
function renderTrash(){$('trash-count').textContent=state.trash.length?`(${state.trash.length})`:'';$('trash-list').innerHTML=state.trash.length?state.trash.map(item=>`<article class="trash-item"><div><strong>${escapeHtml(item.name)}</strong><span>${formatSize(item.sizeBytes)} · ${new Date(item.deletedAt*1000).toLocaleString()}</span></div><div><button data-trash-action="restore" data-trash-id="${escapeHtml(item.id)}">恢复</button><button class="danger" data-trash-action="purge" data-trash-id="${escapeHtml(item.id)}">永久删除</button></div></article>`).join(''):'<div class="empty-state"><strong>回收站为空</strong><span>从结果列表删除的项目会先移动到这里。</span></div>'}
function simulationFps(result){const meta=result?.meta;if(!meta||!Number(meta.duration_system)||!Number(meta.duration_game))return null;return 20*Number(meta.duration_game)/Number(meta.duration_system)}
function renderRuns(){const list=$('run-list');if(!state.runs.length){list.innerHTML='<p class="hint">尚无推理结果。</p>';return}list.innerHTML=state.runs.map(run=>{const active=['queued','running','finalizing'].includes(run.status);const evaluation=state.evaluationStatuses[run.id];const incomplete=run.status==='ready'&&evaluation?.status&&evaluation.status!=='Completed';const badgeText=run.partial?(run.stopRequested?'已停止可回放':'中断可回放'):incomplete?'异常可播放':statusName(run.status);const badgeClass=run.partial||incomplete?'failed':run.status;const message=run.partial?escapeHtml(run.message||'评测未完成'):incomplete?`评测未完成：${escapeHtml(evaluation.status)} · 路线完成率 ${Number(evaluation.scores?.score_route||0).toFixed(2)}%`:run.message?escapeHtml(run.message):'';const modelFps=state.performance[run.id];const simFps=simulationFps(evaluation);const fpsText=[modelFps?`模型平均 ${modelFps.toFixed(2)} FPS`:null,simFps?`仿真 ${simFps.toFixed(2)} FPS`:null].filter(Boolean).join(" · ");const meters=Number.isFinite(run.distanceMeters)?` · 已行驶 ${(run.distanceMeters/1000).toFixed(2)} km`:'';const progress=active?`<div class="run-progress-label">已生成 ${run.frameCount||0} 帧${meters}</div><progress class="run-progress" aria-label="推理中，已生成 ${run.frameCount||0} 帧"></progress>`:'';return `<article class="run-item ${run.id===state.selected?'selected':''}" data-run="${escapeHtml(run.id)}"><div class="run-top"><span class="run-name">${escapeHtml(run.label||run.runName)}</span><span class="badge ${escapeHtml(badgeClass)}">${escapeHtml(badgeText)}</span></div><div class="run-meta"><span>${run.frameCount||0} 帧</span><span>${formatSize(run.sizeBytes)}</span>${fpsText?`<span>${fpsText}</span>`:""}</div>${progress}${message?`<div class="run-message">${message}</div>`:""}<div class="run-actions">${run.status==='ready'?'<button data-action="open">打开</button>':''}${run.status==='running'&&run.managed?'<button data-action="stop">停止</button>':''}<button class="delete" data-action="delete">删除</button></div></article>`}).join('')}

async function openRun(runId){pause();try{state.index=await api(`/api/runs/${encodeURIComponent(runId)}/index`);state.selected=runId;state.frame=0;$('empty-player').hidden=true;$('player').hidden=false;$('player-title').textContent=state.index.label;$('timeline').max=Math.max(0,state.index.frameCount-1);const result=state.index.result;const score=result?.scores?.score_composed;$('score').textContent=score==null?'无评分':`驾驶得分 ${Number(score).toFixed(2)}`;$('simulation-fps-value').textContent=simulationFps(result)?.toFixed(2)||'—';buildCameras();renderRuns();await renderFrame()}catch(error){setConnection(error.message,true)}}
function buildCameras(){$('cameras').innerHTML=cameraOrder.filter(channel=>state.index.channels.includes(channel)).map(channel=>`<figure class="camera"><div class="frame-media"><img id="image-${channel}" alt="${cameraNames[channel]}"><canvas id="overlay-${channel}" width="1600" height="900"></canvas></div><figcaption>${cameraNames[channel]}</figcaption></figure>`).join('')}
function imageUrl(channel,frame){return `/api/runs/${encodeURIComponent(state.selected)}/image/${channel}/${frame}.png`}
async function renderFrame(){if(!state.index)return;const token=state.frame;const channels=state.index.channels;for(const channel of channels){const image=channel==='bev'?$('bev'):$(`image-${channel}`);image.src=imageUrl(channel,token)}$('timeline').value=token;$('frame-label').textContent=`${token+1} / ${state.index.frameCount}`;try{const data=await api(`/api/runs/${encodeURIComponent(state.selected)}/frame/${token}.json`);if(token!==state.frame)return;state.currentData=data;$('speed-value').textContent=formatNumber(data.speed,'m/s');$('steer-value').textContent=formatNumber(data.steer);$('throttle-value').textContent=formatNumber(data.throttle);$('brake-value').textContent=formatNumber(data.brake);$('command-value').textContent=commandNames[data.command]||'未知';$('model-fps-value').textContent=Number(data.modelFps)?.toFixed(2)&&Number(data.modelFps)>0?Number(data.modelFps).toFixed(2):'—';$('command-options').innerHTML=commandNames.map((name,index)=>`<span class="${index===data.command?'active':''}">${name}</span>`).join('');$('frame-json').textContent=JSON.stringify(data,null,2);drawPlan(data.plan||[]);renderOverlays(data)}catch(error){pause();setConnection(error.message,true)}prefetch(token+1);prefetch(token+2)}
function formatNumber(value,unit=''){return Number.isFinite(Number(value))?`${Number(value).toFixed(2)} ${unit}`:'—'}
function prefetch(frame){if(!state.index||frame>=state.index.frameCount)return;for(const channel of state.index.channels){const image=new Image();image.src=imageUrl(channel,frame)}}
function drawPlan(points){const canvas=$('plan'),ctx=canvas.getContext('2d'),width=canvas.width,height=canvas.height;ctx.clearRect(0,0,width,height);ctx.strokeStyle='#cbd2ce';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(width/2,8);ctx.lineTo(width/2,height-12);ctx.moveTo(10,height-18);ctx.lineTo(width-10,height-18);ctx.stroke();if(!points.length)return;const maxY=Math.max(10,...points.map(point=>Math.abs(point[1]))),maxX=Math.max(5,...points.map(point=>Math.abs(point[0])));ctx.strokeStyle='#d94b2b';ctx.lineWidth=4;ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();ctx.moveTo(width/2,height-18);for(const point of points){ctx.lineTo(width/2+(point[0]/maxX)*(width*.4),height-18-(point[1]/maxY)*(height-30))}ctx.stroke()}
function drawOverlayBoxes(ctx,items,color,bev=false){ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=3;ctx.font='bold 18px sans-serif';for(const item of items||[]){const [x1,y1,x2,y2]=item.box||[];if(![x1,y1,x2,y2].every(Number.isFinite))continue;const points=item.corners;if(Array.isArray(points)&&points.length===(bev?8:16)&&points.every(Number.isFinite)){const edges=bev?[[0,1],[1,2],[2,3],[3,0]]:[[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];ctx.beginPath();for(const [a,b] of edges){ctx.moveTo(points[a*2],points[a*2+1]);ctx.lineTo(points[b*2],points[b*2+1])}ctx.stroke()}else{ctx.strokeRect(x1,y1,x2-x1,y2-y1)}const label=`${item.label||'目标'}${Number.isFinite(item.score)?` ${item.score.toFixed(2)}`:''}`;ctx.fillText(label,Math.max(2,x1+3),Math.max(20,y1-5))}}
const BEV_SCALE=8;
const BEV_ORIGIN=[256,256];
const bevPixel=point=>[BEV_ORIGIN[0]+Number(point[0])*BEV_SCALE,BEV_ORIGIN[1]-Number(point[1])*BEV_SCALE];

function drawVectorBev(canvas,lines){
  const ctx=canvas.getContext('2d');
  ctx.fillStyle='#fff';ctx.fillRect(0,0,512,512);
  ctx.strokeStyle='#e8edf1';ctx.lineWidth=1;
  for(let meters=-30;meters<=30;meters+=10){
    const [x,y]=bevPixel([0,meters]);ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(512,y);ctx.stroke();
  }
  for(let meters=-30;meters<=30;meters+=10){
    const [x,y]=bevPixel([meters,0]);ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,512);ctx.stroke();
  }
  ctx.strokeStyle='#b9c7cf';ctx.beginPath();ctx.moveTo(256,0);ctx.lineTo(256,512);ctx.stroke();
  const colors=['#93a6ba','#4169e1','#708090','#6495ed','#c084fc','#efb35a'];
  for(const line of lines||[]){
    if(!Array.isArray(line.points)||line.points.length<2)continue;
    ctx.strokeStyle=colors[line.label]||'#64748b';ctx.lineWidth=2;ctx.beginPath();
    line.points.forEach((point,index)=>{const [x,y]=bevPixel(point);index?ctx.lineTo(x,y):ctx.moveTo(x,y)});
    ctx.stroke();
  }
  ctx.strokeStyle='#15803d';ctx.lineWidth=3;ctx.strokeRect(256-8,256-17,16,34);
  ctx.fillStyle='#243746';ctx.font='bold 15px sans-serif';ctx.fillText('VAD 矢量 BEV',12,23);
}

function drawVectorBoxes(ctx,items,color,dashed=false){
  ctx.strokeStyle=color;ctx.fillStyle=color;ctx.lineWidth=dashed?1.5:2.5;ctx.setLineDash(dashed?[5,4]:[]);
  for(const item of items||[]){
    if(!Array.isArray(item.xy)||item.xy.length!==4)continue;
    ctx.beginPath();item.xy.forEach((point,index)=>{const [x,y]=bevPixel(point);index?ctx.lineTo(x,y):ctx.moveTo(x,y)});
    ctx.closePath();ctx.stroke();
  }
  ctx.setLineDash([]);
}

function drawVectorTrajectories(ctx,items){
  const colors=['#16a34a','#22c55e','#eab308','#f97316','#ef4444','#a855f7'];
  ctx.lineWidth=1.6;
  for(const item of items||[]){
    if(!Array.isArray(item.traj)||!Array.isArray(item.xy)||item.score<0.4)continue;
    const center=[item.xy.reduce((sum,point)=>sum+point[0],0)/4,item.xy.reduce((sum,point)=>sum+point[1],0)/4];
    item.traj.forEach((mode,index)=>{
      if(!Array.isArray(mode)||!mode.length)return;
      ctx.strokeStyle=colors[index%colors.length];ctx.beginPath();
      let [x,y]=bevPixel(center);ctx.moveTo(x,y);
      for(const point of mode){[x,y]=bevPixel(point);ctx.lineTo(x,y)}
      ctx.stroke();
    });
  }
}

function drawBevPlan(ctx,points){
  if(!points.length)return;
  ctx.strokeStyle='#e53935';ctx.lineWidth=3;ctx.beginPath();
  let [x,y]=bevPixel([0,0]);ctx.moveTo(x,y);
  for(const point of points){if(!Array.isArray(point)||point.length<2)continue;[x,y]=bevPixel(point);ctx.lineTo(x,y)}
  ctx.stroke();
  ctx.fillStyle='#e53935';for(const point of points){if(!Array.isArray(point)||point.length<2)continue;[x,y]=bevPixel(point);ctx.beginPath();ctx.arc(x,y,2.6,0,Math.PI*2);ctx.fill()}
}

function renderOverlays(data){
  const overlays=data.overlays;
  const enabledPred=$('show-pred').checked,enabledGt=$('show-gt').checked;
  const vector=overlays?.vectorBev===true;
  $('overlay-status').textContent=overlays?.error?`框数据不可用：${overlays.error}`:vector?'橙色：推理框 · 青色：GT 框 · 彩色：目标未来轨迹':overlays?'旧结果未保存矢量 BEV 与目标轨迹':'此结果未保存 GT/推理框，重新推理后可显示';
  for(const channel of cameraOrder){
    const canvas=$(`overlay-${channel}`);if(!canvas)continue;
    const ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
    if(enabledGt)drawOverlayBoxes(ctx,overlays?.cameras?.[channel]?.gt,'#22d3ee');
    if(enabledPred)drawOverlayBoxes(ctx,overlays?.cameras?.[channel]?.pred,'#fb923c');
  }
  $('bev').hidden=vector;$('bev-vector').hidden=!vector;
  const canvas=$('overlay-bev'),ctx=canvas.getContext('2d');ctx.clearRect(0,0,canvas.width,canvas.height);
  if(vector){
    drawVectorBev($('bev-vector'),overlays.map);
    if(enabledPred)drawVectorTrajectories(ctx,overlays.bev?.pred);
    if(enabledGt)drawVectorBoxes(ctx,overlays.bev?.gt,'#22d3ee',true);
    if(enabledPred)drawVectorBoxes(ctx,overlays.bev?.pred,'#fb923c');
    drawBevPlan(ctx,data.plan||[]);
    return;
  }
  if(enabledGt)drawOverlayBoxes(ctx,overlays?.bev?.gt,'#22d3ee',true);
  if(enabledPred)drawOverlayBoxes(ctx,overlays?.bev?.pred,'#fb923c',true);
  const points=data.plan||[],scale=canvas.width/(100*Math.tan(25*Math.PI/180));
  if(points.length){ctx.strokeStyle='#f43f5e';ctx.lineWidth=4;ctx.lineCap='round';ctx.lineJoin='round';ctx.beginPath();ctx.moveTo(256,256);for(const point of points){if(Array.isArray(point)&&point.length>=2)ctx.lineTo(256+Number(point[0])*scale,256-Number(point[1])*scale)}ctx.stroke();ctx.fillStyle='#f43f5e';ctx.fillRect(252,252,8,8)}
}
async function toggleFrameFullscreen(element){try{if(document.fullscreenElement)await document.exitFullscreen();else await element.requestFullscreen()}catch(error){setConnection(`无法进入全屏：${error.message}`,true)}}
async function loadTownMap(){const town=$('town').value;if(!town)return;const token=++state.mapRequestToken;$('map-loading').hidden=false;try{const map=await api(`/api/maps/${encodeURIComponent(town)}`);if(token!==state.mapRequestToken||$('town').value!==town)return;state.map=map;state.mapTown=town;state.customPoints=[];state.customValidation=null;drawTownMap();renderWaypointSummary()}catch(error){if(token===state.mapRequestToken)setConnection(error.message,true)}finally{if(token===state.mapRequestToken)$('map-loading').hidden=true}}
function projectionFor(canvas,map){if(!map)return null;const bounds=map.bounds,padding=30,spanX=Math.max(1,bounds.maxX-bounds.minX),spanY=Math.max(1,bounds.maxY-bounds.minY),scale=Math.min((canvas.width-padding*2)/spanX,(canvas.height-padding*2)/spanY),drawWidth=spanX*scale,drawHeight=spanY*scale,offsetX=(canvas.width-drawWidth)/2,offsetY=(canvas.height-drawHeight)/2;return {toPixel:point=>[offsetX+(point[0]-bounds.minX)*scale,offsetY+(bounds.maxY-point[1])*scale],toWorld:(x,y)=>[bounds.minX+(x-offsetX)/scale,bounds.maxY-(y-offsetY)/scale]}}
function drawRoadMap(canvas,map){const ctx=canvas.getContext('2d'),projection=projectionFor(canvas,map);ctx.fillStyle='#e8ece9';ctx.fillRect(0,0,canvas.width,canvas.height);if(!projection)return null;ctx.strokeStyle='#65777e';ctx.lineWidth=1.8;ctx.lineCap='round';for(const line of map.polylines){ctx.beginPath();line.points.forEach((point,index)=>{const [x,y]=projection.toPixel(point);index?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke()}return projection}
function mapProjection(){return projectionFor($('town-map'),state.map)}
function drawTownMap(){const canvas=$('town-map'),ctx=canvas.getContext('2d'),projection=drawRoadMap(canvas,state.map);if(!projection)return;if(state.customPoints.length){state.customPoints.forEach((point,index)=>{const [x,y]=projection.toPixel([point.x,point.y]);ctx.fillStyle=index===0?'#36a57f':index===state.customPoints.length-1?'#e69b25':'#fff';ctx.beginPath();ctx.arc(x,y,8,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#25333a';ctx.lineWidth=1;ctx.stroke();ctx.fillStyle='#172026';ctx.font='bold 11px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(String(index+1),x,y)})}}
async function loadPresetMap(routeId){const requested=routeId;$('preset-map-loading').hidden=false;try{const geometry=await api(`/api/routes/${encodeURIComponent(routeId)}/geometry`);if($('route-select').value!==requested)return;state.presetGeometry=geometry;drawPresetMap()}catch(error){setConnection(error.message,true)}finally{if($('route-select').value===requested)$('preset-map-loading').hidden=true}}
function clearPresetMap(){state.presetGeometry=null;const canvas=$('preset-map'),ctx=canvas.getContext('2d');ctx.fillStyle='#e8ece9';ctx.fillRect(0,0,canvas.width,canvas.height);$('preset-map-loading').hidden=true}
function drawPresetMap(){if(!state.presetGeometry)return;const canvas=$('preset-map'),ctx=canvas.getContext('2d'),projection=drawRoadMap(canvas,state.presetGeometry.map);if(!projection)return;ctx.strokeStyle='#d94b2b';ctx.lineWidth=6;ctx.lineJoin='round';ctx.beginPath();state.presetGeometry.points.forEach((point,index)=>{const [x,y]=projection.toPixel(point);index?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();const endpoints=[state.presetGeometry.points[0],state.presetGeometry.points.at(-1)];endpoints.forEach((point,index)=>{const [x,y]=projection.toPixel(point);ctx.fillStyle=index?'#e69b25':'#36a57f';ctx.beginPath();ctx.arc(x,y,9,0,Math.PI*2);ctx.fill();ctx.strokeStyle='#25333a';ctx.stroke()})}
async function toggleFullscreen(element){const actions=$('custom-map-actions');if(document.fullscreenElement){await document.exitFullscreen()}else if(element.requestFullscreen){if(element.contains($('town-map')))element.append(actions);await element.requestFullscreen()}}
function resizeMapCanvases(){for(const canvas of [$('preset-map'),$('town-map')]){const fullscreen=document.fullscreenElement?.contains(canvas);if(fullscreen){const editor=canvas.closest('.map-editor'),styles=getComputedStyle(editor),width=editor.clientWidth-parseFloat(styles.paddingLeft)-parseFloat(styles.paddingRight),height=editor.clientHeight-parseFloat(styles.paddingTop)-parseFloat(styles.paddingBottom);canvas.width=Math.max(320,Math.floor(width));canvas.height=Math.max(240,Math.floor(height))}else{canvas.width=1000;canvas.height=620}}drawPresetMap();drawTownMap()}
function nearestMapZ(x,y){let nearest=null,distance=Infinity;for(const point of state.map.elevationPoints||[]){const candidate=(point[0]-x)**2+(point[1]-y)**2;if(candidate<distance){distance=candidate;nearest=point}}return nearest?nearest[2]:0}
async function addMapPoint(event){if(!state.map)return;const canvas=$('town-map'),rect=canvas.getBoundingClientRect(),pixelX=(event.clientX-rect.left)*canvas.width/rect.width,pixelY=(event.clientY-rect.top)*canvas.height/rect.height,[x,y]=mapProjection().toWorld(pixelX,pixelY),previousPoints=state.customPoints.slice(),previousValidation=state.customValidation;state.customPoints.push({x:Number(x.toFixed(2)),y:Number(y.toFixed(2)),z:Number(nearestMapZ(x,y).toFixed(2))});state.customValidation=null;drawTownMap();renderWaypointSummary('正在查找全图最近 driving lane 并规划车道路径…');const result=await validateCustomRoute();if(!result){state.customPoints=previousPoints;state.customValidation=previousValidation;drawTownMap()}}
async function validateCustomRoute(){if(!state.customPoints.length){state.customValidation=null;renderWaypointSummary();return null}const token=++state.validationToken;const rawPoints=state.customPoints.map(({x,y,z})=>({x,y,z}));try{const result=await api('/api/routes/validate-custom',{method:'POST',body:JSON.stringify({town:$('town').value,waypoints:rawPoints})});if(token!==state.validationToken)return null;state.customValidation=result;state.customPoints=result.points;drawTownMap();renderWaypointSummary();return result}catch(error){if(token===state.validationToken){state.customValidation=null;renderWaypointSummary(`该点未加入：${error.message}`)}return null}}
function renderWaypointSummary(message=''){if(message){$('waypoint-summary').textContent=message;return}if(!state.customPoints.length){$('waypoint-summary').textContent='尚未选择路径点';return}const lines=state.customPoints.map((point,index)=>{const metadata=point.roadId==null?'':` · road ${point.roadId} / section ${point.sectionId} / lane ${point.laneId} · 偏移 ${point.distance.toFixed(2)} m${point.distance>8?' ⚠':''}`;return `${index+1}. x ${point.x.toFixed(2)} · y ${point.y.toFixed(2)} · z ${point.z.toFixed(2)}${metadata}`});if(state.customValidation&&state.customValidation.segments.length){lines.push('',...state.customValidation.segments.map(segment=>`${segment.from+1} → ${segment.to+1}：${segment.connected?'道路网络连通':'不连通'}${segment.connected?'':' ⚠'}`),`道路拓扑检查：${state.customValidation.valid?'通过；实际轨迹由 CARLA 生成':'未通过；实际轨迹由 CARLA 生成'}`)}$('waypoint-summary').textContent=lines.join('\n')}
function play(){if(!state.index)return;if(state.frame>=state.index.frameCount-1)state.frame=0;state.playing=true;$('play').textContent='暂停';schedule()}
function schedule(){clearTimeout(state.timer);if(!state.playing)return;const fps=state.index.fps*Number($('speed').value);state.timer=setTimeout(async()=>{if(state.frame>=state.index.frameCount-1){pause();return}state.frame++;await renderFrame();schedule()},1000/fps)}
function pause(){state.playing=false;clearTimeout(state.timer);$('play').textContent='播放'}

document.querySelectorAll('.tab').forEach(button=>button.addEventListener('click',()=>{document.querySelectorAll('.tab').forEach(item=>item.classList.toggle('active',item===button));document.querySelectorAll('.view').forEach(view=>view.classList.toggle('active',view.id===`${button.dataset.view}-view`))}));
document.querySelectorAll('.mode').forEach(button=>button.addEventListener('click',()=>{state.mode=button.dataset.mode;document.querySelectorAll('.mode').forEach(item=>item.classList.toggle('active',item===button));document.querySelectorAll('.mode-panel').forEach(panel=>panel.classList.toggle('active',panel.dataset.panel===state.mode));if(state.mode==='custom'&&state.mapTown!==$('town').value)loadTownMap()}));
$('route-select').addEventListener('change',renderRouteFacts);$('preset-fullscreen').addEventListener('click',()=>toggleFullscreen($('preset-map-editor')));$('custom-fullscreen').addEventListener('click',()=>toggleFullscreen($('town-map').closest('.map-editor')));document.addEventListener('fullscreenchange',()=>{if(!document.fullscreenElement)$('town').closest('.map-toolbar').append($('custom-map-actions'));requestAnimationFrame(resizeMapCanvases)});window.addEventListener('resize',()=>{if(document.fullscreenElement)requestAnimationFrame(resizeMapCanvases)});$('refresh').addEventListener('click',loadData);$('play').addEventListener('click',()=>state.playing?pause():play());$('previous').addEventListener('click',()=>{pause();state.frame=Math.max(0,state.frame-1);renderFrame()});$('next').addEventListener('click',()=>{pause();state.frame=Math.min(state.index.frameCount-1,state.frame+1);renderFrame()});$('timeline').addEventListener('input',event=>{pause();state.frame=Number(event.target.value);renderFrame()});$('speed').addEventListener('change',()=>{if(state.playing)schedule()});
$('route-town').addEventListener('change',renderRoutes);$('route-search').addEventListener('input',renderRoutes);$('town').addEventListener('change',loadTownMap);$('town-map').addEventListener('click',addMapPoint);$('undo-point').addEventListener('click',()=>{state.customPoints.pop();state.customValidation=null;drawTownMap();renderWaypointSummary();validateCustomRoute()});$('clear-points').addEventListener('click',()=>{state.validationToken++;state.customPoints=[];state.customValidation=null;drawTownMap();renderWaypointSummary()});
$('xml-file').addEventListener('change',async event=>{const file=event.target.files[0];if(file)$('route-xml').value=await file.text()});
$('fullscreen-visuals').addEventListener('click',()=>toggleFrameFullscreen($('player')));document.addEventListener('fullscreenchange',()=>$('fullscreen-visuals').textContent=document.fullscreenElement?'退出全屏':'画面全屏');for(const id of ['show-pred','show-gt'])$(id).addEventListener('change',()=>{if(state.currentData)renderOverlays(state.currentData)});
$('run-list').addEventListener('click',async event=>{const article=event.target.closest('[data-run]');if(!article)return;const runId=article.dataset.run;const action=event.target.dataset.action;if(action==='open')return openRun(runId);if(action==='stop'){try{await api(`/api/runs/${encodeURIComponent(runId)}/stop`,{method:'POST',body:'{}'});loadData()}catch(error){setConnection(error.message,true)}return}if(action==='delete'){const run=state.runs.find(item=>item.id===runId);state.deleteId=runId;$('delete-message').textContent=`${run.label||run.runName}，占用 ${formatSize(run.sizeBytes)}。结果将移入输出目录的 .trash，可由管理员恢复。`;$('delete-dialog').showModal()}});
$('cancel-delete').addEventListener('click',()=>$('delete-dialog').close());$('confirm-delete').addEventListener('click',async()=>{try{await api(`/api/runs/${encodeURIComponent(state.deleteId)}`,{method:'DELETE'});if(state.selected===state.deleteId){pause();state.selected=null;state.index=null;$('player').hidden=true;$('empty-player').hidden=false}$('delete-dialog').close();loadData()}catch(error){setConnection(error.message,true)}});
$('trash-list').addEventListener('click',async event=>{const button=event.target.closest('[data-trash-action]');if(!button)return;const id=button.dataset.trashId,action=button.dataset.trashAction;if(action==='purge'&&!confirm('永久删除后无法恢复，确定继续？'))return;try{if(action==='restore')await api(`/api/trash/${encodeURIComponent(id)}/restore`,{method:'POST',body:'{}'});else await api(`/api/trash/${encodeURIComponent(id)}`,{method:'DELETE'});await loadData()}catch(error){setConnection(error.message,true)}});
$('run-form').addEventListener('submit',async event=>{event.preventDefault();const errorBox=$('form-error');errorBox.hidden=true;let payload={mode:state.mode};try{if(state.mode==='preset')payload.routeId=$('route-select').value;else if(state.mode==='custom'){if(state.customPoints.length<2)throw new Error('请在地图上至少选择起点和终点');const validation=await validateCustomRoute();if(!validation)throw new Error('道路吸附校验未完成');if(!validation.valid)throw new Error('存在不连通的路线分段，请调整坐标点');payload.town=$('town').value;payload.waypoints=validation.points}else payload.xml=$('route-xml').value;await api('/api/runs',{method:'POST',body:JSON.stringify(payload)});document.querySelector('[data-view="runs"]').click();await loadData()}catch(error){errorBox.textContent=error.message;errorBox.hidden=false}});

loadData();setInterval(()=>{if(state.runs.some(run=>['queued','running','finalizing'].includes(run.status)))loadData()},5000);
