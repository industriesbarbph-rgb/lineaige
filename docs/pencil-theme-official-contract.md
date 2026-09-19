# LINEAiGE Pencil Theme — Official Build Contract

Status: official production direction selected 19 September 2026.

This document governs the public LINEAiGE Pencil Theme build. It is not a concept study, demo, prototype, or alternate project.

## Product truth

- LINEAiGE is the evidence-controlled historical system.
- The Pencil Theme is the official public renderer being prepared for deployment.
- The interface must never become the historical source of truth.
- Canonical data, evidence, relationships, learning resources, contextual media, and research/candidate layers remain structurally separate.

## Public historical surface

The public historical timeline renders records from `data/events.json`.

For this deployment:
- publish canonical recorded history;
- publish the `now` living-edge record;
- do not render `data/candidates/` as canonical history;
- do not convert research-ledger items into public historical events;
- do not fabricate announced-future events.

When future records exist, they must come from an evidence-controlled structured layer and remain visibly distinct from accomplished history.

## Data-driven rendering

The HTML must not hard-code the canonical event inventory.

`data/events.json` determines which canonical records exist. The renderer must generate the timeline from that data through the neutral data adapter in `lineaige-data.js`.

A new canonical record should become eligible for the Pencil Theme without manually adding a new hard-coded event node to HTML.


## Authorship provenance and color coding

Every canonical public record carries an `entryOrigin` value:
- `lineaige` — information added through the LINEAiGE editorial/evidence operation;
- `co-author` — information submitted by a public co-author and admitted after moderation and evidence review.

The Pencil Theme must make that distinction visible at a glance.

Origin styling is separate from historical status:
- LINEAiGE-added material uses the core graphite/charcoal authorship mark;
- approved co-author material uses a distinct colored-pencil authorship mark;
- both also carry a readable text label such as `LINEAiGE` or `CO-AUTHOR`, so color is never the only signal.

A co-author record must retain contributor metadata. Approval does not erase authorship.

Historical/future state is an independent visual dimension. For example, a co-author may contribute an announced-future record: its co-author color remains, while its future/unresolved treatment still shows that the plan has not happened.

Existing canonical records are marked `entryOrigin: lineaige`. From this point forward, origin metadata is mandatory for every canonical record.

## Pencil visual language

Official material language:
- textured artist paper;
- graphite;
- charcoal;
- colored pencil;
- visible hand-made marks with controlled legibility;
- one strong left-to-right charcoal timeline;
- handwritten-feeling labels and notes;
- no glossy dashboard treatment;
- no boxes around every record;
- no Beam-Light circuitry, luminous orb, future particles, or colorless-light visual DNA.

The September 6 Beam-Light implementation is discarded and must not be used as the design basis.

## Time architecture

- Past occupies the historical body of the timeline.
- The living edge is presented publicly as **TODAY**, not a frozen `NOW` label.
- TODAY renders the visitor's actual current local date and time at runtime using the browser/device locale and time zone.
- The clock remains live while the page is open.
- The visitor's local time must not be stored as historical evidence.
- No precise-location permission is required merely to show local date/time; the renderer uses the visitor's browser/device time-zone context.
- Space after TODAY is reserved for evidence-backed announced-future records.
- Empty future space must remain empty rather than being populated with decorative pseudo-events.
- Announced-future records are ordered separately from historical events and remain visibly unresolved until evidence changes their status.
- Visual placement must be derived from temporal data rather than fixed per-event coordinates.

## Interaction contract

The Pencil Theme must support:
- dragging through time;
- progressive charcoal/shading response as the visitor moves through the timeline;
- tapping/clicking a record to open its canonical summary and evidence;
- visible source trail;
- source links opening in a new tab;
- relationship traversal without implying unsupported causality;
- keyboard navigation;
- Escape to close record detail;
- focus restoration after closing;
- reduced-motion behavior.

Supplemental media and learning resources remain listeners to the shared `lineaige:record-opened` and `lineaige:record-closed` lifecycle.

## Mobile contract

The production interface must be designed for touch first as well as desktop:
- direct finger drag without browser-zoom tricks;
- no twitch-producing transform loop;
- sufficiently large tap targets;
- readable record detail without gesture conflict;
- scrollable detail content;
- real-device Android and iPhone verification before production deployment.

## Evidence display

Every displayed historical claim must remain traceable to its canonical source trail.

The renderer must expose, where present:
- record status;
- temporal precision;
- summary;
- significance;
- evidence/source roles;
- geography context;
- relationships and their evidence state;
- corrections.

Chronology must not be presented as causality.

## Release rule

No production deployment until:
- canonical data validation is green;
- research/candidate audits are green;
- chronology is green;
- frontend accessibility and graceful-failure audits are green;
- static delivery audit is green;
- JavaScript syntax checks are green;
- Android and iPhone runtime checks pass;
- the exact deployment commit is identified and verified.

Deployment must use the exact validated repository state.
