# Gemini Review: C2 Production Recipe & Verification (C-R5v2)

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Review Target: Production C2 Recipe Implementation (`design/cad-harness-verify-v4/impl-notes-c2-recipe.md`).  
Authority: `C:\dev\CAD-HARNESS-herdr\.tmp-gemini-recipe.md` and `PLAN-V4-ADDENDUM-C.md` (§ C-R5v2).  
Invariants Observed: Read-only audit; zero pilot attachments (`pilot-user/`) or private holdouts (`v4-holdout-private`) were opened or referenced. Zero live model generation calls, zero pilot runs, no commit.

---

## 1. Audit Checklist with File:Line Evidence

### A. Alpha Foreground Extraction
- In `design/cad-harness-verify-v4/c2-production-recipe.json:4-8`, foreground is explicitly bound to `channel: "alpha"`, `polarity: "light"`, and `threshold: 128`. In `lines 9-11`, `alpha.policy: "ignore"` specifies that no secondary opacity gate is superimposed on the selected alpha channel.
- In `tools/cad_verify_v4_contours.py:270-320`, the mask is generated directly from the decoded alpha channel (`alpha >= 128`), fully independent of RGB components. Hidden or non-zero RGB data under transparent pixels cannot affect the mask or resulting geometry.

### B. No Min-R Fillet or Artificial Buffering
- In `design/cad-harness-verify-v4/c2-production-recipe.json:26-31`, `simplify.allowed: false` and `rounding.allowed: false` strictly prohibit candidate rounding, buffering, or hole deletion during preprocessing.
- In `tools/cad_verify_v4_contours.py:350-370` and `tools/cad_verify_v4_biarcs.py:38`, no tool-radius dilation or artificial corner filleting is added to force min-R compliance.
- The user's $R \ge 0.25\text{ mm}$ requirement remains an uncompromised geometric check evaluated directly on the actual CAD output section via `tools/cad_verify_v4_judges.py:min_radius` and `tool_access`.

### C. 50 mm Scaling Bound to Fitted Contour Y Extent
- In `design/cad-harness-verify-v4/c2-production-recipe.json:12-15`, scale specifies `canonical_height_mm: 50.0` and `origin_mm: [0.0, 0.0]`.
- In `tools/cad_verify_v4_contours.py:340-390`, boundary approximation runs first in source pixel units. Once the final fitted line/arc canonical boundary is established, its exact vertical Y extent (`fitted_Y_extent`) is computed, and a single uniform scalar (`50.0 / fitted_Y_extent`) scales both X and Y coordinates symmetrically, preserving aspect ratio without post-hoc normalization.

### D. Single Registration Bound to Both Fidelity Legs
- In `tools/cad_verify_v4_contours.py:420-460`, the derived affine transform (`pixel_to_mm`) is committed to `contour.json`.
- In `tools/cad_verify_v4_judges.py:750-775`, both Leg 1 (`image_to_contour`) and Leg 2 (`contour_to_output`) evaluate against this exact committed registration. Bounding box re-alignment or candidate-dependent registration after scoring is strictly rejected.

### E. Independent Development Fixtures Only
- In `design/cad-harness-verify-v4/dev-c2-production/generate.py:1-40` and `tools/test_verify_v4_c2_recipe_native.py`, all fixtures (annulus, ellipse, rounded rectangle, sharp notch) are generated from analytical pixel equations with deterministic 8x8 area supersampling.
- Zero pixels, dimensions, or geometry from `pilot-user/U5_logo.png` were accessed or used in recipe tuning.

### F. Fail-Closed Security & Hash Pinning
- In `tools/cad_verify_v4_c2_recipe.py:20-63`, the loader enforces exact file SHA-256 (`ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00`), sorted-key compact JSON SHA-256 (`361235a66c015765b65fbd1041c031a84b1b369c671a205dc1b4363d63eb8c06`), and registration SHA-256 (`e3c5a585550856c5bb144066c83c0b0d711ce0fd7e9fbb3e61069b71c1310d34`).
- Any byte modification, whitespace change, or missing file raises `ValueError` immediately. The loader rejects unknown fields, automatic fallbacks, or alternate recipes.

### G. Re-Run Verification of the Complete Host Suite
- **Executed Command**:
  ```bash
  python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_s1 tools.test_verify_v4_s1_integration tools.test_verify_v4_s2 tools.test_verify_v4_s3 tools.test_verify_v4_s3_judges_native.S3CardAdmission tools.test_verify_v4_integrated tools.test_verify_v4_runtime tools.test_verify_v4_artifact_judges_native.ContextAdmission tools.test_verify_v4_artifacts_native.ArtifactIntake tools.test_verify_v4_c2_recipe
  ```
- **Observed Result**: **183 tests run, OK (1 skipped)** in 88.50s. All 182 runnable tests pass; the single skip is the standard Windows symlink-creation privilege control.

---

## 2. Conclusion

The C2 production recipe implementation authored by Sol adheres strictly to C-R5v2, preserving experimental blindness, faithful alpha extraction, and uncompromised geometric tool checking.

Gemini verdict: **SIGN**.
