# Easy News V1 — producer guide

Easy News is the producer workspace at **http://127.0.0.1:8796/producer.html**. Bearing remains the viewing product at the root URL. Both run from `channel/Start Bearing.cmd` and use the same reporting intake.

## Use the desk

1. Start with **The Brief** for immediate-awareness candidates, or **In Focus** for opportunities that deserve explanation. Each has its own ranking and source-linked reasons.
2. Select a story to inspect the news peg, detected change, strategy fit, product requirements and supporting reporting. Publication time means the source published something then; it does not prove the underlying development is new.
3. Use the filters to inspect updates, watch-worthy stories, local signals, your shortlist or dismissed items. Held alternatives remain inspectable without crowding the top recommendations.
4. Shortlist, watch or dismiss a candidate, optionally with an editorial note. Reset returns it to unreviewed candidates. Decisions persist across reloads and server restarts, with an inspectable history. These controls do not assign, produce, approve or publish anything.
5. Open **Strategy & products** to inspect the configured editorial purpose and product definitions. Edit `channel/production/producer-strategy.json` and restart the server to change this single desk's configuration. V1 has no profile-management system.

The page checks every 30 seconds while visible. The server observes existing reporting every 20 seconds, even when the page is closed. Collection remains the existing single pipeline, with publisher polling intervals, cache TTLs, backoff and production-cycle timing. This is a continuously refreshed editorial desk, not a claim of instantaneous source delivery. Feed-check age, availability and publication age remain distinct.

## Representative proof

Switch Reporting to **Representative cycle**. It is synthetic, labeled throughout, and uses a fixed sample clock and separate local state. No sample appears in Bearing or live news.

The baseline includes an actionable product recall, a housing-policy explanation, a court decision, an outage, a developing water investigation, three independent local insurance reports, syndicated copies, political sparring, promotional material, old reporting and a future-dated report. The Brief and In Focus should lead with different stories.

Make a sample editorial decision, then choose **Next development**. The second step changes consequential facts in existing reports, adds a source, and makes cosmetic wording changes. Compare the before/after evidence and the editorial record. Material flags are review prompts; a headline rewrite or additional publisher alone is not confirmation of a new development. A dismissed story with a detected material change remains visible in the updates filter without silently reversing the dismissal.

The local signal requires three distinct markets, identified original reporting, separate ownership and nonduplicated excerpts. Syndicated copies cannot satisfy that threshold. Open the linked evidence and assess comparability before treating convergence as a national story. Patterns follow configuration order, so the specific insurance question takes precedence over a broader housing match using the same reports. **Reset cycle** clears only the disposable sample record and returns to the first step; live decisions are unaffected.

## What is reused

The existing `pipeline.py` collector, approved source registry, retained feed cache and conservative `coverage.py` event IDs remain authoritative. Easy News reads `dist/reporting.json`, `dist/source-status.json` and local `production/candidates/latest.json`. It does not ingest feeds again or maintain a competing story library.

`production/producer.py` derives the producer view and keeps the local observation/decision ledger. `producer-strategy.json` defines this desk's editorial rules and independent product weights. `producer-demo.json` is a versioned synthetic fixture. `dist/producer.html`, `producer.css` and `producer.js` provide the native interface without a new framework or build step. `production/server.py` exposes the local API and runs the observer.

The JSON API is `/api/producer?mode=live` (or `demo`), with decision and sample-cycle POST routes under `/api/producer/`. Mutation requests require local-origin JSON. The HTTP server binds to loopback; there is no remote collaboration or authentication system. Run one server per checkout: the store serializes calls within that server and atomically saves its files, but it is not a multi-process database.

Local state lives in ignored `production/runs/producer-state.json` and `producer-demo-state.json`. Raw feed excerpts stay in the local production/producer path. Opening a source link does not establish commercial reuse rights. No excerpt is automatically transformed into a script or published programme by this workspace.

## Deliberate limits

- Recommendations are inspectable rules over attributed feed titles and excerpts, not semantic fact verification. Thin evidence, speculative wording, source outages and stale dates remain visible.
- Change detection compares observations the local server actually saw. It cannot reconstruct earlier edits, detect every subtle correction, or monitor full article bodies outside the feed. A changed number or action is a potential material change to inspect, not a verified conclusion.
- The current conservative grouping keeps coverage IDs stable for supported matches. It does not automatically join every new article URL, reversal or related angle into a long-running story. Duplicates can remain; weak similarities are not forced together.
- Live local-to-national discovery requires explicit original-reporting and geographic provenance that the current feeds generally do not supply. The sample demonstrates the gate; the live desk must not manufacture those signals from publisher location or repeated wire copy.
- AP and CNN remain source links pending suitable access. Their reporting is not claimed as ingested, and feed health counts describe only configured working feeds.
- The producer's useful work is selection and judgment. Trusted inventory, generalized profiles, assignment management and broad automated production remain outside this milestone.

The accepted Bearing story-quality milestone, its graphics, narration, player, media and playlist behavior are preserved. The archival `easynews-reference` project was not inspected or used for this implementation.
