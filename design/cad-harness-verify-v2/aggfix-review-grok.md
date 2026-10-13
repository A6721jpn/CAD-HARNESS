# AGGFIX diff review (grok)

Read-only, 2026-10-13. Compared `git diff -- tools/eval_verify_v2.py tools/test_verify_v2.py` with `AGGFIX-CONSENSUS.md` and `aggfix-impl-notes.md`. No test, freeze, aggregate, FreeCAD, or Sol run. The 15/15 unit result is the impl-notes record.

verdict: READY

Tracked edits are only those two files. `SHA256.json`, `FROZEN.md`, gold, probe, runner, and the host suite records are not in the diff. Items 4–5 remain the supervisor archive, re-freeze, and aggregate.

- `tools/eval_verify_v2.py:565` replaces only the span conjunct with `abs((deadline-started)-10800) > 1e-6`. Saved run/plan timestamp equality stays exact.
- `deadline_ok` (`:595`) and `ended_elapsed_s >= 10800` (`:575`) are unchanged.
- `run` (`:409–411`) raises `Stop("aggfix_no_live_run")` when `version` ends with `-aggfix`, after `load` and before `paths` or a process. `tools/test_verify_v2.py:279–288` locks that refusal.
- `aggregate` (`:538–559`) calls `load` on the current manifest first. `--run-manifest` is optional and is read through `safe_file` with no fallback. The archive must match on every field except `version`, `created_at`, `local_commit`, and `files`; the version must be the archived version plus `-aggfix`; the file-hash delta must be exactly `{tools/eval_verify_v2.py, tools/test_verify_v2.py}`.
- After that check, version, both `sha_manifest` values, `frozen_sha256`, and driver identity use the archived manifest (`:559–566`, `:580–590`). Top-level `version`, `local_commit`, `plan_commit`, `sha_manifest`, and `frozen_sha256` stay that original identity (`:599–603`). `aggregation_identity` is added only when an archive is passed (`:557–558`, `:604`).
- `tools/test_verify_v2.py:424–501` covers the stored pair `525342.3589999999 - 514542.359`, rejects `10799.9` and `10801`, keeps a `1e-7` run/plan mismatch and the exact deadline, wall, and episode boundaries failing, and checks archive digest, third-file, current-code, no-overwrite, and no-process behavior.
- The Guard assertion at `tools/test_verify_v2.py:215–216` now checks `deadline == started + 10800`. Production Guard code is outside this diff.

No scoring, gold, threshold, order, or probe change is in the diff.
