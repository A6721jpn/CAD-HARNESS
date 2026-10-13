# AGGFIX implementation notes

Recorded: 2026-10-13 11:12:14 JST. Implemented `AGGFIX-CONSENSUS.md`: codex items 1–3 plus grok additions a–c. Uncommitted; supervisor freeze and aggregation remain pending.

## Diff summary

- `tools/eval_verify_v2.py`: replace only the 10800-second span equality with absolute error `>1e-6`. Exact saved run/plan timestamp equality, `deadline_ok`, wall `<10800`, and per-episode `ended_elapsed_s>=10800` checks remain unchanged.
- Append `run_manifest=None` to `aggregate()` and add aggregate-only `--run-manifest`. Existing `load()` verifies the current reviewed manifest first. An explicit archive is read through `safe_file()` and hashed from its original bytes; there is no automatic fallback.
- Archive compatibility requires identical metadata/file key sets; only version/created_at/local_commit/files may differ. All other metadata must match, current version must be original version plus `-aggfix`, and the file-hash delta must be exactly `{tools/eval_verify_v2.py, tools/test_verify_v2.py}`. Reject an extra changed file with `aggfix_manifest_binding`.
- Bind run/plan version and manifest digests, original frozen file map, and existing driver identity checks to the archived original. Keep the aggregate's top-level version/commit/digest/file map as the original measurement identity; add the verified current `aggregation_identity`. Without an archive, retain the single-manifest output and binding behavior.
- `run()` rejects a loaded version ending in `-aggfix` with `Stop("aggfix_no_live_run")` before suite paths/records or processes are created. No other runner behavior changed.
- `tools/test_verify_v2.py`: add one live-run refusal test and extend the existing temporary mock aggregation test. Cover the stored timestamp pair, accepted/rejected spans, exact timestamp/deadline/wall/episode limits, both output identities, CLI forwarding, explicit archive requirement, changed archive bytes, third-file changes, current-code SHA mismatch, and no-overwrite/process-launch protections.
- An existing Guard unit assertion also subtracted real monotonic timestamps with exact equality. It now asserts the cap separately and checks `deadline == started + 10800` exactly. Production Guard/deadline code was not changed.

`freeze()`, `load()`, `verify_frozen()`, `validate_order()`, `record()`, `summarize()`, metrics/token logic, and all scoring/gold/threshold/order/Probe code are unchanged.

## Commands and results

TEMP was redirected by the existing `tools/test_support.py` module setup. Test suite/manifest/aggregation writes occurred only inside temporary mock repositories; no real suite or aggregate command was invoked.

| Command | Final result |
| --- | --- |
| `python -B -m unittest tools.test_verify_v2` | 15/15 PASS, 32.083 s, exit 0 |
| `python -B -m unittest tools.test_verify_v2_native` | 3 tests SKIPPED, 0.000 s, exit 0: normal Python lacks the required FreeCAD runtime |

These are the two `test_verify_v2*.py` modules. No native FreeCAD/smoke batch was started because this task authorizes unit tests and prohibits new CAD runs.

First unit attempt: 15 tests, 14 PASS/1 FAIL, 32.355 s. The pre-existing Guard test expected `deadline-started == 10800`, but observed `10799.999999999942`. After the test-only exact-addition assertion correction above, the complete module passed. All new AGGFIX checks passed on both attempts.

The accepted duration case uses the exact stored pair `525342.3589999999 - 514542.359 == 10799.999999999942`. The mock rejects `10799.9` and `10801`, a run/plan deadline mismatch of `1e-7`, and success at the exact elapsed-time boundary. Temporary archive recovery yields the same summary as the original mock aggregate and launches no subprocess.

## Preservation and handoff

Read-only before/after hashes confirm the only existing source/design/skill changes are the two authorized Python files; this notes file is the sole added file. All other 185 frozen entries, data/gold/test items, binding/review documents, v1/MVP code, and original suite `plan.json`, `suite-run.json`, and `progress.jsonl` remain byte-identical.

Original `SHA256.json` remains byte-identical, digest `129087752bd9a9fb4060dbd96bea58157dbb5dc1adc42c4dd7c1be4db84132d8`. Its only now-stale entries are the two authorized code/test files; it was not rewritten, moved, or re-frozen.

| File | Before SHA256 | After SHA256 |
| --- | --- | --- |
| `tools/eval_verify_v2.py` | `506231d09324cd11543f14d65cf01192016dbc142c3e5c9fe37e04811db51b27` | `2a5ab84204ea04c8ff0dcf10528fc236a179e44fd36e1cab9e59a3867c76308e` |
| `tools/test_verify_v2.py` | `e65cda96253ce2844622bf3881acba408926873121d8588f42b6e49d668e1b9e` | `573232319bf0a4b5667f51ee66071ab257b28b3b730c8841c3980b8fd3a53f0b` |

No git, real freeze/aggregate/run, Sol/CAD calls, manifest/archive/FROZEN.md edits, or original-report writes occurred. Supervisor alone handles codex items 4–5: commit, preserve the original manifest bytes, reviewed aggfix re-freeze/FROZEN.md record, and independent aggregate to a new suffix under the frozen CODEX_HOME identity. Original deadlines and no-overwrite rules remain binding.
