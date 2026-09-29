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

**Last completed:** September 29, 2026: watched and refined the existing In Focus story, now titled **Cybersecurity training. A route to work?**, through rendered narration, explanatory graphics, music and automatic playback into the next story. Warm delivery: 80.98 seconds; measured: 91.77 seconds. See [the editorial and viewing review](IN_FOCUS_WORKFORCE_REVIEW.md).

**Commit:** `6070d61` — Produce a source-grounded cybersecurity In Focus treatment.

**What materially improved:** Less repetition, a verified University of Houston example, a clear distinction between funding and outcomes, four graphics bound to each voice's actual narration cues, quieter internal transitions and readable phone graphics above captions. Existing player, preferences and continuous playlist remain intact. Production returned 11 ready programmes with no holds; 73 Python and 24 JavaScript tests pass. JavaScript tests ran directly with `node --test channel/tests/*.test.mjs` because this machine's npm shim points to a missing npm installation.

**What still feels unresolved:** The synthetic narration still needs a focused listening and performance review with the user; physical speaker output and subjective voice preference are not established. This is an improvement to one dated explanatory story, not approval to expand autonomous publication or claim a fully human presentation.

**Recommended next move:** Listen to this exact In Focus cut in Bearing before extending the treatment. Refine cadence, emphasis and audio mix where the listening review identifies a concrete weakness. Keep broad feature work paused and preserve the current source review and delivery version `3e89d626a639aa91c7f4` for comparison.
