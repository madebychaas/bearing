# Bearing studio production

Direction chosen by the viewer: **polished news studio**. Implemented September 28, 2026.

**Current production note, September 30:** the long timings below document the initial studio format. New narration-only stories should usually remain under 45 seconds, with no long empty ident. The [September 30 PCE story](IN_FOCUS_PCE_REVIEW.md) is a complete 1080p film in two voices, with source-bound animated data graphics and continuous, measured narration. Its revised cut removes the inserted reading pause; graphics earn reading time through their placement under narration. It enters the same native playlist through `films.json`. The accepted cybersecurity cut also has its own shorter directed treatment. Neither requires rebuilding the legacy stories described below.

Each complete story is now a short programme, usually about a minute, with five timed phases:

1. A 4.5-second programme ident with a 1.5-second reveal with an original musical sting.
2. A title card and a narrated, story-specific “why it matters” sentence.
3. The sourced story, its relevant bespoke visual loop, and a sequence of supporting fact graphics.
4. A narrated closing card: the takeaway and a specific question or milestone to follow.
5. A short Up next bridge, then the following story starts automatically.

One initial Play action starts continuous playback with sound. Browser sound-autoplay restrictions can still require that first action. Pausing the player stops narration, motion, music and effects. Chapter controls and the timeline seek through the same audio clock, including backward seeking. A source update enters at the next story boundary.

The studio treatment uses slate, white and ice-blue typography, editorial rules, 1.5-second eased transitions, and story-specific imagery. It does not introduce an artificial presenter or claim that conceptual AI illustrations are event footage. Eleven existing complete stories have individual opening, narrative, closing and look-ahead copy. The underlying sourced edition and previous media remain intact.

## Sound and synchronization

Piper renders the opening, story, and closing independently for each of two voices. Exact phrase boundaries are offset into one continuous narrated MP3. Chapter times, captions and motion graphics follow that track. Speech gaps leave room for a soft transition sweep; an ending tone leads into the next ident. Music smoothly ducks while a captioned speech phrase is active and rises between passages. There are three original procedural sound effects; no third-party sound library is used. A separate Transition sounds preference turns them off. Master mute includes narration, music and effects. Reduced motion freezes the story image and removes the motion on studio cards while narration continues.

## One page, independent stories

The player is the primary experience. A source-attributed Latest desk sits alongside it on desktop and below on mobile. The playlist displays individual story thumbnails, programme titles, durations, publishers, and a Now playing state. Each entry loads its own audio and video; automatic progression swaps entries instead of hiding a compilation behind one long scrubber.

The three franchises are The Brief (fresh headline updates), In Focus (fuller stories), and Field Notes (nature and the planet). One programme selector filters the same playlist. Your mix opens with a full story, then alternates two fresh briefs with a full story when available. Briefs expire from selection at 24 hours; full stories retain their explicit dates and expiry rules. Full and brief versions of the same report are deduplicated. Existing preferences are preserved.

Both old hashes resolve to this single page. Reader updates remain staged and do not change playback. Video editions are accepted at story boundaries. The chapter rail is internal navigation within a single story, while the playlist is navigation between independent videos.

Studio entrances and exits use 1.5-second smoothstep easing, compensated for narration speed. The ident and Up next cards last 4.5 seconds, and each narrated chapter has 1.8 seconds of silence on both sides. Supporting facts also have eased 1.5-second entrances and exits. A separate 1.5-second programme transition joins videos. Reduced motion removes these movements. Original transition sounds are 1.5 seconds, at a fixed speed.

The producer reuses script- and file-hash-verified speech fragments to rebuild new immutable mixes without regenerating identical narration. Old files are retained. The media server now supports partial byte requests, suffix requests, open-ended ranges, and HEAD metadata so browser chapter seeking works after switching stories.

This preserves the quality boundary: a headline alone is insufficient to invent a “why” sentence, contextual narrative, or forecast. Look-ahead copy is framed as questions or milestones, not predicted outcomes. `production/programme-plans.json` binds each presentation to the hash of its underlying sourced script. A changed script or missing story-specific visual holds that package for review. Creating a plan for a newly eligible story is still an editorial step; there is no unattended model making up those fields.

The server runs `produce_programmes.py` after feed and headline production. It reuses hash-verified finished audio, retains earlier versions, archives editions, and atomically publishes `dist/programmes.json`. A fully held edition publishes no playable packages instead of reviving invalid stories. Prior audio is retained on disk. Production and rendering use CPU and do not interrupt other graphics services.

## Validation

49 Python checks and 16 JavaScript checks cover source changes, media bindings, invalid publication times, deduplication, programme filtering, source safety, captions, chapter padding, and byte-range delivery. All 22 re-timed narration files passed full decoding. Browser checks cover one player, individual video selection, visible intermediate transition frames, sound cue playback, independent feed refresh, chapter seeking, autoplay between stories, mute, reduced motion, desktop, mobile, and fullscreen.

Physical speaker output and the subjective quality of narration have not been listening-tested. Full-story visuals remain composed motion from bespoke illustrations, while The Brief uses original animated typography. Neither is documentary event footage.
