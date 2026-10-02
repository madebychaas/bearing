# Bearing: broader sources and live updates

Historical assessment and implementation: September 28, 2026. For the current October 2 source roster, independent intake, national desk and coverage gaps, see [National assignment desk](NATIONAL_ASSIGNMENT_DESK.md). Counts and schedules below describe that earlier checkpoint.

## Decision

Use source polling plus complete, versioned editions for v1. The viewing experience stays continuous: new segments enter between stories. Expand the reporting pool broadly, but allow automatic narration only where both content quality and the source policy permit it. A source link, a completed segment, and a cleared publication licence are different things.

## What is connected

The first expanded collection returned 476 unique candidates from 20 responding endpoints across 14 publisher groups. After date, URL, and basic content checks, 339 recent links were available in the reader. Nineteen feeds had at least one recent item. These are observed results from one run, not availability guarantees. Counts change as feeds update.

| Coverage | Active sources | Narration treatment |
|---|---|---|
| Space | NASA | Complete, attributed agency excerpts may enter automatic production. |
| Nature and science | NOAA, USGS | Same restricted automatic path; sensitive or incomplete excerpts held. |
| Technology | NIST, NSF, BBC | NIST eligible for restricted production; NSF/BBC require review. |
| World and society | BBC, NPR, PBS NewsHour, Guardian, DW, France 24, Al Jazeera | Source discovery and original links; source-grounded script and reuse review before narration. |
| Business and economy | BBC, Federal Reserve | Review, including the distinction between proposals, decisions, and outcomes. |
| Health | BBC | Review before narration; no automatic medical guidance. |
| Art and culture | BBC, Guardian | Discovery plus the existing reviewed cultural segment. |
| Sport | BBC Sport | Discovery; narrated coverage not yet supplied automatically. |
| Optional local coverage | KERA, North Texas | Available as an optional interest, not inferred from device location. Region can be changed. |

BBC's section feeds count as one publisher group. Syndicated reporting across different sites should not be treated as independent corroboration. This is currently an English-language mix with a substantial US/European tilt. Broad geographic coverage does not imply balanced representation of all regions.

Three original, source-checked additions broaden the playable edition: [NIST cybersecurity workforce awards](https://www.nist.gov/news-events/news/2026/09/nist-awards-more-17-million-support-cybersecurity-workforce-development), [Federal Reserve stablecoin proposals](https://www.federalreserve.gov/newsevents/pressreleases/bcreg20260924a.htm), and the [Council of Europe human rights prize](https://www.coe.int/en/web/portal/-/2026-v%C3%A1clav-havel-prize-awarded-to-iranian-human-rights-lawyer-nasrin-sotoudeh). Their scripts distinguish an award or proposal from demonstrated results. The September 28 design revision gives each its own disclosed conceptual AI illustration: a learning workspace, a reserve-backed token concept, and an imagined award with a letter. These are not event photographs or precise depictions of actual objects.

The probe rejected old Library of Congress, NIH, and BLS URLs that returned 404, and a Texas Tribune endpoint that returned 403. They are not configured as working sources. Those results do not establish that the publishers lack other usable feeds.

## Updates running now

- Latest is now the default view, with precise publication times, recent-news windows, and updates checked every 30 seconds. The illustrated channel remains in Watch. See `LATEST_NEWS.md` for the current behavior and limits.
- A local worker checks due sources every minute. Eight general-news feeds have a five-minute target; BBC feeds retain fifteen minutes and agency feeds thirty or sixty. A publisher's longer RSS TTL takes precedence.
- Four concurrent fetches, 18-second request timeout, 2 MB response ceiling, approved HTTPS hosts and redirects.
- ETag/Last-Modified conditional requests where publishers support them; HTTP 304 reuses retained content. A failing source retries with increasing intervals up to six hours. Healthy sources continue independently.
- RSS, Atom, and RDF parsing; canonical URL deduplication removes known tracking parameters without deleting article IDs.
- Candidate publication dates and complete excerpt checks remain separate from network health. Undated, future, old, truncated, or sensitive content cannot enter the unattended narration path.
- Topic and publisher variety guide selection. Recent source dates guide retention; up to four stories per topic and 24 overall. The produced-URL index prevents repeated generation of evicted stories.
- Each playable segment now requires its own visually inspected, script-bound artwork and matching video. Missing art produces a local visual request; it does not trigger speech work or shared topic art. When three or more selected topics have ready stories, playback uses at most two per topic per lap, with other stories appearing in later laps.
- Changed feed text withdraws an affected automatic segment at an edition boundary, with the previous version retained locally. This is not full-article correction tracking or independent fact checking.
- Both local neural voices, matching captions, file hashes, durations, and media decoding must pass before publication. Audio filenames include a script hash. The edition JSON is replaced atomically.
- An active viewer checks the edition every minute and when returning to the tab. Current narration continues; the pending edition applies at the next story boundary. No ticker, interrupting alert, or unsolicited sound.

For the 15-minute feeds, budget roughly 15–25 minutes from a publisher exposing an item to source-link discovery under normal operation. This is an engineering estimate, not a measured service guarantee. A finished video segment now also waits for bespoke artwork generation and visual review; no unattended completion time is promised for that step. Publisher delays, editorial review, production queues, failures, computer sleep, and background-tab throttling can extend latency. The 30–60-minute feeds naturally take longer. Source links can appear before narration is ready.

## Options assessed

| Option | What it adds | Tradeoff and recommendation |
|---|---|---|
| Publisher RSS/Atom with conditional polling | Straightforward, inexpensive discovery with direct attribution | Running now. Feed availability and excerpt quality vary; this is near-live coverage, not a wire-service SLA. |
| AP Media API | Professional multimedia delivery, continuing news feeds, and linked content | Best next option to investigate for dependable broad narrated news. Requires an account and an appropriate agreement, explicitly covering the intended AI adaptation/narration. Price and rights were not assumed. [AP developer portal](https://developer.ap.org/), [feed delivery documentation](https://api.ap.org/media/v/docs/Feed.htm). |
| NewsAPI | A broad discovery API and production-tier real-time article availability | Its free developer tier has a 24-hour delay and is development-only. Business is listed at $449/month billed monthly; it does not provide full article text. Useful discovery infrastructure, but not a replacement for checking publishers' adaptation rights. Not connected or purchased. [Official pricing and FAQ](https://newsapi.org/pricing). |
| GDELT | Global discovery and research metadata on a 15-minute cycle | Useful later to detect geographic blind spots and compare coverage; requires filtering and event grouping. It indexes reporting and does not establish the truth of every claim or clear publisher narration rights. Not connected. [GDELT description](https://blog.gdeltproject.org/gdelt-2-0-our-global-world-in-realtime/). |
| WebSub | Publisher-to-server push notifications | Requires a publisher-advertised hub, reachable callback, renewal and verification. Bearing does not expose a public callback or assume source support. Add selectively when actual publishers support it. [W3C WebSub](https://www.w3.org/TR/websub/). |
| Server-sent events from our own backend | Quicker delivery of a completed edition to viewers | A future delivery improvement; it does not accelerate source publication, editorial checks, or media generation. Minute polling is sufficient for the current local player. |

Do not label the current system “live video.” It is a continuously playing channel of dated, generated segments that updates as complete editions become available.

## Publication and remaining work

The local reader shows credited titles and links. It does not assume that RSS access permits a commercial AI news channel. The [BBC feed terms](https://downloads.bbc.co.uk/usingthebbc/bbc_terms_of_use_31March2022english.pdf) distinguish individual use from business licensing. The [NIST policy](https://www.nist.gov/open/license) and [USGS policy](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits) also distinguish agency-created work from third-party material. Those distinctions are recorded in the source registry; they are not blanket rights clearance.

Before wider public operation: establish appropriate publisher/newswire agreements; add an editorial review interface with evidence and correction history; improve story-level deduplication and regional coverage; and move ingestion/rendering to an always-on worker with monitoring. A private static hosting snapshot would not run this local Python worker or update itself. No paid account, subscription, external upload, or cloud service was created for this expansion.

## Verification

25 automated checks passed. Live probes confirmed all 20 configured feed endpoints. The complete 11-segment edition decoded and passed its media checks after adding the three reviewed stories. Browser checks verified the 339-link library, publisher interleaving, health filtering, nine interest choices, actual playback of a new segment, and pending-edition application only at the next story boundary. The source dialog fits a 390 px viewport without horizontal overflow. This verifies operation, not a human listening judgment or an availability SLA.
