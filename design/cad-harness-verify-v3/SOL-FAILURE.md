# SOL-FAILURE — root cause of the q-A5-r5 stop (verify-v3-reviewed-r1)

Investigation: 2026-10-13 16:05–16:15 JST. The supervisor read the logs only; there was no retry inside the run.

## Evidence (observed)
1. `reports/cad-run/host-verify-v3-reviewed-r1-q-A5-r5-mvp1/driver-run.json`: call 1 (spec/question/initial), session `01a13404-7e78-7a52-a3f2-090d7dffb6b1`, exit 1, wall 3.97 s, `message_code=exec_nonzero_or_missing_final`. Quota snapshot: used 0.0%, decision allow.
2. The Codex session log for that call is `CODEX_HOME(Orca 43cffd0b)/sessions/2026/10/13/rollout-2026-10-13T15-47-52-01a13404-7e78-...jsonl`.
   - 06:47:55.442Z `token_count.rate_limits.primary.used_percent=0.0` (window 10080 min). Credits: `has_credits=true`.
   - 06:47:55.452Z `task_complete.error = {"message":"Selected model is at capacity. Please try a different model.","codex_error_info":"server_overloaded"}`.
3. The same error appears in all of today's 146 sessions on this CODEX_HOME exactly 3 times. All 3 belong to this run:
   - 15:26:50 JST: **geometry-G5-r1**, call 2 (source/initial), exit 1, 7.8 s.
   - 15:28:48 JST: **geometry-G1-r2**, call 2 (source/initial), exit 1, 8.9 s.
   - 15:47:52 JST: **q-A5-r5**, call 1, exit 1, 4.0 s.
4. The harness handled the same provider error in two different ways:
   - G5-r1 and G1-r2 were recorded as `completed=true, passed=false, failure_class=interpretation` (scored as model failures, with no CAD attempt and no repair).
   - q-A5-r5 (ask route) became `harness:missing_report_or_artifact`. The suite guard then stopped the remaining 14 episodes as not_started.
5. Codex stdout/stderr is not saved in the run directory. The provider error message is visible only in the CODEX_HOME session log.
6. Repro (16:13–16:14 JST): same CLI arguments (`exec -m gpt-6.1-sol -c model_reasoning_effort="xhigh" -s read-only --skip-git-repo-check -C <tmp> --json -o <last>`, stdin redirected), trivial prompt. 2 of 2 tries succeeded: exit 0, last=`OK`, 12 s and 10 s.
   - Side note: one earlier attempt without stdin redirection hung with no session created. That was an artifact of the repro method, not of the harness, which uses stdin=DEVNULL.
   - The CLI warns "ignoring 1 unrecognized configuration setting" on every call, including successful ones. This is not related.
7. Not the cause, based on the evidence: quota (0%), credits (present), auth (`codex login status`: logged in; auth.json unchanged since 00:02), and the account (same CODEX_HOME throughout). There was no Windows process error: exit 1 came after a completed session with a server-side error.

## Root cause (supported by 2, 3 and 6)
Transient provider-side capacity rejection (`server_overloaded`) for gpt-6.1-sol. It happened 3 times in about 21 minutes during the run and did not reproduce at 16:13.

## Harness defects exposed (inference from 4 and 5)
- (a) A provider error is not classified as one. It is treated as a model or interpretation failure (score contamination for G5-r1 and G1-r2), or as a harness stop (A5-r5).
- (b) The provider stderr/stdout and the error class are not captured in the run artifacts.
- (c) There is no bounded retry for a provider rejection that produced no model output.
