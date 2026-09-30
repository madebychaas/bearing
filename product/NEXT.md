# Bearing — Active Mission

**Status: active.**

The September 30 editorial-voice and 13-script rewrite milestone is complete and preserved.

The active mission is the selection-to-production proof described in [SELECTION_TO_PRODUCTION.md](SELECTION_TO_PRODUCTION.md).

## Mission

Connect the existing Easy News producer intelligence to the existing Bearing production machinery for one real story.

A producer should be able to take a story opportunity surfaced in Easy News, choose the appropriate product treatment, carry the source evidence and editorial context forward, review the resulting script, and produce a finished Bearing asset without forcing the production side to rediscover the story from scratch.

If the reporting materially changes before completion, the workflow should require editorial reassessment rather than silently finishing stale work.

## Guardrails

- Evolve, don't rebuild.
- Prove, don't platformize.
- Produced, not generated.
- Preserve the existing Easy News desk, editorial voice standard, source grounding, and accepted Bearing production machinery.
- Human selection and approval remain inspectable and reversible.
- Do not render the 13 rewrite examples as a batch.
- Do not build a generalized CMS, assignment system, multi-agent newsroom, broad autonomous publishing system, or major UI redesign.
- Generalize only what the proof requires.

## Technical approach

Astra owns the implementation.

Choose the smallest clean path through the existing codebase. Reuse working machinery wherever practical. Do not stop for routine engineering decisions.

## Success

One current story can travel:

**Easy News opportunity → producer product choice → carried-forward evidence/context → editorial draft/review → Bearing production → finished traceable asset**

with one material-change/reassessment case verified.

When that proof is stable, commit, update this handoff with what the implementation taught us, and stop.
