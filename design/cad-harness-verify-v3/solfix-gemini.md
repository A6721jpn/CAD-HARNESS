# Gemini Verdict: SOLFIX (verify-v3-reviewed-r1-solfix)

AGREE

---

## 1. Assessment of Root Cause and Proposed Fix

The evidence in [`SOL-FAILURE.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/SOL-FAILURE.md) and the episode session logs is conclusive:
- The failure on `q-A5-r5` (call 1, exit 1 in 3.97s) and earlier non-passes on `geometry-G5-r1` (call 2, exit 1 in 7.8s) and `geometry-G1-r2` (call 2, exit 1 in 8.9s) were caused strictly by transient provider-side capacity rejections (`codex_error_info: "server_overloaded"`). In all three cases, no model generation occurred.
- The five proposed fix elements in [`SOLFIX-BRIEF.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/SOLFIX-BRIEF.md) are sound, minimal, and preserve experimental integrity:
  1. **Strict Classification**: Parsing `--json` stdout for `codex_error_info` in `{server_overloaded}` without final text output cleanly isolates provider rejections from genuine model reasoning/format failures.
  2. **Bounded Retry**: At most 2 retries with 30s / 90s exponential backoff, clipped to stage/episode/shared deadlines and counting toward the 163-call cap without consuming model P/R slots, prevents transient provider outages from aborting entire evaluation suites.
  3. **Artifact Capture**: Bounded tail capture (≤16 KB) for stdout/stderr directly solves the observability defect.
  4. **Resumption Segment**: Adding `eval_verify_v3.py resume` to execute only the 14 unstarted episodes (47..60) in frozen order, while locking all 46 completed records byte-identical with dual-manifest aggregation and strict segment clocks, avoids wasteful re-execution while preserving auditability.
  5. **Re-freeze**: Archiving `SHA256.json` → `SHA256.run-r1.json` and re-freezing under `verify-v3-reviewed-r1-solfix` ensures complete cryptographic provenance.

---

## 2. Explicit Decision on Open Question

**AGREE with supervisor default**: Keep `geometry-G5-r1` and `geometry-G1-r2` scored as recorded.
- **Rationale**:
  - Respects the foundational principle of "no manual result replacement" established in [`PLAN-V3-CONSENSUS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/PLAN-V3-CONSENSUS.md).
  - The source cohort pass threshold requires `sum(passed) >= 8` and `all(passed) >= 1` across G1–G5. With G1-r1, G2-r1, G2-r2, G3-r1, G3-r2, G4-r1, G4-r2, and G5-r2 all passing, exactly 8 out of 10 episodes passed and every case passed at least once. The threshold is met even with both provider-rejected episodes counted as failures.
  - Transparent attribution will be documented in `RESULTS.md` with a `provider_rejected` annotation in the aggregate report.

consensus: AGREE 16:26 JST
