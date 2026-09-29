# Easy News — V1 producer handoff

**Status: V1 working proof complete. Stop here pending a new mission.**

Delivered September 29, 2026 in implementation commit `312011e`. This closes the implementation proof activated by `4083efd`; it does not claim that the user has accepted the new producer experience. Do not begin a generalized platform, more profiles, automatic assignments, or expanded media production without a new mission.

## Open it

Run `channel/Start Bearing.cmd` and open **http://127.0.0.1:8796/producer.html**. The existing Bearing viewer remains at **http://127.0.0.1:8796/**. The normal local server is running with automatic source refresh enabled. The temporary test server was stopped.

The [V1 guide](EASY_NEWS_V1.md) describes operation, configuration, the representative cycle and the implementation boundaries. [EASY_NEWS_DIRECTION.md](EASY_NEWS_DIRECTION.md) remains the enduring producer direction. [COVERAGE_RADAR.md](COVERAGE_RADAR.md) remains supporting exploration, not a separately activated build.

## What works

- A producer workspace over the existing collector, retained source reports and canonical coverage IDs. No second ingestion system or manually maintained story library.
- Independent **The Brief** and **In Focus** recommendations. Product-specific reasons expose practical consequence, immediacy, explanatory potential, evidence and gaps. Top candidates stay manageable; alternatives remain inspectable.
- Source publication time, feed health and refresh time remain distinct. Rechecks and cosmetic wording do not create material-update alerts. Potential material changes show exact retained before/after reporting for inspection.
- Shortlist, watch, dismiss and reset with notes and persistent decision history. A dismissed story with a detected material change resurfaces in Updates without reversing the human decision. No action assigns, generates or publishes a story.
- Local-to-national leads require identified original reporting from three separate owners and markets, with wire and near-duplicate exclusion. Actual contributing reports are inspectable across stories. The sample proves this; current live intake has no qualifying provenance-backed pattern.
- An explicitly synthetic, isolated representative cycle proves product differentiation, expanded recall scope, cosmetic revisions, additional reporting, developing stories, held material and local convergence. Sample actions never affect live decisions or Bearing's playlist.

At verification, the live intake contained **220 reports / 217 grouped events**, with **16 of 16 configured feeds available**. These counts are observations, not fixed product guarantees. The Brief prioritized a student-loan deadline, an effective trade restriction and layoffs; In Focus gave more weight to economic research and housing affordability. The default primary view narrowed the pool to roughly twenty practical-impact candidates while preserving the alternatives.

## Verification

- **115 Python tests passed**, including twenty producer-intelligence/state tests and four HTTP-boundary tests. The targeted twenty producer tests passed again after the final local-pattern precedence refinement.
- **38 JavaScript tests passed**, including six producer-view tests and the unchanged playback suite.
- Browser-tested the live desk, different product rankings, source excerpts, strategy definitions, sample-cycle advancement, a dismissed story resurfacing on a material update, persistence through a server restart, reversal of the decision, and the three-market reporting basis.
- Desktop at **1280 × 720** has no document overflow. A **390 px** mobile viewport has no horizontal overflow and uses the flowing layout. Browser warning/error logs were empty after the final checks.
- The server still serves the existing viewer and media ranges. Player code, accepted media, programme assets and source-ingestion code were not changed. Live producer decisions remain untouched by QA; the disposable sample was reset to its baseline.

## What the proof taught us

1. Broad keyword counting was not useful enough. It elevated AI model training, a political recall and a music-rights dispute as practical consumer leads. Using a bounded lead excerpt, contextual impact checks and neutral reaction/framing rules corrected those false positives. This remains inspectable curation assistance, not general semantic understanding.
2. Different product weights are necessary. Clamping scores at one hundred hid meaningful distinctions and let arbitrary IDs break ties; independent, unsaturated rankings and ordered reasons are clearer. The UI does not present a universal importance score.
3. Change and source count are different. Additional reporting can improve an opportunity without creating a new fact. Recent material flags must survive later cosmetic edits, and decisions must survive refreshes, outages and restarts.
4. Evidence must be reachable. An unexplained count of three local markets was insufficient; the producer needs the actual markets, publishers and reports. Specific configured patterns should take precedence over broader matches using the same evidence.
5. Source integrity matters during file handoffs. Mismatched reporting/candidate revisions withhold the excerpt and preserve the last coherent comparison baseline. Corrupt inputs or decision files fail closed instead of erasing the editorial record.

## Known limits to carry forward

Recommendations use rules over attributed feed titles and excerpts; they are leads for judgment, not verified factual summaries or assignments. The engine cannot reconstruct unseen historical revisions, reliably detect every subtle correction, or join every new URL into an ongoing story. Live local reporting lacks enough explicit original-reporting provenance to claim national patterns. AP/CNN are still source links pending suitable access. Source cadence retains publisher TTLs and the existing production worker's schedule.

The local store assumes **one server per checkout**. It is not a multi-user database or a remote editorial service. Strategy and the two product definitions are configured in `channel/production/producer-strategy.json` and loaded on server restart. State is ignored under `channel/production/runs/`; no credentials, local excerpts, decisions or runtime caches were committed.

## Bearing milestone preserved

The previously accepted cybersecurity segment remains delivery `a315989abeedc6ee7f60`, with the 51-word, 23.11-second Warm / 25.71-second Measured cut. Future production should preserve graphic reading time and avoid pushing the voice faster. That production milestone was not reopened.

The old `easynews-reference` repository is archival only and was not inspected or used. The new Easy News workspace is native code in this repository. Its name is not authorization to inspect the archive.

**No next development mission is active.** The next useful input is the user's assessment of the producer desk's actual editorial usefulness; that is not an instruction to keep building in the meantime.
