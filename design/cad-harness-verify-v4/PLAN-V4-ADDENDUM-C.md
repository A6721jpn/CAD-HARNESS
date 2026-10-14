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
- Q1 (U3): OCCT/FreeCAD 1.1.4 has no native G3 constraint solver (G1/G2 at most). Is G2 acceptable, or should G3 be judged numerically with a user-given tolerance on the curvature derivative?
- Q2 (U5): default plate outline/outer dimensions, default thickness, and default logo size? (Parametric, but the defaults are needed for judging.)
- Q3 (U2): maximum outer size of the box (printer bed)?
