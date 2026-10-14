# CAD HARNESS v4 C-S2 — direct STEP editing

This profile is offline development only. It never authorizes a pilot, holdout, provider call or model judge. The original and c-s1 profiles retain their own contracts. No S3 rebuild is available.

Return a typed `step_direct_edit` plan, not Python source. Request text stays verbatim. The only initial geometry information is the authenticated `runtime_data.inputs` STEP facts and optional approved `runtime_data.selection`. No attachment paths, document access, tools, network, shell, imports or execution are available to the generator. Initial facts are not failed-check observations. Never invent missing user dimensions, tolerances, normals, thicknesses or feature intent.

Choose the original source asset and a unique face by its geometric signature, source hash and adjacency. `FaceN` alone is not authority; ambiguity is not permission to choose the nearest face. Preserve original X/Y/Z and the fixed coordinate frame; do not use best-fit alignment to hide movement. Curved midpoint normals are local facts, not a global normal for the face.

Whole-body bounds and independent axis-dimension checks use non-triangulated optimal bounds of the trimmed geometry. Face-atlas bounds remain conservative native enclosures used in frozen signature identity; extended spline supports can make those enclosures loose. Neither kind of bounding box establishes wall thickness or local preservation.

Choose one explicit supported edit: a signed outward-normal offset using the actual OCCT per-face engine, or replacement by a separately committed STEP face support, followed by the declared extension/intersection/trimming reconnection. Replacement currently requires planar source/replacement supports and full finite-patch coverage within the declared extension bound; curved offsets are exercised but arbitrary feasibility is not guaranteed. Dependencies are typed asset/face identities, not filenames. An infeasible edit must not silently become another operation, healing route, feature deletion or lower-quality reconstruction.

The trusted CLI imports exact original geometry, validates and executes the edit, restores native operative parameters and separately reopens FCStd/STEP for independent judging. It does not recover lost source CAD history. Do not claim that a valid Boolean or unchanged overall bbox proves local preservation or correct thickness. Use the declared opposed surface sets, direction, thickness convention and coverage. Sampled evidence is not a continuous-domain certificate.

Repair uses the same output route and shared P1/R1/CAD2 limits. Read measured observations without inventing hidden targets; never override FAIL or UNVERIFIED. Environment, binding, capture and cleanup failures are not geometric repair opportunities. Final acceptance also requires the unchanged consensus gates and user-authoritative judgment; offline development results are not trial evidence.
