# U5 defaults cross-check — sol

**BLOCK the Gemini proposal as written. AGREE with the delegated nominal defaults: a 100 × 100 mm square plate, 3 mm thickness, and a centred logo with nominal total height 50 mm.** These are agent-chosen design defaults, not user dimensions, tolerances or machining guarantees. Proposed replacement C-U5 text is below; Gemini agreement and relay incorporation remain pending.

## Authority and evidence

Reviewed `u5-defaults-gemini.md`, `PLAN-V4-ADDENDUM-C.md` C-EXIT/C-R1/C-R2/C-Q/C-A/C-S, `DECISIONS.md`'s user-answer section, and the public request text in `pilot-user-requests.md:53-59`. No `pilot-user/` file or private holdout was opened. No CAD/model run or commit was made for this review.

C-A Q2 delegates the plate outline, default thickness and default logo size. C-S expressly limits that exception to those defaults: other missing acceptance values remain user questions. C-R2-2 forbids silent contour/topology/radius changes and requires both fidelity legs and actual-geometry min-R checks.

## Findings and concrete corrections

| Item | Decision | Required correction |
| --- | --- | --- |
| 100 × 100 mm outer square, 3 mm thickness | AGREE as nominal defaults | Label as agent design choices only. Remove the unsupported claims of a globally standardized CNC benchmark, guaranteed vise/stock compatibility, or a universal 3 mm robust-machining limit. No material, tool flute length, machine or workholding evidence was supplied. |
| Logo total height 50 mm, centred | AGREE as nominal default/layout definition | Define size from the complete logo contour's bounding extent, not PNG canvas height. Preserve component arrangement and aspect ratio. Centre the logo bounding box on the plate bounding-box centre; do not separately move components. Do not add a placement tolerance. |
| Leaf gap 2.5–3 mm (`u5-defaults-gemini.md:62-64`) | BLOCK: no evidence | Delete the estimate and its claimed cutter-pass conclusion. Gap is unknown here; do not substitute measurements from a different public logo. Only the blinded custodian/checker may establish the actual prepared geometry under the frozen recipe. |
| Ratio ≈0.83, width ≈41.5 mm, horizontal margins ≈29.2 mm | BLOCK: not established for this input | Delete these source-dependent numbers and their fixturing/structural conclusions. Derive width and margins from the actual committed contour, without implementer access. The nominal vertical margin follows arithmetically from the defaults, but proves neither actual feasibility nor workholding. |
| Through-cut | AGREE with full-thickness cutting as a reading of “打ち抜いた”; BLOCK an unconfirmed retained-piece interpretation | “Through” must mean no residual floor. It does not by itself decide whether the deliverable is the punched-out logo or the surrounding plate with a logo-shaped aperture. Gemini's through-pocket construction chooses the latter. Record that interpretation explicitly and obtain clarification if the request/delegation has not established it; do not make it an additional user requirement by implication. |
| ±0.2 mm plate and ±0.5 mm logo tolerances (`:94-95`) | BLOCK: outside delegation | Remove them from pass criteria. Ask the user for applicable dimension/size/placement tolerances and measurement-uncertainty treatment before the freeze. Do not replace missing tolerances with zero or with numerical kernel tolerance. |
| Min radius ≥0.245 mm (`:96`) | BLOCK: relaxes the user's R0.25 | Keep the supplied 0.25 mm constraint unchanged. Numerical uncertainty must be reported and agreed, not converted into a smaller accepted radius. An interval crossing the limit does not prove PASS. |
| Claimed rolling-ball guarantee (`:61`) | BLOCK: unsupported guarantee and possible contour alteration | Do not claim buffering establishes tool access, exact circular fillets or fidelity. Use the dev-frozen recipe, permitted transformations and topology correspondence, both fidelity checks and actual-output min-R/accessibility measurements. Transformation permissions and acceptance bounds remain C-Q7 questions. |
| Parametric ranges and mandatory alternate values (`:14-17`, `:79`, `:98`) | BLOCK as new pilot requirements | Remove the invented ranges, conflicting thickness ranges, mandatory alternate dimensions and universal regeneration guarantee. Keep operative thickness/logo-size parameters as requested; register editability checks and their acceptance basis before freeze without inventing a user operating range. Invalid/infeasible edits must not retain a stale valid result. |

A smallest tool radius of 0.25 mm corresponds to diameter 0.50 mm; it does not establish a mandatory cutter for every operation, a maximum cutting depth, a feasible toolpath, leaf/web clearance, stiffness or physical manufacturability. None of those claims follows from the three delegated defaults.

## Final proposed C-U5 text

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

## Remaining questions for relay/user

- Confirm the intended retained material if not already settled: punched-out logo versus rectangular plate with logo-shaped aperture. This asks about the deliverable, not another numerical default.
- What dimension/size/placement tolerances and numerical-uncertainty treatment apply to the chosen nominal defaults?
- Resolve the existing C-Q7 fidelity and permitted-transformation questions. No gap, aspect ratio, toolpath feasibility or tolerance is supplied by this review.

## S1 review hold

S1 implementation remains available for review. Await the relay-forwarded reviews; do not start S2, make live calls, run the pilot, or commit. No implementation was changed by this defaults cross-check.
