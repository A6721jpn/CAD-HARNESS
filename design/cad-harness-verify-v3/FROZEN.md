# FROZEN — verify-v3-reviewed-r1 (2026-10-13 JST)

- Plan: PLAN-V3-CONSENSUS.md, signed by codex, grok and gemini (AGREE). Plan commit: fd7e215.
- Implementation commits: 4733341, f82c556, 7956b79, 86bf8a7, 32dab3a. Freeze implementation_commit: 32dab3a.
- Reviews:
  - grok-impl-review.md: READY.
  - gemini-impl-review.md: BLOCK on probe active(), fixed, then READY on re-review.
- Host pre-freeze checks: data-only smoke 18 cases / 60 episodes / 83–163 calls; test_verify_v3 OK; native controls host-verify-v3-native-controls-r1-mvp1 exit 0. No Sol calls.
- SHA256.json: 153 files, sha256 743e77764ff768a12234d63962ad2f8cdc7852e55ee1cbe814272a39139f7673. CODEX_HOME is the Orca account 43cffd0b.
- Fresh holdout: G1–G6, S3, A4–A6, C4, C5, F4–F6. Dev set: D1–D3. No v1 or v2 items are scored.
- Phase 3: python -B tools/eval_verify_v3.py run --prefix host-verify-v3-reviewed-r1 --quota-snapshot C:\dev\CAD-HARNESS\.tmp\verify-v2-supervisor-quota.json --call-budget 163

## Re-freeze: verify-v3-reviewed-r1-solfix (2026-10-13 JST)
- Why: the q-A5-r5 harness stop was caused by a provider-side `server_overloaded` rejection (see SOL-FAILURE.md). The frozen v3 had no resume path, and it misclassified provider rejections.
- Consensus: SOLFIX-CONSENSUS.md (codex, grok and gemini AGREE). Reviews: solfix-review-grok.md READY, solfix-review-gemini.md READY.
- User decisions recorded in SOLFIX-CONSENSUS.md:
  - 16:39: on overloaded, wait 600 s and resend, uncapped. Never an abnormal stop; never budgeted or scored.
  - 17:08: no deadline for the resumed segment. The quota 55%/60% stops are kept.
- Implementation commit: ef8c694. Plan commit: fd7e215 (unchanged).
- Original manifest archived (moved) byte-identical as SHA256.run-r1.json, sha256 743e77764ff768a12234d63962ad2f8cdc7852e55ee1cbe814272a39139f7673.
- New SHA256.json: 157 files, sha256 7d6f95ad58e73ae13fc6f6fa918500f3e41021579bd32c96855b29f56f5a20ac.
- Scope:
  - Scoring, gold, thresholds, order, Probe and controls are unchanged.
  - The 46 completed records stay byte-identical.
  - Resume runs A5-r5 (-resume1) and then sequences 48–60.
  - G5-r1 and G1-r2 stay scored as recorded, with a provider_rejected annotation.

## Re-freeze label: solfix-a1 (manifest version stays verify-v3-reviewed-r1-solfix) (2026-10-13 JST)
- Why: resume #2 crashed at completion-C4-r1 with OverflowError (math.floor(inf) at the no-deadline CAD timeout cap). See SOLFIX-ADDENDUM-A1.md.
- Consensus: SOLFIX-ADDENDUM-A1.md Revision 2. codex, grok and gemini all AGREE in solfix-a1-{codex,grok,gemini}.md. Implementation commit: f898d32. 24 tests OK.
- Manifests:
  - The previous solfix manifest is archived (git mv) byte-identical as SHA256.solfix.json, sha256 7d6f95ad58e73ae13fc6f6fa918500f3e41021579bd32c96855b29f56f5a20ac.
  - New SHA256.json: 157 files, sha256 f5b4aafc2ce203c465b0b85490c781345260049e11a05254c02c361c15cd1fcd.
- Archived run directories (renamed, nothing deleted):
  - From resume attempt #1 (quota snapshot stale, 0 Sol calls): suffix -aborted-quota-stale-20261013T1850.
  - From resume attempt #2 (inf overflow): suite, q-A5-r5, q-A6-r5 and completion-C4-r1 -resume1 dirs, suffix -aborted-inf-overflow-20261013T1856. Logs: .tmp/v3resume.{out,err}-aborted-inf-overflow-20261013T1856.log.
- Call charge: the 4 accepted calls from attempt #2 (A5-r5 1, A6-r5 1, C4-r1 2) are charged and unscored. Spent before re-execution: 58 of 163. Worst case: 106.
- Scope: segment 2 (entries[46:]: A5-r5, then sequences 48–60) is re-executed in full. Scoring, gold, thresholds and order are unchanged. The 46 segment-1 records are unchanged.

## Re-freeze label: solfix-a2 (manifest version stays verify-v3-reviewed-r1-solfix) (2026-10-13 JST)
- Why: resume attempt #3 stopped at fault-F4-r1 with harness:report_binding / fault_source_binding. The checker hashed the raw CRLF injection, but the driver re-extracts the source (the final CR is dropped). See SOLFIX-ADDENDUM-A2.md.
- Consensus: solfix-a2-{codex,grok,gemini}.md, all AGREE. Implementation commit: 27de198. 25 tests OK. Checker only; driver, fixtures, scoring, gold, thresholds and order are unchanged.
- Manifests: the previous manifest is archived (git mv) as SHA256.solfix-a1.json (f5b4aafc2ce203c465b0b85490c781345260049e11a05254c02c361c15cd1fcd). New SHA256.json sha256: f4d13350c3070020d0e655b238be8dc9abff92b352b12964110d37634647cd3c.
- Archived (renamed, nothing deleted): attempt #3 suite, A5-r5, A6-r5, C4/C5 r1–r3 and F4-r1 -resume1 dirs, plus logs, suffix -aborted-fault-binding-20261013T1930. Their results are informational and unscored.
- Call charge: attempt #3 spent 17 accepted calls, charged. Spent before re-execution: 54 + 4 + 17 = 75 of 163. Worst case: 123.
- Scope: segment 2 (entries[46:]) is re-executed in full.
