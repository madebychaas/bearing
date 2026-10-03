# Bearing — Second Story + Graphics Quality Proof

**Status:** next active proof.

The first role-separated newsroom story has been reviewed and the workflow has been made repeatable. The next task is to run the same architecture on a **materially different current story** without redesigning the workflow.

Read:
- `AGENTS.md`
- `product/PRODUCT_VISION.md`
- `product/NEWSROOM_ARCHITECTURE.md`
- `product/GRAPHICS_ART_DIRECTION.md`
- the current `product/NEXT.md`
- the accepted October 1 production references already identified there.

## Purpose

Test whether the newsroom roles behave differently when the journalism requires different judgments, and raise graphics quality from “renders correctly” to **professionally art-directed**.

This run is an experiment in reuse, not an invitation to expand the architecture.

## Story selection

Choose one current story that is materially different from the Medicare proof.

Prefer a story with:
- meaningful documentary imagery,
- a real explanatory-graphics need,
- uncertainty, sequence, geography, comparison, process or change,
- enough sourced evidence to produce responsibly.

Weather/disaster is a strong candidate if current desk evidence supports it, but do not force that category if a better current story exists.

## Run the existing workflow

Use the now-repeatable role-separated flow:

```text
Assignment Desk
→ Editor
→ Producer
→ Journalist + Visual Intelligence + Graphics Intelligence
→ Art Direction / Motion Design
→ Standards / Final Edit
→ deterministic production validation
→ private preview
```

Do not create a new autonomous service for Art Direction. Use the smallest bounded stage necessary to test whether separating design judgment materially improves the result.

Do not enable autonomous publishing or production.

## Graphics acceptance is now first-class

A technically valid graphic can still fail.

Graphics Intelligence decides **what needs graphical explanation**.

Art Direction decides **how that approved explanation should look and move**.

The renderer only executes the approved specification.

Follow `product/GRAPHICS_ART_DIRECTION.md` as an active production standard.

For every proposed graphic, record its reason for existence. Remove it if documentary imagery communicates the idea better.

Standards / Final Edit should reject a graphic when it is weak, redundant, overly textual, poorly composed, too dense, too fast, generic, unsupported or unnecessary.

## Preserve the experiment

Do not automatically alter architecture because something feels awkward.

Complete the second story using the existing workflow wherever possible. Record friction and failures as evidence.

Preserve:
- every role artifact,
- important Art Direction changes to the GraphicsSpec,
- graphics that were removed and why,
- source/version lineage,
- any return/revise/resume path,
- final validation results.

## Review questions

At the private-review stop, compare this story with the Medicare proof and answer:

1. Did the roles meaningfully adapt to a different kind of journalism?
2. What did Visual Intelligence contribute that Graphics Intelligence did not?
3. Did Art Direction materially improve the finished graphics?
4. Which proposed graphics were removed because they were unnecessary?
5. Which graphics improved because hierarchy, composition, reading time or motion changed?
6. Did Standards reject anything that was technically valid but editorially/visually weak?
7. Can each poor decision be traced to the newsroom role that owned it?
8. Does the finished piece feel authored and produced rather than generated?
9. Did the workflow remain reusable without code changes? If not, what genuine blocker required a change?

## Stop condition

Stop with:
- one finished **private** preview,
- the persisted artifact chain,
- full relevant tests,
- encoded-frame and complete-playback review,
- the comparison above,
- and a concise recommendation on whether Art Direction deserves a permanent bounded responsibility.

Do not publish. Do not turn on autonomous production. Do not begin Lumina integration yet.

If local work from the first proof has not been pushed, preserve it. Reconcile rather than discarding or overwriting those local commits.
