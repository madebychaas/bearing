# Easy News — Active Mission

**Status: active.**

The prior Bearing story-quality milestone is complete and preserved. Do not reopen that accepted production example unless this mission requires a narrowly scoped compatibility fix.

## Mission

Build the first genuinely useful Easy News producer experience described in [EASY_NEWS_DIRECTION.md](EASY_NEWS_DIRECTION.md).

At the end of this mission, a producer should be able to open Easy News at any time and quickly understand:

1. **What are the top news stories that matter right now according to the configured content strategy?**
2. **How might each of those stories fit into the products this producer is responsible for?**

Use the working codebase as the starting point.

**Evolve, don't rebuild. Prove, don't platformize.**

Astra owns the technical implementation.

## Required proof

Use real or representative news inputs and deliver the smallest convincing working proof that:

- continuously surfaces a manageable set of high-value story opportunities,
- explains why each story matters now and why it fits the configured editorial strategy,
- identifies meaningful change rather than merely repeating new headlines,
- shows product-fit recommendations with understandable reasoning,
- lets the producer inspect supporting reporting,
- preserves editorial judgment rather than auto-assigning coverage,
- and reuses existing working machinery wherever practical.

The proof should prioritize producer usefulness over architectural breadth.

## Product behavior to demonstrate

The producer should be able to distinguish at least:

- strongest immediate-awareness candidates,
- strongest deeper-treatment opportunities,
- meaningful updates to active stories,
- developing or watch-worthy candidates,
- and local-to-national signals when supported.

The same story may have different strengths for different products.

Do not collapse product fit into one universal importance score.

## Interface standard

Build enough human-facing UI to test the editorial intelligence as a real producer experience.

The interface should be simple, fast to scan, and clear about:

- what the story is,
- why it is surfaced,
- what changed,
- why it fits the strategy,
- which products it may fit,
- why,
- and where the supporting reporting comes from.

Do not spend this mission on a broad visual redesign.

Do not expose taxonomy or machine metadata merely because it exists.

## Editorial standard

Recommendations must be explainable and source-grounded.

The configured content strategy may shape relevance and product fit, but the mechanism must remain neutral and must not encode partisan or ideological preference.

A candidate is not an assignment.

Human editorial decisions remain inspectable and reversible.

## Technical freedom

The requirements are behavioral, not architectural.

Inspect the existing implementation and choose the best incremental path.

Generalize only what the proof requires.

Keep working capabilities intact.

Do not create generalized infrastructure merely because it may be useful later.

## Supporting material

[COVERAGE_RADAR.md](COVERAGE_RADAR.md) contains useful prior thinking about change detection, emerging signals, local-to-national patterns, explainability, and producer awareness. Treat it as supporting exploration, not as a prescribed standalone architecture or separate product.

## Stop condition

When the V1 producer experience is convincingly useful and the proof above works:

1. test it end to end,
2. commit and push the stable state,
3. update this file with the handoff and what the implementation taught us,
4. stop.

Do not continue into a generalized multi-profile platform, a major UI redesign, or broad automated production expansion without a new mission.

## Prior milestone preserved

The accepted Bearing production milestone remains the reference for **Produced, not generated** story quality. Its pacing feedback remains relevant to future production work, but it is not the active task.
