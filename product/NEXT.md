# Bearing — Current Mission

## Mission

Make one real **In Focus** story feel unmistakably like Bearing from beginning to end.

Broad feature development is paused.

Use the production machinery that already exists. Improve whatever most prevents the finished experience from delivering the Bearing promise:

**Open Bearing. Pick your lane. Understand what's going on. Keep going if you want.**

## The test

Choose one real sourced story and experience it as a viewer.

Do not evaluate success primarily from pipeline completion, test counts, asset generation, or implementation sophistication.

Evaluate the finished piece.

By the end, the viewer should understand:

- what happened,
- why it matters,
- how the important facts fit together,
- what remains uncertain or developing,
- and what is worth watching next.

The segment should feel like intentional programming.

The editorial test is not merely: **Does this sound like a competent news script?**

It is: **Did Bearing make this easier to understand than reading the underlying reporting myself?**

## Produced, not generated

Voice, writing, images, video, graphics, music, captions, pacing, and transitions should feel like parts of one editorial treatment.

Find and fix whatever currently makes the piece feel assembled from generated components rather than produced as a whole.

Do not assume every existing production element deserves to remain merely because it works.

## Current quality bar

### Write for the ear

- Narration-only stories should normally finish within 45 seconds, including framing. Longer cuts need a deliberate editorial reason, such as soundbites, natural sound or additional voices. Viewer-selected slower playback is separate from this authored duration budget.
- Tighten aggressively.
- Prefer shorter, cleaner sentences.
- Carry one main idea at a time.
- Remove repetition, throat-clearing, generic connective language, and lines that do not earn their runtime.
- Preserve nuance and evidence while making the spoken structure easier to follow.
- Read and listen for cadence, not just grammatical correctness.

### Treat voice quality as a product requirement

The current synthetic narration is not automatically acceptable because it functions technically.

TTS quality is a product blocker when it makes Bearing feel synthetic, distracting, flat, or difficult to listen to.

If the current Piper voices cannot reach the Bearing standard through reasonable performance, pacing, pronunciation, and mix improvements, identify a better voice path. Keep the narration layer replaceable so a stronger voice system can be adopted without redesigning the editorial pipeline.

Do not use EQ, music, or sound design to disguise a fundamentally weak voice.

### Graphics should explain

Graphics are not decoration for narration.

Produce line-specific visual scenes and reveal elements with the voice. Vary the visual form when it serves understanding: original motion graphics, tasteful relevant illustration or clearly licensed documentary media. Third-party material must have verified display permission, appear only when the script references its subject, and carry a restrained top-left courtesy credit. Keep its full attribution and license behind the story. The three-part story structure should feel intentionally showcased in one contained chapter overlay.

Each visual beat should help the viewer understand at least one of:

- a fact,
- a relationship,
- a sequence,
- a comparison,
- a change,
- scale,
- geography,
- consequence,
- or uncertainty.

Avoid generic visual filler that could accompany almost any story.

### End on the real hinge

Avoid generic "what to watch" conclusions.

The ending should land on the specific unresolved question, consequence, decision, deadline, evidence gap, or next development that genuinely determines where the story goes from here.

## Priorities

1. Watch one current In Focus story all the way through.
2. Identify the few highest-leverage weaknesses in the finished experience.
3. Improve those weaknesses using the existing architecture wherever practical.
4. Test the actual output again.
5. Repeat until the story materially improves.
6. Verify that it enters and exits the continuous playlist naturally.
7. Commit stable milestones as you go.

Consider writing, structure, voice quality, visual storytelling, asset relevance, graphics, music, pacing, transitions, context, and resolution together rather than as isolated systems.

## Protect

Preserve the strengths already present:

- one primary viewing surface,
- independent playable stories,
- continuous playback,
- explicit viewer preferences,
- source grounding,
- provenance,
- graceful failure behavior,
- accessibility,
- and the ability to inspect sources or context without turning the main experience into a dashboard.

## Avoid

For this mission:

- no broad UI redesign,
- no feature expansion for its own sake,
- no unnecessary new programme taxonomy,
- no production-console creep into the viewing experience,
- no expansion of autonomous publication before finished-story quality earns it,
- no architectural rewrite when refinement will do.

UI quality matters, but for this mission it is secondary to editorial and production quality. Make focused UI fixes when they materially improve understanding or viewing; do not divert into a broad redesign.

## Autonomy

Continue working until the milestone is materially better or a genuine blocker requires the user.

Do not stop merely because one implementation task is complete. Re-experience the finished product and decide whether the mission has actually been achieved.

## Queued next mission — do not start yet

The next major capability is the producer-facing real-time news intelligence surface described in [COVERAGE_RADAR.md](COVERAGE_RADAR.md).

It should share the same underlying news/event intelligence that ultimately feeds Bearing, while giving a national network producer a human-facing view of what deserves attention now, what materially changed, and what is emerging.

Do not begin that build until this file explicitly makes Coverage Radar the active mission.

## Astra handoff

When stopping after a meaningful milestone, update this section briefly.

**Last completed:** September 29, 2026: produced **A route into cybersecurity** after the user's rejection of the prior voice and repetitive graphics. The 66-word cut runs 31.68 seconds in Warm / Heart and 34.71 seconds in Measured / Michael, including framing. See [the editorial and viewing review](IN_FOCUS_WORKFORCE_REVIEW.md).

**Commit:** `c37be05` — Produce a concise In Focus cut with new voices and directed visuals.

**What materially improved:** A replaceable Kokoro CPU narration path with complete-sentence performance and real word timing; three distinct, voice-led scenes; a licensed Houston file photo with narration-scoped courtesy; an explicit missing-results ending; and one contained chapter overlay named The Brief / The Connection / The Test. Both voices enter the continuous playlist and advance automatically. Desktop stays scroll-less, and phone graphics clear captions. Production returned 11 ready programmes with no holds; 81 Python and 27 JavaScript tests pass. Known-good deliveries survive missing plans or failed builds, and changed compositions receive new identities. Legacy narration was retained when validating the shared renderer. Live refresh was restored after verification.

**What still feels unresolved:** The replacement voices are ready for the user's listening judgment; successful decoding and browser playback do not establish naturalness or voice preference. Physical speaker output is not independently verified. Older stories still use their prior voices and treatments. No broader publication expansion is approved by this milestone.

**Recommended next move:** Review delivery `ca2ee6187725ad6aab25` in Bearing for voice performance and whether each scene earns its screen time. Refine specific pronunciation, cadence, visual or mix problems before applying the approach to more stories. Keep Coverage Radar and broad feature development queued. Preserve both this cut and the earlier rejected treatment for comparison.
