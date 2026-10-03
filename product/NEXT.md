# Bearing — Active Mission

**Status: active mission — second-story + graphics-quality proof.**

The first role-separated newsroom proof has been reviewed and the workflow has been made repeatable. The next active mission is [Second Story + Graphics Quality Proof](SECOND_STORY_GRAPHICS_PROOF.md), with [Editorial Supply Proof](EDITORIAL_SUPPLY_PROOF.md) as its first prerequisite. Read and follow [Editorial Story Library & Ranking](EDITORIAL_STORY_LIBRARY.md) and [Graphics & Art Direction Standard](GRAPHICS_ART_DIRECTION.md) as active standards.

This follow-on mission is deliberately a reuse test: run one materially different current story through the existing role-separated workflow, add only the smallest bounded Art Direction stage needed to test design judgment, produce a private preview, compare the role behavior with the Medicare proof, and stop. Do not enable autonomous production, publish, or begin Lumina integration.

If local commits from the first proof have not yet been pushed, preserve and reconcile them; do not discard completed local work.

---

**Status: active mission — prove the role-separated newsroom pipeline.**

On October 3 the user explicitly expanded the newsroom architecture beyond the assignment-desk-only checkpoint. The assignment desk remains the factual foundation; the next proof is to separate distinct newsroom judgments so one broad model no longer has to discover, frame, produce, write, visualize and approve a story in one inference.

Read [the role-separated newsroom architecture](NEWSROOM_ARCHITECTURE.md) before implementing this mission. This current direction supersedes the older historical guardrail below that said not to build a multi-agent newsroom. Preserve that historical text as the scope of the mission in which it was written; do not treat it as the current instruction.

### Current implementation target

Build the **smallest vertical proof** through the existing Bearing codebase:

```text
current canonical event
→ AssignmentBrief
→ EditorialBrief
→ ProductionPlan
→ Journalist + VisualAssessment + GraphicsSpec
→ FinalReview
→ deterministic production/playout handoff
→ one finished traceable Bearing asset
```

Do not build eight autonomous services or a generalized agent framework. Role separation is initially about isolated context, jurisdiction, schemas, permissions and stop conditions. Reuse one underlying model where sensible.

The first proof must:

1. Reuse the existing national assignment desk/canonical-event evidence rather than replacing it.
2. Persist versioned artifacts for each newsroom handoff.
3. Add a bounded **Editor** that decides meaning, audience need and editorial focus from an `AssignmentBrief`.
4. Add a bounded **Producer** that decides format, structure, timing and element needs from an `EditorialBrief`.
5. Fan out from the production plan to:
   - one **Journalist** intelligence with output modes such as anchor/reporter track,
   - **Visual Intelligence** that judges what available imagery actually proves and what is missing,
   - **Graphics Intelligence** that emits a machine-readable `GraphicsSpec`.
6. Reunite those outputs at a narrow **Standards / Final Edit** role that returns specific edits/holds rather than regenerating the story.
7. Keep technical execution deterministic: missing/stale/mismatched assets, versions or manifests must fail loudly and specifically.
8. Use the accepted Bearing production machinery for the finished proof instead of redesigning the viewer or renderer.
9. Demonstrate one material source update that invalidates or reassesses the correct downstream artifacts.
10. Demonstrate one intentionally broken execution dependency that the technical layer refuses to paper over.

Use **one real current story** for the end-to-end proof. Do not batch stories merely to show orchestration.

### Graphics / Lumina boundary

Angelo's current **Lumina Studio** prototype is a promising graphics renderer and human-edit surface, not an editorial agent. The Graphics Intelligence should decide what explanatory graphic is needed and emit a stable `GraphicsSpec`; a renderer adapter should execute that spec.

For this first mission, define the adapter boundary and keep the existing Bearing graphics path working. Do **not** create a runtime dependency on the Lovable-hosted project or copy the whole studio into Bearing yet. Once the graphics contract is proven, the Lumina code can be explicitly exported/synced and adapted behind that interface.

### Evaluation

Do not declare success because the artifacts validate.

Compare the role-separated output with the existing broad-agent behavior where practical and inspect the actual story. Look for clearer editorial focus, fewer unsupported assertions, better visual evidence choices, more purposeful graphics, less model wandering and a result that feels more produced than generated.

If a bad result occurs, preserve enough provenance to identify **which newsroom judgment failed**.

### Stop condition

When one real current story completes this path, the material-update reassessment works, the technical failure test fails loudly, relevant automated tests pass and the finished story has been reviewed end-to-end, commit stable milestones, update this file with what the proof taught us, and stop for user review.

---


**Status: active mission — the national assignment desk.**

On October 2 the user explicitly parked **Make my newscast** and redirected work to hunting and gathering current national U.S. news, plus consequential world developments. The newsroom should know what changed, why it belongs today, who is affected and where the primary evidence lives. Preserve the accepted player, production approach and saved personal-newscast work.

The current checkpoint evolves the native producer desk at `/producer.html`: independent source gathering, a broader publisher/primary-source network, national relevance and today-peg candidates, source-linked questions, coverage gaps and an official release calendar. It does not grant editorial approval, generate films or redesign the viewer. New sources are discovery-only. No archival reference project was inspected or imported.

Source gathering checks due feeds every 30 seconds independently of media rendering, respecting individual schedules, cache controls and conditional requests. Publication, source updates, public-inspection filings, first discovery and observed reporting changes retain separate meanings. Coherent intake snapshots prevent partially updated evidence from being read together. A keyword match is an inspectable lead, not a verified development. Routine tropical bulletins, local alerts, political sparring and promotional material must not fill the national lead list; contradictory or forecast-only evidence needs review.

See [the national desk record](NATIONAL_ASSIGNMENT_DESK.md) for source coverage, operational details and limits. Faster detection than major newsrooms is an ambition, not a measured result. The local collector runs only while this server and machine are running. Direct BLS/DOL access is currently blocked; AP/CNN access and direct court/congress feeds remain gaps. Build on actual observed misses and fresh-arrival measurements rather than adding volume for its own sake.

### Fifteen-minute editions and one current-story order — October 2

The next requested step is implemented in the national desk: one descending active national story order, with the illustrated top three followed by the remainder at rank 4. Live Brief/In Focus ranking tabs, lane filters and pagination no longer split that front page; representative-cycle controls and the existing source/decision/handoff tools remain available. The desktop list scrolls internally.

`top_stories.rank()` provides the complete distinct order, including consequential health, safety, courts, government operations, security, consumer and public-service coverage alongside the economic leads. Exact source-linked strategy matches can support lower-ranked current developments. Raw keyword volume and publication recency do not substitute for national consequence. Unqualified Watch/Held/local/conflicting material stays out rather than padding the list.

`top_story_editions.py` persists a 15-minute edition schedule and preparation queue in ignored runtime state. The existing observer advances it even with no browser open. New entrants are claimed and prepared outside the reporting lock; the next edition publishes only when all selected hero tiles are source-bound, reviewed, image-verified and ready. The browser decodes the image files before inserting new tiles. Eligible previous editions persist while a replacement is prepared, but changed/held/stale evidence disappears immediately. Refreshing the view checks readiness; it does not force a new ranking or fabricate a new update time.

Creative preparation currently uses the **Bearing Top stories preparation** Codex heartbeat every 15 minutes, through the local queue client. The native server does not contain an image API or embedded model credential. This machine, Bearing and Codex must remain running. New stories use the built-in image tool; the same story's original may be reused after fresh source and visual review. See [the worker workflow](TOP_STORIES_WORKER.md). Recurring runs are limited to tile preparation and ignored runtime assets, with no tracked-code/Git changes or video approval/publication. A configured schedule is not proof of a future unattended run.

Live proof: a new PBS report of the existing G7 fuel agreement entered the actual queue, was claimed, checked against the current primary statement, and completed through the API after the saved original illustration was reinspected. The full three-card edition became ready, with the remainder at ranks 4 and 5. The image was deliberately reused for the same story, not regenerated to manufacture a generation demonstration. New-image generation remains available to the scheduled worker for genuinely new entrants.

Verification: **318 Python tests and 82 JavaScript tests pass.** Tests cover the scheduled edition boundary, all-ready publication, source/art invalidation, exact-source completion, durable exclusive leases/retries, local HTTP access and production isolation. Real Chrome checks covered pending-to-ready publication, all three decoded images, rank 4/5 continuation, source context, keyboard selection and refresh preserving an open decision drawer and unsaved note. Desktop at 1478 × 910 and 1242 × 698 CSS pixels had no outer scroll; the compact list scrolled internally and mobile at 355 × 767 had no horizontal overflow. A real server restart preserved the three ready tiles, original prepared time and next scheduled review. The active local heartbeat configuration was verified; its first unattended execution has not yet been observed. Proof and test logs remain in ignored `output/top-stories/`.

### Initial Top stories — October 2 follow-up

The user requested a horizontal orientation hero above the national desk: the three biggest current national stories, ordered, with impact-forward headlines, a short supporting sentence and optional original imagery. Implemented in the native producer workspace; the watch player and parked personal-newscast flow stay unchanged.

`top_stories.py` selects distinct, consequential national developments from the current source-bound desk. National hazards and broad economic/policy consequences outrank routine agency announcements, isolated enforcement cases and mere recency. Repeated jobs/fuel coverage uses one slot per thread. Held, contradictory, local, future-dated and stale evidence cannot fill the hero. Fewer than three qualified stories leaves an honest incomplete state.

The initial reviewed selection is jobs, the G7 fuel-reserve agreement and the latest national mortgage benchmark. The first two have a Friday development; the mortgage story explicitly carries Thursday's continuing household impact. Supporting BLS, G7 and Freddie Mac references are retained separately from the discovery reports. Generated originals are labeled AI illustrations and retained with prompts/hashes in `top-stories-art-20261002.json`; they are possible future production inputs, not approved video assets.

Authored copy, source-supported carries and illustrations bind to exact evidence and expire within four hours. Changed sources or expiry removes that treatment; the hero continues ranking current source copy rather than silently relabeling old bespoke art. There is no unattended image-generation or headline-writing service implied here. This is an editorial selection from connected coverage, not proof of an objective nationwide top three. Details and browser proof are recorded in [the desk record](NATIONAL_ASSIGNMENT_DESK.md).

Verification: **281 Python tests and 77 JavaScript tests pass.** Actual Chrome checks at 1478 × 910 and 1242 × 698 CSS pixels found no outer desktop scrolling; the mobile cards stack without horizontal overflow. All three original images loaded, all three cards selected the exact story across filters, primary context opened correctly, and refresh preserved selection, keyboard focus, expanded evidence, the editorial drawer and an unsaved note. The existing handoff opened without making a production request. Local screenshots and logs are under ignored `output/top-stories/`. No fresh-film or automatic imagery-generation claim is part of this checkpoint.

### Verified checkpoint — October 2

Added 13 discovery endpoints for **28 enabled feeds**. At 13:11 UTC, all 28 were available; the desk held 14 possible current leads, 79 watch items and 419 held/out-of-scope events. These are a dated observation, not completeness or uptime claims. BEA's feed initially returned 406 because the request omitted its `text/xml` format; normal content negotiation now succeeds without changing identity or circumventing access restrictions. BLS and DOL remain unconnected access gaps, separate from the enabled-feed count.

**262 Python tests and 72 JavaScript tests pass.** The full Python suite includes source/approval/production regressions; new checks cover independent collection under a production lock, atomic snapshots, publisher cache limits, alert expiry, filing/update clocks, baseline versus delayed discovery, misleading forecasts, national scope and exact changed-source attribution. The JavaScript suite was run directly with `node --test channel/tests/*.test.mjs` because this machine's global npm launcher points to a missing npm CLI.

Actual Chrome verification at 1478 × 910 confirmed a scroll-less outer page, Today/Developing/Watch/Held filters, source excerpts, the official scheduled-only BEA calendar, visible source gaps, and refresh preserving the selected report and open evidence. The CBS jobs report led the final view. Routine tropical bulletins, a forecast excerpt paired with released figures, and a retrospective political story no longer occupied Today. These observed misses became regressions. Browser evidence is local under `output/assignment-desk/` and excluded from Git.

Normal intake and media workers remain enabled. Successive runtime checks confirmed source collection progressing independently; the production-lock test proves an occupied renderer cannot lock out collection. All accepted films, scripts, narration and player files remain unchanged. Discovery latency has only an initial sample and is not yet a useful performance benchmark. Continue this sourcing mission from observed misses, primary-source gaps and measured coverage quality; the personal-newscast feature below stays parked.

## Parked — Make my newscast

The October 1 implementation below is preserved. Do not resume creative-provider integration or personal-newscast feature development without the user reopening it.

The prior mission requested a viewer workflow: browse the newest reporting from trusted sources, choose two or three stories, adjust a few meaningful preferences, and make a personal newscast. Production should happen behind a polished living progress screen. A completed result should offer one grounded sentence about its contents and an explicit Play action. This remains historical scope, parked by the October 2 assignment-desk request.

Build this on the existing watch page and production machinery. Preserve the accepted player and story quality. Keep selected stories in their chosen order, keep the personal queue separate from ordinary channel refreshes, and finish the chosen run with replay/return options. Voice, natural/unhurried delivery and score/voice-only preferences belong to the request until playback begins. Progress reflects actual stages; a generated script or an elapsed timer is never a playable result.

The audited gap is creative automation: native narration, scoring, assembly and playback work, but current full-film packets and bespoke visual plans are editorially authored. The accepted loan renderer is specific to that story; it cannot be stamped onto arbitrary headlines. There is no configured server-callable image provider or automatic production director. The creative-provider choice remains unresolved and is parked with this feature; do not pursue it during sourcing work. Do not claim arbitrary fresh stories are fully automatic or substitute headline readouts for produced films. Missing creative production must produce a clear saved/needs-attention state, not an endless spinner or a fake finished newscast.

### Implemented checkpoint — October 1

The home page now has a restrained **Make my newscast** dialog: latest reporting, two or three ordered selections, voice, delivery and sound. An animated creation view follows actual stages, preserves the chosen story titles and shows completed-story counts. It stops moving on a held/failed job. Ready results have a source-grounded sentence and an explicit Play button; personal playback uses the existing player and separate selected queue, then offers replay or return. Returning restores channel preferences and position; background arrivals cannot replace personal selections.

`newscasts.py` persists jobs atomically under ignored run state with idempotent requests, retry/cancel, restart recovery and shared production serialization. `newscast_production.py` can render exact approved native handoffs privately; it preflights the whole selection before expensive work. It binds every selected report to reviewed evidence, repeats approval checks during work and after full media verification, and never creates an approval or modifies the public film manifest. An older approval for the same event cannot stand in for newly joined reporting.

Verification: **210 Python tests and 64 JavaScript tests passed**, including new source/revision, retry, interruption, real-media validation, approval-revocation, private-queue and preference tests. The prior intermittent Windows 413 test passed in this run; its historical failure remains documented below. In the actual browser at 1130 × 1179, the desktop page remained scroll-less, two current stories were selected with Measured / Unhurried / Voice only, the real request reached `needs_attention` with zero finished films, and page refresh restored the same selections/job. Retry retained the same job and rechecked its authority. An identical repeated API request returned the existing job. The local server was restarted with normal source refresh enabled.

**Not proved yet:** fully automatic creative production for arbitrary latest selections, or a freshly generated personal cast playing end-to-end in the browser. No current-story cast was fabricated to demonstrate readiness. The ready/queue paths have automated coverage, but their fresh-film viewer proof follows the creative connection. No new story media was generated or accepted in this checkpoint. The user's backend choice remains pending; next work is connecting that chosen provider through sourced drafting/editing, bespoke direction/media and explicit quality review, then producing one real two-story cast through this exact viewer flow. Do not close this mission as complete yet.

## Accepted production approach

**Previous milestone: production approach accepted and locked in.**

Angelo's October 1 response to `9c4fe29dbfb3a18916ea`: **“This is incredibly close. Great stuff. Lock this in as the approach we want.”** His qualification is part of the standard: keep it tight, dynamic and moving, with judgment about when movement helps and when an idea needs to hold. This accepts the production approach as the reference for future stories, with room for refinement; it is not a request for another edit or blanket signoff on every voice performance. The vision, editorial playbook and machine-readable guidance now retain that distinction. No media, script or playback behavior changed for this acceptance checkpoint. All 10 editorial-guidance tests passed.

The latest October 1 follow-up is **`9c4fe29dbfb3a18916ea`**. It replaces the same loan story entry with two original generated editorial images, a slower single-title build, an exact-word cut into body imagery, three accumulating process columns, a requirements extension on the same diagram, and a calendar → credit → car/apartment explanation. The exact script, audio, captions and timing are unchanged by hash/comparison. Warm is 36.867 seconds; Measured is 40.300 seconds. The renderer is opt-in; the existing player and other films were not redesigned. Both earlier deliveries remain archived.

Both finished MP4s fully decode and all 13 delivery hashes match; 38 encoded frames were inspected. Actual browser playback used the new film, kept the full picture and captions visible, and advanced into the next item. **17 graphics tests and all 54 JavaScript tests pass.** The full Python run passes 182 of 183: an existing Windows HTTP connection-close race intermittently aborts the oversized-request test before the client receives 413. The isolated seven-test server module passes. This was reproduced separately and is unrelated to the picture revision; no server behavior was changed or flaky test hidden. Keep that limitation visible rather than calling the full suite green.

See the [production record and acceptance](STUDENT_LOAN_PRODUCTION_20261001.md), [reviewed packet](../channel/production/reviewed-student-loans-20261001-picture-v3.json), and [original image prompts](../channel/production/student-loan-image-led-v3-prompts.json). Preserve this delivered cut as the accepted approach reference. Earlier milestone notes below retain their status as recorded at delivery; the active sourcing mission is stated above; the personal-newscast mission is parked.

## Previous picture revision

October 1 follow-up delivered: **`b89773d68a5e1c98cbf9`** replaces the loan segment's picture with staged centered typography, larger animated explanations and a rebuilt closing. No persistent eyebrows, source strips, branding or footers occupy the original graphics; internal edits use cuts and object movement, with no cross dissolves. The exact script, narration, score and audio mix are unchanged by hash. The full 16:9 picture uses the video canvas; transport and chapter controls recede while playing and return on interaction or pause. Prior deliveries and other accepted films remain intact.

Revision validation: **179 Python and 54 JavaScript tests passed**. Both complete videos decode; 32 encoded cue frames were inspected. Actual desktop playback verified the full inner frame, hidden idle overlays, visible captions, keyboard restoration, pause/seek and automatic advancement into the next item. The page remained scroll-less at the tested desktop viewport. See the [current revision and preserved initial proof](STUDENT_LOAN_PRODUCTION_20261001.md). No broader mission is authorized; stop for the user's review.

October 1 delivery: **Default help moves online** completes the selected-story path with the user's approved 80-word script, two finished 1080p films, original music/effects, voice-timed graphics, captions and a local playlist entry. Warm runs **36.867 seconds**; Measured runs **40.300 seconds**, without speeding up narration. Actual browser playback reached the next item automatically. See the [finished production and proof](STUDENT_LOAN_PRODUCTION_20261001.md).

The [September 30 checkpoint](SELECTION_PROOF_20260930.md) and its preparation packet remain historical records. The October 1 source hold was resolved by an explicit editorial reassessment: CNBC's discovery report had rotated out of a healthy feed, so fresh Education/Treasury, Federal Student Aid and CFPB evidence became the factual authority. The original opportunity, product choice and discovery report remain traceable. Returning corrections and expired primary checks still require reassessment; no timestamps or approvals were silently renewed.

Validation: **175 Python tests and 50 JavaScript tests passed**; both MP4s fully decode, all delivery hashes match, the exact copy survives narration/captions, and actual encoded frames were inspected. The first word has no added fade; graphics retain their dwell time. The accepted PCE/NIST media and existing player design remain intact. Production is complete; this newly delivered performance is not yet described as viewer-accepted. Do not start another mission without direction.

The September 30 editorial-voice and 13-script rewrite milestone is complete and preserved.

The completed mission is the selection-to-production proof described in [SELECTION_TO_PRODUCTION.md](SELECTION_TO_PRODUCTION.md). Its scope is retained below for context.

## Historical selection-to-production mission

Connect the existing Easy News producer intelligence to the existing Bearing production machinery for one real story.

A producer should be able to take a story opportunity surfaced in Easy News, choose the appropriate product treatment, carry the source evidence and editorial context forward, review the resulting script, and produce a finished Bearing asset without forcing the production side to rediscover the story from scratch.

If the reporting materially changes before completion, the workflow should require editorial reassessment rather than silently finishing stale work.

## Guardrails

- Evolve, don't rebuild.
- Prove, don't platformize.
- Produced, not generated.
- Preserve the existing Easy News desk, editorial voice standard, source grounding, and accepted Bearing production machinery.
- Human selection and approval remain inspectable and reversible.
- Do not render the 13 rewrite examples as a batch.
- Do not build a generalized CMS, assignment system, multi-agent newsroom, broad autonomous publishing system, or major UI redesign.
- Generalize only what the proof requires.

## Technical approach

Astra owns the implementation.

Choose the smallest clean path through the existing codebase. Reuse working machinery wherever practical. Do not stop for routine engineering decisions.

## Success

One current story can travel:

**Easy News opportunity → producer product choice → carried-forward evidence/context → editorial draft/review → Bearing production → finished traceable asset**

with one material-change/reassessment case verified.

When that proof is stable, commit, update this handoff with what the implementation taught us, and stop.
