# U1 + addendum A — v4grok

BLOCK

Agent: v4grok (opencode-go/grok-4.7, herdr w8:p2). Reviewed PLAN-V4-CONSENSUS.md, DECISIONS.md, and PLAN-V4-UPDATE-U1.md including addendum A. Applied addendum A to the 25 candidates in pilot-candidates.md; result in pilot-select-v4grok.md. Did not open C:\dev\v4-holdout-private. No live calls and no execution.

## Exact findings

1. **N=0 is not a pass.** U1 §1 and addendum A set the pass line to ceil(0.7·N) whenever fewer than 10 candidates survive, and they do not exclude N=0. Screening under the fixed E1–E5 rules leaves N=0. ceil(0.7·0)=0, so an empty roster would be a vacuous PASS. Consensus §§3 and 5 require `not_run` when no eligible user tasks exist, not a success fraction. State that N=0 is `not_run`, with no PASS and no invented, rewritten, or substitute tasks.

2. **Control validation is not sequenced before generation.** U1 §4 releases plaintext only after freeze, and says v4gemini validates released items only after run inputs are hashed. Hash verification is identity, not validity. Consensus §4 requires implementation/skill lock, then independent validation of requests, analytic gold, and native controls, with retirement of defective or exposed material before the final freeze. Option B still holds: one author, hidden from the implementer and from the other agents until a commitment exists; isolation stays procedural and RESULTS must say so. The missing sequence is lock, then authoring, then a post-hash pre-freeze release to the control reviewer only, then retire-and-reauthor if invalid, then freeze, then generation. No inspection or repair of scored items after launch.

3. **Addendum A miscounts the hashed source.** Addendum A says 25 requests from 23 conversations. The hashed file's header says 25 items and 13 primary conversations. That file has 25 conversation-ID mentions and 13 distinct IDs. SHA-256 of the file is 63a39ed365324893df7615a83c17db5e217c1701d447594187a2360391910839, matching addendum A. Correct the addendum to 13. Do not edit or rewrite pilot-candidates.md.

4. **The token baseline is not a unique measurement.** U1 §3 proposes the matching v3 cohort, same route classes, per call and per episode. It does not fix the reduction formula, whether the reported figure is a mean of ratios or a ratio of sums, or which v3 calls are included. Consensus §3 keeps retained scored calls (88) separate from total charged calls (109) and forbids the scored aggregate from standing for all historical expenditure. An unlabeled match can collapse those. Unmatched route classes are not defined as null. Do not report a reduction until the comparator, the included call set, and the aggregator are committed. A null on either side stays null. Nullable price fields stay null with a reason; the reduction is an added derived field, not a deletion of that group.

## Retained

DECISIONS.md and addendum A confirm Astra Max (`openai-codex/gpt-6-astra:max` via omp) as the first judge. The user's visual verdict overrides, and both are recorded. U1 §2's "to be confirmed" is stale and does not reopen that identity. The 203 ceiling, separate 163/40 reservations, no borrowing, unchanged numeric active limits, full wall time, and the uncapped 600 s identical resend stay as decided. "5-minute fixes" means the settled 300 elapsed seconds from first edit through headless re-verification, including waits. Adoption, existing checks, and the full enrolled denominator are not waived by omission. Addendum A, not an extra unpublished filter, is the eligibility rule. This review does not authorize execution or a plan edit.

R2: BLOCK R2-4 still does not define a unique reduction against the named aggregate. R2-1, R2-2, and R2-3 close findings 1–3.

R2-4 groups the 88 retained calls in `aggregate-verify-v3-host-reviewed-r1-solfix-rerun2` by route class (spec, source, ask, completion, repair). That file's `route` values are source, spec, ask, completion, mvp, and offline. `repair` is a call stage/kind, not a route. `mvp` is in the retained set and is omitted, so those calls are dropped from the 88 or, if repair-stage calls are pulled out of their episode route, counted twice. The formula (1 − Σv4 / Σv3) × 100 is undefined when Σv3 is 0. In that aggregate, `cache_write_input_tokens` is 0, not null, on all 56 episodes that have token records; null only on 4 offline episodes with no calls. A sum of zeros is not the null case already stated. Group by the aggregate's route field, including mvp, with no repair route, and define Σv3 = 0 as a null reduction.

U1 §4 still says v4gemini never reads the private directory and validates only after the inputs are hashed and after freeze. R2-2 step 3 validates before the hash commit and before freeze. Mark those §4 sentences superseded. The implementer still does not read the review copy.

R3: AGREE

R3-1 groups by the aggregate `route` field (source, spec, ask, completion, mvp, offline), keeps repair-stage calls in the episode route, and includes the 88 once. R3-2 makes Σv3 = 0 a null `zero_baseline` reduction, including when Σv4 = 0, with no division by zero. R3-3 supersedes the conflicting U1 §4 sentences and keeps the implementer off the review copy and the private directory. No private holdout material was opened.
