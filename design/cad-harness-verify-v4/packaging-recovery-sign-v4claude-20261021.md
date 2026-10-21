# Packaging recovery: v4claude summary-based verdict (2026-10-21)

**Verdict: SIGN**, limited to the summary. This supports proceeding with the bounded commit/push and the new post-push lock.

## Limitation

I read only `packaging-recovery-summary-sol-20261021.md`. I did not read source, diffs, other documents, evidence files or private artifacts. I ran no commands or tests, delegated nothing and contacted no one. Every evidence identity and check result below is Sol's statement, not something I observed. This is **not** an independent code audit. It is not a full-v4-ready verdict and it is not a production or live authorization.

## Reasons

1. **Same defect as my STOP.** The repair addresses the root cause in my original60 STOP receipt (§10.1 of `impl-review-launchers-v4claude.md`). That cause was a missing `design/cad-harness-mvp/eval-v1/schema.json` in the isolated episode, which made the offline legacy control fail at preflight with `FileNotFoundError`. According to the summary:
   - the live module now packages the existing MVP and v3 gold schemas;
   - the freeze module now binds the MVP schema that it previously omitted.

   Packaging the v3 schema too is the same missing-file class on an existing route. It adds no new capability.
2. **Scope is minimal.**
   - Two production files and two existing test files changed.
   - Schema bytes, gates, policy numbers, cards, scoring and frozen limits are unchanged.
   - No private input was used.
   - There were 0 additional model or CAD calls. Original60 was not resumed, and its four counted calls and consumed claim are kept.
3. **Reported checks fit the fix.**
   - Host discovery: 0 FAIL/ERROR.
   - A new real-FreeCAD isolated offline regression passed.
   - The MVP and v3 checker contracts each accept valid DEV gold and reject missing dimensions.
   - The offline freeze verifier passed with both schemas bound and authorization null.
   - The neutral CLI checks passed 10/10.
   - The test-path correction is disclosed, and the failed record is kept.
4. **Public identities are consistent with my own records.** Sol reports the family commitment and controls unchanged (`253e2a9f…` / `169f918f…`). Those are the identities of the documents I published. The original public commitment `d87165ce…` is Sol's statement.

## Conditions (Sol still has to do these)

- **Explain the record count.** The snapshot has 411 records, against 410 prior records, of which 405 are unchanged. Sol should state in the lock evidence which record is new, presumably the newly bound MVP schema.
- **Build and verify the new lock.** Sol must create the new post-push integrated lock with all five recipes, actually verify it, and confirm that its source map matches snapshot `6627c5d3…`.
- **Finish and wait.** Sol should update PROGRESS and then wait. Original60 is not restarted, no paid probe runs and no new claim is created. Any future production run is a separate USER decision.
