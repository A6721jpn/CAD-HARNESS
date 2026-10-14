# U5 Default Parameters Proposal & Technical Rationale — Gemini

**Agent:** Gemini (`google-antigravity/gemini-3.8-flash`)  
**Document:** `design/cad-harness-verify-v4/u5-defaults-gemini.md`  
**Authorization:** User Decision 2026-10-14 14:57 JST (`PLAN-V4-ADDENDUM-C.md` Section C-A, Q2 delegation).  
**Constraint:** Established strictly without opening or deriving from `pilot-user/` attachments. These are agent-proposed defaults for pre-registration in `pilot-rubric.json` before freeze, labeled as agent-chosen defaults per C-A Q2.

---

## 1. Summary of Proposed U5 Defaults

| Parameter | Symbol | Proposed Baseline Value | Allowable Parametric Range | Role |
| --- | --- | ---: | --- | --- |
| **Plate Length (X)** | $L_{\text{plate}}$ | **$100.0\text{ mm}$** | $[60.0, 300.0]\text{ mm}$ | Outer carrier plate boundary |
| **Plate Width (Y)** | $W_{\text{plate}}$ | **$100.0\text{ mm}$** | $[60.0, 300.0]\text{ mm}$ | Outer carrier plate boundary |
| **Plate Thickness (Z)** | $t_{\text{plate}}$ | **$3.0\text{ mm}$** | $[1.0, 10.0]\text{ mm}$ | Plate stock thickness / through-cut depth |
| **Logo Height (Scale)** | $H_{\text{logo}}$ | **$50.0\text{ mm}$** | $[20.0, 80.0]\text{ mm}$ | Total bounding height (leaf top to body base) |
| **Logo Width (Derived)** | $W_{\text{logo}}$ | $\approx 41.5\text{ mm}$ | Proportional to $H_{\text{logo}}$ | Aspect-ratio locked ($\approx 0.83 \times H_{\text{logo}}$) |
| **Logo Placement** | $(X_0, Y_0)$ | **$(0.0, 0.0)$ (Centered)** | Plate center | Symmetrical margins |
| **Minimum Edge Margin**| $M_{\min}$ | **$25.0\text{ mm}$** (Y), **$29.2\text{ mm}$** (X) | $\ge 10.0\text{ mm}$ | Clearance from plate perimeter |
| **Min CNC Tool Radius**| $R_{\min}$ | **$0.25\text{ mm}$** | Fixed constraint | $\varnothing 0.50\text{ mm}$ endmill inner concave corner limit |
| **Through-Cut Mode** | — | **Through pocket** | Through / blind | Punched flat plate ("平板を打ち抜いたような形状") |

---

## 2. Technical Rationale for Proposed Values

### A. Plate Outline: $100.0\text{ mm} \times 100.0\text{ mm}$ Square
- **CNC Benchmarking Standard**: A $100 \times 100\text{ mm}$ square plate is a globally standardized benchmark specimen size for 3-axis CNC milling test coupons.
- **Fixturing & Clamping**: Fits standard 4-inch ($100\text{ mm}$) precision machine vises without requiring custom soft jaws or fixture plates.
- **Stock Availability**: Direct match for readily available pre-cut flat bar stock (e.g. $100\text{ mm}$ wide extruded aluminum 6061-T6 or brass sheet).
- **Proportional Geometry**: Provides a clean 1:1 square canvas framing the vertical silhouette of the logo symmetrically.

### B. Plate Thickness: $3.0\text{ mm}$
- **Micro-Tool Aspect Ratio ($L/D$) Limit**:
  - The request mandates a minimum tool radius of $R_{\min} = 0.25\text{ mm}$, dictating a tool diameter of $D = 2 \times R_{\min} = 0.50\text{ mm}$.
  - Micro-endmills with $D = 0.50\text{ mm}$ typically have effective cutting lengths (flute length) of $1.5\text{--}3.0\text{ mm}$ ($3\times$ to $6\times$ diameter).
  - Exceeding a depth-to-diameter ratio of $6:1$ ($> 3.0\text{ mm}$ depth for a $\varnothing 0.5\text{ mm}$ cutter) causes severe tool deflection, chatter, and micro-tool breakage in 3-axis CNC machining.
  - A thickness of $3.0\text{ mm}$ represents the upper physical feasibility limit for robust 3-axis CNC machining with an $R0.25\text{ mm}$ tool in a single continuous through-pocket setup.
- **Sheet Stock Standard**: $3.0\text{ mm}$ is an industry-standard nominal thickness for sheet metal, aluminum plates, and acrylic panels.

### C. Logo Size: Bounding Height $H_{\text{logo}} = 50.0\text{ mm}$
- **Definition of Size**: Logo size is formally defined as the **total vertical bounding extent $H_{\text{logo}}$** spanning from the lowest point of the apple body lobes to the highest tip of the leaf.
- **Proportions**:
  - The canonical silhouette has a width-to-height ratio of approximately $W/H \approx 0.83$.
  - At $H_{\text{logo}} = 50.0\text{ mm}$, the width is $W_{\text{logo}} \approx 41.5\text{ mm}$.
  - This occupies exactly $50\%$ of the plate's vertical span and $41.5\%$ of the plate's horizontal span.
- **Visual & Structural Balance**: Leaves ample solid material surrounding the cutout to prevent warping or thermal distortion during machining, while presenting clear, legible feature geometry.

### D. Logo Placement & Margins
- **Centered Placement**: The center of the logo's bounding box coincides with the plate origin $(X=0, Y=0)$.
- **Margin Clearance**:
  - Vertical margin (top/bottom): $\frac{100.0 - 50.0}{2} = 25.0\text{ mm}$.
  - Horizontal margin (left/right): $\frac{100.0 - 41.5}{2} \approx 29.25\text{ mm}$.
- **Vise Clamping Clearance**: A perimeter solid margin of $\ge 25\text{ mm}$ allows clamping plate edges in a CNC vise with up to $10\text{ mm}$ step jaws without interfering with the tool path or cutout profile.

### E. Consistency with 3-Axis CNC Min Tool Radius ($R_{\min} = 0.25\text{ mm}$)
- **Internal Concave Vertices**:
  - In 3-axis vertical CNC milling, concave inside corners cannot have a radius smaller than the cutting tool radius ($R_{\min} = 0.25\text{ mm}$).
  - All internal sharp junctions (e.g., the top cleft of the apple, the notch between leaf and apple, and the bottom center indentation) must feature fillet arcs with $R \ge 0.25\text{ mm}$.
  - In the custodian pre-freeze S1 pipeline (C-R1-3 / C-R2-2), morphological rolling-ball buffering with radius $0.25\text{ mm}$ ensures the canonical contour natively satisfies $R \ge 0.25\text{ mm}$.
- **Inter-Feature Gap Clearance**:
  - At $H_{\text{logo}} = 50.0\text{ mm}$, the physical gap separating the leaf from the apple body is approximately $2.5\text{--}3.0\text{ mm}$.
  - Since the tool diameter is $D = 0.50\text{ mm}$, the cutter can pass completely through the gap ($2.5\text{ mm} \gg 0.50\text{ mm}$) with multiple clean finish passes.

---

## 3. Parametric Model Interface Specification

To satisfy the user requirement *"厚みとロゴサイズをパラメトリックにしてCADモデルを構築して"* (construct the CAD model with parametric thickness and logo size), the deliverable must fulfill the following contract:

1. **Exposed Parameters**:
   - The generated FreeCAD document must expose driving parameters either via a `Spreadsheet` object or explicit PartDesign Body properties:
     - `PlateLength` (default `100.0 mm`)
     - `PlateWidth` (default `100.0 mm`)
     - `PlateThickness` (default `3.0 mm`)
     - `LogoHeight` (default `50.0 mm`)
2. **Dynamic Regeneration Invariant**:
   - Modifying `PlateThickness` within $[1.0, 6.0]\text{ mm}$ or `LogoHeight` within $[25.0, 75.0]\text{ mm}$ must regenerate a clean, manifold solid without topological naming errors, inverted normals, or self-intersections.
3. **Punched-Plate Construction**:
   - Constructed as a single PartDesign Body:
     - Base Pad: $100.0 \times 100.0 \times 3.0\text{ mm}$.
     - Pocket: Through-all cut matching the scaled vector loops of the logo.

---

## 4. Judging & Pre-Registration Rubric for U5

Under the delegated defaults, Astra Max and the automated judges evaluate U5 as follows:

| Metric | Verification Method | Pass Threshold | Severity |
| --- | --- | --- | --- |
| **Solid Validity** | `shape.isValid()` & `len(shape.Solids) == 1` | True, closed single solid | **Fatal Fail** |
| **Plate Dimensions** | Measured BoundBox outer extents | $100.0 \times 100.0 \times 3.0\text{ mm} \pm 0.2\text{ mm}$ | **Fatal Fail** |
| **Logo Height** | Vertical extent of through-pocket feature | $50.0\text{ mm} \pm 0.5\text{ mm}$ | **Fatal Fail** |
| **Min Corner Radius** | Curvature probe along all inner concave pocket edges | $R \ge 0.245\text{ mm}$ | **Fatal Fail** |
| **Through-Cut Check** | Ray test through logo interior | Ray passes through ($Z$ through-cut) | **Fatal Fail** |
| **Parametric Test** | Regenerate with $t=5.0\text{ mm}$, $H=60.0\text{ mm}$ | Solid remains valid, dimensions update | Critical |
| **Astra Max Visual** | Visual check against canonical silhouette | Proportions, leaf orientation, bite-out placement | Subject to User Override |
