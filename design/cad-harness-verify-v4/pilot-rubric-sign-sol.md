BLOCK

Reviewer: sol. Reviewed `pilot-rubric.json` SHA-256 `948de5bf70e5c2d23aa4ea97b97094d31f0f06d4d0acbc5e75d0c37fde451579`. Read only that draft, `DECISIONS.md`, the public text `pilot-user-requests.md`, and addendum C. No STEP/PNG attachments or private-holdout paths opened; no CAD/model calls, source changes or commit. Only this sign file is written for this review.

## B1 — Superseded exclusions make the operative roster inconsistent

`exit.intake_exclusion` and U3/U4 `eligibility` / `eligibility_source` retain the old E3/no-range-expansion decision (`pilot-rubric.json:24,118-119,134-135`). That intake history is superseded by `DECISIONS.md:29-48`: C4/C5 and S1-S3 are in v4 scope, and all U1-U5 must pass. Addendum C C-EXIT and C-R2-3 require the complete roster and same-manifest 5/5, not an eligible subset.

Fix: retain the old exclusions only as explicitly superseded history. The operative roster must include U3 and U4, subject to implementation/freeze and actual preparation/acceptance gates. This does not assert unseen attachments are feasible: an unsupported or failing task cannot be dropped to obtain a smaller passing denominator; it prevents v4 exit.

## B2 — Mandatory first-handover and cycle gates are omitted

`exit` records only all-five passing; `omitted` broadly discards clocks. Addendum C C-EXIT (`:16-27`) also requires first handover, no edits or fixes of five minutes or less, no critical dimension error, no fabrication, existing exit gates, Astra first and authoritative user visual judgment. C-R2-3 (`:53-56`) requires one complete U1-U5 roster per manifest and prohibits combining successes across cycles. C-U5 (`:84`) explicitly preserves these gates.

Fix: make those common gates operative for every task, preserving the agreed first-handover/five-minute rule verbatim rather than substituting unrelated stage/benchmark clocks. Require all five under the same frozen manifest, one attempt each; retain old outcomes and no cross-cycle combination. Five minutes is already sourced in C-EXIT, not an invented threshold. Keep the required FreeCAD native + STEP single-part deliverable from `pilot-user-requests.md:14,26,38,50,62` and the existing common gates rather than treating a per-task dimensional checklist alone as acceptance.

## B3 — The checklist can pass outputs that omit requested work

- **U1:** the request requires a regular arrangement and numbering of insertion locations (`pilot-user-requests.md:9`); engraved text alone does not require that layout or association.
- **U3:** G2 plus deviation alone (`pilot-rubric.json:120-129`) can accept an unchanged already-G2 STEP while leaving all unwanted design-surface boundaries. Removing/merging unnecessary freeform design-surface boundaries is explicit in `pilot-user-requests.md:33`; only G3 was superseded by G2 (`DECISIONS.md:51`).
- **U4:** thickness and surrounding dimensions alone (`pilot-rubric.json:136-153`) do not require the underside to be an offset of the top surface. The offset relationship and reconnection of adjoining features are explicit in `pilot-user-requests.md:45`; the current reconnection reminder must be an actual qualitative requirement, not merely a note that it has no numeric gate.

Fix: add these source-text requirements as mandatory task criteria. Use Astra plus user visual judgment for genuinely qualitative layout/selection/reconnection aspects; preserve the signed numeric bounds. Do not invent spacing, global face counts, seam residuals, blend radii or new tolerances. Exact attachment-derived selections must be preregistered by the custodian without exposing attachments to implementers.

## B4 — Catch-all visual fallback cannot waive unresolved critical controls

`unspecified_marker` and the catch-all `astra_user_visual` entries allow any unspecified fit/clearance/continuity item to become visual-only. The sources authorize that treatment explicitly for U2 minimal concave-face contact (`DECISIONS.md:65`, addendum C C-A2), not as blanket permission to replace missing critical tolerances or measurement uncertainty. C-EXIT/C-S/C-Q (`addendum C:26,33-42,67,82`) retain unresolved critical acceptance values as pre-freeze questions except for the explicitly delegated defaults/thresholds.

Fix: distinguish qualitative user judgment from missing critical numerical controls. Mark the latter QUESTION FOR THE USER / freeze-blocked unless an explicit decision or delegation resolves them. Do not choose a number, and do not let a visual verdict silently override a required numeric/critical-dimension gate.

## B5 — Bind the operative C-R5v2 preprocessing/failure rules

The draft's `sources` list stops before C-R5v2, and U5 does not bind its operative final-canonical-height/preparation constraints. Addendum C C-R5v2 (`:123-131`) supersedes the void C-R5 mask-height/fillet proposal: final canonical contour Y extent, alpha-derived declared foreground, dev-frozen recipe/software, no min-R fillet or buffer, one committed mask-to-world registration for both fidelity legs, preserved topology, actual-output R/tool checks and no normalization after scoring.

Fix: cite and retain those preconditions in the rubric/its frozen-manifest binding. Do not allow generic visual fallback or the fidelity numbers alone to authorize topology changes, radius repair or refitting. Retain the custodian-only once-per-cycle preparation and failure rule: U5 failure cannot pass that cycle or permit v4 exit; a later cycle needs fresh dev fixes, a new lock/manifest and fresh blind changed-family holdouts, with no tuning on U5 or mixing outcomes. INCOMPLETE remains reserved for budget/quota stops. No new user number is needed for this correction.

## Numerical provenance checked

No unsourced operative numerical threshold was found in the current draft; the BLOCKs concern supersession, missing requirements and missing gating, not a proposal to replace its sourced numbers.

| Draft quantities | Authority |
| --- | --- |
| U1 inner 245 x 365 x 140 mm; tape 0.5 mm | `pilot-user-requests.md:67,72`; `DECISIONS.md:68` |
| U1/U2 play <=0.5 mm per side; angle 3 degrees per side; U2 perimeter gap >=0.5 mm | `DECISIONS.md:58-59`; addendum C C-A2 |
| U2 glass/perimeter band 1.3 mm; capacity 10 | `pilot-user-requests.md:21,68,73` |
| U3 G2 and <=0.005 mm absolute deviation | `DECISIONS.md:51`; addendum C C-A/C-S |
| U4 2 mm and +/-0.1 mm on thickness/unchanged dimensions | `pilot-user-requests.md:45`; `DECISIONS.md:60` |
| U5 3 mm thickness and 50 mm final contour Y extent, parametric agent defaults | `DECISIONS.md:57`; addendum C C-R3-1/C-R5v2 |
| U5 R>=0.25 mm; image-leg IoU>=0.90 / Hausdorff<=1.5 mm; output-leg IoU>=0.92 / Hausdorff<=1.0 mm | `pilot-user-requests.md:57`; addendum C C-D(a)/C-R5v2 |
| Engraving defaults height 5.0 mm, depth 0.6 mm | Delegation `DECISIONS.md:62`; addendum C C-D(b) |
| 100 x 100 mm plate | Explicitly void, not an operative gate: `DECISIONS.md:57`; addendum C C-R3-1 |

Judge/pilot generator identities, same-model caveat, authoritative user visual judgment, no U2 maximum envelope, delegated tape location and qualitative concave-contact treatment are consistent with the cited decisions. Keep them. Re-sign after the operative blockers above are corrected; no attachments are needed for these corrections.
