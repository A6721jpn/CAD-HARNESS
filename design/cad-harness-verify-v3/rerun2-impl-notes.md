# RERUN2 implementation notes

Implemented the 2026-10-14 08:58 JST user decision in `tools/eval_verify_v3.py` and `tools/test_verify_v3.py` only. This note is the sole additional file. No Sol, CAD, real freeze, live rerun/aggregate, or Git command was executed.

- `rerun` requires exactly `geometry-G5-r1` and `geometry-G1-r2`, selected in their frozen order. It rejects other/duplicate/partial ID lists and existing suite, episode or execution-staging targets before launch.
- It reuses `load`, `original_binding`, artifact hashes, the no-deadline `Guard`, the unchanged `agent.run_driver(provider_retry=True)`, and `record`. Both routes remain `source`, max_calls 4 each. Initial charged calls are 105 of 163; their combined maximum is 8, giving at most 113 total. Existing 600-second overload retry, quota 55/60 stops and episode/stage budgets remain unchanged.
- The unchanged driver accepts its existing suffixes. The evaluator uses a fresh supported execution name, then renames only that new directory to the requested `-rerun2` name and adjusts its new report's run/path metadata. `execution_run` retains the actual execution name. Captured payloads and CAD artifact bytes are preserved. No driver code was edited.
- The original manifest, original artifacts, completed resume artifacts, and existing two-segment JSON/CSV are bound and preserved. The new aggregate replaces only the two selected rows, retaining both versions in `substituted_rows` (`original` and `replacement`). Other 58 rows, including A5/A6, are copied without re-scoring. Summary, threshold, metric and token functions are reused unchanged; the segmented CSV writer is shared with existing aggregation.
- New aggregate `real_calls` retains the earlier convention: existing retained-segment 84 plus the new calls. `total_charged_calls` is 105 plus the new calls; `archived_charged_calls=21` preserves the extra aborted-attempt charge. The suite records inherited 105, newly charged `real_calls`, and cumulative `total_real_calls`.

Validation: `python -B -m unittest tools.test_verify_v3` — **29 tests, OK, 1.282 s**, exit 0, final run on 2026-10-14 JST. Four added mocked tests cover the allowlist, existing-target refusal, unchanged-driver directory/artifact compatibility, and substitution/preservation with cumulative call charging. A read-only frozen-file comparison found changes only in the two permitted Python files; scoring, gold, thresholds, order, controls and driver remain unchanged.

Future host commands, **not executed**. Frozen verification stays strict: the supervisor must first bind the reviewed changed code bytes in the current manifest through the existing freeze process, preserving the previous manifests/base aggregate and keeping version `verify-v3-reviewed-r1-solfix`. No freeze or manifest edit was performed here. Refresh the existing quota snapshot externally before invocation and keep it current during execution.

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
python -B tools\eval_verify_v3.py rerun --prefix host-verify-v3-reviewed-r1 --ids geometry-G5-r1,geometry-G1-r2 --run-manifest design\cad-harness-verify-v3\SHA256.run-r1.json --quota-snapshot C:\dev\CAD-HARNESS\.tmp\verify-v2-supervisor-quota.json --codex C:\Users\backo\.codex\packages\standalone\releases\0.159.2-x86_64-pc-windows-msvc\bin\codex.exe
python -B tools\eval_verify_v3.py aggregate --prefix host-verify-v3-reviewed-r1 --suffix host-reviewed-r1-solfix-rerun2 --run-manifest design\cad-harness-verify-v3\SHA256.run-r1.json --rerun2
```

Expected new outputs:

- `reports/cad-run/host-verify-v3-reviewed-r1-verify-v3-suite-mvp1-rerun2/{plan.json,progress.jsonl,suite-run.json}`.
- `reports/cad-run/host-verify-v3-reviewed-r1-geometry-G5-r1-mvp1-rerun2/` and `reports/cad-run/host-verify-v3-reviewed-r1-geometry-G1-r2-mvp1-rerun2/`.
- `reports/aggregate-verify-v3-host-reviewed-r1-solfix-rerun2.json` and `.csv`; existing output names are refused, never overwritten.
