# Bearing: EasyNews independence audit and change inventory

Verified locally on September 29, 2026.

## Finding

No runtime, import, package, or Git repository dependency on `madebychaas/easynews-reference` was found in Bearing. The reference informed native implementations; it is not required to run Bearing.

The inspection snapshot remains at `output/easynews-reference-451b491/`, outside `channel`. It is an ordinary directory, not a link. Documentation mentions and the snapshot are retained for provenance. The configured static publishing directory is `channel/dist`, so the snapshot is outside that publication root.

## Verification performed

- Searched Bearing production code, browser code, launcher and configuration for EasyNews names, old paths and reference identifiers. No executable dependency was found; references were confined to documentation and the inspection snapshot.
- Imported all 13 production Python modules and checked their resolved locations. They resolve to Bearing's own production directory.
- Resolved all 12 browser ES-module import references. All targets exist within Bearing's `dist` directory.
- Inspected requirements, runtime configuration, startup scripts and worker commands. Bearing uses its own Python environment, Piper/ONNX, FFmpeg, media records and native worker scripts. The optional script provider is a separately configured loopback model endpoint.
- Inspected Git configuration, index and metadata directly: no remotes, `.gitmodules`, indexed gitlinks, object alternates or reference-repository include directives. This local workspace currently has no tracked files or remote configured. `git submodule status` could not run because Git shell helpers were unavailable; the direct metadata checks supplied the repository evidence instead.
- Ran `output/dependency-audit/verify_independence.py` with a Python audit hook rejecting EasyNews-named paths before importing Bearing. All 13 imports, eight HTTP routes through Bearing's actual server handler, and 69 Python tests passed. There were zero reference-access attempts.
- Ran the JavaScript suite: 19 tests passed. Total: 88 tests.

Machine-readable evidence: `output/dependency-audit/result.json`.

The eight routes were `/`, `/app.js`, `/desktop.js`, `/programmes.json`, `/latest-edition.json`, `/reporting.json`, `/cameras.json` and `/api/production`. They returned HTTP 200 from an ephemeral server using Bearing's handler.

## Exact reference-inspired implementation changes

| File | Change |
|---|---|
| `channel/production/coverage.py` — new | Conservative event grouping from similar headlines within 36 hours; canonical source URLs; retained source links; stable event identities; grouping reasons. Different figures, opposing actions and older reports remain separate. |
| `channel/production/editorial.py` | Exposed named components of existing editorial scores, added multi-story roundup suppression, and selected one entry per coverage group before existing source-diversity constraints. Version changed to `us-impact-v2`. Existing U.S./consumer/policy priorities were retained. |
| `channel/production/scriptdesk.py` — new | Immutable evidence packets for up to 24 ranked events; original Bearing script schema and voice instructions; optional local-model draft and edit calls; supporting excerpts and evidence IDs; numeric/structural checks; retained attempts and failures. Generated scripts remain `needs-editor-review`. Also creates structured production briefs for existing reviewed programmes. |
| `channel/production/pipeline.py` | Integrated native event grouping, coverage audit/counts, coverage/editorial metadata in edition fingerprints, and automatic evidence-packet preparation. |
| `channel/production/latest_video.py` | Propagated coverage metadata through cached and newly rendered headline entries and edition versions. |
| `channel/production/produce_programmes.py` | Added retained `editorial-brief-<hash>.json` sidecars for reviewed programmes, including when media is cached; propagated coverage metadata into programme editions. |
| `channel/dist/editorial.js` | Collapsed a coverage group to one playable entry, preferring a complete programme over a brief. Preserved topic filtering and existing domestic/diversity priorities. |
| `channel/dist/live-news.js` | Recognized changes to coverage or editorial metadata as edition updates. |
| `channel/dist/app.js` | Preloaded the next selected narration track's metadata; made Next advance the loaded queue without waiting for refresh; skipped failed audio to another eligible story; displayed grouped related-source links with an explicit distinction between similarity and independent confirmation. |
| `channel/tests/test_reference_adaptation.py` — new | Added 12 tests for grouping boundaries, stable identities, roundups, evidence-bound drafts, invented numbers/excerpts, visual evidence, model failure, two-pass records and loopback-only providers. |
| `channel/tests/editorial.test.mjs` | Added a test that a full programme is preferred over a brief from the same coverage group. |
| `product/EASYNEWS_REFERENCE_ADAPTATION.md` — new | Documented reference ideas, native adaptations, deliberate differences, operation and validation limits. |
| `channel/README.md` | Linked the adaptation documentation. |

Generated records accompanying these changes: 24 queued evidence packets, 11 reviewed-programme editorial briefs, and refreshed coverage/editorial metadata in reporting, latest-edition and programme JSON. Existing editions and media were retained.

The briefs specify opening/story/closing copy, estimated duration, evidence hashes, per-beat visual directions, asset bindings and audio direction. They do not themselves generate new images, videos, narration or music.

## Preserved behavior and scope limits

Player styling, studio graphics, 1.5-second transitions, scroll-less desktop layout, narration-driven timing, story-boundary edition changes, existing voices/music/media, U.S. feeds, AP/CNN source links and camera tiles predate this adaptation and were preserved. The nine-stage production journal was already present.

No legacy server, frontend, database, API integration, prompts, ranking weights or hardcoded event families were introduced. The reference's concepts were implemented in Bearing's own modules.

This is a local audit, not verification of a deployed GitHub checkout. There is no committed baseline here for a mechanical before/after diff; the inventory records the adaptation's edits and inspected current files. The reference-path guard covers the audited Python process, not every potential future subprocess or optional service. No live model call or fresh media generation was run in this audit. Draft validation is not independent factual verification, and model-generated scripts still require editorial review.

Files added by this audit itself: this document, `output/dependency-audit/verify_independence.py` and `output/dependency-audit/result.json`. No application behavior was changed during the audit.
