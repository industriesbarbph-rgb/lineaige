'use strict';

let mediaByEvent={};
let currentMediaEventId=null;

const mediaPanel=document.createElement('section');
mediaPanel.className='media-panel';
mediaPanel.hidden=true;
mediaPanel.innerHTML=`
  <div class="media-kicker">CONTEXT MEDIA</div>
  <div class="media-frame-wrap"><iframe id="mediaFrame" title="LINEAiGE context media" loading="lazy" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe></div>
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
.media-kicker{font-size:8px;font-weight:800;letter-spacing:.18em;color:#72655f;margin-bottom:11px}
.media-frame-wrap{position:relative;width:100%;aspect-ratio:16/9;background:#ddd6cb;border:1px solid rgba(64,60,55,.18);overflow:hidden}
.media-frame-wrap iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.media-title{display:block;margin-top:11px;color:#37332f;text-decoration:none;font-family:Georgia,"Times New Roman",serif;font-size:12px;line-height:1.45}
.media-title:hover,.media-title:focus-visible{text-decoration:underline;outline:2px solid rgba(48,48,45,.55);outline-offset:3px}
.media-meta{margin-top:5px;font-size:8px;letter-spacing:.08em;color:#777067}
.media-note{margin:8px 0 0!important;font-size:10px!important;line-height:1.55!important;color:#716a63!important}
`;
document.head.appendChild(mediaStyle);

fetch('data/media.json')
  .then(r=>{if(!r.ok)throw new Error('media unavailable');return r.json()})
  .then(data=>{
    const items=Array.isArray(data.items)?data.items:[];
    mediaByEvent=items.reduce((map,item)=>{
      if(!item||typeof item.eventId!=='string')return map;
      if(!map[item.eventId])map[item.eventId]=[];
      map[item.eventId].push(item);
      return map;
    },{});
    if(currentMediaEventId)showMediaForEvent(currentMediaEventId);
  })
  .catch(()=>{});

function showMediaForEvent(eventId){
  currentMediaEventId=eventId;
  const item=mediaByEvent[eventId]?.[0];
  if(!item||!item.embedUrl||!item.watchUrl){
    mediaPanel.hidden=true;
    mediaFrame.removeAttribute('src');
    return;
  }
  mediaPanel.hidden=false;
  if(mediaFrame.src!==item.embedUrl)mediaFrame.src=item.embedUrl;
  mediaTitle.textContent=item.title||'Open media source';
  mediaTitle.href=item.watchUrl;
  mediaMeta.textContent=[item.creator,item.publishedDate].filter(Boolean).join(' · ');
  mediaNote.textContent=item.note||'';
}

function clearMedia(){
  currentMediaEventId=null;
  mediaFrame.removeAttribute('src');
  mediaPanel.hidden=true;
}

document.addEventListener('lineaige:record-opened',event=>showMediaForEvent(event.detail?.id));
document.addEventListener('lineaige:record-closed',clearMedia);
