# Independent Pilot Screening: User Requests U1–U5 — Gemini

**Agent:** Gemini (`google-antigravity/gemini-3.8-flash`)  
**Source Document:** `design/cad-harness-verify-v4/pilot-user-requests.md`  
**Source Commitments:** `pilot-user/requests.md` (SHA-256 `f386afc7a3a05bb9b3e5600e912bd0f7ee7df7a3fac8ee5467c65d27d24062df`)  
**Attachments Directory:** `design/cad-harness-verify-v4/pilot-user/`  
**Evaluation Scope:** Headless FreeCAD 1.1.4 single-body PartDesign modeling on DPC-019 without range expansion (unchanged v3/v4 capabilities). Zero model generation calls, zero live CAD test executions, no git commit.

---

## 1. Measured Inspection of Attachments (Read-Only)

Attachments were inspected using FreeCAD 1.1.4 headless (`freecadcmd.exe`) strictly to measure bounding boxes and topology. Zero generation or CAD modeling was performed.

| File | SHA-256 | Size (bytes) | Bounding Box (X × Y × Z mm) | Topology |
| --- | --- | ---: | --- | --- |
| `U1.step` | `05f366a5e9a0bd7b451f063ef04ca10447b2028b09f81c734b01a6313a0cf8ae` | 2,695,956 | 53.957 × 69.768 × 17.623 | 1 Solid, 11 Shells, 1028 Faces, 2843 Edges |
| `U2.step` | `a80d43f6180be313290647e94ae31e0a7c6f71658348252f09db733318791bd9` | 808,687 | 62.732 × 115.041 × 23.558 | 0 Solids, 3 Shells, 28 Faces (all B-Spline), 76 Edges |
| `U3.step` | `3cdf4f1d3e9f3e83a7341a0d9e6f9ce2ce8e74c63d578bc27e8810a89ac6fd36` | 2,127,563 | 30.377 × 40.448 × 12.888 | 1 Solid, 1 Shell, 153 Faces, 391 Edges |
| `U4.step` | `d85327e5ce14ccc386d182f2d04b6d535fb49cd74c456bad6aa34e0be630c92a` | 7,081,133 | 112.143 × 165.635 × 140.117 | 1 Solid, 3 Shells, 1032 Faces, 2919 Edges |
| `U5` | *None* | — | — | No attachment provided |

---

## 2. Individual Candidate Screening (U1–U5)

### U1: NF13 Box Chassis Holder

#### Verbatim Request
> この筐体を長手方向が鉛直になるようにガタガタしないように直立させて、プラ箱のNF13 Boxにぴしっとおさまるようなホルダーを作って。並べ方は規則的に適当に並べて。筐体がささるところに番号をつけられるようにして。3Dプリンターで作って両面テープでNF13 boxに貼るから。

#### (a) Capability Scope Class (E3 Analysis) & Public Spec Policy
- **Scope Class**: Single-body 3D-printable holder tray with pocket cavities and embossed/engraved numbers. A prismatic base block with an array of rectangular/stepped pockets and numbers is within the native capabilities of FreeCAD PartDesign (Pad, Pocket, Linear Pattern, ShapeString/Pocket).
- **Public Spec vs. E4 Policy**:
  - The prompt asks: *"Decide whether a fetched public spec counts as an allowed attachment, or whether it is E4 (dimensions only from the user)."*
  - **Decision**: A public specification fetched from the web **cannot** be fetched at runtime by the generator, because the generator is strictly isolated (`--no-tools`, `--no-skills`, stdin `DEVNULL`).
  - Under Consensus §5 and BRIEF, all pilot dimensions and acceptance criteria must come with real-work provenance directly from the user, and nobody may invent numbers.
  - Therefore, unless the user formally provides the authoritative NF13 Box interior dimensions as a pre-registered attachment before the trial, this is **E4** (critical dimensions missing from the user). Even if the box dimensions were supplied, the user's request leaves slot capacity ("適当に並べて"), spacing, rattle clearance, and wall thickness completely unstated.
  - Furthermore, if the holder requires a conformal negative boolean of the complex 1028-face B-rep chassis `U1.step` rather than bounding-box clearance slots, executing boolean cuts of imported complex STEP solids inside FreeCAD PartDesign regularly triggers OpenCASCADE kernel crashes (out of scope for stable headless compilation).

#### (b) Evaluation (E4 / E6 / E7)
- **E6**: Not applicable (request is self-contained intake text).
- **E7**: Attachment `U1.step` exists and is readable. However, the NF13 Box specification file is missing.
- **E4 (Sufficient Exclusion)**: Critical dimensions required to judge the part are absent:
  1. NF13 Box interior boundary dimensions (length, width, maximum height).
  2. Number of chassis slots (capacity N) and grid arrangement (rows × columns).
  3. Slot clearance / tolerance around the chassis (cross section 53.96 mm × 17.62 mm when standing along the 69.77 mm Y-axis).
  4. Base plate / floor thickness for double-sided tape mounting.
- **Verdict**: **Excluded (E4)** pending user answers.

#### (c) Pass Criteria (If Clarified by User)
- **Critical Item 1**: Outer tray dimensions must fit within NF13 Box interior dimensions minus tape/clearance margin.
- **Critical Item 2**: Slot cross-section dimensions must accept upright chassis orientation (Y-axis vertical; opening width $\ge 53.96$ mm + clearance, depth $\ge 17.62$ mm + clearance).
- **Critical Item 3**: Slot count must equal user-specified N, arranged in regular rows/columns.
- **Critical Item 4**: Each slot must have an identifiable number (embossed or debossed).
- **Tolerances**: *Missing — see Questions for the User*.

#### (d) Questions for the User for U1
1. What are the exact interior dimensions (length, width, usable height in mm) of the NF13 Box?
2. Exactly how many chassis should the holder accommodate, and in what grid configuration (e.g., 2×5, 3×4)?
3. What is the allowable clearance for the chassis slot (e.g., +0.5 mm, +1.0 mm) to achieve "no rattle" without binding?
4. Is a stepped rectangular pocket based on the chassis bounding box acceptable, or is a conformal contour required?
5. What are the specifications for slot numbering (location, font size, embossing/debossing depth)?
6. What is the required bottom floor thickness for mounting with double-sided tape?

---

### U2: Curved Glass Storage Box (10 Sheets)

#### Verbatim Request
> このガラスを横に立てて並べる保管用ボックスを3Dプリンターで作るから設計して。10枚入るようにして。ガタガタしないようにして。端面が剥げやすいからガラス端面にはなにもあてないようにして

#### (a) Capability Scope Class (E3 Analysis)
- **Scope Class**: Single-body 3D-printable slotted storage box. Modeling a box with 10 parallel slots or ribs is a classic FreeCAD PartDesign construction (Base Pad + Pocket or Linear Pattern of ribs/grooves).
- **Feasibility & Boundary Constraints**:
  - `U2.step` is an open surface shell (0 solids, 28 B-spline faces, bounding box 62.73 × 115.04 × 23.56 mm). It represents a thin curved 3D glass sheet.
  - Crucial constraint: *"端面が剥げやすいからガラス端面にはなにもあてないようにして"* (glass edge faces must not touch anything because the edge coating peels easily).
  - To support 10 sheets upright on edge without touching their perimeter edge faces, the box must support the sheets along their interior face/surface with bottom and side relief recesses (undercuts/relief channels) along the outer boundary.
  - If modeled as straight or profiled slotted guides with bottom edge clearance channels, this can be constructed as a single PartDesign Body without range expansion.

#### (b) Evaluation (E4 / E6 / E7)
- **E6 / E7**: Attachment `U2.step` exists, is readable, and SHA-256 matches. No external files missing.
- **E3**: Within capability scope as a single-body slotted container.
- **E4 (Pending Clarification)**: The request provides essential qualitative functional requirements (10 sheets, edge-standing, no rattle, zero edge contact), but omits critical quantitative dimensions:
  1. Physical glass sheet thickness (since `U2.step` is an open surface model with zero solid thickness).
  2. Slot width and rattle clearance.
  3. Relief groove margin (standoff distance from glass perimeter edges).
  4. Pitch / center-to-center spacing between the 10 sheets, and maximum external box envelope.
- **Verdict**: **Eligible in Principle (E4 Pending User Clarification)**. This is the single strongest candidate for a genuine pilot task among U1–U5.

#### (c) Fixed Pass Criteria (Subject to User Clarifications)
- **Critical Item 1**: Capacity — exactly 10 distinct, parallel slots/compartments.
  - *Measurement*: Visual and feature count inspection.
  - *Tolerance*: Exactly 10 slots (integer count).
- **Critical Item 2**: Orientation — slots must hold glass sheets standing along their length/width edge.
  - *Measurement*: Slot cross-section alignment relative to `U2.step` bounding box.
- **Critical Item 3**: Edge Non-Contact (Zero Contact on Peripheral Edges) — relief groove at bottom and sides ensuring clearance along the entire glass perimeter edge.
  - *Measurement*: Headless CAD assembly collision / distance check between `U2.step` perimeter edges and box geometry.
  - *Pass threshold*: Minimum clearance distance $> 0.0$ mm (target: user-specified margin).
- **Critical Item 4**: Slot Width / Rattle Fit — slot width equals glass thickness plus specified rattle clearance.
  - *Measurement*: Caliper measurement on CAD slot opening.
  - *Tolerance*: *Missing — see Questions for the User*.
- **Critical Item 5**: Box External Envelope — box length, width, and height.
  - *Measurement*: BoundBox of generated FCStd/STEP.
  - *Tolerance*: *Missing — see Questions for the User*.

#### (d) Questions for the User for U2
1. What is the nominal physical thickness of the glass sheet (in mm)?
2. What is the target slot clearance (e.g., nominal thickness + 0.3 mm / + 0.5 mm) to satisfy "ガタガタしない" (no rattle) while permitting smooth manual insertion?
3. What is the minimum required standoff/relief distance along the glass perimeter edges (e.g., 2.0 mm clearance)?
4. What is the desired pitch between slots, and are there maximum allowable outer dimensions (L × W × H) for the storage box?
5. What wall thickness and bottom thickness should be maintained for 3D printing?
6. Are lead-in chamfers/fillets desired on slot top entries to facilitate insertion?

---

### U3: Freeform Surface G3 Stitching & Deviation Minimization

#### Verbatim Request
> このSTEPは表面がなめらかなはずなんだけど、いくつかのサーフェスに分かれてしまっている。角があるなどの明らかにサーフェス境界が必要なところではない自由曲面の意匠面のサーフェス境界をなくして、かつG3連続でなめらかに意匠面を接合してほしい。元データとの誤差は0.005mmまで絶対値で許容する。

#### (a) Capability Scope Class (E3 Analysis)
- **Scope Class**: Class-A Surface Modeling / Freeform B-Spline surface reconstruction.
- **Analysis against v3/v4 Scope**:
  - `U3.step` is a 153-face solid B-rep. The request demands removing artificial patch boundaries between adjacent B-spline surfaces and merging them with **G3 continuity** while maintaining an absolute deviation $\le 0.005$ mm from original geometry.
  - FreeCAD PartDesign capability in v3/v4 is strictly single-body constructive solid geometry (CSG): Sketch profiles with driving dimensions, Pad, Pocket, Revolution, Patterns, and standard Fillet/Chamfer.
  - FreeCAD headless possesses no automated G3 surface blending or variational surface reconstruction engine. Even dedicated Class-A CAD tools (ICEM Surf, Alias) require interactive curvature matching for G3 continuity.
  - User intake note specifically states: *"The user's notes: U3 and U4 are freeform surface work and likely out of scope."*
- **(b) Evaluation**:
  - **Excluded: E3** (outside current capability scope; requires major range expansion into Class-A surface reconstruction).

#### (c) Pass Criteria & (d) Questions for U3
- **Verdict**: Excluded under E3.
- **Question for User**: Can the user confirm that G3 freeform surface reconstruction is out of scope for the headless FreeCAD PartDesign harness?

---

### U4: Frame Freeform Underside 2mm Offset & Feature Reconnection

#### Verbatim Request
> このフレームの下面の自由曲面部分を、上面からオフセットした形に修正しつつ厚みを2mmにして。下面に接続されているフィーチャーもいい感じに接続し直して。周辺フィーチャーの外寸は変えないで、オフセットさせて自由曲面部分の肉厚だけかえたい。

#### (a) Capability Scope Class (E3 Analysis)
- **Scope Class**: Direct B-rep editing, local organic surface offsetting, and topological defeaturing/re-blending.
- **Analysis against v3/v4 Scope**:
  - `U4.step` is a massive 1032-face, 7.08 MB frame solid.
  - The request demands locally offsetting the bottom organic freeform surface to establish a uniform 2 mm wall thickness relative to the top surface, while preserving surrounding feature envelopes and reconnecting arbitrary internal bosses/ribs ("いい感じに接続し直して").
  - FreeCAD PartDesign cannot perform localized B-rep surface replacement and adaptive rib re-trimming on complex imported STEP models. The OpenCASCADE `BRepOffsetAPI_MakeOffsetShape` regularly fails on complex multi-face organic topologies with attached internal features.
  - User intake note confirms: *"U3 and U4 are freeform surface work and likely out of scope."*
- **(b) Evaluation**:
  - **Excluded: E3** (direct freeform B-rep defeaturing and local re-thickening is outside v3/v4 generative PartDesign scope).
  - **E4**: Reconnecting features "いい感じに" lacks objective mathematical definition or tolerance.

#### (c) Pass Criteria & (d) Questions for U4
- **Verdict**: Excluded under E3.
- **Question for User**: Can the user confirm that localized organic B-rep surface offsetting and rib re-attachment on imported STEP frames is out of scope?

---

### U5: Parametric Apple Logo Plate with CNC R0.25 Minimum Tool Radius

#### Verbatim Request
> アップルのロゴマークをネットから探してきて、それをCADで構築して。平板を打ち抜いたような形状で、厚みとロゴサイズをパラメトリックにしてCADモデルを構築して。あと３軸CNCで作るから最小工具Rを0.25で考えて構築して。

#### (a) Capability Scope Class (E3 Analysis)
- **Scope Class**: 2.5D profile cutout with inner fillet dress-up on a planar plate.
- **Analysis against v3/v4 Scope**:
  - Constructing a flat plate with a through-pocket profile and inner corner fillets of radius $R \ge 0.25$ mm for 3-axis CNC machining is well within FreeCAD PartDesign sketch/pad/pocket capabilities.
  - **However, runtime environment failure**: The prompt explicitly requires: *"アップルのロゴマークをネットから探してきて"* (fetch the Apple logo from the net).
  - In the v4 harness, the generator is completely isolated: no web search, no external tools, no network access. The model cannot fetch reference vector assets or images.
  - Furthermore, Consensus §5 and Addendum B mandate: *"Nobody may invent the geometry. Nothing is reconstructed or substituted."* Neither the agent nor the evaluator may invent an approximate spline profile.
- **(b) Evaluation**:
  - **Excluded: E7** (depends on external web asset/geometry that is not provided in text or attachments).
  - **Excluded: E4** (missing plate outer dimensions, nominal thickness, nominal logo size, and exact geometric arc/spline definitions).

#### (c) Pass Criteria & (d) Questions for U5
- **Verdict**: Excluded under E7 and E4.
- **Questions for User**:
  1. Can the user provide an official, dimensioned 2D DXF or STEP profile of the logo as a local attachment so web fetching is unnecessary?
  2. What are the outer dimensions (length × width) of the flat plate?
  3. What are the default/nominal values for the parametric thickness and logo size?
  4. What tolerance applies to the CNC corner radius (e.g., $R \ge 0.25$ mm with tolerance $+0.1/-0.0$ mm)?

---

## 3. Summary Screening Decision Table

| Request ID | Decision | Primary Code | Scope Classification | Key Reason |
| --- | --- | --- | --- | --- |
| **U1** | **Excluded** (Pending User Answers) | **E4, E7** | Prismatic Multi-Pocket Tray (FreeCAD PartDesign) | NF13 Box dimensions absent from user attachments; slot count, layout, and rattle tolerances missing. |
| **U2** | **Eligible in Principle** (Pending User Answers) | *(E4 pending)* | Slotted Storage Container (FreeCAD PartDesign) | Fits single-body PartDesign; requires user to provide physical glass thickness, slot clearance, and edge relief margin before trial. |
| **U3** | **Excluded** | **E3** | Class-A Freeform Surfacing (G3 Continuity) | Merging 153-face STEP B-splines with G3 continuity exceeds FreeCAD PartDesign capabilities. |
| **U4** | **Excluded** | **E3** | B-rep Organic Offset & Defeaturing | Local 2mm offsetting and boss re-attachment on 1032-face STEP frame exceeds FreeCAD CSG capabilities. |
| **U5** | **Excluded** | **E7, E4** | Parametric 2.5D Pocket Plate | Requires web fetch in an isolated environment without network; logo spline geometry and plate dimensions missing. |

**Current Qualified Count**: $N = 1$ (U2 conditionally eligible upon receiving user answers).  
If U1 is clarified with an authoritative NF13 spec and slot parameters, $N$ could become 2 ($N \le 2$).  
If user answers cannot be obtained prior to freeze, $N = 0 \implies \text{not\_run}$.

---

## 4. Consolidated Questions for the User

To enable pre-registering objective acceptance cards in `pilot-rubric.json` before execution freeze, the user's answers are required for the following:

### Questions for U2 (Primary Candidate):
1. **Glass Sheet Thickness**: What is the nominal physical thickness of the glass sheet (in mm)? (Since `U2.step` is an open surface shell with zero solid thickness).
2. **Slot Clearance / Rattle Tolerance**: What is the target slot width or clearance over the glass thickness (e.g., nominal thickness + 0.3 mm, +0.5 mm) to satisfy *"ガタガタしない"* without binding?
3. **Edge Non-Contact Standoff**: What is the required clearance/standoff distance (in mm) along the peripheral bottom and side edges of the glass so that *"ガラス端面にはなにもあてない"*?
4. **Slot Pitch & External Envelope**: What is the center-to-center pitch between the 10 glass sheets, and what are the maximum allowable overall dimensions (length, width, height) of the storage box?
5. **Wall & Floor Thickness**: What minimum wall thickness and floor thickness are required for 3D printing?

### Questions for U1 (Secondary Candidate, if pursued):
1. **NF13 Box Dimensions**: What are the authoritative interior dimensions (length, width, height in mm) of the NF13 Box?
2. **Chassis Slot Count & Grid**: How many chassis slots should be provided, and in what row × column grid?
3. **Slot Clearance**: What clearance around the chassis bounding cross-section (53.96 mm × 17.62 mm) is required to prevent rattling?
4. **Pocket Geometry**: Is a stepped rectangular pocket acceptable, or is a conformal negative boolean of the chassis required?
5. **Numbering & Base**: Where should slot numbers be positioned, and what is the desired base thickness for double-sided tape mounting?

### Scope Confirmations for U3, U4, U5:
1. Does the user confirm that **U3** (G3 surface blending on 153-face STEP) and **U4** (freeform B-rep offset and feature reconnection on 1032-face STEP) are out of scope (E3)?
2. For **U5**, can the user supply an authoritative DXF/STEP attachment and plate dimensions, or is U5 excluded due to offline tool-less constraints (E7/E4)?
