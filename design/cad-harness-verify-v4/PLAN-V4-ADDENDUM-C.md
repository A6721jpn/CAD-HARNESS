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

## C-S (supersession, from the v4grok BLOCK 17:00)
- C-EXIT "U3: <=0.005 mm absolute, G3" is SUPERSEDED by C-A: U3 is G2 plus <=0.005 mm absolute.
- C-EXIT "Missing tolerances are asked of the user ... never chosen by agents" is SUPERSEDED for the U5 plate outline, default thickness and default logo size only. Those are agent-chosen defaults (C-A Q2), labelled as such and frozen in C-U5 before the trial. All other missing values (Q4-Q10) remain user questions; agents never choose them.
- C-U5 must be filled by sol+gemini consensus before the freeze; an empty C-U5 blocks the freeze.

### C-U5 text (sol proposal, gemini AGREE 17:40; v4grok sign pending)

> **C-U5 — agent-chosen U5 defaults (sol proposal for sol+gemini consensus)**
>
> Under C-A Q2, choose a square nominal outer plate outline **100 × 100 mm**, nominal thickness **3 mm**, and nominal logo total height **50 mm**. These are agent-chosen defaults, not user-specified dimensions or tolerances. Thickness and logo size remain operative CAD parameters. No supported operating range or additional dimension is implied.
>
> Define logo height as the total Y extent of the complete committed logo contour, including all of its components, rather than the image canvas. Preserve its original aspect ratio and relative component placement. Centre its bounding box on the plate bounding-box centre. Actual logo width, gaps and edge margins are derived facts of the committed contour, not assumed values. Do not invent a canonical aspect ratio, replace the supplied artwork, or add/delete/bridge components to force feasibility.
>
> Full-thickness cutting means no residual floor. The retained-material choice must be explicit: a punched-out logo and a surrounding plate with a logo-shaped through-aperture are different deliverables. The latter is Gemini's proposed construction, not a new user fact established by these nominal defaults. If that interpretation is not already confirmed, resolve it before freeze; do not silently add a carrier, floor, bridge or topology change.
>
> Keep the user's **minimum tool R 0.25 mm** unchanged. The defaults do not certify CNC feasibility. The custodian alone prepares the supplied raster once through the dev-frozen deterministic CLI, and locks the original-image/mask hashes, recipe/software identity, scale transform, canonical contour, topology correspondence and transformation report under C-R1-3/C-R2-2. The generator receives typed contour/runtime data only. Implementers do not inspect the attachment or tune on its result.
>
> Pass criteria must not adopt the proposed ±0.2 mm, ±0.5 mm, R0.245, unapproved parameter ranges or mandatory alternate dimensions. Applicable dimension/placement tolerances, numerical uncertainty, both image→contour and contour→output fidelity bounds, and any allowed boundary/topology transformations must be resolved with the user and preregistered before freeze. Keep nominal targets distinct from acceptance tolerances. Failure to establish feasibility or required acceptance values blocks freeze; it does not authorize adapting the defaults after inspecting U5.
>
> Preserve consensus section 5 and C-EXIT/C-R2: all required gates, unchanged first-handover/critical-dimension/fabrication rules, Astra Max judging followed by authoritative user visual judgment, and no combining results across manifests. This defaults agreement is not trial authorization.


## C-A2 (USER 17:28 answers; see DECISIONS.md for the full text)
- U5 = a cut-out logo part, with 3 mm thickness and 50 mm logo height as defaults; the plate outline in C-U5 is void. U1/U2: play <= 0.5 mm per side, angle 3 degrees per side; U2 perimeter-band gap >= 0.5 mm. U4: ±0.1 mm.
- Delegated to the agents (3-party consensus required; record in C-D):
  - (a) lenient U5 IoU/Hausdorff thresholds;
  - (b) engraving size and depth;
  - (c) new-family holdout counts, gates and budgets (no upper limit; quota 55/60 still applies);
  - (d) extended time limits;
  - (e) a baseline-without-harness CAD-time measurement design and a durable dataset.
- Open: the U1 tape location; the U2 minimal concave-face contact (judged by Astra plus the user's visual check; no invented number).
## C-D (agent-delegated values; to be filled by 3-party consensus)
- C-D adopted (sol amended proposal c-d-proposal-sol.md, gemini AGREE item by item at 19:33; v4grok sign pending). Summary:
  - (a) U5 fidelity: mask->contour IoU >= 0.90 and Hausdorff <= 1.5 mm; contour->CAD IoU >= 0.92 and Hausdorff <= 1.0 mm; same frozen transform for both; R >= 0.25 mm on the actual output.
  - (b) engraving: 5.0 mm height and 0.6 mm depth defaults.
  - (c) new families: 43 generative items + 4 admission controls; 129 generation + 43 Astra calls = 172.
  - (d) extended time limits as in c-d-proposal-sol.md section d.
  - (e) a with/without-harness CAD-time benchmark: 20 pairs, 100 calls, durable dataset `cad-harness.cad-time-benchmark.v1`. It requires named qualified human operators for the without-harness arm (user question).
- C-A2 recording: gemini AGREE (19:2x), sol AGREE (19:33).
- C-A2 addendum (USER 19:47): the U1 tape location is delegated to the agents and is not a pass/fail item; only the 0.5 mm tape thickness must be accommodated in the fit. The remaining open item is U2 minimal concave-face contact (Astra plus the user's visual check).
- C-D(e) amendment (USER 21:09):
  - The without-harness arm is Codex (the same model as the with-harness arm) running the same requests with no cad_run, no CAD-harness skills or contracts, and no harness CLI. Its operating envelope (tools allowed, FreeCAD 1.1.4 headless access, time ceiling, number of calls, how its output is handed over and judged with the same cards) must be agreed by the 3 parties before the freeze.
  - Its model calls need their own budget line (the "zero model calls" manual-arm rule is void). Human-operator fields become not-applicable.
  - Same-model pairing removes the operator-skill confound, but it measures harness-vs-bare-agent time, not human time saved; RESULTS must state this.

## C-R3 (22:20 JST; from v4grok batch2 notes; for 3-party sign)
- **C-R3-1 (C-U5 plate void):** the 100 x 100 mm plate in C-U5 is not operative (USER 17:28: U5 is a cut-out logo part). Operative U5 defaults: thickness 3 mm, logo total height 50 mm (contour Y extent, aspect preserved), min tool R 0.25 mm; C-D(a) fidelity thresholds unchanged.
- **C-R3-2 (benchmark reservation):** the C-D(e) 100-call total (which counted a zero-call manual arm) is superseded by the agreed envelope (c-de-amend-sign-sol.md, AGREE by gemini and v4grok): 20 tasks; with-harness generation <= 60, bare-arm generation <= 60, Astra judge <= 40; total <= 160. Separate from #5 and the 172-call family reservation; quota 55/60 applies.
- **C-R3-3 (integrated lock):** S1/S2 locks do not bind HEAD. Before family authoring, one integrated implementation lock binds current HEAD (original, c-s1, c-s2, c-s3 profiles, tools, schemas, fonts, recipes, judges). Plus the freeze prerequisite: the neutral bare/harness artifact adapter demonstrated on independent fixtures.

## C-R4 (00:41 JST, procedural; for 3-party sign) - lock-loop fix
- Committing a note moves HEAD and invalidates the integrated lock. Rule: lock notes and holdout public commitments are committed together in one commit after authoring; then the integrated lock is re-issued against that commit at the final freeze, and only that final lock is operative. Interim locks (6f832af, manifest 6a92bbbc...3542) are evidence history. Any later HEAD change requires a new lock before any live call.
- Q2 confirmation: holdout and both benchmark arms use openai-codex/gpt-6.1-sol xhigh; gpt-6-astra max is the pilot generator only (USER 14:07), and the Astra Max judge everywhere.

## C-R5 (01:52 JST; for 3-party sign) - U5 contour recipe
- Fact (pilot-bundle-commitment.md): the single custodian run with the dev ounding-recipe (luminance/dark/127, require-opaque, fillet 3 mm) ended FAIL contour_nonopaque_image; no contour. The intake already records U5_logo.png as RGBA (pilot-user-requests.md). That recipe was a fixture recipe, never a recipe registered for the C2 family.
- Rule: the attempt is kept as history, not retried as-is. sol authors ONE C2 production recipe on independent dev fixtures only (including RGBA/transparent-background fixtures): foreground from alpha (or alpha-composited onto white, then luminance), no fillet beyond what min-R 0.25 mm requires, scale = 50 mm over the foreground-mask Y extent. It is frozen by hash before the custodian runs it once more on U5. No U5 pixels or results are used to choose it. If that run fails, U5 is INCOMPLETE for this cycle (C-R1-2), not re-tuned.

## C-R5v2 (02:00 JST; supersedes C-R5 above, which is void; fixes sol/v4grok BLOCKs)
- Fact: the single custodian run used the dev fixture recipe rounding-recipe (SHA-256 d0551190...300b) with one disclosed substitution, scale.mm_per_pixel 0.25 to 0.05; foreground luminance/dark/127, alpha require-opaque, rounding radius_mm 3 unchanged. Result: worker status FAIL, error contour_nonopaque_image, no mask, no contour (pilot-bundle-commitment.md; private history in v4-holdout-private/pilot-v1). Kept as history; not retried as-is. No C2 production recipe was registered.
- Status of this revision: it happens BEFORE the final freeze, with no pilot, holdout or benchmark run. It is recorded explicitly as an agreed pre-freeze implementation revision (not a post-failure cycle under C-R2-3). The final integrated lock (C-R4) binds the revised code, skill, recipe and judges plus a fresh independent neutral proof.
- Recipe: sol authors ONE C2 production recipe on independent dev fixtures only, including transparent-background RGBA fixtures; foreground taken from alpha (or alpha-composited onto white, then luminance), declared in the recipe. No fillet or buffer is added to satisfy min-R; R >= 0.25 mm stays a check on the actual output with the existing tool-access checks. Boundary approximation only as the frozen recipe specifies, and both fidelity legs and topology must still pass (C-D(a)). No silent radius change (C-R2-2).
- Scale: the nominal logo height 50 mm is the final canonical contour's Y extent, aspect preserved (C-U5, C-R3-1). The deterministic scale/approximation order is specified and tested on dev fixtures; one mask-to-world registration is committed and used for both fidelity legs; no renormalization after scoring.
- C2 cohort: the C2 items and C2 benchmark pairs authored under the previous lock are retired (kept as history) and v4grok authors a fresh blind C2 cohort after the recipe freeze; other families are unaffected.
- Custodian runs the frozen production recipe once on U5. Sol never sees U5 pixels or results. If it fails, the worker status and error are recorded, U5 cannot pass in this cycle (so v4 cannot exit, C-EXIT), and there is no retuning. INCOMPLETE stays reserved for budget_exhausted/quota_stop.
- C-R5v2 note (02:42 JST, from C-EXIT): if U5 fails in this cycle, v4 is not complete (all of U1-U5 must pass). The response is a fix on fresh dev material and a next cycle under a new lock and manifest with fresh blind holdouts for the changed families (C-R2-3); results of this cycle are kept and never combined.

## C-R6 (03:30 JST; decision relayed by the parent; for 3-party sign) - cycle 1 closed, multi-island C2
- Cycle 1 is CLOSED before the freeze. No live budget was spent (0 generation, 0 judge calls). Its records (family holdout commitment, retired C2 cohorts, C-R4/C-R5/C-R5v2, both U5 preparation failures, the rubric work) are committed as a closed-cycle record without a lock. Sealed holdout content stays private.
- Cause: the U5 single run with the C2 production recipe (ae1db1b4...af00) gave worker FAIL contour_multiple_islands_one_solid_refused. Multi-piece raster input is a missing C2 capability.
- Cycle 2, C2 change (default; it does not alter the shape): a foreground made of several disconnected pieces is kept as separate pieces. Each piece is traced and extruded to the logo shape, and all pieces are output as separate solids in ONE output document/STEP (a compound). No bridges, backing or joining are added. Piece count, nesting and holes are preserved and checked, and both fidelity legs and min-R are judged over all pieces together. The single-solid rule is relaxed only for this declared multi-piece C2 case; every other family keeps one solid.
- Process: sol implements this on independent dev fixtures only (multi-piece RGBA included). Then a new C2 production recipe and a fresh neutral proof; v4grok authors a fresh blind C2 cohort (the cycle-1 C2 cohorts stay retired); one custodian U5 run; then the C-R4 combined commit, final lock, live runs and the pilot. The other families' cycle-1 cohorts are carried into cycle 2 unchanged, since none was ever run or scored.
- Open user question (does not block): bridges or a backing plate instead of separate pieces (user-questions-morning.md).
## C-R7 (05:15 JST; decision relayed by the parent; for 3-party sign) - cycle 2 closed, cycle 3 contour hardening
- Cycle 2 is CLOSED before the freeze; 0 generation and 0 judge calls. The single U5 run with c2-production-recipe-cycle2.json (0b6d09b6...7e04) gave worker FAIL contour_curve_fit_error_budget_unattainable. Records (cycle-2 C2 cohort, now retired; pilot v3) are committed as closed history.
- Stress-suite gate: before any U5 run, the agents pre-register (hash-locked before the recipe is finalized) a generic stress suite of agent-made raster logos: thin strokes, sharp corners, dense corner/curve mixes, small features, anti-aliased RGBA edges, multi-piece, nested holes. Nothing is taken from U5. The cycle-3 recipe must pass every stress case (both fidelity legs, min-R/tool access on the actual output, valid solids, both arms of the neutral checker) before the custodian U5 run.
- Fit budget: per USER 17:28 (the logo only needs to roughly match; model correctness matters more), the internal 1-pixel arc-fit budget is stricter than intended. Cycle 3 allows a certified fallback (polyline / exact-pixel boundary, or a looser certified arc fit) whose source-deviation bound is tied to the lenient C-D(a) fidelity (mask-to-contour Hausdorff <= 1.5 mm, IoU >= 0.90), not 1 px. Kept: 50 mm final canonical contour height, one registration, no rounding/filling/bridging/buffering, topology preserved, valid solids, R >= 0.25 mm and tool access checked on the final part.
- Known tension for sol to resolve on fixtures, not by waiving a check: a raw pixel polyline has zero-radius corners. Concave corners then fail the 0.25 mm min-R/tool-access check on the final part. The fallback must produce boundaries that pass that check within the fidelity bound (for example a certified fit whose tolerance allows corner arcs >= 0.25 mm), or the case fails. It is never rounded silently after scoring.
- Then: sol implements on generic fixtures only; gemini reviews; new recipe and lock; fresh C2 cohort by v4grok; one U5 run; then the C-R4 combined commit, final lock, quota check, live runs and pilot.