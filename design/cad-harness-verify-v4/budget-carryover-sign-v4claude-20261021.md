# Budget carryover: v4claude summary-only procedural review (2026-10-21)

**Verdict: AGREE (conditional).** The bounded cumulative-budget repair may go on to commit/push and a new lock. Release for production stays closed until every gate listed below passes.

## Limitation

I read only `budget-carryover-summary-sol-20261021.md`. I saw no source, diffs, evidence, notes, private inputs or outputs. I ran no commands, tests, CAD, models or Git, delegated nothing, and had no contact with Gemini or Grok. Every result and SHA in the summary is Sol's statement. This is a procedural consistency check, **not** an independent code audit, and **not** a production authorization.

## Consistency check: no internal inconsistency found

1. **The arithmetic holds.** 163 − prior 4 = 159 new counted calls. Each figure below is consistent with that:
   - the boundary tests;
   - the DEV smoke, where 159 reservations reached 163 and the 160th was refused;
   - the spent-budget test, where 0 new calls were admitted;
   - the rule that `charged_calls` stays at the global 163 ceiling.

   The prior value is required and strictly validated, with no implicit default of 0. There is no workaround, wrapper cap or fake quota.
2. **The prior-run figures match my custody records.** I operated the first attempt, and its details agree with what I recorded:
   - 4 counted calls, 1 CAD attempt, INCOMPLETE/harness:legacy_runtime;
   - ledger `5867a5b7…`, summary `fb0f4b46…`;
   - cohort `45bb80a5…`.

   These 4 calls become the frozen prior value. They are not refunded, and the results are not pooled.
3. **The record count adds up.** 406 identical + 5 changed (2 production files, 2 existing test files, the DECISIONS record) = 411, matching the review snapshot of 411 records.
4. **The scope matches what the USER approved.** The change covers counting only:
   - authorization validation;
   - guard initialization.

   Caps, quota, rule 6, refunds, policy, gates, scoring, cards and the cohort bytes and order are all reported unchanged. Per-run costs in the ledger cover new activity only, and prior and new cumulative calls are reported separately.
5. **Paid activity is still zero.** No paid CAD-model calls, new authorization or new claim. The DEV reservations are not production charges.

Observation, not a blocker: only the model-call budget carries over. Episode caps start fresh because the same 60 run again from the beginning.

## Gates that must all pass before any production call

1. All 10 refreshed DEV native checks actually PASS. The refresh is still in progress and is not yet passed. If any fails, STOP and ASK.
2. Bounded commit/push to `herdr/v4`, excluding caches and private or unrelated changes.
3. A new integrated lock with all five recipes, whose authoritative verification passes and whose 411-record source map matches `e50ae182…` exactly.
4. A new frozen original authorization that binds prior 4 and the prior attempt's evidence and passes verification. It must also take a fresh quota admission and keep the 60-episode custody unchanged.
5. A new exclusive claim.

During the run, 55% means ASK and 60% means STOP. A non-budget issue or any issue found during the run means ASK without fixing. There is no automatic restart after a terminal stop.
