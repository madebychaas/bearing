# EasyNews reference adaptation

Reference: https://github.com/madebychaas/easynews-reference/tree/451b4919f7e337b05c5cba6dde5727d51b63ca6c
Reviewed September 29, 2026. The downloaded source is kept only under output/easynews-reference-451b491 for inspection; Bearing does not import or execute it. No legacy database, server, frontend, ranking weights, prompts or hardcoded event families were copied into Bearing.

| Area | Useful reference idea | Native Bearing implementation |
|---|---|---|
| Curation | Cluster coverage of an event; rank by practical audience impact; explain the result | production/coverage.py groups high-confidence headline matches within 36 hours and keeps every source URL. Opposing actions, different numeric figures, and old reports stay separate. Editorial rules now expose score dimensions and exclude multi-story roundups from single-story video selection. |
| Scripts | Structured spoken copy, supporting context, pronunciation notes, edit pass | production/scriptdesk.py creates immutable evidence packets and an original local-model drafting/editing workflow. Each sentence carries source IDs and exact supporting excerpts; figures must occur in those excerpts. All generated output remains needs-editor-review. |
| Media | Plan graphics and video according to the narrative | Reviewed programmes gain an editorial brief with opening/body/closing blocks, runtime estimates, per-beat shot instructions, asset bindings and explicit restrictions on charts, maps and documentary-looking generated imagery. Existing visuals, voice and music remain intact. |
| Playlist | One canonical event per rundown, with source lists | The native selector collapses a coverage group to one entry, preferring a complete programme when available; other source links are available behind the story. Topic filters, domestic source priority and freshness limits still apply. |
| Playback | Continuously cycle through independent stories and refresh editions | Bearing keeps narration-driven timing and stages arrivals at story boundaries. Next no longer waits for a network refresh. Metadata for the next selected voice track is preloaded; failed media can advance to another ready story. |

## Deliberate differences

The reference handoff identifies weak title-based deduplication and hardcoded story families. Bearing uses cautious generic matching with an audit trail, not those event-specific rules. Similarity and multiple publisher labels are not described as independent confirmation. A new number, contradictory action or weak match stays separate for review; some duplicates will intentionally remain.

The reference broadcast page advances on estimated runtime and resets its playlist after fetching. Bearing continues to use actual narration completion, preserves the last playable edition through outages, and keeps the existing 1.5-second transitions. The player renderer and visual styling, including the one-screen desktop shell, were not changed by this adaptation.

The reference deterministic script fallback can produce generic context. Bearing instead records missing evidence and holds drafts. A schema pass and source-excerpt match do not establish factual accuracy, rights, independent sourcing or suitable voice quality.

## Operating the native script desk

The normal collector automatically writes up to 24 ranked evidence packets to channel/production/runs/script-desk/<sourceRevision>/evidence.json and a script-desk-queue.json index. Old evidence and attempts are retained. Eleven existing reviewed programmes receive editorial-brief files alongside their existing media records.

To explicitly draft against an already available local model, from channel with the configured Python environment:

    python production/scriptdesk.py --generate SOURCE_REVISION --model RESIDENT_MODEL --url http://127.0.0.1:1234/v1

CURRENT_SCRIPT_MODEL and CURRENT_SCRIPT_URL may supply defaults; CURRENT_SCRIPT_TOKEN is optional and remains server-side. The adapter accepts loopback endpoints only, disallows redirects, applies a request timeout and response-size bound, and does not install or load a model. Draft and edit are separate calls. This command does not approve or publish a story. Review source support, attribution, rights, uncertainty, names/pronunciation and visual requirements before creating a reviewed Bearing story and presentation plan through the existing production path.

No resident model was configured or invoked during this change. Live automated model quality is therefore unverified; adapter orchestration was tested with fixtures. No new claim is made that fresh reporting is autonomously ready for air.

## Validation

69 Python tests and 19 JavaScript tests pass. Added checks cover distinct events, opposing actions, changed figures, stale coverage, identity preservation after a group splits, source-bound drafts, invented numbers and excerpts, unsupported media references, model failure, two-pass draft recording and restricted provider destinations. The active collector produced 24 script packets and 11 reviewed editorial briefs. Browser checks verified related-source links, media-error recovery, and a 1366 by 768 desktop without page scrolling.
