# VERIFY v4 — Phase 1–2 implementation notes

2026-10-14. Implemented the signed [consensus plan](PLAN-V4-CONSENSUS.md)'s offline measurement and consolidation phases. **0 live Sol calls, 0 live CAD runs, no freeze and no git operations.** Holdout and pilot remain `not_run`; overload robustness remains `UNVERIFIED`.

## Files

| New file | Purpose |
| --- | --- |
| `tools/cad_verify_v4_ledger.py` | Append-only journal; complete binary stdout/stderr archives with bounded parser/display tails; five token fields; usage deduplication/cumulative reconciliation; nullable Decimal pricing; per-call/episode/run accounting; read-only historical backfill |
| `tools/cad_verify_v4_agent.py` | Recorded-runtime interface and one request path; isolated dependency bindings around the unchanged v3 driver; request/skill submission evidence, typed factual feedback, quota/call slots, simulated active versus wall clocks |
| `tools/eval_verify_v4.py` | Offline CLI facade, policy/contract preflight, batch adapter, cost CSV and historical aggregate replay using existing v3 scoring/export helpers |
| `tools/test_verify_v4.py` | 19 deterministic tests; subprocess launch is denied by mocks |
| `skills/cad-harness-v4/SKILL.md` | Consolidated instruction/runtime-data protocol and embedded machine policy |
| `skills/cad-harness-v4/modeling.md` | Byte-identical copy of the existing modeling skill |
| `skills/cad-harness-v4/contracts.md` | Existing spec/schema, capability, clarification, source and repair contracts, checked against their original definitions |
| `design/cad-harness-verify-v4/policy.json` | Machine policy, zero live authorization, existing caps and pending live decisions |
| `design/cad-harness-verify-v4/ledger.schema.json` | Versioned event/stream/nullable-usage schema |
| `design/cad-harness-verify-v4/pilot-rubric.json` | Unregistered rubric template; empty user-task roster, null judge, `not_run` |
| `design/cad-harness-verify-v4/impl-notes-p12.md` | This handoff |

No v3 frozen source, old skill, gold, thresholds, order or old report was edited. The v3 driver is loaded with private adapter bindings; the imported original module is not monkey-patched. Existing parsing, compilation, verification and repair decisions remain in that driver/helpers. All CAD results used during implementation were unit mocks or copied recorded artifacts.

## CLI

From `C:\dev\CAD-HARNESS`:

```text
python -B -m unittest tools.test_verify_v4
python -B tools/eval_verify_v4.py preflight
```

The exact successful historical backfill and aggregate commands were:

```text
python -B tools/eval_verify_v4.py ledger --source-root reports/cad-run --history v3 --aggregate reports/aggregate-verify-v3-host-reviewed-r1-solfix-rerun2.json --run-dir reports/verify-v4-v3-backfill-p12-r2
python -B tools/eval_verify_v4.py aggregate --replay-aggregate reports/aggregate-verify-v3-host-reviewed-r1-solfix-rerun2.json --run-dir reports/verify-v4-v3-replay-p12-r2
```

These output directories now exist. Use a new unused directory for another offline derivation; outputs are exclusively created. The backfill writes `ledger.jsonl`, `summary.json` and `calls.csv`. The aggregate writes `summary.json` and `rows.csv` using the existing aggregate writer.

The request and batch interfaces are:

```text
python -B tools/eval_verify_v4.py request --request <request.txt> --acceptance <checker-card.json> --replay <recording.json> --run-dir <unused-output-dir>
python -B tools/eval_verify_v4.py run --phase holdout --replay <recorded-roster.json> --run-dir <unused-output-dir>
python -B tools/eval_verify_v4.py run --phase pilot --run-dir <unused-output-dir>
```

The last command records `not_run` because no user pilot tasks/human judgment have been supplied. A replay batch always labels itself offline and never claims a fresh holdout or real pilot. Batch requests call the same single-request path; the parent ledger imports linked evidence and accounts for the fixed roster, phase reservation, operational stops and unstarted entries.

A checker card uses `schema=cad-harness.acceptance.v4`, `request_sha256`, `route` (`spec`, `source`, `ask` or `completion`), an applicable private `gold` path, and optional `max_calls`, `preview`, `rubric` and genuine `answer`. Checker gold is not submitted to the model. The original request bytes remain the user message, including completion calls; genuine answers and measured diagnostics use skill-defined runtime data. Each physical invocation archives its actual argv/submission hash and raw streams.

A recording uses `schema=cad-harness.replay.v4`, `evidence_mode=recorded`, an explicit timezone-bearing `started_at`, simulated `quota_percent`, and ordered `steps`. Each step identifies `operation` (`model` or `cad`), recorded `elapsed_s`, `returncode`, `stdout_path` and `stderr_path`; a model step can provide `final_path`, and a CAD step provides `artifacts_dir`. Paths stay within the recording bundle. Replayed CAD artifacts must pass the existing driver's source/gold/result bindings. Replay elapsed times and quota are simulation inputs, not observations of a live account or new CAD execution.

A replay roster uses `schema=cad-harness.replay-roster.v4` and ordered `entries`, each containing relative `request`, `acceptance` and `replay` paths. No sealed holdout/private trial input is accepted by the Phase 1–2 batch command.

`--rate-source <user-file>` is optional on `ledger` and `request`. Without it all unsupported prices remain null. A supplied card must identify user provenance, applicable product/model/tier, source/effective date/currency and explicit billing-category token coefficients/rates. Recorded billing identity must match. Cached/reasoning subsets are not automatically charged twice; synthetic unit-test rates are not real prices.

`--manifest` can verify supplied file commitments without creating a manifest. No manifest is needed for offline development. `freeze` is explicitly unavailable, and a request without a replay/injected unit runtime fails before output allocation or executable launch. Future live interfaces cannot bypass the current zero authorization.

## Validation and historical reconciliation

Final test command: `python -B -m unittest tools.test_verify_v4`.

**Ran 19 tests in 1.282s — OK.** Coverage includes nullable rollups, billing categories, complete byte capture/bounded memory, missing/unfinished evidence, archived and partial historical calls, one-entry spec/source/repair/completion paths, unchanged request/skill instructions, shared P/R limits, six consecutive overloads, byte-identical resends, full versus active time, quota interruption, timeout capture, recorded CLI/batch execution, existing aggregate predicates and blocked live/freeze paths. No Sol or CAD executable was launched.

The final [backfill summary](../../reports/verify-v4-v3-backfill-p12-r2/summary.json) reconciles **88 retained-segment calls + 21 archived calls = 109 total charged calls**, from 109 discovered physical model attempts. Bindings include the SHA-verified base aggregate and the original partial A5-r5 call; final selected scoring rows alone are insufficient to reconstruct retained-segment expenditure.

All five complete token totals remain null because three calls have missing usage; known subtotals and missing counts are retained. Prices remain null without a user rate source. Historical total operational wall time remains null because complete operation/interruption boundaries were not recorded; available episode and interruption evidence is preserved without summing overlapping intervals or inventing downtime.

The [aggregate replay](../../reports/verify-v4-v3-replay-p12-r2/summary.json) has `identical_summary=true`: its entire v3 summary matches the original, including all eight thresholds true and `bar_met=true`. This is historical predicate-equivalence evidence, not a new v4 holdout result. Natural/parse/completion-repair denominators retain their existing definitions.

Intermediate offline directories `reports/verify-v4-v3-backfill-p12` and `reports/verify-v4-v3-replay-p12` are retained unchanged. The first backfill exposed a missing link to the original partial call; the authoritative `-r2` output above includes it. These are offline derivations, not additional model/CAD attempts.

Protection checks matched the starting snapshot: byte hashes for 162 v3/old-skill files, and sizes/modification timestamps for 13,497 pre-existing report files. No old report was rewritten.

## Open items before live phases

- Appoint the independent holdout author, separate control reviewer and custodian; establish access isolation and supply validated fresh commitments. No fresh holdout content was authored here.
- Authorize the live call allowance. Current authorization remains **0**; 163 holdout + 40 pilot = 203 is still the plan's proposed reservation, not implementation permission to spend.
- Confirm the live clock amendment. Offline tests exclude verified rejected-attempt transport plus the full 600-second backoff from enclosing active budgets, preserve numeric work limits, and include every second in wall time. Overload retries have no cap and consume no accepted/P/R slots. Independent quota/cancellation stops remain explicit.
- Supply user-only pilot tasks and a named human judge; agree/register the rubric, critical dimensions/tolerances, first-handover fatal rule and adoption evidence before trial. Otherwise `not_run`.
- Supply an applicable rate source if a supported price estimate is desired; continued null pricing is an allowed default.
- Complete implementation review and later authorized live-runtime/host integration and freeze. Current executable transports are deliberately recording/unit-runtime only; there is no live launch path in Phase 1–2. No fresh run, native control run, live overload recovery or real pilot outcome is claimed.
