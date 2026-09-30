# Bearing — current handoff

**September 30, 2026: the 13-script rewrite and editorial-voice milestone is complete.**

The existing authored-story library now has thirteen source-checked writing revisions using the viewer's updated guidance: a concrete, impact-first lead; a self-contained explanation; natural spoken rhythm; and a specific closing. Average length fell from about **106 to 60 words**, with revised scripts ranging from **52 to 68 words**. The library records before/after copy, claim support, dated context, pronunciation needs, visual cues and the reason for each edit.

These are reviewed writing examples, not thirteen new viewer-approved performances. **No TTS, music, graphics or video was generated for this milestone.** The accepted PCE and cybersecurity deliveries remain unchanged. The library's PCE closing and NIST script are writing alternatives, not replacements in the live playlist.

## Use the new writing standard

- [Editorial voice playbook](EDITORIAL_VOICE.md): the maintained writing and editing standard.
- [Before/after rewrite book](SCRIPT_REWRITES_20260930.md): all thirteen scripts, source checks and concrete lessons.
- [Editable voice profile and selected examples](../channel/production/editorial-voice.json): loaded by the native draft desk for both drafting and editing.
- [Versioned rewrite library](../channel/production/editorial-rewrites-20260930.json): structured scripts, evidence, timing status and visual directions.

This is persistent editorial guidance and example-based prompting; **no model weights were trained**. Examples teach structure and voice, never supply evidence for another story. New drafts remain source-bound and require editorial approval. To publish a rewrite, recheck why it belongs now, facts and rights; review pronunciation and visual choices; create a new narration and media delivery; then verify measured duration, sound, picture and continuous playback. Word counts and estimated runtimes do not prove a finished segment meets the 45-second ceiling.

The draft desk loads one current profile for both model passes, enforces a 35–80-word normal envelope and records its revision. Each attempt carries one persisted UTC `asOf` clock for assessing time-relative language; that clock is not evidence of a new development. Queue records identify older drafts needing a style refresh while retaining the original evidence and attempts.

Verification for this milestone: **142 Python tests and 46 JavaScript tests passed**. Focused checks cover both prompt passes, stale-profile handling, the persisted clock, evidence isolation, script length and the thirteen-script bank. Model calls were stubbed in tests; no local model was run or retrained. All thirteen saved baselines exactly match their published/source records, and tracked delivery manifests, media and production plans have no changes.

The source checks and script/cue consistency review cover the writing library. This milestone makes no new listening, render or playback claim. Prior production verification below belongs to the earlier PCE milestone.

## Previous milestone: the finished PCE story

On September 30, the user requested a major story from that day, then asked for a stronger new-report lead, clean audio entry, more suitable music, flowing narration and graphics in reading order. **Inflation erased the income gain** incorporates that feedback. Its source is the September 30 BEA Personal Income and Outlays release, rechecked after the revision. The accepted cybersecurity cut and broader product design remain untouched.

### Watch the existing delivery

Open **http://127.0.0.1:8796/**. Choose **In Focus**, then **Inflation erased the income gain.** One Play continues into the next independent story. The preview uses Natural pace; the user's previous A little quicker setting had been accelerating playback by 15%.

- Story: `reviewed-pce-buying-power-20260930-v1`
- Final delivery: `a7ab64e194631e40f31c`
- Script: **58 words**
- Warm / Heart: **26.867 seconds**
- Measured / Michael: **30.500 seconds**
- Standalone complete movie: `channel/dist/assets/films/a7ab64e194631e40f31c/measured.mp4` (Warm is alongside it)
- [Editorial, source, rights and production review](IN_FOCUS_PCE_REVIEW.md)

The current-news record is valid through October 2 and expires from the playlist at October 3, 00:00 UTC. The released August estimates are the source period; September 30 is the actual news peg. Future corrections or updates require a new editorial review, not an automatic claim that this fixed film remains current.

### What was produced previously

A consequence-led script, locally synthesized narration, original 1080p animated explanatory graphics, an original ducked musical bed and sound punctuation, two complete MP4s with English subtitles, clean voice tracks, source-specific posters, and an entry in the existing continuous playlist.

The film leads with the new report's buying-power impact, attributes it to BEA and Wednesday in the next sentence, explains the monthly income/price mechanism, compares 3.4% annual PCE inflation with the Fed's 2% longer-run goal, and closes on whether income can outpace prices. Four different compositions serve The Shift / The Pressure / What Counts. Numbers and labels reveal at spoken cues; no unrelated footage is used. The upper-left courtesy names BEA and the Federal Reserve.

The speaking rate remains 0.93; flow improves through shorter section tails and removal of the inserted 1.7-second reading pause. Guarded edits remove only 0.458 seconds Warm / 0.420 seconds Measured of additional quiet PCM, keeping roughly 0.20-second sentence breaths and every spoken sample. The first-word cues are 0.438 seconds Warm / 0.569 seconds Measured. The new dry opening accent ends at 0.230 seconds, before speech; narration has unity gain and no fade. A sparse pulse and muted-key alternative replace the swelling ambient treatment. The current 3.4% figure reveals left before the 2% goal on the right. The chart holds through 'The next test' as narration continues: the goal stays fully settled for 1.75 seconds Warm / 2.23 seconds Measured before the transition. The closing question appears at its spoken cue. Existing caption and picture safe areas remain intact.

### Existing implementation boundary

- `production/produce_film.py` reuses the existing source/script gates, current-news check, CPU speech and production lock. `film_visuals.py` supplies original narration-timed graphics; `film_audio.py` supplies guarded silence compaction and an original dry score.
- `dist/films.json` is approved delivery inventory merged into the same playlist with existing source-URL deduplication and boundary updates. There is no new editorial intake, automatic assignment service or manually managed source library.
- Voice-specific picture follows the narration clock. Buffer starvation pauses picture; recovery resynchronizes. Both voice movies must be valid before playlist admission. Less movement steps through settled narrated states.
- Asset copies use verified temporary files and atomic replacement. Both complete voice versions must decode and meet the duration budget before the manifest changes. Intermediate revisions remain local; only the final reviewed delivery and its score are committed.
- Changes to picture fitting and caption spacing apply only to finished films. The outer player, accepted story renderer, broader interface and producer desk retain their existing design.

### Verification of the previous PCE delivery

- **132 Python tests and 46 JavaScript tests passed.** JavaScript ran with `node --test channel/tests/*.test.mjs`; the machine's npm launcher points at a missing npm installation, so the equivalent package script was invoked directly.
- Both final MP4s fully decode and match their authored duration. The revised AAC mixes decode with peaks 0.7996 Warm / 0.7992 Measured and no clipped samples. First-word level is not attenuated; the first 250 milliseconds of every narration phase preserve the unedited paced source within one PCM16 quantization unit. Captions and standalone subtitles reproduce every word and punctuation mark of the approved script.
- Both movies return HTTP 206 and correct byte ranges from the normal local server.
- Revision browser checks confirmed both new voice-specific pictures and narration, both new music choices, pause/seek clock agreement, chart/caption separation, the idle poster and autoplay into the next independent story. The console remained clear. The previous cut also verified Natural and Unhurried rates, master mute, reduced movement, source/script dialog and boundary updates; playback code was unchanged in this revision.
- The preceding browser pass verified a scroll-less 1280 × 720 desktop and no horizontal overflow at 390 px; the revision leaves that layout unchanged. The revised chart was inspected in the native player at the normal desktop size.
- Independent source and visual review checked numbers, periods, zero-baseline geometry, courtesy and the qualified closing. New waveform tests protect the first phoneme, quiet-only cuts and unity voice gain; visual tests protect left-to-right reveal order and a picture hold without a narration pause. Existing buffering, malformed voice-video and interrupted-copy regression checks still pass.
- The accepted NIST story record and all nine referenced media/score assets are **byte-for-byte unchanged**, still delivery `a315989abeedc6ee7f60`.

Physical speaker output and subjective voice appeal are not independently listening-verified. The viewer's judgment remains the final creative acceptance; successful software checks do not stand in for it.

## Earlier work and stop boundary

The native producer desk remains at **http://127.0.0.1:8796/producer.html**. Its completed September 29 proof is preserved in [EASY_NEWS_V1_HANDOFF.md](EASY_NEWS_V1_HANDOFF.md), with operation in [EASY_NEWS_V1.md](EASY_NEWS_V1.md).

The draft/edit desk now carries the maintained voice profile and selected examples alongside its source evidence. The archival reference repository was not inspected or used, and no dependency on it was introduced. The requested rewrite and editorial-guidance pass is complete. Do not publish these alternatives, begin another story or start a broad feature mission without new direction.
