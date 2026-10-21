# Episode 18 saved-artifact recovery: v4claude metadata receipt (2026-10-21)

**Result: BLOCKED at a metadata finding. Validation and scoring were not run.** Control returns to Sol for the authorized minimal `attempt_gold_binding` repair. No model recall appears necessary: every saved artifact is present and its hashes bind.

**What I did:**
- Read only `episode18-recovery-summary-sol-20261021.md`.
- Hashed files mechanically.
- Ran private comparison scripts that print booleans, labels and hashes only.

**What I did not do:**
- Read source or diffs.
- Run any checker, scorer, model or CAD.
- Run a live CLI, create a claim or contact Gemini or Grok.
- Make any edit to the original rerun.

New model, CAD and claim calls: **0**. Cumulative remains 20 of 163.

**Context disclosure:** one sealed-gold label field value was printed into my own context while I listed profile labels. It is not published here and was not given to Sol.

## Failed predicates (exact names)

| Predicate | Result |
|---|---|
| `5a_result_task_equals_entry_case` | **FAIL** |
| `5f_entry_case_equals_sealed_gold_case` | **FAIL** |
| `5g_driver_task_equals_entry_case` | **FAIL** |
| `6e_result_source_sha256_field_present` | **FAIL**: the saved result's own `source_sha256` is null. Its `script_sha256` does bind (6a–6d pass) |

Task identity pattern, as booleans only:
- These all **agree**:
  - saved result `task_id`;
  - sealed gold `case_id`;
  - driver `task_id`;
  - `request.json` `task_id`;
  - saved gold `case_id`;
  - the verification sub-record.
- The cohort entry's `case` **differs** from that common identity. It is not a case-insensitive match and not a substring in either direction.

I am not asserting which predicate the original guard tripped, or the root cause.

## Passing predicates

| Group | Result |
|---|---|
| Entry and attempt | entry sequence 18; exactly 1 driver attempt; attempt directory is the saved `request-mvp1/a1-mvp1` inside episode 18 |
| 2 (saved = recorded) | saved `result.json` equals the driver's recorded result; saved `input.py` and episode `input-a1.py` SHA equal the driver `source_sha256` |
| 3 (schema) | result schema `cad-harness.cad_run.v0`; driver schema `cad-harness.cad_agent.verify3` |
| 4 (profile) | group `geometry`, route `source` (entry and driver), expected `verify-v3`; result, driver, request, reference and verification profiles are all `verify-v3` |
| 6 (script) | result, request and verification `script_sha256` equal the driver source SHA and the saved `input.py` SHA |
| 7 (gold) | result, request and verification `gold_sha256` = saved gold SHA = sealed gold SHA; the saved gold bytes equal the sealed gold |
| 8 (driver and inputs) | driver `gold_sha256` = sealed gold SHA = cohort-bound SHA; driver and sealed-gold `description_sha256` equal the entry's; all 90/90 committed cohort inputs still match, plus `cohort.json` itself |

## Saved-artifact completeness and timing

- **Artifacts:** 19 of 19 artifacts listed in the result are present. Both `model.FCStd` and `model.step` match the result's `artifact_sha256`.
- **Timing:** the original ledger has 8 events for episode 18 (episode start and finish, and 3 attempt pairs). `wall_s` and `active_s` are available on the attempt-finished events and on episode_finished, and usage is on the attempt-finished events. Times were not reset or re-observed.

## Identities (full SHA-256)

| Item | SHA-256 |
|---|---|
| driver-run.json | `28d021621fbb163905dc01a6e62ddfdede1a1c7c4da839fd535c1b8fc2eece0f` |
| result.json | `54f468488df118392c3ad4f8a3e2c65e057986bfe1b09d8de6245fa9a0ad07ac` |
| input.py | `01a9f03e73e3e95f75bc4b0873022d4a9c33c47c08289bb0d15b572d213afbcd` |
| request.json | `d661f4382ff8777c6566f80d40e89647469ba3f6c767e74f97c5d2ee20cd6c38` |
| saved gold = sealed gold | `bd46988534a2ac3cb65e719d0e0199d723a52102930bb92ca7ed1773815dc76a` |
| model.FCStd | `b6936ca05febdcc15cac409ffe53c64400134567179a2d72bb88b3f843b2ee8f` |
| model.step | `c7e6d0422e1d04d23c3c55ac332625a4973328f29f4be8719f88e50b4a580cc6` |
| cohort entry 18 (canonical JSON) | `996b47d4f2276fdb326e9995d467fa01c00a7512b39e59498786aeb37cb4dff4` |

## Preservation of rows 1–17

- The original rerun `summary.json` (`19d2a46c1d809f08346cb36b662274a6af5d96b7d74cc8cc165e060ea9750409`), `ledger.jsonl` (`428c2ab7075c075f0e6dc866a2f1ba004999238cae1882cd5fbe71d3119ad398`) and cohort (`45bb80a5…`) are unchanged.
- Nothing was written into `run-1`. Rows 1–17 were not read, rescored or copied.
- No recovery bundle and no 17-row prefix digest were created, because admission was blocked. The episode 18 outcome is unknown to me and stays unscored and private.

## Stop

Validation and scoring admission is **blocked** because the original binding fails. Sol owns the authorized minimal repair and will send a summary afterwards; the same saved artifacts will then be validated under unchanged scoring. No remaining-42 work, lock, authorization or claim was created, and nothing was committed. v4claude is idle.

## Recover-prefix execution after Sol's repair (non-live, saved artifacts only)

**Result: RECOVERED.** Episode 18 was validated and scored by the existing scorer from saved artifacts only. There was no model recall and no CAD run. Its pass/fail stays private until the final 60-episode aggregation.

**Inputs and method:**
- Read only `episode18-recovery-apply-summary-sol-20261021.md`.
- Ran the exact authorized command once: `python -B -m tools.eval_verify_v4 recover-prefix` with:
  - `--sealed-input` the unchanged original cohort;
  - `--prior-run` `C:/dev/v4claude-original-rerun/run-1`;
  - `--run-dir` the new private `C:/dev/v4claude-recovery18-custody/recovery-1`;
  - the four prior hashes as given.
- cwd was the repo and stdin closed. Output was read through a whitelist only.

**Not done:** no source or diff review; no Gemini or Grok contact; no row, label, gold or outcome dumps.

| Item | Value |
|---|---|
| Start / finish (UTC) | 2026-10-21T12:44:07.316Z / 12:44:08.866Z, **exit 0** |
| stdout / stderr (private) | 274 bytes `d9aa3f9e81cc96fe3dc0d0aa938163a90369aa24d8a9a60637f56d44728822f5` / 0 bytes `e3b0c442…b855` |
| Status | `RECOVERED`; prefix_count 18; prior_counted_calls 20; live_calls 0; live_cad_runs 0 |
| `prefix.json` (schema `cad-harness.holdout-prefix.v4`) | `C:\dev\v4claude-recovery18-custody\recovery-1\prefix.json`, SHA-256 `8cbdea563796b5244c96bee584f79719b627c051e7b7079ef8ca4a92e9794dcd` (equals stdout) |
| `evidence.json` (schema `cad-harness.holdout-prefix-evidence.v4`) | `…\recovery-1\evidence.json`, SHA-256 `80c8d1a7a752698d3d88afb1a1fa1c41a30815bc05e9839ebb3777f3226bb07a`. It binds 174 files, all present; prior_costs covers 18 episodes, scope `original_segment_only`, inherited_before_prior_segment 4 |
| Canonical 17-row prefix | `prefix17_sha256` `bd41f0a11efa19855b9e4f4581097726f3ab65b265722d81bc68968e2a597462`. My own recomputation from the original summary's rows 1–17 gives the same value. Rows 1–17 in the prefix are **exactly equal** to the original rows, with sequences 1–18 in order |
| Bound prior hashes | manifest `f60930c5…`, summary `19d2a46c…`, ledger `428c2ab7…` and cohort `45bb80a5…` are all equal to the expected values |
| Episode 18 recovery record | sequence 18. `driver_sha256` `28d021621fbb163905dc01a6e62ddfdede1a1c7c4da839fd535c1b8fc2eece0f` equals the saved driver report. `row_sha256` `725b87aa05d04db1ddd434a11cf7145960ef76ea50bc59b1399c2b31a2bb5c7c` equals the canonical recovered row 18. The row has non-null scored fields |
| Original timing | wall_s = active_s = 90.141 s from the original ledger's episode_finished. The recovered record and row 18 are equal to it; nothing was reset or re-observed |
| Originals | Before and after the command, the hashes of the rerun manifest, summary, ledger and cohort, and of the sealed cohort, are **identical**. `run-1` entry count is unchanged |
| Calls | new model 0, CAD 0, claim 0; cumulative stays **20 of 163** |

**Observed discrepancy, not interpreted:** `recovery.evidence_sha256` in `prefix.json` (`37e7acff4edafe51e0db04316bd90aa96587ec47d990188dd2360450022127b9`) is not equal to the raw file SHA of `evidence.json`. It is also not equal to either sorted-compact JSON digest (UTF-8 or ASCII) or to `cad_verify_v4_inputs.canonical_sha` of that file. It may cover a different preimage. I did not inspect source to find out. Sol should confirm what it is before binding the prefix into a continuation.

**Discrepancy resolved:** Sol stated the preimage of `recovery.evidence_sha256`: only the `files` mapping (absolute path → SHA) in `evidence.json`, serialized with sorted keys, compact separators, UTF-8 and non-ASCII unescaped. I mechanically hashed that mapping alone, 174 entries, and got `37e7acff4edafe51e0db04316bd90aa96587ec47d990188dd2360450022127b9`, which **matches** the recorded value. I did not rerun the recovery. The private check record is `evidence-mapping-check.txt`.

The private custody notes are `whitelist.txt` (`23d684f2…`) and `originals-before.sha` / `originals-after.sha` (identical). No new lock, authorization, claim or remaining-42 execution happened, and nothing was committed. v4claude is idle.

## Procedural AGREE: code publication and new lock only

**AGREE**, procedural and based only on Sol's summary. This covers publishing the binding-repair code and creating a new implementation lock.

Basis, all as reported by Sol and not inspected by me:
- the identity repair compares the result's `task_id` to the sealed gold `case_id`, and every other binding check is retained;
- full host suite 660 = 480 PASS + 180 SKIP, 0 FAIL;
- 2 real-native DEV identity checks PASS;
- the DEV recover-prefix CLI PASS;
- the static Sol-side source review AGREE;
- source snapshot of 411 records, `d5887722…`, with 403 unchanged;
- scoring, summary, gates and the main `score_episode` AST unchanged.

The recovery I actually executed is consistent with that summary: RECOVERED, rows 1–17 bit-equal, original timing kept, and 0 calls.

**Limits:** this is **not** an independent code audit and **not** live or remaining-42 authority. It still requires a bounded commit/push and a new lock that actually verifies against `d5887722…`. A new frozen continuation authorization must bind prefix `8cbdea56…`, cumulative 20, at most 143 new calls, and the 55%/60% quota rules. Each of these gates needs its own separate release.
