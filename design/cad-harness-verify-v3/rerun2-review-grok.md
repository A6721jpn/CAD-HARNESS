READY

Diff is only `tools/eval_verify_v3.py` and `tools/test_verify_v3.py`. `RERUN2_IDS` is exactly `geometry-G5-r1` and `geometry-G1-r2`. `rerun2_ids` rejects any other, partial, or duplicate list before load or launch. The provider-annotation set must be those same two preserved `server_overloaded` failures. Episodes are taken from frozen order (G5-r1, then G1-r2), both `route=source` and `max_calls=4`, through `agent.run_driver(..., provider_retry=True)` and the existing `record()`. The driver file, `summarize` thresholds, gold, and `run-order.json` are not edited. The `-rerun2` directory is only a rename of a new `-mvp1` execution plus path updates in that new report.

Original segment-1 files, the resume-1 tree, and the existing `*-solfix` aggregate JSON/CSV are hashed before the run and checked after. `write_json` and the CSV use exclusive create. Existing suite, episode, or staging paths raise `rerun2_prefix_exists`. The new suffix must not already exist.

Charge starts at `RERUN2_SPENT=105` of 163 with no suite deadline. `before_episode` reserves 8, so the ceiling is 113. New calls are `guard.calls-105`; `total_real_calls` is the cumulative count. The aggregate keeps `real_calls` as 84 plus the new calls, sets `archived_charged_calls` to 21, and `total_charged_calls` to 105 plus the new calls, and rejects a total above 163. Quota remains the unchanged 55/60 check on every `before_call`. The 600 s overload resend is the existing provider-retry path.

Substitution builds replacements only for those two IDs. The other 58 rows, including A5/A6, are the base aggregate objects, not passed through `record()`. `substituted_rows` keeps `original` and `replacement`. `summarize` is called unchanged.
