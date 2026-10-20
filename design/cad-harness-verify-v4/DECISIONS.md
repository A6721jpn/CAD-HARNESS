# v4 decisions (2026-10-14 10:39 JST)

These two were decided by the supervising agent under the user's standing policy, and relayed to this run. They were not given directly by the user.

- **#5 Call budget: option A.** At most 203 charged accepted calls in total: 163 for the holdout and 40 for the pilot. There is no automatic borrowing or extension.
- **#6 Overload clock: option A.** Verified server_overloaded backoff and resend cycles are excluded from the stage and episode active budgets.
  - The numeric work limits are unchanged.
  - All elapsed wall time is recorded.
  - This follows the standing user rule of 2026-10-13 16:39 JST: wait 600 s and resend, uncapped, never scored.

Pending with the user: #1 pilot tasks, #2 pilot judge and rubric, #3 price source, #4 holdout author and custodian. Phases 3 and 4 do not run until these are relayed.

## User decisions 2026-10-14 12:50 JST (relayed)
- **#1 Pilot tasks:** real past CAD request prompts extracted from the chat-history HTML DB.
  - Another bot writes them to `design/cad-harness-verify-v4/pilot-candidates.md`. Wait for that file. Never fabricate tasks.
- **#2 Judge:** "Astra Max" first, then the user double-checks visually. The criteria are fixed before the trial.
  - **USER-CONFIRMED (12:58 JST):** Codex GPT 6 Astra inside omp on herdr, i.e. `openai-codex/gpt-6-astra` with thinking `max`. Earlier interpretation: `openai-codex/gpt-6-astra` at reasoning effort `max`, run via omp. It is the model configured as the omp `vision`, `plan` and `advisor` role.
  - Probe at 12:5x JST: `omp -p --model openai-codex/gpt-6-astra:max` answered "PONG openai-codex/gpt-6-astra". omp did not report the effort level.
- **#3 Price:** none. Report only the % reduction of each token type versus the baseline.
  - The token types are input, cached input, cache write, output and reasoning.
  - A null on either side gives a null reduction.
- **#4 Holdout:** option B. One agent authors the holdout, hidden from the other two agents and from the implementer.

## USER 2026-10-14 14:07 JST - pilot generator (pilot only)
- For the pilot only, the generator (Codex role) is `openai-codex/gpt-6-astra` with thinking `max`, instead of `openai-codex/gpt-6.1-sol` (xhigh). The holdout is unchanged: gpt-6.1-sol, xhigh.
- Caveat: the judge (Astra Max) is the same model as the pilot generator. RESULTS must state this same-model judge/generator caveat. The user's visual verdict remains authoritative.
- USER 2026-10-14 13:52 / 14:05: the user supplies the pilot requests personally. 5 requests (U1-U5), verbatim in pilot-user-requests.md; N <= 5.

## USER 2026-10-14 14:28 JST - capability expansion (supersedes "no range expansion" for the items listed)
- Implement in v4:
  - (1) STEP import as a fixed user attachment, plus measured data passed to the generator;
  - (2) an image-to-vector contour CLI (binarize/trace/smooth/hash), a contour-extrude family with parametric thickness and size, and min tool R enforcement;
  - (3) text engraving (font);
  - (4) direct edit of an imported STEP: face selection, offset/replace/reconnect;
  - (5) freeform surface rebuild/merge with G1-G3 continuity;
  - (6) new judges: maximum surface deviation, curvature continuity G1-G3, face count, thickness distribution, unchanged-dimension comparison, solid validity, IoU/Hausdorff against the image, min R.
- Process: U1 addendum C plan, then 3-party consensus. Staged by difficulty: U5/U1/U2 first, then U4, then U3. Deterministic parts go in the CLI; judgment goes in the skill.
- Integrity:
  - Each new family needs its own fresh holdout.
  - Pilot tasks U1-U5 are user tasks. They are NEVER used for development, tuning or fixtures: no reading of their attachments by implementers, no gold derived from them.
  - Development uses independently created dev fixtures only.
  - The existing 163-call holdout (unchanged scope) and its custody are unaffected.

## USER 2026-10-14 14:40 JST - mandatory exit criterion
- The goal is unchanged. Passing ALL 5 user requests U1-U5 is now a mandatory v4 exit criterion.
- U1-U5 remain pass/fail material only. They are never used for tuning, development or fixtures. Separate fresh holdouts per new family are still required.
- S1 through S3 are all in v4 scope.
- The pilot runs after implementation and freeze. It is judged by Astra Max (gpt-6-astra max), then the user's visual check.

## USER 2026-10-14 14:57 JST - answers to C-Q (relayed)
- (a) U3 is judged with G2 continuity (instead of G3), together with the existing <=0.005 mm absolute deviation.
- (b) U5: the plate outline, the default thickness and the default logo size are delegated to the agents. sol and gemini set reasonable defaults, which are stated explicitly in addendum C (C-U5) before the freeze. They stay parametric.
- (c) U2: no maximum outer size.
- C-R1-2 (separate retry budget, INCOMPLETE on exhaustion) and C-R1-3/C-R2-2 (contour pre-extracted and hash-locked before the freeze) are adopted.

## USER 2026-10-14 17:28 JST - answers to C-Q4..Q10 and the U5 deliverable (relayed)
1. U5 deliverable: a part cut out in the logo shape (not a plate with an aperture). C-U5's plate outline therefore does not apply; the thickness (3 mm default) and logo height (50 mm default) stay as parametric defaults.
2. U1: play <= 0.5 mm PER SIDE; Y-vertical angle tolerance 3 degrees per side.
3. U2: same as U1 (play <= 0.5 mm per side, angle 3 degrees per side). The perimeter-band "no contact" criterion requires a minimum gap of 0.5 mm.
4. U4: tolerance ±0.1 mm on the 2 mm thickness and on the unchanged outer dimensions.
5. U5: the logo only needs to match roughly; model correctness matters more. The agents set lenient IoU/Hausdorff thresholds; the user checks visually.
6. Engraving size and depth: delegated to the agents.
7. The agents may approve the new-family holdouts (counts/gates) themselves. Extra call budget for them is approved with NO upper limit. The quota rule (consult at 55%, stop at 60%) still applies.
8. Time limits may be extended. CAD time must be measured precisely, and a durable dataset must compare work WITH vs WITHOUT the CAD harness (time saved). The baseline-without-harness measurement design must be agreed by the three.
Still open (not answered): the U1 tape location; the U2 "minimal concave-face contact" criterion (until answered: Astra plus the user's visual judgment, with no numeric gate invented).

## USER 2026-10-14 19:47 JST - U1 tape location
- The U1 double-sided tape location may be anywhere; it is delegated to the agents. The agents choose a sensible location. It is not a pass/fail criterion, except that the tape must fit within the 0.5 mm thickness allowance.

## USER 2026-10-14 21:09 JST - without-harness benchmark arm
- The no-harness comparison arm is run by Codex WITHOUT the harness: the same model and the same requests, with no cad_run, no CAD-harness skills and no harness CLI. It replaces the "named qualified human operators" assumption in C-D(e).

## USER 2026-10-14 22:02/22:03 JST - v4grok access path
- v4grok's backend is replaced: it now runs Grok Build natively (grok CLI 1.0.52, logged in with grok.com, model grok-4.7) in herdr w8 pane w8:p2, not via OpenCode Go and not wrapped in omp/Orca.
- The model is the same family and version (previously opencode-go/grok-4.7); only the access path changed. The role is unchanged: reviewer and the existing holdout author/custodian (option B).

## USER 2026-10-14 22:08 JST - Grok effort
- Grok always runs at High effort. v4grok stays on native Grok Build, model grok-4.7, effort high, on every restart (launch: grok -m grok-4.7 --cwd C:\dev\CAD-HARNESS-herdr in w8:p2; confirm the footer shows "Grok 4.7 (high)").

## USER 2026-10-16 19:51 JST - U5 separate pieces
- U5's separate logo pieces stay as separate parts (separate solids in one output). No bridges and no backing plate. This confirms C-R6.


## USER 2026-10-17 14:40 JST — registryRead-only resumption and conditional live authorization
- Supersedes the morning stop and the prior zero-capability choice **only** by permitting the bare LPAC token's Windows `registryRead` capability. No other capability, filesystem/network/GUI/process right, shared ACL or ownership expansion is approved.
- Resume reconciliation of Gemini's native failures, necessary fixes and offline verification; then v4grok final review/signature, combined commit/push on `herdr/v4` excluding `__pycache__`, and a NEW verified implementation lock.
- **After** that lock, the user authorizes the original **163-call** live budget. This is not borrowing or a replacement authorization for family/benchmark/pilot pools. Existing frozen-manifest/commitment/control-validation gates remain required. Consult at55% quota; stop at60%; no fabricated usage or results.
- Do not touch CAE, launch Fusion/SolidWorks, modify the main `C:/dev/CAD-HARNESS` working tree or contact the two development directors. Preserve the holdout/pilot custody boundaries and independent DEV-only implementation fixtures.
- If stopped or blocked, record the actual stopping point in `PROGRESS.txt` and wait. No live call is permitted before review, publication and re-lock are complete.

## USER 2026-10-18 00:06 JST — pinned bare-FreeCAD Win32k startup exception
- Supersedes the remaining Win32k blocker only: permit the isolation change necessary for starting the bare pinned FreeCAD host. Keep registryRead as the sole capability; no other filesystem, network, token, child-process, extension-point, job/UI, shared ACL or ownership relaxation.
- Implementation scope is the verified private copy of pinned FreeCAD Python only. Shell children retain Win32k disable. Windows mitigation is per process, not a per-function whitelist: the FreeCAD process retains Win32k access, while headless bootstrap and existing job/UI restrictions remain.
- Resume in order: actual bare verification, Gemini confirmation, v4grok final confirmation/signature, combined commit/push, NEW verified implementation lock, then the already authorized original163-call live run. Consult at55% usage and stop at60%; fresh quota/frozen authority gates remain.
- Preserve CAE/Fusion/SolidWorks/main-working-tree/director prohibitions and custody boundaries. Record the actual change/stopping point in PROGRESS.txt; wait if genuinely blocked. No live calls before the new lock.

## USER 2026-10-18 — quota reset and approved-scope resumption
- User supplied quota2% snapshot `omp-usage-1792286207260-7d=2` observed2026-10-18T01:16:47.260Z. Parent read a newer snapshot `omp-usage-1792286268602-7d=2` observed01:17:48.602Z, also2%; prior63% stop no longer bars resumption.
- Fix only bare temp_directory_path / temporary storage within existing scratch; registryRead and the minimal pinned-FreeCAD Win32k exception are the only approved relaxations. No other rights or shared ACL/ownership changes.
- Order unchanged: successful actual bare proof, Gemini confirmation, v4grok final signature, commit/push excluding __pycache__ plus NEW verified lock, then only the approved original163-call budget. Fresh quota55% consultation/60% hard stop remain, with no invented counts/results.
- Preserve CAE/Fusion/SolidWorks/main-working-tree/director and sealed/pilot custody prohibitions; record progress/stopping points and wait if genuinely blocked.

## USER 2026-10-20 JST — independent checker-card revision and reseal approved
- In the explicit choice following v4grok section9 B2, USER selected **「カード改訂・再封印を承認」**: independent personnel preregister and validate the missing C4/C5 checker criteria and acceptance values, then re-review under a NEW commitment. This supersedes the prior lack of authority to revise/reseal those incomplete cards only.
- Preserve every existing validity, native/export/reimport, operative-editability, dimensional, continuity and deviation gate. Do not synthesize acceptance values in the runner, silently augment sealed cards, or choose values after observing scored model outputs. The approved independent revision must identify its acceptance basis, register it before validation, retain old sealed evidence, and publish new hashes.
- Original60 cohort bytes, original163 reservation, family/benchmark/pilot budget separation, generator identities and55% consultation/60% stop remain unchanged. No additional Windows rights are authorized beyond registryRead and the pinned-FreeCAD-only Win32k exception.
- Sol never opens private cohorts or pilot attachments. Existing independent custody handles the private revision; source/code/skill/recipe/judge identities are frozen before authoring, and revised publication plus source undergo renewed signatures before combined commit/push and the final post-push lock (C-R4).
- The original163 conditional authorization is not a bypass: no live generation before required review, publication, NEW verified final lock and frozen original authority. Preserve all CAE/Fusion/SolidWorks/main-working-tree/director prohibitions.
- Approval observed with actual UTC clock2026-10-19T16:35:51.5400472Z. Actual quota snapshot `omp-usage-1792427671421-7d=14`, observed16:34:31.421Z,14%; this is evidence at resumption, not a prediction or future admission.

## USER 2026-10-20 JST — affected geometry and existing measurement-reference revision approved
- Following the retained-trace diagnosis (v4grok launcher review section14), USER selected **「独立担当による改訂・再封印を承認」** in the explicit additional-authority question.
- Retain the old candidates/evidence. The independent custodian may retire/re-author the11 affected C5 cases with fresh arrangements inside the unchanged c-s3 capability scope. This includes valid immutable reference STEP, request/gold/card bindings and native analytical controls; it does not relax the single-valid-positive-volume-solid source/handover gate.
- For the3 affected C4 benchmark cases, independently inspect and correct the existing opposed-face/landmark measurement references, preserving geometry and request if they are valid. Re-author a case only if its geometry is actually defective. A simple label error was not established by the earlier retained evidence.
- Freeze corrected data/acceptance before validation and publish a new commitment only after actual positive and decisive-violation controls. Do not use constructor/judge agreement alone as independent analytical-gold correctness proof; preserve the old proposals and failures.
- Counts, signed strata, all numerical/validity/continuity/deviation/editability/round-trip gates, strict C5 maximum0.005mm, original60 bytes/original163 reservation, pool separation, generator identities, source/skill/policy/recipes/judges and Windows rights stay unchanged. No model generation is authorized during authoring.
- Sequence stays independent controls/new commitment, renewed Gemini/v4grok signatures, combined commit/push excluding caches/private material, NEW verified post-push implementation lock, then only the conditionally authorized original163 maximum under fresh55%consult/60%stop.
- Actual approval-record UTC2026-10-20T00:08:12.672235Z. Read quota snapshot `omp-usage-1792454841803-7d=16`, observed00:07:21.803Z,16%; this is not future admission proof.

## USER 2026-10-20 15:13 JST — auxiliary precision redesign and v4claude appointment
- USER selected **「補助判定・評価データの再設計を承認」** (option1), not original-only-first or stop. An independent author may reregister the auxiliary native-roundtrip volume maximum or numerical-error budget with a measured/certified basis; the old donor literal/budget is not immutable for this bounded redesign. Values and method must be preregistered before validation, separately reviewed, and old proposals/failures retained. This supersedes the prior no-numeric-change restriction ONLY for that auxiliary precision decision.
- Problematic C4 candidates may be replaced by fresh cards/cases under the same conditions, capability scope, counts and signed strata, including uncertifiable/inconsistent/exposed candidates; replacement is no longer restricted to an actually defective solid. Preserve old/exposed candidates as history.
- Requested critical dimensions, absolute0.005mm deviation and G2 requirements remain unchanged, as do validity, operative editability, complete coverage, frozen source/skill/policy/recipe/judge algorithms, original60 bytes/original163 maximum, pool separation and55%consult/60%stop. No model generation during authoring; no new Windows permissions or rights expansion.
- USER appoints **v4claude**, new pane **w8:p9**, **Claude Code, Opus5.5 high effort**, to replace v4grok for the independent card/precision/C4 work and final-signature responsibility. USER explicitly withdraws the earlier10/12 Claude-exclusion decision.
- **v4grok w8:p8 stays stopped. Send it nothing.** Sol arranges the handoff; v4grok's private notes remain private and are not copied into sol's context. Author and reviewer roles must remain separate; self-review is not authorized. No silent model/effort substitution.
- The CAD generation identities do not change: original/family/benchmark generator remains openai-codex/gpt-6.1-sol xhigh; pilot generator and model judge remain Astra Max in their separately authorized pools. Claude is not the CAD-generation model.
- Sequence remains new preregistered data/precision, independent controls/reviews/signatures, combined reviewed commit/push excluding caches/private/reports per policy, NEW verified post-push implementation lock, then only the already authorized original163 maximum. Full-family data gates are not silently bypassed.
- User note time is15:13JST. Actual parent record UTC2026-10-20T06:16:18.974209Z; read quota snapshot `omp-usage-1792476926156-7d=18`, observed06:15:26.156Z,18%. Current p9 metadata confirms v4claude/Claude/idle/worktree, without reading any private terminal or notes.
