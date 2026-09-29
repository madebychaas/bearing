# Easy News — Product Direction

## V1 outcome

Easy News V1 should enable a producer to open one interface at any time and quickly answer two questions:

1. **What are the top news stories that matter right now according to the configured content strategy?**
2. **How might each of those stories fit into the products this producer is responsible for?**

That is the first proof.

Do not broaden the mission beyond what is needed to make that experience genuinely useful.

## What Easy News is

Easy News is a reusable editorial production mechanism.

It should be able to take a large, continuously changing universe of reporting and story signals and move useful opportunities toward trusted, strategy-aligned editorial products.

The product direction is:

**signal → understanding → editorial decision → product decision → production → approval → trusted content inventory**

This is a product requirement, not a prescribed software architecture.

Astra should inspect the existing codebase and decide the best technical path.

**Evolve, don't rebuild. Prove, don't platformize.**

## Produced, not generated

Easy News produces editorial products.

Generative models may help research, compare, summarize, draft, visualize, voice, assemble, or transform material.

Unreviewed model output is not automatically an editorial product.

A useful output should reflect intentional editorial choices, supported information, an appropriate product purpose, and a known state of readiness.

## One underlying news reality

Different people and downstream products may need different views of the news.

They should not require separate systems to independently decide what is happening.

The same underlying understanding of stories and developments should be capable of feeding:

- a broad newsroom-awareness experience,
- a specialized producer experience,
- production workflows,
- and downstream products using trusted content inventory.

Do not create competing copies of the same story simply because two interfaces need different presentations.

## V1 producer experience

The first useful Easy News interface is for a producer.

It should continuously surface a manageable ranked set of story opportunities and make each recommendation understandable.

For each surfaced story, the producer should be able to understand quickly:

- what the story is,
- why it matters now,
- why it fits the configured content strategy,
- what materially changed,
- how current and well-supported the reporting is,
- which defined products it may fit,
- why it fits those products,
- and what might cause the recommendation to change.

Recommendations should support editorial judgment, not replace it.

Do not hide the reasoning behind an unexplained aggregate score.

## Awareness and understanding are different jobs

Easy News should recognize that different stories may serve different audience needs.

Some developments primarily require timely awareness:

**What do people need to know right now?**

Other topics deserve deeper understanding:

**What do people need to understand today?**

The strongest immediate-awareness story does not have to be the strongest deeper-treatment opportunity.

Do not force all products to use one universal ranking.

## Product-aware assistance

Easy News should understand configured product definitions well enough to help a producer see how a story might fit the work they actually need to make.

A product definition may include:

- audience purpose,
- intended editorial function,
- suitable story characteristics,
- required components,
- expected length or shape,
- freshness and shelf-life expectations,
- success standards,
- and update or retirement conditions.

For V1, demonstrate this with the currently defined immediate-awareness product and deeper story/franchise products.

Treat those product definitions as configurable editorial requirements, not universal Easy News architecture.

## Strategy-aware, not strategy-blind

Easy News should use the configured editorial strategy to help rank and explain opportunities.

Useful considerations may include:

- urgency,
- timeliness,
- national significance,
- audience impact,
- awareness need,
- understanding gap,
- development potential,
- reporting strength,
- human consequence,
- utility,
- accountability,
- local-to-national relevance,
- freshness,
- and meaningful change.

The exact implementation is Astra's decision.

The mechanism must remain neutral. It should not encode partisan or ideological preference. Strategy can shape relevance and product fit without becoming viewpoint favoritism.

## Candidate pool is not the assignment list

Easy News should be excellent at noticing potentially important things.

Surfacing a candidate does not mean the producer should cover it.

The system should preserve more possibilities than any one product ultimately selects.

Selection remains an editorial decision informed by evidence, strategy, product need, timing, reporting opportunity, and opportunity cost.

Do not optimize toward producing something from every signal.

## Meaningful change matters

News is not a collection of static headlines.

Easy News should help producers understand what materially changed in an ongoing story.

A cosmetic headline rewrite is not a material update.

A useful change may include a new confirmed fact, consequential decision, reversal, correction, widened impact, new evidence, changed risk, new market pattern, or other development that changes the editorial understanding or product need.

Existing work should be able to remain valid, require updating, or be retired as the facts change.

## Local-to-national signals

Easy News should be capable of noticing when independent reporting from multiple communities or markets may reveal a larger national phenomenon.

Do not infer a national trend from one anecdote or from syndicated duplicates.

Local convergence should create an explainable editorial signal, not an automatic factual conclusion.

## Human-facing experiences

The long-term mechanism should be able to support multiple human views over the same underlying news understanding.

### Newsroom view

A broad awareness surface answering questions such as:

- What matters now?
- What materially changed?
- What is emerging?
- What should we watch?
- What local reporting may signal something larger?

### National Producer view

A more specific view answering questions such as:

- What are the strongest candidates for my next immediate-awareness product?
- What should rotate because the news changed?
- What topic most deserves deeper treatment?
- What products or audience needs could this reporting support?
- What are the strongest alternatives?
- What is not ready yet?
- What existing work may need updating or retirement?

For V1, prioritize the National Producer usefulness test. Do not build multiple polished interfaces merely to prove the concept.

## Trusted content inventory

The larger Easy News direction includes producing a trusted pool of approved editorial material that humans, agents, sites, and other products can use.

Keep a meaningful distinction between:

- **editorial intelligence** — things the system has noticed, grouped, interpreted, or recommended,
- and **trusted content inventory** — material that has progressed far enough through sourcing, editorial judgment, production, quality checks, and approval to be appropriate for downstream use.

V1 does not need to complete the entire future inventory system.

Do not let that larger direction distract from proving producer usefulness first.

## What Astra should decide

The requirements above describe behavior, not implementation.

Astra should decide:

- what existing machinery can be reused,
- what should remain product-specific,
- what should be generalized now,
- what should stay coupled until reuse is proven,
- how story continuity and material change are represented,
- how product fit is evaluated,
- how human editorial actions affect shared state,
- and what the minimum useful interface should be.

Prefer working behavior over architectural elegance.

Document consequential choices after they become real.

Do not stop for approval on routine engineering decisions.

## Guardrails

- **Evolve, don't rebuild.**
- **Prove, don't platformize.**
- **Produced, not generated.**
- Keep recommendations explainable.
- Keep editorial control inspectable and reversible.
- Do not build a second newsroom humans must manually maintain.
- Do not redesign the existing viewing product unless this mission requires a narrowly scoped integration.
- Preserve working production capabilities.
- Do not begin a large generalized platform build after the proof succeeds without a new mission.

## V1 success test

Give a producer Easy News during a real or representative news cycle.

Without manually reconciling dozens of sources, they should be able to:

- identify the most important strategy-aligned story opportunities,
- understand why each is surfaced,
- see meaningful changes as they occur,
- understand which products the strongest stories may fit and why,
- inspect the underlying reporting,
- and make an informed editorial decision quickly.

The most useful validation questions are:

1. Did Easy News surface the stories the producer expected?
2. Did it catch anything important the producer otherwise might have missed?
3. Were the reasons for surfacing stories useful and credible?
4. Did the product-fit recommendations make editorial sense?
5. Did it reduce the hunting, sorting, and synthesis the producer had to do?

If this producer experience is convincingly useful, stop and document what the implementation taught us before broadening the platform.
