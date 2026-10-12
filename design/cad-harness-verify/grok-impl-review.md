# CAD-HARNESS VERIFY Phase 2 impl review (grok, 2026-10-12)

Uncommitted working tree against signed `PLAN-CONSENSUS.md` (R3b). Read-only. No code edits, FreeCAD, Sol, or unittest in this pass. The offline 47/47, legacy 4/4, and 73 unit results are `impl-notes.md:7`'s host record.

Tracked diff is `tools/cad_agent.py`, `tools/cad_run.py`, `tools/cad_run_freecad.py`, `tools/cad_verify_freecad.py` (123 insertions, 23 deletions). New verify files are `tools/cad_verify_probe.py`, `tools/cad_verify_guard.py`, `tools/eval_verify.py`, `tools/fixtures/verify_native.py`, `tools/smoke_cad_verify.py`, `tools/test_cad_verify.py`, `tools/test_verify_dv3_native.py`, and `design/cad-harness-verify/` (`test/`, `dev/`, `run-order.json`, `gold-schema.json`, `SHA256.json`, `impl-notes.md`). `tools/eval_mvp.py`, `tools/cad_spec.py`, `tools/cad_spec_probe.py`, and `design/cad-harness-mvp/eval-v1` are absent from the diff.

## Checked

Holdout and freeze. `eval_verify.py:267` sets `evaluation` only when `group!="dev"`. `run-order.json` sequences 1–3 are DV1, DV6, DQ2, and `dev_max_calls` is 4 (`:12`). Dev description text differs from the test parts (DV1 vs V1). `freeze` (`eval_verify.py:42-56`) writes `SHA256.json` once through `write_json` / `open("x")` (`:36-38`). `verify_frozen` (`:59-68`) stops on a byte mismatch, an agents change, or a settings change. `run` refuses an existing prefix or run directory (`:236`) and sets `stopped` when `call_budget` is below `planned_calls` 71 (`:241`). `before_run` reserves the remaining `min_calls` sum (`:248`).

Gold stays out of generation. The Sol argv receives `input_text` (`cad_agent.py:476`). `--gold` is passed only to `tools/cad_run.py` (`:563-567`). `description_gold_identity` (`:412-413`) requires `gold["description"] == input_text` before a call. The verify spec contract appends the full allowed field-ID list (`:458-460`). V1–V6, S1, Q1–Q3, and F1–F3 `description.txt` lines match the signed table. S1 includes 「垂直辺は鋭く残す」.

Eval-v1 bar. `summarize` (`eval_verify.py:325-349`) keeps the MVP record at ≥8/10 and each `eval_mvp.ORDER` part ≥1, legacy 4/4, V1–V5 ≥8 with each ≥1, V6≥2, S1≥4, Q1≥2, Q2≥4, Q3≥4, `q_inventions==0`, fault `established==6` and `detected==6`, final repair ≥4, each of F1–F3 ≥1, and repair kinds exactly `{source, spec}`. A stopped suite cannot set `bar_met`. Wilson uses z=1.96 and returns None unless every planned row in that batch completed (`:293-304`). `interval_scope` (`:392`) keeps groups separate.

Probe. `tight_box` is `optimalBoundingBox(False, False)` with no BoundBox fallback (`cad_verify_probe.py:22-25`). `load_gold` accepts `volume_scope` only for a `rect_prism` fillet (`:44-46`). S1 gold is bbox `[-29,29,-21,21,0,16]`, target 29232, relative 1e-4, formula `W*D*(pocket_floor-bottom)`, scope `[-29,29,-21,21,0,12]` (`test/S1/gold.json:84-104`). The volume gate uses `shape.common(stock).Volume` when a scope is present; `m["volume_mm3"]` stays the whole solid (`cad_verify_probe.py:402-417`). Reimport compares that whole volume at relative 1e-4 (`cad_verify_freecad.py:66-68`). Unknown profiles raise.

Fault injection. `observe` (`cad_verify_guard.py:128-136`) requires a settled CAD exit, `probe_status=="predicate_fail"`, `geometry_ok is False`, `native_valid is True`, and `expected_predicate` in `predicate_diff`. It does not write `probe_pass`. `injected` becomes true only when the replacement is returned (`:125`). F1 is a source replace with `expected_predicate` `roller`; F3 matches one V6 hole at `center_xy [-36,-27]`, diameter 4, z `[0,12]`, and sets diameter 6 (`test/F3/fault.json:1-25`). A geometry pass after an observed, undetected fault raises `fault_false_pass` (`cad_agent.py:583-585`). Both fault codes are harness stops (`eval_verify.py:114`).

Quota and deadline. The snapshot must be exactly `snapshot_id`, `observed_at`, `used_percent`, with a timezone. `age<0` is future, `age>300` is stale, `>=60` is hard, `>=55` is soft (`cad_verify_guard.py:27-46`). `before_call` checks, then increments (`:74-79`). Guard `seconds` must be 10800 and `call_budget` must be 1..125 (`:51-53`). A verify row with `ended_elapsed_s>=10800` is cleared (`eval_verify.py:281`, `:369`). Aggregation requires the same-boot monotonic clock still before `deadline_monotonic` and `wall_s<10800` (`:384`). CAD timeout is `min(300, budget.remaining()-5)` (`cad_agent.py:564`). Aggregates refuse an existing path or symlink (`eval_verify.py:356`) and create the CSV with `open("x")` (`:396`). `run-order.json` has 54 sequences in the signed order through `fault-F3-r2`, `planned_calls` 71, `max_calls` 125.

## Findings

MUST: none. A missed injection cannot set `bar_met`.

1. SHOULD `tools/cad_verify_guard.py:99`. `Fault.inject` sets `reached=True` before the spec match. A miss at `:114-116` stores `not_reached_reason="candidate_target_missing"` and returns the original candidate with `injected` still false. `observe` (`:129`) then returns immediately, so `observed` stays unset and `cad_agent.py:583-585` does not raise. The unmutated spec can finish with `geometry_ok` true. `fault_bar` still requires `established==6` and `detected==6` (`eval_verify.py:335-337`), so `bar_met` stays false. The `reached` count in the suite report is high. Set `reached=True` only in the update at `:125`, when `injected` becomes true.

2. NIT `design/cad-harness-verify/SHA256.json` with `tools/eval_verify.py:38` and `:55`. The file on disk is the pre-fix snapshot (`impl-notes.md:16-17`). `freeze` cannot replace it, and `verify_frozen` (`:63-64`) fails closed on the mismatch. The supervisor renames or removes it and runs `freeze` before Phase 3. The COMMIT PLAN already says this.

3. NIT `tools/cad_agent.py:507-514`. A verify `needs_clarification` object stops that run, including a fully specified geometry part. The row is a miss. The MVP path still raises `needs_clarification` and retries (`:515`).

4. NIT `tools/cad_verify_guard.py:157-163`. Q2/Q3 `critical_invention` is true when `regions` or `holes` is present, or when the missing field name is in `raw`. An unsupported-only object fails `clarification` (`:144-148`) and scores 0 with `critical_invention` false. Q2/Q3 `passed` still requires `q_score==1`, one Sol call, and zero CAD attempts (`eval_verify.py:198`).

5. NIT `tools/cad_agent.py:559` and `:564`, `tools/cad_verify_guard.py:63-66`. `Guard.remaining` already subtracts 5 s. The CAD timeout subtracts another 5 s, and CAD is refused when `budget.remaining()<=6`. The run stops inside the 10800 s window.

6. NIT `tools/cad_agent.py:584-585`. `fault_detection_mismatch` aborts the version when the fault was observed and the expected predicate is absent, including when `geometry_ok` is false. `harness_failure` (`eval_verify.py:114`) then stops the suite, and `bar_met` requires `not stopped` (`:345`).

verdict: READY
