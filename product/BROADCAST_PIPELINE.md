# Bearing broadcast pipeline

Each story is an independent playlist entry. The worker retains prior editions and publishes a complete edition atomically; viewers receive updates at a story boundary.

## Current writing milestone

The September 30 pass completed thirteen source-checked script rewrites, reducing average length from about **106 to 60 words**, with revised scripts ranging from **52 to 68 words**. The [rewrite book](SCRIPT_REWRITES_20260930.md) and [structured library](../channel/production/editorial-rewrites-20260930.json) preserve evidence, before/after choices, timing limits and visual cues. These are writing alternatives; the accepted PCE and NIST deliveries were not changed, and no TTS or media was generated for this pass.

The [editorial playbook](EDITORIAL_VOICE.md) is the human-readable standard. The native script desk loads the [editable profile and selected examples](../channel/production/editorial-voice.json) into both drafting and editing, retaining the profile revision with the result. This is example-based editorial guidance, not model-weight training. Examples do not become factual evidence for a new story. New or rewritten copy still needs editorial review, a fresh timeliness and rights check, pronunciation review, new media assembly and finished playback verification before publication. The library is not a claim that all alternatives have viewer approval.

## Production stages

The draft desk records the voice-profile revision and a UTC `asOf` clock for each generation attempt. Both model passes use the same current profile and clock. The queue flags drafts written under an older profile for a style refresh without replacing historical evidence or draft files. The clock helps interpret source dates; it cannot establish that an older story is new.

1. **Source:** gather permitted feed metadata and preserve source attribution, date and the reviewed source script.
2. **Write:** compile a broadcast opening, why-it-matters sentence, narrative, takeaway and qualified look-ahead from a source-bound editorial plan.
3. **Edit:** require a matching source revision, complete structure, suitable length and an existing editorial review. Automated checks are not independent fact verification.
4. **TTS:** produce the plan's explicitly selected local CPU narration provider, with script hashes, captions and provenance. Reviewed directed stories use Kokoro (Heart/Michael); older programmes retain their reviewed Piper performance. An unavailable chosen engine holds production rather than silently changing voices. Kokoro synthesizes complete sentences and exposes duration-derived word timing for visual cues.
5. **Plan visuals:** record the purpose of each scene and its mixture of text, illustration, video and motion graphics. Charts/maps require reviewed numeric/geographic evidence.
6. **Create visuals:** compose the story-specific graphics with its approved bespoke illustration and motion video. Illustrations are disclosed, not represented as documentary footage.
7. **Create music:** compose two original story-seeded procedural beds locally. This is synthesis, not a neural music model. Viewer silence and music preferences remain available.
8. **Assemble:** time the opening/story/closing, 1.5-second transitions, sound accents, narration, captions and ducked music. Decode audio and validate asset hashes. Existing studio programmes use a synchronized browser composition; reviewed finished films also have complete, independently playable MP4s for each voice.
9. **Publish:** put only completed packages into `dist/programmes.json` or reviewed finished-film deliveries into `dist/films.json`; record publication only after the corresponding edition contains the exact package version. Both feed the same continuous playlist.

## Automation boundary

The existing reviewed plans run automatically through production. New factual scripts and new bespoke artwork currently require editorial/art review; there is no unattended script-writing or image-generation service configured. The ranked waiting list is `channel/production/runs/broadcast-queue.json`. Short attributed headline clips remain a separate format and do not claim completion of this full-story workflow.

Per-version records live under `channel/production/runs/programmes/<version>/`: source evidence, draft and edited script, visual plan, composition, music provenance, audio and `production.json`. Failures retain the stage and reason; incomplete packages are not published. Cached packages are checked against narration, visual, music and renderer hashes.

Narration-only In Focus stories normally have a 45-second delivery ceiling. The writing standard aims for 50–75 words; the draft desk's normal envelope is 35–80 words. Neither a word count nor a runtime estimate replaces measured TTS and finished playback. The accepted 51-word cybersecurity example tightens its own budget to 32 seconds, delivering 23.11/25.71 seconds in the two voices. Its chapters are **The Shift / The Design / The Payoff**, with narration beginning at 0.45 seconds under a musical signature. The accepted September 30 PCE film uses 58 words and delivers 26.867/30.500 seconds; see [its production review](IN_FOCUS_PCE_REVIEW.md). Both remain unchanged by the rewrite library. A slower viewer pace can extend elapsed playback beyond the authored duration.

New or changed full-story scripts require `editorialTiming` metadata with a specific why-now reason and source evidence. Current-news reviews require a trigger and bounded validity window; retrieval/build dates and unexplained page updates cannot stand in for a development. Expired current reviews lose live eligibility even when a prior playable delivery is retained. Dated context examples remain explicitly marked. Unchanged legacy exceptions are frozen to ID, source revision and spoken-script hashes. These are editorial review checks, not independent factual verification. See the current story review for the selected example's evidence limits.

Scenes and individual reveals bind to reviewed phrases in real model-duration word timings. Backward seeks and reduced motion still respect those reference boundaries. Third-party imagery and map geometry require local asset hashes, exact source and license URLs, author, affirmative use review and a courtesy credit. They appear only in the corresponding narrated scene; the top-left courtesy identifies the source, and Behind this story contains licensing. The current map's pinned ISC notice is retained with its paths and provenance. Successful downloading never establishes permission.

Use `python production/produce_programmes.py --only STORY_ID` for a single-story review. Other published entries are retained. Missing plans and failed builds retain the previous playable entry. Renderer, composition and voice changes produce a new delivery identity; audio files are staged until both voices, all cues and the runtime ceiling pass. Retained source clips, original photographs and previous deliveries are preserved.

The current product is a continuous local web playlist. Outgoing YouTube Live encoding, streaming and a fully autonomous reporting/editorial service are not implemented.

## Verification, September 29, 2026

Eleven existing full programmes completed all nine stages. Both narration voices and original music assets passed checks. The complete suite passed 57 Python and 18 JavaScript tests, including stage order, changed-source holds, cross-story visual rejection, intact publication assets and domestic selection rules. Browser checks are recorded separately in channel/output/playwright.

Browser verification confirmed narration advances, automatic next-story loading, camera/main-player exclusion and no horizontal overflow at 390 px. Camera iframe images stayed blank in the automated Chromium browser. A subsequent in-app browser check displayed USGS camera imagery and NASA's own routine loss-of-signal notice, verifying both provider players load there; uninterrupted live availability is not guaranteed. Physical listening quality still needs viewer judgment.
