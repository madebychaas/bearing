# Bearing broadcast pipeline

Each story is an independent playlist entry. The worker retains prior editions and publishes a complete edition atomically; viewers receive updates at a story boundary.

1. **Source:** gather permitted feed metadata and preserve source attribution, date and the reviewed source script.
2. **Write:** compile a broadcast opening, why-it-matters sentence, narrative, takeaway and qualified look-ahead from a source-bound editorial plan.
3. **Edit:** require a matching source revision, complete structure, suitable length and an existing editorial review. Automated checks are not independent fact verification.
4. **TTS:** produce both local CPU Piper voices, with script hashes, captions and provenance.
5. **Plan visuals:** record the purpose of each scene and its mixture of text, illustration, video and motion graphics. Charts/maps require reviewed numeric/geographic evidence.
6. **Create visuals:** compose the story-specific graphics with its approved bespoke illustration and motion video. Illustrations are disclosed, not represented as documentary footage.
7. **Create music:** compose two original story-seeded procedural beds locally. This is synthesis, not a neural music model. Viewer silence and music preferences remain available.
8. **Assemble:** time the opening/story/closing, 1.5-second transitions, sound accents, narration, captions and ducked music. Decode audio and validate asset hashes. Delivery is a synchronized browser composition, not a baked broadcast MP4.
9. **Publish:** put only completed packages into `dist/programmes.json`; record publication after the edition contains the exact package version.

## Automation boundary

The existing reviewed plans run automatically through production. New factual scripts and new bespoke artwork currently require editorial/art review; there is no unattended script-writing or image-generation service configured. The ranked waiting list is `channel/production/runs/broadcast-queue.json`. Short attributed headline clips remain a separate format and do not claim completion of this full-story workflow.

Per-version records live under `channel/production/runs/programmes/<version>/`: source evidence, draft and edited script, visual plan, composition, music provenance, audio and `production.json`. Failures retain the stage and reason; incomplete packages are not published. Cached packages are checked against narration, visual, music and renderer hashes.

The current product is a continuous local web playlist. Outgoing YouTube Live encoding, streaming and a fully autonomous reporting/editorial service are not implemented.

## Verification, September 29, 2026

Eleven existing full programmes completed all nine stages. Both narration voices and original music assets passed checks. The complete suite passed 57 Python and 18 JavaScript tests, including stage order, changed-source holds, cross-story visual rejection, intact publication assets and domestic selection rules. Browser checks are recorded separately in channel/output/playwright.

Browser verification confirmed narration advances, automatic next-story loading, camera/main-player exclusion and no horizontal overflow at 390 px. Camera iframe images stayed blank in the automated Chromium browser. A subsequent in-app browser check displayed USGS camera imagery and NASA's own routine loss-of-signal notice, verifying both provider players load there; uninterrupted live availability is not guaranteed. Physical listening quality still needs viewer judgment.
