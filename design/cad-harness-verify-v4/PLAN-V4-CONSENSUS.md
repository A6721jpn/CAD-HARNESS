# VERIFY v4 CONSENSUS PLAN — DRAFT

2026-10-14. Synthesis of [BRIEF](BRIEF.md), [Codex](plan-r1-codex.md), [Grok](plan-r1-grok.md) and [Gemini](plan-r1-gemini.md). Three-party approval is pending; this document authorizes no execution, spending or freeze.

The order is **cost ledger → skill/CLI consolidation → fresh holdout → real design pilot**. Holdout and pilot answer different questions and run sequentially. Preserve v3 reports and its final result: 60/60 PASS after rerun2, 88 calls in retained scored segments, 109 total charged calls including archived work. Neither the repaired history nor an overload-free run establishes blind reproduction or overload recovery.

## 1. Phases and deliverables

| Phase | Deliverables | Completion condition |
| --- | --- | --- |
| 1 — cost ledger | Versioned ledger schema, streaming capture, usage/time collector for every route including geometry, pricing adapter, historical v3 backfill and reconciliation report | Every discoverable invocation and interruption is represented; missing evidence is explicitly null. Call/episode/run totals reconcile, with completeness reported independently of known subtotals. Historical files remain unchanged. |
| 2 — skill and CLI | New v4 skill bundle, one request entry point, thin batch adapter, deterministic ledger/aggregate commands, minimal mocked regression checks | One invocation owns routing, generation, verification, export/reimport and recording. Recorded/mocked responses exercise the whole request path. Existing scoring predicates, gold interpretation, tolerances, order and gates remain unchanged. |
| 3 — fresh reproduction | Independently authored sealed cohort, one manifest, fixed order, one process/segment and immutable result bundle | Execute the complete cohort once without interim outcome inspection, fixes, restart, resume, substitutions or retakes. Evaluate only the pre-frozen gates. An interrupted run is INCOMPLETE. |
| 4 — real pilot | User-supplied requests, pre-registered acceptance cards/rubric, human judgments, edit and adoption evidence | At least 7 of 10 enrolled tasks are adopted with no edits or verified corrections within 300 elapsed seconds; no critical dimension error or fabrication in a handed-over result. |

**Phases 1–2 require zero live model calls and no pending user decision.** Implement nullable pricing, empty holdout/pilot inputs, the policy interfaces and all collectors with existing records and mocks. Do not add a live smoke, invent pilot tasks, obtain rates independently or expose candidate holdout items to prove implementation. Mock fixtures are development evidence only. Missing rates may remain null even in later phases; missing holdout custody, live budget, clock agreement or pilot prerequisites block only the corresponding live phase.

After plan consensus: implement phases 1–2, obtain implementation/policy reviews, settle applicable live decisions, then freeze. Bind code, skill, policy, host, data commitments, order, budgets and applicable rubric before execution. Keep the same implementation through holdout and pilot. Obtain three-party RESULTS review afterward. Follow the brief's commit/push policy during that later work; never commit `reports/` or `.tmp/`, force-push or overwrite historical evidence.

## 2. CLI and file layout

Use one new evaluator facade rather than several competing entry points or a rewritten driver:

| Path | Role |
| --- | --- |
| `tools/eval_verify_v4.py` | `ledger`, `preflight`, `freeze`, `request`, `run`, `aggregate`; batch execution calls the same request path |
| `tools/cad_verify_v4_agent.py` | Thin model/runtime adapter with streaming capture and the v4 clock policy; reuse existing execution/verification helpers |
| `tools/cad_verify_v4_ledger.py` | Append-only journal, usage reconciliation, billing-category calculations and derived summaries |
| `tools/test_verify_v4.py` | Focused mocks and recorded-response equivalence checks; no new modeling features |
| `skills/cad-harness-v4/SKILL.md` and contract resources | Frozen modeling/verification, P/R, clarification, resend and logging instructions; move existing inline contracts here |
| `design/cad-harness-verify-v4/{policy.json,ledger.schema.json,pilot-rubric.json,SHA256.json}` | Machine-readable policy/schema, pre-registered rubric and final execution commitments |
| `reports/<unused-v4-run-id>/` | Manifest copy, ledger JSONL, actual submitted payloads, complete per-attempt streams, artifacts and derived JSON/CSV |

Proposed interfaces below describe future commands, not commands executed by this draft. Paths in angle brackets are supplied inputs.

```text
python -B tools/eval_verify_v4.py ledger --source-root reports/cad-run --history v3 --run-dir reports/verify-v4-v3-backfill
python -B tools/eval_verify_v4.py preflight --policy design/cad-harness-verify-v4/policy.json
python -B tools/eval_verify_v4.py freeze --policy <policy> --holdout-commitment <commitment> --run-dir <unused-freeze-dir>
python -B tools/eval_verify_v4.py request --request <request.txt> --acceptance <private-checker-card.json> --manifest <manifest.json> --run-dir <unused-request-dir>
python -B tools/eval_verify_v4.py run --phase holdout --manifest <manifest.json> --sealed-input <custodian-input> --run-dir <unused-holdout-dir>
python -B tools/eval_verify_v4.py run --phase pilot --manifest <manifest.json> --tasks <user-roster> --run-dir <unused-pilot-dir>
python -B tools/eval_verify_v4.py aggregate --manifest <manifest.json> --holdout <holdout-dir> --pilot <pilot-dir-or-not_run> --run-dir <unused-summary-dir>
```

All output directories are exclusively created. There is no holdout `resume` or `rerun` command. Reuse existing record, guard, probe and aggregate/scoring helpers through adapters; retain v1–v3 behavior and files. Scoring remains deterministic CLI work. `policy.json` is a checked machine representation of generic skill policy, not a second independently editable set of rules. Gold and private acceptance cards are checker inputs only.

The submitted instruction text consists of the original request bytes and frozen skill bundle. Preserve existing modeling prose; consolidate contracts without rewriting capabilities. Genuine answers, prior outputs and measured diagnostics needed by existing P/R/completion are typed runtime data under fields defined in that skill. They contain no extra imperative wrapper prose, gold or corrected fixture source. Record the actual envelope and hashes for every route. This interpretation preserves the request-plus-skill instruction boundary without deleting the existing feedback protocol.

## 3. One ledger: null is not zero

Use `cad-harness.ledger.v4` append-only JSONL, journaling operation start before launch and completion afterward. Attempt, wait, interruption, CAD, edit, episode and run events share linked IDs. JSON/CSV summaries are derived from this journal, never independent counters.

| Field group | Required content |
| --- | --- |
| Identity | Schema version; run, phase, episode, route/stage, logical-call, physical-attempt and retry-parent IDs; manifest, code, skill, request, CLI, model, host and FreeCAD identities |
| Transport/evidence | UTC endpoints; monotonic endpoints and boot identity; typed error, exit/session IDs, output-presence classification; submitted bytes/argv hashes; stdout/stderr paths, SHA256 and byte counts |
| Accounting | Physical attempts, charged accepted calls, exempt overload attempts, P/R usage and CAD attempts separately; charge decision/evidence; provider billing status independently nullable |
| Usage | Nullable input, cached-input, cache-write, output and reasoning token counts; event/session source references, final/cumulative semantics and per-field missing reasons |
| Time | Physical-call elapsed, full episode/run elapsed, model/CAD intervals, requested/actual backoff, quota/operator interruptions, human edit and re-verification intervals; active-budget time separately |
| Price | Nullable amount/currency; product/model/tier; user-supplied source, effective date and source hash; billing categories, quantities and rates; status `unknown`, `verified_rate_estimate` or `invoice_actual`; missing reason |
| Pilot | User ticket/card and human judge IDs; adoption; first/final artifact hashes; edited parts/dimensions/features, before/after values and source diff; edit duration; critical/fabrication flags; judgment evidence |

For each numeric field, a complete sum is null if any required contribution is unknown. Also report `known_subtotal`, expected/known/missing counts and reasons. A verified empty stream has zero bytes; a missing historical stream has null bytes/path with a reason. Missing usage is not zero tokens, no observed rejection is not missing rejection data, and an unrun pilot is `not_run`, not a successful zero-task trial.

Capture **complete stdout and stderr for every attempt directly to disk**, including rejection, timeout and failure. Bound only in-memory/display tails. Historical truncation is disclosed rather than repaired with invented bytes. A new capture/storage failure stops the run with incomplete evidence.

Deduplicate usage by event/session identity; do not sum cumulative snapshots. Preserve the five token measurements without assuming their billing categories are disjoint. Apply only documented rate semantics: cached input and reasoning may already be subsets. A missing non-billed diagnostic field need not invalidate an otherwise fully supported estimate, but every required billing quantity must be known. Use decimal arithmetic. An overload exemption from the harness cap does not establish a free provider invoice.

**Price defaults to null unless the user supplies an applicable rate source.** Record its product/model/tier/currency/date and distinguish estimates from invoice cost. Do not substitute another product's API prices, a reference-equivalent model or an invented hourly rate. Missing rates do not block token/time measurement or quality assessment.

Full elapsed time includes backoff, interruptions and editing. Use monotonic intervals within one boot; preserve UTC evidence and uncertainty across restarts. Do not subtract downtime, add overlapping intervals twice or fabricate interrupted endpoints. Report scored-segment cost and all-work cost separately. Backfill v3's retained 88 versus total charged 109 without making the scored aggregate stand for historical expenditure.

## 4. Fresh holdout and blindness

Recommend **60 fresh items, core 51**, preserving the v3 allocation, frozen family order and private scoring aliases. Replace content, not rules:

| Stratum | Count | Existing gate retained |
| --- | ---: | --- |
| Unscored previews | 3 | Existing preview contracts; outside the bar |
| Legacy / MVP analogues | 4 / 10 | Legacy 4/4; MVP at least 8/10 and each family at least 1/2 |
| Source families | 10 | At least 8/10, each of five families at least 1/2, actual fallback |
| Complex / stock / defaults | 3 / 5 / 3 | At least 2/3, 4/5, 2/3 respectively |
| Clarification | 10 | Each case at least 4/5; zero critical invention |
| Completion, outside bar | 6 | Existing question/answer/completion gates; reported separately |
| Designated faults | 6 | Establish/detect 6/6; final at least 4/6, each case at least 1/2, source and spec R success |

Retain all geometry, editability, native/export/reimport, tolerance, no-false-pass and P/R/CAD predicates. Keep existing natural/parse/completion-repair denominators separate from forced faults. Zero eligible observations means UNVERIFIED; never add faults or tasks to improve a denominator.

The user appoints an independent author, separate analytical/native-control reviewer and custodian. Lock implementation and skill before they author the cohort. They validate fresh requests, analytic gold and native controls without running the generation model. Reject exposed v1–v3 tasks, rewordings and scalar-only mutations; use new arrangements within the existing capability classes. Hash inequality alone does not prove novelty.

Keep plaintext requests/gold/controls outside the implementation workspace and generator's readable files; publish only schema, strata, order and cryptographic commitments. A shared folder labeled private is insufficient. The custodian supplies an immutable, commitment-checked bundle to a checker process; each isolated generation invocation sees only its current request, skill and permitted runtime facts. It cannot browse future items or gold. Record identities, access disclosures and reveal times.

If author validation finds a defect, return to development before the final freeze and retire any exposed candidate material. After launch there is one manifest, one process/segment and no change or replacement. During execution expose only quota, budget, capture health and liveness; seal model output, gold and scores until termination. An operator consultation/restart breaks the uninterrupted claim; automatic frozen-policy overload backoff does not.

## 5. Real pilot and rubric, registered before trial

Pilot tasks come **only from the user**, with real-work provenance. Recommend ten consecutive eligible requests from the user's backlog; pre-register eligibility exclusions and retain the screening log. No catalog exercise, synthetic request or planner-created example substitutes for missing work. If the user supplies no tasks, record `not_run`.

Before the first trial, commit the roster/order and request hashes, owner/human judge, critical dimensions and tolerances, allowed defaults, task routes/caps, quality checks and rubric. Bind these commitments in the execution manifest; if unavailable at freeze, the planned pilot is `not_run`, with later enrollment requiring a separately authorized trial rather than alteration of that manifest.

A successful task is human-adopted, passes existing checks, and needs no edit or completes corrections plus headless re-verification within **300 elapsed seconds from first edit**. Include waits during that correction interval; record initial generation wait in full task elapsed. Also record active edit time and the amount changed. Unstarted, failed, declined, non-adopted and unassessable enrolled tasks remain non-successes in the denominator of ten. Pilot PASS requires at least seven successes.

Any critical dimension error or fabrication in the **first proposed handover or a later handed-over artifact** irreversibly fails that task and the pilot, even if corrected within five minutes. Internal repair candidates remain governed by existing repair gates; designated internal faults are not reclassified as pilot handovers. Pre-register this detection point and the human's interpretation before trial. Do not invent a universal tolerance, an extra perturbation test or new editability gate. A fatal quality flag remains visible; continue the remaining fixed roster for complete measurement unless an independent operational stop applies.

The named human makes adoption and critical/fabrication judgments; no LLM surrogate signs off. Human edits are recorded source/native-parameter changes followed by existing headless checks on **DPC-019, FreeCAD 1.1.4**. No GUI workflow, other CAD product, CAE or shape/capability expansion is introduced.

## 6. Call budget, clocks and stops

Propose a new authorization of **203 charged accepted calls**, separate from historical v3 expenditure:

| Reservation | Maximum |
| --- | ---: |
| Phases 1–2, historical backfill, mocked development | 0 live calls |
| Fresh holdout | 163 |
| Real pilot | 10 × 4 = 40 |
| Total | 203 |

Holdout derivation: source 14×4 + supported spec 13×3 + clarification 10×1 + completion 6×4 + MVP 10×3 + previews 4 = **163**. Freeze each pilot route/cap at at most four; unused capacity is not automatically transferred between phases. No separate smoke, retake, overload hunt or contingency allowance. Until the user authorizes a live allowance, the authorized new live budget is zero. This does not prevent phases 1–2.

Charge every non-exempt invocation, including unsuccessful/aborted work; conservatively reserve a slot if its charge classification is uncertain. Record both scored work and all charged work, including any abandoned run. Physical attempts and provider billing are separate from this cap.

Honor the standing **2026-10-13 16:39 rule**: a structured `codex_error_info=server_overloaded` with verified no final/assistant output is recorded separately, consumes neither an accepted-call slot nor P/R, waits the full **600 seconds**, then resends the byte-identical submitted call. There is **no overload retry cap**. Preserve prompt/context/argv/model/options bytes; per-attempt capture metadata must not alter the call. Other errors or output-bearing failures do not receive this exemption. An overload rejection is never itself a scored, harness or abnormal failure.

The previous inclusive 450-second stage clocks cannot contain a mandatory 600-second wait. **Draft clock recommendation:** retain numeric active-work limits (episode 900 seconds, initial/repair 450, existing P/R/CAD sublimits), but exclude a verified provider-unavailability cycle—the rejected attempt and its mandatory backoff—from all enclosing active deadlines. Do not reset remaining active time or P/R/CAD slots. Charging rejected-attempt transport time against those deadlines would create an indirect overload cap, so record it as unavailable time too. Count every second in full operational wall time. There is no suite wall deadline; overload can extend wall time without bound. This is an explicit proposed timing amendment requiring confirmation before live freeze, not a claim that v3's inclusive timing already complies. Implement and mock this policy in phase 2; never silently clip the wait to a stage deadline.

Before each admitted call check manifest/host identities, remaining reservations and a fresh quota snapshot. **55%: consult and admit no new calls pending a reply; 60%: hard stop.** Missing/stale quota also stops. Explicit cancellation, quota and capture/host failures remain independent stop causes during backoff; record an interrupted wait and INCOMPLETE run without inventing a successful resend. Ordinary episode/quality failures remain scored and execution continues. Active-work exhaustion uses existing episode failure handling, never an overload-specific harness failure.

Stop the run on capture failure, identity/order mismatch, holdout leakage/intervention, uncontrolled CAD cleanup, invalid scoring evidence or exhausted call authorization. Preserve charged calls, raw evidence and unstarted entries; never extend a ceiling or fix/re-take exposed items to obtain PASS. A pilot fatal quality verdict follows the reporting rule above rather than authorizing substitutions.

Live overload robustness requires evidence of an actual rejection → full wait → identical resend → accepted response. A rejection alone proves no recovery. No rejection means **UNVERIFIED**, even if mock retry tests pass; do not provoke an overload to fill this gap.

## 7. Conflicts resolved in this draft

| Conflict | Resolution and reason |
| --- | --- |
| Gemini parallel holdout/pilot versus ordered phases | Sequential phases 1–4, as the user requires. Practical usefulness does not bypass reproduction. |
| Grok 57 items versus Codex/Gemini 60 | Retain 60, including three fresh unscored previews, to preserve the complete v3 allocation and entry-path coverage. Public dev previews are not fresh evidence. |
| Grok 201 / Codex 203 / Gemini 220 calls | Recommend 203 = 163 + 40. Remove Grok's two live smoke calls and Gemini's 17-call contingency; exempt overloads need no accepted-call reserve. No forecast of actual token/call consumption is invented. |
| Existing skill edits, multiple new drivers, CLI-only policy text | New frozen v4 skill and one facade; preserve old skill/results and reuse execution/scoring helpers. Skill contains generic rules; CLI executes their checked machine representation. |
| Request-only initial prompt versus later feedback prose | Keep original request/skill instructions and frozen typed factual feedback. No ad hoc repair instructions or checker gold enter context. |
| Tail-only capture versus full streams | Full disk streams, bounded memory/display only. Missing historical capture remains unknown. |
| Example/reference-model prices versus missing rates | Discard all illustrative prices, usage and latency figures. Applicable user-supplied source or null with reason; avoid cache/reasoning double billing. |
| Assigned AI author and shared-tree holdout versus independence | User appoints author/reviewer/custodian; seal outside implementer/generator access after code lock. No planner self-appoints. |
| Catalog/synthetic pilot, GUI edits, agent judgment, adoption as annotation | User requests only; recorded headless edits; human judgment; adoption is required for a successful task. Keep all enrolled tasks in the denominator. |
| Inclusive stage deadlines versus uncapped 600-second resend | Propose explicit unavailable-cycle exclusion from active clocks, preserve full wall accounting, and require confirmation before live freeze. No clipped-wait fallback. |
| Pilot fatal error stopping evidence collection versus fixed roster | Fatal handover error fixes the pilot verdict to FAIL; remaining tasks continue only under unchanged operational safeguards and budgets. |

Report cost-evidence completeness, price knowledge, CLI consolidation, fresh reproduction, pilot usefulness and overload recovery as separate verdicts. One successful category never fills another's missing evidence.

## USER DECISIONS REQUIRED

These decisions affect live execution; **none blocks implementation or offline acceptance of phases 1–2**. Defaults below apply while answers are pending; recommendations are proposals, not approvals.

| Decision | Pending default | Recommendation |
| --- | --- | --- |
| Which real pilot tasks and owners? | No user tasks means `not_run`; never invent replacements. | User supplies ten consecutive eligible real backlog requests, acceptance owners and provenance before roster/rubric commitment. |
| Which rate source applies? | All unsupported prices remain null with reasons; token/time collection continues. | User supplies the actual product/model/tier billing source, currency and effective date. Record sourced estimates separately from invoice actuals. No price decision is required merely to run with unknown cost. |
| Who authors/reviews/custodies the unseen holdout, and how is access isolated? | No sealed, independently validated cohort means holdout `not_run`; use only old records/mocks for development. | Name an independent author and separate control reviewer; user-appointed custodian keeps plaintext outside implementation/model access and releases commitment-verified inputs only after code lock/freeze. |
| What is the total live call authorization? | Zero new live calls; no inherited v3 allowance. | Authorize at most 203 charged accepted calls, reserved 163 holdout + 40 pilot, with no automatic borrowing or extensions. Approve any reduced scope before freeze rather than trimming after outcomes. |
| How does mandatory overload waiting interact with stage clocks? | Standing rule remains 600 seconds + identical resend, uncapped and unscored. Implement/mock the proposed active-clock policy; no live freeze under contradictory clock rules. | Confirm exclusion of verified rejected-attempt/backoff cycles from enclosing active budgets, numeric work limits unchanged, full wall time recorded and no suite deadline. Independent quota/cancellation stops remain explicit. |
| Who judges the pilot and signs its rubric? | No named human/rubric agreement means pilot `not_run`; no agent substitute. | User/owner names the human judge and commits critical dimensions, tolerances, first-handover fatal-error rule, adoption requirement and 7/10 with ≤300-second verified corrections before trial. |
