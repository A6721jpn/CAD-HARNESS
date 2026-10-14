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
