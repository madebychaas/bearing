# Bearing

One watch-first news page: a large player, a playlist of individual stories, and a latest-news desk alongside it (below it on mobile). Every video has its own source, duration, thumbnail, and selection control. One initial Play starts continuous playback. Stories remain independently playable; they are not stitched into a multi-story compilation.

## Current mission: national assignment desk

Open **http://127.0.0.1:8796/producer.html** for current national U.S. reporting and consequential world leads. Source gathering runs independently of media production every 30 seconds, checking only due feeds and respecting publisher TTL/cache controls. The desk exposes possible today pegs, changed reporting, watch items, held sources, beat gaps and scheduled BEA releases. The 28 configured endpoints include 13 new discovery-only sources; AP/CNN and several primary beats remain explicit gaps. Read [the current sourcing record](../product/NATIONAL_ASSIGNMENT_DESK.md).

The local server and machine must remain running for collection. `--no-media` keeps gathering sources without background media generation; `--no-refresh` disables automatic gathering as well. The default continues both. No competitor latency comparison has been measured.

## Parked feature: Make my newscast

Use **Make my newscast** beside the channel controls to choose two or three stories from the current trusted domestic-source intake. Your selection order becomes the running order. Choose Warm or Measured narration, Natural or Unhurried delivery, and an editorial score or voice only. These choices apply to the personal playlist when you press Play; returning to the channel restores its prior settings.

The creation view follows real production stages and finished-story counts. Jobs survive page refresh and retain their selections if production stops. Completed films remain individual playlist items with the existing 1.5-second handoffs; the selected run ends with replay and return options. Channel arrivals cannot replace a story in that personal run.

**Current limitation:** automatic writing, visual direction and original imagery are not yet connected to a server-callable creative provider. Existing reviewed native handoffs can render; unprepared selections stop with their choices saved and a clear attention message. This is not yet an unattended, arbitrary-news-to-film service. The accepted story renderer must not be reused as a generic template for unrelated headlines.

`GET /api/newscast/catalog` exposes current source-bound choices. `POST /api/newscasts` accepts two or three `{id, revision}` objects, preferences and a UUID `requestId`. `GET /api/newscasts/{id}` restores status; `POST /api/newscasts/{id}/cancel` and `/retry` handle interruption. Requests are idempotent; changed source revisions require new selections. State stays in ignored `production/runs/newscasts/`. The server owns one worker and shares the existing production lock. Jobs interrupted by restart become explicitly interrupted, retaining completed artifacts for retry.

`production/newscast_production.py` uses the same editorial SelectionStore as the producer desk. It requires exact approved evidence/script/voice/packet lineage, produces privately with `publish_result=False`, and carries that lineage into each selected film. Delivery verifies all requested stories, both voice tracks, captions, media hashes, full decoding, expiry and current approval before offering playback. It does not write `films.json` or manufacture editorial approval. See [the active handoff](../product/NEXT.md).

## Editorial voice and script rewrites

The September 30 writing pass completed **13 source-checked drafts**, taking the existing scripts from about **106 to 60 words on average**, with a **52–68 word** range. The [rewrite book](../product/SCRIPT_REWRITES_20260930.md) retains the before/after copy, evidence, timing caveats, visual cues and specific editing lessons. The [editorial playbook](../product/EDITORIAL_VOICE.md) and [editable voice profile](production/editorial-voice.json) supply persistent guidance and selected examples to both drafting and editing in `production/scriptdesk.py`.

These examples guide style; they are not evidence for another story or model-weight training. New copy still requires editorial review, a current why-now check, rights and pronunciation checks, and newly rendered narration and media before publication. No TTS or media was generated in this pass. The accepted PCE and NIST media remain unchanged, and the new alternatives do not imply viewer approval. Estimated script runtimes are planning aids, not measured delivery durations. See [the current handoff](../product/NEXT.md).

## Programmes

- **The Brief** — fresh, attributed publisher headlines, automatically produced as short video updates. No invented contextual narration.
- **In Focus** — fuller sourced stories with an opening, why it matters, visual storytelling, takeaway, and what to watch next.
- **Field Notes** — the same full production format for nature and our changing planet.

Your mix opens with a full story and places two recent briefs between full stories where available. Topic selection and topic balancing still apply. Programme filtering narrows this same playlist; there is no second player or separate Watch/Latest page. Both old URLs open the same viewing surface. A full presentation supersedes its matching brief, so the report is not repeated twice.

## Use it

Run **Start Bearing.cmd**, then open **http://127.0.0.1:8796**. The configured local runtime keeps collecting and producing news. Space/K pauses or resumes; N/right arrow advances; left arrow restarts the current story. Preferences, source details, captions, fullscreen, music, two voices, and reduced movement remain available.

The latest desk shows reports published within 24 hours, newest first, with For you/All/topic filters. It checks completed local snapshots every 30 seconds. Reader updates wait behind an updates button; new playable editions enter at video boundaries. Refreshing the desk never resets playback. Feed polling retains publisher TTLs and existing 5–60 minute schedules, so this is continuously updating news, not event footage or guaranteed instant delivery.

## Bearing producer workspace

Open **http://127.0.0.1:8796/producer.html** on the same server for producer work. The separate workspace shares Bearing's reporting and coverage IDs. The Brief and In Focus have independent recommendations, source-linked reasons and readiness gaps; shortlist, watch, dismiss and reset are editorial decisions, not assignments or publication commands. Live feed excerpts remain in this local producer interface, behind a loopback-only API.

The server observes collected reporting every 20 seconds; the producer page polls its snapshot every 30 seconds. Source collection has its own worker and interprocess lock; it retains publisher schedules while continuing independently of production. The desk reads one coherent intake snapshot. A source check time is not a publication time or a guaranteed live update. **Sample cycle** uses clearly labeled representative inputs and separate state to demonstrate meaningful updates, cosmetic edits, syndication and local reporting signals without mixing them into live news.

Configuration lives in `production/producer-strategy.json`. Editorial history and decisions persist locally under the ignored `production/runs/` directory. Run one local server per checkout to keep one writer for that state. See [the V1 guide](../product/EASY_NEWS_V1.md) for the proof, limits and operation. The Bearing player and accepted story segment remain independent of these controls.

**Prepare** opens the selected-story review in the same desk. Choose a treatment and record why now; review and save the cited script and prepared picture/sound plan; approve, hold or reject with a named reviewer. Approved live In Focus work can produce a finished **preview**, without playlist publication. The source/approval guard blocks changed or stale work, including during rendering. Primary evidence requires an explicit source reread within the last hour, and the guard cannot observe uncollected remote-page edits. Supplemental primary evidence and story-specific film preparation currently use `/api/producer/handoff`; they are not a generalized planning UI. See the [checkpoint, API actions, proof and remaining real-story approval](../product/SELECTION_PROOF_20260930.md).

## Production feel

The September 30 **Inflation erased the income gain** story is a complete, individually playable 1080p film: 58 words, 26.867 seconds Warm or 30.500 seconds Measured at Natural pace. Original data graphics reveal in reading order at narration cues, with 1.5-second scene blends and no inserted reading pause. The revised score uses a brief dry accent and sparse accompaniment; narration stays at full gain from its first word. The accepted cybersecurity segment keeps its prior production. [The new story review](../product/IN_FOCUS_PCE_REVIEW.md) documents the decisions and evidence.

Earlier studio graphics ease in and out over **1.5 seconds of viewing time**, including at the chosen narration speed. Those legacy opening and closing idents last 4.5 seconds, while narration has 1.8 seconds of lead and tail space per chapter. These longer timings are historical treatments, not the standard for new narration-only stories. A 1.5-second branded transition separates playlist entries. Sound cues are optional, music ducks under speech, and master mute covers all audio. Reduced movement removes transitions and freezes legacy illustrations; finished films step between their narrated graphic states.

All eleven complete studio stories were re-timed in both voices. Verified speech fragments were reused and remixed; previous media and editions remain intact. The local server supports byte-range delivery for MP3, MP4, and WAV, making chapter seeking reliable. See `../product/STUDIO_PRODUCTION.md` for the detailed format and verification.

## Deliberate automation boundary

Automatic briefs use a complete, attributed excerpt from an approved agency feed. They do not use an LLM to invent missing context. Incomplete excerpts (including ellipses), missing or unsuitable dates, unfamiliar hosts, identified sensitive subjects, and publishers without an approved narration policy are held for review. These checks reduce failure modes; they are not independent fact verification or a guarantee that a publisher is correct. Independent reporting remains available as attributed links in More reporting while narration requires source review and appropriate reuse rights.

Every full story requires bespoke artwork; there is no shared topic-image fallback. Source collection and the article library keep updating automatically. Eligible full-story candidates without a reviewed, script-matched image and video are recorded in `production/runs/visual-requests.json` before any speech work. Images are generated with the built-in image-generation tool and visually inspected, then installed using `production/install_visuals.py --manifest <manifest.json>`. This explicit art step is not an unattended generation service. Once approved visuals are registered, eligible source briefs can complete the normal automatic narration and publication path.

The Brief has a separate, fully local headline playback lane in `production/latest_video.py`. It uses only attributed title metadata, without article excerpts or generated factual elaboration. A custom graphic contains that exact headline, source, topic, and original publication time. Restrained motion and embedded speech make a complete video. It targets 32 recent clips across interests, attempts up to eight new or changed clips per scheduler cycle, and reuses hash-verified output. Both video/audio tracks must decode before atomic publication. Headline revisions get new immutable media; unavailable revisions and clips older than 24 hours leave the edition instead of being replayed as current. Prior files and editions are retained. This is a local personal headline readout, not a grant of commercial narration or syndication rights; existing source policies and full-story review gates remain intact.

New art uses one clear subject, generous negative space, and a restrained palette. Motion is a seamless 12-second, 2% cosine zoom composed on the CPU; the Less movement preference freezes it. Illustrations are conceptual, not documentary evidence. Original prompts, story/script bindings, file hashes, and visual-review notes are retained in `production/visuals.json`. Prior assets and editions remain on disk. Music is original AI-composed, algorithmically synthesized audio. Neural narration runs locally with Piper and ONNX Runtime on two CPU threads.

Each complete segment must pass media decoding, duration, script-hash, audio-hash, caption text, caption timing, source, date, and bespoke-visual checks. Image/video hashes and story/script bindings must match, and different stories cannot share an image in one edition. A new edition replaces the current one atomically only after validation. Failed runs retain the last complete edition. Parallel producer runs are locked out. Prior editions and run reports are retained locally.

Changed feed text withdraws its matching automatic segment from the next rotation until reviewed. It does not interrupt the current segment. This detects changes to feed titles/descriptions, not every correction to a full article. Published URLs remain indexed after leaving the rotation so they are not repeatedly produced. New automatic segments expire seven days after the source date; reviewed additions carry explicit expiry dates. Legacy illustrated launch stories retain their visible dates.

Topics are Space, Nature, Culture, World, Technology, Business, Health, Sport, and optional North Texas. Existing preferences are preserved; select new topics in Tune your channel. All nine interests are eligible for the headline video lane when recent reports exist. For longer In Focus and Field Notes summaries, NASA, NOAA, NIST, and USGS are eligible for the restricted automatic path; all other feeds require review. Government and institutional sources are not substitutes for independent reporting.

`production/sources.json` records each source's publisher group, topic, polling interval, approved hosts, narration policy, and policy reference. Do not infer reuse permission from a successful feed fetch. The local reader is not a cleared commercial syndication service. See the workspace's `product/SOURCES_AND_LIVE_UPDATES.md` for the live-update assessment and remaining coverage gaps.

## Operate production

Use the Python executable and model directory recorded in `production/runtime.json`:

```text
python production/pipeline.py collect
python production/pipeline.py auto --limit 2
python production/latest_video.py --limit 8
python production/produce_programmes.py
python production/pipeline.py check
python production/produce_reviewed.py --input production/reviewed-additions-20260928.json
python production/produce_film.py --input production/reviewed-pce-20260930.json
python -m unittest discover -s tests -v
node --test tests/*.test.mjs
```

`auto` requires `CURRENT_PIPER_MODEL_DIR` pointing to the downloaded model directory. The launcher supplies that setting. No narration text leaves the computer.

For another machine, create a virtual environment, install `production/requirements.txt`, and download the model/config pairs named in `production/speech.py` from the linked official model cards. Create `production/runtime.json` with `python`, `modelDir`, and `ffmpeg` absolute paths. No model files or machine-specific paths are required by the hosted viewer.

## Source and production records

- `production/edition-source.json`: original sourced scripts and editorial distinctions.
- `production/editorial-voice.json`: editable voice principles, word budget, editing pass and selected style examples supplied to the native draft/edit desk.
- `production/editorial-rewrites-20260930.json`: thirteen versioned writing alternatives with source checks, timing status and visual cues; not live playlist or approved production plans.
- `production/art-provenance.json`: exact image-generation prompts and artifact lineage.
- `production/visuals.json`: active bespoke visual registry, prompts, review notes, story/script bindings, and media hashes.
- `production/runs/visual-requests.json`: eligible source candidates waiting for bespoke art; these have not been published as video segments.
- `production/media-provenance.json`: media hashes, model identities, and rendering records.
- `production/runs/`: retained intake results, production reports, and previous editions (not published).
- `production/runs/feed-cache.json`: conditional-request metadata, retry deadlines, and retained feed entries.
- `production/runs/intake-version.json`: the last archived intake fingerprint; minute scheduling does not create duplicate full intake archives when source content and availability are unchanged.
- `production/runs/published-index.json`: URLs already produced, including segments no longer in rotation.
- `dist/reporting.json` and `dist/source-status.json`: source links and source availability for the viewer; raw excerpts stay in local production records.
- `dist/edition.json`: the complete illustrated Watch edition.
- `dist/programmes.json`: source-bound complete studio programmes, narration, chapters, opening/closing copy and visual beats; consumed by Watch and Latest's produced-story mode.
- `dist/films.json`: reviewed finished-film deliveries merged into the same viewer playlist, with a complete MP4 and clean narration for each voice. This is delivery inventory, not an additional source collection system.
- `production/reviewed-pce-20260930.json`: the September 30 source-bound script, accuracy review, visual direction, exact data and current-news expiry.
- `production/produce_film.py`, `film_visuals.py` and `film_audio.py`: assemble a reviewed complete film with original cue-aligned graphics, a per-story narration pace, guarded quiet-gap editing and an original dry score. Uses the existing production lock, editorial gates and speech provider. Failed production preserves the published edition; new deliveries use immutable paths.
- `production/programme-plans.json`: individual editorial presentation plans, each bound to its underlying sourced script.
- `dist/latest-edition.json`: the complete headline-video edition, with source times, captions and media hashes.
- `production/runs/latest-video/`: per-revision narration provenance and completed segment records.
- `production/runs/latest-video-status.json`: latest production counts and held render errors.

Piper engine source and model cards are recorded in `production/speech.py` and media provenance. Models run locally; they are not bundled into the Site.

The reviewed cybersecurity In Focus story now selects `kokoro-local-cpu` explicitly. Install the pinned `production/requirements.txt` into the existing CPU production environment. Obtain `kokoro-v1.0.onnx` (with duration outputs) and `voices-v1.0.bin` from the [Kokoro ONNX documented model release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1), then set `BEARING_KOKORO_MODEL_DIR` to their local directory. A `kokoro-models` folder beside the configured `piper-models` folder is also recognized. Model and voice weights are Apache-2.0; the adapter is MIT. Models stay in the ignored runtime, and every delivery records hashes and license references. No model downloads or script uploads occur implicitly at narration time, and unavailable Kokoro does not silently fall back to Piper.

This story's 51-word cut runs 23.11 seconds in Warm / Heart or 25.71 seconds in Measured / Michael, including framing. Voice-led typography, a credited map of award states, a training/employer diagram and a resolved closing replace the earlier footage and Houston detour. An original signature overlaps the lead, with ducked music and a sustained playlist handoff. The contained chapter overlay reads The Shift / The Design / The Payoff. This September 18 announcement is labeled a context example; new or changed scripts need a reviewed reason to run now. See [the current story review](../product/IN_FOCUS_WORKFORCE_REVIEW.md) for rights, timing and verification.

## Verification

The earlier illustrated-channel revision passed 30 Python checks, three rotation checks, full media decoding of all 11 stories, and browser playback of every distinct visual. The Latest revision adds precise-time, date-only exclusion, polling TTL, source revision, retained-outage, and recent-news selection checks. Browser QA covers desktop and mobile, time and interest filters, retained Watch playback, pausing when leaving Watch, staged report updates, and connection failures. Source checks and visual-art holds remain active in the local worker.

Physical speaker output and TV/remote-control hardware have not been tested. The sound and editorial pacing still benefit from the viewer's listening judgment.

## U.S. selection and full-story production

The default playlist now prioritizes domestic consumer/economic impact and consequential policy. AP/CNN remain source links pending licensed access. Official USGS/NASA camera tiles remain separate from the playlist. See ../product/US_EDITORIAL_AND_CAMERAS.md for sources and reuse boundaries.

Camera tiles use the official YouTube IFrame API, an explicit page origin and muted startup. They report playback only after a provider playing event, expose retry/source controls on failures, and destroy the external player when closed or when returning to news. Both configured cameras were verified playing in Chrome on September 29, 2026. The Codex in-app browser still left the cross-origin YouTube frames blank in that check; use Bearing in Chrome or the tile's source link when this occurs. No video extraction or restreaming is involved. Player events follow the [official IFrame API](https://developers.google.com/youtube/iframe_api_reference).

The nine-stage production records, automation boundaries and verification are documented in ../product/BROADCAST_PIPELINE.md. Run `python production/produce_programmes.py` to assemble reviewed plans under the production lock. The scheduler also invokes it. New scripts and bespoke artwork remain review-gated; headline clips are a separate format. Each complete programme includes its own original procedural music beds.

## Desktop home screen

At viewports at least 960 px wide and 650 px high, the desktop shell fits one viewport. Latest reports use page buttons; the playlist has browse arrows; Cameras and Sources share a tabbed side panel. Expanded details can scroll within that panel. Smaller or heavily zoomed windows retain the flowing layout for accessibility. The player renderer, internal styles and motion remain unchanged.

## Reference-inspired editorial improvements

See ../product/EASYNEWS_REFERENCE_ADAPTATION.md for the pinned EasyNews reference review and native implementation map. The collector now groups conservative duplicate coverage, records ranking dimensions and prepares source-bound script packets. Optional local-model drafting has a separate edit pass and always stops for editorial review. The viewer keeps one entry per coverage group and exposes the other sources behind the story.

## Bearing branding and repository

Private repository: https://github.com/madebychaas/bearing. The product was renamed from current. to Bearing without changing the player design or playback behavior. Existing `CURRENT_*` environment variables and the `current.preferences.v1` browser storage key remain compatibility identifiers. Historical media prompts and provenance retain their original wording. See the root README for repository exclusions and the one-story production milestone.

The old `easynews-reference` repository is archival only; do not inspect or use it unless explicitly asked to compare against EasyNews. The new Easy News producer workspace is native code in this repository and follows the current product direction.
