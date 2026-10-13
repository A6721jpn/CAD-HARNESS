# AGGFIX verdict (grok)

COUNTER

Date: 2026-10-13. Read-only. No code edit, no aggregate, no freeze, no FreeCAD, no Sol.

## Accepted facts

`reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/suite-run.json` and `plan.json` both store `started_monotonic` 514542.359 and `deadline_monotonic` 525342.3589999999. Their difference is 10799.999999999942, which is 5.820766091346741e-11 below 10800. `sha_manifest` on both files is `129087752bd9a9fb4060dbd96bea58157dbb5dc1adc42c4dd7c1be4db84132d8`. `version` is `verify-v2-reviewed-r1`. The failing conjunct is `tools/eval_verify_v2.py:547`.

The 1e-6 span window, the three-value unit test, the new outputs `reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json` and `.csv`, and a new `FROZEN.md` section are the right fix. Do not edit `suite-run.json` or `plan.json`. Do not overwrite an existing aggregate.

## Blocker

Re-freezing `SHA256.json` and pointing `verify_frozen` at that new manifest breaks the rest of `aggregate` (`tools/eval_verify_v2.py:542–548` and `:548`):

- `digest` becomes the hash of the new file, so `observed["sha_manifest"]` and `plan["sha_manifest"]` no longer match.
- `observed["version"]` stays `verify-v2-reviewed-r1`, so a new version string fails `suite_record_binding`.
- `observed["frozen_sha256"]==manifest["files"]` fails once `tools/eval_verify_v2.py` or a listed test file changes. `versions_consistent` becomes false and `bar_met` becomes false (`:524`) with no score change.
- `load` (`:131`) calls `verify_frozen` before the span check. A patched `tools/eval_verify_v2.py` currently stops at `sha_mismatch:tools/eval_verify_v2.py` even after the span line is fixed.

## Exact change

Leave `design/cad-harness-verify-v2/SHA256.json` byte-identical. Do not call `freeze`. Version stays `verify-v2-reviewed-r1`. A byte-identical copy such as `SHA256.run-r1.json` is optional and must not be produced by rewriting the original.

In `aggregate` only:

1. Replace the span conjunct at `tools/eval_verify_v2.py:547` with `abs((observed["deadline_monotonic"]-observed["started_monotonic"])-10800) > 1e-6`. Every other binding stays exact, including `sha_manifest` against the unchanged `SHA256.json`.
2. Give `verify_frozen` an `allow_mismatch=()` argument. Default empty. `run` and the normal `load` pass nothing. `aggregate` loads with `allow_mismatch=("tools/eval_verify_v2.py",)` only. Any other path still raises `sha_mismatch`.
3. On the new aggregate document, add audit fields that `summarize` does not read: `aggregator_exception` = `tools/eval_verify_v2.py`, `aggregator_file_sha256` = the on-disk hash, `manifest_file_sha256` = the hash stored for that path. `version`, `sha_manifest`, and `frozen_sha256` in the aggregate stay the original manifest values.

Put the unit test in a new file that is not added to `CODE` and not added to `SHA256.json`. Required cases: span 10799.999999999942 accepted; 10799.9 rejected; 10801 rejected. Include the stored pair 525342.3589999999 − 514542.359 as the accepted case.

`FROZEN.md` gets one post-run section: the span value, the 1e-6 window, the single allowed path, both hashes, and the new aggregate names. No gold, threshold, order, probe, or runner change. `deadline_ok` (`:577`) and the `ended_elapsed_s >= 10800` pass clear (`:557`) stay exact. This patched tree must still be refused for a new live run.

verdict: COUNTER
consensus: AGREE 2026-10-13 10:58:24 JST
