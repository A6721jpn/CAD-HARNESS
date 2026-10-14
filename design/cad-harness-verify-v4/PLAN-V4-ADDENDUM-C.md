# PLAN-V4 addendum C - capability expansion (USER 14:28 JST) - DRAFT skeleton (relay), to be filled by sol + gemini, then signed by all 3

## C0 Integrity
- Each new family requires its own fresh holdout, authored and custodied like option B. Tuning on U1-U5 is forbidden; those attachments are not used as dev fixtures.
- The existing 163-call holdout covers the unchanged scope only. New capabilities do not enter it unless they are re-frozen before its authoring.
- Each stage freezes its code, skill and judges before its holdout. There is no range expansion beyond C1-C6.

## Stages (by difficulty)
- S1: C1 STEP attachment import + measured facts; C2 image->contour CLI + contour-extrude family + min-R; C3 text engraving; C6 judges for S1 (solid validity, IoU/Hausdorff, min-R, unchanged-dim) -> targets U5/U1/U2.
- S2: C4 direct edit of imported STEP (face selection, offset/replace/reconnect) + C6 thickness distribution / unchanged-dim / face count -> U4.
- S3: C5 freeform rebuild/merge G1-G3 + C6 surface deviation max / curvature continuity -> U3.

## TBD by sol/gemini
For each Cx: CLI vs skill split, schema/contract changes, allowed imports, determinism, failure modes, tests, judge definitions and tolerances (user values only), holdout strata/counts/call budget (needs a user decision), and quota estimate (no invented numbers).

## C-EXIT (USER 14:40 JST)
- v4 exits only when (a) the existing exit gates pass, AND (b) all 5 pilot tasks U1-U5 PASS. Each passes on its first handover, needing no edits or fixes of 5 minutes or less, with no critical dimension error and no fabrication. Astra Max judges first; the user's visual check is final.
- Order:
  1. S1 implementation (U5/U1/U2 capabilities), reviewed;
  2. S2 (U4);
  3. S3 (U3);
  4. per-family fresh holdouts, authored and custodied like option B;
  5. freeze;
  6. holdout runs;
  7. pilot run of U1-U5, one attempt each, under the frozen manifest, with no retake after seeing results.
- U1-U5 are never opened by implementers. Per-task pass criteria use user-given values only (U1: NF-13CR inner 245x365x140, part Y vertical, play <=0.5 mm, tape 0.5 mm, engraved numbers; U2: glass 1.3 mm, no contact on the 1.3 mm perimeter band, convex face may contact, concave face minimal contact, 10 pieces; U3: <=0.005 mm absolute, G3; U4: 2 mm thickness, surrounding outer dimensions unchanged; U5: parametric thickness and size, min tool R 0.25). Missing tolerances are asked of the user before the freeze, never chosen by agents.
- If any of U1-U5 fails, v4 does not exit. The response is a further development cycle on fresh dev fixtures, followed by a NEW pilot attempt under a new manifest. Old results are kept and never overwritten.

## C-R1 (gemini BLOCK fixes that need no user numbers; proposed for 3-party agreement)
- **C-R1-2 (budget):** each further development/pilot cycle after a failure needs its own separately authorized call budget and a fresh quota check before launch. Nothing is borrowed from #5. Exhausting a budget or hitting a quota stop ends that attempt as `INCOMPLETE` (reason `budget_exhausted` or `quota_stop`). It is never PASS, never looped and never extended.
- **C-R1-3 (U5 contour):** before the freeze, the deterministic S1 image-to-contour CLI runs once on pilot-user/U5_logo.png in the custodian/bundle step, never by implementers. It writes contour.json (closed loops, units, scale reference, min-R report), which is SHA-256 locked in the manifest. The generator receives it only as typed runtime data; it never sees the PNG and never traces. CLI parameters are frozen from dev fixtures before the run, with no tuning on U5.
## C-Q (user questions; implementation continues meanwhile)
- Q1 (U3): G3 remains the required result unless the user explicitly changes it. No general native G3 constraint solver has been demonstrated in the installed FreeCAD/OCCT bindings; that does not prove G3 geometry is impossible. What geometric continuity residuals, units and tolerances should be registered for seam position, normal angle, curvature and curvature derivative? Keep the already given <=0.005 mm absolute deviation bound unchanged; numerical sampling alone must not be described as a certified continuous-domain bound.
- Q2 (U5): What default thickness, initial logo size, and definition of that size/physical scale should be used? Is a separate carrier/base plate actually desired? Only if it is, provide its outline/dimensions; do not assume an extra rectangular plate is required.
- Q3 (U2): Is there a required maximum box envelope / printer-bed size? If so, provide it; otherwise confirm that no extra envelope limit is imposed.
- Q4 (U1): For the already given play <=0.5 mm, what datum, movement directions and total-versus-one-sided convention define the measurement? What angular tolerance defines Y-vertical, and what box-fit/measurement-uncertainty rule applies? Confirm the tape mounting location and any required variation/compression allowance around the already given 0.5 mm tape thickness. Do not add an agent-chosen allowance to the play limit.
- Q5 (U2): What no-rattle/play limit and standing-orientation tolerance apply? What thickness variation around the already given 1.3 mm and gap/measurement-uncertainty rule establish non-contact at its perimeter band? What quantitative limit, permitted regions or explicitly agreed qualitative judgment defines minimal concave-face contact? U1's play limit is not automatically a U2 value.
- Q6 (U4): What tolerance applies to the already given 2 mm thickness and to unchanged surrounding outer dimensions? Exact target/preserved selections must be recorded by the custodian/user without exposing attachments to implementers.
- Q7 (U5 / S1 fidelity judges): What IoU and symmetric boundary-distance limits, physical units/scale convention and numerical uncertainty are acceptable for original-image -> canonical-contour and contour -> handed-over shape? Which boundary/topology changes, if any, are permitted for the already given min tool R 0.25? No silent widening or contour alteration is authorized.
- Q8 (engraving): Are any glyph size/depth/placement tolerances critical, or may these be registered design choices with user-final readability judgment? No numeric engraving range or font-specific requirement from an agent draft is adopted by default.
- Q9 (new-family live trials): Approve the fresh per-family case counts, separate generation/refusal denominators, family pass gates and additional accepted-call reservations, including a finite allowance for any model judging. Existing #5 reservations are not expanded by either agent's proposal.
- Q10 (resource limits, only if needed): If independently measured C operations cannot fit the existing active-work limits, what revised limits are authorized? Until explicitly amended, existing limits apply; mandatory overload waits remain separately excluded and fully wall-accounted.

## C-R2 (adopts sol B1-B3 verbatim intent; supersedes conflicting C0/C-R1-3/C-EXIT text)
- **C-R2-1 (original holdout untouched):** C0's re-freeze exception is deleted. The original 163-call, unchanged-scope holdout and its custody/reservation remain unchanged. C1-C6 have separate fresh family cohorts and commitments. No C capability, item replacement, call borrowing or altered interpretation enters the original cohort.
- **C-R2-2 (image fidelity chain):** the custodian commits:
  - the original image SHA and the mask SHA;
  - the dev-frozen recipe and software identity;
  - the pixel-to-mm transform and the user scale;
  - the canonical contour SHA;
  - the topology correspondence and the transformation report.
  - The original image and the mask are checker-only. Fidelity is judged on both legs, image->contour and contour->output, against pre-registered criteria. The min-R value is rechecked from geometry. No silent deletion, bridging, smoothing or radius change is allowed. Missing acceptance values block the freeze, not the dev implementation.
- **C-R2-3 (locks and cycles):**
  - After S1-S3 and the reviews, lock the code, skill, recipes and judges BEFORE family authoring. The final freeze binds those locks plus the cards, cohorts, custody, budgets and the 5 pilot inputs.
  - Any post-failure change starts a separately authorized cycle: fresh dev material, a new lock, and fresh blind validation for the changed families.
  - Each cycle runs the complete U1-U5 roster once. Exit requires 5/5 within the same manifest. Successes from different cycles are never combined, and old outcomes are kept.

## C-A (USER 14:57 answers)
- Q1: U3 passes with G2 continuity (not G3) and <=0.005 mm absolute deviation.
- Q2: the U5 plate outline, default thickness and default logo size are delegated to sol + gemini. They are recorded in C-U5 below before the freeze and stay parametric. These are agent-chosen defaults, labelled as such; they are not user dimensions.
- Q3: U2 has no maximum outer size.
- C-R1-2 and C-R1-3/C-R2-2 are adopted as final.
## C-U5 (defaults; to be filled by sol+gemini consensus)
