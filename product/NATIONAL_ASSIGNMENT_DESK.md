# Bearing national assignment desk

Checkpoint: October 2, 2026.

The current mission is to keep Bearing aware of consequential national news, identify what changed and why it matters today, and give a producer the next reporting question. The personalized-newscast feature is parked while this sourcing foundation improves.

The desk is available at `/producer.html`. It gathers source material, groups related reporting, and proposes leads. A lead is not a verified story, an assignment, or permission to produce and publish a segment.

## Editorial scope

The scope is U.S. national news, with international developments included when the reporting indicates substantial U.S. or cross-border consequences. Household costs, jobs, the economy, consumer protection, consequential government action, health, major hazards, and significant technology developments are central beats. A story's location alone does not decide its importance: a local event can have national consequences, while an article from a national publisher can remain a local brief.

The desk retains reporting broadly, then separates it into:

- **Today's leads:** recent reporting with a possible concrete development and national consequence.
- **Developing:** a possible meaningful change to retained reporting, with before/after evidence to inspect.
- **Watch:** anticipated decisions or releases, public-inspection filings, updated-only source clocks, and recent reports whose today peg still needs verification.
- **Held / out of scope:** local reporting, stale or unavailable evidence, unusable timestamps, commentary and promotion, or material without established national relevance.

These are explainable heuristics over headlines and available excerpts. They can miss a story, infer the wrong scope, or overvalue an institutional announcement. A producer must confirm the event timing, affected audience, scale, source context, and practical consequence. Routine research, institutional promotion, evergreen explainers, and political sparring do not deserve elevation merely because they were posted recently. Science remains eligible when there is an actual consequential development.

Ordinary local weather warnings are retained for checking rather than filling the national agenda. Extreme coastal hazards can prompt national assessment; that classification is still not proof of nationwide impact. NHC's Miami dateline is not the storm's location. Routine tropical outlooks and “no tropical cyclones” placeholders must not become breaking-news stories. Specialized cyber advisories likewise need a meaningful public or infrastructure consequence.

The today's-news boundary uses **America/Chicago**. Overnight reporting can still be relevant, but its publication clock does not establish that the underlying event happened today.

## Connected discovery sources

The registry contains **28 enabled endpoints**, including **13 added at this checkpoint**. Endpoint count is not a count of independent reporting organizations. Multiple feeds from CBS, NPR, PBS, NOAA, or another publisher must not be treated as separate confirmation; republications of the same wire report also require lineage checks.

KERA is disabled for this national exercise and retained in the registry as a local source. Existing national publisher and agency sources remain available, including Axios, CNBC, NPR, PBS, the Federal Reserve, FTC, NASA, NOAA, NSF, NIST, and USGS. BBC reporting remains available for relevant international context.

The additions below returned valid responses during verification on October 2. Runtime availability can change; the source-health panel is the current operational record.

| Added endpoint | Purpose | Configured minimum interval |
| --- | --- | --- |
| [CBS U.S.](https://www.cbsnews.com/latest/rss/us) | National reporting | 5 minutes |
| [CBS MoneyWatch](https://www.cbsnews.com/latest/rss/moneywatch) | Consumer and economic reporting | 5 minutes |
| [New York Times U.S.](https://rss.nytimes.com/services/xml/rss/nyt/US.xml) | National reporting and consequential policy | 5 minutes |
| [BEA releases](https://apps.bea.gov/rss/rss.xml) | Primary economic releases, including GDP and personal income/outlays | 17 minutes |
| [SEC releases](https://www.sec.gov/news/pressreleases.rss) | Financial regulation, enforcement, and investor impact | 5 minutes |
| [FDA recalls](https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/recalls/rss.xml) | Product safety and consumer action | 6 minutes |
| [FDA releases](https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/press-releases/rss.xml) | Health and regulatory developments | 5 minutes |
| [CISA advisories](https://www.cisa.gov/cybersecurity-advisories/all.xml) | Cybersecurity signals requiring public-impact assessment | 5 minutes |
| [NHC Atlantic](https://www.nhc.noaa.gov/index-at.xml) | Tropical hazard monitoring | 5 minutes |
| [NHC eastern Pacific](https://www.nhc.noaa.gov/index-ep.xml) | Tropical hazard monitoring | 5 minutes |
| [USGS significant earthquakes](https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_day.atom) | Significant seismic events and updates | 1 minute |
| [NWS severe/extreme alerts](https://api.weather.gov/alerts/active.atom?severity=Extreme,Severe) | Official hazards, with geographic and editorial filtering | 1 minute |
| [Federal Register public inspection](https://www.federalregister.gov/api/v1/public-inspection-documents/current.json) | Newly filed federal documents to inspect | 5 minutes |

These additions are marked for **discovery and review**, not automatic narration or publication. The endpoint documentation is available from [CBS](https://www.cbsnews.com/rss/), [BEA](https://www.bea.gov/resources/for-developers), [SEC](https://www.sec.gov/about/developer-resources), [FDA](https://www.fda.gov/about-fda/contact-fda/subscribe-podcasts-and-news-feeds), [NHC](https://www.nhc.noaa.gov/mobile/rss.html), [USGS](https://earthquake.usgs.gov/earthquakes/feed/v1.0/atom.php), and the [Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1).

An institution is authoritative about its own release, but that does not make its framing independent reporting. Major claims and consequences still need scrutiny and, where relevant, independent confirmation.

## Gathering and freshness

`server.py` runs a source-gathering loop independently of media production. It checks for due work on a **30-second cadence**, with bounded parallel requests in `pipeline.py`. Rendering a segment no longer needs to finish before the next intake check can begin. A slow collection can take longer than the nominal interval; checks do not overlap to create an expanding backlog.

Thirty seconds is the scheduler cadence, not a promise to request every source twice a minute. Each source retains its configured interval, RSS TTL, HTTP cache duration, ETag/Last-Modified validators, and failure backoff. The effective interval uses the applicable longer cache requirement. BEA's observed RSS TTL is 17 minutes. [NWS guidance](https://www.weather.gov/documentation/services-web-alerts) recommends no more than one alert request every 30 seconds; Bearing's configured interval is one minute. [USGS documents](https://earthquake.usgs.gov/earthquakes/feed/v1.0/atom.php) minute-level feed updates.

Health distinguishes an actual network attempt, a successful response or 304, a cached result, and an unavailable source waiting for retry. It records request duration, last success, next check, effective interval, and available source timestamps. A successful request with no events can be healthy. A successful request containing old articles does not establish current coverage. Partial outages retain earlier reporting with the source marked unavailable.

The collector writes `production/runs/intake-snapshot.json` atomically with reporting, candidates, and source health from the same intake. The producer reads this coherent snapshot instead of joining separately replaced files from different moments. Existing editorial decisions and comparison history remain separate from the collector's source records.

The retained clocks have different meanings:

| Clock | Meaning |
| --- | --- |
| Source publication time | The publisher's reported publication time, when supplied precisely. |
| Source update time | A source's update clock; it does not prove a new event occurred. |
| First seen | When Bearing first collected the report. Initial backlog is explicitly distinguished from a new arrival. |
| First revision seen | When Bearing observed a changed version of source text. |
| Material-change observation | When retained evidence first showed a possible consequential quantity or action change. |
| Filing time | When a Federal Register document became available for public inspection. |
| Scheduled release time | An originating agency's planned release time, not confirmed publication. |

The event's actual time remains a reporting question when the evidence does not establish it. Refreshing a feed, changing formatting, or adding another publisher does not create a new development. A headline announcing an outcome while its excerpt still describes a forecast goes to Watch for reconciliation rather than being treated as confirmed results.

## Scheduled releases and documents

`release_calendar.py` reads the [official BEA calendar](https://www.bea.gov/news/schedule/ics/online-calendar-subscription.ics), linked from BEA's [release schedule](https://www.bea.gov/news/schedule). Refresh is conditional and no more frequent than hourly. Desk reads use the retained cache without making network requests.

Calendar handling preserves stable identifiers, folded text, explicit time zones, and source revisions. Date-only or timezone-free entries are not assigned invented times. Cancelled entries are removed. The desk shows up to 12 events across the next seven days and the previous six hours. A due event says to check the source; it does not report that the release happened. Failures preserve the last good schedule with explicit stale/error information. Older reference periods in release titles describe the scheduled data, not a new claim about current conditions.

`primary_feeds.py` reads bounded Federal Register public-inspection metadata. It retains the document type, agency, filing time, and planned publication date without inventing an explanatory excerpt. A filing is a **watch lead**. It is not automatically a final rule, a published rule, or an action already in effect. Inspect the underlying document and effective dates before making those claims. FederalRegister.gov also distinguishes its informational XML from the official legal edition; legal-effect reporting must be checked against the corresponding official document. [Federal Register documentation](https://www.federalregister.gov/developers/documentation/api/v1)

## Coverage and access gaps

- **BLS:** official news feeds and its calendar returned HTTP 403 from this machine during this checkpoint. Publisher coverage does not replace direct verification of a jobs or inflation release. [Official BLS feeds](https://www.bls.gov/feed/) and [calendar](https://www.bls.gov/schedule/)
- **Department of Labor:** the official release feed returned HTTP 403. Direct weekly-claims and labor-policy gathering is not connected. [Official DOL feed information](https://www.dol.gov/rss)
- **AP:** no licence or supported API access has been supplied. It remains a source link, not a working wire feed. [AP Media API documentation](https://api.ap.org/media/v/docs/Getting_Started_API.htm)
- **CNN:** no licensed access is configured; previously tested legacy RSS did not pass verification. It remains a source link.
- **Courts and Congress:** no direct national court-opinion or congressional-action feed is connected. Publisher reporting is useful discovery but leaves a primary-source gap. [Supreme Court source materials](https://www.supremecourt.gov/publicinfo/publicinfo.aspx)
- **Other gaps:** direct Treasury announcements, comprehensive national transportation disruption, and full international primary-source coverage are not established by this set of feeds.

There is no paywall or access-control workaround. A source that fails remains visibly unavailable or unconnected. The coverage panel describes the material collected by Bearing; it is not an inventory of every important event in the country.

## Rights and operating limits

**Availability is not a reuse licence.** RSS access, a successful HTTP response, an embedded image, or government hosting does not grant rights to reproduce third-party text, audio, video, or photographs. Publisher excerpts stay in the local editorial workflow; production still requires source-bound editorial review and appropriate media rights. The new discovery sources do not authorize automatic narrated derivatives. A government page can contain separately copyrighted material.

The first timing instrument measures source publication to Bearing's first observed arrival after a fixed, instrumented baseline for that source. Initial or migrated backlog, pre-baseline backfill, future timestamps, and updated-only clocks are excluded. Reports published after that baseline but indexed late by a feed remain in the sample, even if earlier polls missed them; excluding these delays would flatter the result. The desk exposes sample size, median, and P90. This is an operational proxy, not event-to-detection latency, and not a measurement against CNN, Fox News, or the New York Times. There is no measured basis yet for claiming Bearing is faster than those newsrooms. A useful future comparison must match the same event and documented detection times, while also measuring misses and incorrect leads.

This checkpoint runs on the local server. The machine must remain awake, connected, and running Bearing for continuous gathering. `--no-media` keeps intake running without background media generation; `--no-refresh` stops automatic gathering too. No hosted always-on service, external push-wire subscription, or unattended uptime guarantee has been established.

Runtime caches, discovery ledgers, source-health snapshots, calendar state, and the endpoint-probe evidence under `output/assignment-desk/` are operational state and remain outside Git. Source configuration and the native implementation are versioned. Archival EasyNews material is not part of this mechanism.

## Checkpoint verification

At 13:11 UTC on October 2, all 28 enabled endpoints were available. The national desk showed 14 possible current leads, 79 watch items and 419 held/out-of-scope events. These changing counts show the current retained coverage, not everything happening nationally. BLS, DOL and other unconnected sources are outside that health denominator and remain named gaps.

The full run passed **262 Python tests and 72 JavaScript tests**. A real Chrome session at 1478 × 910 verified the live lane filters, held-source inspection, source excerpts, source gaps, scheduled-only calendar, and refresh retaining the selected story and open evidence. The outer desktop page did not scroll. Runtime checks saw successive independent intake cycles; a regression also gathers successfully while the production lock is occupied. No accepted film, script, voice performance or player code changed.

The first live review caught routine NHC products elevated by their agency dateline, partial-word beat matches, a forecast excerpt paired with released jobs figures, a retrospective political headline, and mismatched clocks across clustered reports. These now have regression coverage. This is evidence of an improved, inspectable triage path, not a claim that keyword heuristics can replace a national editor. Local browser evidence and test logs remain in ignored `output/assignment-desk/`.

## Top stories orientation

The initial implementation below was extended to 15-minute editions and a single current-story list; see the follow-up after this checkpoint for the current publication behavior.

The top of the national desk now offers one horizontal container with three ranked story cards: a concise change-led headline, one supporting sentence, source attribution and optional original illustration. Clicking a card opens that exact event, including a top-story outside the active list filter, and exposes the supporting primary context. The ordinary source evidence and production approval path remain separate.

The `top_stories.py` rubric favors national scale and consequence over a fresh timestamp. An active large-scale hazard outranks economic coverage; major labor/inflation/growth/rate developments, national policy, fuel supply, housing borrowing costs and public accountability have explicit consequence classes. Institution names, routine launches, individual enforcement cases, commentary and local-only stories do not fill gaps. Duplicate jobs and fuel reports occupy one hero slot. This bounded rubric will miss unfamiliar developments; it is a current editorial shortlist of connected reporting, not an exhaustive measure of national importance.

Optional `top-stories-editorial.json` copy is bound to event/report identity and a hash of the exact retained headline, excerpt, URL and source clock. It expires within four hours. Supporting primary evidence must have been checked within an hour before that review; clocks retain whether they mean publication, observed confirmation or a discovery report's publication. A current higher-impact hazard can displace a lower-tier reviewed choice. An explicitly reviewed continuing-impact carry may use a report up to 48 hours old, but cannot override a held source, conflicting evidence, local scope or source failure. When a source changes, bespoke copy and art stop displaying; exact current publisher copy remains the fallback. No approval is manufactured and no story is published into the video queue by this hero.

The October 2 initial edition leads with U.S. hiring, the new G7 fuel-release agreement, and Thursday's latest mortgage benchmark. It is grounded in the [BLS September employment release](https://www.bls.gov/news.release/empsit.nr0.htm), the [October 2 G7 statement](https://www.elysee.fr/emmanuel-macron/2026/10/02/g7-leaders-statement-on-global-energy-security-and-market-stability), and [Freddie Mac's mortgage survey](https://www.freddiemac.com/pmms). The G7 statement confirms an implementation schedule; it does not prove deliveries or retail-price relief. The mortgage survey remains dated Thursday rather than being promoted as a new Friday announcement. BLS page verification through the browser/web tool does not repair the machine's disconnected feed.

Three original 1672×941 PNG illustrations live in `channel/dist/assets/top-stories/`. Their [prompt and provenance manifest](../channel/production/top-stories-art-20261002.json) records built-in image generation, inspection and file hashes. They are conceptual imagery, visibly labeled AI illustration, and have not been upscaled or rendered into a film. Future production may reuse a still only if it remains appropriate for that script. Typography stands on its own whenever no current, matching illustration is available.

Top-stories verification: **281 Python tests and 77 JavaScript tests pass**, including reviewed Watch promotion, source/clock validity, copy/art expiry, consequence ordering, duplication and exact event selection. Real Chrome checks at 1478 × 910 and 1242 × 698 CSS pixels kept the outer desktop page scroll-less; mobile at 355 × 767 stacked the three cards without horizontal overflow. All illustrations loaded, all three selections opened their exact reporting (including the mortgage story outside the Today filter), and the primary-source context/link/excerpt was inspected. Refresh retained selection, focus, open evidence, the editorial disclosure and an unsaved note; the test note was then cleared. Coverage opens over the workspace, and collapsed decision controls preserve room for evidence. The existing preparation dialog opened for the selected event without saving or producing anything. Network-outage display is implemented but was not forced against the running local server. Browser screenshots and full test logs remain local under ignored `output/top-stories/`.

A live CNBC feed-clock change during final verification also removed the G7 authored card as intended. Its headline/excerpt had not changed. The primary G7 statement was reread before rebinding the new exact source hash; that reassessment and the prior hash are retained in the editorial record. The original observed-confirmation clock was preserved, rather than promoting the feed timestamp into a new development.

## Fifteen-minute editions and current-story list

The front page now uses one complete national ranking. Top stories occupies its first three positions; the remaining current stories continue in that order in one internally scrolling list. The separate Brief/In Focus rank views, lane filters and pagination are hidden in live mode and retained for the representative cycle. Selecting any story still opens its exact source evidence and existing editorial/production controls. The watch player remains unchanged.

`top_stories.rank()` expands the consequence rubric beyond the initial economic cases to national health, infrastructure, rights, federal operations, security and meaningful world consequences. Its lower tiers use exact-report strategy evidence for consumer, work and public-service developments. A high raw score, a repeated keyword or an agency name cannot qualify a story by itself. Macro duplicates share one position; general policy stories need overlapping subject evidence before they are collapsed. The result is a bounded shortlist of the connected coverage, not all national news or an objective national-importance score.

`top_story_editions.py` maintains the assessed order, next scheduled check, staged replacement, source-bound finished tiles and claim leases in `production/runs/top-stories-editions.json`. The existing background observer checks the 15-minute due time independently of browser activity. It performs no model or network-generation call inside the producer lock. The UI polls for readiness every 30 seconds; its Refresh button does not reset the editorial schedule. A complete new edition replaces the last valid edition only after its selected hero tiles are ready. The initial hero stays withheld until its selected tiles are ready. Removed evidence leaves a rank gap until the next scheduled assessment rather than secretly promoting the fourth story on a UI poll.

Every view rechecks exact source identity, eligibility, source health and review expiry. Corrections, holds and stale reporting remove affected treatment immediately even while the next edition is being prepared. A trusted checked-in illustration must match its inspected provenance hash. Runtime completions must include a source-bound editorial review, fresh primary support, the actual generation prompt and visual review, a matching file hash and a valid landscape image. The browser separately loads and decodes incoming images before committing complete tiles; failed media never creates a half-ready card.

`GET /api/top-stories/jobs` and local-origin-protected `POST /api/top-stories/prepare` expose the narrow claim/complete/hold flow. Twelve-minute leases prevent concurrent duplicate preparation; restart preserves jobs, expired claims become available again, superseded sources lose authority, and held work backs off by at least 15 minutes. The client is `production/top_story_worker.py`; the complete operating procedure and receipt format live in [Top stories worker](TOP_STORIES_WORKER.md). Long-unattended pending work is marked as needing attention. No generated tile confers script or video approval.

The local chat heartbeat **Bearing Top stories preparation** is active every 15 minutes and uses the built-in image-generation tool for new stories. Its scope is the runtime queue, fresh editorial/source review and inspected imagery; it cannot change tracked code or Git, inspect archival reference material, resume personal-newscast work or publish a film. The desktop app, machine and Bearing server must remain running. No dedicated image API or new model credential was installed. The first live queue completion reused the inspected fuel illustration for a new PBS report of the same G7 agreement, after rereading the primary statement. That proves the real claim/review/ready-publication path; it does not claim a future unattended run or a newly generated picture was observed in this checkpoint.

Runtime originals named `live-*`, queue state, claims and receipts are excluded from Git. Existing original illustrations and accepted media remain preserved.

Verification: **318 Python tests and 82 JavaScript tests pass.** Tests cover the scheduled edition boundary, all-ready publication, source/art invalidation, exact-source completion, durable exclusive leases/retries, local HTTP access and production isolation. Real Chrome checks covered pending-to-ready publication, all three decoded images, rank 4/5 continuation, source context, keyboard selection and refresh preserving an open decision drawer and unsaved note. Desktop at 1478 × 910 and 1242 × 698 CSS pixels had no outer scroll; the compact list scrolled internally and mobile at 355 × 767 had no horizontal overflow. A real server restart preserved the three ready tiles, original prepared time and next scheduled review. The active local heartbeat configuration was verified; its first unattended execution has not yet been observed. Proof and test logs remain in ignored `output/top-stories/`.
