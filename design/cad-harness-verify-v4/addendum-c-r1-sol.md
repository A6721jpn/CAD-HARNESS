# Addendum C — independent R1 plan, sol

**DRAFT FOR CONSENSUS.** DECISIONS.md's USER 14:28 authorization permits C1–C6, in S1 → S2 → S3 order. It does not authorize extra live calls, numerical tolerances, silent changes to existing gates, or tuning on the pilot. This document proposes implementation and measurement contracts; it implements and runs none of them.

## 1. Integrity and decisions

1. **Keep the original scope and its 163-call holdout intact.** Keep its implementation/skill/judge identity, cohort, custody and reservation separate from the expansion. Do not add C cases, replace items, borrow calls or reinterpret its result. Skeleton C0's possible “re-freeze before authoring” language must not become implicit permission to repurpose that holdout: DECISIONS.md says it is unaffected. Any actual replacement would require separate authorization.
2. **No pilot-derived development input.** I did not open `pilot-user/` files, obtain measurements/contours/fonts/face selections from those attachments, reopen earlier pilot measurements, or access `v4-holdout-private` for this draft. Stage target IDs below come only from the authorization/skeleton. None of the proposed development fixtures, thresholds, operation choices or sample counts is derived from pilot geometry.
3. For each stage: independently created dev fixtures → offline implementation and judge validation → implementation/skill/judge lock → independent fresh authoring and control review → final execution commitment → one sealed run → independent results review. A defect found before execution returns to development and retires exposed candidate material; no fixes/replacements after launch.
4. The implementer must not preprocess or inspect pilot attachments or their derived geometry. A separately appointed custodian runs the **already locked** preparation recipe and supplies commitment-bound inputs to isolated invocations. Author/reviewer/custodian identities, disclosures and reveal times are recorded. Shared-filesystem procedural isolation is not a security guarantee.
5. Numeric geometry and acceptance tolerances are **UNKNOWN until supplied/approved in the applicable user card or independently authored holdout contract**. Use named parameters, units and provenance, not arbitrary constants copied from old cases. Existing-profile tolerances remain unchanged; new-profile tolerances are not secretly inherited.
6. Preserve one manifest/process per trial, full raw streams, nullable accounting, quota consultation/admission stop at 55%, hard stop at 60%, and the standing verified-overload → full 600-second wait → identical resend policy. Only verified unavailable cycles are excluded from active clocks. No retry cap, slot resets or overload-specific scoring failure.

**Architecture decision:** deterministic input interpretation, geometry construction, editing and measurement belong to the CLI. The skill selects the intended design/regions and an explicit bounded operation plan; it never imports files, traces pixels through a tool, opens documents, runs probes or declares success. New families use a declarative plan, not a second unrestricted source-generation path.

## 2. Offline installation evidence — observed, not assumed

Inspection used package inventories, read-only file/font metadata and isolated `python -B` import/API probes with bytecode writes disabled. No CAD document/shape was constructed by the probes, no renderer/solver was exercised, no package installed and no model called. The host reported **DPC-019**.

Distribution root, abbreviated **FC_ROOT** below: `C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311`.

| Component | Observed offline availability | Decision / limitation |
| --- | --- | --- |
| FreeCAD / OCCT | FreeCAD **1.1.4**, OCCT **7.8.1**; `GuiUp=0`, empty document list at core inventory | Primary native construction, topology, STEP and FCStd/reimport engine. Presence is not an operation-success benchmark. |
| Bundled Python | **3.11.14**, `FC_ROOT/bin/python.exe` | Use this environment for CAD/geometry processing. Do not load its DLLs/extensions into the host Python 3.12 process. |
| pythonocc | `OCC` imports; version **7.8.1.1**; installed package inventory agrees | Available lower-level OCCT algorithms/derivatives for C4–C6. Its package metadata lookup returned null, so record module version and distribution inventory rather than inventing a pip version. |
| Raster / contours | Pillow **12.0.0**, NumPy **1.26.4**, ContourPy **1.3.3** import successfully | Prefer this installed stack for decoding, declared masks and tracing; no network dependency or unobserved Potrace requirement. |
| Numeric / planar geometry | SciPy **1.16.3**, Shapely **2.1.2** import; inventory GEOS **3.14.1** | Distances, bounded fitting, polygon topology and planar tool-center accessibility. GEOS is not a NURBS kernel or a global surface-error certificate. |
| Font / vector output | fontTools **4.61.1**, svgwrite **1.4.3** import; FreeType **2.14.3** and HarfBuzz **11.4.5** in installed inventory | FontTools outlines are usable without a GUI. Native text-shaping libraries being installed does not prove that a Python shaping path is available. |
| Font asset | `FC_ROOT/bin/Lib/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSansMono.ttf`; digit coverage verified; SHA-256 `602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3` | Proposed registered font, not a user-approved default yet. Adjacent `LICENSE_DEJAVU` exists; redistribution requires the license notices. Do not silently fall back to Arial/system fonts. |
| Higher-level surface API | FreeCAD `Surface` imports, exposing `BlendCurve`/`BlendPoint`; `Part.BRepOffsetAPI.MakeFilling` exists | Useful building blocks, not evidence of arbitrary G3 surface reconstruction. |
| Additional native tools | Gmsh **4.15.0** in inventory and `bin/gmsh.exe` present | Not selected: meshing/CAE expansion is not needed for this plan. |
| Not found in inspected environments | `cv2`, `skimage`, `potrace`, `OCP` unavailable in bundled import probes; Potrace/Inkscape/ImageMagick absent from inspected PATH | Do not declare them installed. This is not a machine-wide absence claim. No installation is proposed merely to duplicate available functions. |
| Host Python | **3.12.10**, Pillow **12.3.0**; the inspected host environment lacks the bundled numeric/CAD modules | It may supervise workers, but must not silently choose different image processing just because it is on PATH. |

Observed APIs include FreeCAD `Shape.makeOffsetShape`, `replaceShape`, `distToShape`, `optimalBoundingBox`, `removeSplitter`, `isValid`, and B-spline construction/approximation/normal/curvature methods. Imported pythonocc classes include `STEPControl_Reader`, `BRepCheck_Analyzer`, `BRepOffsetAPI_MakeOffsetShape`, `BRepTools_ReShape`, `ShapeUpgrade_UnifySameDomain`, `GeomPlate_BuildPlateSurface`, `GeomAPI_PointsToBSplineSurface`, `GeomAPI_ProjectPointOnSurf`, `BRepExtrema_DistShapeShape` and `BRepMesh_IncrementalMesh`.

`Geom_Surface`/`Geom_BSplineSurface` expose D0/D1/D2/D3/DN. The inspected filling/plate interfaces expose G0/G1/G2 error methods; **no working G3 constructor, global error certificate or FreeCAD/pythonocc shape interchange was demonstrated**. Those remain dev proof obligations. `BRepExtrema_DistShapeShape` measures closest distance: it must not be mislabeled maximum surface deviation.

## 3. Shared CLI, schema and skill contract

### Single facade, stage-bound profiles

Extend `tools/eval_verify_v4.py`; retain its existing ledger/request/run/freeze/aggregate ownership. Proposed deterministic subcommands are `prepare`, `contour`, `engrave`, `edit`, `rebuild` and `judge`, dispatched through the same request execution path. These are proposed interfaces, not commands run by this draft. Avoid a competing driver for every family.

Use bounded implementation modules for attachment preparation, contours, fonts, direct edits, surface reconstruction and judges. Existing profiles keep their exact contracts; each C stage gets a new capability/schema/skill/judge identity. A verified old manifest must never acquire a new capability by importing a newly added helper. Keep executable stage snapshots independently verifiable rather than changing files under a previously frozen manifest.

### Common data objects

- **Capability manifest:** stage, supported family/operation enums, generator/judge identities, code/skill/schema hashes, exact Python/FreeCAD/OCCT and numeric/image/font dependencies, algorithms, resource limits, tolerance-card commitments, custody, order and phase reservations. Unknown required fields prevent the corresponding live freeze, not offline development.
- **Input manifest:** opaque asset IDs, original bytes SHA, type/units/coordinate frame, reference-to-world transform, permitted reference roles and preparation recipe/hash. Paths remain CLI-side. Fonts, source images, canonical contours and original STEP data are separately committed.
- **Prepared input packet:** schema-versioned measured facts and their source/method/units/uncertainty; reference face/edge atlas; canonical contour/font IDs where applicable; truncation/coverage flags. It contains no gold, expected verdict, correct model, reference solution source or later request.
- **Capability plan:** discriminated family plus declared operation parameters, input/selection IDs, placements, preservation constraints and requested outputs. No executable expressions, imports, external filenames or unconstrained operation-language evaluator.
- **Judge card/result:** criterion/ROI, source of target, metric and units, tolerance, method/version, approximation/uncertainty bounds, domain coverage, values and evidence hashes. Distinguish PASS, FAIL and UNVERIFIED/invalid evidence; missing evidence cannot become PASS.

### Explicit instruction changes

Amend SKILL.md runtime protocol to permit a named **`inputs`** field for authenticated initial attachment-derived facts and a **`selection`** field for approved semantic region/face choices. Retain `answer` for genuine answers and `observations` for real prior outputs/errors/failed checks. Initial attachment measurements must never masquerade as failed checks or human answers.

Add a **`plan`** output target for the new families. Existing profiles still begin under their frozen Spec/source protocol; a new-family request emits its validated family plan directly. This avoids adding a hidden interpretation/fallback model call.

**Generated-source imports do not expand:** retain FreeCAD, Part, Sketcher and math, with file/network/shell/document-lifecycle/probe operations prohibited. Trusted, frozen CLI workers may import Pillow/NumPy/ContourPy/Shapely/fontTools/SciPy/FreeCAD/Part/pythonocc as declared per operation. In particular, no generated `Part.read`, Draft/font-file loading, arbitrary DLL loading or raw source bypass is authorized.

The skill decides intended supports, selected surfaces, allowed contact, preserved boundaries, font/text placement and whether input ambiguity requires clarification. The CLI validates and executes that decision; it must not guess user intent from whichever geometric solution happens to converge. New clarification field IDs must be explicitly specified for the C profile, not added to old profiles implicitly. Resolve critical acceptance ambiguity before trial registration whenever possible.

## 4. C1 — fixed STEP import, measurements and reference-conditioned modeling [S1]

**CLI:** hash and validate the immutable original STEP; import through the pinned FreeCAD/OCCT reader in an owned headless worker; record STEP units, placements, roots, solid/shell status, bounded face/edge atlas and actual measurement uncertainty. Preserve the original reference. Canonicalization/healing is a declared separate operation with a provenance map, never silent mutation of input truth.

Generate an input packet containing useful geometry facts, not just a filename or bounding box. Support references through opaque IDs in a **`reference_fixture`** family built from the permitted stock/rib/pocket operations, with explicit reference placements and constraints. The CLI, not generated code, loads exact reference shapes for evaluation. Multiple positioned references are measurement context; they do not silently turn a single-part deliverable into an assembly.

**Skill:** choose the design arrangement/support strategy and identify relevant faces/directions from the packet and genuine answers. A whole-file bounding box cannot stand in for a curved contact surface, part thickness or principal direction. Ambiguous face semantics require a typed question/approved selection, not nearest-face guessing.

**Schema / imports:** add reference role, frame, placement, unit conversion and preparation provenance; include source digest in every face ID. Allow atlas selectors and geometric facts under `inputs`. New source imports are unnecessary. Read-only reference import is a trusted worker capability with fixed file confinement, not general generator I/O.

**Judges:** exact declared-pose interference/separation and protected-contact checks against the original reference; orientation and declared-region dimensions; solid/native/export/reimport validity. If geometric play is required, define the permitted directions/orientation, datum and movement interval in advance. A bounded translation/collision measure is not unrestricted six-DOF retention, material/friction simulation or CAE. Numerical physical-fit claims remain limited by the supplied manufacturing/installation assumptions.

**Failures:** wrong STEP units or frame; multiple ambiguous roots; open/nonmanifold geometry; tolerant-edge import; stale/ambiguous face IDs; atlas truncation; replacing geometry by its bounds; preserving only a renamed input; false no-contact from minimum distance at an unrelated face; treating collision-free placement as no-rattle. Fail closed on identity/coverage errors and record ordinary supported-case misses as misses.

**Independent dev checks:** original analytic shapes and separately authored curved-reference fixtures with known units/poses; positive and negative protected-contact cases; equivalent references with changed entity ordering; identical bounding boxes but different local geometry; corrupted/path-escape inputs; placement/sign errors; unit conversion; references unaffected by construction. Verify geometry and required dimensional drivers using independently computed truth, not generator output.

**Holdout:** its own reference-fixture family and custody, as proposed in §11. User acceptance bounds and contact/play definitions remain input-card decisions, not constants derived from any pilot attachment.

## 5. C2 — raster-to-contour, contour extrusion and minimum tool radius [S1]

**CLI preparation:** Pillow decodes only registered asset formats with resource limits. Apply a frozen foreground/alpha/background and connectivity rule. Ambiguity in color, antialiasing or topology must be resolved by an approved policy; no per-image tuning on pilot/holdout outcomes. ContourPy can trace the declared scalar/mask field; Shapely checks ring closure, winding, nesting, self-intersections and component policy. Record pixel-coordinate conventions and the pixel-to-mm transform. Preserve the original image/mask and each transformation's SHA.

Smoothing/simplification is a bounded, versioned algorithm, constrained by declared error and topology limits. It must not remove a narrow feature, fill a hole, connect disconnected components or alter a logo to make a solid unless explicitly authorized. The canonical contour is a legitimate derived user input, not hidden gold; independent expected masks/curves remain checker-only.

**Skill:** resolve what the user wants represented and select approved extrusion/size/orientation options. It does not invent missing scale, thickness, smoothing tolerance, component handling or inaccessible feature geometry. It chooses from a frozen policy, not arbitrary image processing code.

**Schema / imports:** add **`contour_extrude`**, referencing a canonical contour ID/hash, size definition, thickness, frame, hole/component policy and machining constraint card. Preserve operative size/thickness parameters in the native model. No generated image-reading or font imports; all decoding, tracing and compilation stay in the trusted CLI.

**Offline libraries:** Pillow, NumPy, ContourPy, Shapely/GEOS and FreeCAD/OCCT; optional bounded fitting with SciPy. None requires OpenCV or Potrace. Bezier/B-spline approximation must preserve holes/orientation and its stated bound.

**Judges:** canonical-coordinate mask IoU and symmetric boundary Hausdorff (§9), contour-to-solid consistency, operative size/thickness, solid validity, preserved component/hole policy, and minimum-R/tool-center accessibility. Local curve radius alone does not establish CNC machinability: inspect concave corners, narrow channels, reachable planar tool-center region and allowed approximation. Engraving/contour offsets cannot be called a full CAM/toolpath or collision-safe three-axis machining certificate.

**Failures:** inverted alpha; aliased edges; wrong pixel origin/scale; dropped islands/counters; smoothing across a gap; self-intersections; cusp/infinite curvature; min-R “repair” silently changing the intended boundary; disconnected components conflicting with the existing single-solid gate. **No automatic bridge or deletion:** the user must decide component policy; preserving a single-part gate may make a particular input unassessable until clarified. Any new multi-solid exception requires explicit agreement, not implication from C2.

**Independent dev checks:** analytic rasterized polygons/arcs with independently known outlines, nested holes, narrow connections, antialiased/transparent variants, scaled copies, same-area wrong outlines, valid/invalid radius and channel boundaries, and explicit component-policy cases. Do not use a pilot image, its mask, its contour or a scalar mutation of it.

## 6. C3 — font-based text engraving [S1]

**CLI:** resolve a registered font by ID, bytes SHA and license; fontTools supplies glyph outlines/metrics. Compile closed glyph contours and perform a bounded, native cut at a declared support face/frame/depth. Preserve text, font identity, placement and dimensional parameters in the compilation record. Missing glyphs, failed outline closure or insufficient remaining material is an error, never silent substitution.

**Skill:** choose an approved font/placement and the intended text from the request/card, respecting user-critical dimensions. It does not infer a different numbering/text scheme or invent critical depth/readability tolerances. Proposed DejaVu Sans Mono is an offline choice awaiting agreement, not an already approved default.

**Schema / imports:** add engraving operations to the new family plans: text/codepoints, font ID, glyph layout/frame, height/scale, depth, target selection and preservation constraints. The CLI owns font reads; generated-source imports stay unchanged. No ambient font fallback. Pin a shaping/layout policy: fontTools outline/advance access is not by itself a complete complex-script shaping engine. Glyph coverage and any required shaping backend must be validated before admitting the requested text; unknown support must not produce replacement boxes.

**Judges:** actual recessed material removal, glyph topology and counter preservation, depth/height/placement where specified, remaining-wall/thickness and unaffected-region comparison, native recompute and export/reimport. Readability/semantic correspondence is an Astra/user rubric item; font existence alone is not an engraving pass.

**Failures:** font drift, missing characters, inconsistent kerning/shaping, reversed text, wrong face normal or cut sign, open/self-intersecting glyphs, relief instead of engraving, counters filled, through-cutting a wall, disconnected decoration and nonoperative parameter metadata.

**Independent dev checks:** fixture-author-selected text not copied from pilot numbering; digits and counter-bearing glyphs, whitespace/layout, transforms, supported/unsupported codepoints, missing-font rejection, near-wall engraving, depth changes driving actual geometry and round-trip persistence. License notices accompany any bundled font.

## 7. C4 — direct STEP face edit: select, offset/replace/reconnect [S2]

**CLI:** import a fresh hash-bound reference and execute a bounded **`step_direct_edit`** plan. Bind selectors to the original shape plus geometric signatures and adjacency, not volatile `FaceN` labels. Resolve a unique selection before mutation and record the face/edge provenance map through split/merge/reconnection. Implement only the declared operation sequence; rollback the candidate on invalid intermediate geometry without changing the original.

**Skill:** choose target and preserved regions, offset side/direction, replacement relation and reconnection intent. Geometrically equivalent alternatives may be judged against the registered intent; ambiguous selection is not a license to move the nearest surface.

**Schema / imports:** reference ID; selection predicates/approved IDs; offset direction/distance or replacement source; allowed trimming/reconnection; preserved ROIs and dimension definitions; output requirements. The new CLI can use FreeCAD `makeOffsetShape`/`replaceShape`, pythonocc `BRepOffsetAPI_MakeOffsetShape`, `BRepTools_ReShape` and sewing/fix operations as independently validated. Generated imports/file restrictions remain unchanged.

**Editability decision:** do not promise to recover an imported STEP's lost original feature history. New edits must have operative declared parameters. Prefer native features; if a trusted parametric worker feature is necessary, its recompute code/dependencies must be frozen, use data-only persistence and pass the registered native/recompute gate. A one-shot Shape assignment plus inert custom numbers is not editability. Portability without the frozen extension is an unresolved deliverable requirement; do not silently waive it to get a passing FCStd.

**Judges:** signed thickness over the intended region; original-versus-output preservation checks; solid validity; intended face/topology changes; maximum deviation in preserved regions; native and independent export/reimport evidence. Reconnection needs both geometric continuity and a valid trimmed/topological boundary, not merely touching bounding boxes.

**Failures:** offset beyond local reach causing folds/self-intersections; reversed normals or inner/outer-side confusion; stale selectors; sliver faces; unsown gaps; unintended feature movement; lost small features; apparent thickness from the wrong opposing surface; successful Boolean return with an invalid solid. Failures are explicit supported-case outcomes, not reasons to expand the operation set during a run.

**Independent dev checks:** analytic offsets and independently authored smooth surfaces with known normals/thickness, replacement faces with constrained boundaries, adjacent feature reconnection, reordered/split faces, preserved dimensions with a localized decoy change, invalid offsets and ambiguous selections. Verify that selection ambiguity stops rather than silently choosing. New fixture parameters come from the independent author, not a pilot measurement.

## 8. C5 — freeform rebuild/merge with G1–G3 [S3]

**CLI:** a **`surface_rebuild`** plan names selected patches, boundaries that must remain, intended merges, continuity order, allowable deviation, fitting settings/resource limits and output topology. Freeze the algorithm and search policy before authoring. Any deterministic fitting/subdivision iterations are charged to CAD/episode time; they are not unlimited hidden model repair attempts.

**Skill:** distinguish an intended smooth seam from an intentional sharp boundary, choose the region/continuity intent and approved reconstruction route, and request clarification when semantics are ambiguous. It must not decide that a difficult seam can simply be deleted, smoothed at a lower order or moved beyond tolerance.

**Offline choices:** use available OCCT B-spline/Bezier representations and lower-level pythonocc derivatives. Same-domain unification is suitable only when geometry already supports it. GeomPlate/MakeFilling and approximation routines are candidates to validate on independent fixtures, not a proven general G3 solver. A genuine G3 constrained reconstruction may require a deterministic constrained B-spline fitter using the available numeric stack and OCCT evaluation; algorithm, conditioning and supported domains must be proved in development.

**Schema / imports:** boundary/patch correspondence, allowed parameterization mapping, continuity order and metric tolerances, periodic/trimmed-domain handling, fixed sharp edges, maximum bidirectional surface-error requirement and provenance of face removal/merging. Trusted CLI native/numeric imports only; no unrestricted generated optimizer or source file access.

**Judges:** region-specific face-count target, topological validity, deviation bounds and geometric continuity (§9). “Fewer faces,” a clean render, a large spline degree or a kernel `Continuity` enum is not evidence that the reconstructed boundary is G3.

**Failures:** incompatible boundary jets; overconstraint; poor parameterization/conditioning; near singularities; approximation localized bumps; curvature oscillation; preserving G1/G2 but missing G3; topology changes that hide a seam; changed sharp features; convergence without tolerance compliance; inability to certify a global maximum. No silent downgrade from G3 to G2 and no sample maximum promoted to an exact guarantee.

**Independent dev checks:** analytic polynomial/rational patch pairs with known geometric jets; the same geometry under different parameterizations; G1-only/G2-not-G3 decoys; matching principal-curvature values in an incorrect tangent frame; periodic/trimmed seams; intentional sharp boundaries; singular points requiring rejection/qualification; localized deviation spikes between coarse sample locations. Gold uses analytic relations and independently reviewed native controls, not the same fitter's output as truth.

**S3 live prerequisite:** demonstrate a working reconstruction plus a trustworthy required judge on independent dev data. Installed APIs alone do not meet it. If a requested guarantee cannot be established within the frozen limits, report UNVERIFIED/FAIL and retain the item; do not change the gate or omit it.

## 9. C6 — deterministic judges, staged with the families

### Shared numerical contract

Each metric binds original/handed-over hashes, coordinate mapping, selected region, boundary/trim domain, units, algorithm and coverage. User-supplied acceptance tolerance and numerical evaluation uncertainty are separate fields. The second must not silently enlarge the first. For a maximum-error requirement, retain a lower/upper bound `[L,U]`: PASS only if the supported upper bound meets the allowed limit; FAIL if the supported lower bound exceeds it; otherwise UNVERIFIED. Exact handling of equality, valid-solid requirements and refusal cases is registered before trial. UNKNOWN tolerances block registration of that criterion.

### Judge definitions

1. **Maximum surface deviation [S2 preserved regions; S3 full rebuilt region].** Use bidirectional distance/Hausdorff between the registered trimmed surfaces in the fixed frame: both original→candidate and candidate→original. Minimum shape distance, nearest sampled-point distance and one-sided projection are insufficient. Record extrema and coverage. A certified upper bound needs justified patch/trim enclosures or a demonstrated conservative approximation-error bound; OCCT mesh deflection is not automatically such a proof. Adaptive sampling gives a sampled lower bound, not an exact global maximum. If a certificate cannot be established, say so and do not certify a maximum-error requirement.
2. **G1 [S3].** After positional seam compliance, compare oriented tangent planes/normals along the mapped common boundary. Control orientation and corners/degenerate regions explicitly; missing boundary coverage cannot pass. Angular and positional tolerances are required user/holdout-card values.
3. **G2 [S3].** Compare second-order geometric behavior in a shared tangent frame under a valid reparameterization, including the second fundamental form/normal-curvature behavior. Equal principal-curvature numbers alone are insufficient. Curvature tolerances have inverse-length units; boundary and singularity treatment must be explicit.
4. **G3 [S3].** Require third-order geometric jet compatibility under the approved boundary correspondence/reparameterization, including curvature variation, not equality of arbitrary UV derivatives or a parametric C3 label. Freeze the exact mathematical residuals and their units. Available D3 evaluation is necessary evidence for an implementation, not proof of a correct invariant judge or feasible reconstruction. Unsupported singularities are UNVERIFIED, not auto-pass.
5. **Face count [S1 topology record; S2/S3 specified edit target].** Count actual B-rep faces before/after on the declared region and full shape, with a correspondence map. Score only against an explicit expected relation/target. Lower is not universally better; removing an intended feature or sharp edge is a failure even if count falls.
6. **Thickness distribution [S1 protective/remaining walls; S2].** Define the opposed surface sets, side/direction and thickness convention first. Report region extrema/distribution, sampling or certified coverage and unresolved/multiple intersections. A shortest distance somewhere, ray to an unrelated face, or a bounding-box span is not wall thickness. Surface-normal offset and nearest-opposing-surface thickness are not interchangeable. A sampled distribution cannot prove an unbounded-domain maximum/minimum without an error bound.
7. **Unchanged dimensions [S1 as specified; S2/S3 preserved regions].** Freeze semantic dimension/landmark and ROI definitions against the original reference; compare them after the declared global transform only. Do not optimize alignment independently to hide movement. Check explicit dimensions plus preservation-region geometry where required; equal overall bounds/volume cannot certify unchanged local features.
8. **Solid validity / native and reimport [all stages].** Use OCCT/FreeCAD validity and B-rep checks, required connected-solid/Body/Tip/native recompute conditions, intended shell closure/orientation and the existing independent FCStd/STEP evidence. A no-exception kernel call is not validity; a valid solid is not design compliance. Any exception to old single-solid/editability requirements must be explicit and family-scoped before freeze, not a post-failure interpretation.
9. **Image IoU and boundary Hausdorff [S1].** Compare the model's declared 2D silhouette/cross-section to the committed mask/contour in the same scale/frame. IoU = intersection area / union area under the frozen rasterization/coverage convention. Report symmetric contour distance with declared pixel/mm transform and a bound for discretization. Do not choose alignment to maximize score after seeing the output. IoU alone misses small features; Hausdorff alone does not establish hole/component topology. Thresholds, resolution and error budget are UNKNOWN until registered, not selected from a pilot image.
10. **Minimum R and planar tool accessibility [S1].** Evaluate the specified tool radius against continuous boundary curvature, nonsmooth concave corners and access through narrow regions, with inside/outside orientation handled correctly. Combine it with the tool-center feasible-region test; straight segments are not small-radius failures, and convex outside corners differ from concave inaccessible corners. Limits come from the card. This is not a promise of a production toolpath, feeds/speeds, workholding or machine collision clearance.

C1 additionally uses original-reference contact/separation and declared-motion measurements as bounded geometric evidence. These must not be inflated into a physical no-rattle or friction/elasticity guarantee outside C1–C6.

### Skill and human judging

The skill interprets intent and reads measured diagnostics; it cannot override numeric judges or hide UNVERIFIED fields. Astra Max judges evidence sufficiency, visual/semantic intent and adoption suitability **after** deterministic metrics, not by estimating dimensions/curvature from renders. The named user's final adoption/critical-error verdict remains authoritative; record both verdicts and disagreements.

Keep consensus §5: first proposed/later handover critical dimension error or fabrication irreversibly fails the task/pilot; no-edit adoption or corrections plus headless re-verification within 300 elapsed seconds from first edit; waits and amount changed recorded; non-adopted/unassessable enrolled tasks remain non-successes. Continue a fixed roster unless an independent operational stop applies.

Pilot generation remains Astra Max under the relayed pilot-only decision; the unchanged holdout generator remains Sol/xhigh. The pilot judge sharing the generator's model is a declared limitation. A Sol holdout does not establish Astra-specific blind reproduction. Model-matched additional reproduction would need its own user authorization and fresh cohort, not an inferred equivalence.

## 10. Stage rollout and acceptance

### S1 — C1/C2/C3 plus S1 C6 judges; targets U5/U1/U2

Deliver the safe input/facts bridge, registered raster recipe, contour-extrude compiler, parametric text engraving and reference-aware evidence. Ship these as one stage profile so hashes, transforms, fonts and contours are bound consistently. Offline independent-fixture proof must include parameter changes that actually affect native geometry, invalid-input rejection, figure/solid topology and export/reimport. Do not claim that installing a font or copying a STEP completes this stage.

Freeze code/skill/judges and processing policies before fresh S1 authoring. Run each new family cohort under its own committed denominators; independently review results before any corresponding live pilot. Whether all S1 families must pass before any S1 pilot is admitted is a user-decision gate; recommended yes, to avoid deploying only the easiest subset while calling S1 complete.

### S2 — C4 plus S2 C6 judges; target U4

Require S1 infrastructure/judge stability, then independently validate selections, offset/replacement/reconnection, preservation and thickness with the native worker. Freeze a new stage identity; do not mutate S1's frozen executable snapshot. Complete a separately authored direct-edit holdout before its pilot. No promise of recovered source CAD history or arbitrary offset feasibility.

### S3 — C5 plus S3 C6 judges; target U3

Require the actual geometric-continuity/deviation judge and reconstruction proof before final freeze. Validate derivatives, reparameterizations, trimmed boundaries, certificates and hard negatives independently. Complete its own fresh continuity/rebuild holdout before its pilot. If the dev proof fails, this stage stays blocked rather than shipping a sampled-error/G2 substitute labeled G3.

**Pilot version/denominator decision:** staged implementation freezes are different treatments. Recommended: explicitly authorize separately committed stage pilots and report them separately; do not pool them into a claim of one unchanged implementation across all five user requests. Keep the original request IDs/order within each authorized roster. If the user instead requires one five-request/single-implementation trial, defer that pilot until the final common implementation and all applicable fresh validation are locked. Do not silently change N, reuse exposed scored items as new blind evidence or turn pending stages into successful zero-task trials. No pilot-derived evidence is exposed to implementers for later development/tuning.

## 11. Fresh holdout strata and budgets — PROPOSAL, USER DECISION REQUIRED

The following are proposed experimental allocations, **not observed demand, quota forecasts or authorized calls**. Each named generative family gets a separately authored, sealed cohort; the fixed existing holdout is outside this table. Each listed set of six strata receives two independently authored cases. Mark expected generation, refusal/clarification and preflight-stop strata separately before freeze; correct refusal/preflight rejection must not inflate the geometric-success denominator.

| Stage / family | Proposed strata | Cases | Proposed accepted-model cap per case | New reservation |
| --- | --- | ---: | ---: | ---: |
| S1 C1 reference fixture | Units/pose; face-identity stability; thin/curved reference contact; repeated placements; interference/protected regions; ambiguous or invalid reference handling | 12 | 3 | 36 |
| S1 C2 contour extrusion | Nonconvex boundary; nested holes; alpha/background interpretation; narrow-feature preservation; radius/channel accessibility; component-policy ambiguity | 12 | 3 | 36 |
| S1 C3 engraving | Glyph counters/digits; layout/transforms; small marks/remaining walls; approved glyph coverage; depth/operative parameters; missing font or ambiguous text policy | 12 | 3 | 36 |
| S2 C4 direct edit | Valid signed offset; boundary-constrained replacement; neighboring-feature reconnection; face split/reordering; preserved-region dimensions; infeasible edit/ambiguous selection | 12 | 3 | 36 |
| S3 C5 surface rebuild | G1 regular seam; G1 trimmed seam; G2 regular seam; G2 trimmed seam; G3 regular seam; G3 trimmed seam | 12 | 3 | 36 |
| C6 independent judge challenges, delivered before the corresponding stage run | Each of the ten judge definitions above: independent positive, decisive negative and uncertainty/boundary case | 30 | 0 | 0 |

New generative reservation proposal: **180 accepted calls**, separate from the existing 163/40 reservations. The proposed cap of three is one plan response plus at most one shared parse repair and one CAD repair; it does not authorize extra repair loops. Existing-profile caps remain unchanged. A different initial-question/completion path requires a separately specified cap/reservation before freeze, not a hidden fourth call. Deterministic preparation/judging and independent native controls make no model calls and are still recorded/timed.

The judge-challenge set has independent private truth and is not a replay of development fixtures or automatically generated correct/incorrect versions of pilot geometry. Live judge challenges are not model generations; record CAD/CPU work separately. Implementation and oracle must not share the same unexamined approximation as their only correctness evidence.

**Still requiring user/consensus decisions:** cohort counts and exact per-family gates/denominators; all-critical-fail policy; whether gates require coverage in every stratum; numerical user/author cards; new call authorization; reservations for actual Astra judging; stage pilot rosters/order and whether trials are separate. Do not invent a success-rate threshold for these fresh families by copying the pilot's 70% adoption criterion. No post-outcome trimming, transfer or retake is permitted.

Judge-model calls, if used, are real charged work. Their count depends on the registered handover/judgment policy and is **UNKNOWN** here; they are not free deterministic C6 work and are not silently included in the generator ceilings. Before live freeze, authorize and reserve their finite allowance explicitly and retain human final judgment. Existing pilot reservations are not automatically enlarged or repurposed by this table.

**Quota estimate: UNKNOWN.** No expanded-family token/latency measurements exist from this inspection; a call count is not a quota percentage. Keep every unsupported token/time/price forecast null. Obtain a fresh observed quota snapshot and user live authorization at the applicable freeze. Missing rates do not prevent measurement; prices remain null without an applicable user source. V3 route-baseline reductions for genuinely new families have no matching baseline and must remain null, not a claimed improvement.

## 12. Development tests, deterministic behavior and failure accounting

- Reuse existing test conventions and unchanged-profile regression tests. Add permanent tests only for consumer-visible boundaries: input identity/units, geometry/parameter effects, face correspondence, topology, preservation, forbidden fallback, metric correctness and uncertainty transitions.
- Native positive/negative fixtures and analytic oracles are independently authored/reviewed. No pilot attachments, derived packets, masks, contours, shape signatures, tolerance choices or public examples scalar-mutated from them enter development. Author/reviewer validation uses no generation model.
- Verify that each required parameter drives the actual geometry and survives normal recompute/round-trip. Do not add an unrequested live perturbation gate; parameter perturbations belong in independent development/control verification unless a trial card expressly requires them.
- Use frozen processing parameters, coordinate conventions, order and seeds wherever algorithms depend on them. Record exact artifacts and numeric evidence. Native serialization byte identity is not generally guaranteed across kernel/platform versions; pin this host/runtime and distinguish semantic geometry invariants from raw SHA identity of a particular run.
- Keep generation and verification owned, separate headless workers; never let generated code run metric logic. Distinct analytic/native controls reduce common-mode error, but two wrappers around the same OCCT kernel are not independent numerical engines.
- Resource exhaustion, capture failure, identity/selector mismatch or invalid scoring evidence preserves partial data and stops appropriately. Ordinary model/design misses remain in their committed denominators. A numerical judge unable to resolve its required bound returns UNVERIFIED, never a fabricated maximum or curvature result.
- Existing active-work clocks remain the default unless explicitly amended. New processing/solver time limits must be established using independent dev measurements and agreed before freeze; their adequacy for S2/S3 is **UNKNOWN**. No long solver silently bypasses an episode deadline. Mandatory verified overload waits remain uncapped and fully wall-accounted.

## 13. Guarantees deliberately not made

This plan does not guarantee that arbitrary imported STEP can be healed, that every offset exists, that every raster has a unique faithful contour, that arbitrary glyph/script layout works, that a disconnected silhouette can satisfy a single-solid gate, that every freeform patch admits G3 within the user's error bound, or that sampled metrics certify a continuous-domain maximum. It does not recover lost parametric history, certify print friction/fit from nominal CAD alone, provide CAM/CAE, prove a globally minimal-contact design or forecast model quota/cost.

C1–C6 are now authorized directions, not proofs that all their algorithms and judges already work. Stage completion requires the specified end-to-end offline proof and separately frozen fresh evidence; installation inventories, screenshots, mock echoes or a successful Boolean are not substitutes.

**Next:** reach three-party consensus on the new contracts, judge mathematics, unknown acceptance/resource values, stage/version policy and proposed budgets. Then implement using independent dev material only. No live authorization, implementation cutover, input release or commit is performed by this R1 draft.

Signed: **sol** (`openai-codex/gpt-6.1-sol`).
