# Gemini Sign-off: PLAN-V4 Update U1 + Addendum A

Verdict: **BLOCK**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).
Reviewed: `design/cad-harness-verify-v4/PLAN-V4-CONSENSUS.md`, `design/cad-harness-verify-v4/DECISIONS.md`, `design/cad-harness-verify-v4/PLAN-V4-UPDATE-U1.md` (including Addendum A), and `design/cad-harness-verify-v4/pilot-candidates.md`.
No private holdout directory (`C:\dev\v4-holdout-private`) was opened or read. Zero live model calls and zero live executions were performed.

---

## Exact Findings

1. **N=0 Pilot Roster Gap (Undefined Non-Success Handling)**:
   - PLAN-V4-UPDATE-U1 §1 and Addendum A state: *"If fewer than 10 are eligible, N is what exists. The pass line becomes ceil(0.7·N) and is fixed before the trial."*
   - Applying exclusion criteria E1–E5 across all 25 candidate items in `pilot-candidates.md` results in 0 eligible candidates ($N = 0$; see `pilot-select-gemini.md`).
   - If $N = 0$, $\lceil 0.7 \times 0 \rceil = 0$, which would permit a mathematically vacuous pilot PASS (0 successes out of 0 tasks).
   - This directly contradicts Consensus §3, §5, and BRIEF requirements: real pilot evaluation requires real user backlog tasks, and if no eligible tasks exist, the pilot status must be explicitly recorded as `not_run`, with no success fraction or PASS claimed. No synthetic, catalog, or rewritten tasks may be substituted. The update must define $N = 0 \implies \text{not\_run}$.

2. **Holdout Control Validation Timing and Freeze Sequencing**:
   - PLAN-V4-UPDATE-U1 §4 states: *"Control review: v4gemini validates the released items only after the run inputs are hashed."*
   - It also states: *"Release happens only after freeze. The run verifies the commitment."*
   - Consensus §4 strictly mandates: *"Lock implementation and skill before they author the cohort. They validate fresh requests, analytic gold and native controls without running the generation model. ... If author validation finds a defect, return to development before the final freeze and retire any exposed candidate material."*
   - If control validation takes place only post-release/post-freeze, defects detected during control review cannot be retired before freeze, violating the pre-freeze gate and risking invalidation of the entire reproduction run.
   - The execution sequence must be explicitly specified: implementation/skill lock $\to$ independent authoring and control validation of requests/gold/controls $\to$ cryptographic commitment and execution freeze $\to$ release and generation execution.

3. **Inconsistent Source Conversation Count in Addendum A**:
   - Addendum A describes the candidate source as *"25 real requests from 23 conversations, 2026-07-24 to 10-05"*.
   - In `pilot-candidates.md` (SHA-256 `63a39ed365324893df7615a83c17db5e217c1701d447594187a2360391910839`, which matches Addendum A), line 3 explicitly states: *"件数：25件／13一次会話"*.
   - Direct verification of distinct `会話ID` values in `pilot-candidates.md` yields exactly 13 unique conversations.
   - Addendum A must be corrected to reflect 13 conversations rather than 23 to preserve factual reconciliation across documents.

---

## Confirmations Retained

- **Judge Identity**: DECISIONS.md confirmed Astra Max (`openai-codex/gpt-6-astra:max` via omp) with visual double-check by the user (user verdict overrides).
- **Budget & Clocks**: Live budget cap remains strictly bound to 203 charged accepted calls (163 holdout + 40 pilot; 0 for Phases 1–2). Mandatory 600-second overload backoff with identical resends is excluded from active stage/episode deadlines, with full monotonic wall-clock recorded and no suite deadline.
- **Pricing & Evidence**: Pricing remains `null` with explicit missing reason in the absence of an authoritative user rate card. Token reductions against baseline propagate nulls.
- **Custody**: Option B holdout authoring isolation is recognized as procedural, to be formally disclosed in RESULTS.

---

## Revision 2 Review

R2: AGREE

Revision 2 (R2-1 through R2-3) directly resolves all three findings identified in Gemini's initial review:
1. **R2-1 (N=0 $\implies$ `not_run`)**: Eliminates the vacuous pass loophole by explicitly requiring `not_run` with no PASS or success fraction when 0 candidates survive E1–E5, preserving Consensus §§3 and 5.
2. **R2-2 (Holdout sequencing)**: Explicitly sequences implementation/skill lock $\to$ private authoring $\to$ control validation by v4gemini $\to$ hash commitments and final freeze $\to$ release and generation. Scored items remain uninspected during execution, preserving Consensus §4 pre-freeze validation gates.
3. **R2-3 (Conversation count)**: Corrects the source description to 13 primary conversations, matching the verified count and hash of `pilot-candidates.md`.

R2-4 establishes the comparator (v3 retained scored calls, 88 calls, aggregate `-solfix-rerun2`) and ratio-of-sums reduction formula. As required by Consensus §3 nullable arithmetic, any zero baseline sum ($\Sigma v3 = 0$) or missing/null contribution evaluates to a null reduction with reason (never divide by zero, never report 0%). No private holdout material was opened; zero live calls were performed.

---

## Revision 3 Review

R3: AGREE

Revision 3 completely resolves the remaining edge cases and ambiguities:
1. **R3-1 (Route grouping)**: Correctly groups by the aggregate's native `route` field (`source`, `spec`, `ask`, `completion`, `mvp`, `offline`), incorporating all 88 retained calls exactly once and retaining repair-stage calls within their parent episode's route.
2. **R3-2 (Zero baseline handling)**: Explicitly defines that $\Sigma v3 = 0$ yields a null reduction with reason `zero_baseline` (including when $\Sigma v4 = 0$), preventing any division by zero.
3. **R3-3 (Holdout review clarification)**: Formally supersedes the contradictory sentences in U1 §4 with R2-2, clarifying that v4gemini receives a pre-freeze review copy after private authoring to complete control validation before hash commitments and freeze, while implementer v4codex remains strictly isolated from private holdout materials.

No private holdout directory was opened; zero live calls were performed.
