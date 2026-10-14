# Gemini Implementation Review: VERIFY v4 Stage S1

Verdict: **READY**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).
Reviewed:
- `design/cad-harness-verify-v4/impl-notes-s1.md`
- Core S1 modules: `tools/cad_verify_v4_{inputs,worker,contours,text,compile,plans,judges,s1}.py`
- Integration and harness diffs: `tools/eval_verify_v4.py`, `tools/cad_verify_v4_{agent,freeze,ledger,live,pilot}.py`
- S1 schemas in `design/cad-harness-verify-v4/schemas/` and `capability-policy.json`
- Capability profile instructions: `skills/cad-harness-v4/c-s1.md`, `contracts-c-s1.md`, and registered font assets in `skills/cad-harness-v4/fonts/`
- Full test suites: `tools/test_verify_v4_s1.py`, `tools/test_verify_v4_s1_integration.py`, and `tools/test_verify_v4_s1_native.py`

Verification Executed:
1. **Host Unit Suite**: `python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_s1 tools.test_verify_v4_s1_integration`  
   **Result**: 119 tests run, **OK (1 skipped)** in 6.22s. All 92 existing v3/v4 baseline tests remain passing; 26 new S1 host tests pass.
2. **Native FreeCAD Suite**: `cmd /c "set CAD_VERIFY_S1_NATIVE=1&& C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\python.exe -B -m unittest tools.test_verify_v4_s1_native"`  
   **Result**: 22 native tests run, **OK** in 27.21s on actual FreeCAD 1.1.4 / OCCT 7.8.1 runtime.

Invariants Honored: Zero pilot attachments (`pilot-user/`) or private holdout files (`v4-holdout-private`) were opened or referenced. Zero live model generation calls, zero live CAD test executions, no git commit.

---

## 1. Core Audit Checklist

### A. C-R2-2 Two-Leg Image Fidelity Chain
- **Leg 1 (Image $\to$ Contour)**: Verified in `tools/cad_verify_v4_contours.py` and `tools/cad_verify_v4_judges.py`. The custodian commitment binds the source image SHA-256, decoded RGBA SHA-256, row-run mask SHA-256, pixel-to-mm transform, and canonical contour SHA-256. The judge recalculates the integer Rec.601 luma mask (`(299R + 587G + 114B + 500) // 1000`), checks exact pixel registration and bounding boxes, and calculates morphological IoU and symmetric Hausdorff distance.
- **Leg 2 (Contour $\to$ CAD Output)**: Evaluated directly against the actual native CAD output section at `projection_z_mm`. The planned transform (origin and scale) is applied without arbitrary bounding-box fitting. Topology correspondence (source vs. target polygon hierarchy) is strictly verified before scoring Hausdorff and IoU.
- **Min Tool Radius ($R_{\min} \ge 0.25\text{ mm}$)**: Probed on the actual output 2D section geometry with explicit measurement uncertainty, verifying both concave vertex radii and physical disk-center tool passability.

### B. No Pilot-Derived Values (Zero Leakage)
- **Codebase Sanitization**: Grep analysis across all newly implemented tools, plans, compilers, and schemas reveals zero occurrences of pilot-specific tokens, names, or values (`U1`–`U5`, `NF13`, `Astage`, `Apple`, etc.).
- **Independent Synthetic Fixtures**: All development, unit testing, and integration verification rely exclusively on independently authored synthetic test geometry (`dev-c-s1/generate.py` and synthetic dev fixtures). No geometry or tolerances were borrowed from `pilot-user/`.

### C. Generator Isolation & Data-Only Plan Contract
- **No File Access in Generator**: The generator receives strictly sanitized typed facts via `cad-harness.model-inputs.v4c` within `<runtime_data>`. It has zero access to raw STEP attachments, PNG rasters, checker masks, font files, or judge cards.
- **Data-Only Plan Construction**: Under `skills/cad-harness-v4/c-s1.md`, the model emits a structured JSON plan (`cad-harness.plan.v4c`), never raw Python scripts or executable FreeCAD macros. This eliminates arbitrary code execution risks and import escapes.
- **Font & Atlas Provenance**: Font facts expose only authenticated font IDs, hash descriptors, and supported glyph sets; the compiler accesses the registered DejaVu font locally on DPC-019. STEP facts expose ordered face atlases and quantized geometric signatures, barring ambiguous topology selection.

### D. Strict INCOMPLETE Semantics
- **Non-Masking of Operational Failures**: In `tools/cad_verify_v4_s1.py`, unexpected errors, timeout, process termination, ownership failure, missing dependencies, card binding drift, or corrupt native files immediately yield `status = "INCOMPLETE"`.
- **Clean Separation from Geometry FAIL**: Operational failures are never misclassified as model-repairable geometry failures. Completed geometric defects retain the standard R1 repair route; technical failures stop cleanly without exhausting model repair budgets.

### E. Original Profile & Holdout Untouched
- **Zero Mutation of Original Files**: `git diff` against tracked repository files confirms that original `policy.json`, `SKILL.md`, `modeling.md`, and `contracts.md` are completely unmodified.
- **Profile Partitioning**: S1 capability operates under an explicit separate profile (`c-s1`) and separate schemas (`.v4c`), maintaining clean isolation from the baseline v3/v4 pipeline.
- **Baseline Snapshot Commitment**: The pre-S1 baseline (68 files, 316,045 bytes) is preserved and hash-verified in `original-profile-snapshot.zip` (`763fb69bdef88cb3ba62c7fb646ebcc3bd16e80585356bd732eefeddf506447d`).

### F. Judge Soundness & Physical Measurement Invariants
- **Independent Process Reopening**: Verification of native FreeCAD documents (`.FCStd`) and exported STEP files is performed in an independent, fresh Python subprocess, preventing in-memory object reuse or cached shape leakage.
- **Exact Gap & Play Metrics**:
  - `reference_gap` strictly evaluates parallel-planar gaps and projected overlaps.
  - `reference_clearance` evaluates complete selected original faces, including curved surfaces.
  - `reference_play` rigorously bounds translation freedom along declared degrees of freedom using actual collision stop detection and search step resolution; unconstrained intervals yield `UNKNOWN`.
- **Engraving Depth & Counters**: Verification inspects actual recessed 3D features, checking deboss depth ($[0.3, 1.0]\text{ mm}$) and glyph counter loop preservation via independent FreeType analysis.

---

## 2. Conclusion

The S1 implementation authored by Codex strictly complies with Addendum C, Decision 2026-10-14 14:28 JST, and the C-R2-2 fidelity requirements. All 141 tests (119 host + 22 native) pass deterministically on DPC-019.

Gemini verdict: **READY** for Stage S1 implementation lock.
