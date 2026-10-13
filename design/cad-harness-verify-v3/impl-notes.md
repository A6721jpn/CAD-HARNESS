# VERIFY v3 Phase 2 — Codex implementation

Binding: signed PLAN-V3-CONSENSUS.md; Codex owns generic code and description-only analytic data. No git, Sol, real suite run, aggregation, or freeze is performed in this task. Old data/manifests/results remain unchanged.

## Status and deferred independent controls

Codex-owned implementation is complete, uncommitted. Phase 2 as a whole is **pending independent native controls, new-dev calibration, Grok analytic review, and implementation reviews**. Context was compacted before implementation; the signed plan was reread after compaction. Continue from these notes if another context boundary is reached.

Gemini owns, and has not yet delivered, `tools/fixtures/verify_v3_native.py`, each geometry case's `positive.py`, `negative.py`, `offline.json`, F4/F5 `candidate.py`, and `dev/native-matrix.json` plus its native sources. These paths are required gates, not passing placeholders. Grok's independent analytic/role review is pending. Native v3 all-positive/all-negative/fault/parameter-edit checks cannot be claimed complete before delivery and dev calibration. No holdout measurement will be used to tune the rules.

## Diff summary

- New `cad_verify_v3_probe.py` preserves v2 consumed-link/partial-selection reachability and v1 analytic BRep/optimal-bbox gates. v3 gold requires named primary roles; roller bottom OD is geometry only. OD/bore/length have attached native proofs; groove depth/width use typed boundary relations and operative native length. Negative anchors never connect unrelated geometry. Inactive/reference/disconnected/unresolved evidence is rejected. Expression support is a finite native constraint reference/alias resolver, without evaluation of arbitrary expressions.
- New `cad_verify_v3_agent.py`/guard keep P1/R1/CAD2, source4/spec3/ask1/completion4, 450+450/900, shared10800 and max163. Schema checking precedes the one exact capability allowlist (`unsupported_shaft_operation`); accepted validator-origin unsupported uses source without P. Raw successful interpretations, schema/capability/origin and actual call purposes remain recorded. Settled in-schema editability failures invoke R. Source/repair payload/context bytes are archived separately and SHA-bound. Repair retains actual failed geometry/role evidence and never receives full gold/correct source.
- Shared edits are restricted to `tools/cad_run.py`, `cad_run_freecad.py`, `cad_verify_freecad.py`: opt-in verify-v3 dispatch, stage status/measurement records, v3 settled native-miss routing, and new diagnostic labels. Default/old-profile branches are preserved. Generation and FCStd/STEP verification still use independent owned headless processes and existing integrity/exit gates.
- New `eval_verify_v3.py`: separate v3 run/aggregate/schema names, strict reviewed freeze prerequisites/no overwrite, order/cap/byte identities, independent driver/context/fault/artifact checks, unchanged class thresholds, completed-cohort Wilson95, separate C planned/conditional/post-answer first-attempt measures, fallback origins, phase/failure distribution, provider fields/nulls, wall/attempt/P/R counts. Reviewed aggfix duration-rounding tolerance remains absolute1e-6 only for duration subtraction; live `-aggfix` runs are rejected. No v3 freeze/run/aggregate was invoked.
- Data: `test/` G1–G6/S3/A4–A6/C4–C5/F4–F6 and `dev/` D1–D3 are new description-only inputs. Descriptions use the signed suffix rules; F text is a byte copy of clean G text. C answer files have no terminal LF; binding/gold/order all hash description+one LF+answer. A5/A6 and D3 have rubric only, no invented geometry gold/answer. Named primary roles, analytic formulas/numbers, geometry predicates and tolerance are in new v3 gold/schema. F6 candidate/rule changes only the selected D6→D9. F4/F5 source candidates are deliberately absent pending Gemini.
- New `smoke_verify_v3.py` performs read-only data checks or, after handoff, dev matrix/edit checks before all native positive/negative/fault checks. Missing/incomplete independent controls are hard preparation stops. `call-cap.md` derives baseline83/max163/core51 from the exact60-entry order. `native-controls-handoff.md` gives Gemini's explicit paths and control/matrix contracts.

## Fix log (pre-Sol; no holdout measurements)

1. Initial schema-capability mock used a `radius` step key; the actual schema requires `diameter`. Corrected only the mock input. No schema/compiler/gold changes were made to pass it.
2. FreeCAD API introspection (no shape construction/measurement) showed unary point-coordinate constraints use `Second=-2000`, explicit origin uses `First=-1`, and Pad/Pocket `Type` is string `Length`. v3 now recognizes these actual typed representations, rejects arbitrary external anchors and ThroughAll/default Length2, and has a regression test. The successful repeat used isolated `.tmp/v3-api-{user,system}.cfg`. The initial metadata-only query omitted config arguments and printed inability to open default user/system configuration; it created no model/document/output report and was repeated with isolated config.
3. Test discovery with `-s tools -t .` was rejected because `tools` is a namespace package without `__init__.py`. Used explicit module names, without adding package files or changing old tests.
4. No native holdout controls were available or measured; there was no positive gold disagreement, measurement-driven rule change, arithmetic-gold correction, or exposed holdout tuning.
5. The final mock pass also checks that an active circle `Equal` binds a reached construction radius to the consumed boundary, while mere `Coincident` reachability does not; finite aliases resolve and unknown/arithmetic expressions fail as predicate evidence. Symmetry records its actual driven half-width value, not a value copied from gold.

## Test / Sol-free results

Measured through 2026-10-13 13:54:39 JST (no model calls).

- `python -B -m unittest tools.test_verify_v3`: **14 tests, OK** (final repeat 0.248 s after all v3 changes). Covers exact schema/capability boundary, validator fallback without P, actual R after P + settled in-schema miss, native worker routing, reserved budgets/shared clock/time stop, Q/C byte/question contracts, role/decoy arithmetic isolation, native-origin sentinel, reachability, phase-not-reached, F6 one-shot mutation, data/order/caps, and completed-cohort separation. TEMP uses `tools/test_support.py` under `.tmp/unittest-mvp1`.
- Full explicit unit command below: **106 tests, OK; 6 skipped; 34.913 s**. The six are old native-only DV3/v2 tests under ordinary Python, not v3 calibration. All old unit/profile regressions remain unchanged. The command's old evaluator freeze/run/aggregate tests use temporary mock repositories/providers; no live suite or real frozen manifest/aggregate was created.
- `python -B tools/smoke_verify_v3.py --data-only`: **18 cases, 60 episodes, planned83/max163, Sol0/CAD0, pass**. Gold schema/description identity, role declarations, rubric controls, C bindings and F text identity pass.
- `python -B tools/smoke_cad_mvp.py --run verify-v3-codex-phase2-20261013-1340-mvp1 --group legacy`: **4/4**, exit0, specified FreeCADcmd only. A-good/B-good pass; A-broken/B-broken fail their intended Probe gate. [Smoke evidence](../../reports/cad-run/verify-v3-codex-phase2-20261013-1340-mvp1/smoke-summary.json).
- `python -B tools/smoke_verify_v3.py --run verify-v3-codex-native-pending-check-mvp1`: expected preparation stop `independent_dev_native_matrix_pending`, before output-directory creation/CAD launch. This does **not** count as a native smoke pass. Full new native positives/negatives/F4–F6/dev edits remain pending Gemini.
- AST parsing passed for all `tools/*.py`. Baseline SHA comparison of existing tools/design/skills found only the three opt-in shared CAD files changed; existing eval-v1/v1/v2 data, schema/compiler/skill/evaluators/tests and SHA256 manifests are byte-identical. No old reports were edited; only the new legacy smoke evidence was written. No git or real aggregate operation occurred.

Full unit command:

```powershell
python -B -m unittest tools.test_cad_agent tools.test_cad_mvp tools.test_cad_run tools.test_cad_spec tools.test_cad_spec_probe tools.test_cad_verify tools.test_eval_mvp tools.test_verify_dv3_native tools.test_verify_v2 tools.test_verify_v2_native tools.test_verify_v3
```

## COMMIT PLAN (supervisor only; final Codex scope)

1. `feat(verify-v3): semantic dimension proofs and capability routing` — `tools/cad_verify_v3_probe.py`, `tools/cad_verify_v3_guard.py`, `tools/cad_verify_v3_agent.py`, `tools/cad_verify_v3_diagnostics.py`, `tools/cad_run.py`, `tools/cad_run_freecad.py`, `tools/cad_verify_freecad.py`.
2. `feat(verify-v3): fresh analytic holdout and bounded evaluator` — `tools/eval_verify_v3.py`, `design/cad-harness-verify-v3/gold-schema.json`, `dev/{D1,D2,D3}/`, `test/{G1,G2,G3,G4,G5,G6,S3,A4,A5,A6,C4,C5,F4,F5,F6}/`, `run-order.json`, `call-cap.md`. Include only current authored data; missing Gemini paths are not placeholders.
3. `test(verify-v3): offline contracts and review handoff` — `tools/test_verify_v3.py`, `tools/smoke_verify_v3.py`, `design/cad-harness-verify-v3/native-controls-handoff.md`, `impl-notes.md`.
4. Separate Gemini control commit after delivery/review — the exact native helper/control/matrix/edit files specified in the handoff. Grok must independently rederive gold/requested roles before native measurement. Dev calibration must lock rules before holdout checks; any holdout-triggered code rule change follows the signed replacement rule.

Do not include `.tmp/` authoring/API scripts, temporary unit repositories, unrelated dashboard changes or generated reports in implementation commits. The supervisor already committed the signed plan. No implementation commit IDs or unavailable reviews are invented here.

## Deferred host commands (not executed here)

After Gemini controls and Grok analytic review, run dev-only checks first, lock the rules, then run the complete batch from its beginning with a fresh prefix. Every rerun needs a new prefix; first disagreement stops. The runner invokes only `C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe`, headless, with isolated configuration.

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
python -B tools/smoke_verify_v3.py --data-only
python -B -m unittest tools.test_verify_v3
python -B tools/smoke_verify_v3.py --run host-verify-v3-dev-controls-r1-mvp1 --dev-only
python -B tools/smoke_verify_v3.py --run host-verify-v3-native-controls-r1-mvp1
python -B tools/smoke_cad_mvp.py --run host-verify-v3-legacy-controls-r1-mvp1 --group legacy
```

After all required independent reviews/controls pass and the supervisor selects local commits, the supervisor alone may freeze/measure. These are future templates, **not** authorization or actions taken in this implementation task. Replace the two commit IDs, reviewed CLI path and actual quota-snapshot path with supervisor values; never overwrite an existing SHA manifest or prefix.

```powershell
python -B tools/eval_verify_v3.py freeze --version verify-v3-reviewed-r1 --implementation-commit <implementation-commit> --plan-commit <plan-commit> --codex <reviewed-cli-path>
python -B tools/eval_verify_v3.py run --prefix host-verify-v3-reviewed-r1 --quota-snapshot <supervisor-snapshot-path> --call-budget 163
python -B tools/eval_verify_v3.py aggregate --prefix host-verify-v3-reviewed-r1 --suffix host-reviewed-r1
```

The run establishes one10800-second monotonic clock; independent aggregation must finish before its stored strict deadline. Expected new outputs: `reports/aggregate-verify-v3-host-reviewed-r1.json/csv`. Supervisor quota remains missing/stale>300/future/invalid stop, 55% soft, 60% hard; no percentage inference from estimated calls/tokens.

`design/cad-harness-verify-v3/SHA256.json` is intentionally absent. Generic freeze code refuses missing independent controls; no freeze was performed in this task.

## Review fixes

Applied 2026-10-13 14:54:10 JST, uncommitted, against `gemini-impl-review.md` MUST1 and the in-scope findings in `grok-impl-review.md`. No freeze, Sol, git, real suite run/aggregate, native holdout measurement, gold/data edit, or semantic-rule change was performed.

- **Gemini MUST1:** v3 `active()` now checks `getActive()` first. Only Distance, DistanceX, DistanceY, Radius, Diameter and Angle call `getDriving()`; non-dimensional geometric constraints use activity alone. It does not catch/ignore invalid dimensional IDs or turn reference/inactive dimensions into driving evidence. Typed role relations, boundary attachment, reachability, tolerances and every pass/fail gate are preserved.
- **Gemini mock realism:** the regression reproduces FreeCAD 1.1.4's `ValueError("Invalid constraint id")` on a geometric `getDriving()` query. It checks all six datum types (including Angle), geometric constraints, inactive constraints, reference dimensions, and zero geometric `getDriving()` calls. Existing expression/Equal/coordinate mocks now enforce that same API distinction. No extra geometry behavior is introduced.
- **Grok NIT1:** the redundant non-package loader condition in `cad_run.py` now names only verify-v2; the earlier verify-v3 branches already select the v3 Probe. Actual dispatch for existing profiles is unchanged.
- **Grok pre-gate missing-file finding:** `require_controls(..., dev_only=True)` checks the native helper, D1 gold, matrix and every referenced dev source/edit gold. Full checks also require all holdout positive/negative/offline files and F4/F5/F6 fault rules/candidates. `smoke()` invokes this before data checks, run-directory creation or CAD launch, including dev-only mode. Missing files raise `independent_native_controls_pending` with their exact repository-relative paths. Read-only presence checks for both full and dev-only controls passed on the current delivered Gemini files. This is not a native smoke result.
- **Grok NIT2/3 disposition:** retain PCD floating-point residuals within the frozen tolerance and the signed non-roller v2 flat-dimension behavior. Rounding gold or changing half-value/Length2 semantics is outside this API/preflight fix and conflicts with the instruction to keep semantic rules unchanged. No old-profile or gold edits were made.

Verification ran in the requested order, with TEMP redirected by `tools/test_support.py`:

| Command | Result |
| --- | --- |
| `python -B -m unittest tools.test_verify_v3` | 16 tests, OK, 0.378 s |
| `python -B -m unittest tools.test_cad_agent tools.test_cad_mvp tools.test_cad_run tools.test_cad_spec tools.test_cad_spec_probe tools.test_cad_verify tools.test_eval_mvp tools.test_verify_dv3_native tools.test_verify_v2 tools.test_verify_v2_native tools.test_verify_v3` | 108 tests, OK, 36.340 s; 102 passed and 6 existing native-only tests skipped under ordinary Python |
| `python -B tools/smoke_verify_v3.py --data-only` | pass: 18 cases, 60 episodes, baseline83/max163, Sol0/CAD0 |

Fresh mock run prefix: `mock-v3-review-fixes-r1-mvp1`; missing-file cases use `review-fixes-preflight-r1-mvp1` through `r4`. All are confined to fresh temporary mock repositories. Data-only is read-only and accepts no run prefix; it created no report directory and reused no native/live run. The regression removes only disposable mock files, never real helper/control files. The full command's existing evaluator tests freeze/run/aggregate only mocked temporary repositories; no real version or aggregate was created.

Changed paths for the supervisor's review-fix commit (`fix(verify-v3): respect Sketcher datum API and preflight native controls`): `tools/cad_verify_v3_probe.py`, `tools/cad_run.py`, `tools/eval_verify_v3.py`, `tools/smoke_verify_v3.py`, `tools/test_verify_v3.py`, and this `impl-notes.md`. A baseline SHA comparison confirms all native control sources, descriptions/answers/rubrics/gold, signed plan, run-order, numerical tolerances, previous evaluators and SHA manifests remain byte-identical. Gemini's reported earlier native batch was not rerun or re-scored in this review-fix task; native re-review/calibration remains a separate supervisor-controlled step before freeze.

## Solfix

Implemented uncommitted, validated **2026-10-13 17:44:58 JST**. Binding: `SOLFIX-CONSENSUS.md` together with `solfix-codex.md`, including all three USER DECISION sections. The 16:39 decision replaces capped/charged overload retries; the final 17:08 update supersedes both the inherited deadline and the intervening 20:00 cutoff with **no deadline for segment 2**. No Git mutation, Sol/FreeCAD invocation, real freeze, real resume, or real aggregate was executed. The original frozen manifest remains `verify-v3-reviewed-r1`.

### Changes and policy

- `tools/cad_verify_v3_agent.py`: opt-in `solfix-600s-unlimited-v1` transport policy. Only exact typed `codex_error_info=server_overloaded` with no final/assistant output is a provider rejection. CLI versions without a typed stdout code may use the uniquely bound actual session's typed rollout event; free text never establishes rejection. Unknown errors, partial/final output, parse failures and CAD failures receive no provider resend.
- Each rejection requests **600 seconds** of backoff, in chunks of at most 60 seconds, then the byte-identical argv/prompt/context is resent without an attempt cap, subject to the unchanged episode/stage and quota stops. Fresh quota/version/hash/time checks precede every actual invocation. Rejected attempts consume **zero** new shared-call/P/R/model slots; accepted responses and unclassified failures remain charged, including late responses. Attempts, requested/actual waits, session IDs, exact errors and usage are recorded separately; rejection itself never creates a harness or abnormal stop.
- Production exec stdout/stderr are drained concurrently in 8192-byte chunks, with at most **16384 UTF-8 bytes retained per stream**, complete-stream hashes and byte counts. Structured events and session/usage metadata are inspected before truncation, including assistant `response_item` payloads. Event assembly is bounded to 1048576 characters, and metadata lists are bounded; uninspectable streams cannot establish a rejection. Rollout evidence is also read incrementally. Timeout capture retains bounded tails and remains an unclassified charged attempt. Classification never relies on a truncated tail.
- `tools/cad_verify_v3_guard.py`: resume inherits started 534990.093, ceiling 163 and **spent 54 / remaining 109**, and sets the shared deadline to `None`. The original 545790.093 deadline is retained only as segment-1 evidence. No replacement 10800-second clock or wall-clock cutoff is introduced. Clock/cap authentication, quota stops (**55% soft / 60% hard**), model slot caps and **900/450/450/P60/R180** episode/stage reservations remain. The shared 960-second start reserve applies only when a shared deadline exists.
- **Time consequence:** overload backoff remains wall time within the unchanged episode/stage budgets. A 600-second wait cannot finish inside an initial 450 / repair 450 stage; P60/R180 can stop it sooner. This is an ordinary incomplete time-stop episode, with no rejected P/R slot consumed and no provider-failure harness stop. Episode timers are not paused or reset. The original A5 backoff is credited from recorded elapsed time; any remaining wait is performed before its authorized replay.
- `tools/eval_verify_v3.py resume`: authenticates the archived manifest and UTC/monotonic correspondence, preserves all 60 original rows/artifacts byte-for-byte, and selects **A5-r5 first, then sequences 48–60**. It writes 14 segment-2 rows under the original suite/run names plus `-resume1`, with original-run/manifest/artifact bindings. A5's first input/context identity is checked before invocation and during aggregation; its prior rejection is retained separately. Completed IDs 1–46 are not re-executed, and existing outputs are never overwritten.
- Two-segment aggregation binds segment 1 to archived `SHA256.run-r1.json` and segment 2 to solfix `SHA256.json`. Only the four code files below may differ; gold, Probe, controls, data/order/model/CLI/AGENTS/plan identities must match. Aggregate output names require `-solfix`. Segment 1 retains its original recorded `deadline_ok` (or the saved wall/deadline evidence when that field is absent); segment 2 reports **`deadline: none (user decision 17:08)`**, with `deadline_monotonic: null`. Resume and aggregate are allowed after the original deadline, while the shared 163 ceiling remains enforced. The original stop/A5 partial remain an annex; only segment-2 A5 is scored. New rejections/waits are unscored and uncharged.
- **Historical treatment remains the signed conservative choice:** completed G5-r1/G1-r2 keep their original scores/classes/artifacts, with independent provider-rejected evidence annotations. Inherited spent54 remains the stored historical total; no retrospective refund or result replacement is made. New rejected attempts are uncharged. The aggregate labels the mixed harness versions explicitly as signed segmented recovery, rather than one unchanged frozen run.
- Solfix freeze support records the four amendment/evidence documents and requires the archived original manifest; transition validation rejects unapproved code/data changes. Cold `run` of the solfix version is rejected; only `resume` is permitted. Shared `cad_agent.py`, MVP/v1/v2 code paths and Probe/gold/scoring rules remain unchanged.

### Tests and checks

Final checks, after all code changes:

| Command/check | Result |
| --- | --- |
| `python -B -m unittest tools.test_verify_v3` | **23 tests, OK, 0.955 s**, exit0; TEMP redirected by `tools/test_support.py` |
| `python -B tools/smoke_verify_v3.py --data-only` | **pass**, exit0: 18 cases, 60 episodes, baseline83/max163, Sol0/CAD0 |
| AST parse of the four changed Python files | pass |
| Read-only comparison against the original frozen manifest | only the four permitted code/test paths differ; all other frozen data/Probe/control/older-profile hashes match |

The seven Solfix tests cover strict structured/no-output classification; full-stream event/session detection with bounded multibyte tails and timeout capture; five refusals followed by an identical accepted call with only one charged slot; unknown-error non-retry; ordinary stage-time stops and both 55/60 quota stops; inherited cap/clock authentication and manifest allowlist; resume/aggregate **after the original deadline** with original artifact/score preservation and tamper rejection; and unconsumed rejected P/R slots. The unlimited-retry scheduler test mocks sleep without advancing wall time; advancing-clock tests separately verify 450/P60/R180 clipping. All provider/CAD launches are mocked. Resume/aggregate progress comes only from disposable mock repositories. Mock prefixes: `mock-v3-solfix-r1-mvp1`, `mock-v3-solfix-resume-r1`.

### COMMIT PLAN — supervisor only

1. `fix(verify-v3): recover structured overloads with inherited suite identity` — `tools/cad_verify_v3_agent.py`, `tools/cad_verify_v3_guard.py`, `tools/eval_verify_v3.py`, `tools/test_verify_v3.py`, `design/cad-harness-verify-v3/impl-notes.md`. Preserve the separately authored consensus/evidence documents; no gold/control/order/Probe change belongs in this commit.
2. Supervisor's archive/re-freeze commit, only after review — byte-identical `design/cad-harness-verify-v3/SHA256.run-r1.json`, new `SHA256.json`, and the supervisor's `FROZEN.md` update. The new manifest binds `SOLFIX-CONSENSUS.md`, `SOLFIX-BRIEF.md`, `SOL-FAILURE.md`, `solfix-codex.md`; all four have separate provenance. No archive, manifest, FROZEN edit or git operation was done by Codex.

### Future host commands — NOT executed

Use the same reviewed CLI and original plan commit. Set the supervisor's reviewed implementation commit below; keep the original quota snapshot path actively refreshed (maximum age 300 seconds). Archive only after confirming the archive/resume/aggregate outputs are absent. These are future host commands, not actions performed in this task.

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
$solfixImplementationCommit = 'REPLACE_WITH_SUPERVISOR_REVIEWED_COMMIT'
if ($solfixImplementationCommit -notmatch '^[0-9a-f]{7,40}$') { throw 'set the reviewed solfix implementation commit first' }
if (Test-Path -LiteralPath design\cad-harness-verify-v3\SHA256.run-r1.json) { throw 'archive already exists' }
Move-Item -LiteralPath design\cad-harness-verify-v3\SHA256.json -Destination design\cad-harness-verify-v3\SHA256.run-r1.json
python -B tools\eval_verify_v3.py freeze --version verify-v3-reviewed-r1-solfix --implementation-commit $solfixImplementationCommit --plan-commit fd7e215 --codex C:\Users\backo\.codex\packages\standalone\releases\0.159.2-x86_64-pc-windows-msvc\bin\codex.exe
python -B tools\eval_verify_v3.py resume --prefix host-verify-v3-reviewed-r1 --run-manifest design\cad-harness-verify-v3\SHA256.run-r1.json --quota-snapshot C:\dev\CAD-HARNESS\.tmp\verify-v2-supervisor-quota.json
python -B tools\eval_verify_v3.py aggregate --prefix host-verify-v3-reviewed-r1 --suffix host-reviewed-r1-solfix --run-manifest design\cad-harness-verify-v3\SHA256.run-r1.json
```

Expected supervisor outputs: `reports/cad-run/host-verify-v3-reviewed-r1-verify-v3-suite-mvp1-resume1/{plan.json,progress.jsonl,suite-run.json}`, 14 selected episode directories with `-mvp1-resume1`, and `reports/aggregate-verify-v3-host-reviewed-r1-solfix.{json,csv}`. **There is no segment-2 suite deadline or aggregate cutoff**; quota/call/episode/stage checks remain enforced.
