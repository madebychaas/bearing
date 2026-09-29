# Coverage Radar — Producer News Intelligence

**Status:** Queued next mission. Do not build until `product/NEXT.md` activates it.

## Purpose

Coverage Radar is the human-facing news-intelligence surface for a national network producer.

Its job is simple:

**At any moment, what would a strong national network news team regret not knowing about?**

It should help a producer stay continuously oriented to the latest real-time news without requiring them to manually reconcile dozens of feeds, homepages, local reports, alerts, and repeated write-throughs.

Coverage Radar is not a separate news universe from Bearing.

The same underlying event intelligence should support both:

```text
sources / feeds / local signals / reporting
                    ↓
          shared news intelligence
      ingest → normalize → cluster → update
                    ↓
          canonical event records
             ↙                ↘
     Coverage Radar          Bearing
      producer UI       production machinery
```

**Coverage Radar knows what is happening. Bearing knows how to make something from it.**

## Product promise

A producer should be able to open Coverage Radar and answer, within seconds:

- What do I need to know right now?
- What materially changed since I last looked?
- What is becoming a national story?
- What deserves coverage?
- What is important but not ready yet?
- What am I likely to miss if I only follow the obvious national feeds?
- What reporting supports each signal?

The interface should feel like a continuously updating assignment desk, not another headline feed.

## One shared reality model

Coverage Radar and Bearing should consume the same canonical event records.

Do not maintain one interpretation of the news for the producer UI and another for Bearing.

A canonical event should be able to represent:

```text
event_id
working_headline
status
first_seen
last_updated

what_happened
why_it_matters
what_changed

sources[]
source_count
source_diversity
local_market_signals[]

topics[]
locations[]
people[]
organizations[]

freshness
national_significance
audience_impact
immediacy
change_magnitude
source_momentum
geographic_spread
institutional_significance
tellability
distinctiveness

known_facts[]
uncertainties[]
conflicts[]

why_surfaced
coverage_state
event_version
```

The exact schema may evolve. Preserve stable event identity whenever the underlying event remains the same.

## The producer view

The default experience should organize the event stream into three editorial states.

### Cover Now

Stories a national producer should know about and actively consider for coverage now.

These should have enough significance, freshness, sourcing, and tellability to merit immediate attention.

### Watch

Important developments that could become significant but are not mature enough, sufficiently sourced, or consequential enough yet.

A producer should understand exactly what threshold has not been crossed.

### Emerging Signals

Patterns that may not yet appear as one obvious national headline.

This is especially important for independent local reporting that begins to converge around the same underlying phenomenon.

Examples of the pattern:

```text
multiple markets report similar insurance cancellations
                    ↓
possible national consumer story

local hospitals independently report the same shortage
                    ↓
possible national health story

several utilities announce similar rate or service changes
                    ↓
possible national affordability story
```

Do not create a national pattern merely because stories share broad keywords. Require meaningful event or phenomenon-level similarity.

## What changed is a first-class feature

A producer does not only need to know what exists.

They need to know:

**What do I need to know that I did not know the last time I looked?**

Event history and producer seen-state should support clear change labels such as:

- NEW STORY
- MATERIAL UPDATE
- CONFIRMED
- CORRECTION
- NEW SOURCE
- NEW NATIONAL ANGLE
- NEW CONSEQUENCE
- MULTIPLE NEW MARKETS
- WATCH → COVER NOW
- COVER NOW → WATCH
- SOURCE CONFLICT
- RESOLVED / SUPERSEDED

A cosmetic headline rewrite is not a material update.

The system should compare event versions and explain the substantive difference.

## Editorial ranking

Rank events for national-news coverage significance, not generic popularity or clicks.

Useful dimensions include:

### National consequence

How many people, institutions, systems, markets, or communities could be affected?

### Immediacy

Does a producer or audience need to know this now?

### Change magnitude

Is this actually new information, a consequential escalation, reversal, decision, correction, threshold crossing, or outcome?

### Source momentum

Is credible reporting expanding or deepening?

Multiple stories copying the same original report should not masquerade as independent momentum.

### Geographic spread

Are independent markets or regions encountering the same development or phenomenon?

### Audience utility

Would understanding this materially change what viewers know, expect, prepare for, spend, do, or watch?

### Institutional significance

Does it involve consequential action by courts, agencies, companies, infrastructure operators, health systems, public-safety institutions, markets, or other nationally relevant actors?

### Tellability

Is there enough verified substance to tell a coherent national story now?

### Distinctiveness

Is this an important signal that is not already obvious from every national homepage?

## Penalties and holds

Reduce or hold stories when significance is being inflated by:

- duplicate or syndicated write-through coverage,
- old developments presented as new,
- one thin or uncorroborated source when the claim requires more,
- unsupported social virality,
- generic outrage or celebrity chatter without broader consequence,
- sensational headline wording,
- weak event matching,
- unresolved contradictions,
- or insufficient evidence to explain why the event matters.

A high score is not a declaration of truth. It is an editorial attention recommendation grounded in available reporting.

## Explain every recommendation

Every surfaced event should answer:

**Why is this here?**

A compact explanation might resemble:

> Federal agency changed the deadline 23 minutes ago; the action could affect a large national group; official documentation and several additional reports now support the update.

The explanation should identify the ranking factors that actually caused the event to surface.

Do not expose a mysterious aggregate score without interpretable reasons.

## Local-to-national detection

This is a core differentiator.

National desks already see obvious national stories.

Coverage Radar should be unusually good at noticing when separate local reports reveal a shared underlying development before it becomes an obvious national headline.

The system should:

1. retain source geography and market identity,
2. distinguish syndicated copies from independent reporting,
3. detect semantically related phenomena across markets,
4. surface the pattern with supporting examples,
5. explain why the pattern may have national relevance,
6. preserve uncertainty until the relationship is adequately supported.

Local convergence should create a signal, not automatically create a fact.

## Human editorial controls

The producer UI should eventually support lightweight actions such as:

- Cover
- Watch
- Dismiss
- Pin
- Merge
- Split
- Not the same story
- National angle
- Needs verification

These actions should update the shared canonical event state rather than creating UI-only annotations that Bearing cannot see.

Example:

```text
producer marks:
COVER + NATIONAL ANGLE
          ↓
canonical event state changes
          ↓
Bearing can see:
high-priority candidate for full treatment
```

Human action should inform the machinery without making the UI a production console.

## Bearing relationship

Coverage Radar identifies and maintains the news reality Bearing can work from.

Bearing should later be able to consume event state such as:

- eligible for Brief,
- candidate for In Focus,
- watch only,
- needs verification,
- superseded,
- materially updated,
- nationally significant,
- or explicitly prioritized by a producer.

Coverage Radar should not directly publish a Bearing segment.

The production and review boundaries remain separate.

## Human-facing UI

Build the first UI for speed of comprehension, not beauty.

A producer scanning the default screen should be able to understand:

- the event,
- why it matters,
- why it is surfacing now,
- what changed,
- how strong the sourcing is,
- and where to inspect the underlying reporting.

Event cards should reveal deeper detail on demand rather than displaying every metadata field at once.

The first version should prove editorial usefulness before receiving a major design pass.

## Machine-readable output

The human-facing UI and Bearing should both consume structured event data.

A simple derived output such as `coverage-radar.json` is acceptable for an MVP, but the canonical event records and history should remain the durable source.

Do not make the UI DOM, rendered cards, or a separate manually maintained file the source of truth.

## First build milestone

When this mission becomes active:

1. Reuse Bearing's existing source collection and coverage-grouping machinery where it is appropriate.
2. Establish or strengthen canonical event records and event-version history.
3. Compute interpretable editorial-attention dimensions.
4. Produce Cover Now / Watch / Emerging Signals.
5. Implement material-change detection.
6. Build a fast human-facing producer UI over those same records.
7. Make every surfaced event explain why it is there and show supporting reporting.
8. Demonstrate at least one local-to-national emerging signal using retained or test data.
9. Verify that Bearing can consume the same event objects without a parallel interpretation layer.

## Success test

Give the system messy, overlapping reporting from national sources, official sources, and multiple local markets.

A producer should be able to open Coverage Radar and quickly understand:

- the most important underlying events,
- which reports are duplicates versus distinct developments,
- what materially changed,
- what deserves national attention now,
- what is still only a watch,
- what pattern may be emerging,
- why the system thinks so,
- and which reporting supports that judgment.

The producer should feel **dangerously well-informed**, not overwhelmed.

## Non-goals for the first version

Do not:

- redesign the Bearing viewer,
- build a separate competing ingestion system,
- use generic engagement or social virality as the primary ranking signal,
- treat multiple publisher labels as proof of independent confirmation,
- auto-publish full Bearing stories from Radar recommendations,
- over-polish the producer UI before the event intelligence proves useful,
- or collapse uncertain, contradictory, or merely similar events into one story for neatness.
