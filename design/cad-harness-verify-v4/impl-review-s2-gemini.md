# Gemini Implementation Review: VERIFY v4 Stage S2

Verdict: **READY**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Reviewed:
- `design/cad-harness-verify-v4/impl-notes-s2.md`
- S2 core modules: `tools/cad_verify_v4_s2_{contracts,edit,judges}.py`
- Shared harness updates: `tools/eval_verify_v4.py`, `tools/cad_verify_v4_{agent,freeze,inputs,pilot,plans,s1,worker}.py`
- Profile assets: `design/cad-harness-verify-v4/policy-c-s2.json`, `skills/cad-harness-v4/c-s2.md`, `contracts-c-s2.md`, and schemas `design/cad-harness-verify-v4/schemas/s2-*.schema.json`
- Synthetic dev fixtures: `design/cad-harness-verify-v4/dev-c-s2/`
- Full test suites: `tools/test_verify_v4_s2.py`, `tools/test_verify_v4_s2_edit_native.py`, and `tools/test_verify_v4_s2_judges_native.py`

Verification Executed:
1. **Host Test Suite**:
   ```bash
   python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_s1 tools.test_verify_v4_s1_integration tools.test_verify_v4_s2
   ```
   **Result**: 127 tests run, **OK (1 skipped)** in 7.12s. All 92 baseline v3/v4 tests, all 26 S1 host tests, and all 8 new S2 host tests pass.
2. **Native FreeCAD Suite** (with `CAD_VERIFY_S1_NATIVE=1` and `CAD_VERIFY_S2_NATIVE=1`):
   ```bash
   C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe -B -m unittest tools.test_verify_v4_s1_native tools.test_verify_v4_s2_edit_native tools.test_verify_v4_s2_judges_native -v
   ```
   **Result**: 59 native tests run, **OK** in 42.17s on FreeCAD 1.1.4 / Python 3.11.14 / OCCT 7.8.1. (22 S1 native tests + 13 S2 edit native tests + 24 S2 judge native tests).

Invariants Honored: Zero pilot attachments (`pilot-user/`) or private holdout files (`v4-holdout-private`) were opened or referenced. Zero live model generation calls, zero live CAD test executions, no git commit.

---

## 1. Core Audit Checklist

### A. Face-Selection Binding
- **Dual Geometric Signature & Topological Adjacency**: Implemented in `tools/cad_verify_v4_s2_edit.py` (`_selector` and `_native_selector`).
  - Face selection does not rely solely on transient `FaceN` identifiers. It binds a SHA-256 geometric signature composed of surface type, quantized area, quantized center of mass, quantized bounding box, and quantized normal with canonical signed-zero handling (`+0.0` vs. `-0.0`).
  - Strict topological adjacency binding requires the exact, sorted list of shared-edge neighbor face IDs (`adjacent_face_ids`).
- **Native Verification against Loaded Geometry**: When the native Part shape is loaded, `_native_selector` recomputes all face signatures and actual edge shared-adjacency from the raw CAD B-rep. If signatures are non-unique, stale, or adjacent topology mismatches, execution immediately aborts with `ValueError("native_signature_not_unique_or_stale")` or `ValueError("native_adjacency_mismatch")`.
- **Replacement Patch Boundary Binding**: Finite replacement patches require planar source and replacement supports. The replacement face must fully cover the resulting trimmed face without unconfirmed clipping or floating patches.

### B. C6 Judges Implementation (Thickness, Unchanged Dimensions, Face Counts, Solid Validity)
- **`thickness_distribution`**:
  - Implemented in `tools/cad_verify_v4_s2_judges.py`. Evaluates normal ray casting between explicitly declared opposing surface sets (`source_opposed_face_ids` and `target_opposed_face_ids`).
  - Correctly detects interior cavities, multiple solid crossings along a ray, and wrong opposing face hits as explicit failures.
  - Distinguishes continuous domain certificates from sampled point checks. Unsupported continuous domains evaluate sampled observations and leave global extrema as `null` with explicit `UNVERIFIED` status.
- **`unchanged_dimensions`**:
  - Evaluates source-relative axis extents and registered landmarks in the original fixed frame.
  - Utilizes `optimalBoundingBox(False, False)` on trimmed geometry, preventing untrimmed spline support extents from distorting measurements.
  - Bounding box checks do not allow alignment optimizations to mask local translation or rotation.
- **`preserved_regions`**:
  - Evaluates two-way symmetric volume differences (`material_lost_mm3` and `material_added_mm3`) within a fixed region of interest (ROI). Correctly flags local feature shifts that maintain equal global bounding box and volume.
- **`face_counts`**:
  - Validates positive-area clipped regional or whole-solid BREP face counts against expected counts/deltas.
- **`solid_valid`**:
  - Evaluates `shape.isValid() == True`, `shape.isNull() == False`, `len(shape.Solids) == 1`, and manifold closed shell topology.
  - Recomputes all checks via independent reopening in a separate subprocess, ensuring no in-memory cache leakage from the compilation step.

### C. S1 Profile Preservation (Zero Regressions)
- **Host & Native Regression Suites**: All 119 host tests pass (all 92 v3/v4 baseline tests + 26 S1 host tests), and all 22 S1 native tests pass without failure.
- **Baseline Snapshot Integrity**: Pre-S2 S1 executable source set (98 files, 935,955 bytes) is hash-locked and verified in `design/cad-harness-verify-v4/s1-profile-snapshot.zip` (SHA-256 `f1f0276822bea29e1da951a449b2ff5203c989e7a204cc1e721f0de0124bb816`).
- **Profile Segregation**: S2 capabilities operate strictly under the separate `c-s2` profile (`policy-c-s2.json`, `c-s2.md`, `contracts-c-s2.md`) and distinct schemas (`s2-*.schema.json`). Original v4 and S1 profiles remain untouched.

### D. No Pilot-Derived Values
- **Complete Sanitization**: Grep analysis across all S2 modules, schemas, and test files confirms zero occurrences of pilot part tokens or user values (`U1`–`U5`, `NF13`, `Astage`, `Apple`, or U4 frame parameters).
- **Independent Synthetic Fixtures**: All development, unit tests, and native verification rely strictly on synthetic geometric fixtures (`dev-c-s2/` and `tools/test_verify_v4_s2*.py`: planar blocks, tilted wedges, and cubic B-spline roofs).

### E. Semantic Separation of INCOMPLETE vs. UNVERIFIED
- **`INCOMPLETE` (Harness / Process Interruption)**:
  - Applied in `cad_verify_v4_s1.py` and `eval_verify_v4.py` when process execution fails due to unexpected technical faults, process timeouts, abnormal termination, missing dependencies, card binding drift, or quota halts.
  - Ensures operational/host failures are never masked as model-repairable geometry failures.
- **`UNVERIFIED` (Indeterminate Geometric Verification)**:
  - Applied in `cad_verify_v4_s2_judges.py` when candidate CAD geometry is successfully produced and inspected, but the geometric certificate cannot be mathematically proven (e.g., measurement uncertainty spans the tolerance boundary, incomplete continuous ray domain coverage, missing judge card criteria, or uncertified continuous extrema).
  - Preserves clean scientific reporting: candidate models are not falsely failed or falsely passed when evidence is incomplete.

---

## 2. Conclusion

The Stage S2 direct B-rep editing implementation authored by Codex strictly complies with Addendum C, Decision 2026-10-14 14:28 JST, and the architectural requirements. All 186 tests (127 host + 59 native) pass deterministically on DPC-019.

Gemini verdict: **READY** for Stage S2 implementation lock.
