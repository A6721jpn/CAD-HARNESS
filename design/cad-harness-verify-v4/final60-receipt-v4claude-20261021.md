# final60 custody receipt — Opus custody operator

Written under the Sol USER-authorized release `final60-launch-summary-sol-20261021.md`. Only whitelisted aggregates, hashes, times and statuses appear here: no task IDs, labels, requests, gold, generated text or geometry, and no per-case outcomes beyond the 59 failure the USER already approved. The full private captures stay in `C:/dev/v4claude-final60-custody/`. Nothing was committed or pushed.

## Pre-launch authentication (mechanical, no source read)

- Repo HEAD = origin/herdr/v4 = `1a39eaaa02f3aca6cf9ae5f7c57f494549982d4c`.
- The `--sealed-input` locator was taken by program from the old `C:/dev/v4claude-continuation42-custody/launch.json` argv: 1 occurrence, 1 unique value, absolute path, file exists. The sealed-input SHA256 equals the cohort SHA `45bb80a5…3258c65`. Its contents were not displayed. The OMP_PROFILE env value was copied from the same metadata by program and not displayed. PI_CONFIG_DIR was absent.
- Raw hashes MATCH: freeze manifest `42baa6ab…bcc3`, authorization `aff7a891…a115`, lock manifest `d1c86952…1b24`, prefix59 `944c566a…94ee`, omp.exe `97f5c9d5…4946`, and prior manifest/summary/ledger/calls (`afdb3cca…`, `e879d95a…`, `0d6fa929…`, `ad3e48a1…`).
- Seals MATCH (`sha256_file`): freeze `d77a5190…455a`, lock `d879a730…13b2`.
- Recover59, host, native and integrated checks were NOT rerun.

## Early actual readiness (observed, not inferred)

Disclosure: the readiness facts below were observed on disk at 15:54:45Z, while both PIDs were still alive. The CLI then exited at 15:55:14Z, before this receipt file was written, so the early and terminal sections were written together in one file.

- Invocation count: **1**. Own launcher SHA `03bf18fe…c0a7`. Glue only: stdin DEVNULL, CREATE_NO_WINDOW|CREATE_NEW_PROCESS_GROUP, no job breakaway, no timeout, retries 0.
- Fresh quota at admission: 19% (observed 15:53:19.777Z, age 49.07s, read 15:54:08.851Z), below 55.
- Spawn window 15:54:08.852423Z – 15:54:08.858612Z. Launcher PID 28792, CLI PID 66476. Both were alive at 15:54:45Z.
- New claim (created only by the frozen CLI): `original-final60-freeze/manifest.claim.json`, 336 B, SHA256 `8856f224d91d4a37a47b6c865be0ba180670ddcb4aeb865e50a055b02bfc3251`, created 15:54:39.948Z.
- Prefix59 admitted. `run-1/continuation/` holds prefix `944c566a…`, driver `255f78ab…`, evidence `4d27a133…`, and prior-cohort/ledger/manifest/summary with the hashes listed above.
- First and only episode directory: `episode-060`, created 15:54:41.057Z. No episode 001–059 directory was created.

## Terminal facts

- CLI exit **0**, observed at 15:55:14.275Z. status `COMPLETE`, stop_reason `null`, fresh_holdout `complete`, evidence_mode `live`, pilot `not_run`.
- Rows: 60 ordered and unique (sequence 1..60, 60 unique). passed TRUE **57**, passed FALSE **3**. No partial claim.
- Rows 1–59: byte-equal (canonical JSON) to the frozen prefix, 59/59, with 0 differing fields. Row 59 is still `passed=false` and `completed=true`. Rows 1–58: 56 pass, unchanged. Only sequence 60 was executed (1 episode_started and 1 episode_finished event).
- Core 51 (scored): **48/51**. Unscored preview 3: **3/3**. Completion 6: **6/6**.
- valid_suite TRUE, complete TRUE, core_complete TRUE, deadline_ok TRUE, versions_consistent TRUE, bar_met **TRUE**. Thresholds are all TRUE: source, complex, stock, defaults, ambiguity, faults, mvp, legacy. These come from the unchanged scorer. No criterion was changed, no row was forced, and nothing was retaken.
- Generator: openai-codex/gpt-6.1-sol / xhigh, omp/18.11.2, SHA `97f5c9d5…4946`.

## Budget (new segment only; cost_scope = current_segment_only)

- physical_model_attempts 2, conservative_reserved_calls 2, new_counted_calls 2, retained charged calls 2/2 known, archived 0, unfinished_attempts 0, cad_attempts 2.
- prior 88 + new 2 = cumulative **90** ≤ 163, and new 2 ≤ 75. The old 4+16+68 costs are kept separate in prior raw ledgers and were not merged.
- full_cost_known FALSE. Price is null (2 of 2 contributions missing). Currency is null. Invoice charges are unknown, and no grand total is made. The historical row 59 keeps its two false capture flags and one unknown usage, unrepaired. Reasoning tokens and prices stay null where missing.
- operational_wall_s = active_s = 34.281. wait_s is null (no_observations). exempt_overload_attempts 0. overload_robustness **UNVERIFIED** (rule6 was not exercised).
- Quota: 11 quota_checked events, min 19, max 19, last 19. 55 and 60 were not reached. A post-run read showed 20% at 15:56:24Z.

## Captures and hashes

- Parent stdout: 110317 B, SHA `0e66ddd184f5ca6916da0b709e840ed8eef108457bd5d99f4b9cd4b2168aac99`. Parent stderr: 0 B, SHA `e3b0c442…b855`.
- CLI capture accounting: expected 8, complete 8, missing or partial 0. The run-dir holds 18 stdout/stderr capture files, 268338 B total, and 213 files overall.
- run-1: summary `2049806ae35db2cb5374022e9828dca8715fc46d85740afdc9d442a2bfc3681e`, ledger `f474dd732dbfae825b7b1ab058742377e1b3fb0515e41c4429a8dab24ba29804` (23 lines), calls `c0e21f21f377eaa491036141f46ac7a11bdf35e7f6c4f9d411d529b46df96076`, manifest `13398ea18a78311e8e739dd2de8065ce42e2f4badc318f70926fb616326480b5`, cohort `45bb80a5…3258c65`.
- Custody: launch.json `bc0e6517163241ad9cca78ddc4b8cc8ab0755218463b259c0bde9a9aa954be82`, exit.json `88318735aa10ac85fd05a9669a8810fdff22c4175473b3c89f59337c10d201ef`.
- After the run, every prior and frozen record listed above still matches its pre-launch hash.

## Settlement

- The launcher (28792) and CLI (66476) both exited. A one-time read-only process snapshot (Win32_Process, names matching freecad or omp) was taken after the CLI exited at 15:55:14.275Z and before this receipt was created at 15:57:00.987Z. Its exact time was not recorded. It found **0 currently alive** matching processes created after 15:54:00Z, and 0 currently alive children of PIDs 28792 or 66476. This does NOT mean zero processes were ever launched: the run did make 2 model attempts and 2 CAD attempts (see Budget), and those processes had ended by the time of the snapshot. The 25 omp.exe processes alive in the snapshot were all created before launch, are unrelated, and were left alone.
- No new runtime, source, capture or auth issue was observed, so no ASK is raised. No retry, fix, or call after the stop. Operator is now IDLE. Sol publishes the terminal evidence.

## Clarification appended after Sol wording check

- The process line in Settlement now refers only to processes alive at the time of the snapshot. The settlement claim is only that no qualifying process from this run was still alive at that point. It is not a claim that none was ever launched.
- Evidence of "no retry / no calls after the stop" comes separately from the run ledger (`run-1/ledger.jsonl`, SHA `f474dd73…9804`, unchanged since the terminal receipt). It has 23 events in this order: run_started → episode_started → 4 attempt_started/attempt_finished pairs interleaved with 11 quota_checked → episode_finished → run_finished. run_finished is the last line, with 0 events after it. This agrees with physical_model_attempts 2 + cad_attempts 2 = 4 attempts, unfinished 0 and exempt_overload 0. The launcher made 1 invocation with retries=0.
- Nothing was rerun, relaunched or recomputed for this clarification. The only new reads were the ledger's event order and this receipt file's creation time.
