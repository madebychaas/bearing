# Selection-to-production checkpoint — September 30, 2026

**Status: implemented and browser-checked; the real story is prepared, awaiting the user's script approval. The finished-asset mission remains active.**

The September 30 pull advanced `master` from `08ec13a` to `9c07f50` and introduced the [selection-to-production mission](SELECTION_TO_PRODUCTION.md). This checkpoint connects the native Easy News producer desk to Bearing's existing film machinery. The archival `easynews-reference` project was not inspected or used.

## The real editorial preparation

The live desk surfaced CNBC's report about the new federal support center for defaulted student loans (`event-a347e2e1848fea`, report `auto-bf2e58c53bb630`). The selected treatment is **In Focus**, with an explicit September 30 launch peg and a practical distinction: applying starts a process; it does not clear a default.

The independent primary check used [Treasury's September 30 launch announcement](https://home.treasury.gov/news/press-releases/sb0639/) and [Federal Student Aid's default guidance](https://studentaid.gov/articles/default/). The Treasury release was readable through its official indexed search result; its direct page open failed. Its date is verified, but no publication clock time is asserted. The official support-center destination was linked by Treasury; no borrower account, eligibility decision or application was tested. The 9.3 million default count refers to older quarterly data and is intentionally omitted.

The retained [preparation packet](SELECTION_PROOF_STUDENT_LOANS_20260930.json) contains the source review, exact supporting excerpts, proposed script and original picture/sound plan. It is a historical preparation snapshot, not a fresh source check or approval. The local selection ID is `selection-6fa7e2370b86374d3e57fb74`.

> Borrowers with defaulted federal student loans have a new online route toward repayment. Treasury and the Education Department launched a support center Wednesday. It lets borrowers compare rehabilitation and consolidation, upload documents and track progress. Applying is only the start. Borrowers still need to meet the requirements of their chosen path to leave default.

The 54-word script follows the maintained editorial voice. Planned pictures change with the job: an impact lead, a service explanation and a bounded closing. Options reveal left to right; a separate band accurately labels document upload and progress as rehabilitation tools. The closing supplies `StudentAid.gov/default-support`. All graphics and music are original; there are no borrowed images, footage, screenshots or logos. The plan retains measured narration and a 45-second maximum. A still contact sheet has been visually inspected, using illustrative timing only.

**No TTS, finished movie, final listening pass or new playlist item exists for this candidate yet.** The user was asked to approve the exact script for a preview, with no automatic publication. Do not infer approval from the engineering work or from `reviewStatus: verified`, which records only the assistant's accuracy/rights preparation.

## What now travels together

- Explicit product choice, why-now reasoning, producer note and the desk's opportunity context.
- Pinned intake report IDs, source URLs, source text and publication context, plus separately reviewed primary evidence.
- The cited opening/body/closing draft, visual intent, pronunciation notes, unresolved issues and maintained voice revision.
- An exact matching film packet and its accuracy, voice, picture and rights review.
- Named approval bound to script, sources, voice guidance and prepared packet hashes.
- A revision archive retaining selection, edits, holds, rejections, reassessment and production outcomes.
- On successful production, that lineage in the finished asset's `production.selection` record.

The assistant still had to read the primary material, choose the angle, write/edit the script and author its story-specific film packet. Those decisions are now retained rather than rediscovered by the renderer. The local-model drafting and editing prompts also accept the carried context, explicitly separated from factual evidence; the real candidate was assistant-authored, not a demonstrated local-model generation. Preparing primary evidence and the film packet currently uses the local API. This proof does not add a general media-planning interface.

## Operation

Open `/producer.html`, choose a live opportunity, and use **Prepare** in its existing decision area. Ranking tabs remain recommendations; the dialog's product selector is the explicit treatment choice. Review sources, edit the three script sections and citations, and save. A named reviewer can approve a saved, validated script with a prepared production plan, hold it, or reject it. **Produce preview** is available only for an approved live In Focus preparation. The Brief can be selected, but has no finished-film treatment in this proof and stays blocked from production.

The loopback-only, same-origin `/api/producer/handoff` endpoint reads one selection with `eventId` and `mode`. POST actions are `select`, `evidence`, `save`, `prepare`, `review`, `reassess` and `produce`. Updates require the current `expectedRevision`; stale requests receive HTTP 409. Supplemental primary evidence includes an explicit source check and review note. A primary recheck may replace its own reviewed ID but cannot replace an intake ID. Never refresh a check timestamp without rereading the source.

The production worker reuses the existing production lock, Kokoro, renderer, sound assembly and media validation. It calls `produce_film.produce(..., publish_result=False, completion_guard=...)`; successful previews return local film links without modifying `films.json`. Existing direct production callers retain their prior publication behavior. Runtime selection history lives under ignored `channel/production/runs/selections/`; run one server per checkout.

## Changed-reporting behavior and limits

Source wording, publication context, availability, inconsistent intake revisions or changed editorial guidance invalidate approval and require explicit reassessment. The check compares the pinned evidence directly, rather than trusting a desk ranking or materiality label. Reassessment retains the old draft for comparison but invalidates its validation, prepared plan and approval. Old citations must be checked against the adopted evidence before the draft can proceed.

Primary checks expire after one hour. They require an explicit reread/update followed by reassessment; reassessment alone cannot renew their timestamps. The same approval/evidence guard runs before rendering, before delivery, at final completion and on cached output. Holds and rejections can revoke a render in progress. A completed encode cannot override them.

The guard sees collected intake and maintained primary excerpts. It **cannot detect an unobserved change on an external page**. This is not a second news crawler or a claim of continuous remote-page fact checking. Source review and final editorial listening/viewing remain necessary.

## Verification at this checkpoint

- **168 Python tests passed**, including approval binding, evidence replacement/expiry, revision conflicts, changes during rendering, rejection during rendering, cached completion guards and preview-only assembly.
- **50 JavaScript tests passed**, including review/production eligibility, local preview links and preservation of script citations.
- Actual Chrome flow: selected the live loan opportunity; inspected its populated review dialog. In the isolated sample cycle, saved a cited draft, held and rejected it, advanced reporting from 10,000 to 40,000, and verified that stale saving/approval/production were disabled. Explicit reassessment adopted the new source; the old cited draft then failed validation. Unsaved edits survived a saved-state refresh; saved close/reopen retained the draft.
- Updated service/closing stills were visually checked; the six visual tests passed again after that adjustment. Actual voice, mix, movie decode and continuous playback remain untested for this new candidate.
- The existing player, accepted PCE/NIST media and playlist manifests were not edited.

Local browser screenshots, logs and illustrative picture sheets are in ignored `output/selection-proof/`. They are review evidence, not repository runtime dependencies.

## Exact continuation

1. Read the user's response to the pending script-approval question. A revision request requires revising the proposal, not assuming approval.
2. Before production, reread the primary sources and current intake. Replace reviewed evidence with actual check timestamps, explicitly reassess if required, resave the cited draft and prepare its exact matching film packet. Do not republish this September 30 preparation as current after its editorial window expires.
3. Record the actual approval and reviewer faithfully, then produce an unpublished preview through the selection endpoint/dialog.
4. Inspect narration flow, protected first word, music fit, cue ordering, dwell time, captions, full media decode and finished duration. Verify the resulting lineage and any preview/playback limitations. Keep accepted films intact.
5. Complete the mission handoff only after the real asset passes review; commit and push the proof, then stop. Do not expand the platform or render the rewrite library.
