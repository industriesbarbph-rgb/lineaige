let mediaByEvent={};

const mediaPanel=document.createElement('section');
mediaPanel.className='media-panel';
mediaPanel.hidden=true;
mediaPanel.innerHTML=`
  <div class="media-kicker">YOUTUBE · CONTEXT SOURCE</div>
  <div class="media-frame-wrap"><iframe id="mediaFrame" title="LINEAiGE YouTube source" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>
  <a id="mediaTitle" class="media-title" target="_blank" rel="noopener noreferrer"></a>
  <div id="mediaMeta" class="media-meta"></div>
  <p id="mediaNote" class="media-note"></p>`;

document.getElementById('drawer')?.appendChild(mediaPanel);

const mediaFrame=mediaPanel.querySelector('#mediaFrame');
const mediaTitle=mediaPanel.querySelector('#mediaTitle');
const mediaMeta=mediaPanel.querySelector('#mediaMeta');
const mediaNote=mediaPanel.querySelector('#mediaNote');

const mediaStyle=document.createElement('style');
mediaStyle.textContent=`
.media-panel{margin-top:28px;padding-top:22px;border-top:1px solid rgba(255,255,255,.12)}
.media-kicker{font-size:9px;letter-spacing:.28em;color:rgba(255,255,255,.48);margin-bottom:14px}
.media-frame-wrap{position:relative;width:100%;aspect-ratio:16/9;background:#000;border:1px solid rgba(255,255,255,.12);overflow:hidden;box-shadow:0 0 28px rgba(255,255,255,.06)}
.media-frame-wrap iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.media-title{display:block;margin-top:14px;color:#fff;text-decoration:none;font-size:12px;line-height:1.45}
.media-title:hover{text-decoration:underline}
.media-meta{margin-top:7px;font-size:9px;letter-spacing:.12em;color:rgba(255,255,255,.4)}
.media-note{margin:10px 0 0!important;font-size:10px!important;line-height:1.55!important;color:rgba(255,255,255,.42)!important}
`;
document.head.appendChild(mediaStyle);

fetch('data/media.json')
  .then(r=>{if(!r.ok)throw new Error('media unavailable');return r.json()})
  .then(data=>{
    const items=Array.isArray(data.items)?data.items:[];
    mediaByEvent=items.reduce((map,item)=>{
      if(!map[item.eventId])map[item.eventId]=[];
      map[item.eventId].push(item);
      return map;
    },{});
  })
  .catch(()=>{});

function showMediaForEvent(eventId){
  const item=mediaByEvent[eventId]?.[0];
  if(!item){
    mediaPanel.hidden=true;
    mediaFrame.removeAttribute('src');
    return;
  }
  mediaPanel.hidden=false;
  mediaFrame.src=item.embedUrl;
  mediaTitle.textContent=item.title;
  mediaTitle.href=item.watchUrl;
  mediaMeta.textContent=[item.creator,item.publishedDate].filter(Boolean).join(' · ');
  mediaNote.textContent=item.note||'';
}

document.querySelectorAll('[data-event]').forEach(node=>{
  node.addEventListener('click',()=>setTimeout(()=>showMediaForEvent(node.dataset.event),0));
});

document.getElementById('close')?.addEventListener('click',()=>{
  mediaFrame.removeAttribute('src');
  mediaPanel.hidden=true;
});
