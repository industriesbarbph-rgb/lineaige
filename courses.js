'use strict';

let coursesByEvent={};
let currentCourseEventId=null;

const coursesPanel=document.createElement('section');
coursesPanel.className='courses-panel';
coursesPanel.hidden=true;
coursesPanel.innerHTML=`
  <div class="courses-kicker">LEARN THIS</div>
  <div class="courses-intro">Reviewed learning resources connected to this record. Learning material is not historical proof.</div>
  <div id="coursesList" class="courses-list"></div>`;

document.getElementById('drawer')?.appendChild(coursesPanel);
const coursesList=coursesPanel.querySelector('#coursesList');

const coursesStyle=document.createElement('style');
coursesStyle.textContent=`
.courses-kicker{font-size:8px;font-weight:800;letter-spacing:.18em;color:#5c6570;margin-bottom:8px}
.courses-intro{font-family:Georgia,"Times New Roman",serif;font-size:11px;line-height:1.55;color:#6f6962;margin-bottom:12px}
.courses-list{display:grid;gap:9px}
.course-card{display:block;padding:11px 12px 12px;border-left:3px solid rgba(68,101,138,.48);background:rgba(255,255,255,.24);color:#34312e;text-decoration:none}
.course-card:hover,.course-card:focus-visible{background:rgba(255,255,255,.5);outline:2px solid rgba(48,48,45,.55);outline-offset:3px}
.course-badges{display:flex;gap:5px;flex-wrap:wrap;margin-bottom:7px}
.course-badge{font-size:6px;letter-spacing:.11em;padding:3px 5px;border:1px solid rgba(68,101,138,.24);color:#5a6673}
.course-title{font-family:Georgia,"Times New Roman",serif;font-size:12px;line-height:1.4}
.course-meta{font-size:8px;line-height:1.45;color:#777067;margin-top:4px}
`;
document.head.appendChild(coursesStyle);

fetch('data/courses.json')
  .then(r=>{if(!r.ok)throw new Error('courses unavailable');return r.json()})
  .then(data=>{
    const items=Array.isArray(data.items)?data.items:[];
    coursesByEvent=items.reduce((map,item)=>{
      if(!item||!Array.isArray(item.eventIds))return map;
      item.eventIds.forEach(eventId=>{
        if(!map[eventId])map[eventId]=[];
        map[eventId].push(item);
      });
      return map;
    },{});
    if(currentCourseEventId)showCoursesForEvent(currentCourseEventId);
  })
  .catch(()=>{});

function showCoursesForEvent(eventId){
  currentCourseEventId=eventId;
  const items=coursesByEvent[eventId]||[];
  coursesList.replaceChildren();
  if(!items.length){
    coursesPanel.hidden=true;
    return;
  }
  coursesPanel.hidden=false;

  items.forEach(item=>{
    if(!item||!item.courseUrl||!item.title)return;
    const card=document.createElement('a');
    card.className='course-card';
    card.href=item.courseUrl;
    card.target='_blank';
    card.rel='noopener noreferrer';

    const badges=document.createElement('div');
    badges.className='course-badges';
    [item.providerType,item.level,item.access].filter(Boolean).forEach(value=>{
      const badge=document.createElement('span');
      badge.className='course-badge';
      badge.textContent=String(value).replaceAll('-',' ').toUpperCase();
      badges.appendChild(badge);
    });

    const title=document.createElement('div');
    title.className='course-title';
    title.textContent=item.title;

    const meta=document.createElement('div');
    meta.className='course-meta';
    const start=item.startYear ? 'STARTED '+item.startYear : null;
    meta.textContent=[item.institution,item.provider,start].filter(Boolean).join(' · ');

    card.append(badges,title,meta);
    coursesList.appendChild(card);
  });
}

function clearCourses(){
  currentCourseEventId=null;
  coursesList.replaceChildren();
  coursesPanel.hidden=true;
}

document.addEventListener('lineaige:record-opened',event=>showCoursesForEvent(event.detail?.id));
document.addEventListener('lineaige:record-closed',clearCourses);
