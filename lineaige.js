let records={};
const drawer=document.getElementById('drawer');
const statusEl=document.getElementById('status');
const dateEl=document.getElementById('date');
const titleEl=document.getElementById('title');
const summaryEl=document.getElementById('summary');
const relationsEl=document.getElementById('relations');
const circuits=[...document.querySelectorAll('.circuit')];
const eventNodes=[...document.querySelectorAll('[data-event]')];
const eventOrder=['foundations','learning','deep','transformer','generative','now'];

fetch('data/events.json')
  .then(r=>{if(!r.ok)throw new Error('record unavailable');return r.json()})
  .then(data=>{records=Object.fromEntries(data.events.map(e=>[e.id,e]));document.documentElement.classList.add('record-ready')})
  .catch(()=>document.documentElement.classList.add('record-error'));

function energize(id){
  const index=eventOrder.indexOf(id);
  circuits.forEach((c,i)=>{
    c.classList.remove('active','wake');
    if(i===index)c.classList.add('active');
    else if(Math.abs(i-index)===1)c.classList.add('wake');
  });
  document.body.classList.add('energized');
  clearTimeout(energize.timer);
  energize.timer=setTimeout(()=>document.body.classList.remove('energized'),1200);
}

function openRecord(id){
  const e=records[id];
  if(!e)return;
  energize(id);
  statusEl.textContent=e.status;
  dateEl.textContent=e.date;
  titleEl.textContent=e.title;
  summaryEl.textContent=e.summary;
  relationsEl.innerHTML=e.relations.map((x,i)=>`<button class="relation" style="--delay:${i*70}ms"><span></span>${x}</button>`).join('');
  drawer.classList.add('open');
}

eventNodes.forEach(node=>{
  node.addEventListener('pointerenter',()=>energize(node.dataset.event));
  node.addEventListener('click',()=>openRecord(node.dataset.event));
});

document.getElementById('close').addEventListener('click',()=>drawer.classList.remove('open'));
document.addEventListener('keydown',e=>{
  if(e.key==='Escape')drawer.classList.remove('open');
  const current=document.activeElement?.dataset?.event;
  const idx=eventOrder.indexOf(current);
  if((e.key==='ArrowRight'||e.key==='ArrowLeft')&&idx>=0){
    const next=e.key==='ArrowRight'?Math.min(idx+1,eventOrder.length-1):Math.max(idx-1,0);
    const node=document.querySelector(`[data-event="${eventOrder[next]}"]`);
    node?.focus();energize(eventOrder[next]);
  }
});
