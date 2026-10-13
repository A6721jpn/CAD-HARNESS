READY

Uncommitted diff: `tools/cad_verify_v3_agent.py`, `tools/cad_verify_v3_guard.py`, `tools/eval_verify_v3.py`, `tools/test_verify_v3.py`. Checked against `SOLFIX-CONSENSUS.md` (including the 16:39 and both 17:08 USER DECISION sections) and the impl-notes Solfix section.

Scoring, gold, thresholds, order, and the 46 records:

- `q_score`, `summarize` thresholds, quota 55/60, and Budget 900/450/450/P60/R180 are not edited. Gold files and `run-order.json` are not in the diff. `transition` rejects any gold, order, Probe, model, CLI, AGENTS, or plan-identity change. The allowlist is the four code files above; new manifest keys are only the four solfix documents.
- The only pass-predicate edit is ask/completion using `logical_calls` when that field exists, else `len(calls)`. Segment-1 reports have no `logical_calls`, so the 46 re-score through the old count. Rejected transports are uncharged and are not an extra scored call.
- Sequences 1–46 must already be `completed` and are not in the resume slice. `order['entries'][46:]` is q-A5-r5, then sequences 48–60 (14 ids, frozen order). Original suite and episode bytes are hashed before and after. Aggregate scores sequences 1–46 from segment 1 and A5-r5 only from segment 2. G5-r1 and G1-r2 stay failed rows; the provider note is a separate annotation. Inherited spent calls stay 54. Ceiling stays 163.

Decisions present in the diff:

- Rejection is only a complete typed `codex_error_info=server_overloaded` with no final or assistant output. Rollout is used only when stdout has no typed code, for one bound session. Free text, unknown errors, timeouts, parse failures, and CAD failures do not resend.
- Each rejection waits 600s in chunks of at most 60s and resends the same argv, prompt, and context, with no attempt cap. The wait is clipped by the episode stage clock. Quota stops stay. A rejection refunds the shared call and does not consume a P or R slot. It does not by itself stop the suite.
- Resume sets the shared deadline to `None` after checking the archived 10800s span, start, and 54/163. There is no new 10800s clock and no 20:00 cutoff. The 960s reserve runs only when a deadline exists. Segment 2 is `deadline: none (user decision 17:08)` with `deadline_monotonic` null. Segment 1 keeps its own `deadline_ok`. Cold `run` of `verify-v3-reviewed-r1-solfix` is rejected.
