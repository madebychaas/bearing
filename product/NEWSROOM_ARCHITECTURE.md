# Bearing — Role-Separated Newsroom Architecture

**Status:** Product architecture. The active implementation slice is defined in `product/NEXT.md`.

## Why this exists

Bearing should not rely on one broadly instructed model to discover a story, decide what it means, choose the treatment, write it, visualize it, edit it and approve it in one inference.

That collapses distinct newsroom judgments into one opaque act.

Bearing should instead encode the **division of cognitive labor that makes a strong newsroom work**:

```text
evidence → understanding → editorial judgment → story architecture
         → language + visual journalism + graphics
         → final edit → execution
```

The goal is not to imitate a newsroom org chart for its own sake. Separate a role only when it represents a genuinely different kind of reasoning.

## Core principle

**Agents make bounded judgments. Systems perform defined work.**

A role is an agent when it must interpret evidence, exercise editorial judgment or transform one editorial artifact into another.

A capability should remain deterministic software when correctness can be established by rules, schemas, asset checks, timing, rendering or other defined operations.

Role separation is primarily **semantic and contextual**, not infrastructural. The first implementation does not require eight services, eight models or free-running autonomous workers. Multiple roles may use the same underlying model while receiving different system instructions, isolated context, permissions, tools, schemas and stop conditions.

Agents do not hold open-ended conversations with one another. They pass **persisted artifacts** downstream.

## The newsroom model

```text
                           NEWS DIRECTOR
                                │
                 priorities / escalation / allocation
                                │
                                ▼
SOURCES ──► ASSIGNMENT DESK ──► EDITOR ──► PRODUCER
                                             │
                         ┌───────────────────┼──────────────────┐
                         ▼                   ▼                  ▼
                    JOURNALIST        VISUAL INTELLIGENCE   GRAPHICS INTELLIGENCE
                         │                   │                  │
                         │                   └──────┬───────────┘
                         │                          ▼
                         │                   GRAPHICS RENDERER
                         │                          │
                         └──────────────┬───────────┘
                                        ▼
                               STANDARDS / FINAL EDIT
                                        │
                                        ▼
                                TD / PLAYOUT SYSTEM
```

The **News Director is portfolio-level**, not a required hop inside every individual story. It considers the field of current events and production capacity. Story-level work begins from the assignment desk.

## Role contracts

Every intelligent role must define four things:

1. **Jurisdiction** — what judgment this role owns.
2. **Artifact** — the structured output it must produce.
3. **Prohibitions** — decisions it is not allowed to make.
4. **Stop condition** — the point at which its work is complete.

A role should receive the smallest useful context necessary to perform its jurisdiction. It should not inherit the entire chain of prompts, deliberations and tools used upstream.

### 1. Assignment Desk

**Question:** What happened, what changed and what evidence supports it?

**Jurisdiction**
- discovery and factual state,
- source provenance,
- known facts,
- contradictions and uncertainty,
- what materially changed,
- reporting gaps,
- scheduled next developments.

**Artifact:** `AssignmentBrief`

Expected fields:

```text
event_id
event_version
working_headline
today_peg
what_happened
what_changed
known_facts[]
uncertainties[]
conflicts[]
sources[]
open_reporting_questions[]
next_expected_developments[]
eligibility_state
```

**Prohibited**
- choosing the story's final editorial framing,
- writing a script,
- designing production,
- treating discovery as verification.

**Stop condition:** enough sourced evidence exists for an editor to make an editorial judgment, or the brief explicitly records why it does not.

The existing national assignment desk and canonical-event work should evolve into this role rather than being replaced.

### 2. Editor

**Question:** What is this story actually about, why does it matter, and what should the audience understand?

**Jurisdiction**
- editorial meaning,
- audience need,
- story focus,
- significance and context,
- necessary qualifications,
- what still must be reported before production.

**Artifact:** `EditorialBrief`

Expected fields:

```text
event_id
event_version
core_development
why_it_matters
audience_need
editorial_focus
essential_context[]
required_attribution[]
do_not_overstate[]
reporting_needed[]
update_triggers[]
recommended_coverage_state
```

**Prohibited**
- inventing facts,
- treating unsupported inference as reporting,
- designing shot-by-shot production,
- changing source evidence.

**Stop condition:** a defensible editorial direction exists, with unresolved reporting needs made explicit.

### 3. Producer

**Question:** How should Bearing tell this story?

**Jurisdiction**
- format,
- story architecture,
- duration,
- sequencing,
- editorial beats,
- element requests,
- transitions and pacing,
- handoff to language and visual specialists.

**Artifact:** `ProductionPlan`

Expected fields:

```text
event_id
event_version
format
target_duration
story_beats[]
required_elements[]
visual_questions[]
graphics_questions[]
script_mode
opening_strategy
ending_strategy
update_trigger
```

**Prohibited**
- changing factual conclusions,
- silently resolving editorial uncertainty,
- fabricating visual evidence,
- rendering final media.

**Stop condition:** every essential editorial need has a production treatment or is explicitly marked unresolved.

### 4. Journalist

Reporter and anchor are one underlying intelligence with different output modes.

**Question:** How should a human journalist communicate the approved editorial plan?

Possible modes include:
- `anchor`
- `reporter_track`
- `live_shot`
- `vo_sot`
- `interview`
- `explainer`

**Jurisdiction**
- language,
- questioning,
- narrative transitions,
- spoken clarity,
- Bearing editorial voice.

**Artifact:** `JournalisticDraft`

**Prohibited**
- changing the editorial focus,
- strengthening a claim beyond the evidence,
- inventing facts, quotes or observations,
- adding unsupported certainty.

**Stop condition:** the requested mode communicates the approved plan completely and naturally within its target.

A future reporter role may become separate if Bearing begins actively acquiring new reporting through interviews, records requests or other original reporting. Writing alone does not justify that split.

### 5. Visual Intelligence

**Question:** What do the pictures prove, and what visual evidence best tells this story?

Visual Intelligence is journalism, not decoration.

**Jurisdiction**
- documentary image and video assessment,
- what footage actually establishes,
- visual evidence strength,
- image provenance,
- shot/footage requests,
- missing visual evidence,
- picture-to-script alignment,
- identifying when graphics are needed because available pictures cannot explain something.

**Artifact:** `VisualAssessment`

Expected fields:

```text
strongest_visual_evidence[]
available_visuals[]
proof_limits[]
avoid_as_proof[]
missing_visuals[]
recommended_sequence[]
graphics_needs[]
rights_or_courtesy_notes[]
```

**Prohibited**
- treating illustrative or synthetic imagery as documentary evidence,
- using generic file footage as proof of a current claim,
- deciding the story's editorial meaning,
- drawing the requested graphics.

**Stop condition:** the producer and editor can understand what the available pictures establish, what they do not, and what remains visually missing.

### 6. Graphics Intelligence

**Question:** What explanatory graphic would make the approved information easier to understand?

**Jurisdiction**
- graphic purpose,
- information hierarchy,
- graphic type,
- data/labels/copy,
- source attribution,
- animation intent,
- template selection,
- machine-readable graphics specification.

**Artifact:** `GraphicsSpec`

Example:

```json
{
  "type": "timeline",
  "purpose": "Show when the policy changes take effect",
  "headline": "Changes begin in January",
  "duration": 8,
  "elements": [],
  "source_attribution": [],
  "editorial_constraints": [],
  "template": "bearing.timeline.v1"
}
```

**Prohibited**
- independently changing the facts,
- deciding the story angle,
- presenting synthetic output as documentary evidence,
- free-styling outside the approved design system in production.

**Stop condition:** the graphic's communicative purpose and all content required to render it are unambiguous.

### 7. Standards / Final Edit

**Question:** Is this proposed story supported, clear, fair, coherent and ready to execute?

This role is a narrow critic, not a replacement writer.

**Jurisdiction**
- claim-to-source support,
- attribution,
- overstatement,
- internal consistency,
- script/picture agreement,
- graphics accuracy,
- editorial voice,
- repetition and unnecessary complexity,
- required corrections or holds.

**Artifact:** `FinalReview`

Possible decisions:
- `approve`
- `approve_with_edits`
- `return_to_editor`
- `return_to_producer`
- `hold_for_reporting`

Edits should be specific and traceable. Do not regenerate the whole story merely because a smaller correction is needed.

**Prohibited**
- inventing replacement facts,
- silently changing source evidence,
- reopening settled creative choices without a concrete defect.

**Stop condition:** every blocking issue is either resolved or returned to the role that owns it.

### 8. News Director

**Question:** Across the field of current events, what deserves newsroom attention and production resources?

**Jurisdiction**
- portfolio priorities,
- relative editorial urgency,
- resource attention,
- escalation,
- story competition and duplication,
- identifying when a previously secondary event becomes a priority.

**Artifact:** `NewsroomPriorities`

The News Director should consume canonical event state and editorial readiness. It should not rewrite individual story briefs.

For the first role-separated implementation, the existing assignment-desk ranking machinery may continue to provide portfolio priority. Do not build a News Director agent merely to complete the diagram.

### 9. TD / Playout

**Not an editorial agent.**

Technical execution should be deterministic wherever possible.

It validates:
- required assets exist,
- hashes/versions match,
- durations are legal,
- captions and narration correspond,
- graphics resolve,
- sequence structure is valid,
- rights/courtesy metadata is present where required,
- no stale artifact has been substituted,
- the finished manifest can actually play.

If something is wrong, **fail loudly and specifically**.

A model may later diagnose a technical failure, but software should determine whether the sequence is valid.

## Artifact chain and provenance

The core implementation should make the editorial transformations inspectable:

```text
Canonical Event
   ↓
AssignmentBrief
   ↓
EditorialBrief
   ↓
ProductionPlan
   ├── JournalisticDraft
   ├── VisualAssessment
   └── GraphicsSpec
          ↓
     RenderedGraphics
   ↓
FinalReview
   ↓
PlayoutManifest
   ↓
FinishedAsset
```

Every artifact should carry:
- stable `event_id`,
- input `event_version`,
- schema/version identifier,
- source/provenance references as appropriate,
- creation/update time,
- upstream artifact references,
- status,
- reason when held or returned.

A material change to the canonical event must invalidate or require reassessment of downstream artifacts whose conclusions depended on the changed evidence.

## No free agent chat

Do not implement a room full of agents talking to one another.

Each role should:
1. receive defined inputs,
2. perform its bounded judgment,
3. emit a structured artifact,
4. stop.

This makes failures diagnosable. When an outcome is poor, Bearing should be able to answer:

**Which newsroom judgment failed?**

not merely:

**Why did the AI do that?**

## Graphics renderer boundary

Graphics Intelligence is not the renderer.

Use a renderer adapter boundary:

```text
GraphicsSpec
    ↓
Graphics Renderer Adapter
    ↓
rendered asset + render manifest
```

This allows Bearing to target its existing graphics machinery and, later, Angelo's **Lumina Studio** without giving the renderer editorial authority.

### Lumina Studio

The current Lumina Studio prototype is a normal TypeScript/React application with a 1280×720 stage, layers, text/shapes/particles, motion controls, timeline behavior and structured scene operations. It can export MP4, PNG, SVG, PNG sequences, JSON and Blender output.

Treat Lumina as a promising **graphics execution and human-edit surface**, not as the Graphics Intelligence itself.

Before production integration:
- export/sync only the needed code through an explicit project transfer,
- replace generic creative-direction assumptions with the Bearing design system,
- preserve a human-editable studio surface,
- define stable templates and safe areas,
- make source attribution a first-class field,
- constrain information density and text lengths,
- keep synthetic/explanatory graphics visually distinct from documentary evidence,
- preserve deterministic render inputs and output manifests.

Do not create a hard Bearing runtime dependency on the Lovable-hosted project. Import or adapt code only after the graphics contract is proven.

## First implementation slice

Do **not** attempt to build the full newsroom at once.

Prove one vertical story path using the existing national assignment desk and production machinery:

1. Define versioned schemas for:
   - `AssignmentBrief`
   - `EditorialBrief`
   - `ProductionPlan`
   - `JournalisticDraft`
   - `VisualAssessment`
   - `GraphicsSpec`
   - `FinalReview`
   - `PlayoutManifest`

2. Produce a real `AssignmentBrief` from one current canonical event.

3. Add a role-isolated Editor that consumes only the assignment artifact plus explicitly allowed source evidence and emits `EditorialBrief`.

4. Add a role-isolated Producer that consumes the approved editorial brief and emits `ProductionPlan`.

5. Fan out from the production plan to:
   - Journalist,
   - Visual Intelligence,
   - Graphics Intelligence.

6. Reunite those artifacts at Standards / Final Edit.

7. Convert an approved result into the existing Bearing production path through a deterministic manifest/adapter rather than rebuilding the player or renderer.

8. Verify a material source update forces the appropriate downstream reassessment instead of silently completing stale work.

9. Intentionally break one required asset or version reference and verify the technical layer refuses to play/render it with an actionable error.

The first proof should use **one real current story**. Do not batch-produce stories merely to demonstrate orchestration.

## Evaluation

Compare the role-separated result against the current broad-agent path where practical.

Evaluate the actual editorial output, not only schema compliance:

- Is the story focus clearer?
- Did unsupported assertions decrease?
- Does the script preserve the editor's intended meaning?
- Are the visuals evidentiary rather than decorative?
- Are graphics requested only when they improve understanding?
- Does the finished piece feel more produced and less generated?
- Can a bad result be traced to a specific role/artifact?
- Does each role stop when its job is complete?
- Does the role separation reduce unnecessary model context and wandering?

Record failures as architecture evidence. Do not hide them by adding more agents.

## Guardrails

- Evolve the existing codebase; do not rebuild Bearing.
- Preserve the accepted viewer and October 1 production approach.
- Preserve the national assignment desk and canonical source/evidence work.
- A new role must represent a distinct judgment, not merely a new prompt name.
- Do not create long-lived autonomous loops for story production.
- Do not let downstream roles silently repair upstream evidence.
- Do not let agents freely converse or share hidden chain-of-thought.
- Persist decisions and artifacts, not model deliberation.
- Keep human selection/review inspectable and reversible.
- Do not auto-publish.
- Do not import Lumina or another external project until the renderer interface is clear.
- Prefer a small vertical proof over a generalized agent framework.
- Stop and reassess if the architecture produces more complexity without a measurable editorial improvement.

## Success condition

The first milestone succeeds when one real current story can move through:

```text
current sourced event
→ AssignmentBrief
→ EditorialBrief
→ ProductionPlan
→ Journalist + Visual Intelligence + Graphics Intelligence
→ FinalReview
→ deterministic production handoff
→ finished traceable Bearing asset
```

and Bearing can demonstrate:

1. each role received only the context required for its jurisdiction,
2. each role emitted a persisted inspectable artifact,
3. a material reporting change invalidated or reassessed the correct downstream work,
4. an execution defect failed loudly rather than being papered over by a model,
5. the resulting story is at least as factual and materially better focused/coherent than the broad-agent baseline.

Once that vertical proof is stable, use what it teaches to decide which roles deserve further autonomy, which should remain simple transforms, and when to integrate the Lumina renderer.
