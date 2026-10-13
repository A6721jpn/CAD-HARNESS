**VERIFY v3 results — 2026-10-13**

**Final verdict: PASS; `bar_met=true` for the signed segmented solfix recovery.** The final [aggregate JSON](../../reports/aggregate-verify-v3-host-reviewed-r1-solfix.json) records `valid_suite=true`, `complete=true`, `core_complete=true`, `versions_consistent=true`, `deadline_ok=true`, `stop_reason=null`, and all eight thresholds true. The matching [aggregate CSV](../../reports/aggregate-verify-v3-host-reviewed-r1-solfix.csv) contains the episode results. These are the authoritative scoring artifacts; this report does not re-score them.

Aggregate identity: prefix `host-verify-v3-reviewed-r1`, version `verify-v3-reviewed-r1-solfix`, implementation `27de198`, plan `fd7e215`, created at `2026-10-13T11:07:46.504231+00:00`. Its final manifest digest is `f4d13350c3070020d0e655b238be8dc9abff92b352b12964110d37634647cd3c`.

The retained suite has **60/60 completed, 58 passing**, including **51/51 completed core observations, 49 passing**. These counts are direct sums of the aggregate's episode rows, not a pooled estimate of general accuracy. Dev and completion observations are outside `bar_met`. Resume #4's [segment-2 suite](../../reports/cad-run/host-verify-v3-reviewed-r1-verify-v3-suite-mvp1-resume1/suite-run.json) has **14/14 completed and PASS**, with no stop; it executes A5-r5 first, then sequences 48–60. The original 46 completed records remain unchanged. A read-only comparison against the final resume plan found no differences in its 770 bound original files.

The following observations come from `summary.per_part`, `summary.fault`, `summary.thresholds` and the aggregate rows. The requirements are the unchanged [signed plan](PLAN-V3-CONSENSUS.md).

| Threshold | Required result | Aggregate observation | Result |
| --- | --- | --- | --- |
| `source` | G1–G5 at least 8/10; each at least 1/2; actual source fallback | 8/10: G1 1/2, G2 2/2, G3 2/2, G4 2/2, G5 1/2; source threshold true | PASS |
| `complex` | G6 at least 2/3 | G6 3/3 | PASS |
| `stock` | S3 at least 4/5 | S3 5/5 | PASS |
| `defaults` | A4 at least 2/3 | A4 3/3 | PASS |
| `ambiguity` | A5 and A6 each at least 4/5; zero critical invention | A5 5/5, A6 5/5; critical invention count 0 | PASS |
| `faults` | Establishment and designated detection 6/6; final gates at least 4/6; each fault case at least 1/2; successful source and spec repair | Reached, established and detected each 6/6; final gates 6/6; F4, F5 and F6 each 2/2; each has 2 repair calls, covering source and spec repair | PASS |
| `mvp` | At least 8/10; every P case at least 1/2 | 10/10; P1, P2, P4, P5 and P3 each 2/2 | PASS |
| `legacy` | All A/B good/broken controls 4/4 | A-good, A-broken, B-good and B-broken each 1/1 | PASS |

| Cohort (`per_suite`) | Planned | Completed | Passing |
| --- | ---: | ---: | ---: |
| Dev, unscored | 3 | 3 | 3 |
| Legacy | 4 | 4 | 4 |
| MVP | 10 | 10 | 10 |
| Geometry | 18 | 18 | 16 |
| Defaults/clarification (`q`) | 13 | 13 | 13 |
| Completion, outside the bar | 6 | 6 | 6 |
| Forced faults | 6 | 6 | 6 |

C4 and C5 each have 3/3 correct initial questions, 3/3 post-answer first-attempt passes and 3/3 final completions; `not_reached=0` for each. Each conditional completion rate is `1.0`, with the recorded Wilson95 interval `[0.43849391955098227, 1]`. Across the retained suite, `parse_repair_calls=0`, `repair_calls=6`, and `fallback_origins={"model":14}`. Forced-fault pass per established fault is 6/6, rate `1.0`, with Wilson95 `[0.6096569663469354, 0.9999999999999999]`.

The aggregate explicitly binds two segments:

| Segment | Identity and manifest | Recorded wall seconds | Calls in retained-segment ledger | Deadline evidence |
| --- | --- | ---: | ---: | --- |
| 1 | `verify-v3-reviewed-r1`; archived [SHA256.run-r1.json](SHA256.run-r1.json), digest `743e77764ff768a12234d63962ad2f8cdc7852e55ee1cbe814272a39139f7673` | 2366.75 | 54 | Original deadline 545790.093; `deadline_ok=true` |
| 2, resume #4 | `verify-v3-reviewed-r1-solfix`; final [SHA256.json](SHA256.json), digest `f4d13350c3070020d0e655b238be8dc9abff92b352b12964110d37634647cd3c` | 1819.890000000014 | 30 | `none (user decision 17:08)`; `deadline_monotonic=null` |

**Root causes, fixes and refreezes.** [SOL-FAILURE.md](SOL-FAILURE.md) establishes transient provider capacity rejection: exact structured `codex_error_info=server_overloaded`, with no assistant/final output, in G5-r1, G1-r2 and the original A5-r5. The original harness classified the first two as interpretation failures and stopped on A5's missing final artifact. It also lacked saved transport output for those original calls. The retained original A5 partial remains an annex; only resume #4's A5 answer is scored.

| Amendment | Root cause and resulting behavior | Implementation commit | Refreeze commit |
| --- | --- | --- | --- |
| Solfix | Strict structured rejection classification and bounded transport capture; 600-second byte-identical resend policy with no overload retry cap; rejected new attempts/waits separately recorded and uncharged to 163/P/R. Adds preserved-original resume and two-manifest aggregation. The final 17:08 user decision removes the resumed segment's suite deadline; quota and episode/stage budgets remain. | `ef8c694` | `671f324` |
| A1 | No-deadline guard returns infinity; flooring it at the first completion CAD launch raised OverflowError. `cap_timeout` preserves the finite episode/stage timeout and applies the shared cap only when finite. | `f898d32` | `b483cc9` |
| A2 | CRLF fixture injection and the source actually sent to CAD differed by the terminal CR. The driver re-extracts injected source; the checker previously hashed the raw injection. `fault_source_sha` mirrors that existing extraction exactly for source faults; spec faults and raw injection evidence are unchanged. | `27de198` | `3b99cf6` |

See [SOLFIX-CONSENSUS.md](SOLFIX-CONSENSUS.md), [A1 Revision 2](SOLFIX-ADDENDUM-A1.md), [A2](SOLFIX-ADDENDUM-A2.md) and [FROZEN.md](FROZEN.md). Refreezes preserved the original manifest as `SHA256.run-r1.json`, the first solfix manifest as [SHA256.solfix.json](SHA256.solfix.json), and the A1 manifest as [SHA256.solfix-a1.json](SHA256.solfix-a1.json). A1/A2 are section labels; the manifest version remains `verify-v3-reviewed-r1-solfix`. Scoring, gold, thresholds, order, rubric, Probe and controls were unchanged by these repairs.

**Archived aborted attempts are informational and unscored.** Their directories and logs were renamed and retained without deletion. The archive suffixes below apply to the original suite/episode `-resume1` names under `reports/cad-run`; none of these archived outcomes contributes a replacement score or an extra observation to the final cohort.

| Resume attempt | Archive suffix | Cause and informational outcome | Charged calls |
| --- | --- | --- | ---: |
| #1 | `-aborted-quota-stale-20261013T1850` | Stale quota snapshot; no Sol invocation | 0 |
| #2 | `-aborted-inf-overflow-20261013T1856` | A5-r5 and A6-r5 passed; C4-r1 crashed before CAD on infinity conversion. Suite and the three started episode directories retained. | 4 |
| #3 | `-aborted-fault-binding-20261013T1930` | A5-r5, A6-r5 and C4/C5 r1–r3 passed (8/8). F4-r1's driver completed with successful fault detection/repair, but the checker stopped the suite with `harness:report_binding` / `fault_source_binding`. Later entries were not started. Suite and all nine started episode directories retained. | 17 |

Logs remain at `.tmp/v3resume.{out,err}.aborted-quota-stale-20261013T1850.log`, `.tmp/v3resume.{out,err}-aborted-inf-overflow-20261013T1856.log`, and `.tmp/v3resume.{out,err}-aborted-fault-binding-20261013T1930.log`. Replaying the complete segment rather than stitching its earlier passes into the cohort preserves the frozen order and the original segment-1 records.

**Call charge: 54 + 4 + 17 archived + 30 = 105 of 163.** This is the total accepted-call budget charge across the retained original segment, both aborted attempts with accepted responses, and final resume #4. Attempt #1 adds zero. The archived 4 and 17 remain charged despite their results being unscored.

The aggregate counts only the retained scored-result segments: `inherited_calls=54`, `resumed_calls=30`, `real_calls=84`, `transport_attempts=84`. It excludes the 21 archived calls, so **84 is not the total execution charge**. Dev/completion calls remain in this ledger even though their scores are outside `bar_met`. The original 54 is inherited conservatively as recorded, including historical provider-rejection charges; there is no retrospective refund. Under the new policy overload rejections are separately recorded and uncharged. The final aggregate records `provider_rejected_attempt_count=0` and `provider_wait_s=0` for new retained-segment transport; its separate historical annotations must not be mistaken for zero historical provider errors.

**Preserved scored failures.** `geometry-G5-r1` and `geometry-G1-r2` remain segment-1 `completed=true`, `passed=false`, `failure_class=interpretation`, with zero CAD attempts and zero repair calls. In `historical_provider_attempts`, both have `original_score_preserved=true` and `summary.provider_rejected=true`, with exact `server_overloaded` evidence and `assistant_output=false`. They were neither rerun nor converted into successes. Their retained failures explain geometry 16/18 and G1/G5 each 1/2; the source threshold still passes at 8/10.

**Limitations.** This is an amended, mixed-implementation segmented recovery, not evidence of an uninterrupted run meeting the original suite-wide time limit. Segment 1 retains its original deadline evidence; segment 2 has no suite deadline by explicit user decision. The 55% soft/60% hard quota stops, 900-second episode budget and stage reservations remain. The segment wall values above exclude the full elapsed operational cost of pauses, repairs and aborted attempts; the call ledger separately includes aborted charges.

The finite, repeated case cohorts do not establish broad CAD reliability. Wilson intervals describe the recorded fixed completed cohorts only; no heterogeneous pooled success probability is claimed. Completion and dev are outside the bar. Intermediate segment-2 results were inspected before harness fixes and full replays, so this is not a fresh blind replication. No gold, thresholds or cohort order were changed in response.

Forced-fault repair succeeded, but natural repair evidence is absent: `eligible=0`, `invoked=0`, `denominator=0`, `rate=null`, `wilson95=null`; completion repair likewise has denominator 0 and null rate/interval. With zero parse repair calls and only model-origin fallbacks recorded, this run does not exercise every repair/capability route. No new provider rejection occurred in the final segment, so its results do not demonstrate live repeated-overload recovery. Backoff remains subject to unchanged episode/stage budgets. Original transport streams were not saved; historical attribution relies on the bound structured session evidence. Geometry provider-token totals are null in the aggregate and must not be treated as zero or as a complete cost estimate.

This file was prepared from existing aggregates, suites, archives and amendment/commit records by read-only inspection. No Sol, CAD, freeze, aggregate regeneration, archive operation or Git mutation was performed; no other file was edited.
