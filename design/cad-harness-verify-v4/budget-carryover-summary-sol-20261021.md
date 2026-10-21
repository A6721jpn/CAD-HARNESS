# Sol summary — budget-only carryover; no source/diff review

For v4claude/Opus: read ONLY this Sol-written summary. Do not inspect source, diffs, other evidence, old notes, private inputs, terminals or model outputs. Do not run commands, CAD, models, tests, Git or delegation for this review. Write only `design/cad-harness-verify-v4/budget-carryover-sign-v4claude-20261021.md`: AGREE or BLOCK, clearly summary-based/procedural, not an independent code audit. State concrete blockers if this summary is internally inconsistent. Do not launch production.

## USER authority and invariant scope

- USER10/21 15:13 authorizes a new full run of the SAME original60, not new tasks, with a fresh authorization/claim. Prior4 counted calls remain inside cumulative163; at most159 NEW counted calls are available. Old INCOMPLETE attempt and its consumed claim remain separate immutable history, never pooled for favorable scores.
- Read-only preflight of908589c5 showed its per-run0/163 guard could not carry the prior4. It rejected159 as an authorization limit and ignored extra carryover fields. No production restart, authorization or claim was issued.
- USER answered the ASK by approving ONLY minimal cumulative-budget repair, tests, a NEW verified implementation lock, then this same60 run. No workaround. If scope expands beyond counting, or production needs any code fix, STOP without fixing and ASK.
- Policy numbers, acceptance gates, cards, scoring and cohort bytes/order stay unchanged.55% means stop and ASK,60% means stop. Existing overload rule6 remains600-second wait, identical resend, exempt from call/time caps with full-wall accounting. No borrowing from other pools.
- Opus receives ONLY Sol summaries, never code/diffs. NO Gemini/Grok. All private-data, CAE/Fusion/SolidWorks/main-working-tree/shared-ACL/permission/director prohibitions remain.

## Bounded implementation facts reported by Sol

- Only TWO production files changed: authorization validation in `tools/cad_verify_v4_freeze.py`; guard initialization in `tools/cad_verify_v4_live.py`.
- A frozen authorization now REQUIRES `prior_counted_calls`, an integer in0..163. Omission, booleans, fractional values, negative values and values above163 are refused. No implicit fresh0 default in production.
- The global authorized ceiling stays163. The cumulative admission counter starts at the frozen prior value. The real new authorization will bind prior4, so only159 further counted admissions can occur, across all episodes. Episode caps, quota checks, overload handling, refunds, scoring, transport and run logic were not changed.
- Existing valid unit authorizations explicitly supply0. The new real authorization must supply4 and bind the prior attempt's evidence. It must not set charged_calls159: that field remains the global163 ceiling. No fake quota, dummy production charges, monkeypatch, wrapper cap or permissive fallback.
- Per-run ledger costs remain actual NEW activity only. Terminal public accounting will report NEW counted calls and prior4+NEW cumulative calls separately; provider-invoiced billing remains unknown without an invoice.

## Actual observed proof — no paid CAD-model generation

- Baseline before edits: UTC2026-10-21T08:40:39.751633Z,411 bound source records from908589c5.
- Full host regression:646 tests =466PASS +180SKIP;0FAIL/ERROR. Actual199.766s, finished2026-10-21T08:47:45.756428Z. Blocked/attempted real provider launches0.
- New permanent boundary tests: after prior4,159 new admissions across episode boundaries reach cumulative163 and the next is refused; a fully spent prior budget admits no new call; invalid/missing prior fields are rejected; an exempt overload preserves prior4 and charges only the eventual success. Freeze validation also rejects invalid carryovers.
- Actual production-guard DEV smoke, outside unittest, used the real fresh quota snapshot:159 simulated admission reservations reached163; the160th was refused. This was an UNFROZEN DEV counter instance, not a production authorization/claim, and performed0 actual model calls. Its reservations are NOT production charges.
- Actual pinned-FreeCAD independent DEV isolated offline episode:1PASS,3.802s test time/4.375s process wall, no missing checker dependency. This DID execute native CAD checking; it was NOT a paid generation call.
- SHA comparison:406/411 source records byte-identical; changed records are exactly the two production files, two existing test files and DECISIONS approval recording. The entire production AST outside ONLY guard constructor/authorization validator is identical. Thus call/episode caps, quota, overload/refund behavior, policy, gates, scoring and all other bound files are unchanged.
- Public original commitment SHA remains `d87165cebd273de13fc1e7796cb2bc58fffb4e88a6d1f71665194d8866493a7f`; cohort SHA remains attested `45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65`. Parent did NOT read private cards/cohort/gold/raw outputs and does NOT claim to have inspected the external private tree.
- Review source snapshot:411 records, canonical SHA `e50ae1820ee6277cbf4c857ec4b56e86b4065cf6a892cbbc31ab230ea03f901b`.
- Actual refresh of all10 independent DEV native artifact checks is IN PROGRESS, not yet claimed PASS. C5 bare is the existing DEV restoration-extension fixture, never live-bare authority. These fixtures are independent of original/pilot/private inputs.

## Prior history and release gates still closed

- First attempt:4 counted/physical/reserved model calls,1 CAD attempt, INCOMPLETE/harness:legacy_runtime. Its ledger SHA `5867a5b796506497ba17990347f5eb3fc5d3c5d864b5db5c7842c97e4deff812`, summary SHA `fb0f4b4622ed4a19e126c4a9be5a1bcb4b0fbbab9b6b8a5290042513373d5915`; retain unchanged. Its4 calls are the new frozen prior value, not refunded or erased.
- Existing published7ead85c and908 seal remain immutable history; they are NOT authorization for running modified source.
- Before ANY new production call: all10 actual DEV checks must pass; finish bounded commit/push toherdr/v4 excluding caches/private/unrelated changes; create NEW five-recipe integrated implementation lock; authoritative verification must pass and its411 source map must EXACTLY match the review snapshot; then create/verify NEW frozen original authorization with prior4, fresh profile/quota admission and unchanged60 custody, then a new exclusive claim.
- Current additional paid CAD-model calls0, new production authorization0, new claim0. Generator for eventual production remains Sol `openai-codex/gpt-6.1-sol`, thinkingxhigh, throughomp with closed stdin. Opus is reviewer/custodian only, never the CAD generator.
- No automatic restart/retake after a terminal stop.55ASK/60stop remain binding; a non-budget or during-run code issue requires ASK without fixing. Results commit/push occurs only after terminal accounting, then finalPROGRESS and idle.
