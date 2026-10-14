# PLAN-V4 update U1 (user decisions 2026-10-14 12:50 JST), draft for 3-party agreement

1. **Pilot source**
   - Use only the tasks in `pilot-candidates.md` (real past requests from the chat-history DB, written by another bot). The roster is frozen as the first 10 eligible entries, in file order, under the existing scope rules. Ineligible entries are listed with their reason.
   - If fewer than 10 are eligible, N is what exists. The pass line becomes ceil(0.7·N) and is fixed before the trial.
   - Nothing is invented.
2. **Judge**
   - Step 1: an independent agent judge, Astra Max (`openai-codex/gpt-6-astra:max` via omp; to be confirmed). It scores each handed-over model against the pre-registered rubric, using the renders, the measured dimensions and the request text.
   - Step 2: the user visually double-checks. The user's verdict overrides. Both are recorded.
   - The rubric, the critical dimensions and tolerances, the first-handover fatal rule (critical dimension error or fabrication = fail), and "≥70% need no edits or ≤5-minute fixes" are committed before the trial.
3. **Cost**
   - No prices. The ledger and RESULTS report the % reduction for each token type versus a baseline. Proposed baseline: the matching v3 cohort (same route classes), per call and per episode.
   - Nulls propagate. The reduction is not computed when the baseline or the v4 value is null.
4. **Holdout authoring (option B)**
   - Author: **v4grok** (opencode-go/grok-4.7, herdr w6:p2). It writes 60 items, by the plan's stratum counts, to a private directory outside both worktrees: `C:\dev\v4-holdout-private\`.
   - It publishes only a SHA-256 commitment file into the repo.
   - Implementer v4codex and reviewer v4gemini never read that directory.
   - Release happens only after freeze. The run verifies the commitment.
   - Limitation: isolation is procedural, because all agents share one filesystem and instructions are the only barrier. RESULTS must state this.
   - Control review: v4gemini validates the released items only after the run inputs are hashed. This is recorded.
5. **Execution** goes via herdr w6 (omp agents), in the worktree `C:\dev\CAD-HARNESS-herdr`, branch herdr/v4.
   - Live calls must stay within budget #5 (203).
   - Overload handling follows #6.
   - Quota: consult at 55%, stop at 60% (`omp usage`, Codex 7-day).

## U1 addendum A: pilot selection (2026-10-14 12:59 JST)
- **Source:** `pilot-candidates.md`, 25 real requests from 13 primary conversations, 2026-07-24 to 10-05, extracted by another bot. sha256 63a39ed365324893df7615a83c17db5e217c1701d447594187a2360391910839.
- **Selection:** about 10 self-contained candidates, chosen by 3-party agreement. The candidate text is used verbatim; there is NO rewriting.
- **Exclusion criteria** are fixed in this addendum BEFORE selection. A candidate is excluded if:
  - E1: it depends on prior conversation context, such as "that one", "the previous part" or a selection.
  - E2: it depends on an attachment or existing geometry or file that is not inside the text.
  - E3: it is outside the current capability scope; there is no range expansion. Examples: assemblies, CAE, drawings-only requests, non-FreeCAD tools.
  - E4: it lacks the critical dimensions needed to judge it, and the missing dimensions cannot be asked through the existing clarification route.
  - E5: it is a duplicate or near-duplicate of a candidate already selected (the earliest one is kept).
- **Ordering:** candidates are considered in file order. The first 10 that are not excluded form the roster. If fewer than 10 remain, N is the count left and the pass line is ceil(0.7·N).
- **Record:** `pilot-roster.md` lists every candidate with selected or excluded and its criterion code. It must be signed by all 3 before the trial.
- **Judge:** Astra Max (user-confirmed), then the user's visual double-check.

## Revision 2 (after BLOCKs from sol and gemini, 2026-10-14 13:1x JST)
- **R2-1 (N=0):** if fewer than 1 candidate survives E1–E5, the pilot is `not_run`. There is no success fraction and no PASS, and no task is invented, rewritten or substituted. If N ≥ 1, the pass line is ceil(0.7·N) and this is fixed before the trial.
- **R2-2 (holdout sequence):** the steps run in this order:
  1. Lock the implementation and the skill.
  2. v4grok authors the holdout privately.
  3. v4gemini performs the control validation of requests, gold and native controls, without any generation calls. Defective or exposed items are retired.
  4. Commit the hashes and the final execution freeze.
  5. Release and generation.
  - Nothing scored is inspected or repaired during execution. Option B's procedural isolation limitation is stated in RESULTS.
- **R2-3:** the source count is corrected to 13 primary conversations. The candidate file itself is unchanged.
- **R2-4 (token baseline, from v4grok's BLOCK):**
  - Comparator: the v3 *retained scored* call set (88 calls, aggregate `-solfix-rerun2`), grouped by route class (spec, source, ask, completion, repair).
  - Formula, per token type and per route class: ratio of sums, reduction % = (1 − Σv4 / Σv3) × 100. The v4 side is the holdout's scored calls.
  - The 109 charged set is reported separately as context only and is not used for the reduction.
  - A route class missing on either side, or any null in a sum, gives a null reduction. Never 0.
  - Price fields stay null with a reason. The reduction is an added derived field.

## Revision 3 (after the R2 BLOCKs from sol and v4grok)
- **R3-1 (supersedes the R2-4 grouping):**
  - Group by the aggregate's own `route` field: source, spec, ask, completion, mvp, offline. There is no separate repair route; repair-stage calls stay inside their episode's route.
  - All 88 retained calls are included exactly once.
- **R3-2 (zero baseline):** if Σv3 = 0 for a token type and route, the reduction is null with reason `zero_baseline`. This holds even when Σv4 = 0. Nothing is ever divided by zero.
  - Example: `cache_write_input_tokens` is 0 on every v3 episode that has token records, so its reduction is null with `zero_baseline`.
- **R3-3:** in U1 §4, the sentences "v4gemini never read that directory" and "validates the released items only after the run inputs are hashed" are **SUPERSEDED** by R2-2.
  - v4gemini receives a pre-freeze review copy only after authoring is done, and validates it before the hash commit and the freeze.
  - The implementer v4codex never reads the review copy or the private directory.

## U1 addendum B: pilot reopening (user decision 2026-10-14 13:36 JST) - DRAFT for 3-party sign
User decision: request text stays verbatim; the ORIGINAL conversation context and attachments (from history.db / the jsonl paths in pilot-candidates.md) are supplied. This supersedes E1/E2 of addendum A and the N=0 not_run of pilot-roster.md (that roster is kept as history, not overwritten).
- **B1 context:** a deterministic CLI extracts, from the candidate's listed jsonl (read-only), the user and assistant message texts of the same conversation strictly BEFORE the request locator, verbatim, in order. Tool calls and tool outputs are excluded. Window: the most recent turns that fit in 40,000 characters, cut at message boundaries; the cut is recorded. The extract is hashed and frozen before the trial. Missing or unreadable jsonl means exclude (E6).
- **B2 attachments:** every file, folder or geometry the request or the context window references must exist now at that path and be readable. It is copied into an immutable pilot bundle and hashed before the trial. If any required attachment is missing, the candidate is excluded (E7). Nothing is reconstructed or substituted.
- **E3, E4, E5 stay unchanged.** E3 also excludes requests whose deliverable must be a Fusion, SolidWorks or other non-FreeCAD native file, or an assembly, CAE or drawing-only output. FreeCAD 1.1.4 headless on DPC-019 only.
- **No rewriting:** the request, context and attachments are passed as typed runtime data. There is no paraphrase, summary or added instruction beyond the frozen skill.
- **Selection:** file order; the first 10 that are not excluded; each of the 3 screens independently, and disagreement means exclude. If fewer than 10 remain, N = the remaining count. N=0 means not_run.
- **Pass criteria, fixed before the trial:**
  - Per-task critical dimensions and tolerances are taken only from the request or context text and agreed by the 3 parties. They are committed in pilot-rubric.json.
  - A task passes when its first handover needs no edits, or needs fixes of 5 minutes or less.
  - Any critical dimension error or fabrication is a fail.
  - The pilot passes when at least ceil(0.7×N) tasks pass.
  - Judge: Astra Max (`openai-codex/gpt-6-astra`, thinking max, via omp), then the user's visual double-check. The user's verdict overrides.
- **Order and budget:** the pilot runs after the holdout and uses the same frozen implementation, with 40 calls at no more than 4 per task.
