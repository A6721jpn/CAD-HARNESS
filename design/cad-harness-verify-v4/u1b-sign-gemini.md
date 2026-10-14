# Gemini Sign-off: PLAN-V4 Update U1 Addendum B

Verdict: **BLOCK**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).
Reviewed: `design/cad-harness-verify-v4/PLAN-V4-UPDATE-U1.md` (including Addendum B: Pilot Reopening, 2026-10-14 13:36 JST).
Independent screening executed and recorded in `design/cad-harness-verify-v4/pilot-select-b-gemini.md`.
No private holdout material was opened; zero live model calls and zero CAD executions were performed.

---

## Findings and Required Concrete Fixes

The reopening of pilot selection with verbatim requests, original conversation context, and attachments is accepted in principle. However, four concrete specification fixes are required before enrollment or execution freeze:

1. **B1 Context Extraction & Window Size Specification**:
   - **Fix**: Define the 40,000-character limit strictly as Unicode character count (not UTF-8 bytes) of retained message text.
   - **Window extraction**: Extract a contiguous suffix of complete user/assistant message turns occurring strictly prior to the target request locator; never truncate mid-message or omit intervening turns.
   - **Locator contract**: Formally distinguish physical line numbers in JSONL files from turn/message ordinals (e.g., candidate 1 has target at physical line 9 / turn ordinal 8). Exclude under E6 if the source is missing, unreadable, non-JSONL (e.g., SQLite), or if the locator fails to match the verbatim request.

2. **B2 Dependency Closure & Attachment Verification (E7)**:
   - **Fix**: Enforce an explicit dependency closure verifying that every file, image, directory, or geometry referenced in the request or retained context exists and is readable on disk.
   - Relative paths must resolve strictly against the session's recorded working directory (`cwd`).
   - Missing attachments (e.g., deleted clipboard selection images, missing STEP attachments, or absent workflow files like `C:\dev\CAD\CAD_modeling_workflow.md`) must trigger exclusion under E7.
   - Copy verified attachments into an immutable, hashed pilot bundle before trial freeze; never reconstruct or substitute files.

3. **Critical Dimension Pre-registration Procedure (E4)**:
   - **Fix**: For any candidate considered for enrollment, explicit critical dimensions, units, reference features, and tolerances must be extracted directly from the request or retained context.
   - Distinguish dimensions that can be queried via the existing typed clarification route from dimensions absent beyond that route; only the latter establish E4.
   - If clarification is needed, genuine human answers must be obtained before trial commitment without rewriting request text. If objective acceptance criteria cannot be agreed upon by all three parties and committed to `pilot-rubric.json`, exclude under E4. LLM surrogates must never fabricate missing human dimensions.

4. **Preservation of Consensus §5 Quality & Evaluation Invariants**:
   - **Fix**: Explicitly confirm that Addendum B does not dilute or waive Consensus §5 gates:
     - Human adoption is mandatory for task success.
     - Headless re-verification must complete within $\le 300$ elapsed seconds from first edit (including waits).
     - Any critical dimension error or fabrication in the first or later handed-over artifact results in fatal task and pilot failure.
     - Astra Max acts as preliminary judge; the user's visual verdict remains authoritative and overriding.

---

This sign-off is a technical review finding, not an authorization to execute or commit.
