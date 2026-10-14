# VERIFY v4 BRIEF (user order 2026-10-14 09:54 JST)

Source: COMMITTEE-CLI conclusion (copied as COMMITTEE-CONCLUSION-20261014.md). The committee's first choice for practical usefulness was REAL_PILOT; for closing the evidence gap it was FRESH_HOLDOUT.
Base: frozen v3 (HEAD ca8eb51, manifest verify-v3-reviewed-r1-solfix). The final v3 result is PASS, 60/60 after rerun2.

## Scope, in user priority order
1. **Cost measurement.**
   - Record tokens (including geometry), wall time (including waits and interruptions), and price per call, per episode and per run, in one ledger.
   - A missing value stays null; it is never 0. Price uses a documented rate source; if there is none, the price is null with a reason.
2. **Consolidation.** Move rules (scoring, resend, logging policy) into a skill, and deterministic processing into CLI commands. The text sent to the model is only the design request plus that skill.
   - Pass criterion: one entry point completes a request.
   - Existing gates must be unchanged.
3. **Reproduction.** Run once end-to-end on a fresh, unseen holdout. That means one segment and one manifest, with no mid-run inspection, fixing or re-taking. The verdict uses only gates fixed before the run.
4. **Real design-work trial.** Pass criteria are fixed and committed BEFORE the trial. Proposed:
   - At least 70% of tasks need no edits, or fixes of 5 minutes or less.
   - Any critical dimension error or any fabrication is a fail.
   - Record per task: adopted or not, which parts were edited and how much, and time including waits.
   - The tasks must be real design requests. If the user must supply them, that is a user-decision point.

## Constraints
- Save stdout and stderr for every attempt.
- Do not count a run that had no overload as evidence of overload robustness.
- No range expansion (no new shape or capability classes).
- FreeCAD 1.1.4 headless on DPC-019 only. No Fusion, no SolidWorks, no CAE, no invented numbers.
- Quota: consult at 55%, stop at 60%. On server_overloaded: wait 600 s and resend.
- Never tune on test items. Never overwrite old reports. Commit and push after each commit (no force, no reports/ or .tmp/).
- Process: three-party plan consensus, then implement, reviews, freeze, run, RESULTS consensus.

## Each planner must answer
- The concrete deliverables for 1–4, and their order.
- File and CLI layout.
- The ledger schema.
- How the holdout is authored without being seen.
- The pilot task source and the pre-registered rubric.
- The call budget.
- Stop rules.
- What needs a user decision.
