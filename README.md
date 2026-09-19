# LINEAiGE

A living evidence-traversal system for seeing and investigating the evolution of artificial intelligence—past, present, and announced future.

## Architectural truth

**The historical record is LINEAiGE. The interface is a representation of LINEAiGE.**

LINEAiGE is designed around zero irreplaceable dependencies. Historical records, contextual media, learning resources, research-review material and candidate records are stored separately in portable structured data so the public renderer can change without becoming the source of truth.

## Official public renderer

The selected production direction is the **Pencil Theme**.

Its material language is textured artist paper, graphite, charcoal and colored pencil. It must render canonical LINEAiGE data rather than hard-code a small set of historical nodes.

The September 6 Beam-Light interface family is discarded as a production direction. The existing Beam-era frontend files on the working branch are transitional only and must be replaced before deployment.

See `docs/pencil-theme-official-contract.md` for the production build contract.

## Time model

- **Past** — recorded evidence.
- **TODAY** — the living edge, rendered with the visitor’s current local date and time at runtime.
- **Announced future** — documented intentions, targets, proposals and plans; never represented as accomplished fact.

No decorative future marker is itself evidence.

## Evidence rule

Chronology alone is never presented as causality. Relationships must be supported, classified and inspectable. Primary evidence, secondary evidence, contextual media and learning resources remain visibly distinct.

Unsupported precision is withheld rather than manufactured.

## Current data layers

- `data/events.json` — canonical historical and living-edge records.
- `data/event.schema.json` — portable event/source/relationship schema.
- `data/candidates/` — evidence-controlled candidate records awaiting deliberate canonical admission.
- `data/research-ledger.json` — research that is held back, under review, or preserved as a resolved canonical-review trail.
- `data/media.json` — supplemental public media attached to records; context is not automatically historical proof.
- `data/courses.json` — learning resources; courses are a learning layer, not historical evidence.

## Renderer architecture

- `lineaige-data.js` — neutral canonical timeline data adapter and temporal ordering.
- `index.html` — public renderer shell; to be replaced by the official Pencil Theme before deployment.
- `lineaige.js` — record interaction, traversal, source rendering and shared lifecycle behavior.
- `lineaige.css` — renderer styling; current Beam-era styling is transitional and is not the production direction.
- `media.js` — contextual media synchronized to record traversal.
- `courses.js` — learning-resource rendering synchronized to record traversal.

## Data-driven rule

The HTML must not define the historical inventory.

`data/events.json` determines which canonical records exist. The Pencil renderer must generate the public timeline from the canonical data through `lineaige-data.js`.

Candidate and research-ledger files must not be silently rendered as canonical history.


## Authorship provenance

Every canonical public record carries `entryOrigin`:
- `lineaige` for records added through the LINEAiGE editorial/evidence operation;
- `co-author` for approved public co-author contributions.

The Pencil Theme renders these with distinct authorship marks and readable labels. Color is not the sole indicator. Co-author approval never erases contributor metadata.

Authorship origin and temporal status are separate: an announced-future record can be LINEAiGE-added or co-author-added while still remaining visibly unresolved.

## Shared traversal contract

Every successful record opening emits `lineaige:record-opened`, regardless of whether the visitor enters from a timeline mark or follows a relationship. Supplemental layers listen to that lifecycle instead of maintaining separate navigation state.

Closing a record emits `lineaige:record-closed` so supplemental layers can release their state cleanly.

## Graceful failure

The core historical record view remains usable if supplemental media or course data fail to load. Missing supplemental data is hidden rather than represented as evidence. If canonical data cannot load, the interface must visibly fail closed instead of fabricating content.

## Deployment rule

Before deployment, verify canonical and research data, chronology, relationship semantics, global coverage, frontend accessibility, responsive behavior, static delivery, JavaScript syntax, real-device Android/iPhone behavior, and the exact commit intended for production.

Deployment must use the exact validated repository state.

Established September 6, 2026.
