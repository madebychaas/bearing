# In Focus — the income gain inflation erased

Produced September 30, 2026. Delivery `a7ab64e194631e40f31c`.

## Editorial decision

The user requested one of today's major domestic stories, finished through the same quality milestone as the accepted cybersecurity segment. Today's **BEA Personal Income and Outlays release** supplies the news peg: a new national reading of prices, income and spending, with direct household relevance. August is the measurement period; September 30 is the publication date. We waited for the release rather than substituting a forecast or an older inflation report.

The story is **Inflation erased the income gain.** Its central distinction is that aggregate after-tax income gained no buying power after inflation. This is a national statistic, not a claim about every household's paycheck. The ending poses a meaningful question rather than predicting rates, markets or future income. The viewer's follow-up asked for a new-report lead, source and weekday attribution, a continuous news rhythm, appropriate music, and graphics revealed in reading order.

## Finished script

**The Shift:** A new report shows inflation swallowed Americans' income gains.

**The Pressure:** The Bureau of Economic Analysis said Wednesday that after-tax income rose in August. Prices rose too, leaving buying power flat. Annual inflation was three point four percent, above the Fed's two percent goal.

**What Counts:** The next test: can income start outpacing prices? That's what gives households more room to breathe.

58 words. Warm / Heart runs **26.867 seconds**; Measured / Michael runs **30.500 seconds**, at Natural playback speed. Both retain whole-sentence Kokoro synthesis and the same pitch-preserving 0.93 speaking rate. The revision removes the inserted 1.7-second reading pause and shortens chapter tails from 0.8 to 0.16 seconds. Only verified quiet samples between timed words are compacted, with speech guards and roughly 0.20-second sentence breaths; captions and visual cues follow every edit. No global voice or accepted-story settings changed.

## Source and accuracy review

- [BEA release 26-43, Personal Income and Outlays, August 2026](https://www.bea.gov/news/2026/personal-income-and-outlays-august-2026), published September 30 at 8:30 a.m. EDT and retrieved at 12:30:48 UTC: headline PCE inflation **3.4% year over year**; current-dollar disposable personal income **+0.3% month over month**; real disposable income **0.0%**; real spending **+0.6%**. The mechanism uses words rather than adding three more numerical claims to the screen.
- [Federal Reserve inflation-goal explanation](https://www.federalreserve.gov/faqs/economy_14400.htm): **2% over the longer run**, measured by annual PCE price changes. The chart labels the goal accordingly. This is headline PCE, not core PCE or CPI.
- Today's annual update revises earlier estimates. This story makes no comparison with unrevised July annual inflation. The mechanism explicitly says **August vs. July**, separate from the annual inflation chart.
- The live release was rechecked at September 30, 14:05:56 UTC; relevant figures were unchanged. “Prices rose too” avoids claiming exact equality from rounded monthly changes. Wednesday is the verified release weekday. The spending statistic remains evidence, but is omitted from the shorter narration and graphics.
- The primary release and fixed PDF were retained locally. PDF SHA-256: `b00e0ab232a97032083bb402fee930c68fd556bc066f9b423d1f6588945b2e29`. Domestic post-release corroboration was not yet indexed at the editorial check; the numbers are attributed directly to BEA.

The source-bound packet is [`reviewed-pce-20260930.json`](../channel/production/reviewed-pce-20260930.json). Current-news eligibility requires review after October 2; the entry expires at October 3, 00:00 UTC. A new source correction requires editorial review and a new immutable delivery, not a claim that this fixed cut updates itself.

## Picture and sound direction

Four original scenes serve three chapters:

1. An ink-and-ivory lead establishes the new report's impact. A dry opening accent is audible immediately and ends before the first spoken word. Narration has no gain ramp or fade.
2. The mechanism explains after-tax income up, prices up, buying power flat, revealing each step left to right at its spoken cue.
3. A zero-baseline chart compares annual PCE inflation with the Fed's longer-run goal. The first spoken figure, 3.4%, appears on the left; the 2% goal follows on the right. The chart remains visible under “The next test,” without adding a silent reading pause: the goal stays fully settled for 1.75 seconds Warm / 2.23 seconds Measured before the transition.
4. The closing question appears when “can income” is spoken, resolving toward an open endpoint rather than depicting an invented future outcome.

Picture is 1920 × 1080, 30 fps, with 1.5-second scene blends, no camera shake and no stock footage. The lower picture area leaves room for the existing caption and chapter container. Source credits read **COURTESY / BEA · FEDERAL RESERVE**. All compositions are original code graphics; no third-party images or video are used. [BEA permits reuse of its public-domain information unless otherwise marked](https://www.bea.gov/help/faq/147). No agency logos are reproduced.

The new original score uses a sparse low-register pulse and a dry muted-key alternative. A 0.28-second opening accent replaces the 2.1-second swelling signature. There are no borrowed samples, sentimental chord progression, chime melody, riser or sustained pad. The finite composition spans the complete story rather than repeating a short loop. Dialogue ducks the accompaniment; the voice stays at unity gain with zero fade. Both full mixes decode without clipping. Narration, music and effects remain separately controllable in the viewer. The standalone MP4 includes the complete sound mix and optional embedded English captions.

## Native production path

`production/produce_film.py --input production/reviewed-pce-20260930.json` uses the configured local runtime. It reuses the existing source/script checks, why-now gate, CPU speech provider and production lock. `film_visuals.py` supplies the finished picture; `film_audio.py` supplies guarded silence edits and the revised original score. Both voices must pass duration and full-decode gates before atomic publication.

`dist/films.json` is a delivery manifest merged into the existing playlist, not a second source intake or editorial library. A completed film supersedes a same-URL brief. Updates enter at story boundaries; a failed refresh retains the last playable film. The muted, voice-specific movie follows the existing narration clock for play, pause, seeking and speed changes. Less movement steps through settled, cue-aligned frames. Failed picture playback withholds the story instead of continuing audio over a broken picture.

Reviewed final movies, narration, subtitles, posters, the manifest and exact score assets are versioned. Working frames, intermediate renders, downloaded source copies and production archives stay local. The accepted NIST delivery and its existing renderer remain unchanged.

## Verification boundary

Production checks include both complete movie decodes, frame-clock duration, source/script binding, ordered cues, first-phoneme preservation, quiet-only silence edits, zero narration fade and final artifact hashes. Original chart geometry, left-to-right reveal order and the narrated chart hold have focused tests. Browser verification and repository test results are recorded in the current handoff. Physical speaker output and the user's subjective voice and music preferences remain listening judgments; successful rendering does not claim those are independently verified.
