# C-R8 review — sol

BLOCK

Reviewed `PLAN-V4-ADDENDUM-C.md:145-150`. No new user acceptance values proposed.

## B1 — removal-only scope is not compatible with the new tiny pieces unless bounded expansion elsewhere is explicitly permitted

`PLAN-V4-ADDENDUM-C.md:147-148` splits the foreground into 4-connected pieces, then permits opening the pinch by “removing material only.” It does not distinguish that local opening operation from the rest of the certified fit. A globally removal-only interpretation cannot make these fixtures pass while preserving every new piece and actual R >= 0.25 mm.

Read-only measurement of the unchanged PNGs, using the production alpha >=128 mask and SciPy cross-neighbour component labelling:

| Candidate | 4-connected pieces | Single-pixel pieces | Maximum single-pixel side in the final registration, mm |
| --- | ---: | ---: | ---: |
| case02_sharp_corners | 9 | 8 | 0.06077981651376147 |
| case10_mixed_crescent_stars | 6 | 2 | 0.06416464891041163 |

Evidence paths: `dev-c2-stress/case02_sharp_corners.png`, `dev-c2-stress/case10_mixed_crescent_stars.png`, relative to this directory. Source foreground heights are respectively 872 and 826 pixels. The upper side bounds above are derived, not tolerances: a common registration, final height 50 mm and source Hausdorff <=1.5 mm imply source height <=53 mm, hence side <=53/source-height-pixels. Removing material cannot grow those pieces to accommodate the required 0.25 mm minimum radius (0.5 mm diameter).

Concrete fix: state that **only the local topological pinch opening is removal-only**, if that is the intended rule, and explicitly say whether the existing certified approximation may move other boundaries outward within the unchanged fidelity bounds. No added bridge, merged piece, deleted singleton, mask editing or post-scoring repair is permitted. If expansion of the affected pieces is forbidden, retain a specific infeasibility refusal and a stress FAIL; author intent alone cannot make the geometry feasible. Do not silently replace this ambiguity with buffering.

## B2 — declare the complementary hole/nesting topology and checker cutover

`PLAN-V4-ADDENDUM-C.md:147-148` defines foreground connectivity but not complementary background connectivity or how a pinch within an otherwise connected region determines holes and nesting. Splitting a shared vertex is not, by itself, a complete source-topology contract.

Concrete fix: explicitly declare the paired foreground-4/background-8 convention, deterministic boundary traversal, and the source component/hole/nesting forest derived from that adjacency. Bind this interpretation in the recipe and independently in both source-fidelity/checker paths. Fitted/native/STEP boundaries must still be valid and separated; do not waive their manifold/separation checks merely because the unchanged raster has a pinch.

## Retained gates

Any expectation amendment under `:149-150` must retain the original manifest and failed results as history, receive a fresh hash commitment **before recipe finalization** as required by `:140-143`, and distinguish intended refusal cases from positive native/STEP acceptance. Merely committing it before the final run is not permission for post-finalization relabelling. All fourteen cases remain represented; unresolved or unexpected refusal remains blocking. No U5 run is authorized by this review.

This review adds only this signature. It uses public plan/stress data and read-only pixel analysis, not user attachments/private holdout data. The already-running C-R7 offline verification is separate work, not evidence that C-R8 has passed. No source/stress edits or commit for this review.
