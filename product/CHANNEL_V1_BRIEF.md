# Future of Newz — working channel brief

Updated: 2026-09-28. The agreed direction has been implemented as Bearing v1 in `channel/`.

## Confirmed direction

Create an original, modern news viewing experience for a broad audience. The intended benefit is a less stressful way to stay informed, with meaningful customization.

The primary experience is a continuous video loop of stories selected from the viewer's explicit preferences. Images, video, graphics, and voice tracks are produced with AI. EasyNews is a reference for useful behavior, not a design or code template to reproduce.

## Reference findings

- Local reference: `C:\easynews`.
- GitHub reference: https://github.com/AngeloTobo/EasyNews, main at `5102c20b8a0347afde41b4ef0ff90b28f65e3069` when inspected.
- The reference separates a producer control panel from a broadcast overlay. It uses RSS stories, synthesized narration, source labels, and automatic story advancement after narration finishes.
- The useful ideas are low-effort playback, narration-led pacing, configurable sources, and voice choice.
- The new experience should put viewer preferences and the story itself first. Complete visual story segments should carry the experience; production settings should not dominate viewing.
- The GitHub README describes an earlier implementation. Current source also contains optional article extraction, clustering, and narration rewriting. These are code observations, not proof that the local integrations are working.

## Proposed experience

1. Choose interests and a small number of presentation preferences.
2. Start a personal channel with a deliberate first click to enable sound.
3. Watch one coherent story at a time. Narration, captions, imagery, and graphics share a timeline.
4. Pause, skip, adjust sound, or change preferences without losing the current position unnecessarily.
5. Open the source and context for a story when wanted; return easily to playback.

Preference changes should affect the next eligible story without abruptly interrupting narration. The system should explain why a story was selected in plain language, based on the viewer's choices.

## Design principles

- Give the moving story the largest share of attention. Keep controls quiet and reveal detail on demand.
- Use calm, direct language and measured transitions. Avoid urgent visual treatment by default.
- Keep serious facts intact. The viewer's chosen content boundaries and the presentation style are separate decisions.
- Use explicit preferences for the first version. Do not invent a hidden engagement-based personalization system.
- Treat the generated visuals as illustrations or explanations. Label them clearly; do not present synthetic scenes as eyewitness footage.
- Tie factual narration and graphic values to identifiable reporting or primary sources. Visual generation is not a source of facts.
- Show the story's actual date and update time. A playing loop is not automatically a live report.
- Provide readable captions, keyboard access, and reduced-motion behavior as part of the player.

## Media production shape

Source material → supported story facts → narration and storyboard → AI media production → synchronized segment → eligible channel queue.

Generate a reusable segment for a story, then personalize selection and sequence. Whether production is a reviewed pilot, an ongoing reviewed pipeline, or an automatically published pipeline remains open.

Each segment needs its own source references, script, captions, media provenance, duration, and production status. Only complete, playable segments belong in the viewing queue. Generation progress and failures belong outside the viewing experience.

## Settled v1 choices

1. Calm pace, music, and delivery selected by the viewer.
2. Widescreen desktop/TV first, with a usable responsive phone layout.
3. Automate as far as quality allows. Bearing produces bounded, attributed agency-source briefs automatically and retains incomplete or more sensitive items for review.

Bearing uses original generated artwork, CPU-composed motion, original synthesized music, and local Piper neural narration. Source intake and production run locally while the server is active, with no external script upload or GPU-service changes. See `channel/README.md` for the implemented operating boundary and verification.

## Evidence required before calling it v1

- Actual playable segments with working AI-produced audio and visuals; placeholders do not demonstrate the requested experience.
- Preferences demonstrably change which eligible stories play.
- Playback advances cleanly without overlapping narration; pause, resume, and skip work.
- Captions follow the narration and remain readable in the selected primary format.
- Source links, generation labels, and story dates are accessible during viewing.
- Empty selections, unavailable media, and stale content have understandable behavior.
- Verify the supported desktop/mobile layouts and keyboard interactions. Report TV-device or physical-audio checks separately if they have not been tested.
