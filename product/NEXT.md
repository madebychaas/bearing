# Bearing — Active Mission

**Status: active mission — the national assignment desk.**

On October 2 the user explicitly parked **Make my newscast** and redirected work to hunting and gathering current national U.S. news, plus consequential world developments. The newsroom should know what changed, why it belongs today, who is affected and where the primary evidence lives. Preserve the accepted player, production approach and saved personal-newscast work.

The current checkpoint evolves the native producer desk at `/producer.html`: independent source gathering, a broader publisher/primary-source network, national relevance and today-peg candidates, source-linked questions, coverage gaps and an official release calendar. It does not grant editorial approval, generate films or redesign the viewer. New sources are discovery-only. No archival reference project was inspected or imported.

Source gathering checks due feeds every 30 seconds independently of media rendering, respecting individual schedules, cache controls and conditional requests. Publication, source updates, public-inspection filings, first discovery and observed reporting changes retain separate meanings. Coherent intake snapshots prevent partially updated evidence from being read together. A keyword match is an inspectable lead, not a verified development. Routine tropical bulletins, local alerts, political sparring and promotional material must not fill the national lead list; contradictory or forecast-only evidence needs review.

See [the national desk record](NATIONAL_ASSIGNMENT_DESK.md) for source coverage, operational details and limits. Faster detection than major newsrooms is an ambition, not a measured result. The local collector runs only while this server and machine are running. Direct BLS/DOL access is currently blocked; AP/CNN access and direct court/congress feeds remain gaps. Build on actual observed misses and fresh-arrival measurements rather than adding volume for its own sake.

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
