# LINEAiGE

A living evidence-traversal system for seeing and investigating the evolution of artificial intelligence—past, present, and announced future.

## Architectural truth

**The historical record is LINEAiGE. The interface is a representation of LINEAiGE.**

LINEAiGE is designed around zero irreplaceable dependencies. The public interface is static HTML/CSS/JavaScript. Historical records, contextual media and learning resources are stored separately in portable structured data so the interface can change without becoming the source of truth.

## Time model

- **Past** — recorded evidence.
- **Now** — the living edge where history is forming.
- **Announced future** — documented intentions, targets, proposals and plans; never represented as accomplished fact.

## Evidence rule

Chronology alone is never presented as causality. Relationships must be supported, classified and inspectable. Primary evidence, secondary evidence, contextual media and learning resources remain visibly distinct.

## Current data layers

- `data/events.json` — canonical historical and living-edge records.
- `data/event.schema.json` — portable event/source/relationship schema.
- `data/media.json` — supplemental public media attached to records; context is not automatically historical proof.
- `data/courses.json` — AI learning resources from universities, schools, platforms and providers; courses are a learning layer, not historical evidence.

## Interface structure

- `index.html` — primary beam interface and evidence drawer.
- `lineaige.css` — colorless-light visual system and responsive layout.
- `lineaige.js` — canonical record loading, source rendering, traversal and shared record lifecycle events.
- `media.js` — contextual media renderer synchronized to every record traversal path.
- `courses.js` — learning-resource renderer synchronized to every record traversal path.

## Traversal contract

Every successful record opening emits the same `lineaige:record-opened` event, whether the visitor enters from the beam or follows a relationship. Supplemental layers listen to that shared lifecycle instead of maintaining separate navigation state. Closing the record emits `lineaige:record-closed` so embedded media and supplemental panels can release their state cleanly.

## Graceful failure

The core historical drawer remains usable if supplemental media or course data fail to load. Missing supplemental data is hidden rather than represented as evidence. If the canonical record cannot load, the interface marks the record layer offline instead of fabricating content.

## Deployment checklist

Before deployment, verify that every beam `data-event` maps to a canonical record, every relationship target resolves or is intentionally null, every supplemental `eventId`/`eventIds` maps to a canonical record, JSON files parse cleanly, source URLs use valid public destinations, keyboard traversal and Escape work, mobile drawer content remains scrollable, reduced-motion behavior is respected, and the static build runs without requiring a framework, database, login or proprietary runtime.

Established September 6, 2026.
