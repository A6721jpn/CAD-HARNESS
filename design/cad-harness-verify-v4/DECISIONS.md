# v4 decisions (2026-10-14 10:39 JST)

These two were decided by the supervising agent under the user's standing policy, and relayed to this run. They were not given directly by the user.

- **#5 Call budget: option A.** At most 203 charged accepted calls in total: 163 for the holdout and 40 for the pilot. There is no automatic borrowing or extension.
- **#6 Overload clock: option A.** Verified server_overloaded backoff and resend cycles are excluded from the stage and episode active budgets.
  - The numeric work limits are unchanged.
  - All elapsed wall time is recorded.
  - This follows the standing user rule of 2026-10-13 16:39 JST: wait 600 s and resend, uncapped, never scored.

Pending with the user: #1 pilot tasks, #2 pilot judge and rubric, #3 price source, #4 holdout author and custodian. Phases 3 and 4 do not run until these are relayed.
