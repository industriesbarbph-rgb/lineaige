let records={};
const drawer=document.getElementById('drawer');
const statusEl=document.getElementById('status');
const dateEl=document.getElementById('date');
const titleEl=document.getElementById('title');
const summaryEl=document.getElementById('summary');
const relationsEl=document.getElementById('relations');

fetch('data/events.json').then(r=>r.json()).then(data=>{
  records=Object.fromEntries(data.events.map(e=>[e.id,e]));
}).catch(()=>{});

document.querySelectorAll('[data-event]').forEach(node=>node.addEventListener('click',()=>{
  const e=records[node.dataset.event];
  if(!e)return;
  statusEl.textContent=e.status;
  dateEl.textContent=e.date;
  titleEl.textContent=e.title;
  summaryEl.textContent=e.summary;
  relationsEl.innerHTML=e.relations.map(x=>`<span>${x}</span>`).join('');
  drawer.classList.add('open');
}));

document.getElementById('close').addEventListener('click',()=>drawer.classList.remove('open'));
document.addEventListener('keydown',e=>{if(e.key==='Escape')drawer.classList.remove('open')});
