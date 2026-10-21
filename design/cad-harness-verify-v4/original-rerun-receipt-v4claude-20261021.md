# Original60 rerun: v4claude custody receipt (2026-10-21)

v4claude is the custodian only, not the CAD generator. This receipt is public and holds aggregates only. Raw captures, the ledger, model streams, cohort content and per-case outcomes stay private in `C:\dev\v4claude-original-rerun\`. The cohort is the **same** original60 used in the prior attempt; it is reused, not newly fresh. I did not review source, diffs or generated outputs, and had no contact with Gemini or Grok.

## 1. Admission: mechanical checks, all passed before the claim

| Check | Result |
|---|---|
| HEAD / tree / `origin/herdr/v4` | `8b7aa8be…` / `239c44a2…` / `8b7aa8be…` |
| Implementation lock `verify-integrated-lock` | exit 0 (09:14:07–09:15:44Z). `sha256_file` `cd4d924b…`, raw manifest `0c6b4cdc…`. Status offline_locked, authorization null, `final_v4_ready` false, live_calls 0, 5 recipes. 411 source records with canonical digest `e50ae182…`, an exact match |
| Original freeze `cad_verify_v4_freeze.verify` | PASS, exit 0. `sha256_file` `04c2b231…`, raw `5c25d496…`, 139 bindings |
| Frozen authorization | holdout; `charged_calls` 163 (global); `prior_counted_calls` 4, so at most **159 new**. Model `openai-codex/gpt-6.1-sol`, xhigh, OMP 18.11.2, executable `97f5c9d5…`. Bound to the cd4d lock and HEAD. Commitment `d87165ce…` |
| Quota limits (frozen) | consult 55, stop 60, maximum snapshot age 300 s |
| Claim before launch | absent. The old 83df claim and the prior-attempt records were left untouched |
| Sealed cohort | `45bb80a5…`, 37412 bytes, 60 entries. 91/91 files present: the 90 non-cohort files are all hash-bound in the cohort. Used in place, with no copy, reorder or edit |
| Quota at admission | snapshot `omp-usage-1792574459693-7d=15`, observed 09:20:59.693Z, **15%**, age 48 s at spawn |

## 2. RUNNING

- **Launch:** once, at 2026-10-21T09:21:47.86Z. The task-owned glue launcher (`86495e5f…`, PID 49184) runs detached in a hidden window. It refuses before spawn on a present claim, an identity mismatch, or a quota that is stale, invalid or ≥55; it adds no cap or bypass.
- **CLI:** PID 56328, running the exact frozen command: `python -B -m tools.eval_verify_v4 run --profile original --phase holdout --manifest <04c2 original-rerun-freeze> --sealed-input <unchanged cohort> --run-dir <new private run-1>`, with cwd at the repo.
- **Process conditions:**
  - stdin: DEVNULL;
  - parent stdout and stderr: fully captured to private files;
  - `OMP_PROFILE=cad-harness`, `PI_CONFIG_DIR` absent;
  - no timeout, retry, restart or job breakaway;
  - no change to permissions, sandbox, ACLs or global settings.
- **New one-time claim:** `manifest.claim.json` `2c9c76d1…`, created by the CLI itself.
- **Budget:** prior 4 + new at most 159 = cumulative at most 163. New paid calls by v4claude: 0.

Terminal facts will be appended as section 3.

## 3. TERMINAL: STOP / INCOMPLETE

The CLI ran once and was not relaunched. The background waiter (task `b1ip14i1v`) was passive: it only waited for the exit record and logged quota privately, with no cap or watchdog.

- **Exit:** CLI PID 56328 exited with **code 1** at 2026-10-21T09:27:55.29Z, after starting at 09:21:47.87Z. Parent stderr is 0 bytes. Parent stdout is 117397 bytes, `71ca2452…`.
- **Status:** `INCOMPLETE`, `fresh_holdout` incomplete, `valid_suite` true, `complete` false, `bar_met` false. **stop_reason `attempt_gold_binding`**.
  - This is a harness stop, not a measured result. Per the release terms, I did not review source, private cases or generated output, made no fix and did not restart.
  - The partial per-gate threshold flags are not interpretable as v4 results, because the run is incomplete.
- **Episodes:** 18 started and 18 finished; **42 not started** of 60.
- **Ledger events:**
  - run_started 1, run_finished 1;
  - episode_started 18, episode_finished 18;
  - quota_checked 103;
  - attempt_started 31, attempt_finished 31.
- **New counted calls:** 16 (12 retained segments + 4 archived work), with 16 physical model attempts and 16 conservative reserved calls. Unfinished attempts: 0.
  - **Cumulative: prior 4 + new 16 = 20 ≤ 163.** The new maximum of 159 was not reached.
  - CAD attempts: 15. Without an invoice, counted and reserved calls are not asserted as provider-billed charges.
- **Overload (rule 6):** 0 exempt overload attempts, and wait_s had no observations, so overload robustness is **UNVERIFIED**.
- **Time:** operational wall = active = 366.86 s. The deterministic-work counter is 0.
- **Usage (known for 16 of 16 calls):**
  - input 52578;
  - cached input 10368;
  - cache-write 0;
  - output 8952.

  Reasoning output tokens are **missing** for 16 of 16. Price is unknown (0 of 16 known), currency is null, and `full_cost_known` is false.
- **Capture:** 62/62 complete, 0 missing or partial.
- **Private identities:**
  - run `ledger.jsonl` `428c2ab7…`;
  - `summary.json` `19d2a46c…`;
  - `calls.csv` `9faff7d5…`;
  - run `manifest.json` `f60930c5…`;
  - run `cohort.json` `45bb80a5…` (unchanged);
  - launch record `3249cb84…`;
  - exit record `4046e088…`.

  The claim `2c9c76d1…` exists and is now consumed. The old 83df claim and the prior-4 records are unchanged and separate.
- **Cleanup:** launcher 49184 and CLI 56328 have exited, and no FreeCAD process remains. Nothing was left running untracked.
- **Quota after:** 15%, snapshot `omp-usage-1792574891864-7d=15`, observed 09:28:11.864Z. It stayed at 15% throughout, so the 55% and 60% thresholds were not reached.

**STOP. ASK: the harness stopped on `attempt_gold_binding` after 18 of 60 episodes.** This looks like a harness-level stop that needs Sol's diagnosis. I have not diagnosed or fixed anything, and I will not restart or retake. Any continuation needs a USER decision on accounting for the 20 cumulative calls and a new, separately authorized chain. I made no commit, push, lock or source edit.

## 4. Provenance: full SHA-256

These are mechanical `sha256sum` hashes taken at 2026-10-21T09:31:46Z. No contents were exposed, and none of the requested hashes is missing.

| Private record (rerun) | SHA-256 |
|---|---|
| `run-1/ledger.jsonl` | `428c2ab7075c075f0e6dc866a2f1ba004999238cae1882cd5fbe71d3119ad398` |
| `run-1/summary.json` | `19d2a46c1d809f08346cb36b662274a6af5d96b7d74cc8cc165e060ea9750409` |
| `run-1/calls.csv` | `9faff7d549469be52b06bfca64647f73dd8d565052cc36cc268d2ddd7b95a252` |
| `run-1/manifest.json` | `f60930c56fc43e82357feef2e814d976111ea8a8ba2811f7b8f8e1c6058da42d` |
| `run-1/cohort.json` | `45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65` |
| `parent.stdout.bin` | `71ca24529bed1c361a4bc950534d707bf114813a4bb64b30522fb497e1a66b74` |
| `parent.stderr.bin` (0 bytes) | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `launch.json` | `3249cb84e591625e537e77ae2d7fa9cea0f3cd8cb7f7595027c68e8508948396` |
| `exit.json` | `4046e0888639b2b8dbd411ba514ea2741352c9e0f3f38cceea48048e233522d4` |
| New claim (04c2 freeze, consumed) | `2c9c76d1a41c7f7c8185a5c38d41e9a042041cc05a0282ec2a05df2d5a520280` |

### Prior records are unchanged

All rehashed records match the identities recorded at the prior stop (`impl-review-launchers-v4claude.md` §10.1). The prior ledger and summary still carry their 2026-10-20T12:32:21Z mtime.

| Prior attempt record | SHA-256 |
|---|---|
| prior `run-1/ledger.jsonl` | `5867a5b796506497ba17990347f5eb3fc5d3c5d864b5db5c7842c97e4deff812` |
| prior `run-1/summary.json` | `fb0f4b4622ed4a19e126c4a9be5a1bcb4b0fbbab9b6b8a5290042513373d5915` |
| prior `run-1/calls.csv` | `04c414932a2d4e733d1b3e4169ffcc155d470734a7d33d794aaf6759298ed9f1` |
| prior `exit.json` | `5f6f0725f125ab4db4d3876a83702318ba17e908c696a407c19fb2c65b7ac7bd` |
| old claim (83df freeze, consumed) | `31f57869286512f50cb8384c0e9aa7ebe0ce737737c2ed747bff9dc0bba5648e` |

### Processes and calls after the stop

- **Processes:** at 09:31:46Z there was no launcher 49184, no CLI 56328, and no FreeCAD or FreeCADCmd process. Every process I owned had exited.
- **Calls after the stop:** none. The rerun ledger's last write was at 09:27:55Z, the CLI exit time, The summary counts 31 attempts started and 31 finished, made up of 16 model attempts and 15 CAD attempts, with 0 unfinished. v4claude has made no generation call.
- **State:** v4claude is now idle.
