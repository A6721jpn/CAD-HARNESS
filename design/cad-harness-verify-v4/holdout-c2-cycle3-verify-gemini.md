# Verification of C2 Cycle 3 Holdout Commitment & Pilot v4 — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Verification Target: Public records committed in HEAD (`0ea24bc` on `herdr/v4`):
- `design/cad-harness-verify-v4/holdout-families-commitment.md` (§ C2 cycle 3)
- `design/cad-harness-verify-v4/pilot-bundle-commitment.md` (§ Pilot v4 (cycle 3))  
Authority: `.tmp-gemini-c3v.md` and `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (§§ C-R4, C-R7, C-R8v3).  
Invariants Observed: Strict read-only audit of PUBLIC records only. Zero access to `C:\dev\v4-holdout-private` or `pilot-user/` attachments. Zero live model generation calls, zero live CAD runs, no commit.

---

## 1. Audit Checklist: `holdout-families-commitment.md` (C2 cycle 3)

### A. Counts and Strata Match the Signed Plan
- In `holdout-families-commitment.md:131`:
  - **Generative Cohort** (10 items):
    - `convex`: C2-01, C2-02, C2-03 (3 items)
    - `connected_holes`: C2-04, C2-05, C2-06, C2-07 (4 items)
    - `notch_tool_access`: C2-08, C2-09, C2-10 (3 items)
  - **Benchmark Pairs** (4 pairs):
    - `convex`: B05, B08 (2 pairs)
    - `connected_holes`: B06 (1 pair)
    - `notch_tool_access`: B07 (1 pair)
  - **Total Items**: Exactly 10 generative items + 4 benchmark pairs (14 items total).
  - Allocation strictly preserves the signed stratum partition from earlier cycles (`lines 94, 121`).

### B. Recipe SHA Matches the Committed File
- In `holdout-families-commitment.md:133`:
  - Recorded path: `design/cad-harness-verify-v4/c2-production-recipe-cycle3.json`
  - Recorded SHA-256: `af0a2e13ff292404684a43e1227c3f3bfda327c72ffcdb24004c05cbd41a4934`
  - Recorded size: 928 bytes
- Independent check of local file `design/cad-harness-verify-v4/c2-production-recipe-cycle3.json`:
  - Computed SHA-256: `af0a2e13ff292404684a43e1227c3f3bfda327c72ffcdb24004c05cbd41a4934`
  - Computed size: 928 bytes
  - Exact match.

### C. Cycle-2 Cohort Retired as History
- In `holdout-families-commitment.md:129`:
  - The previous cycle-2 cohort files were cleanly moved (not modified or overwritten) to `retired-c2-cycle2/`.
  - Marked with `retired-c2-cycle2/RETIRED.txt` as historical record.
  - Previous recipe SHA-256 (`0b6d09b67c67a050de5247e9c28f95abc454ee33b2c8cef604f5839ea7dc7e04`, 847 bytes) recorded as retired metadata.
  - Full SHA-256 table (`lines 980-1124`) tracks all retired cycle-2 bundle members alongside earlier retired cycle-1 and v1 cohorts.

### D. Zero Coordinates or Content Leakage
- In `holdout-families-commitment.md:127-136`:
  - Only component and hole counts per item, strata labels, item IDs, and recipe metadata are recorded.
  - Explicit commitment (`line 133`): *"This file records no contour coordinates."*
  - Zero coordinate pairs `[x, y]`, polygon loops, or geometry descriptors are present.

### E. Zero Live Model Calls
- In `holdout-families-commitment.md:133`:
  - Explicitly committed: *"Live calls: 0."*
  - Admitted under `evidence_mode: "independent_dev"` with `output_object: null`.
  - No model generation ran.

---

## 2. Audit Checklist: `pilot-bundle-commitment.md` (Pilot v4 (cycle 3))

### A. Single Invocation
- In `pilot-bundle-commitment.md:151,166`:
  - Exactly one image-to-contour invocation ran after the cycle-3 cohort was committed.
  - Invocations: 1. Exit code: 0. Status: `PASS`.
  - Zero model generation calls, zero second attempt.

### B. Unedited Production Recipe
- In `pilot-bundle-commitment.md:155-161`:
  - Recipe file: `design/cad-harness-verify-v4/c2-production-recipe-cycle3.json`
  - SHA-256: `af0a2e13ff292404684a43e1227c3f3bfda327c72ffcdb24004c05cbd41a4934`, 928 bytes.
  - Verified identical before and after the run.

### C. Input PNG SHA Matches `pilot-user-requests.md`
- In `pilot-user-requests.md:75`:
  - Attachment U5: `pilot-user/U5_logo.png`, raster RGBA 814x1000, 39139 bytes.
  - Recorded SHA-256: `cff917e0b7e317eff88977aafea0379a99522e3ab120b36b7d73ee5626bfdd3b`.
- In `pilot-bundle-commitment.md:161`:
  - Recorded SHA-256: `cff917e0b7e317eff88977aafea0379a99522e3ab120b36b7d73ee5626bfdd3b`, 39139 bytes.
  - Verified exact match to the user-supplied asset without modification or re-encoding.

### D. Leg-1 IoU and Hausdorff Meet C-D(a) Envelope
- In `pilot-bundle-commitment.md:174`:
  - Thresholds: mask-to-contour $\text{IoU} \ge 0.90$, $\text{Hausdorff} \le 1.5\text{ mm}$.
  - Measured point IoU: $0.9967485812614983 \ge 0.90$ (**PASS**).
  - Certified IoU enclosure ratio: $0.9940656161169514 \ge 0.90$ (**PASS**).
  - Measured Hausdorff upper: $0.347902178443684\text{ mm} \le 1.5\text{ mm}$ (**PASS**).

### E. Minimum Radius Meets Requirement
- In `pilot-bundle-commitment.md:175`:
  - Threshold: $R \ge 0.25\text{ mm}$.
  - Measured min-R: $0.280754330499573\text{ mm} \ge 0.25\text{ mm}$ (**PASS**).
  - Evaluated directly on the published contour report.

### F. Zero Coordinates Leakage
- In `pilot-bundle-commitment.md:178`:
  - Explicit confirmation: *"No contour coordinates are in this file."*
  - Only scalar verification metrics, file digests, and execution metadata are present.

---

## 3. Conclusion

All requirements for the public holdout commitment and pilot v4 execution are satisfied:
1. `holdout-families-commitment.md` (§ C2 cycle 3) reflects the signed strata distribution, matches the active recipe hash, retires the cycle-2 cohort as history, leaks zero coordinates, and reports zero live calls.
2. `pilot-bundle-commitment.md` (§ Pilot v4 (cycle 3)) documents a single invocation on the unedited cycle-3 recipe using the verified user PNG hash, satisfying Leg-1 C-D(a) fidelity and min-R thresholds without coordinate leakage.

Verdict: **SIGN**
