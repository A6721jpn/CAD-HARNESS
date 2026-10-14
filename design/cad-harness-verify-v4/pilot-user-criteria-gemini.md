# Pilot User Criteria & Blocker Check — Gemini

**Agent:** Gemini (`google-antigravity/gemini-3.8-flash`)  
**Context:** Intake of 5 user pilot requests (`pilot-user-requests.md`) and user clarifications of 2026-10-14 14:25 JST (`pilot-user/requests.md`).  
**Rules & Contracts:** Unchanged v3/v4 capability scope (`skills/cad-harness-v4/`), Consensus Plan §5, Decisions, Update U1 Revisions 1–3, and Addendum B.  
**Operational Invariants:** Zero live generation calls, zero live pilot runs, no git commit.

---

## 1. Re-Judgment of U5 (Raster PNG Attachment)

### Assessment
- **Status of U5**: **EXCLUDED (E3 / E7)**.
- **Is raster-to-contour inside the unchanged scope?**: **NO.**
- **Evidence & Architectural Invariants**:
  1. **Generator Sandbox**: The generator subprocess is invoked via `omp --print --mode json` with `--no-tools --no-lsp --no-pty --no-extensions --no-skills --no-rules --no-title --no-session --no-prewalk` and stdin `DEVNULL`. It possesses zero tools, no web access, and no file read capabilities. It cannot inspect binary image files.
  2. **Source Mode Contract (`contracts.md:273`)**: Allowed imports are strictly `FreeCAD, Part, Sketcher, math`. File I/O, `PIL`, `cv2`, `potrace`, `os`, and `sys` are strictly prohibited in the generated script.
  3. **FreeCAD Headless Capability Scope**: FreeCAD headless PartDesign has no built-in automatic raster autotracing capability in `Part` or `Sketcher`. Raster-to-vector contour extraction requires external image processing libraries or interactive GUI workbenches (`Image` workbench), which represents an unapproved range expansion (E3).
  4. **Fabrication Prohibition**: Addendum B and Consensus §5 explicitly mandate: *"Nobody may invent the geometry. Nothing is reconstructed or substituted."* Generating hand-approximated splines without exact mathematical definitions constitutes fabrication and fatal quality failure.
- **Conclusion**: U5 remains excluded under **E3** (raster-to-vector tracing is outside capability scope) and **E7** (vector spline geometry is missing from local attachments).

---

## 2. Blocker Check & Architectural Resolution (U1 / U2)

### The Contract Constraint
- `skills/cad-harness-v4/contracts.md:273` strictly dictates:
  > *Allowed imports: FreeCAD, Part, Sketcher, math. No file, shell, network, document lifecycle, save or probe operations.*
- `SKILL.md:12` establishes:
  > *Initial output uses the Spec contract. An optional <runtime_data> JSON object contains factual state only. Its allowed keys are target (spec or source), stage (initial or repair), observations (...), and answer (...).*

### Subquestion A: How can U1/U2 STEP attachments reach the generator or checker without scope/capability change?
1. **At the Generator Boundary**:
   - The generator and its generated Python `build(doc)` script **cannot** read STEP files from disk (prohibited by `contracts.md:273` no-file-ops rule).
   - Therefore, the generated script cannot perform runtime boolean cuts or imports of `U1.step` or `U2.step`.
   - Instead, the generated model must construct the holder/box parametrically using native FreeCAD PartDesign CSG (Sketch + Pad + Pocket + LinearPattern).
2. **At the Checker Boundary**:
   - The checker process runs in the host environment (DPC-019), completely outside the generator's restricted sandbox.
   - The checker **can** read `U1.step` and `U2.step` via `Part.read()`, import the generated STEP deliverable, position the parts in the generated slots, and execute automated distance, collision, play, and clearance measurements.

### Subquestion B: Are attachment-derived measured facts (bounding boxes) permitted runtime data?
- **Decision**: **YES, when supplied as factual data in `runtime_data` (`answer` or `observations`).**
- **Evidence**:
  - `SKILL.md:12` explicitly defines `<runtime_data>` to contain *"factual state only"*, including `"answer"` (genuine user answers to clarification) and `"observations"` (measured factual states).
  - Addendum B explicitly provides that: *"the request, context and attachments are passed as typed runtime data."*
  - Supplying the deterministic, headless pre-measured bounding box dimensions ($53.96 \times 69.77 \times 17.62\text{ mm}$ for U1; $62.73 \times 115.04 \times 23.56\text{ mm}$ for U2) provides the objective factual dimensions needed to construct clearance pockets without forcing the model to guess or fabricate dimensions.

### Subquestion C: Is engraved numbering (U1) representable without a font file?
- **Analysis**:
  - Standard FreeCAD 3D text uses `Draft.make_shapestring()`, which requires an external `.ttf` font path (a file operation) and imports `Draft` (which is not in `FreeCAD, Part, Sketcher, math`). This is barred by `contracts.md:273`.
  - However, engraved numbering is representable within pure Sketcher/PartDesign in two compliant ways:
    1. **Native Sketcher Numerals**: Recessed V-grooves or rectangular strokes sketched directly on the top face and pocketed $0.5\text{ mm}$ deep.
    2. **Harness Font Provision / Relaxation**: If simple groove identification is accepted, or if the harness runner provides standard font curves via permitted imports.
  - To maintain strict contract compliance, the pass criteria for U1 should verify identifiable engraved/debossed slot index markings (recessed depth $0.3\text{--}1.0\text{ mm}$) without mandating a proprietary TrueType font file.

### Subquestion D: Eligibility Verdict for U1 and U2
- **U1 Verdict**: **ELIGIBLE**.
  - *Evidence*: Constructing a rectangular pocket tray that fits within the confirmed NF-13CR box interior ($245 \times 365 \times 140\text{ mm}$) with vertical upright slots ($53.96 \times 17.62\text{ mm}$ opening + play $\le 0.5\text{ mm}$) and flat bottom for tape is 100% native FreeCAD PartDesign CSG. It requires no file I/O in `build(doc)`.
- **U2 Verdict**: **ELIGIBLE**.
  - *Evidence*: Constructing a slotted storage box for 10 glass pieces ($1.3\text{ mm}$ thick, $115.04 \times 62.73\text{ mm}$ sheet) with face contact on the convex side and dedicated perimeter relief trenches ($>0\text{ mm}$ clearance on the $1.3\text{ mm}$ edge band) is fully achievable as a single PartDesign Body via Sketch, Pad, Pocket, and LinearPattern. Checker verifies non-contact offline via OpenCASCADE distance API.

---

## 3. Fixed Pass Criteria (Using Only User-Given Values)

### A. U1: NF-13CR Chassis Holder Tray

#### User-Given Inputs
- **Box**: JEJ Astage NF-13CR, catalog interior $245 \times 365 \times 140\text{ mm}$ (user-confirmed).
- **Orientation**: Chassis longest outer dimension (Y axis, $69.77\text{ mm}$) stands vertical (Z direction).
- **Chassis Cross-Section**: $X = 53.96\text{ mm}$, $Z = 17.62\text{ mm}$ in the horizontal plane.
- **Slot Play**: $\le 0.5\text{ mm}$ (ガタは0.5mm以下).
- **Mounting Tape Thickness**: $0.5\text{ mm}$ (flat planar bottom).
- **Slot Count**: User explicitly stated: *"並べる数は指定なし"* (unspecified by user; generator chooses regular integer grid $N \ge 2$).
- **Numbering**: Engraved numbers per slot (*"刻印がよい"*).

#### Fixed Criteria, Measurement Methods & Tolerances
1. **Outer Envelope Fit (NF-13CR Box)**:
   - *Requirement*: Holder outer $X \le 364.0\text{ mm}$, outer $Y \le 244.0\text{ mm}$, total height $H \le 69.5\text{ mm}$ (allowing $69.77\text{ mm}$ chassis + $0.5\text{ mm}$ tape to clear the $140.0\text{ mm}$ box height).
   - *Measurement Method*: `Part.read(deliverable).BoundBox`.
   - *Tolerance*: Length $\in [100.0, 364.0]\text{ mm}$, Width $\in [100.0, 244.0]\text{ mm}$, Height $\in [20.0, 69.5]\text{ mm}$. Exceeding $365.0 \times 245.0\text{ mm}$ is a FATAL FAIL.
2. **Upright Chassis Slot Dimensions & Play**:
   - *Requirement*: Slot cavity cross-section must receive chassis $53.96 \times 17.62\text{ mm}$ with horizontal play $\le 0.5\text{ mm}$.
   - *Slot Opening X*: Nominal $53.96\text{ mm} + \text{play} \implies [54.06, 54.46]\text{ mm}$.
   - *Slot Opening Y*: Nominal $17.62\text{ mm} + \text{play} \implies [17.72, 18.12]\text{ mm}$.
   - *Measurement Method*: Automated distance between parallel pocket faces in deliverable Body.
   - *Tolerance*: Play $\in [0.10, 0.50]\text{ mm}$. Play $> 0.50\text{ mm}$ or slot $< 53.96\text{ mm}$ is a FATAL FAIL.
3. **Pocket Array Regularity & Structure**:
   - *Requirement*: Pockets arranged in a regular row $\times$ column rectangular pattern ($N \ge 2$).
   - *Partition Wall Thickness*: Minimum inter-slot wall $\ge 2.0\text{ mm}$.
   - *Measurement Method*: Minimum distance between adjacent pocket internal faces.
4. **Engraved Identification Markings**:
   - *Requirement*: Distinct engraved/recessed number markings adjacent to each slot.
   - *Measurement Method*: Feature inspection of top-face pocket cuts.
   - *Tolerance*: Recess depth $\in [0.3, 1.0]\text{ mm}$.
5. **Double-Sided Tape Base**:
   - *Requirement*: Continuous planar bottom face at $Z = 0$ with base thickness $\ge 1.5\text{ mm}$ under pockets.
   - *Measurement*: Planarity check of bottom face and minimum floor thickness.

#### Remaining Question for the User for U1
- *Question*: Are simple sketch-based V-groove/stroke numerals acceptable for engraved numbers to adhere to the strict no-external-font-file sandbox constraint?

#### Astra Max Judge Rubric for U1
- **R1 (Enclosure Fit)**: Clear visual and dimensioned fit inside the $245 \times 365\text{ mm}$ tray footprint without interference.
- **R2 (Orientation & Array)**: Clean upright vertical orientation of slots arranged in an orderly, space-efficient grid.
- **R3 (Engraved Numbering)**: Legible, neatly positioned engraved slot numbers adjacent to each opening.
- **R4 (3D Printability)**: Robust solid geometry free of non-manifold edges, self-intersections, or razor-thin walls ($< 1.5\text{ mm}$).

---

### B. U2: Curved Glass Slotted Storage Box

#### User-Given Inputs
- **Glass Thickness**: Nominal $1.3\text{ mm}$ (user-confirmed).
- **Capacity**: Exactly 10 pieces (*"10枚入るようにして"*).
- **Orientation**: Standing on edge (*"横に立てて並べる"*).
- **Perimeter Edge Face Non-Contact**: *"端面は厚みをつけた1.3mmの外周帯状の面であたってさえなければOK"* (the $1.3\text{ mm}$ perimeter band face must have ZERO contact).
- **Face Support Distribution**: *"ガラスは凸面側は当ててよいが、凹面は最低限の接触にしてほしい"* (convex face may have broad contact; concave face contact must be minimal).
- **Rattle**: *"ガタガタしないようにして"* (no rattle).

#### Fixed Criteria, Measurement Methods & Tolerances
1. **Slot Capacity (10 Pieces)**:
   - *Requirement*: Exactly 10 parallel slots/compartments.
   - *Measurement Method*: Count of distinct slotted guide channels.
   - *Tolerance*: Strict integer count $= 10$.
2. **Glass Slot Guide Width & Play**:
   - *Requirement*: Accommodate $1.3\text{ mm}$ glass sheet without binding or excessive play.
   - *Slot Width*: Target $1.3\text{ mm} + 0.3\text{ mm} \implies 1.6\text{ mm}$.
   - *Measurement Method*: Caliper distance between guide support faces.
   - *Tolerance*: Slot width $\in [1.45, 1.80]\text{ mm}$ (play $\in [0.15, 0.50]\text{ mm}$). Slot width $< 1.30\text{ mm}$ is a FATAL FAIL.
3. **Perimeter Edge Band Non-Contact (Zero Contact Invariant)**:
   - *Requirement*: A relief groove/channel along the bottom and side guide tracks so that the $1.3\text{ mm}$-wide perimeter edge band of `U2.step` hangs in free air with zero physical contact.
   - *Measurement Method*: Headless checker imports deliverable STEP and `U2.step`, positions `U2.step` seated in slot against convex support face, and evaluates minimum Euclidean distance between the 1.3 mm perimeter edge band of `U2.step` and all box surfaces.
   - *Pass Threshold*: Minimum clearance $> 0.0\text{ mm}$ everywhere on perimeter band. Target standoff $\ge 0.5\text{ mm}$. Any contact (distance $= 0.0\text{ mm}$) on the edge band is a FATAL FAIL.
4. **Asymmetric Face Contact**:
   - *Requirement*: Slot guide profile supports glass along its convex face, while concave guide profile features localized/minimal contact.
   - *Measurement Method*: Visual cross-section and contact area ratio (concave support area $\le 0.3 \times$ convex support area).
5. **Structural Integrity for 3D Printing**:
   - *Requirement*: Minimum inter-slot partition wall $\ge 1.5\text{ mm}$; minimum outer wall and floor thickness $\ge 2.0\text{ mm}$.
   - *Measurement Method*: Caliper wall thickness check.

#### Remaining Question for the User for U2
- *Question*: What is the preferred overall envelope limit (maximum length, width, height) to match your 3D printer bed (e.g., $256 \times 256\text{ mm}$)?

#### Astra Max Judge Rubric for U2
- **R1 (Slot Count & Spacing)**: Exactly 10 parallel, uniformly spaced vertical slots.
- **R2 (Perimeter Edge Relief)**: Clear, observable relief trench along the bottom/sides preventing perimeter edge contact.
- **R3 (Convex/Concave Support Asymmetry)**: Thoughtful guide design cradling the convex face while keeping concave contact minimal.
- **R4 (3D Print Feasibility)**: Self-supporting, clean single-body PartDesign geometry ready for slicing.

---

## 4. Consensus Section 5 Quality Gates Retention

The pilot trial for eligible requests (U1, U2) strictly adheres to the pre-frozen Consensus §5 rules:
1. **Pre-Registered Rubric**: The criteria and tolerances defined above are committed to `pilot-rubric.json` before execution freeze.
2. **Mandatory Human Adoption**: Task success requires verified human adoption with no edits or minor edits completed within $\le 300$ elapsed seconds (including headless re-verification).
3. **Fatal First-or-Later Handover Rule**: Any critical dimension error (e.g., U1 slot $< 53.96\text{ mm}$ or play $> 0.5\text{ mm}$; U2 slot $< 1.3\text{ mm}$ or perimeter edge collision) or fabrication in the proposed artifact irreversibly results in immediate task and pilot FAIL.
4. **Judge Hierarchy**: Astra Max (`openai-codex/gpt-6-astra:max`) scores first; the user's visual double-check is authoritative and overrides.
5. **Pilot Pass Threshold**: Pilot PASS requires at least $\lceil 0.7 \times N \rceil$ successful tasks (for $N = 2$, pass line is $\lceil 1.4 \rceil = 2 / 2$).
