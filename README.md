# Bearing

A calm, watch-first news experience: individual produced stories, a continuous playlist, and a latest-news feed. The editorial focus is practical U.S. consumer, economic and consequential policy news.

The application lives in [`channel/`](channel/README.md). Run **`channel/Start Bearing.cmd`** on the configured Windows machine. Open **http://127.0.0.1:8796/** to watch Bearing or **http://127.0.0.1:8796/producer.html** for the **Easy News** producer workspace. See the application README for Python, Piper models, FFmpeg and runtime setup on another machine.

## Milestone status

The one-story quality milestone is complete and was accepted by the user on September 29, 2026: a sourced script, narration, story-specific graphics, audio treatment, assembly, playlist entry and automatic playback into the next item. The accepted cybersecurity cut remains intact. Carry-forward feedback: the voice is slightly too fast and the graphics need enough time to land. See [the handoff](product/NEXT.md) for the accepted delivery and stop boundary.

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
