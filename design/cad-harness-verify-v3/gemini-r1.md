# CAD-HARNESS VERIFY v3 — Gemini R1 Proposal

Reference: [`design/cad-harness-verify-v3/BRIEF.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/BRIEF.md), [`design/cad-harness-verify-v2/RESULTS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/RESULTS.md).

## 1. Editability Semantics: Equivalent Driving Representations
- **Root Cause Resolution**: In v2, the model drove the user-stated radial depth $d=3$, while gold strictly required derived groove bottom diameter $D=34$. In CAD PartDesign, a cylindrical cut is legitimately parameterized by radial depth ($d$) or bottom diameter/radius ($D_{inner} = D_{outer} - 2d$).
- **Dual Representation Contract**:
  - Gold authoring discipline: `key_dimensions_mm` must explicitly list the parameters directly stated in the user prompt (e.g., depth 3, width 8, outer diameter 40, length 48, bore 10).
  - For standard derived feature relations, gold specifies an equivalence set: `{"groove_depth_or_dia": [3.0, 34.0, 17.0]}`. A driving dimension on the reached feature sketch matching either the direct stated depth or the derived inner diameter/radius satisfies the key dimension gate.
  - Zero numeric soup: The dimension must be an active driving constraint on geometries in the reachability graph from consumed native Tip features. Unconnected decoys, reference/inactive dimensions, or arbitrary unlinked numbers remain strictly rejected.
- **Offline Calibration**: Calibrate strictly on dev cases (DV1–DV6) and offline decoys (unconnected depth lines, inactive diameter dimensions) in FreeCAD 1.1.4 before freezing.

## 2. Unsupported-Family Routing & Diagnostic Repair Feedback
- **Prompt Routing Contract**:
  - The developer contract will clarify that shapes outside the 4 standard schema families (`rect_prism`, `stepped_shaft`, `turned_flange`, `box_pocket_fillet`) must immediately return `{"unsupported": [...]}` on Turn 1 without attempting to invent non-existent families (preventing wasted parse budget on hallucinations like `stepped_shaft` for grooved rollers).
- **Enriched Diagnostic Repair Feedback**:
  - When CAD attempt 1 fails editability, pass explicit failed gate diagnostics in `previous` feedback: e.g. `{"failed_predicate": "editability", "missing_driving_dimension_mm": [34.0, 3.0], "detail": "groove requires direct driving radial depth or inner diameter constraint"}`.
  - This provides actionable semantic direction to the model during its guaranteed $R=1$ call without leaking full gold models or code.

## 3. Failure-Phase Diagnostics & Provenance
- **Disaggregate `verification` Failure Class**:
  - Replace monolithic `verification` failure label with two distinct phases:
    1. `native_editability_fail`: script exited 0 and solid geometry passed, but failed native sketch links, driving dimensions, or clean recompute. Reimport is recorded as `reimport_status: "not_reached"`.
    2. `reimport_verification_fail`: editability passed and STEP/FCStd were exported, but independent reimport verification failed bbox, volume, or mesh checks.
- **Context Provenance**: Save exact source and repair prompts/contexts alongside their SHA256 digests in `driver-run.json` to enable definitive attribution without post-hoc context reconstruction.

## 4. Fresh Holdout Design (Unseen Items, Same Reps & Cohorts)
All items are fresh, hand-authored shapes with unseen dimensions, frozen before any Sol call. Reps and cohort sizes are identical to v1/v2 to preserve the exact acceptance bar.

| Case | Reps | Route | Cohort / Bar Target | Description & Geometry Summary |
|---|---|---|---|---|
| W1' | 2 | source | Source ($\ge 8/10$, each $\ge 1/2$) | Hollow roller: OD 50, L 60, Bore 12. Groove Z=25..35 (W 10, radial depth 4). Gold accepts depth 4 or ID 42. |
| W2' | 2 | source | Source | Square taper: Z=0 is 60×36, Z=50 is 36×21. Linear loft, centered. |
| W3' | 2 | source | Source | 90° pipe elbow: centerline R40, OD 20, ID 12. Swept toroidal tube. |
| W4' | 2 | source | Source | Open box with triangular rib: 80×52×28, wall 4. Triangular rib thickness 4, Z 4..20. |
| W5' | 2 | source | Source | Flange: OD 110, H 12, center bore D30. PCD 84 with 6× D8 holes, top slots. |
| W6' | 3 | spec | Complex ($\ge 2/3$) | Plate 104×70×16. Top pockets 24×16 depth 5. 6× D6 through holes. Top edge chamfer 1.5. |
| S2' | 5 | spec | Stock ($\ge 4/5$) | Block 76×54×20. Pocket 24×18 depth 6. Top outer 4 edges filleted R3. Scope V measured. |
| A1' | 3 | spec | Defaults ($\ge 2/3$) | Plate 96×56×14 with central D12 through hole. Centered XY, bottom Z=0. |
| A2' | 5 | ask | Ambiguity ($\ge 4/5$, 0 inv) | Plate 74×40. 4 corner D6 holes, offset X10 Y8. Rubric: `plate_thickness`. |
| A3' | 5 | ask | Ambiguity ($\ge 4/5$, 0 inv) | Plate 68×44×14. 2× D10 through holes. Rubric: `hole_positions`. |
| K1' | 2 | source | Faults (6/6 detect, $\ge 4/6$ pass) | W1' description. Injected fault: missing groove. Repair must restore groove and driving depth. |
| K2' | 2 | source | Faults | W5' description. Injected fault: missing PCD bolt hole. Repair restores hole on PCD. |
| K3' | 2 | spec | Faults | W6' description. Injected fault: single hole diameter altered D6→D9. Repair restores diameter. |
| C2' | 3 | compl | Outside bar (independent Wilson) | Plate 80×46, 4× D7 corner holes. Turn 1 asks thickness; Answer "厚さは12。"; Turn 2 completes solid. |
| C3' | 3 | compl | Outside bar (independent Wilson) | Plate 76×48×10, 2× D8 holes. Turn 1 asks hole pos; Answer "穴中心は(20,0)と(-20,0)。"; Turn 2 completes solid. |
| Legacy | 4 | offline | Legacy controls (4/4) | Fixed A-good, A-broken, B-good, B-broken offline baseline regressions. |
| MVP | 10 | mvp | Fresh eval-v1 ($\ge 8/10$, each $\ge 1/2$) | Fresh P1–P5 × 2 reps standard eval-v1 regression. |
| Dev | 3 | preview | Unscored preview | V1 preview ($\le 2$ calls), V6 spec preview (1 call), Q2 ask preview (1 call). |

Total: 60 episodes (51 core scored + 6 completion outside bar + 3 dev preview). Call cap: planned 83, max 163.

## 5. What We Would NOT Change
1. **Acceptance Bar Thresholds**: All 8 component bar criteria and sample denominators remain byte-identical to `PLAN-CONSENSUS.md`.
2. **Quota Guard Discipline**: 55% soft stop, 60% hard stop, 300 s staleness check, future timestamp rejection, checked before every LLM call.
3. **Execution & Sandboxing**: Headless FreeCAD 1.1.4 only (`freecadcmd.exe`). No CAE/FEM solvers, no network, read-only repo.
4. **Budget Partitioning**: 900 s per run (450 s initial + 450 s repair), monotonic 10800 s suite deadline, $P \le 1, R \le 1$, CAD attempts $\le 2$, guaranteed repair call on settled CAD fail.
5. **C Cohort Isolation**: C2/C3 completion measured strictly outside `bar_met`.
6. **Integrity & Aggregation**: Freeze before Sol, exclusive file writes (`open("x")`), no-overwrite aggregates, independent FreeCAD verification process with clean closure and PID tracking.
