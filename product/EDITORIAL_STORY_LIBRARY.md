# Bearing — Editorial Story Library & Ranking

**Status:** active editorial-system standard.

Bearing needs more than a small list of top stories. It needs a **robust, continuously refreshed library of current story candidates** from which the newsroom can rank, select, update, cycle and produce.

The Top Stories surface is a presentation of editorial judgment. It is **not** the inventory.

## Core model

```text
sources / feeds / primary documents / local signals
                        ↓
                 canonical events
                        ↓
              CURRENT STORY LIBRARY
        retain → cluster → verify → update → expire
                        ↓
              editorial ranking lenses
        consequence + freshness + Bearing strategy
                        ↓
          newsroom priority / production eligibility
                ↙                    ↘
          Top Stories              production
```

The library should be large enough that Bearing has meaningful editorial choice at any moment, while remaining disciplined about evidence and duplication.

Do not solve scarcity by lowering verification standards or padding the library with junk.

## The editorial problem

A national newsroom should not have to choose among only a handful of stories because an early heuristic filter eliminated everything else.

The desk should distinguish:

- **not important enough to lead**
from
- **not a valid current story**

Those are not the same judgment.

A story can be a legitimate current national story without belonging in the top three.

## Current Story Library

Maintain a durable current-event inventory that includes verified or inspectable stories across states such as:

- **breaking** — consequential event unfolding now,
- **developing** — material updates continue to arrive,
- **current** — valid current story with a clear today/now reason,
- **continuing** — still relevant because consequences remain active even without a brand-new publication in the last few hours,
- **scheduled** — known upcoming event/release worth newsroom awareness,
- **watch** — plausible important development not yet sufficiently verified/mature,
- **held** — evidence conflict, weak sourcing, unclear timing or other blocker,
- **resolved / superseded** — retained for continuity but no longer active.

Do not force every story into Top Stories simply because it exists.

## Inventory target

Do not hard-code a vanity number, but the system should normally expose **dozens of legitimate current national story candidates**, not four or five, when the news environment supports them.

As an operational target, evaluate whether the connected source set can sustain approximately:

- **20–60 active/current/continuing story threads** in the usable library,
- a broader Watch pool behind them,
- and a much smaller Top Stories set.

If the live environment genuinely contains fewer supported stories, show fewer. Never fabricate volume to hit a quota.

The purpose of the target is to detect an over-restrictive editorial funnel.

## Story identity, not article inventory

The library stores **underlying stories/events**, not a flat pile of articles.

Multiple reports about one event should strengthen or update one canonical story unless they represent materially different developments.

Each story should retain:

```text
event_id
event_version
working_headline
status
first_seen
last_material_update
last_verified
today_or_now_peg

what_happened
what_changed
why_it_matters
who_is_affected
what_to_watch_next

sources[]
primary_sources[]
independent_source_count
source_lineage

topics[]
locations[]
people[]
organizations[]

known_facts[]
uncertainties[]
conflicts[]

editorial_dimensions
strategy_dimensions
production_readiness
visual_availability
history[]
```

## Separate validity from priority

The desk should make at least three different decisions:

### 1. Is this a legitimate current story?

A current-story eligibility decision should consider:

- real development or continuing consequence,
- adequate sourcing for the claim being made,
- interpretable timing,
- national relevance or meaningful cross-market pattern,
- not merely duplicate/syndicated material,
- not routine institutional promotion,
- not stale content dressed up by a recent page timestamp.

### 2. How important is it?

Newsworthiness dimensions include:

- national consequence,
- immediacy,
- change magnitude,
- scale of affected audience,
- safety/health consequence,
- economic/household consequence,
- institutional significance,
- geographic spread,
- source momentum,
- uncertainty requiring attention,
- durability of consequence.

### 3. How relevant is it to Bearing's editorial strategy?

Bearing strategy should be an explicit, inspectable ranking lens, not a hidden keyword boost.

Useful strategy dimensions include:

- **orientation value** — does understanding this materially help someone get their bearings?
- **audience utility** — could this change what people expect, prepare for, spend, do or watch?
- **context opportunity** — is Bearing especially useful because the story needs relationships or consequences explained?
- **household relevance** — money, work, health, safety, services, rights, infrastructure and other lived effects.
- **system significance** — consequential changes in public institutions, markets, technology or infrastructure.
- **undercovered significance** — important signal that is not already obvious from every headline surface.
- **continuity value** — does this advance a story Bearing has been helping viewers understand?
- **tellability** — is there enough substance to create a coherent explanation?
- **visual/explanatory potential** — can the story be meaningfully shown or explained without manufacturing spectacle?

Strategy relevance can affect ranking. It must **not erase objectively major news** simply because it is less on-brand.

A catastrophic event, major war development, national emergency, landmark court action or other objectively dominant story still belongs near the top when warranted.

## Brand / strategy tiers

For inspectability, derive a strategy classification such as:

- **CORE** — directly aligned with Bearing's orientation mission and recurring editorial strengths.
- **STRONG FIT** — nationally important and particularly suited to Bearing explanation.
- **GENERAL NATIONAL** — legitimate significant national story; Bearing should know it even if it is not distinctive to the brand.
- **WATCH FIT** — potentially relevant but not sufficiently mature, consequential or sourced.
- **LOW FIT** — valid news but weak alignment and low consequence for Bearing's national strategy.

Do not treat LOW FIT as “not news.” It simply ranks lower for this product.

## Ranking is multi-dimensional

Avoid one mysterious scalar becoming the editorial truth.

Store interpretable dimensions, then derive views such as:

### National Priority
“What would a strong national newsroom most regret missing?”

### Bearing Priority
“What current stories best match Bearing's mission of orientation and understanding?”

### Fast Change
“What materially changed most recently?”

### Household Impact
“What current developments most affect daily life, money, work, health, safety or services?”

### Emerging / Undercovered
“What supported signal may matter more than its current headline visibility suggests?”

### Production Ready
“What is sufficiently sourced and developed to move into the newsroom pipeline now?”

The default newsroom order can combine these dimensions, but producers should be able to inspect why a story ranks where it does.

## Top Stories

Top Stories should select from the Current Story Library.

The top three are the strongest immediate orientation set, but the ranked list below them should remain deep enough to support real newsroom cycling.

The system should avoid:
- showing the same three themes all day because they happen to score well,
- allowing economics/policy to crowd out safety, health, world or accountability stories,
- overreacting to publisher frequency,
- treating a recent headline timestamp as importance,
- filling gaps with weak items.

Use editorial diversity as a **tie-breaker and portfolio consideration**, not a quota that displaces clearly more important news.

## Continuing stories

A major weakness of pure “today peg” logic is that it can discard stories that remain highly consequential.

Allow a continuing story to remain active when:
- consequences are still unfolding,
- an audience still needs current orientation,
- a decision/implementation period remains active,
- the story is awaiting a known next development,
- the story has materially changed within a reasonable retained window,
- the last verified state is still accurate.

Continuing relevance must be explicit and periodically rechecked. Do not keep stale stories alive indefinitely.

## Real-time update behavior

When new evidence arrives:

1. match it to an existing canonical story where appropriate,
2. determine whether it is a material update,
3. update the event version,
4. recompute editorial and strategy dimensions,
5. change status/rank only when the evidence supports it,
6. record what changed and why the rank moved,
7. invalidate downstream production if the material change affects an in-progress artifact.

The newsroom should be able to answer both:
- **What are the most important stories right now?**
- **What changed since the last editorial assessment?**

## Source breadth and scarcity diagnosis

When the active library is too thin, diagnose **why** rather than simply loosening thresholds.

Possible reasons:
- source coverage gaps,
- ingestion failures,
- over-aggressive national-scope rules,
- inability to carry consequential continuing stories,
- poor clustering that collapses distinct developments,
- weak extraction of the actual development from a report,
- ranking logic being mistaken for eligibility,
- insufficient use of primary/scheduled sources,
- too much material trapped in Watch/Held without a path to re-evaluation.

Expose this diagnosis in tests or editorial telemetry.

## Editorial QA

Periodically sample:
- stories included in the active library,
- stories left in Watch,
- stories held/out of scope,
- major national stories visible elsewhere but absent from Bearing.

For misses, classify the failure:
- source unavailable,
- ingested but misclassified,
- clustered incorrectly,
- today/continuing peg missed,
- consequence underestimated,
- strategy fit underestimated,
- evidence insufficient,
- correctly excluded.

The point is to improve recall **without destroying precision**.

## Success

The library is working when:

- Bearing consistently has a deep set of legitimate current stories to choose from,
- the top rank still feels disciplined rather than padded,
- major national news is rarely absent because of a narrow heuristic,
- Bearing-specific strategy meaningfully reorders the middle of the list,
- continuing stories remain available when they still matter,
- new material updates existing story threads instead of creating article clutter,
- producers can understand why each story is present and why it ranks where it does,
- the production pipeline can select materially different stories without engineering a new candidate by hand.

The desired feeling is:

**Bearing knows what is going on, has a point of view about what matters, and still shows its work.**
