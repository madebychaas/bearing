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
