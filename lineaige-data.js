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

  function temporalValue(record){
    if(record.recordType==='living_edge') return Number.POSITIVE_INFINITY;

    const precision=record.datePrecision || (record.eventDate ? 'day' : null);
    if(precision==='day' && record.eventDate){
      const value=Date.parse(record.eventDate+'T00:00:00Z');
      return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
    }
    if(precision==='month' && record.eventMonth){
      const value=Date.parse(record.eventMonth+'-01T00:00:00Z');
      return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
    }
    if(precision==='year' && record.eventYear){
      const value=Date.parse(record.eventYear+'-01-01T00:00:00Z');
      return Number.isFinite(value) ? value : Number.POSITIVE_INFINITY;
    }
    return Number.POSITIVE_INFINITY;
  }

  function canonicalTimelineRecords(events){
    const records=events.filter(usableRecord);
    const recorded=records
      .filter(record=>record.recordType!=='living_edge')
      .slice()
      .sort((a,b)=>temporalValue(a)-temporalValue(b) || a.id.localeCompare(b.id));
    const now=records.find(record=>record.id==='now' && record.recordType==='living_edge') || null;
    return now ? [...recorded, now] : recorded;
  }

  async function load(){
    const response=await fetch(EVENTS_URL,{cache:'no-store'});
    if(!response.ok) throw new Error(`canonical record unavailable (${response.status})`);

    const data=await response.json();
    if(!data || !Array.isArray(data.events)) throw new Error('invalid canonical record document');

    const timeline=canonicalTimelineRecords(data.events);
    if(!timeline.length) throw new Error('canonical record document is empty');

    return {
      schemaVersion:data.schemaVersion || null,
      product:data.product || 'LINEAiGE',
      principle:data.principle || null,
      records:timeline,
      recorded:timeline.filter(record=>record.recordType!=='living_edge'),
      now:timeline.find(record=>record.id==='now') || null
    };
  }

  global.LINEAiGEData=Object.freeze({
    EVENTS_URL,
    load,
    canonicalTimelineRecords,
    temporalValue
  });
})(window);
