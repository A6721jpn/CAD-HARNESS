# PHASE 3 smoke (supervisor, 2026-10-10 JST)

Commit under test: f19001a. Host DPC-019, FreeCAD 1.1.4 bin\freecadcmd.exe, recipe freecadcmd, --timeout-s 300. No GUI, no Sol rollout, no N=5. Claude Code did not take part (organization disabled Claude subscription access for Claude Code).

## Unit tests
python -B -m unittest tools.test_cad_run (Python 3.12.10): Ran 11 tests in 0.283s, OK.

## good: tools/fixtures/cad_run_a_build.py -> reports/cad-run/smoke-good-1010
exit 0, wall 2.99 s (PowerShell), events preflight 23:14:16.378 -> run_finished 23:14:19.299 JST (2.92 s; launch->worker_ready 0.83 s).
status ok, probe_status pass, cad_exit_code 0, cleanup_status exited (cleanup_action none), document_closed true, predicate_diff [].
Probe: bbox 40.0000 x 30.0000 x 20.0 (x -20..20, y -15..15, z 0..20), volume 22239.9556819442, area 5364.637121611783, faces 15, solids 1, valid true. removed_warning_lines 2.

## broken: fixture copy + `build = build_without_fillet` (reports/cad-run/_inputs/broken_no_fillet_1010.py) -> reports/cad-run/smoke-broken-1010
exit 1, wall 0.45 s, events 23:14:25.797 -> 23:14:26.169 JST (0.37 s).
status failed, failed_phase probe, probe_status predicate_fail, code_owner script, next_actor sol, cad_exit_code 0, cleanup_status exited, message_code worker_failed.
Probe: bbox 40 x 30 x 20, volume 22500.0, area 5550.0, faces 11, solids 1, valid true. predicate_diff [volume, faces, feature_counts, feature_chain, outer_fillet].

Processes: before/after both runs only sldworks_fs (pid 29356, untouched); owned freecadcmd pids 40520 / 6736 exited.

## Observations (open)
- worker-events.jsonl lines carry no ts; parent stamps build_finished/probe_finished at merge time, so build vs probe time cannot be separated.
- event_seq 8 reuses build_finished for the stderr capture record (stderr_bytes/sha256) after cleanup; a distinct capture event name would be clearer.
- #9 (Pad/Pocket Type "0"): worker-result.json does not record str(Type), so still undecided.
- Only one recipe (freecadcmd) and one failure class (predicate_fail) were exercised; launch/timeout/dialog paths are covered only by no-CAD unit tests.
