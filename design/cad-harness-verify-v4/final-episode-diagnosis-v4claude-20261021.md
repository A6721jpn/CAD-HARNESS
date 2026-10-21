# Final-episode diagnosis: v4claude metadata-only receipt (2026-10-21)

**Scope and limits.**
- **Read:** only `final-episode-diagnosis-summary-sol-20261021.md` and my own custody metadata.
- **Method:** private whitelist scripts that print only sequence numbers, enums, booleans, counts, durations and hashes.
- **Not read or printed:** source, diffs, cards, requests, gold, generated text, geometry, tracebacks, argv or raw error text, task IDs and outcomes.
- **Not run:** model, CAD, claim, freeze, repair, retry or rescoring.
- **Calls:** cumulative stays at 88 of 163, with at most 75 remaining. There was no Gemini or Grok contact.

**I make no inferred cause.** The facts below are as recorded.

## 1. Failed attempt: exactly one

| Field | Value |
|---|---|
| Episode sequence | **59** |
| Operation / stage | model / repair |
| Attempt index | 4 of 4 in episode 59 (the episode's last attempt) |
| Retained segment / charged | true / true (one of the 68 counted calls) |
| Error class (ledger) | `TimeoutExpired` |
| exit_code | null |
| wall_s = active_s | 180.172 |
| Stored timeout | Ledger: no timeout field (unknown). The seq-59 driver call record stores `timeout_s` **180** for this call, with elapsed 177.625 s |
| provider_rejected | false |

Across the run, `attempt_finished` events with an error: 1 of 106.

## 2. The two incomplete captures

Both belong to the failed attempt above (sequence 59, attempt 4).

| Stream | File exists | Recorded bytes = actual bytes | SHA matches ledger | complete flag | missing_reason |
|---|---|---|---|---|---|
| stdout | true | 99003 = 99003 | true | false | `transport_or_capture_interrupted` |
| stderr | true | 0 = 0 | true | false | `transport_or_capture_interrupted` |

The bytes on disk are exactly what the ledger recorded, and their hashes match. The incompleteness is the `complete=false` flag, set with the interruption reason. Whether additional stream bytes would have followed is **unknown**.

## 3. Structured provider summary (failed attempt)

- parse_complete true;
- assistant_output **false**;
- provider_rejected false;
- source `stdout`;
- error_infos 0, event_shapes 0.

Usage: no values are present, and all five usage fields carry missing_reason `transport_or_capture_incomplete`. This is the single "usage unknown" call. Every other model attempt has usage values except reasoning tokens, which are missing for all calls.

## 4. Scored-row coverage (current 60-row summary)

- **Rows:** 60, in sequence order 1–60. The 18 prefix rows are bit-equal in the current summary.
- **Empty placeholder pattern:** I took the pattern from the old rerun's unscored row 18 (10 null keys), which is identical to the unstarted-row pattern. **Only sequence 60** matches it in the current summary.
- **Cohort `scored=false` by design:** sequences 1–3 and 49–54.
- **Structural note, not judged:** sequences 39–48 have `final` null but a typed `q_score`, `passed` and `completed`. They are populated rows, not placeholders. Whether `final` = null is normal for their route was not assessed, since that would need source.
- **Sequence 59:** it has a populated row (`passed` bool, `final` present, `completed` bool) with row `stop_reason` = `transport_or_capture_interrupted`.
- **If only sequence 60 were added:** no other row would be left as an empty placeholder. Sequence 59's row would stay as recorded, including its interruption stop_reason.

## 5. Impact on existing results

- **Capture and usage gaps:** they belong only to sequence 59. None belongs to rows 1–58.
- **Sequence 59 depends on the failed attempt.** That attempt was its final repair call, and the episode-finished status for 59 is `incomplete`; the other 40 episodes are `completed`. The attempt lacks completed capture flags and usage.
- **Affected sequence: 59.** Whether its recorded row is a valid result under the unchanged rules is **unknown** here. An unknown is not a PASS.

## 6. Saved driver report for sequence 59

- 1 report present, schema `cad-harness.cad_agent.verify3`.
- `status` `failed`; `message_code` `transport_or_capture_interrupted`.
- final out dir present; `ended_at` present; `geometry_ok` is a bool.
- Calls recorded: 3, all invoked, with exits [0, 0, null]. Attempts recorded: 1. llm_calls 3, cad_attempts 1, repair_invoked true.
- Call `timeout_s` [419.672, 402.266, 180] against elapsed [0.328, 17.734, 177.625].

The ledger counts 4 attempts for this episode: model and CAD operations together, versus the driver's 3 LLM calls plus 1 CAD attempt.

## 7. Integrity

- Hashes taken before and after the diagnosis are **identical** for:
  - the continuation ledger `0d6fa929…`, summary `e879d95a…`, calls `ad3e48a1…`, manifest `afdb3cca…`, cohort `45bb80a5…`, parent stdout `e48aeff5…` and exit record `6c0d899f…`;
  - the prefix `8cbdea56…`;
  - the old rerun summary `19d2a46c…` and ledger `428c2ab7…`;
  - the sealed cohort.
- **Calls and claims:** new model calls 0, CAD runs 0, claims 0.
- **Files written:** this receipt and two task-owned private notes: `diag/ledger-diag.json` `cb59ec9e7f199bb701f849e94ca11350e3262412a22d646ea1c8507702b36aa4` and `diag/coverage.json` `d0c69fb6b46de2f5e708f6e9a24fc38789f1511500d6656dbf5568efac45c268`.

**ASK.** An existing result appears to be affected: sequence 59's final repair call hit `TimeoutExpired` at about 180 s. Its capture is flagged incomplete and its usage is unknown. Under the USER condition, this needs a STOP/ASK before any repair or before starting episode 60. Sol analyzes public source separately. v4claude is idle, and nothing was committed or pushed.
