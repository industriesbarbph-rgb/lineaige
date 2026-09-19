(function(global){
  'use strict';

  const EVENTS_URL='data/events.json';
  const COURSES_URL='data/courses.json';
  const CREATOR_RELEASES_URL='data/creator-releases.json';

  function usableRecord(record){
    return Boolean(
      record &&
      typeof record.id==='string' &&
      typeof record.title==='string'
    );
  }

  function parseDay(value){
    if(typeof value!=='string') return Number.POSITIVE_INFINITY;
    const parsed=Date.parse(value+'T00:00:00Z');
    return Number.isFinite(parsed) ? parsed : Number.POSITIVE_INFINITY;
  }

  function temporalValue(record){
    const precision=record.datePrecision || (record.eventDate ? 'day' : null);
    if(precision==='day' && record.eventDate) return parseDay(record.eventDate);
    if(precision==='month' && record.eventMonth) return parseDay(record.eventMonth+'-01');
    if(precision==='year' && record.eventYear) return parseDay(record.eventYear+'-01-01');
    return Number.POSITIVE_INFINITY;
  }

  function futureTargetValue(record){
    const precision=record.targetPrecision ||
      (record.targetDate ? 'day' : record.targetMonth ? 'month' : record.targetYear ? 'year' : 'unknown');

    if(precision==='day' && record.targetDate) return parseDay(record.targetDate);
    if(precision==='month' && record.targetMonth) return parseDay(record.targetMonth+'-01');
    if(precision==='year' && record.targetYear) return parseDay(record.targetYear+'-01-01');

    return parseDay(record.announcementDate);
  }

  function learningTemporalValue(item){
    const precision=item.startPrecision ||
      (item.startDate ? 'day' : item.startMonth ? 'month' : item.startYear ? 'year' : null);
    if(precision==='day' && item.startDate) return parseDay(item.startDate);
    if(precision==='month' && item.startMonth) return parseDay(item.startMonth+'-01');
    if(precision==='year' && item.startYear) return parseDay(item.startYear+'-01-01');
    return Number.POSITIVE_INFINITY;
  }

  function learningEndValue(item){
    if(item.endDate) return parseDay(item.endDate);
    if(item.endMonth) return parseDay(item.endMonth+'-01');
    if(item.endYear) return parseDay(item.endYear+'-01-01');
    return Number.POSITIVE_INFINITY;
  }

  function creatorTemporalValue(item){
    const precision=item.releasePrecision ||
      (item.releaseDate ? 'day' : item.releaseMonth ? 'month' : item.releaseYear ? 'year' : null);
    if(precision==='day' && item.releaseDate) return parseDay(item.releaseDate);
    if(precision==='month' && item.releaseMonth) return parseDay(item.releaseMonth+'-01');
    if(precision==='year' && item.releaseYear) return parseDay(item.releaseYear+'-01-01');
    return Number.POSITIVE_INFINITY;
  }

  function partitionCanonicalRecords(events){
    const records=events.filter(usableRecord);

    const recorded=records
      .filter(record=>record.recordType==='event' || record.recordType==='entry_point')
      .slice()
      .sort((a,b)=>temporalValue(a)-temporalValue(b) || a.id.localeCompare(b.id));

    const now=records.find(record=>record.id==='now' && record.recordType==='living_edge') || null;

    const announcedFuture=records
      .filter(record=>record.recordType==='announced_future')
      .slice()
      .sort((a,b)=>futureTargetValue(a)-futureTargetValue(b) || a.id.localeCompare(b.id));

    return {recorded,now,announcedFuture};
  }

  function canonicalTimelineRecords(events){
    const {recorded,now,announcedFuture}=partitionCanonicalRecords(events);
    return [...recorded,...(now ? [now] : []),...announcedFuture];
  }

  async function fetchJson(url,required){
    try{
      const response=await fetch(url,{cache:'no-store'});
      if(!response.ok){
        if(required) throw new Error(`${url} unavailable (${response.status})`);
        return null;
      }
      return await response.json();
    }catch(error){
      if(required) throw error;
      return null;
    }
  }

  async function load(){
    const [eventData,courseData,creatorData]=await Promise.all([
      fetchJson(EVENTS_URL,true),
      fetchJson(COURSES_URL,false),
      fetchJson(CREATOR_RELEASES_URL,false)
    ]);

    if(!eventData || !Array.isArray(eventData.events)) throw new Error('invalid canonical record document');

    const partitioned=partitionCanonicalRecords(eventData.events);
    const timeline=[...partitioned.recorded,...(partitioned.now ? [partitioned.now] : []),...partitioned.announcedFuture];
    if(!timeline.length) throw new Error('canonical record document is empty');

    const courses=Array.isArray(courseData?.items) ? courseData.items.filter(usableRecord) : [];
    const creatorReleases=Array.isArray(creatorData?.items) ? creatorData.items.filter(usableRecord) : [];

    return {
      schemaVersion:eventData.schemaVersion || null,
      product:eventData.product || 'LINEAiGE',
      principle:eventData.principle || null,
      records:timeline,
      recorded:partitioned.recorded,
      now:partitioned.now,
      announcedFuture:partitioned.announcedFuture,
      courses,
      creatorReleases
    };
  }

  global.LINEAiGEData=Object.freeze({
    EVENTS_URL,
    COURSES_URL,
    CREATOR_RELEASES_URL,
    load,
    canonicalTimelineRecords,
    partitionCanonicalRecords,
    temporalValue,
    futureTargetValue,
    learningTemporalValue,
    learningEndValue,
    creatorTemporalValue
  });
})(window);
