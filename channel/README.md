# Bearing

One watch-first news page: a large player, a playlist of individual stories, and a latest-news desk alongside it (below it on mobile). Every video has its own source, duration, thumbnail, and selection control. One initial Play starts continuous playback. Stories remain independently playable; they are not stitched into a multi-story compilation.

## Programmes

- **The Brief** — fresh, attributed publisher headlines, automatically produced as short video updates. No invented contextual narration.
- **In Focus** — fuller sourced stories with an opening, why it matters, visual storytelling, takeaway, and what to watch next.
- **Field Notes** — the same full production format for nature and our changing planet.

Your mix opens with a full story and places two recent briefs between full stories where available. Topic selection and topic balancing still apply. Programme filtering narrows this same playlist; there is no second player or separate Watch/Latest page. Both old URLs open the same viewing surface. A full presentation supersedes its matching brief, so the report is not repeated twice.

## Use it

Run **Start Bearing.cmd**, then open **http://127.0.0.1:8796**. The configured local runtime keeps collecting and producing news. Space/K pauses or resumes; N/right arrow advances; left arrow restarts the current story. Preferences, source details, captions, fullscreen, music, two voices, and reduced movement remain available.

The latest desk shows reports published within 24 hours, newest first, with For you/All/topic filters. It checks completed local snapshots every 30 seconds. Reader updates wait behind an updates button; new playable editions enter at video boundaries. Refreshing the desk never resets playback. Feed polling retains publisher TTLs and existing 5–60 minute schedules, so this is continuously updating news, not event footage or guaranteed instant delivery.

## Production feel

Studio graphics ease in and out over **1.5 seconds of viewing time**, including at the chosen narration speed. Opening and closing idents last 4.5 seconds, while narration has 1.8 seconds of lead and tail space per chapter. Supporting facts fade smoothly at their own boundaries. A 1.5-second branded transition separates playlist entries. Sound cues are optional, music ducks under speech, and master mute covers all audio. Reduced movement removes transitions and freezes the illustration.

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
python -m unittest discover -s tests -v
node --test tests/*.test.mjs
```

`auto` requires `CURRENT_PIPER_MODEL_DIR` pointing to the downloaded model directory. The launcher supplies that setting. No narration text leaves the computer.

For another machine, create a virtual environment, install `production/requirements.txt`, and download the model/config pairs named in `production/speech.py` from the linked official model cards. Create `production/runtime.json` with `python`, `modelDir`, and `ffmpeg` absolute paths. No model files or machine-specific paths are required by the hosted viewer.

## Source and production records

- `production/edition-source.json`: original sourced scripts and editorial distinctions.
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
- `production/programme-plans.json`: individual editorial presentation plans, each bound to its underlying sourced script.
- `dist/latest-edition.json`: the complete headline-video edition, with source times, captions and media hashes.
- `production/runs/latest-video/`: per-revision narration provenance and completed segment records.
- `production/runs/latest-video-status.json`: latest production counts and held render errors.

Piper engine source and model cards are recorded in `production/speech.py` and media provenance. Models run locally; they are not bundled into the Site.

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

EasyNews material is archival only; do not inspect or use it unless explicitly asked to compare against EasyNews.
