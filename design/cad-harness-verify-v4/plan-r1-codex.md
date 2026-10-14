**VERIFY v4 PLAN proposal — codex, 2026-10-14. Not an execution authorization.**

Recommendation: follow the [brief](BRIEF.md)'s order: cost ledger → skill/CLI consolidation → one fresh blind run → real-work pilot. The [committee](COMMITTEE-CONCLUSION-20261014.md) prioritizes REAL_PILOT for usefulness and FRESH_HOLDOUT for evidence; neither substitutes for the other. [v3 RESULTS](../cad-harness-verify-v3/RESULTS.md) and [RERUN2 RESULTS](../cad-harness-verify-v3/RESULTS-RERUN2.md) establish the baseline: final 60/60 PASS, retained-segment calls 88, total charged calls 109, but post-result substitutions and no observed overload recovery. Preserve both histories unchanged. All allocations below are proposals, not measured outcomes or price quotations.

**1. Deliverables and order**

| Order | Concrete deliverable | Acceptance |
| --- | --- | --- |
| 1: measurement | Append-only attempt/event ledger; complete stdout/stderr capture; token, elapsed-time and price reconciliation; rate-card provenance | Every invocation, rejection, wait, CAD attempt and interruption is accounted for, including unsuccessful work. Missing fields remain null with reasons. Geometry uses the same collector as other routes. Report token/pricing completeness separately from known subtotals. |
| 2: consolidation | Frozen skill bundle and one CLI facade around existing compiler, CAD execution, probes and scoring | One request invocation returns artifacts or an explicit incomplete/unsupported result. Input traces prove no additional instructional prose. Existing recorded-answer/native-control checks retain identical gates and outcomes; no capability additions. |
| 3: reproduction | Independently authored sealed cohort; one committed manifest/order/rubric; one unattended execution and independent aggregate | Complete the fixed cohort once, with the unchanged per-stratum bar, no mid-run inspection, code/skill changes, restart, replacement or retake. Failure/early stop remains the result. |
| 4: pilot | Ten genuine requests, owner-approved acceptance cards, adoption/edit/time records and final report | At least 7/10 adopted with no edits or verified fixes within 300 seconds; no critical dimension error or fabrication. All enrolled tasks remain in the denominator. |

Finish three-party plan consensus before implementation. Develop using separate dev data and recorded/mocked transport only; review implementation and policy equivalence before sealing the run. Freeze code, skill, data commitments, rubric, order, budgets and rate-card identity together. Run holdout before pilot, with no implementation changes between them. Seek three-party RESULTS consensus afterward. Every logical commit is immediately pushed; no force push and no `reports/` or `.tmp/` committed. This proposal itself performs no commit/push.

**2. File and CLI layout**

| Location | Responsibility |
| --- | --- |
| `skills/cad-verify-v4/SKILL.md` plus frozen contract resources | Generic modeling, verification, repair, resend and logging rules; schema/output contracts. No item-specific gold, expected answers or correct source. |
| `tools/cad_v4.py`, `cad_verify_v4_agent.py`, `cad_verify_v4_ledger.py` | Single facade, thin request/stage adapter, streaming capture/ledger/pricing. Reuse existing deterministic compiler, headless CAD runner, probes and scoring helpers; retain v1–v3 behavior/results. |
| `tools/test_verify_v4.py` | Minimal mocks: payload identity, complete-stream capture/usage deduplication, null/pricing reconciliation, retry/quota/budget boundaries. Reuse existing regression checks; no new modeling feature tests. |
| `design/cad-harness-verify-v4/` | Signed plan, machine policy/schema, rate-card provenance, pilot rubric, public cohort commitments/order, freeze and RESULTS documents. Sealed test content is held separately by its custodian. |
| `reports/<fresh-v4-run-id>/` | Request/skill hashes, manifest, ledger, per-attempt raw streams, CAD artifacts, human edits and derived JSON/CSV. Exclusive creation; local artifacts only. |

Proposed facade subcommands: `preflight`, `freeze`, `request`, `run --phase holdout|pilot`, `aggregate`. Normal entry: `python -B tools/cad_v4.py request --input request.txt --acceptance acceptance.json --manifest manifest.json --run-id UNUSED`. That invocation owns routing, execution, verification, export/reimport and recording; acceptance data is private to the checker. Batch `run` calls that same path, not a second generation implementation.

The user-message bytes are the original design request; instructional context is exclusively the frozen skill bundle. Move inline contracts into that bundle rather than re-injecting them as wrapper prose. Existing output/diagnostic data needed for P/R and genuine clarification answers require the explicit protocol decision below; gold and fixture source never enter model context. Save actual submitted bytes/hashes for every route, not reconstructed text.

**3. One ledger, with explicit unknowns**

Use `cad-harness.ledger.v4` JSONL, journaled before launching each operation. Derive episode/run summaries and CSV from this ledger; do not maintain competing cost counters.

| Record scope | Required fields |
| --- | --- |
| Identity | `run_id`, phase, episode ID, route, stage/purpose, logical-call ID, physical-attempt ID, parent/retry ID; manifest/code/skill/request/CLI/model/FreeCAD/host identities |
| Transport | UTC and monotonic start/end, boot/clock identity, exit/error, exact typed error code, session/request IDs, final/assistant-output presence, request/context/argv hashes, stdout/stderr paths + SHA256 + byte counts |
| Accounting | Physical attempts, accepted/unknown charged attempts, model slots and P/R slots separately; `provider_rejected`, guard charge, provider billing status and evidence. Guard-exempt does not imply a zero provider invoice. |
| Usage | Input, cached-input, cache-write, output and reasoning tokens individually nullable; raw event reference, source and missing reason. Deduplicate session/event usage; do not add cumulative snapshots or double-charge reasoning/cache subsets. |
| Time | Full request-to-terminal elapsed time, model/CAD intervals, requested/actual backoff, quota/operator interruptions and human edit intervals. Unknown interrupted endpoints remain null. |
| Money | Currency, applicable model/product/tier, rate-card hash, source URL/document and effective/observed dates; billing-category quantities/rates, amount, status `verified_rate_estimate|invoice_actual|unknown`, missing reason |
| Pilot | Owner/card ID, adoption, first/final artifact hashes, critical/fabrication flags, changed dimensions/features/source diff, edit start/end, active edit time and verification result |

Stream complete raw stdout/stderr to disk for every attempt, including failures/timeouts; bounded in-memory tails are only a display aid. Never silently truncate the archival stream. A capture/storage failure stops safely and marks evidence incomplete.

Count waits and interruptions in operational elapsed time. Use monotonic intervals within a boot and UTC endpoints across interruptions, flagging clock changes; do not subtract downtime or invent durations. Do not sum overlapping categories into a false run total. A missing usage/rate component makes its complete total null; also report known subtotal and missing/expected counts. A documented actual zero remains zero. Use decimal money arithmetic and billing-category semantics from the applicable source. An API list-price estimate must not masquerade as actual Codex subscription/credit cost; absent a matching source, price is null with a reason. Human monetary cost is also null unless an hourly rate is supplied. Ledger completeness and `full_cost_known` are separate verdicts.

**4. Holdout authoring and unseen execution**

Lock the implementation/skill commit before independent authors create test content. Assign an author and separate analytical/native-control reviewer who do not tune the implementation. A user-appointed custodian holds plaintext gold, requests, answers and controls outside the implementation/model workspace; publish only hash commitments and strata/order. Shared workspace folders alone are not a blindness guarantee. Disclose author access; prevent generator/implementer access until execution, and reveal each request only to its isolated model invocation. Reviewers may validate sealed analytic gold and native controls on DPC-019 without showing results to implementers.

Reject v1–v3 rewordings, scalar-only mutations and previously model-tried tasks. Author new arrangements within existing shape/capability classes. Old regression fixtures are preflight evidence, not fresh scored observations. Proposed cohort retains the v3 allocation and gates, using fresh item identities and private scoring aliases:

| Stratum | Episodes | Unchanged pass gate |
| --- | ---: | --- |
| Unscored previews | 3 | Existing preview contracts; excluded from bar |
| Fresh legacy and MVP analogues | 4 + 10 | Legacy 4/4; MVP at least 8/10 and each family at least 1/2 |
| Source families | 10 | At least 8/10, each of five families at least 1/2, actual fallback |
| Complex / stock / defaults | 3 + 5 + 3 | At least 2/3, 4/5 and 2/3 respectively |
| Clarification | 10 | Each of two cases at least 4/5, zero critical invention |
| Completion, outside bar | 6 | Existing question/answer/completion gates, reported separately |
| Designated faults | 6 | Establish/detect 6/6; final gates at least 4/6, each case at least 1/2, source and spec R success |

Total 60, core 51; preserve geometry/editability/native/export/reimport predicates, tolerances, P/R/CAD limits and no-false-pass requirements. Fresh gold values are derived independently, never fitted to generated output. If author validation exposes a code/rule defect, retire affected candidate data, fix on separate dev data, and commission fresh replacements before the one final execution manifest. Once launched, expose only operational quota/log-health status, not case outcomes. Seal results until termination. An interrupted/fixed/restarted run is INCOMPLETE, not blind PASS; no automatic retry experiment or substitution command.

**5. Real-work pilot and pre-registered rubric**

Request ten consecutive eligible real tickets from the user's actual backlog, with provenance and an owner available to judge adoption. Register scope exclusions before enrollment and retain the screening log; do not hand-pick successes or substitute synthetic benchmarks if requests are unavailable. Commit all ten request hashes, routes/caps, critical dimensions/tolerances, allowed defaults, rubric and order before the first pilot invocation.

A task passes only if its owner adopts an artifact meeting every existing quality gate, with no human edit or with corrections and re-verification completed within 300 elapsed seconds from first edit. Record active editing separately; verification/waits during correction count toward that interval, while initial generation wait remains in total task time. Record what changed, before/after values and artifact/source diffs. Human changes use recorded source/native-parameter edits followed by headless verification on DPC-019, not a different CAD product. Failed, unstarted, declined or unassessable enrolled tasks are non-successes out of ten. Any critical dimension error or invented design fact beyond frozen defaults is fatal to that task and the pilot verdict, not recoverable by a five-minute edit; agree the detection stage explicitly before trial. No LLM judge replaces owner sign-off.

Observe natural, completion and parse repair in their own eligible/invoked/success denominators, fixed before outcomes. Forced faults never enter those denominators. A zero denominator means UNVERIFIED; do not add cases or inject failures to make it positive.

**6. Call budget and stop rules**

Propose a new v4 authorization of **203 charged model calls**: offline preparation 0; holdout maximum 163; pilot maximum 10 × 4 = 40. Derive holdout 163 from the existing route caps: source 14×4 + supported 13×3 + ask 10×1 + completion 6×4 + MVP 10×3 + preview 4. Freeze each pilot route/cap, reducing its reservation for smaller routes. No additional live cost-smoke or overload-hunting calls. The historical v3 109 is retained in history, not reset or hidden; 203 is a proposed new allowance requiring approval, not an inherited entitlement. No phase borrows another's reservation automatically.

Exact structured `server_overloaded` with verified no output: uncharged model/P/R slot, record every attempt, wait 600 seconds and resend identical call bytes, without an overload-attempt cap. Other errors/output-bearing failures receive no transport retry and remain charged. Actual rejection-to-accepted-response evidence is required for live robustness PASS; no rejection means UNVERIFIED. Mock rejection tests establish only implementation behavior.

Before each invocation verify frozen identities, DPC-019, FreeCAD 1.1.4 headless, remaining calls and fresh quota. At 55% consult and stop new calls pending an answer; at 60% hard stop. Missing/stale quota also stops. A consultation/cancellation/process restart invalidates the uninterrupted-holdout claim; automatic frozen-policy backoff alone does not. Ordinary case gate failures remain in the cohort and execution continues; hash/order leakage, capture failure, false pass, uncontrolled CAD cleanup or a fatal pilot error stops safely. Keep all charged work and unstarted entries. Never overwrite reports, extend caps, change thresholds or fix/re-take exposed test items to obtain PASS.

**7. Decisions required before live execution**

| Decision | Recommendation and safe action while unanswered |
| --- | --- |
| Who supplies ten real requests and acceptance ownership? | User supplies backlog/owner and names an independent holdout custodian. Continue offline work; pilot remains NOT RUN, not replaced with invented tasks. |
| Approve 203 calls and pricing basis? | Approve explicit phase reservations and provide the applicable billing source/currency. Unknown prices stay null. If only 163 total is authorized, do not promise both worst-case cohorts; revise scope before freeze, never silently increase spend. A hard money cap needs a defensible pre-call cost bound or no launch. |
| Does request-plus-skill allow runtime data? | Allow prior outputs, actual CLI diagnostics and genuine answers as typed data under the frozen skill, with no extra instructions. If the literal restriction excludes this data too, existing P/R/completion cannot be preserved; resolve before implementation of that interface, not through hidden prompt additions. |
| How can 600-second backoff coexist with existing clocks? | Current v3 includes waits in 450-second stages/900-second episodes; a 600-second wait cannot fit. Recommend an explicit operational amendment excluding only verified provider backoff from active stage budgets while recording every wall second. This is a timing change requiring approval. Until then retain existing clipping and make no claim that mandatory wait-and-resend is implemented; do not launch under contradictory rules. Never silently pause/reset clocks. |
| Pilot fatal-error stage and five-minute rule? | Confirm the strict rubric above and whether critical errors in internal candidates, as well as handed-over artifacts, are fatal. Default proposal is the stricter any-candidate rule; no pilot until committed agreement. No correction can erase the fatal flag. |

Report packaging, measurement completeness, price knowledge, blind reproduction, pilot usefulness and overload evidence as distinct verdicts. Neither v3's recovered PASS, mock retries, nor a pilot success fills an unobserved v4 evidence category. No capability expansion, Fusion, SolidWorks, CAE, fabricated usage/rates or test-based tuning is included.

Only this proposal file was written. Source documents were read; no Sol/CAD run, implementation, freeze, Git mutation or other file edit was performed.
