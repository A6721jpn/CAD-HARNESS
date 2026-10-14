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
