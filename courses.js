let coursesByEvent={};
let currentCourseEventId=null;

const coursesPanel=document.createElement('section');
coursesPanel.className='courses-panel';
coursesPanel.hidden=true;
coursesPanel.innerHTML=`
  <div class="courses-kicker">LEARN THIS ERA · AI COURSES</div>
  <div class="courses-intro">University, school, platform and provider courses are kept separate from historical evidence.</div>
  <div id="coursesList" class="courses-list"></div>`;

document.getElementById('drawer')?.appendChild(coursesPanel);
const coursesList=coursesPanel.querySelector('#coursesList');

const coursesStyle=document.createElement('style');
coursesStyle.textContent=`
.courses-panel{margin-top:28px;padding-top:22px;border-top:1px solid rgba(255,255,255,.12)}
.courses-kicker{font-size:9px;letter-spacing:.28em;color:rgba(255,255,255,.48);margin-bottom:9px}
.courses-intro{font-size:10px;line-height:1.55;color:rgba(255,255,255,.34);margin-bottom:14px}
.courses-list{display:grid;gap:10px}
.course-card{display:block;padding:13px 14px;border:1px solid rgba(255,255,255,.1);background:rgba(255,255,255,.025);color:#fff;text-decoration:none;transition:border-color .2s,background .2s,transform .2s}
.course-card:hover,.course-card:focus-visible{border-color:rgba(255,255,255,.28);background:rgba(255,255,255,.05);transform:translateX(2px);outline:1px solid rgba(255,255,255,.35);outline-offset:3px}
.course-badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}
.course-badge{font-size:7px;letter-spacing:.14em;padding:4px 6px;border:1px solid rgba(255,255,255,.12);color:rgba(255,255,255,.46)}
.course-title{font-size:12px;line-height:1.4}
.course-meta{font-size:9px;line-height:1.5;color:rgba(255,255,255,.38);margin-top:5px}
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
    [item.providerType,item.level,item.access].filter(Boolean).forEach(text=>{
      const badge=document.createElement('span');
      badge.className='course-badge';
      badge.textContent=String(text).replaceAll('-',' ').toUpperCase();
      badges.appendChild(badge);
    });

    const title=document.createElement('div');
    title.className='course-title';
    title.textContent=item.title;
    const meta=document.createElement('div');
    meta.className='course-meta';
    meta.textContent=[item.institution,item.provider].filter(Boolean).join(' · ');
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
