# Saved-59 final-prefix recovery: v4claude metadata receipt (2026-10-21)

**Result: RECOVERED.** This was a non-live recovery from saved records only. Sequence 59 is recorded as **FAILED** under unchanged rules and the existing repair-timeout semantics, as the USER permitted. All other outcomes stay withheld until the final 60-row aggregation.

**What I did:**
- Read only `final59-recovery-summary-sol-20261021.md`.
- Ran the exact authorized command once.
- Read the output only through a private whitelist script, `whitelist.json` `cbe580408e7595d19b7afb0c55d4cf9284d36f9d6eb5fd9c90fbc6b79c4b3f9c`.

**What I did not do:**
- Review source, diffs or private content, or talk to other agents.
- Run any model, CAD, freeze, claim or episode-60 work, or retry.
- Change rights or any original record.

## Command

| Item | Value |
|---|---|
| Command | `python -B -m tools.eval_verify_v4 recover-final-prefix`, with `--sealed-input` = the same original cohort, `--prior-run` `C:/dev/v4claude-continuation42-custody/run-1`, `--run-dir` the new exclusive `C:/dev/v4claude-recovery59-custody/recovery-1`, and the four prior hashes as given. cwd was the repo; stdin was closed |
| Start / finish (UTC) | 2026-10-21T15:19:16.646Z / 15:19:20.209Z, **exit 0** |
| Private stdout / stderr | 274 bytes `affa085951d3c10cb0168d5123e2655818613489d09fae0282aad9e67cbf0919` / 0 bytes `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| Status | `RECOVERED`; prefix_count **59**; prior_counted_calls **88**; live_calls 0; live_cad_runs 0 |

## Outputs

| Item | Value |
|---|---|
| `prefix.json` | `C:\dev\v4claude-recovery59-custody\recovery-1\prefix.json`, raw SHA-256 `944c566ab1983a524f3876fc1ca5eaaea569cf6600e5fd771851ef5ee0fb94ee` (equals stdout). Schema `cad-harness.holdout-prefix.v4`, 59 rows, sequences 1–59 in order |
| Bound prior | manifest `afdb3cca…`, summary `e879d95a…`, ledger `0d6fa929…`, cohort `45bb80a5…` |
| `evidence.json` | raw SHA-256 `4d27a13380bdd24b9dd1ebd3faa4243d3d305da8364b8b469eec65925f302608`. Schema `cad-harness.holdout-prefix-evidence.v4`, **4371** file bindings |
| Files map digest | Computed over `evidence.files` only (sorted, compact, UTF-8, `ensure_ascii=False`): `2790e851d9a82733807c898989332590d5ba7aa7a52ce5f95f2a527073b57fe6`. **Equals** `recovery.evidence_sha256` |
| Inherited cost evidence | prior_cost_scope `original_segment_only`, 18 prior-cost entries, inherited_before_prior_segment 20. The nested earlier chain has 174 files and 4 inherited calls. Old costs are not pooled |

## Preservation and sequence 59

**Rows 1–58:** these were not rescored or re-executed.
- They are **exactly equal** to rows 1–58 of the continuation summary.
- `prefix58_sha256` `c44d728a9e2a6d8e82c6f9dd10c9626cc0759759b1e7b534d69646130c9536ed` equals my canonical recomputation.
- Rows 1–18 are also equal to the earlier 18-row prefix `8cbdea56…`.

**Original row 59:** `original_row_sha256` `13cfb9adee9637f3a46da4e340ecba7f42dc079adae987cfa2f8a3a5e5671784` equals the canonical summary row 59, and the embedded original row equals it.

**Recovered row 59:**
- `row_sha256` `a7efd5376b76215942f7b226ac179f0e80dd44cb8c394f18b3eb8b3d19c42129` equals the canonical prefix row 59.
- Driver `255f78ab37084f036700cfcdde012e895172c74f35cc5d4ba023e3665c237546` equals the saved, unmodified episode-59 report.

**Status of recovered 59:**
- `passed` **false**; `completed` true; row stop_reason null.
- error_type `TimeoutExpired`; `repair_unfinished` **true**.
- The only keys that differ from the original row are `completed` and `stop_reason`, which are mechanical differences. No other field changed.

**Times:** none were reset.
- The original scored wall/active times and the ledger episode_finished times are both 359.671 s / 359.671 s.
- The recovered row's wall time equals the original's.
- The original failed call ran 177.625 s against a stored timeout of 180 s. The original report wall is 358812.0 ms.

**Tokens:** the recovered row 59 `tokens` are unchanged from the original row, keeping the null/unknown values.

**Historical flags:** these were kept as immutable evidence and not promoted.
- `raw_capture_flags`: stdout and stderr both `complete=false` / `transport_or_capture_interrupted`.
- 1 call's usage stays unknown.
- No bytes or usage were fabricated, nothing was refunded, and nothing was retaken.

## Integrity

- **Hashes taken before and after the command are identical** (`originals-before.sha` `dbc69679…` = after) for:
  - the continuation run ledger, summary, calls, manifest, cohort, parent stdout and exit record;
  - the old 18-row prefix and its evidence;
  - the old rerun summary, ledger, manifest and calls;
  - the sealed cohort.
- The full prior-run tree is also identical before and after: 6854 files, `prior-run-tree-before.sha` `dc87e259…` = after.
- **Calls and claims:** new generator calls 0, CAD runs 0, claims 0. Cumulative stays at **88 of 163**, with at most 75 new.
- **Files written:** only the new task-owned `C:\dev\v4claude-recovery59-custody\` and this receipt. Nothing was committed or pushed.

## Procedural AGREE: code publication and new lock only

**AGREE**, procedural and based only on Sol's summary. This covers publishing the code and creating a new implementation lock. Basis, as Sol reported:
- source snapshot `dc0f0fa3…`, 405 of 411 unchanged;
- the 6 scorer, summary and gates ASTs are exact, with `score_episode` `2224656b…`;
- no policy, card or deadline changes;
- the reconciled host suite is 671 = 491 PASS + 180 SKIP, with 0 unresolved. Sol does not claim this as a second clean full run;
- the guarded live-module run is 38 PASS + 1 SKIP;
- the owned-pipe smoke tests 2 PASS;
- the DEV recover-final-prefix CLI PASS;
- the static prefix AGREE, with timeout BLOCK 2 remediated.

The actual recovery above is consistent with that summary.

**Limits:**
- This is **not** a code audit and **not** live authority.
- The native-10 source proof is still a separate running gate.
- Any episode-60 generation needs, in order:
  - a separately verified new lock;
  - a frozen authorization that binds prior 88, prefix `944c566a…` and a fresh quota;
  - the USER-approved release for episode 60 only.

v4claude is idle.
