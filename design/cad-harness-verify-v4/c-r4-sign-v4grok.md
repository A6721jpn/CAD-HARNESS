# C-R4 — v4grok

Verdict: **SIGN**

Reviewed `PLAN-V4-ADDENDUM-C.md:115-117`. No other edit, no commit, no live call. No new user value.

## Lock loop

SIGN. `impl-notes-integrated-lock.md:94` and `impl-notes-integrated-lock-head.md:29` both state that a HEAD change invalidates the integrated lock even when source bytes are unchanged. Committing the lock note is such a change. `PLAN-V4-ADDENDUM-C.md:116` stops the loop: lock notes and the holdout public commitment are committed together after authoring, the integrated lock is re-issued against that commit at the final freeze, and only that final lock is operative. A later HEAD change still requires a new lock before any live call. Authoring is not a live call.

The cited interim lock is real evidence, not the operative trial lock. Current `HEAD` is `6f832af0474e148c42975f4e48df0a7263b0332b`. The manifest file `reports/verify-v4-integrated-relock-20261014T153013Z/integrated-lock-head/manifest.json` has SHA-256 `6a92bbbccb2f8861b401e3dfb488dd9c70074c9dfb4477a7e34b511abf113542`, which is the abbreviation in `PLAN-V4-ADDENDUM-C.md:116` and the identity in `impl-notes-integrated-lock-head.md:7-10`. Authorization on that lock remains null (`impl-notes-integrated-lock-head.md:13`).

## Q2 models

SIGN. `PLAN-V4-ADDENDUM-C.md:117` matches the recorded roles. `DECISIONS.md:24-25` keeps the holdout generator at `openai-codex/gpt-6.1-sol` / `xhigh` and limits `openai-codex/gpt-6-astra` / `max` to the pilot generator. `c-de-amend-sign-sol.md:15` and `envelope-sign-v4grok.md:16` use that same Sol identity for both benchmark arms. Astra Max remains the judge (`DECISIONS.md:15-16`).

No live calls, CAD, private holdout access, or commit.
