# Original60 remaining-42 continuation: v4claude custody receipt (2026-10-21)

v4claude is the custodian only; the generator is Sol. This receipt is public and holds aggregates only. Raw captures, the ledger, model streams and per-case outcomes stay private under `C:\dev\v4claude-continuation42-custody\`. The cohort is the **same** original60, reused under explicit USER authority; it is not newly fresh. I read only `original-continuation-summary-sol-20261021.md` and custody metadata. I did no source, diff or private-content review and had no contact with Gemini or Grok. The USER confirmed the launch in-session.

## 1. Admission: mechanical checks, all passed before the claim

| Check | Result |
|---|---|
| HEAD / tree / `origin/herdr/v4` | `9eaa96504a2d849c0b0ed43ddd431c4a9b31f5de` / `8137c6b37dce00729b93844b783eb8edfed3f3f7` / equal to HEAD |
| Implementation lock `verify-integrated-lock` | exit 0 (13:04:06–13:05:39Z). `sha256_file` `c12bb18ee7bc8594ac5022f757e3fcd0895e61e91f6aaf95ddd94eafde3989d9`, raw `791a0513a914a6a09047d8d99a315df927799aa932e9453feb4b15a03b651efa`. Status offline_locked, authorization null, `final_v4_ready` false, live 0, 5 recipes. 411 source records with canonical digest `d5887722dc1f24c54bea059a001378cc9fb310beff826128aff96386b0007583`, an exact match |
| Continuation freeze `cad_verify_v4_freeze.verify` | PASS, exit 0. `sha256_file` `770e1523b881a684f5ed72a08de90a5b5da03eb5523b1a70fafcbdba7358fca7`, raw `d5e262d83fbe5773befe082e84340c4e8964962046515a7d3ea245a7a584c34d`, 139 bindings. The authorization file is `55ad6b221fc1dc7084c2ad97bf4fad396e5fe13641a39c2ecc2f73b9f484e2f6` |
| Frozen authorization | holdout; `charged_calls` 163 (global); `prior_counted_calls` **20**, so at most **143 new**. Bound to the c12b lock, HEAD and d588 source. Model `openai-codex/gpt-6.1-sol`, xhigh, OMP 18.11.2, `97f5c9d5…`. Commitment `d87165ce…`. Stops: 55% STOP_AND_ASK, 60% STOP, code issue STOP_WITHOUT_FIX_AND_ASK, rule 6 unchanged |
| Bound continuation | prefix `8cbdea563796b5244c96bee584f79719b627c051e7b7079ef8ca4a92e9794dcd` (18 rows; the on-disk SHA matches). Prior manifest `f60930c5…`, summary `19d2a46c…`, ledger `428c2ab7…`, cohort `45bb80a5…` |
| Recovery receipt binding | `e9cd33fc9ad1172f1c3d2dcf9f8340d23feb6efef22622a0d7db6a8162856cd8`, equal to the file on disk at admission. Prefix17 `bd41f0a1…` and evidence map `37e7acff…` |
| Prior attempts recorded | 4 (INCOMPLETE, legacy_runtime) + 16 (INCOMPLETE, attempt_gold_binding). Both claims are consumed and immutable, with no quality pooling |
| Claim before launch | absent |
| Sealed cohort | `45bb80a5…`, the same in-place path, 60 entries |
| Quota at admission | snapshot `omp-usage-1792588001526-7d=17`, observed 13:06:41.526Z, **17%**, age 5.7 s at spawn |

## 2. READY / RUNNING (one actual invocation)

- **Launch:** once, at 2026-10-21T13:06:47.27Z. The glue launcher (`cd806e9f42714ce54e39671c0c6b67839d87867797ed8b49f6acaeae1a476a44`, PID 25028) runs hidden and detached. It refuses before spawn on a present claim, an identity mismatch, or a quota that is stale, invalid or ≥55.
- **CLI:** PID **70796**, running the exact frozen command: `-B -m tools.eval_verify_v4 run --profile original --phase holdout --manifest <770e continuation freeze> --sealed-input <same cohort> --run-dir C:/dev/v4claude-continuation42-custody/run-1`.
- **Process conditions:**
  - stdin: DEVNULL;
  - parent stdout and stderr: fully captured to private files;
  - `OMP_PROFILE=cad-harness`, `PI_CONFIG_DIR` absent;
  - no timeout, retry, restart or job breakaway;
  - no permission, ACL or settings change.
- **New one-time claim (created by the CLI):** `manifest.claim.json` `090189e3429d459110cdb71c7365f335b3392e703b96ce5ceef7303ddc0c5261`.
- **Prefix admission:** observed. The run directory has a `continuation` record, and the first episode directory created is **episode-019**. Only 19–60 are being run.
- **Status:** the root launcher was alive at 13:07Z. I'm attached through a passive terminal wait.

Terminal facts will be appended as section 3.

## 3. TERMINAL: STOP / INCOMPLETE

The CLI ran once and was not relaunched. The passive waiter (task `b7jgqe2iz`) only waited for the exit record and logged quota privately.

- **Exit:** CLI PID 70796 exited with **code 1** at 2026-10-21T13:59:27.66Z, after starting at 13:06:47.27Z. Parent stderr is 0 bytes. Parent stdout is 151218 bytes, `e48aeff52539a722da3566508a72f9d898068880a61a94be67b898c4c14eda65`.
- **Status:** `INCOMPLETE`, `fresh_holdout` incomplete, `valid_suite` true, `complete` false, `bar_met` false. **stop_reason `transport_or_capture_interrupted`**.
  - I did not diagnose it, review source or outputs, fix anything or retry.
  - Because the 60-episode aggregation did not complete, I am withholding the pass count and per-case outcomes, including episode 18's. The partial threshold flags are not v4 results.
- **Episodes in this segment:** 41 started and 41 finished (directories episode-019 to episode-059). **Episode 60 was not started.**
  - The prefix of 18 rows was retained as frozen and not re-run.
  - Total coverage is 18 + 41 = 59 of 60.
- **Ledger events:**
  - run_started 1, run_finished 1;
  - episode_started 41, episode_finished 41;
  - quota_checked 365;
  - attempt_started 106, attempt_finished 106.
- **Calls in this segment only (`cost_scope` current_segment_only):** 68 new counted calls (56 retained + 12 archived). That is also 68 physical model attempts and 68 conservative reserved calls. Unfinished attempts: 0. CAD attempts: 38.
  - **Cumulative: prior 20 + new 68 = 88 ≤ 163.** The new maximum of 143 was not reached.
  - The old 16 + 4 records stay separate references; there is no ledger pooling.
  - Counted and reserved calls are not asserted as provider-billed charges, since no invoice exists.
- **Overload (rule 6):** 0 exempt overload attempts, and wait_s had no observations, so overload robustness is **UNVERIFIED**.
- **Time:** operational wall = active = 3159.48 s.
- **Usage, known subtotal:** 67 of 68 calls are known, and **1 call's usage is missing** (missing_contributions):
  - input 221919;
  - cached input 62208;
  - cache-write 0;
  - output 87921.

  Reasoning tokens are missing for 68 of 68. Price is unknown (0 of 68 known), and `full_cost_known` is false. No totals are fabricated.
- **Capture:** **210 of 212 complete; 2 missing or partial.**
- **Private identities (full SHA-256):**
  - run `ledger.jsonl` `0d6fa929d82f8c124cb637210de6d66a9c867638fc756e0590322569554a555e`, last write 13:59:27Z, which is the exit time;
  - `summary.json` `e879d95a2d1d681424926de6179d7c1c5b94ee6a14f794a75fa85bbd74325617`;
  - `calls.csv` `ad3e48a1a91bf60214c8cbca4dad223125083b03c8506203dd949cb68ccabaab`;
  - run `manifest.json` `afdb3ccae838b2a957adc8cb097d48792d38e8bb81f9687f7a2f3e1afce8c674`;
  - run `cohort.json` `45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65`;
  - `launch.json` `54ff091e19108131f4166579d51dee37a22e3c42cd483cf4e1233505de7cead8`;
  - `exit.json` `6c0d899f0522b8aaee70f25b009fe54ca7f192e6e9c1c9c0d0359a456de1a6e6`.

  The new claim `090189e3429d459110cdb71c7365f335b3392e703b96ce5ceef7303ddc0c5261` is now consumed.
- **Originals unchanged:**
  - prefix `8cbdea56…`, so prefix17 `bd41f0a1…` is unchanged with it;
  - old rerun summary `19d2a46c…`, ledger `428c2ab7…`, manifest `f60930c5…` and calls `9faff7d5…`;
  - sealed cohort `45bb80a5…`.
- **Cleanup:** launcher 25028 and CLI 70796 have exited, and no FreeCAD process remains. No omp process started after the launch; all 31 existing omp processes predate it and were not touched. With 0 unfinished attempts and the last ledger write at exit time, no calls were made after the stop.
- **Quota:** 26 passive observations from 13:07 to 13:57Z, all **17%**, and 17% after the stop (snapshot `omp-usage-1792591210642-7d=17`, 14:00:10.642Z). The 55% and 60% thresholds were not reached.

**STOP. ASK: `transport_or_capture_interrupted` after 41 of 42 remaining episodes. Episode 60 was not started, 2 captures are missing or partial, and 1 call's usage is missing.** This needs a USER decision and Sol's sanitized diagnosis. I made no fix, retry, recall, commit or push, and v4claude is idle.
