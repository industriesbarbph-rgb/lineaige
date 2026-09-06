let records={};
const drawer=document.getElementById('drawer');
const statusEl=document.getElementById('status');
const dateEl=document.getElementById('date');
const titleEl=document.getElementById('title');
const summaryEl=document.getElementById('summary');
const relationsEl=document.getElementById('relations');
const evidenceEl=document.getElementById('evidence');
const circuits=[...document.querySelectorAll('.circuit')];
const eventNodes=[...document.querySelectorAll('[data-event]')];
const eventOrder=eventNodes.map(node=>node.dataset.event);
let activeId=null;

fetch('data/events.json')
  .then(r=>{if(!r.ok)throw new Error('record unavailable');return r.json()})
  .then(data=>{
    if(!data||!Array.isArray(data.events))throw new Error('invalid record');
    records=Object.fromEntries(data.events.filter(isUsableRecord).map(e=>[e.id,e]));
    if(!Object.keys(records).length)throw new Error('empty record');
    document.documentElement.classList.add('record-ready');
  })
  .catch(()=>document.documentElement.classList.add('record-error'));

function isUsableRecord(record){
  return record&&typeof record.id==='string'&&typeof record.title==='string'&&typeof record.summary==='string';
}

function energize(id){
  const index=eventOrder.indexOf(id);
  circuits.forEach((c,i)=>{
    c.classList.remove('active','wake');
    if(i===index)c.classList.add('active');
    else if(index>=0&&Math.abs(i-index)===1)c.classList.add('wake');
  });
  document.body.classList.add('energized');
  clearTimeout(energize.timer);
  energize.timer=setTimeout(()=>document.body.classList.remove('energized'),1200);
}

function selectNode(id){
  activeId=id;
  eventNodes.forEach(node=>node.classList.toggle('selected',node.dataset.event===id));
}

function openRecord(id){
  const record=records[id];
  if(!record)return;
  selectNode(id);
  energize(id);
  statusEl.textContent=record.status||'RECORD';
  dateEl.textContent=record.displayDate||record.date||'—';
  titleEl.textContent=record.title;
  summaryEl.textContent=record.summary;
  renderEvidence(record);
  renderRelationships(record);
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden','false');
}

function renderEvidence(record){
  const sourceCount=Array.isArray(record.sources)?record.sources.length:0;
  const verification=record.verification?.state;
  if(verification==='navigation-only'){
    evidenceEl.textContent='Navigation entry point only. It is not presented as a verified historical claim. Verified event records will expose their source trail here.';
    return;
  }
  if(sourceCount===0){
    evidenceEl.textContent='No publishable source trail is attached to this record yet.';
    return;
  }
  evidenceEl.textContent=`${sourceCount} source${sourceCount===1?'':'s'} attached to this record. Relationship claims remain distinct from chronology and context.`;
}

function renderRelationships(record){
  relationsEl.replaceChildren();
  const relationships=Array.isArray(record.relationships)?record.relationships:
    Array.isArray(record.relations)?record.relations.map(label=>({label,evidenceState:'navigation-only',targetId:null})):[];

  relationships.forEach((relationship,index)=>{
    const button=document.createElement('button');
    button.className='relation';
    button.style.setProperty('--delay',`${index*70}ms`);
    button.type='button';
    if(relationship.targetId)button.dataset.target=relationship.targetId;
    const dot=document.createElement('span');
    dot.setAttribute('aria-hidden','true');
    const label=document.createTextNode(relationship.label||'Related record');
    button.append(dot,label);
    button.addEventListener('click',()=>followRelationship(button,relationship));
    relationsEl.appendChild(button);
  });
}

function followRelationship(button,relationship){
  const targetId=relationship.targetId;
  if(targetId&&records[targetId]){
    button.animate([
      {opacity:.55,transform:'translateX(0)'},
      {opacity:1,transform:'translateX(7px)'},
      {opacity:.72,transform:'translateX(0)'}
    ],{duration:340,easing:'ease-out'}).finished.catch(()=>{}).finally(()=>openRecord(targetId));
    return;
  }
  flashRelation(button);
}

function flashRelation(button){
  if(!activeId)return;
  const idx=eventOrder.indexOf(activeId);
  circuits.forEach(c=>c.classList.remove('active','wake'));
  const target=circuits[Math.max(0,Math.min(circuits.length-1,idx))];
  target?.classList.add('active');
  button.animate([
    {opacity:.55,transform:'translateX(0)'},
    {opacity:1,transform:'translateX(7px)'},
    {opacity:.72,transform:'translateX(0)'}
  ],{duration:520,easing:'ease-out'});
}

function closeDrawer(){
  drawer.classList.remove('open');
  drawer.setAttribute('aria-hidden','true');
  eventNodes.forEach(node=>node.classList.remove('selected'));
  activeId=null;
}

eventNodes.forEach(node=>{
  node.addEventListener('pointerenter',()=>energize(node.dataset.event));
  node.addEventListener('focus',()=>energize(node.dataset.event));
  node.addEventListener('click',()=>openRecord(node.dataset.event));
});

document.getElementById('close').addEventListener('click',closeDrawer);
document.addEventListener('keydown',event=>{
  if(event.key==='Escape')closeDrawer();
  const current=document.activeElement?.dataset?.event;
  const idx=eventOrder.indexOf(current);
  if((event.key==='ArrowRight'||event.key==='ArrowLeft')&&idx>=0){
    event.preventDefault();
    const next=event.key==='ArrowRight'?Math.min(idx+1,eventOrder.length-1):Math.max(idx-1,0);
    eventNodes[next]?.focus();
    energize(eventOrder[next]);
  }
  if(event.key==='Enter'&&current)openRecord(current);
});
