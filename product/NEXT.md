# Bearing — current handoff

**September 30, 2026: one current domestic story produced and ready for viewer review.**

The user requested a major story from today, taken through the complete quality path. The result is **Inflation erased the income gain**, based on this morning's BEA Personal Income and Outlays release. This mission did not reopen the accepted cybersecurity cut or expand the producer platform.

## Watch

Open **http://127.0.0.1:8796/**. Choose **In Focus**, then **Inflation erased the income gain.** One Play continues into the next independent story. The preview uses Natural pace; the user's previous A little quicker setting had been accelerating playback by 15%.

- Story: `reviewed-pce-buying-power-20260930-v1`
- Final delivery: `0b3b3c40a075da4bed57`
- Script: **63 words**
- Warm / Heart: **33.900 seconds**
- Measured / Michael: **37.767 seconds**
- Standalone complete movie: `channel/dist/assets/films/0b3b3c40a075da4bed57/measured.mp4` (Warm is alongside it)
- [Editorial, source, rights and production review](IN_FOCUS_PCE_REVIEW.md)

The current-news record is valid through October 2 and expires from the playlist at October 3, 00:00 UTC. The released August estimates are the source period; September 30 is the actual news peg. Future corrections or updates require a new editorial review, not an automatic claim that this fixed film remains current.

## What was produced

A consequence-led script, locally synthesized narration, original 1080p animated explanatory graphics, an original ducked musical bed and sound punctuation, two complete MP4s with English subtitles, clean voice tracks, source-specific posters, and an entry in the existing continuous playlist.

The film leads with buying power, compares 3.4% annual PCE inflation with the Fed's 2% longer-run goal, explains the monthly income/price mechanism, and closes on whether income can outpace prices. Four different compositions serve The Shift / The Pressure / What Counts. Numbers and labels reveal at spoken cues; no unrelated footage is used. The upper-left courtesy names BEA and the Federal Reserve.

Per-story pitch-preserving pacing is 0.93; the opening voice starts at 0.52 seconds. A 1.7-second musical reading breath leaves the goal comparison fully settled for 2.17 seconds Warm / 2.59 seconds Measured before its transition. Short exact-word captions and a picture safe area protect graphic reading time. On a narrow phone the film sits above the captions and existing controls; fine chart text remains better suited to landscape/fullscreen viewing.

## Implementation boundary

- `production/produce_film.py` reuses the existing source/script gates, current-news check, CPU speech, score and production lock. `film_visuals.py` supplies original narration-timed graphics.
- `dist/films.json` is approved delivery inventory merged into the same playlist with existing source-URL deduplication and boundary updates. There is no new editorial intake, automatic assignment service or manually managed source library.
- Voice-specific picture follows the narration clock. Buffer starvation pauses picture; recovery resynchronizes. Both voice movies must be valid before playlist admission. Less movement steps through settled narrated states.
- Asset copies use verified temporary files and atomic replacement. Both complete voice versions must decode and meet the duration budget before the manifest changes. Intermediate revisions remain local; only the final reviewed delivery and its score are committed.
- Changes to picture fitting and caption spacing apply only to finished films. The outer player, accepted story renderer, broader interface and producer desk retain their existing design.

## Verification

- **126 Python tests and 46 JavaScript tests passed.** JavaScript ran with `node --test channel/tests/*.test.mjs`; the machine's npm launcher points at a missing npm installation, so the equivalent package script was invoked directly.
- Both final MP4s fully decode and match their authored duration. The final AAC mixes decode with peaks 0.8094 Warm / 0.8170 Measured, below clipping. Captions and standalone subtitles reproduce every word and punctuation mark of the approved script: 13 chunks per voice, at most eight words / fifty characters.
- Both movies return HTTP 206 and correct byte ranges from the normal local server.
- Actual browser checks cover voice-specific media, Natural and Unhurried rates, pause and forward/backward seek, caption and graphic alignment, master mute, reduced movement, the source/script dialog, and automatic progression into the next independent item. The authored poster remains visible until Play. Live delivery updates wait for a story boundary.
- Desktop at 1280 × 720 remains scroll-less. The 390 px mobile layout has no horizontal overflow; picture, captions and controls stay separated.
- Independent source and visual review checked numbers, periods, zero-baseline geometry, courtesy and the qualified closing. Buffering, malformed voice-video entries and interrupted-copy recovery have regression tests.
- The accepted NIST story record and all nine referenced media/score assets are **byte-for-byte unchanged**, still delivery `a315989abeedc6ee7f60`.

Physical speaker output and subjective voice appeal are not independently listening-verified. The viewer's judgment remains the final creative acceptance; successful software checks do not stand in for it.

## Earlier work and stop boundary

The native producer desk remains at **http://127.0.0.1:8796/producer.html**. Its completed September 29 proof is preserved in [EASY_NEWS_V1_HANDOFF.md](EASY_NEWS_V1_HANDOFF.md), with operation in [EASY_NEWS_V1.md](EASY_NEWS_V1.md).

The archival reference repository was not inspected or used. No dependency on it was introduced. This completes the requested single-story production pass; do not begin another story or broad feature mission without new direction.
