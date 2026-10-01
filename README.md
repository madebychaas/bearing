# Bearing

A calm, watch-first news experience: individual produced stories, a continuous playlist, and a latest-news feed. The editorial focus is practical U.S. consumer, economic and consequential policy news.

The application lives in [`channel/`](channel/README.md). Run **`channel/Start Bearing.cmd`** on the configured Windows machine. Open **http://127.0.0.1:8796/** to watch Bearing or **http://127.0.0.1:8796/producer.html** for the **Easy News** producer workspace. See the application README for Python, Piper models, FFmpeg and runtime setup on another machine.

## Milestone status

The [selection-to-production proof](product/SELECTION_TO_PRODUCTION.md) is complete: a producer-selected student-loan story carries its evidence, editorial context and exact approval through two finished films and into the local playlist. **Default help moves online** runs 36.9 seconds in Warm and 40.3 seconds in Measured, with original animated graphics, music, effects and captions. Changed reporting blocks stale completion; explicit reassessment preserves discovery history when a report rotates out of intake. See the [finished production review](product/STUDENT_LOAN_PRODUCTION_20261001.md).

The first October 1 picture revision gave this segment the full video canvas: staged centered typography, larger voice-timed explanations and purposeful cuts, with no persistent template labels. Playback controls recede during viewing. That delivery and its exact script and audio remain archived.

The [image-led follow-up](channel/production/reviewed-student-loans-20261001-picture-v3.json) is delivered in the local playlist. It starts more slowly on an original generated editorial image, assembling one title during the first sentence, then cuts to a separate image when the body begins. Three process columns accumulate and hold together, with the requirements extending that same explanation. The close explains default through month pages, a credit report and everyday borrowing or housing consequences. The exact script, narration, captions, timing, music and mix are preserved and verified. Both movies decode, and actual playback advanced into the next item. This is a focused production revision, with no broad product redesign. The [production review](product/STUDENT_LOAN_PRODUCTION_20261001.md) includes validation and the unrelated existing Windows HTTP test limitation.

The viewer accepted the October 1 loan film as Bearing's **production approach reference**: tight, dynamic storytelling, with purposeful movement and enough hold time for understanding. Future stories should carry forward that judgment rather than repeat a fixed image-and-graphics template. The delivered film remains intact.

The September 30 editorial pass rewrote **13 existing scripts**, reducing average length from about **106 to 60 words**; the drafts range from **52 to 68 words**. The [rewrite book](product/SCRIPT_REWRITES_20260930.md) preserves source checks, before/after copy and the lessons from each edit. The [voice playbook](product/EDITORIAL_VOICE.md) and [editable profile with selected examples](channel/production/editorial-voice.json) now guide both native drafting and editing. This is maintained editorial guidance, not model-weight training. The drafts need fresh editorial review and a new rendered delivery before publication; they are not all viewer-approved, and no TTS or media was generated in this pass. Accepted PCE and NIST media remain untouched. See [the current handoff](product/NEXT.md).

The previous production milestone remains available:

The first story-quality milestone was accepted on September 29, 2026. The accepted cybersecurity cut remains intact. On September 30, the user requested a major domestic story produced through the same complete path. **Inflation erased the income gain** uses that morning's BEA release, a 58-word script, flowing measured narration, original animated explanatory graphics and a complete scored 1080p movie for each voice. See [the story review](product/IN_FOCUS_PCE_REVIEW.md) for source evidence, rights, pacing and delivery details, and [the handoff](product/NEXT.md) for verification.

Easy News adds an editorial view over the same source intake and event IDs: separate immediate-awareness and deeper-treatment recommendations, source inspection, change history, and reversible producer decisions. Its sample news cycle is explicitly separated from live reporting. Recommendations do not assign, generate or publish stories. See [the V1 guide](product/EASY_NEWS_V1.md) and [current handoff](product/NEXT.md).

## Repository

Private repository: [madebychaas/bearing](https://github.com/madebychaas/bearing). The root package manifest supplies project metadata and the JavaScript test command; this is a native browser application with a Python production service, not an npm build pipeline.

- `channel/dist/`: browser application and reviewed programme assets.
- `channel/production/`: sourcing, editorial records, script preparation, media production and local server.
- `channel/tests/`: existing Python and JavaScript verification.
- `product/`: product and production documentation, including dated historical decisions.
- `visual-concepts/`: earlier exploratory concepts, not the application.

Local model environments, machine-specific `runtime.json`, production run archives, credentials, browser evidence, and downloaded reference material are excluded from Git. Continuously refreshed reporting, source status, headline editions and headline assets are also excluded; the local collector/producer rebuilds them. Reviewed full-story snapshots and their assets are included. Running production can update those snapshots after checkout.

## Branding and compatibility

The product is **Bearing**, formerly **current.** The rename changes display copy and metadata, not playback logic or layout. `CURRENT_*` environment variables, the `current.preferences.v1` storage key, internal CSS selectors and existing local folder names remain compatible to preserve configuration and viewer preferences. Historical generation prompts and media provenance retain their original wording.

The old `easynews-reference` repository is archival reference only. Do not inspect or use it unless the user explicitly requests a comparison against EasyNews. It is not a runtime, import or repository dependency. The new **Easy News** producer workspace is implemented natively here, following [the current product direction](product/EASY_NEWS_DIRECTION.md); its name does not authorize using the archive.

## Verification

Run `npm test` for JavaScript checks. From `channel/`, use the configured Python environment to run `python -m unittest discover -s tests -v`. The full Python suite also checks local production archives: on a fresh checkout, configure the runtime and run `python production/produce_programmes.py` first. Production setup and media requirements are in the [application README](channel/README.md).
