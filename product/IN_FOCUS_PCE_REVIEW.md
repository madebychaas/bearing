# In Focus — the income gain inflation erased

Produced September 30, 2026. Delivery `0b3b3c40a075da4bed57`.

## Editorial decision

The user requested one of today's major domestic stories, finished through the same quality milestone as the accepted cybersecurity segment. Today's **BEA Personal Income and Outlays release** supplies the news peg: a new national reading of prices, income and spending, with direct household relevance. August is the measurement period; September 30 is the publication date. We waited for the release rather than substituting a forecast or an older inflation report.

The story is **Inflation erased the income gain.** Its central distinction is that spending grew while aggregate after-tax income gained no buying power after inflation. This is a national statistic, not a claim about every household's paycheck. The ending poses a meaningful question rather than predicting rates, markets or future income.

## Finished script

**The Shift:** Americans spent more, but inflation erased the gain in after-tax income.

**The Pressure:** Today's federal report puts annual price growth at three point four percent, above the Fed's two percent goal. After-tax income rose in August. Prices rose, too, leaving buying power flat. Spending still grew, even after inflation.

**What Counts:** The next test: can income start outpacing prices? That's what gives households more room to breathe.

63 words. Warm / Heart runs **33.900 seconds**; Measured / Michael runs **37.767 seconds**, at Natural playback speed. Both retain whole-sentence Kokoro synthesis, with a pitch-preserving 0.93 tempo treatment applied only to this story. An authored 1.7-second breath after “two percent goal” gives the comparison time to land. The score continues underneath. No global voice or accepted-story settings changed.

## Source and accuracy review

- [BEA release 26-43, Personal Income and Outlays, August 2026](https://www.bea.gov/news/2026/personal-income-and-outlays-august-2026), published September 30 at 8:30 a.m. EDT and retrieved at 12:30:48 UTC: headline PCE inflation **3.4% year over year**; current-dollar disposable personal income **+0.3% month over month**; real disposable income **0.0%**; real spending **+0.6%**. The mechanism uses words rather than adding three more numerical claims to the screen.
- [Federal Reserve inflation-goal explanation](https://www.federalreserve.gov/faqs/economy_14400.htm): **2% over the longer run**, measured by annual PCE price changes. The chart labels the goal accordingly. This is headline PCE, not core PCE or CPI.
- Today's annual update revises earlier estimates. This story makes no comparison with unrevised July annual inflation. The mechanism explicitly says **August vs. July**, separate from the annual inflation chart.
- The primary release and fixed PDF were retained locally. PDF SHA-256: `b00e0ab232a97032083bb402fee930c68fd556bc066f9b423d1f6588945b2e29`. Domestic post-release corroboration was not yet indexed at the editorial check; the numbers are attributed directly to BEA.

The source-bound packet is [`reviewed-pce-20260930.json`](../channel/production/reviewed-pce-20260930.json). Current-news eligibility requires review after October 2; the entry expires at October 3, 00:00 UTC. A new source correction requires editorial review and a new immutable delivery, not a claim that this fixed cut updates itself.

## Picture and sound direction

Four original scenes serve three chapters:

1. An ink-and-ivory lead establishes the lost income gain. Voice begins at 0.52 seconds, overlapping the original musical signature.
2. A zero-baseline chart compares annual PCE inflation with the Fed's longer-run goal. Each value appears at its spoken cue. The 2% figure remains fully settled for **2.17 seconds Warm / 2.59 seconds Measured** before the following transition.
3. A different graphic explains the mechanism: after-tax income up, prices up, buying power flat. The spending distinction appears only when the narration reaches it.
4. A restrained closing asks whether income can outpace prices, resolving toward an open endpoint rather than depicting an invented future outcome.

Picture is 1920 × 1080, 30 fps, with 1.5-second scene blends, no camera shake and no stock footage. The lower picture area leaves room for the existing caption and chapter container. Source credits read **COURTESY / BEA · FEDERAL RESERVE**. All compositions are original code graphics; no third-party images or video are used. [BEA permits reuse of its public-domain information unless otherwise marked](https://www.bea.gov/help/faq/147). No agency logos are reproduced.

Music and punctuation use Bearing's existing original composition and synthesis, with no third-party samples. Dialogue ducks the score. Both full mixes decode without clipping; sample peaks are below 0.821, so no additional limiting attenuation was needed. Narration, music and effects remain separately controllable in the viewer. The standalone MP4 includes the complete sound mix and optional embedded English captions.

## Native production path

`production/produce_film.py --input production/reviewed-pce-20260930.json` uses the configured local runtime. It reuses the existing source/script checks, why-now gate, CPU speech provider, score and production lock. A new `film_visuals.py` compositor supplies the finished picture. Both voices must pass duration and full-decode gates before atomic publication.

`dist/films.json` is a delivery manifest merged into the existing playlist, not a second source intake or editorial library. A completed film supersedes a same-URL brief. Updates enter at story boundaries; a failed refresh retains the last playable film. The muted, voice-specific movie follows the existing narration clock for play, pause, seeking and speed changes. Less movement steps through settled, cue-aligned frames. Failed picture playback withholds the story instead of continuing audio over a broken picture.

Reviewed final movies, narration, subtitles, posters, the manifest and exact score assets are versioned. Working frames, intermediate renders, downloaded source copies and production archives stay local. The accepted NIST delivery and its existing renderer remain unchanged.

## Verification boundary

Production checks include both complete movie decodes, frame-clock duration, source/script binding, ordered cues, a quiet insertion point for the reading pause and final artifact hashes. Original chart geometry and timed reveals have focused tests. Browser verification and repository test results are recorded in the current handoff. Physical speaker output and the user's subjective voice preference remain listening judgments; successful rendering does not claim those are independently verified.
