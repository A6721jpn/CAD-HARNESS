# Addendum C-D Delegated Proposals & Specifications — Gemini

**Agent:** Gemini (`google-antigravity/gemini-3.8-flash`)  
**Target:** `c-d-proposal-gemini.md`  
**Authority:** User Decisions 2026-10-14 17:28 JST (`DECISIONS.md`), `PLAN-V4-ADDENDUM-C.md` Sections C-A2 and C-D.  
**Inviolable Rules:**
1. Zero inspection of or derivation from `pilot-user/` attachments (`U1.step`–`U5.step`, `U5_logo.png`).
2. Do not touch or open `C:\dev\v4-holdout-private`.
3. Zero live model calls, zero pilot runs, no git commit.
4. No invented measurements or results; missing baseline metrics remain null until observed.

---

## (a) Lenient U5 Fidelity Thresholds (Both Legs)

### Context & Deliverable Model
Per User Decision 17:28 (C-A2), the U5 deliverable is a **cut-out logo part** (solid logo silhouette with separate leaf component, not a surrounding plate with a cutout). The user explicitly specified: *"the logo only needs to match roughly; model correctness matters more. The agents set lenient IoU/Hausdorff thresholds; the user checks visually."*

### Proposed Concrete Thresholds

| Fidelity Leg | Metric | Proposed Threshold | Technical Rationale |
| --- | --- | ---: | --- |
| **Leg 1: `image_to_contour`** (Raster $\to$ Canonical Vector) | **Minimum IoU** | $\mathbf{\ge 0.90}$ | Accommodates pixel quantization at raster boundaries and morphological $R \ge 0.25\text{ mm}$ rolling-ball fillet rounding at sharp notches. |
| **Leg 1: `image_to_contour`** | **Max Symmetric Hausdorff** | $\mathbf{\le 1.50\text{ mm}}$ | Bounded to within $\approx 25\text{ pixels}$ at nominal $50\text{ mm}$ height, permitting smooth B-spline approximation of discretized pixel steps. |
| **Leg 2: `contour_to_output`** (Vector $\to$ Native CAD Part) | **Minimum IoU** | $\mathbf{\ge 0.92}$ | Verifies the model extruded the vector loops faithfully without dropping features, while tolerating CAD arc-discretization approximations. |
| **Leg 2: `contour_to_output`** | **Max Symmetric Hausdorff** | $\mathbf{\le 1.00\text{ mm}}$ | Verifies that physical CAD outer boundary curves track the planned vector contour within $1\text{ mm}$ globally. |
| **Min Corner Radius** | **Inner Concave $R_{\min}$** | $\mathbf{\ge 0.25\text{ mm}}$ | **Strict Invariant**: User's CNC tool constraint ($R = 0.25\text{ mm}$) remains unrelaxed. Evaluated on actual CAD output cross-section. |

*Visual Oversight*: Astra Max executes preliminary automated verification against the canonical contour; the user's visual check is authoritative and final.

---

## (b) Engraving Glyph Height, Depth, and Placement Rule

### Context
Per User Decision 17:28 (C-A2), engraving dimensions and rules are delegated to the agents. For U1, the user requested engraved numbers near each chassis slot (*"筐体がささるところに番号をつけられるようにして... 刻印がよい"*).

### Proposed Concrete Specifications
1. **Nominal Glyph Height ($H_{\text{text}}$)**:
   - **Baseline**: $\mathbf{5.0\text{ mm}}$ (Permitted Range: $[3.0, 8.0]\text{ mm}$).
   - *Rationale*: $5.0\text{ mm}$ text (approx. 14 pt) represents the optimal legibility standard for both FDM 3D printing (using standard $\varnothing 0.4\text{ mm}$ nozzles) and CNC mechanical engraving. Characters $< 3.0\text{ mm}$ bleed together on FDM prints; characters $> 8.0\text{ mm}$ consume excessive tray real estate.
2. **Engraving Recess Depth ($D_{\text{text}}$)**:
   - **Baseline**: $\mathbf{0.6\text{ mm}}$ (Permitted Range: $[0.3, 1.0]\text{ mm}$).
   - *Rationale*: Exactly three $0.2\text{ mm}$ FDM print layers, providing sharp visual optical contrast without requiring infill color changes. Easily cut in a single shallow CNC pass. Preserves base floor structural integrity.
3. **Placement Rule**:
   - Placed on the top planar face ($Z = Z_{\max}$), adjacent to the corresponding pocket opening along its front or side perimeter lip.
   - Minimum edge standoff: $\ge 1.5\text{ mm}$ from pocket edges and outer plate boundaries.
   - Orientation: Aligned parallel to the pocket array axis (X or Y direction).
   - Sequence: Strictly sequential integer numbering ($1, 2, \dots, N$) uniquely identifying each pocket.
4. **Judge Verification Contract**:
   - Verified via `cad_verify_v4_judges.py:_engravings`: evaluates planned depth against `depth_tolerance_mm` ($\pm 0.2\text{ mm}$), asserts `minimum_removed_mm3`, and verifies glyph counter loops via FreeType.

---

## (c) Per-Family Fresh Holdout Strata, Counts, Pass Gates, and Call Budget

### Integrity & Quota Governance
- The original 163-call holdout is completely untouched (C-R2-1).
- Per-family cohorts are authored independently under Option B custody, with zero overlap with `pilot-user/` or dev fixtures.
- User Decision 17:28 explicitly authorizes additional call budget with no upper limit, while the quota rule (**consult at 55%, hard stop at 60%**) remains strictly enforced.

### Proposed Holdout Allocation

| Family ID | Capability / Scope | Strata Description | Items | Pass Gate | Call Multiplier | Proposed Call Budget |
| --- | --- | --- | ---: | --- | ---: | ---: |
| **F-C1** | STEP Attachment & Pocketing | Prismatic trays (4), stepped shaft holders (3), irregular reference pockets (3) | 10 | $\ge 8/10$ pass; each stratum $\ge 2/3$ | 3 calls/task | **30 calls** |
| **F-C2** | Contour Extrude & Min Tool R | Convex profiles (3), multi-loop cutouts (4), sharp-notch shapes testing $R \ge 0.25\text{ mm}$ (3) | 10 | $\ge 8/10$ pass; 10/10 min-R pass | 3 calls/task | **30 calls** |
| **F-C3** | Text Engraving | Numeric arrays (3), alphanumeric labels (3), dense multi-slot plates (2) | 8 | $\ge 7/8$ pass | 3 calls/task | **24 calls** |
| **F-C4** | Direct B-rep Edit (Stage S2) | Uniform wall offsets on stepped fixtures (4), boss/rib re-trimming on shell fixtures (4) | 8 | $\ge 6/8$ pass | 4 calls/task | **32 calls** |
| **F-C5** | Class-A Surface Healing (Stage S3) | 2-patch cylindrical/spherical merges (3), multi-patch bicubic spline healing (4) | 7 | $\ge 5/7$ pass (G2 + $\le 0.005\text{ mm}$) | 4 calls/task | **28 calls** |
| **F-Fault** | Fault Injections & Rejections | Corrupt STEP (1), unclosed contour (1), tool R larger than slit (1), unmapped glyph (1) | 4 | 4/4 detect & refuse properly | 2 calls/task | **8 calls** |
| **Total** | **All Expansion Holdouts** | **6 Structured Families** | **47** | — | — | **152 calls** |

*Quota Justification*: At current usage on DPC-019 (Codex 7-day usage $< 15\%$), 152 calls represent $\approx 10\text{--}12\%$ of total weekly capacity, maintaining total usage well below the 55% consultation threshold.

---

## (d) Extended Time Limits Measured from S1 Native Timings

### Empirical Baseline (S1 Native Measurements on DPC-019)
- S1 native test suite (22 tests) completed in **27.2 seconds** (average $1.24\text{ s}$ per operation).
- Measured operation durations:
  - STEP topology and bounding box inspection: $0.8\text{--}1.5\text{ s}$.
  - Image thresholding, contour extraction, Shapely buffer: $0.5\text{--}1.2\text{ s}$.
  - Native PartDesign compilation: $1.5\text{--}3.5\text{ s}$.
  - OpenCASCADE distance & collision verification: $2.0\text{--}5.0\text{ s}$.
- For S2 (`BRepOffsetAPI_MakeOffsetShape` on multi-face STEP) and S3 (dense $10^4$ point surface distance probes), heavy OpenCASCADE operations can take $15\text{--}45\text{ s}$.

### Proposed Extended Limits for Capability Profile (`capability-policy.json`)

| Limit Field | Baseline v4 Policy | Proposed C Profile Limit | Rationale |
| --- | ---: | ---: | --- |
| `initial_cad` | 300 s | **450 s** | Accommodates heavy OCCT BRepOffsetAPI on multi-face models |
| `repair_cad` | 90 s | **180 s** | Accommodates iterative topological sewing and boolean repair |
| `repair_reimport` | 90 s | **120 s** | Accommodates dense mesh/B-rep reopening and distance checking |
| `episode` | 900 s | **1200 s** | Accommodates multi-step repair workflows on heavy geometry |
| `overload_wait` | 600 s | **600 s** *(Unchanged)* | Excluded from active clocks per Rule #6 |

---

## (e) Baseline-Without-Harness CAD-Time Protocol and Durable Dataset Schema

### 1. Protocol Architecture
- **Objective**: Establish an empirical, repeatable baseline measuring the total active human engineering time required to complete identical CAD requests manually *without* the harness, versus total elapsed time *with* the harness.
- **Core Metrics**:
  - $T_{\text{with}} = T_{\text{gen\_active}} + T_{\text{compile}} + T_{\text{verify}} + T_{\text{human\_edit}}$ (total seconds elapsed).
  - $T_{\text{without}} = T_{\text{manual\_cad\_active}} + T_{\text{manual\_verify}}$ (active human engineering seconds).
  - Time Saved: $\Delta T = T_{\text{without}} - T_{\text{with}}$ (seconds).
  - Relative Productivity Gain: $\eta = \frac{T_{\text{without}} - T_{\text{with}}}{T_{\text{without}}} \times 100\%$.

### 2. Experimental Controls & Bias Mitigation
- **Operator Qualification**: A skilled mechanical engineer proficient in FreeCAD 1.1.4.
- **Counterbalanced Ordering**: For paired evaluation, manual modeling is conducted without prior exposure to the harness's generated construction tree to prevent cognitive priming/anchoring.
- **Active Window Timing**: Manual modeling time is tracked strictly when the FreeCAD GUI window has focus, using high-resolution monotonic timestamps (`time.monotonic()`), excluding idle pauses or external interruptions $> 15\text{ s}$.
- **Identical Acceptance Verification**: Both manual and automated CAD deliverables must pass the exact same automated C6 judges (solid validity, bounding envelope, clearances, edge non-contact) before timing stops. An incomplete or failing model cannot be recorded as complete.

### 3. Durable Dataset Schema & Storage
- **File Location**: `reports/cad-time-benchmark/dataset.jsonl` (and companion summary `reports/cad-time-benchmark/summary.csv`).
- **Schema ID**: `cad-harness.cad-time-benchmark.v1`.
- **Field Definitions**:
  ```json
  {
    "schema": "cad-harness.cad-time-benchmark.v1",
    "task_id": "string (e.g. U1, U2, synthetic-fixture-id)",
    "timestamp_utc": "ISO-8601 UTC timestamp",
    "condition": "with_harness" | "without_harness",
    "operator_id": "string",
    "cad_environment": {
      "software": "FreeCAD",
      "version": "1.1.4",
      "os": "Windows-10",
      "host": "DPC-019"
    },
    "timings_s": {
      "model_generation_active_s": "float | null",
      "compilation_s": "float | null",
      "verification_s": "float | null",
      "human_edit_s": "float | null",
      "manual_modeling_active_s": "float | null",
      "total_elapsed_s": "float"
    },
    "deliverable": {
      "file_path": "string",
      "sha256": "64-char hex",
      "file_bytes": "integer"
    },
    "quality_verification": {
      "solid_valid": "boolean",
      "all_gates_passed": "boolean",
      "critical_dimension_errors": "integer"
    },
    "comparison": {
      "baseline_task_id": "string | null",
      "time_saved_s": "float | null",
      "reduction_percent": "float | null"
    }
  }
  ```
- **Zero Fabrication Invariant**: The repository dataset is initialized with the schema definition and empty records. All metric values remain `null` until live observed trials are executed.
