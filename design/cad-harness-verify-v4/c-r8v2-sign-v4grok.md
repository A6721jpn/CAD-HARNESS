# C-R8v2 — v4grok

Verdict: **BLOCK**

Reviewed `PLAN-V4-ADDENDUM-C.md:150-155`. No other edit, no commit, no live call. No new user value. This sign authorizes no live run, no pilot, no operative lock, and no retirement of the cycle-2 cohort.

## Topology

SIGN. `PLAN-V4-ADDENDUM-C.md:151` is sol's B2 fix (`c-r8-sign-sol.md:22-26`). Foreground connectivity is 4-connected and background connectivity is 8-connected, with deterministic boundary traversal. The component, hole, and nesting forest comes from that adjacency. The recipe binds it, and both source-fidelity and checker paths bind it independently. Fitted, native, and STEP boundaries stay valid, manifold, and separated. Those checks stay in force.

## Pinch

SIGN. `PLAN-V4-ADDENDUM-C.md:152` is the local-versus-elsewhere distinction in sol's B1 (`c-r8-sign-sol.md:20`). Only the opening of a split corner contact is removal-only. Elsewhere the certified approximation may move a boundary inward or outward, inside the unchanged C-D(a) bounds (`PLAN-V4-ADDENDUM-C.md:98`): mask-to-contour Hausdorff <= 1.5 mm and IoU >= 0.90, contour-to-CAD IoU >= 0.92 and Hausdorff <= 1.0 mm. No bridge, no merge, no mask edit, and no post-scoring repair. The 0.25 mm figure remains the existing minimum tool radius.

## Sub-tool specks

BLOCK on `PLAN-V4-ADDENDUM-C.md:153`. Two sentences are false.

The area sentence says a 4-connected piece whose registered source area is smaller than a 0.5 mm-diameter disc cannot be produced as a valid part with R >= 0.25 mm. The disc diameter is twice the existing 0.25 mm tool radius, so that size is not a new user radius. The impossibility does not follow. `:152` allows the certified approximation to move other boundaries outward within Hausdorff <= 1.5 mm (`PLAN-V4-ADDENDUM-C.md:98`). A source piece smaller than that disc can be enlarged, within that bound, to a disc of radius 0.25 mm. The drop rule is tied to the impossibility sentence, so the drop stays unsigned. Sol's B1 also excluded a deleted singleton (`c-r8-sign-sol.md:20`).

The scoring sentence says both fidelity legs are scored against the original mask, so a drop counts against IoU and Hausdorff. C-D(a) does not do that (`PLAN-V4-ADDENDUM-C.md:98`). `image_to_contour` compares the contour with the mask (`tools/cad_verify_v4_judges.py:881-889`). `contour_to_output` compares the contour with the CAD section (`tools/cad_verify_v4_judges.py:895-896`). A piece omitted from both the contour and the CAD still matches on that second leg. The USER 17:28 citation itself matches `DECISIONS.md:61`. That decision sets rough match and the lenient thresholds. It does not state a speck drop.

The closing sentence of `:153` is right: any other piece that cannot meet R >= 0.25 mm within the bounds is a refusal and a stress FAIL. Listing a declared change in the transformation report matches the existing report (`PLAN-V4-ADDENDUM-C.md:51`).

## Gate

SIGN. `PLAN-V4-ADDENDUM-C.md:154` keeps all 14 cases (`dev-c2-stress/manifest.json:4`). The expected outcome is a geometric pass. Gemini's suite sign says cases 02 and 10 are intended feasible (`c-r8-sign-gemini.md:15-17`). The original manifest and the failed results stay history. There is no relabelling after recipe finalization (`PLAN-V4-ADDENDUM-C.md:140`, `:143`; `c-r8-sign-sol.md:30`).

## Morning note

UNSIGNED while `:153` is blocked. `PLAN-V4-ADDENDUM-C.md:155` would tell the user that sub-tool specks are dropped. `user-questions-morning.md:14` does not yet say that. In `:155`, 0.5 mm is the cutter diameter named by the disc in `:153`, not a new tool radius and not the U1/U2 0.5 mm play or gap (`DECISIONS.md:58-59`).

No live calls, CAD, or commit.
