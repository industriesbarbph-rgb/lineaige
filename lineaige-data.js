(function(global){
  'use strict';

  const EVENTS_URL='data/events.json';

  function usableRecord(record){
    return Boolean(
      record &&
      typeof record.id==='string' &&
      typeof record.title==='string' &&
      typeof record.summary==='string' &&
      typeof record.recordType==='string'
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

  async function load(){
    const response=await fetch(EVENTS_URL,{cache:'no-store'});
    if(!response.ok) throw new Error(`canonical record unavailable (${response.status})`);

    const data=await response.json();
    if(!data || !Array.isArray(data.events)) throw new Error('invalid canonical record document');

    const partitioned=partitionCanonicalRecords(data.events);
    const timeline=[...partitioned.recorded,...(partitioned.now ? [partitioned.now] : []),...partitioned.announcedFuture];
    if(!timeline.length) throw new Error('canonical record document is empty');

    return {
      schemaVersion:data.schemaVersion || null,
      product:data.product || 'LINEAiGE',
      principle:data.principle || null,
      records:timeline,
      recorded:partitioned.recorded,
      now:partitioned.now,
      announcedFuture:partitioned.announcedFuture
    };
  }

  global.LINEAiGEData=Object.freeze({
    EVENTS_URL,
    load,
    canonicalTimelineRecords,
    partitionCanonicalRecords,
    temporalValue,
    futureTargetValue
  });
})(window);
