const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const escapeHtml=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const timeLabel=s=>{s=Math.max(0,Math.floor(s));return `${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`};
const statusNames={draft:'待上传',ready:'待分析',running:'分析中',uploading:'上传中',completed:'已完成',failed:'分析失败',interrupted:'已中断'};
let projects=[],current=null,statistics=null,health=null,activeTab='setup',drawing=null,points=[],line=null,roi=[0,0,1,1],eventOffset=0,eventTotal=0,pollBusy=false,uploading=false,editing=false;
async function api(url,options={}){
  const r=await fetch(url,{...options,headers:{...(options.body?{'Content-Type':'application/json'}:{}),...options.headers}});
  const data=await r.json();if(!r.ok)throw new Error(data.error||'请求失败');return data;
}
const post=(url,body={})=>api(url,{method:'POST',body:JSON.stringify(body)});
function toast(text){$('#toast').textContent=text;$('#toast').hidden=false;clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('#toast').hidden=true,6500)}
async function busy(button,fn,label='处理中…'){
  const old=button.textContent;button.disabled=true;button.textContent=label;
  try{return await fn()}catch(e){toast(e.message)}finally{button.disabled=false;button.textContent=old}
}
async function refreshProjects(){projects=await api('/api/projects');renderProjects()}
function renderProjects(){
  $('#projectCount').textContent=projects.length;
  $('#mobileProjectSelect').innerHTML=projects.length?projects.map(p=>`<option value="${p.id}" ${current?.id===p.id?'selected':''}>${escapeHtml(p.name)}</option>`).join(''):'<option value="">暂无项目</option>';
  $('#projectList').innerHTML=projects.length?projects.map(p=>`<button class="project-item ${current?.id===p.id?'active':''}" data-project="${p.id}"><span class="project-icon">▤</span><div><strong>${escapeHtml(p.name)}</strong><small>${escapeHtml(p.meta['拍摄日期']||'未填日期')} · ${statusNames[p.status]||p.status}</small></div></button>`).join(''):'<div class="empty-side">还没有调研项目<br>从第一段街景开始。</div>';
  $$('[data-project]').forEach(b=>b.onclick=()=>selectProject(b.dataset.project).catch(e=>toast(e.message)));
}
$('#mobileProjectSelect').onchange=e=>{if(e.target.value)selectProject(e.target.value).catch(err=>toast(err.message))};
async function selectProject(id){
  if(uploading){toast('请等待视频上传结束');return}
  current=await api('/api/projects/'+id);localStorage.setItem('street-project',id);history.replaceState(null,'',`/?project=${id}`);
  line=current.settings?.line||null;roi=current.settings?.roi||[0,0,1,1];drawing=null;points=[];eventOffset=0;
  $('#videoStage').classList.remove('drawing');
  $('#welcome').hidden=true;$('#workspace').hidden=false;$('#exportPdf').hidden=false;
  $('#pageTitle').textContent=current.name;$('#pageSubtitle').textContent='记录眼前的客流，为下一步经营判断收集依据。';
  $('#projectMeta').innerHTML=Object.entries(current.meta).filter(([,v])=>v).slice(0,6).map(([k,v])=>`<span>${escapeHtml(k)}：${escapeHtml(v)}</span>`).join('');
  const hasVideo=!!current.video_url;
  $('#dropZone').hidden=hasVideo;$('#videoBox').hidden=!hasVideo;
  $('#setupVideo').removeAttribute('src');$('#reviewVideo').removeAttribute('src');
  if(hasVideo){$('#setupVideo').src=current.video_url;$('#reviewVideo').src=current.video_url;$('#videoInfo').textContent=`${current.width} × ${current.height} · ${current.fps.toFixed(1)} fps · 时长 ${timeLabel(current.duration)}`}
  $('#csvLink').href=`/api/projects/${id}/csv`;renderTask();renderProjects();
  await refreshStats();await loadEvents();await loadChat();renderReport();
  switchTab(hasVideo&&current.status==='completed'?'overview':'setup');
}
function switchTab(tab){activeTab=tab;if(tab!=='setup')$('#setupVideo').pause();if(tab!=='review')$('#reviewVideo').pause();$$('[data-tab]').forEach(b=>{b.classList.toggle('active',b.dataset.tab===tab);b.setAttribute('aria-selected',b.dataset.tab===tab)});$$('.tab-panel').forEach(p=>p.hidden=p.id!==`tab-${tab}`);if(tab==='setup')requestAnimationFrame(sizeCanvas);if(tab==='review')loadEvents().catch(e=>toast(e.message));}
$$('[data-tab]').forEach(b=>b.onclick=()=>switchTab(b.dataset.tab));
function renderTask(){
  const p=current;$('#taskStatus').hidden=!['running','completed','failed','interrupted','uploading'].includes(p.status);
  $('#taskTitle').textContent=statusNames[p.status];$('#taskPercent').textContent=p.progress.toFixed(1)+'%';$('#taskBar').style.width=p.progress+'%';$('#taskMessage').textContent=p.message;
  $('#startAnalysis').hidden=p.status==='running';$('#stopAnalysis').hidden=p.status!=='running';
  $('#startAnalysis').disabled=!p.video_url||uploading;
  $('#drawLine').disabled=p.status==='running';$('#drawRoi').disabled=p.status==='running';$('#resetRoi').disabled=p.status==='running';
}
async function refreshStats(){if(!current)return;statistics=await api(`/api/projects/${current.id}/stats`);renderStats()}
function renderStats(){
  const s=statistics;
  $('#metrics').innerHTML=[['总通行人次',s.total.toLocaleString(),'每次有效过线计一次'],['方向 A',s.a.toLocaleString(),'到达计数线正侧'],['方向 B',s.b.toLocaleString(),'到达计数线负侧'],['平均每分钟',s.per_minute,'有效分析 '+timeLabel(s.effective_seconds)]].map(([label,n,note])=>`<article class="metric"><span>${label}</span><strong>${n}</strong><small>${note}</small></article>`).join('');
  renderChart();const percent=s.total?Math.round(s.a/s.total*100):0;
  $('#directionChart').innerHTML=`<div class="donut" style="background:conic-gradient(#618a65 0 ${percent}%,#d6b38a ${percent}% 100%)"><strong>${s.total?percent+'%':'—'}</strong></div><div class="direction-detail"><span><i class="dot green"></i>方向 A</span><strong>${s.a} 人次</strong></div><div class="direction-detail"><span><i class="dot orange"></i>方向 B</span><strong>${s.b} 人次</strong></div>`;
  $('#attributes').innerHTML=s.attributes.map(a=>`<div class="attribute">${escapeHtml(a.name)}<small>${a.status} · 未生成统计</small></div>`).join('');
  $('#limitations').innerHTML=s.limitations.map(l=>escapeHtml(l)).join('<br>');
}
function renderChart(){
  if(!statistics)return;
  if(!statistics.event_count&&current.status!=='completed'){$('#flowChart').innerHTML='<div class="empty-chart">完成视频分析后，客流变化会显示在这里。</div>';return}
  const bins=$('#binSize').value==='15'?statistics.bins15:statistics.bins5;const max=Math.max(1,...bins.map(b=>b.total));
  $('#flowChart').innerHTML=bins.map(b=>`<div class="chart-column" title="${timeLabel(b.start)} 起：${b.total} 人次，方向 A ${b.a}，方向 B ${b.b}"><span class="bar-total">${b.total}</span><div class="chart-bars"><div class="bar-a" style="height:${b.a/max*145}px"></div><div class="bar-b" style="height:${b.b/max*145}px"></div></div><span class="bar-label">${timeLabel(b.start)}</span></div>`).join('');
}
$('#binSize').onchange=renderChart;
function sizeCanvas(){
  const video=$('#setupVideo'),canvas=$('#lineCanvas');if(!video.videoWidth)return;
  canvas.width=video.clientWidth*devicePixelRatio;canvas.height=video.clientHeight*devicePixelRatio;canvas.style.width=video.clientWidth+'px';canvas.style.height=video.clientHeight+'px';drawOverlay();
}
function drawOverlay(){
  const canvas=$('#lineCanvas'),ctx=canvas.getContext('2d'),w=canvas.width,h=canvas.height;
  ctx.clearRect(0,0,w,h);const scale=devicePixelRatio;ctx.lineWidth=2*scale;
  if(roi.join(',')!=='0,0,1,1'){
    ctx.strokeStyle='#e5c488';ctx.setLineDash([5*scale,4*scale]);ctx.strokeRect(roi[0]*w,roi[1]*h,(roi[2]-roi[0])*w,(roi[3]-roi[1])*h);ctx.setLineDash([]);
    ctx.fillStyle='#e5c488';ctx.font=`${11*scale}px sans-serif`;ctx.fillText('统计区域',roi[0]*w+7*scale,roi[1]*h+18*scale);
  }
  const active=points.length===2?points:line;
  if(active){
    const [a,b]=active;ctx.strokeStyle='#8ddcb2';ctx.beginPath();ctx.moveTo(a[0]*w,a[1]*h);ctx.lineTo(b[0]*w,b[1]*h);ctx.stroke();
    [a,b].forEach(p=>{ctx.fillStyle='#e4ffed';ctx.beginPath();ctx.arc(p[0]*w,p[1]*h,4*scale,0,Math.PI*2);ctx.fill()});
    // signed_distance operates in normalized coordinates: use the same normal here.
    const dx=b[0]-a[0],dy=b[1]-a[1],len=Math.hypot(dx,dy),cx=(a[0]+b[0])/2,cy=(a[1]+b[1])/2;
    ctx.font=`bold ${14*scale}px sans-serif`;ctx.fillStyle='#c0ffdc';ctx.fillText('A',(cx-dy/len*.055)*w,(cy+dx/len*.055)*h);ctx.fillStyle='#ffd6a2';ctx.fillText('B',(cx+dy/len*.055)*w,(cy-dx/len*.055)*h);
  }
  if(points.length===1){ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(points[0][0]*w,points[0][1]*h,5*scale,0,Math.PI*2);ctx.fill()}
}
$('#setupVideo').onloadedmetadata=sizeCanvas;window.addEventListener('resize',sizeCanvas);
function startDraw(type){if(!current?.video_url)return;drawing=type;points=[];$('#setupVideo').pause();$('#videoStage').classList.add('drawing');$('#drawHint').textContent=type==='line'?'请在画面中点击计数线起点，再点击终点。':'请点击矩形区域左上角，再点击右下角。计数线须位于区域内。';drawOverlay()}
$('#drawLine').onclick=()=>startDraw('line');$('#drawRoi').onclick=()=>startDraw('roi');
async function saveSettings(){if(!line)return;const p=await api(`/api/projects/${current.id}`,{method:'PATCH',body:JSON.stringify({settings:{line,roi}})});current=p;renderReport()}
$('#lineCanvas').onclick=async e=>{
  if(!drawing)return;const rect=e.currentTarget.getBoundingClientRect();points.push([(e.clientX-rect.left)/rect.width,(e.clientY-rect.top)/rect.height]);
  if(points.length===2){
    const oldLine=line,oldRoi=roi;
    if(drawing==='line')line=points;else roi=[Math.min(points[0][0],points[1][0]),Math.min(points[0][1],points[1][1]),Math.max(points[0][0],points[1][0]),Math.max(points[0][1],points[1][1])];
    drawing=null;points=[];$('#videoStage').classList.remove('drawing');
    try{await saveSettings();toast('统计设置已保存');$('#drawHint').textContent='设置已保存。A / B 表示越线后到达的一侧；再次绘制可调整。'}catch(e){line=oldLine;roi=oldRoi;toast(e.message)}
  }drawOverlay();
};
$('#resetRoi').onclick=async()=>{const old=roi;roi=[0,0,1,1];try{await saveSettings();drawOverlay();toast('已恢复全画面')}catch(e){roi=old;toast(e.message)}};
function openCreate(){editing=false;$('#projectForm').reset();$('#projectDialog h2').textContent='开始一份街道调研';$('#projectForm button[type="submit"]').textContent='创建调研 →';$('#projectDialog').showModal()}
$('#editProject').onclick=()=>{editing=true;const form=$('#projectForm');form.reset();for(const [k,v] of Object.entries({...current.meta,name:current.name})){if(form.elements.namedItem(k))form.elements.namedItem(k).value=v}$('#projectDialog h2').textContent='编辑调研背景';$('#projectForm button[type="submit"]').textContent='保存修改 →';$('#projectDialog').showModal()};
$('#newProject').onclick=openCreate;$('#heroCreate').onclick=openCreate;
$$('[data-close]').forEach(b=>b.onclick=()=>$('#'+b.dataset.close).close());
$('#projectForm').onsubmit=async e=>{e.preventDefault();const f=new FormData(e.currentTarget),name=f.get('name');f.delete('name');await busy(e.submitter,async()=>{const payload={name,meta:Object.fromEntries(f)};const p=editing?await api(`/api/projects/${current.id}`,{method:'PATCH',body:JSON.stringify(payload)}):await post('/api/projects',payload);$('#projectDialog').close();e.target.reset();await refreshProjects();await selectProject(p.id)},'保存中…')};
async function upload(file){
  if(!current||!file)return;if(current.status==='running'){toast('请先停止当前分析');return}
  if(current.video_url&&!confirm('更换视频将清除当前统计和报告。继续吗？'))return;
  const extension='.'+file.name.split('.').pop().toLowerCase();if(!['.mp4','.mov','.avi','.mkv','.m4v'].includes(extension)){toast('请上传 MP4、MOV、AVI 或 MKV 文件');return}
  if(file.size>20*1024**3){toast('视频不能超过 20GB');return}
  uploading=true;$('#uploadProgress').hidden=false;$('#uploadProgress').textContent='开始上传…';const pid=current.id;renderTask();
  const xhr=new XMLHttpRequest();xhr.open('PUT',`/api/projects/${pid}/video`);xhr.setRequestHeader('Content-Type','application/octet-stream');xhr.setRequestHeader('X-Video-Extension',extension);
  xhr.upload.onprogress=e=>{if(e.lengthComputable)$('#uploadProgress').textContent=`上传中 ${Math.round(e.loaded/e.total*100)}% · ${(file.size/1024**2).toFixed(0)} MB`};
  xhr.onload=async()=>{uploading=false;try{const p=JSON.parse(xhr.responseText);if(xhr.status!==200)throw new Error(p.error||'上传失败');$('#uploadProgress').hidden=true;await refreshProjects();await selectProject(pid);toast('视频已上传，请绘制计数线')}catch(e){toast(e.message);$('#uploadProgress').textContent=e.message;current=await api(`/api/projects/${pid}`);renderTask()}};
  xhr.onerror=()=>{uploading=false;$('#uploadProgress').textContent='上传中断，请重试';toast('上传中断，请检查服务连接');renderTask()};xhr.send(file);
}
$('#videoInput').onchange=e=>{upload(e.target.files[0]);e.target.value=''};
$('#replaceVideo').onclick=()=>$('#videoInput').click();
const drop=$('#dropZone');drop.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();$('#videoInput').click()}};drop.ondragover=e=>{e.preventDefault();drop.classList.add('dragover')};drop.ondragleave=()=>drop.classList.remove('dragover');drop.ondrop=e=>{e.preventDefault();drop.classList.remove('dragover');upload(e.dataTransfer.files[0])};
$('#startAnalysis').onclick=()=>busy($('#startAnalysis'),async()=>{if(!line)throw new Error('请先绘制计数线');if(statistics?.event_count&&!confirm('重新分析会替换现有统计及人工修正。继续吗？'))return;await saveSettings();await post(`/api/projects/${current.id}/analyze`);current=await api(`/api/projects/${current.id}`);renderTask();toast('分析任务已启动；首次运行可能需要下载模型')},'启动中…');
$('#stopAnalysis').onclick=()=>busy($('#stopAnalysis'),async()=>{await post(`/api/projects/${current.id}/stop`);toast('已请求停止，正在保存当前结果')});
$('#deleteProject').onclick=async()=>{if(!confirm('永久删除此项目、本地视频、统计和对话？'))return;await busy($('#deleteProject'),async()=>{await api(`/api/projects/${current.id}`,{method:'DELETE'});current=null;localStorage.removeItem('street-project');await refreshProjects();$('#workspace').hidden=true;$('#welcome').hidden=false;$('#exportPdf').hidden=true;$('#pageTitle').textContent='每一条街，都有它的生意。';$('#pageSubtitle').textContent='从一段街景视频开始，读懂客流，找到值得验证的开店方向。';if(projects.length)await selectProject(projects[0].id)})};
async function loadEvents(){
  if(!current)return;const out=await api(`/api/projects/${current.id}/events?offset=${eventOffset}&limit=25`);eventTotal=out.total;
  $('#eventsBody').innerHTML=out.items.length?out.items.map(e=>`<tr class="${e.included?'':'excluded'}"><td><button class="event-time" data-seek="${e.sec}">${timeLabel(e.sec)}</button></td><td><button data-flip="${e.id}" data-direction="${e.direction}" data-included="${e.included}">${e.direction} ⇄</button></td><td>${e.reviewed?'已复核':'待复核'}</td><td><button data-review="${e.id}" data-direction="${e.direction}" data-included="${e.included}">确认</button> <button data-exclude="${e.id}" data-direction="${e.direction}" data-included="${e.included}">${e.included?'排除':'恢复'}</button></td></tr>`).join(''):'<tr><td colspan="4" class="empty-chart">还没有过线事件。</td></tr>';
  $$('[data-seek]').forEach(b=>b.onclick=()=>{$('#reviewVideo').currentTime=Math.max(0,Number(b.dataset.seek)-1);$('#reviewVideo').play().catch(()=>{})});
  async function correct(b,type){try{await api(`/api/projects/${current.id}/events`,{method:'PATCH',body:JSON.stringify({id:Number(b.dataset[type]),direction:type==='flip'?(b.dataset.direction==='A'?'B':'A'):b.dataset.direction,included:type==='exclude'?!Number(b.dataset.included):!!Number(b.dataset.included)})});await refreshAfterReview();toast('复核已保存')}catch(e){toast(e.message)}}
  $$('[data-flip]').forEach(b=>b.onclick=()=>correct(b,'flip'));$$('[data-review]').forEach(b=>b.onclick=()=>correct(b,'review'));$$('[data-exclude]').forEach(b=>b.onclick=()=>correct(b,'exclude'));
  $('#eventPage').textContent=out.total?`${eventOffset+1}–${Math.min(eventOffset+25,out.total)} / ${out.total}`:'0 条事件';$('#prevEvents').disabled=eventOffset===0;$('#nextEvents').disabled=eventOffset+25>=out.total;
}
async function refreshAfterReview(){current=await api(`/api/projects/${current.id}`);await refreshStats();await loadEvents();renderReport();$('#chatVersion').textContent=`当前数据版本 v${current.revision}；历史消息标记各自版本`}
$('#prevEvents').onclick=()=>{eventOffset=Math.max(0,eventOffset-25);loadEvents().catch(e=>toast(e.message))};$('#nextEvents').onclick=()=>{if(eventOffset+25<eventTotal)eventOffset+=25;loadEvents().catch(e=>toast(e.message))};
$('#manualEvent').onclick=()=>busy($('#manualEvent'),async()=>{await post(`/api/projects/${current.id}/manual`,{sec:$('#reviewVideo').currentTime,direction:$('#manualDirection').value});await refreshAfterReview();toast('已补录一条通行事件')});
function renderReport(){
  if(!current)return;const r=current.report;const stale=r&&current.report_revision!==current.revision;
  $('#generateReport').textContent=r?(stale?'基于新数据重新生成 ↗':'查看 / 复用当前报告'):'生成 AI 报告 ↗';
  if(!r){$('#reportContent').innerHTML='<div class="report-empty">完成客流分析并配置 DeepSeek 后，即可生成调研报告。<br>AI 会说明依据与未知信息，帮助你确定下一步调查方向。</div>';return}
  $('#reportContent').innerHTML=(stale?'<div class="stale">数据已更新，这份报告基于旧版本。请重新生成。</div>':'')+`<article class="report-block"><span class="eyebrow">OBSERVATION / V${current.report_revision}</span><h3>街道观察摘要</h3><p>${escapeHtml(r.summary)}</p><div class="evidence">引用指标：${r.evidence_keys.map(k=>`${escapeHtml(k)} = ${r.verified_statistics[k]}`).join(' · ')}</div></article>`+r.candidates.map((c,i)=>`<article class="report-block"><span class="eyebrow">OPPORTUNITY / 0${i+1}</span><h3>${escapeHtml(c.name)}</h3>${[['basis','依据'],['conditions','适用条件'],['missing','缺少信息'],['next_steps','验证方法']].map(([k,l])=>`<p><strong>${l}</strong><br>${escapeHtml(c[k])}</p>`).join('')}</article>`).join('')+`<article class="report-block"><h3>下一步验证</h3><ul>${r.next_steps.map(s=>`<li>${escapeHtml(s)}</li>`).join('')}</ul><h3>数据局限</h3><ul>${r.limitations.map(s=>`<li>${escapeHtml(s)}</li>`).join('')}</ul><p class="hint">${escapeHtml(r.model)} · ${escapeHtml(r.validation_note)} · 数据版本 v${current.report_revision}</p></article>`;
}
$('#generateReport').onclick=()=>busy($('#generateReport'),async()=>{if(!health.ai.configured){$('#settingsBtn').click();return}await post(`/api/projects/${current.id}/report`);current=await api(`/api/projects/${current.id}`);renderReport();toast('报告已准备好')},'AI 正在分析统计摘要…');
async function loadChat(){if(!current)return;const chats=await api(`/api/projects/${current.id}/chat`);if(chats.length){$('#chatMessages').innerHTML=chats.map(c=>`<div class="chat-bubble ${c.role==='user'?'user':''}"><small>${c.role==='user'?'你':'调研助手'} · v${c.revision}</small>${escapeHtml(c.content)}</div>`).join('');$('#chatMessages').scrollTop=$('#chatMessages').scrollHeight}else{$('#chatMessages').innerHTML='<div class="chat-placeholder">还有哪些问题需要验证？<br>试着问：“这个客流适合做咖啡店吗？”</div>'}$('#chatVersion').textContent=`基于当前项目 · 数据版本 v${current.revision}`}
$('#chatForm').onsubmit=async e=>{e.preventDefault();const text=$('#chatInput').value.trim();if(!text)return;await busy(e.submitter,async()=>{await post(`/api/projects/${current.id}/chat`,{message:text});$('#chatInput').value='';await loadChat()},'思考中…')};
$('#exportPdf').onclick=()=>window.open(`/api/projects/${current.id}/pdf`,'_blank');
function refreshAiStatus(config){health.ai=config;$('#aiStatus').textContent=config.configured?'● AI 已配置':'AI 待配置';$('#aiStatus').classList.toggle('ready',config.configured);$('#connectionInfo').textContent=config.configured?`已保存密钥 ${config.key_hint} · ${config.model}`:'尚未保存密钥 · 视频统计功能可独立使用';$('#apiKeyInput').placeholder=config.configured?'已保存；留空保留现有密钥':'粘贴 sk- 开头的完整密钥';$('#aiModelInput').value=config.model;$('#deleteApiKey').disabled=!config.configured}
$('#settingsBtn').onclick=async()=>{try{refreshAiStatus(await api('/api/ai/settings'));$('#apiKeyInput').value='';$('#apiKeyInput').type='password';$('#toggleApiKey').textContent='显示';$('#testResult').textContent='';$('#settingsDialog').showModal()}catch(e){toast(e.message)}};
$('#aiStatus').onclick=()=>$('#settingsBtn').click();
$('#settingsDialog').addEventListener('close',()=>{$('#apiKeyInput').value='';$('#apiKeyFile').value=''});
$('#toggleApiKey').onclick=()=>{const input=$('#apiKeyInput');input.type=input.type==='password'?'text':'password';$('#toggleApiKey').textContent=input.type==='password'?'显示':'隐藏'};
$('#importApiKey').onclick=()=>$('#apiKeyFile').click();
$('#apiKeyFile').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>4096)throw new Error('请选择只包含 API Key 的小型 TXT 文件');$('#apiKeyInput').value=(await file.text()).trim();$('#testResult').textContent='密钥已导入，点击“保存配置”后生效。'}catch(err){toast(err.message)}finally{e.target.value=''}};
$('#aiSettingsForm').onsubmit=async e=>{e.preventDefault();await busy(e.submitter,async()=>{const config=await api('/api/ai/settings',{method:'PUT',body:JSON.stringify({api_key:$('#apiKeyInput').value.trim(),model:$('#aiModelInput').value.trim()})});$('#apiKeyInput').value='';refreshAiStatus(config);$('#testResult').textContent='配置已加密保存，可点击“测试已保存连接”验证。';toast('AI 配置已保存，无需重启')},'保存中…')};
$('#deleteApiKey').onclick=()=>busy($('#deleteApiKey'),async()=>{const config=await api('/api/ai/settings',{method:'DELETE'});$('#apiKeyInput').value='';refreshAiStatus(config);$('#testResult').textContent='已删除当前配置的密钥，AI 功能暂停；视频统计仍可使用。';toast('已删除保存的密钥')});
$('#testConnection').onclick=()=>busy($('#testConnection'),async()=>{if($('#apiKeyInput').value.trim())throw new Error('请先保存填写的密钥，再测试连接');if(!health.ai.configured)throw new Error('请先填写并保存 API Key');$('#testResult').textContent='正在验证连接…';try{const r=await post('/api/ai/test');$('#testResult').textContent='连接成功 · '+r.model;toast('DeepSeek 连接成功')}catch(e){$('#testResult').textContent='连接失败：'+e.message;throw e}},'正在测试…');
$('#compareBtn').onclick=()=>{$('#compareList').innerHTML=projects.filter(p=>p.status==='completed').map(p=>`<label><input type="checkbox" value="${p.id}"> ${escapeHtml(p.name)}</label>`).join('')||'<p>还没有已完成分析的项目。</p>';$('#compareResult').textContent='';$('#compareDialog').showModal()};
$('#runCompare').onclick=()=>busy($('#runCompare'),async()=>{const ids=$$('#compareList input:checked').map(x=>x.value);if(ids.length<2||ids.length>5)throw new Error('请选择 2—5 个已完成项目');const r=await post('/api/compare',{project_ids:ids});$('#compareResult').textContent=r.answer},'正在比较…');
async function poll(){
  if(!current||pollBusy||uploading)return;pollBusy=true;
  try{const pid=current.id,p=await api(`/api/projects/${pid}`);if(current?.id!==pid)return;const was=current.status;current=p;renderTask();if(was==='running'||p.status==='running'){await refreshStats();if(p.status!==was){await refreshProjects();await loadEvents();renderReport();toast(p.message)}}}catch(e){/* Keep current page on temporary connectivity loss. */}finally{pollBusy=false}
}
async function boot(){
  try{health=await api('/api/health');$('#detectorStatus').textContent=health.detector_ready?'● 检测引擎已就绪':'检测依赖待安装';$('#detectorStatus').classList.toggle('ready',health.detector_ready);$('#aiStatus').textContent=health.ai.configured?'● AI 已配置':'AI 待配置';$('#aiStatus').classList.toggle('ready',health.ai.configured);await refreshProjects();const selected=new URLSearchParams(location.search).get('project')||localStorage.getItem('street-project');if(projects.length)await selectProject(projects.some(p=>p.id===selected)?selected:projects[0].id);setInterval(poll,2200)}catch(e){toast('无法连接本地服务：'+e.message)}
}boot();
