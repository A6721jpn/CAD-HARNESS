# S1 Implementation & Review Plan — Gemini

**Agent:** Gemini (`google-antigravity/gemini-3.8-flash`)  
**Target:** Stage S1 Capability Implementation (C1 STEP Import + Facts, C2 Image $\to$ Contour CLI + Min-R, C3 Text Engraving, S1 Automated Judges)  
**File Location:** `design/cad-harness-verify-v4/s1-plan-gemini.md`  
**Invariants:**
- Zero inspection of or derivation from `pilot-user/` attachments (`U1.step`–`U5.step`, `U5_logo.png`). All development and verification use independent synthetic fixtures only.
- `C:\dev\v4-holdout-private` remains unread and untouched.
- Zero live model generation calls, no live trial runs, no git commit.

---

## 1. Architectural Scope & Target Capabilities for Stage S1

Stage S1 builds the foundational 2.5D, attachment-handling, and engraving capabilities needed for real-world user requests (targeting U5, U1, and U2):
1. **C1: STEP Attachment Ingestion & Geometric Facts (`measured_facts`)**:
   - Host-side deterministic extraction of bounding boxes, face/edge counts, solid counts, centers of mass, and principal dimensions from user-supplied STEP attachments via FreeCAD `Part.read()`.
   - Factual injection into `<runtime_data>` so the generator knows exact part boundaries without violating the sandbox or needing file I/O.
2. **C2: Image-to-Contour CLI Pipeline + Contour-Extrude Family + Min Tool R Enforcement**:
   - Deterministic CLI command (`image-to-contour`) that reads raster images (Pillow), binarizes via Otsu thresholding, extracts closed vector loops, and applies morphological tool radius buffering ($R \ge R_{\min}$) via Shapely.
   - Outputs a cryptographically bound `contour.json` in the pre-freeze custodian bundle step.
   - Introduces the new declarative `contour_extrude` Spec family in `contracts.md`.
3. **C3: Text Engraving Pipeline**:
   - Standardized text-to-wire generation using FreeCAD `Draft.make_shapestring` with locked Windows system font (`C:\Windows\Fonts\arial.ttf`) or pure Sketcher stroke generation.
   - Emits 2D wire loops into `<runtime_data>` or permits standard PartDesign top-face pocket debossing ($0.3\text{--}1.0\text{ mm}$).
4. **S1 Automated Judges (C6 for S1)**:
   - Automated evaluation of solid validity, 2D raster IoU ($\ge 0.95$), 2D Hausdorff distance ($\le 1.0\text{ mm}$), minimum corner radius ($R \ge R_{\min} - 0.005\text{ mm}$), and bounding envelope / slot clearance.

---

## 2. Concrete Files to Create / Modify

### A. New Tooling Modules
1. **`tools/cad_verify_v4_step.py`**:
   - *Role*: Deterministic inspection of STEP files and extraction of `cad-harness.step-facts.v4`.
   - *Functions*:
     - `extract_step_facts(step_path) -> dict`: Computes BoundBox, solid/shell/face/edge counts, planarity of faces, principal axis extents.
     - `verify_step_attachment(path, expected_sha256) -> bool`.
   - *Dependencies*: `Part` (FreeCAD 1.1.4 OCCT), `cad_verify_v4_ledger`.
2. **`tools/cad_verify_v4_contour.py`**:
   - *Role*: Deterministic raster processing, contour tracing, and min-R buffering.
   - *Functions*:
     - `trace_raster_contour(image_path, min_r=0.25, target_bounds=None, threshold=None) -> dict`: Reads PNG/JPG via `PIL.Image`, binarizes, traces external/internal loops, applies `shapely.geometry.Polygon.buffer` for $R \ge R_{\min}$, and writes `cad-harness.contour.v4`.
     - `verify_contour_json(contour_json_path) -> bool`.
   - *Dependencies*: `PIL`, `numpy`, `scipy.ndimage`, `shapely.geometry`.
3. **`tools/cad_verify_v4_text.py`**:
   - *Role*: Deterministic text-to-wire generation for 3D engraving without arbitrary file I/O in generated scripts.
   - *Functions*:
     - `text_to_wires(text_string, font_size=5.0, font_path="C:\\Windows\\Fonts\\arial.ttf") -> list`: Emits 2D closed wire coordinates for requested numbers/strings.
     - `verify_font_file(font_path) -> dict`.
   - *Dependencies*: `FreeCAD`, `Draft`, `Part`.
4. **`tools/cad_verify_v4_judges_s1.py`**:
   - *Role*: Automated quantitative verification metrics for Stage S1 outputs.
   - *Functions*:
     - `judge_solid_validity(shape) -> dict`: Evaluates `shape.isValid()`, closed manifold check, volume $> 0$, single solid.
     - `judge_contour_iou(cad_shape, source_image_path, resolution_dpi=100) -> dict`: Renders top-down projection, calculates $\text{IoU} = \frac{|A \cap B|}{|A \cup B|}$ and Hausdorff distance.
     - `judge_min_radius(cad_shape, min_r=0.25) -> dict`: Probes 2D cross-section inner concave vertices for curvature radius $R \ge R_{\min}$.
     - `judge_bounding_envelope(cad_shape, max_envelope, clearances) -> dict`: Evaluates outer fit and internal slot play.

### B. Core Harness File Updates
1. **`tools/eval_verify_v4.py`**:
   - Add CLI subcommands:
     - `step-facts --step <file.step> --out <facts.json>`
     - `image-to-contour --image <file.png> --min-r <float> --out <contour.json>`
     - `text-wires --text <str> --out <wires.json>`
   - Extend `pilot-bundle` to automatically run `step-facts` and `image-to-contour` when copying attachments into the immutable bundle.
2. **`skills/cad-harness-v4/contracts.md`**:
   - Add the declarative `contour_extrude` Spec family:
     ```json
     {
       "family": "contour_extrude",
       "contour_file": "contour.json",
       "thickness": 3.0,
       "base_plate": {"length": 100.0, "width": 100.0, "thickness": 3.0},
       "pocket_mode": "through"
     }
     ```
   - Update `Source` mode contract (`contracts.md:273`):
     - Maintain strict ban on arbitrary file, shell, and network operations.
     - Authorize consuming pre-parsed vector loops and font wires passed via `<runtime_data>`.
3. **`skills/cad-harness-v4/SKILL.md`**:
   - Formally document the schema for `<runtime_data>` when handling S1 tasks:
     - `"measured_facts"`: bounding dimensions and orientation of user STEP attachments.
     - `"contour"`: closed 2D loops and scale parameters for 2.5D contour extrusion.
     - `"engraving"`: target numbering and font wire definitions.
4. **`design/cad-harness-verify-v4/policy.json`**:
   - Register supported S1 families: `rect_prism`, `rect_stack`, `stepped_shaft`, `contour_extrude`.

---

## 3. Concrete Unit Test Suites to Create

All unit tests will execute purely offline using **independently authored synthetic fixtures** located in `tests/fixtures/synthetic/` (never touching `pilot-user/`):

1. **`tools/test_verify_v4_step.py` (C1 Verification)**:
   - Test 1: `test_step_facts_prismatic`: Ingests synthetic rectangular block STEP; asserts exact BoundBox and face count ($6$).
   - Test 2: `test_step_facts_complex`: Ingests synthetic stepped shaft STEP; asserts correct solid count ($1$) and principal axis alignment.
   - Test 3: `test_step_corrupted`: Ingests truncated STEP; asserts deterministic error handling without crashing.
2. **`tools/test_verify_v4_contour.py` (C2 Verification)**:
   - Test 1: `test_binarize_otsu`: Verifies contrast separation on synthetic multi-tone image.
   - Test 2: `test_contour_tracing_star`: Traces a synthetic sharp 5-point star; verifies loop closure and vertex ordering.
   - Test 3: `test_min_r_buffering`: Tests morphological roll-ball on star with sharp inner corners ($R=0$); asserts all inner concave radii satisfy $R \ge 0.25\text{ mm}$.
   - Test 4: `test_contour_json_hash_binding`: Verifies SHA-256 reproducibility of output vector JSON.
3. **`tools/test_verify_v4_text.py` (C3 Verification)**:
   - Test 1: `test_font_file_presence`: Verifies presence and readability of Windows font `arial.ttf`.
   - Test 2: `test_text_to_wires_digits`: Generates wires for `"0123456789"`; asserts valid closed Part Wires.
   - Test 3: `test_engraving_pocket_compilation`: Compiles single-body PartDesign block with debossed numerals; asserts pocket depth $\in [0.3, 1.0]\text{ mm}$.
4. **`tools/test_verify_v4_judges_s1.py` (S1 Judges Verification)**:
   - Test 1: `test_judge_solid_valid`: Validates manifold solid passes; non-manifold shell fails.
   - Test 2: `test_judge_iou_synthetic`: Evaluates IoU of CAD extrusion against original synthetic silhouette ($\ge 0.95$ PASS; offset mismatch FAIL).
   - Test 3: `test_judge_hausdorff`: Asserts boundary Hausdorff distance $\le 1.0\text{ mm}$ on passing part.
   - Test 4: `test_judge_min_r_probe`: Probes inner corner; flags failure if radius $< 0.25\text{ mm}$.
   - Test 5: `test_judge_box_clearance`: Verifies clearance detection on synthetic chassis tray.
5. **Integrated Test Suite**:
   ```bash
   python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live tools.test_verify_v4_step tools.test_verify_v4_contour tools.test_verify_v4_text tools.test_verify_v4_judges_s1
   ```

---

## 4. Synthetic Development Fixtures (Independent Creation)

To maintain absolute experimental hygiene and prevent data leakage:
- **`tests/fixtures/synthetic/syn_box.step`**: Simple $50 \times 70 \times 20\text{ mm}$ box with chamfers.
- **`tests/fixtures/synthetic/syn_open_shell.step`**: Open curved B-spline shell with zero thickness.
- **`tests/fixtures/synthetic/syn_sharp_star.png`**: $500 \times 500$ 1-bit PNG of a geometric star with zero-radius inner notches.
- **`tests/fixtures/synthetic/syn_logo_circle.png`**: $500 \times 500$ circle with an off-center circular cutout.

---

## 5. Review Acceptance Criteria for Stage S1

Gemini will review the Stage S1 implementation against the following strict gates:
1. **Zero Pilot Exposure**: Codebase contains zero hardcoded numbers, heuristics, or paths referencing `pilot-user/` or `U1`–`U5`.
2. **Deterministic CLI Execution**: `step-facts`, `image-to-contour`, and `text-wires` run purely offline without network, producing byte-identical outputs across repeated runs on identical inputs.
3. **No File I/O in Generator Script**: Generated `build(doc)` functions import only allowed modules and execute zero file reads or system calls.
4. **100% Test Pass**: All new test suites pass deterministically in $\le 10$ seconds.
5. **No Regressions**: Historical v3 tests (29 tests) and Phase 1–3 tests (63 tests) continue to pass without deviation.
