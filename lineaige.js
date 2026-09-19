'use strict';

const viewport=document.getElementById('timelineViewport');
const world=document.getElementById('lineaigeTimeline');
const historyLane=document.getElementById('historyLane');
const learningLane=document.getElementById('learningLane');
const creatorLane=document.getElementById('creatorLane');
const futureLane=document.getElementById('futureLane');
const historyLine=document.getElementById('historyLine');
const futureLine=document.getElementById('futureLine');
const travelShade=document.getElementById('travelShade');
const todayMark=document.getElementById('todayMark');
const todayDate=document.getElementById('todayDate');
const todayTime=document.getElementById('todayTime');
const todayZone=document.getElementById('todayZone');
const readingGuide=document.getElementById('readingGuide');
const readingDate=document.getElementById('readingDate');
const timelineShell=document.querySelector('.timeline-shell');

const drawer=document.getElementById('drawer');
const closeEl=document.getElementById('close');
const titleEl=document.getElementById('title');
const dateEl=document.getElementById('date');
const recordTypeEl=document.getElementById('recordType');
const summaryEl=document.getElementById('summary');
const significanceEl=document.getElementById('significance');
const whySection=document.getElementById('whySection');
const originEl=document.getElementById('origin');
const verificationEl=document.getElementById('verification');
const sourceCountEl=document.getElementById('sourceCount');
const proofButton=document.getElementById('proofButton');
const traceButton=document.getElementById('traceButton');
const proofSection=document.getElementById('proofSection');
const traceSection=document.getElementById('traceSection');
const sourcesEl=document.getElementById('sources');
const relationsEl=document.getElementById('relations');
const marginaliaSection=document.getElementById('marginaliaSection');
const marginaliaToggle=document.getElementById('marginaliaToggle');
const marginaliaCount=document.getElementById('marginaliaCount');
const marginaliaList=document.getElementById('marginaliaList');
const brandInfo=document.getElementById('brandInfo');
const linkNote=document.getElementById('linkNote');

const state={
  data:null,
  recordsById:new Map(),
  markerById:new Map(),
  minTime:null,
  maxTime:null,
  todayTime:null,
  todayX:0,
  worldWidth:5400,
  padding:96,
  offsetX:0,
  dragging:false,
  pointerId:null,
  dragStartX:0,
  dragStartOffset:0,
  moved:false,
  activeId:null,
  lastTrigger:null,
  readTimer:null
};

const CAUSAL_TYPES=new Set(['ancestor','descendant','influenced','enabled']);
const NONCAUSAL_TYPES=new Set(['chronological','contextual','navigation','related','source-path']);
const reduceMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function safeExternalUrl(value){
  if(typeof value!=='string') return null;
  try{
    const parsed=new URL(value,window.location.href);
    return parsed.protocol==='https:' || parsed.protocol==='http:' ? parsed.href : null;
  }catch{
    return null;
  }
}

function clamp(value,min,max){
  return Math.min(max,Math.max(min,value));
}

function dateFromValue(value){
  return Number.isFinite(value) ? new Date(value) : null;
}

function yearFromValue(value){
  const d=dateFromValue(value);
  return d ? d.getUTCFullYear() : null;
}

function recordTime(record){
  if(record?.recordType==='announced_future') return LINEAiGEData.futureTargetValue(record);
  return LINEAiGEData.temporalValue(record);
}

function displayOrigin(record){
  if(record?.entryOrigin==='co-author'){
    const name=record?.contributor?.name || record?.contributor?.creditPreference;
    return name ? `CO-AUTHOR · ${name}` : 'CO-AUTHOR';
  }
  if(record?.__kind==='learning') return record.institution || record.provider || 'LEARNING & PROGRAMS';
  if(record?.__kind==='creator') return record.creator || record.organization || 'CREATOR RELEASE';
  return 'BARBPH LINEAiGE';
}

function verificationLabel(record){
  const stateValue=record?.verification?.state;
  if(stateValue) return String(stateValue).replaceAll('-',' ').toUpperCase();
  if(record?.verifiedAt) return 'VERIFIED EXISTENCE';
  return 'RECORD';
}

function recordSources(record){
  const direct=Array.isArray(record?.sources) ? record.sources : [];
  if(direct.length) return direct;
  if(record?.__kind==='learning' && safeExternalUrl(record.courseUrl)){
    return [{
      title:record.title,
      url:record.courseUrl,
      publisher:record.institution || record.provider || null,
      sourceType:'official destination',
      sourceRole:'learning resource',
      primary:true
    }];
  }
  if(record?.__kind==='creator'){
    const url=safeExternalUrl(record.projectUrl || record.releaseUrl);
    if(url){
      return [{
        title:record.title,
        url,
        publisher:record.creator || record.organization || null,
        sourceType:'official destination',
        sourceRole:'release record',
        primary:true
      }];
    }
  }
  return [];
}

function displayDate(record){
  if(record?.recordType==='living_edge') return localTodayLabel();
  if(record?.displayDate) return record.displayDate;
  if(record?.startDate) return record.startDate;
  if(record?.startMonth) return record.startMonth;
  if(record?.startYear) return record.startYear;
  if(record?.releaseDate) return record.releaseDate;
  if(record?.releaseMonth) return record.releaseMonth;
  if(record?.releaseYear) return record.releaseYear;
  return '—';
}

function localTodayLabel(){
  return new Intl.DateTimeFormat(undefined,{year:'numeric',month:'long',day:'numeric'}).format(new Date());
}

function updateToday(){
  const now=new Date();
  todayDate.textContent=new Intl.DateTimeFormat(undefined,{year:'numeric',month:'short',day:'numeric'}).format(now);
  todayTime.textContent=new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(now);
  todayZone.textContent=Intl.DateTimeFormat().resolvedOptions().timeZone || 'LOCAL TIME';
}

function setupTimelineScale(){
  const historical=state.data.recorded
    .map(record=>recordTime(record))
    .filter(Number.isFinite);

  const now=Date.now();
  const earliest=historical.length ? Math.min(...historical) : Date.UTC(1950,0,1);
  const today=now;
  const historySpan=Math.max(today-earliest,365*24*60*60*1000);
  let futureEnd=today+(historySpan*.25);

  const futureValues=state.data.announcedFuture
    .map(record=>LINEAiGEData.futureTargetValue(record))
    .filter(Number.isFinite);
  if(futureValues.length) futureEnd=Math.max(futureEnd,...futureValues);

  state.minTime=earliest;
  state.todayTime=today;
  state.maxTime=futureEnd;

  const viewportWidth=Math.max(viewport.clientWidth,320);
  const count=Math.max(1,state.data.recorded.length);
  state.worldWidth=Math.max(viewportWidth*4.8,4800,count*260);
  state.padding=Math.max(86,viewportWidth*.06);

  world.style.setProperty('--world-width',`${state.worldWidth}px`);
  world.style.width=`${state.worldWidth}px`;
  state.todayX=xForTime(today);
  world.style.setProperty('--history-start',`${state.padding}px`);
  world.style.setProperty('--today-x',`${state.todayX}px`);
  clampOffset();
  applyOffset();
}

function xForTime(value){
  if(!Number.isFinite(value)) return null;
  const usable=state.worldWidth-(state.padding*2);
  const ratio=(value-state.minTime)/(state.maxTime-state.minTime);
  return state.padding+(clamp(ratio,0,1)*usable);
}

function timeForX(x){
  const usable=state.worldWidth-(state.padding*2);
  const ratio=clamp((x-state.padding)/usable,0,1);
  return state.minTime+(ratio*(state.maxTime-state.minTime));
}

function clearTimeline(){
  historyLane.replaceChildren();
  learningLane.replaceChildren();
  creatorLane.replaceChildren();
  futureLane.replaceChildren();
  state.markerById.clear();
}

function createMark(record,kind,timeValue){
  const x=xForTime(timeValue);
  if(x===null) return null;

  const button=document.createElement('button');
  button.type='button';
  button.className=`timeline-mark ${kind}`;
  if(record.entryOrigin==='co-author') button.classList.add('co-author');
  button.dataset.recordId=record.id;
  button.style.left=`${x}px`;
  button.setAttribute('aria-label',`Open ${record.title}, ${displayDate(record)}`);

  const stroke=document.createElement('span');
  stroke.className='mark-stroke';
  stroke.setAttribute('aria-hidden','true');

  const copy=document.createElement('span');
  copy.className='mark-copy';
  const date=document.createElement('span');
  date.className='mark-date';
  date.textContent=displayDate(record);
  const title=document.createElement('span');
  title.className='mark-title';
  title.textContent=record.title;
  copy.append(date,title);
  button.append(stroke,copy);

  button.addEventListener('pointerdown',event=>event.stopPropagation());
  button.addEventListener('click',()=>{
    if(state.moved) return;
    state.lastTrigger=button;
    openRecord(record.id);
  });

  state.markerById.set(record.id,button);
  return button;
}

function renderHistory(){
  state.data.recorded.forEach(record=>{
    const t=LINEAiGEData.temporalValue(record);
    if(!Number.isFinite(t)) return;
    state.recordsById.set(record.id,record);
    const mark=createMark(record,'history',t);
    if(mark) historyLane.appendChild(mark);
  });
}

function learningSummary(item){
  if(typeof item.summary==='string' && item.summary.trim()) return item.summary;
  const topics=Array.isArray(item.topics) ? item.topics.filter(Boolean) : [];
  if(topics.length) return `Topics include ${topics.join(', ')}.`;
  return 'A verified AI learning or program record.';
}

function renderLearning(){
  let count=0;
  state.data.courses.forEach(item=>{
    const t=LINEAiGEData.learningTemporalValue(item);
    if(!Number.isFinite(t)) return;
    const record={
      ...item,
      __kind:'learning',
      recordType:'learning_program',
      summary:learningSummary(item),
      significance:item.significance || null,
      entryOrigin:item.entryOrigin || 'lineaige'
    };
    state.recordsById.set(record.id,record);
    const mark=createMark(record,'learning',t);
    if(!mark) return;

    const endValue=LINEAiGEData.learningEndValue(item);
    const active=item.status==='active' || item.active===true || (!Number.isFinite(endValue) && item.ongoing===true);
    if(active){
      const endX=state.todayX;
      const startX=xForTime(t);
      if(endX>startX){
        const stroke=document.createElement('span');
        stroke.className='ongoing-stroke';
        stroke.style.width=`${endX-startX}px`;
        mark.appendChild(stroke);
      }
    }
    learningLane.appendChild(mark);
    count++;
  });
  setKeyVisibility('key-learning',count>0);
}

function renderCreators(){
  let count=0;
  state.data.creatorReleases.forEach(item=>{
    const t=LINEAiGEData.creatorTemporalValue(item);
    if(!Number.isFinite(t)) return;
    const record={
      ...item,
      __kind:'creator',
      recordType:'creator_release',
      summary:item.summary || 'A documented AI-related or AI-assisted creator release.',
      entryOrigin:item.entryOrigin || 'lineaige'
    };
    state.recordsById.set(record.id,record);
    const mark=createMark(record,'creator',t);
    if(mark){
      creatorLane.appendChild(mark);
      count++;
    }
  });
  setKeyVisibility('key-creator',count>0);
}

function renderFuture(){
  let count=0;
  state.data.announcedFuture.forEach(record=>{
    const t=LINEAiGEData.futureTargetValue(record);
    if(!Number.isFinite(t)) return;
    state.recordsById.set(record.id,record);
    const mark=createMark(record,'future',t);
    if(mark){
      futureLane.appendChild(mark);
      count++;
    }
  });
  setKeyVisibility('key-future',count>0);
}

function setKeyVisibility(className,visible){
  const swatch=document.querySelector(`.${className}`);
  const item=swatch?.closest('span');
  if(item) item.hidden=!visible;
}

function renderTimeline(){
  clearTimeline();
  renderHistory();
  renderLearning();
  renderCreators();
  renderFuture();
  setKeyVisibility('key-history',state.data.recorded.length>0);
}

function supportedRelationships(record){
  const relationships=Array.isArray(record?.relationships) ? record.relationships : [];
  return relationships.filter(rel=>{
    if(!rel || typeof rel.targetId!=='string' || !state.recordsById.has(rel.targetId)) return false;
    if(CAUSAL_TYPES.has(rel.type)){
      return rel.evidenceState==='verified' && Array.isArray(rel.sourceUrls) && rel.sourceUrls.length>0;
    }
    if(NONCAUSAL_TYPES.has(rel.type)){
      return ['verified','contextual','navigation-only'].includes(rel.evidenceState);
    }
    return false;
  });
}

function renderSources(record){
  sourcesEl.replaceChildren();
  const sources=recordSources(record);
  sources.forEach(source=>{
    const href=safeExternalUrl(source?.url);
    if(!href) return;

    const link=document.createElement('a');
    link.className='source-item';
    link.href=href;
    link.target='_blank';
    link.rel='noopener noreferrer';

    const type=document.createElement('div');
    type.className='source-type';
    const role=typeof source.sourceRole==='string' ? source.sourceRole.replaceAll('-',' ').toUpperCase() : null;
    const sourceType=typeof source.sourceType==='string' ? source.sourceType.replaceAll('-',' ').toUpperCase() : 'SOURCE';
    type.textContent=[source.primary?'PRIMARY':'SECONDARY',sourceType,role].filter(Boolean).join(' · ');

    const sourceTitle=document.createElement('div');
    sourceTitle.className='source-title';
    sourceTitle.textContent=source.title || href;

    const publisher=document.createElement('div');
    publisher.className='source-publisher';
    publisher.textContent=[source.publisher,source.publishedDate].filter(Boolean).join(' · ');

    link.append(type,sourceTitle,publisher);
    sourcesEl.appendChild(link);
  });
}

function renderRelationships(record){
  relationsEl.replaceChildren();
  const relationships=supportedRelationships(record);
  relationships.forEach(rel=>{
    const target=state.recordsById.get(rel.targetId);
    const button=document.createElement('button');
    button.type='button';
    button.className='relation';

    const main=document.createElement('span');
    main.textContent=rel.label || target.title;
    const meta=document.createElement('small');
    const typeLabel=String(rel.type || 'relationship').replaceAll('-',' ').toUpperCase();
    const evidence=String(rel.evidenceState || '').replaceAll('-',' ').toUpperCase();
    meta.textContent=[typeLabel,evidence].filter(Boolean).join(' · ');

    button.append(main,meta);
    button.addEventListener('click',()=>{
      if(state.recordsById.has(rel.targetId)){
        openRecord(rel.targetId);
      }else{
        showLinkNote('RELATIONSHIP UNAVAILABLE. No relationship claim is inferred from a broken path.');
      }
    });
    relationsEl.appendChild(button);
  });
  return relationships.length;
}

function contributionSources(contribution){
  if(!Array.isArray(contribution?.sources)) return [];
  return contribution.sources.map(item=>typeof item==='string'?item:item?.url).filter(Boolean);
}

function renderMarginalia(record){
  marginaliaList.replaceChildren();
  const contributions=Array.isArray(record?.contributions) ? record.contributions : [];
  const publicContributions=contributions.filter(item=>item && item.public!==false && typeof item.text==='string' && item.text.trim());

  if(!publicContributions.length){
    marginaliaSection.hidden=true;
    marginaliaList.hidden=true;
    marginaliaToggle.setAttribute('aria-expanded','false');
    return;
  }

  marginaliaSection.hidden=false;
  marginaliaCount.textContent=`${publicContributions.length} CO-AUTHOR ${publicContributions.length===1?'NOTE':'NOTES'}`;
  publicContributions.forEach(item=>{
    const note=document.createElement('article');
    note.className='margin-note';

    const type=document.createElement('div');
    type.className='margin-type';
    type.textContent=String(item.type || 'context').replaceAll('-',' ').toUpperCase();

    const body=document.createElement('p');
    body.textContent=item.text;

    const credit=document.createElement('div');
    credit.className='margin-credit';
    const name=item?.contributor?.name || item?.contributor?.creditPreference || item?.credit || 'CO-AUTHOR';
    credit.textContent=[name,item.admittedAt || item.approvedAt].filter(Boolean).join(' · ');

    note.append(type,body,credit);

    const urls=contributionSources(item);
    if(urls.length){
      const links=document.createElement('div');
      links.className='margin-credit';
      urls.forEach((url,index)=>{
        const safe=safeExternalUrl(url);
        if(!safe) return;
        const a=document.createElement('a');
        a.href=safe;
        a.target='_blank';
        a.rel='noopener noreferrer';
        a.textContent=index===0?'SOURCE':' · SOURCE';
        links.appendChild(a);
      });
      note.appendChild(links);
    }
    marginaliaList.appendChild(note);
  });
}

function openRecord(id){
  const record=state.recordsById.get(id);
  if(!record){
    showLinkNote('RECORD UNAVAILABLE. LINEAiGE will not invent a missing record.');
    return;
  }

  state.activeId=id;
  state.markerById.forEach((marker,key)=>marker.classList.toggle('selected',key===id));

  recordTypeEl.textContent=record.recordType==='living_edge'
    ? 'LIVING EDGE'
    : String(record.__kind || record.recordType || 'record').replaceAll('_',' ').replaceAll('-',' ').toUpperCase();
  dateEl.textContent=displayDate(record);
  titleEl.textContent=record.recordType==='living_edge' ? 'TODAY' : record.title;
  summaryEl.textContent=record.recordType==='living_edge'
    ? 'The living edge where history is still forming. Visitor-local time is interface state, not historical evidence.'
    : (record.summary || '');

  if(record.significance){
    significanceEl.textContent=record.significance;
    whySection.hidden=false;
  }else{
    significanceEl.textContent='';
    whySection.hidden=true;
  }

  originEl.textContent=displayOrigin(record);
  verificationEl.textContent=verificationLabel(record);

  const sources=recordSources(record);
  sourceCountEl.textContent=String(sources.length);
  proofButton.hidden=sources.length===0;
  proofSection.hidden=true;
  proofButton.setAttribute('aria-expanded','false');
  renderSources(record);

  const relationshipCount=renderRelationships(record);
  traceButton.hidden=relationshipCount===0;
  traceSection.hidden=true;
  traceButton.setAttribute('aria-expanded','false');

  renderMarginalia(record);

  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden','false');
  requestAnimationFrame(()=>titleEl.focus({preventScroll:true}));
  document.dispatchEvent(new CustomEvent('lineaige:record-opened',{detail:{id,record}}));
}

function closeDrawer(){
  drawer.classList.remove('open');
  drawer.setAttribute('aria-hidden','true');
  state.markerById.forEach(marker=>marker.classList.remove('selected'));
  state.activeId=null;
  proofSection.hidden=true;
  traceSection.hidden=true;
  marginaliaList.hidden=true;
  marginaliaToggle.setAttribute('aria-expanded','false');
  document.dispatchEvent(new CustomEvent('lineaige:record-closed'));
  if(state.lastTrigger && document.contains(state.lastTrigger)){
    requestAnimationFrame(()=>state.lastTrigger.focus({preventScroll:true}));
  }
}

function toggleFold(button,section){
  const willOpen=section.hidden;
  section.hidden=!willOpen;
  button.setAttribute('aria-expanded',String(willOpen));
}

proofButton.addEventListener('click',()=>toggleFold(proofButton,proofSection));
traceButton.addEventListener('click',()=>toggleFold(traceButton,traceSection));
marginaliaToggle.addEventListener('click',()=>{
  const willOpen=marginaliaList.hidden;
  marginaliaList.hidden=!willOpen;
  marginaliaToggle.setAttribute('aria-expanded',String(willOpen));
});
closeEl.addEventListener('click',closeDrawer);

function clampOffset(){
  const min=Math.min(0,viewport.clientWidth-state.worldWidth);
  state.offsetX=clamp(state.offsetX,min,0);
}

function applyOffset(){
  world.style.transform=`translate3d(${state.offsetX}px,0,0)`;
  const centerWorldX=(-state.offsetX)+(viewport.clientWidth/2);
  const readTime=timeForX(centerWorldX);
  const year=yearFromValue(readTime);
  readingDate.textContent=year ? String(year) : '—';
  travelShade.style.width=`${clamp(centerWorldX,0,state.worldWidth)}px`;
}

function beginReading(){
  timelineShell.classList.add('reading','has-travelled');
  clearTimeout(state.readTimer);
}

function endReading(){
  clearTimeout(state.readTimer);
  state.readTimer=setTimeout(()=>timelineShell.classList.remove('reading'),reduceMotion?0:480);
}

viewport.addEventListener('pointerdown',event=>{
  if(event.button!==0 && event.pointerType!=='touch') return;
  state.dragging=true;
  state.pointerId=event.pointerId;
  state.dragStartX=event.clientX;
  state.dragStartOffset=state.offsetX;
  state.moved=false;
  viewport.classList.add('dragging');
  viewport.setPointerCapture?.(event.pointerId);
  beginReading();
});

viewport.addEventListener('pointermove',event=>{
  if(!state.dragging || event.pointerId!==state.pointerId) return;
  const dx=event.clientX-state.dragStartX;
  if(Math.abs(dx)>5) state.moved=true;
  state.offsetX=state.dragStartOffset+dx;
  clampOffset();
  applyOffset();
  if(Math.abs(dx)>3) event.preventDefault();
});

function endPointer(event){
  if(!state.dragging || (event.pointerId!==undefined && event.pointerId!==state.pointerId)) return;
  state.dragging=false;
  viewport.classList.remove('dragging');
  try{viewport.releasePointerCapture?.(state.pointerId);}catch{}
  state.pointerId=null;
  endReading();
  window.setTimeout(()=>{state.moved=false;},0);
}
viewport.addEventListener('pointerup',endPointer);
viewport.addEventListener('pointercancel',endPointer);

viewport.addEventListener('wheel',event=>{
  const horizontal=Math.abs(event.deltaX)>Math.abs(event.deltaY) ? event.deltaX : (event.shiftKey ? event.deltaY : 0);
  if(!horizontal) return;
  event.preventDefault();
  beginReading();
  state.offsetX-=horizontal;
  clampOffset();
  applyOffset();
  endReading();
},{passive:false});

function nudgeTimeline(direction){
  beginReading();
  state.offsetX+=direction*150;
  clampOffset();
  applyOffset();
  endReading();
}

document.addEventListener('keydown',event=>{
  if(event.key==='Escape'){
    if(drawer.classList.contains('open')){
      event.preventDefault();
      closeDrawer();
      return;
    }
    if(brandInfo.getAttribute('aria-expanded')==='true'){
      brandInfo.setAttribute('aria-expanded','false');
    }
  }

  if(document.activeElement===viewport){
    if(event.key==='ArrowRight'){
      event.preventDefault();
      nudgeTimeline(-1);
    }else if(event.key==='ArrowLeft'){
      event.preventDefault();
      nudgeTimeline(1);
    }
  }
});

todayMark.addEventListener('click',()=>{
  state.lastTrigger=todayMark;
  if(state.data?.now) openRecord(state.data.now.id);
});

brandInfo.addEventListener('click',()=>{
  const open=brandInfo.getAttribute('aria-expanded')==='true';
  brandInfo.setAttribute('aria-expanded',String(!open));
});

document.addEventListener('pointerdown',event=>{
  if(!brandInfo.contains(event.target) && !document.getElementById('brandExplainer').contains(event.target)){
    brandInfo.setAttribute('aria-expanded','false');
  }
});

function showLinkNote(message){
  linkNote.textContent=message;
  linkNote.hidden=false;
  clearTimeout(showLinkNote.timer);
  showLinkNote.timer=setTimeout(()=>{linkNote.hidden=true;},3600);
}

['youtubeLink','contactLink'].forEach(id=>{
  const link=document.getElementById(id);
  link?.addEventListener('click',event=>{
    if(link.dataset.unconfigured==='true'){
      event.preventDefault();
      showLinkNote(`${link.textContent} destination is intentionally not invented. Connect the verified public URL before deployment.`);
    }
  });
});

function handleResize(){
  if(!state.data) return;
  const centerTime=timeForX((-state.offsetX)+(viewport.clientWidth/2));
  setupTimelineScale();
  renderTimeline();
  const newCenter=xForTime(centerTime);
  state.offsetX=(viewport.clientWidth/2)-newCenter;
  clampOffset();
  applyOffset();
}
window.addEventListener('resize',()=>{
  clearTimeout(handleResize.timer);
  handleResize.timer=setTimeout(handleResize,120);
});

async function boot(){
  try{
    state.data=await LINEAiGEData.load();
    state.recordsById.clear();
    state.data.records.forEach(record=>state.recordsById.set(record.id,record));
    setupTimelineScale();
    renderTimeline();
    updateToday();
    setInterval(updateToday,1000);
    applyOffset();
    document.documentElement.classList.add('record-ready');
  }catch(error){
    document.documentElement.classList.add('record-error');
    showLinkNote('LINEAiGE could not load its canonical record. Historical claims are withheld rather than guessed.');
  }
}

boot();
