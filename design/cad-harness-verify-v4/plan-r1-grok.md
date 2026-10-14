# VERIFY v4 plan (grok, r1)

User order 2026-10-14 09:54 JST. This file is a proposal. It does not authorize a Sol or CAD run.

Base: HEAD `ca8eb51`, manifest version `verify-v3-reviewed-r1-solfix`. Pre-rerun2 `RESULTS.md`: 60/60 completed, 58 passing, retained `real_calls` 84, charge 105 of 163. `RESULTS-RERUN2.md`: G5-r1 and G1-r2 PASS, `rerun2_calls` 4, aggregate `real_calls` 88, `archived_charged_calls` 21, `total_charged_calls` 109 of 163, geometry 18/18, all eight thresholds true, `bar_met` true, 60/60 passing. Refreeze `c6cc8d8`, impl `c345617`, SHA256 `024ecb52…`. That rerun is not a blind uninterrupted replication. v3 has no further phase. v4 starts a new counter at 0.

Committee (3/3, 2026-10-14T00:23:03Z): practical usefulness = REAL_PILOT; evidence gap = FRESH_HOLDOUT; feasibility and low risk = COST_METRICS; policy fit = SKILL_CLI_PACKAGING. The user priority order below is the execution order. The pilot and the holdout still happen. Capability expansion, a campaign to force repair denominators, and any attempt to provoke overload are out of this phase. A zero repair denominator stays null. A run with no `server_overloaded` records `overload_robustness: not_evidence`.

Host: DPC-019. FreeCAD 1.1.4 headless. No Fusion, SolidWorks, or CAE.

## 1. Deliverables and order

1. **Cost ledger.** No Sol calls. Read existing v3 driver reports and write `design/cad-harness-verify-v4/LEDGER-V3-BACKFILL.json`. Missing tokens, waits, stdout, and stderr stay null with a reason. Geometry cohort totals stay null while any geometry row is null. The file states both 88 (retained) and 109 (charged) and does not collapse them. Price is null (see the ledger). v3 `RESULTS.md`, `RESULTS-RERUN2.md`, and the aggregates are not rewritten.
2. **Consolidation.** New v4 entry point, model-visible skill, and CLI policy file (layout below). `skills/freecad-modeling/SKILL.md` stays byte-identical (`18f11567…` in v3 `SHA256.json`). v3 scoring functions are not edited. Offline tests replay the rerun2 aggregate through the existing threshold predicates and require the same eight booleans. Then one live smoke: public `dev-D1-r1` only (`route=source`, `max_calls=2`), prefix `host-verify-v4`, suffix `smoke-d1`. Pass: that command finishes the request, call 1 prompt bytes equal the request file, and call 1 context bytes equal the v4 skill file. A smoke failure may be fixed only as a harness crash or a ledger bug. Skill prose is the verbatim move described below and is not rewritten after the smoke.
3. **Holdout.** After freeze, one process, one manifest, no resume and no rerun. Verdict uses the v3 cohort gates on the sizes in the holdout section. Mid-run reading of scores, gold, or model text makes the run `interrupted` and ends the blind claim. Quota percent and process liveness are the only live checks.
4. **Pilot.** Same frozen code and skill, separate process, suffix `pilot-r1`. Not a retake of the holdout. Starts only after the holdout process has exited and the quota is under 60%. No code or rubric change between the two. If the user has not supplied tasks at freeze, this deliverable is `not_run`, which is not a fail.

Unused calls do not move to another phase. A stopped holdout is not replayed.

## 2. File and CLI layout

New files only, plus no edit to the v3-hashed modeling skill:

- `skills/cad-harness-v4/SKILL.md` — only model-visible text besides the request. Start from the current modeling skill. Replace the sentence that the driver supplies the contract with the current driver strings, copied verbatim: `CAPABILITY_CONTRACT`, `REPAIR_CONTRACT`, and the clarification sentence with `CLARIFICATION_FIELDS` (`plate_thickness`, `hole_positions`, `hole_diameter`, `pocket_depth`, `pocket_size`, `stock_dimensions`, `axis`, `finish_size`).
- `skills/cad-harness-v4/POLICY.md` — scoring gates, resend, logging. Loaded by the CLI. Never concatenated into a prompt or developer context.
- `tools/eval_verify_v4.py` — entry point. Subcommands: `ledger`, `request`, `holdout`, `pilot`, `aggregate`.
- `tools/cad_verify_v4_agent.py` — driver. Calls existing v3 guard, probe, and `summarize` predicates. Does not copy a second scorer.
- `tools/test_verify_v4.py`
- `design/cad-harness-verify-v4/dev/` — the already public D1 fixture for the smoke.
- `design/cad-harness-verify-v4/holdout/` — absent until the author’s freeze commit.
- `design/cad-harness-verify-v4/pilot/rubric.json` and `pilot/tasks/` — rubric from this plan; task text only if the user supplies it before freeze.
- `design/cad-harness-verify-v4/SHA256.json` — one manifest at freeze. Version label `verify-v4-reviewed-r1`.
- Run dirs: `reports/cad-run/host-verify-v4-<phase>/`. Ledgers: `reports/ledger-verify-v4-<suffix>.jsonl`. Aggregates: `reports/aggregate-verify-v4-<suffix>.json`. Exclusive create. v3 report paths are not opened for write.

`request --request FILE --prefix host-verify-v4 --suffix smoke-d1 --quota-snapshot PATH --codex PATH` is the one entry point. `holdout` and `pilot` call that same driver in frozen order. There is no `resume` and no `rerun`.

Every attempt writes `stdout.txt` and `stderr.txt` beside the attempt record before the next attempt starts. A captured empty stream is bytes `0` with the empty-file sha256. A capture the harness did not write stays null, reason `not_captured`.

Call 1 context is byte-identical to `skills/cad-harness-v4/SKILL.md`. Call 1 prompt is byte-identical to the request file. A later repair call, only when the existing v3 schedule issues one, keeps that same context. Its prompt is the request file plus the existing measurement JSON (`FEEDBACK_KEYS` only). Policy text is in neither. The entry-point pass is call 1.

## 3. Ledger schema

`schema: cad-harness.ledger.v4`. One JSON object per line. Kinds: `call`, `episode`, `run`. A sum is null when any addend is null.

Call fields: `run_id`, `episode_id`, `attempt` (1-based, includes uncharged rejects), `charged` (bool), `provider_rejected` (bool), `rejection_code` (string or null), `prompt_sha256`, `context_sha256`, `prompt_is_request` (bool), `context_is_skill` (bool), `started_at`, `ended_at` (UTC), `wall_s` (ended minus started, or null), `provider_wait_s` (slept backoff, or null if the sleeper did not record), `interruption_s` (gap after the previous `ended_at`, or null), `tokens` with the five `USAGE_KEYS` (`input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens`), each int or null, `token_reason` (null, `provider_usage_absent`, or `partial_usage`), `price` (null or `{currency, amount}`), `price_reason`, `stdout_sha256`, `stderr_sha256`, `stdout_bytes`, `stderr_bytes`, `cad_attempts`, `exit_code`.

Episode and run add: `charged_calls`, `rejected_attempts`, the same token object, `price`, `price_reason`, `wall_s` from the first `started_at` to the terminal `ended_at` (this span includes waits and interruptions), `stop_reason`. Run also has `phase` (`backfill`, `smoke`, `holdout`, `pilot`), `quota_snapshots`, and `overload_robustness` (`observed` only when `provider_rejected` is true at least once; otherwise `not_evidence`).

Price: this repo has no rate card. `price` is null and `price_reason` is `no_documented_rate_source` unless a user-committed `design/cad-harness-verify-v4/RATE.json` is in the freeze. That file, if present, has `source_url`, `retrieved_on`, `currency`, and one number per `USAGE_KEYS` entry. Price is computed only when all five token fields on that row are ints. Otherwise `price_reason` is `incomplete_tokens`. No rate is invented here.

v3 backfill uses these fields. Historical segment walls stay under `recorded_segment_wall_s`. Operational `wall_s` is null, reason `not_recorded`, where the old clock excluded pauses. Historical stdout and stderr are null, reason `not_captured`.

Pilot episode fields, recorded by the CLI clock: `adopted` (`yes`, `no`, `not_finished`), `edited_driving_dimensions` (int or null), `edited_features` (int or null), `edit_note` (one line or null), `human_edit_s` (null unless `pilot mark-edit-start` and `mark-edit-end` both fired), `critical_dimension_error` (bool), `fabrication` (bool).

## 4. Holdout, authored unseen

Planners and the implementer do not write or read item prose, dimensions, or gold. This plan names no part.

Cohort sizes match the v3 gates, so the existing predicates apply without a new ratio. No dev slots (D1 is the smoke, already public).

| Cohort | Count | Route pattern from v3 | max_calls each |
| --- | ---: | --- | ---: |
| legacy | 4 | offline | 0 |
| mvp | 10 | mvp | 3 |
| geometry source G1–G5 | 10 (2 per case) | source | 4 |
| geometry spec G6×3 + S3×5 | 8 | spec | 3 |
| q A4×3 | 3 | spec | 3 |
| q A5×5 + A6×5 | 10 | ask | 1 |
| completion C4×3 + C5×3 | 6 | completion | 4 |
| fault F4×2 + F5×2 + F6×2 | 6 | source for F4/F5, spec for F6 | 4 or 3 |

57 items. Sum of `max_calls` = 159. Families stay inside the current contract: `rect_prism`, `rect_stack`, `stepped_shaft`, and the features that contract already lists. New prose and new dimensions. Description sha256 values must not match any committed v1–v3 description hash.

Authoring: the user writes `holdout/run-order.json`, `holdout/<id>/description.txt`, and `holdout/<id>/gold.json` outside the review path. A checker (no model) checks schema, cohort counts, and hash uniqueness, and prints only pass/fail plus the colliding hash. The directory is added in the freeze commit, after implementation review, and is then covered by `SHA256.json`. The run refuses to start if any description hash is in the v1–v3 set or the manifest digest differs.

During the run the supervisor may read the quota snapshot and whether the process is alive. The run is one segment. A crash, a quota stop, or a harness exception is the result. Partial artifacts are kept. They are not archived and replayed.

## 5. Pilot source and rubric

Source: real design requests the user already has. This plan does not invent them. N = 10, fixed in `pilot/rubric.json` before freeze, each request hashed in the manifest. Each task’s call cap is 4 (the v3 source episode cap).

Pre-registered rubric, committed before any pilot call:

- An item is `light` when `human_edit_s` is 0, or when it is a recorded value ≤ 300. Null edit time is not `light`.
- An item is `clean` when `critical_dimension_error` is false and `fabrication` is false. Fabrication means a dimension, feature, or material the request did not state.
- The trial **fails** if any item is not `clean`.
- The trial **passes** if every item is `clean` and at least 7 of 10 are `light`.
- `not_finished` stays in the denominator and is not `light`.
- `adopted` is recorded and does not override `light` or `clean`.
- Edit amount is the two counts plus `edit_note`. Null counts stay null.

The designer’s edit interval is the CLI marks, so waits inside that interval stay in `human_edit_s`. Model waits stay in the ledger’s `provider_wait_s` and `wall_s`.

## 6. Call budget

v4 counter, separate from v3. v3 remains 109 of 163. The 54 left on that cap are not the v4 budget.

| Phase | Ceiling | Charged when |
| --- | ---: | --- |
| Backfill | 0 | read-only |
| Smoke `dev-D1-r1` | 2 | accepted Sol responses |
| Holdout | 159 | accepted Sol responses |
| Pilot | 40 | accepted Sol responses |
| **v4 ceiling** | **201** | sum |

Typed `server_overloaded` with no assistant output is uncharged, as in solfix, and still writes a ledger row and both streams. The 600 s wait is `provider_wait_s`, not a call. Episode clock stays 900 s, with the existing stage caps (initial 450, repair 450, Sol 450 / parse 60 / repair 180, CAD 300 / repair 90). `cap_timeout` stays in force so a no-deadline guard cannot floor infinity. No suite deadline.

`before_episode` reserves the remaining max-calls of that phase. The holdout does not start unless the v4 counter plus 159 is ≤ 201 and the smoke directory exists. The pilot does not start unless the holdout process has exited, the counter plus 40 is ≤ 201, and quota is under 60%.

## 7. Stop rules

- Quota: consult at 55%, stop at 60%, on every `before_call`, from a fresh DPC-019 snapshot. The rerun2 snapshot (9%) is not reused.
- Phase ceiling reached: that phase stops. Later phases do not inherit the remainder as extra calls. The pilot’s 40 stay reserved through the holdout, so a holdout that would pass 159 does not start.
- Episode or stage deadline: end that episode, write the ledger, continue to the next item. Do not retake the episode.
- Overload: wait 600 s in chunks of at most 60 s and resend the same argv, prompt, and context while the episode clock remains. Then continue the suite. Zero such rows means `overload_robustness: not_evidence`.
- Harness exception or process death: stop. Keep the partial tree. Do not resume.
- Operator reads scores, gold, or model output before process exit: mark `interrupted` and stop. That run is not the reproduction.
- Pilot: a critical dimension error or a fabrication fails the trial. Keep going through the remaining tasks until the list, the ceiling, or the quota stops the process, so the per-task record is complete.
- Exclusive create. Same suffix twice is a stop (`exists`). Old reports stay in place.
- No tuning on holdout or pilot items. No new shape or capability class. No second manifest.

## 8. User decisions

1. **Holdout author.** Supply the 57 items under the cohort table, unseen by planners and the implementer, before freeze. This proposal has no items and no dimensions.
2. **Pilot tasks.** Supply 10 real request texts before freeze, or say the pilot is deferred. Deferred is `not_run`, not a fail. A different N changes the 7-of-10 line and needs a new signed rubric.
3. **Rate card.** Commit `RATE.json` with a real source before freeze, or accept null prices with `no_documented_rate_source`.

Consensus on this plan is the agreement to the repair-prompt rule, the 201 ceiling, and no suite resume. No other open choice is required to implement phases 1 and 2.

## Process

Three-party consensus on the plans, then implement, reviews, one freeze, the smoke (before holdout text is in the tree), the holdout, the pilot, then RESULTS consensus. Commit and push after each commit. No force. Do not commit `reports/` or `.tmp/`.
