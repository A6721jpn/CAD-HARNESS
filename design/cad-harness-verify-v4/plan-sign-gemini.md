# Gemini Sign-off: VERIFY v4 Consensus Plan

Verdict: **AGREE**

---

## 1. Review Summary & Findings

The synthesized consensus plan in [`design/cad-harness-verify-v4/PLAN-V4-CONSENSUS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v4/PLAN-V4-CONSENSUS.md) accurately reconciles the proposals from Codex, Grok, and Gemini while faithfully honoring all user orders and constraints from [`BRIEF.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v4/BRIEF.md) and [`COMMITTEE-CONCLUSION-20261014.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v4/COMMITTEE-CONCLUSION-20261014.md).

No blocking defects or contradictions were found. The plan establishes rigorous experimental hygiene, clean architectural separation, and realistic operational safeguards.

---

## 2. Key Confirmations

### A. Phase Ordering and Zero-Call Invariant for Phases 1–2
- **Strict Sequence**: Phase 1 (Cost Ledger) → Phase 2 (Skill/CLI Packaging) → Phase 3 (Fresh Reproduction Holdout) → Phase 4 (Real Design Pilot).
- **Phases 1–2 Offline Invariant**: Guaranteed **0 live model calls** and no blocking user decisions. All backfills, schema validators, adapters, and CLI commands in Phases 1–2 operate purely against historical v3 logs, recorded responses, and deterministic unit mocks (`tools/test_verify_v4.py`).

### B. Live Call Budget & Accounting
- **Authorized Cap**: **203 charged accepted calls** total:
  - Phases 1–2: 0 calls.
  - Phase 3 (Holdout): 163 calls (14×4 source + 13×3 spec + 10×1 clarification + 6×4 completion + 10×3 MVP + 4 preview).
  - Phase 4 (Pilot): 40 calls (10 tasks × 4 max route cap).
- **Budget Hygiene**: Eliminates arbitrary live smoke and contingency pads. Overload rejections are exempt from the accepted-call count, so no reserve is consumed by provider outages. Scored-segment cost and total operational spend are recorded independently.

### C. Overload Policy & Active Stage Deadlines
- **Standing Rule Honored**: 600-second backoff with byte-identical payload resend and no retry cap upon verified `server_overloaded` without assistant output.
- **Clock Alignment**: Explicitly resolves the stage-clock paradox by excluding verified provider-unavailability intervals (rejection transport + 600s wait) from active deadlines (initial/repair 450s, episode 900s). Preserves full wall-clock accounting, monotonic interval tracking, and hard quota stops (55% consult, 60% hard stop).

### D. Single Append-Only Ledger & Nullable Pricing
- Unified `cad-harness.ledger.v4` JSONL journals operation initiation prior to invocation and results upon completion.
- Full streaming capture of `stdout` and `stderr` directly to disk for all attempts.
- Nullable pricing model: `null` is explicitly distinguished from zero. Illustrative or borrowed API rates are forbidden; pricing remains null unless an authoritative, user-supplied rate card with effective date is bound.

### E. Blind Fresh Holdout Protocol
- Preserves the 60-item suite structure (core 51 + 3 unscored previews + 6 completion) and all v3 scoring predicates, tolerances, and gates.
- Enforces strict custody: independent author, separate control reviewer, and independent custodian. Generator and workspace have zero access to plaintext requests/gold prior to execution; evaluation executes once without interim inspection, retry, or resume.

### F. Real Design Pilot Rubric & Fatal Quality Rule
- Ten consecutive user backlog tasks; synthetic or catalog tasks are prohibited (`not_run` if unavailable).
- Objective bar: at least 7/10 adopted as-is or corrected/re-verified within ≤ 300 elapsed seconds from first edit.
- Zero tolerance on critical dimension errors or fabrications in handed-over artifacts: immediately marks the task as FAIL. All judgments signed by a named human engineer.

---

## 3. Conclusion

The consensus plan is coherent, conservative, and ready to guide implementation. Gemini confirms full agreement: **AGREE**.
