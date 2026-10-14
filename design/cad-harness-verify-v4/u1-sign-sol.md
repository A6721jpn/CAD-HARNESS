# U1 + addendum A review — sol

BLOCK

Reviewed PLAN-V4-CONSENSUS.md, DECISIONS.md and PLAN-V4-UPDATE-U1.md including addendum A. Agent: sol (openai-codex/gpt-6.1-sol). No private holdout material was opened; no execution or live calls were performed.

## Exact findings

1. **Zero eligible tasks has no defined non-success verdict.** U1 §1 and addendum A's Ordering rule apply `ceil(0.7*N)` when fewer than ten survive, without excluding N=0. Screening the supplied candidates under E1–E5 leaves N=0 (see pilot-select-sol.md). A threshold of zero must not become a vacuous pilot PASS. Specify that N=0 means `not_run`, with no success fraction or PASS; do not invent, rewrite or substitute tasks. This preserves consensus §§3 and 5.

2. **Holdout control validation is not explicitly required before generation starts.** U1 §4 says the control reviewer validates released items only after run inputs are hashed, but does not establish that independent request/gold/native-control validation finishes before final execution freeze and before the first generation call. Hashing establishes identity, not validity. Consensus §4 requires that validation and retirement of defective/exposed material before the final freeze. Explicitly sequence implementation/skill lock → independent authoring and control validation → final commitments/freeze → generation, retaining the user-decided option B and recording its procedural-isolation limitation. No inspection or repair of scored items during execution is acceptable.

3. **The source description is inconsistent with the committed file.** Addendum A's Source bullet says 25 requests from 23 conversations; pilot-candidates.md's header says 25 requests from 13 primary conversations. The file's observed SHA-256 is `63a39ed365324893df7615a83c17db5e217c1701d447594187a2360391910839`, exactly matching addendum A. Correct the conversation count in the addendum; do not alter or rewrite the candidate source.

## Decisions retained

DECISIONS.md's confirmed Astra judge identity supersedes U1's stale “to be confirmed”; the user's final judgment remains authoritative. The 203-call ceiling, separate 163/40 reservations, unchanged active-work limits, full wall-time recording and uncapped mandatory overload policy remain unchanged. Prices remain null without a source. A proposed token baseline is not a measured comparison: matching and aggregation must be committed before reporting reductions, and missing values must remain null.

This is a review finding, not approval to execute or alter the plan. Only the two requested review artifacts are written.

R2: BLOCK R2-1 through R2-3 resolve my original findings. R2-4 still leaves a zero baseline token sum undefined: its formula divides by Σv3, but its null rules cover only missing route classes and null contributions, not a known Σv3=0. This can occur for an individual token type even when both route classes contain calls. Specify that a zero baseline sum yields a null reduction with a zero-baseline reason, including when Σv4 is also zero; never divide by zero or report a fabricated percentage. No private holdout material was opened.

R3: AGREE
