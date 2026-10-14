# User-pilot criteria and blocker check — sol

## Verdict under the unchanged contracts

| Request | Decision | Decisive reason |
| --- | --- | --- |
| U1 | **E3** | The box/holder primitives and font-free numbers are not the decisive obstacle. The unchanged generator has no authorized attachment/reference-fact input, generated source cannot import the enclosure STEP, and the checker has no declared original-STEP fit/play comparison contract. |
| U2 | **E3** | The supplied glass is an external geometric reference. Its thickness alone does not describe its two curved faces and perimeter. The frozen path cannot supply/consume that reference or verify its protected-band/contact requirements without a new interface/checker capability. |
| U3 | **E3**, unchanged | Freeform G3 surface reconstruction remains outside the frozen classes; the user explicitly did not expand scope. |
| U4 | **E3**, unchanged | Freeform offset/healing with surrounding-feature preservation remains outside the frozen classes. |
| U5 | **E3** | A supplied raster is not a permitted raster-to-contour/CNC silhouette pipeline. The absent-logo attachment finding is withdrawn, but neither the input channel nor the contour reconstruction capability exists in the unchanged contract. |

**No request is ELIGIBLE for this unchanged pilot. N=0 means `not_run`, not PASS.** This revises my earlier conditional U1/U2 assessment: identifying a plausible box-like shape family was insufficient without checking the actual attachment and checker interfaces. The new user values resolve several acceptance ambiguities; they do not authorize changing those interfaces.

Independent review only. No other party's screen/signature was consulted. No source, skill, policy, request or attachment was modified. No generation, CAD execution, pilot run or commit was performed.

## Sources and observed checks

- Original requests plus verbatim answers: `pilot-user/requests.md:13-17`, under this design directory. Current SHA-256 `a3a75986e005d18f9e2c734638b455adb8370b362095fcc4fe149bee3ae20593`, 2,542 bytes; matches the intake commitment.
- Confirmed interpretation/values: `pilot-user-requests.md:65-75`. NF-13CR identity and its 245 × 365 × 140 mm effective interior dimensions are now user-confirmed, unlike the previous screening round. No additional web lookup or invented numbers are needed for that nominal reference.
- `pilot-user/U5_logo.png`: exists/readable; 39,139 bytes; SHA-256 `cff917e0b7e317eff88977aafea0379a99522e3ab120b36b7d73ee5626bfdd3b`, matching the intake. PNG signature/IHDR checked: 814 × 1000 pixels, 8-bit RGBA. The image was inspected read-only; no tracing, resampling, vectorization or model construction was performed.
- Frozen instructions: `skills/cad-harness-v4/SKILL.md:8-18` and `contracts.md:266-277`.
- Executable evidence: `tools/cad_verify_v4_agent.py:23,168-189`; `tools/cad_verify_v4_live.py:282-295`; `tools/cad_run.py:114-131`; `tools/cad_run_freecad.py:49-59,145-151`; `tools/cad_verify_freecad.py:41-78`; `tools/cad_verify_v3_probe.py:22-40`; `tools/cad_verify_v4_pilot.py:324-357`.
- Pure Python contract inspection, without invoking a generator or CAD: a new `reference_bounds_mm` runtime key is rejected with `runtime_data_fields`; AST calls named `Part.read` and `FreeCAD.openDocument` are rejected with `source_operation_contract`. The serializer accepts arbitrary nested contents under `observations`; that permissiveness is **not** semantic authorization to violate SKILL.md:12.

## 1. U5 after the raster attachment

**Raster-to-contour remains outside scope.** The user has supplied authoritative image bytes, resolving the old missing-logo asset issue. E7 must not be reasserted merely because those bytes are raster rather than vector. E3 is a different question.

The unchanged payload is original request text plus typed runtime data; it has no image-content input. An attached PNG path, a copied PNG file or its hash is not the image delivered to this tool-less invocation. Even if a model could receive pixels through some other API, that is not the frozen path being evaluated.

Turning pixels into editable CAD outlines also requires a specified conversion: foreground/alpha interpretation, boundary extraction, treatment of antialiasing, disconnected contours, curve fitting and dimensional deviation. No such conversion/approximation policy or shape class is frozen. A finite raster does not uniquely specify exact CAD curves or a physical scale. The R0.25 mm tool constraint does not supply that missing geometry, logo size or thickness. It is not an instruction to invent a contour or indiscriminately fillet it.

Thus neither having FreeCAD installed nor recognizing the logo makes this request an existing rectangular-stock, roller, taper, tube, ribbed-box or flange case. No tracing, new image channel, image-reading tool, vectorization helper or logo-specific implementation may be slipped into this pilot. This is a limitation of the frozen experiment, not a claim that FreeCAD can never model a logo.

## 2. Attachment and source-mode blocker check

### Generator: attachment-derived facts are not currently authorized initial runtime data

SKILL.md:12 defines exactly four keys:

- `target`: spec/source selection;
- `stage`: initial/repair selection;
- `observations`: actual previous output, parse errors or **measured failed checks**;
- `answer`: a **genuine clarification answer**.

An analyst's preflight STEP bounding box is not a previous generated output, parse error or failed check on a generated candidate. It therefore **cannot be injected as initial `observations` under the present meaning**. Introducing `attachments`, `reference_geometry`, `bbox` or another initial-facts key changes the contract. Hiding those facts inside an existing key changes its semantics just as surely. They must not be relabeled as a human answer or inserted into the verbatim request.

The actual new user answers may be preserved as genuine user facts; the analyst's earlier measurements do not become user-given answers by association. In any event, a bounding box is not a replacement for the enclosure/glass boundary, contact faces or permitted seated motions. The earlier inspection established only axis-aligned bounds, not a complete reference model or a fit criterion.

The live code confirms the boundary: `payload.json` contains `request` and `runtime_data`, and omp runs with `--no-tools`. No STEP, PNG, reference preload or image channel is supplied there. The isolated `build(doc)` worker starts a fresh document; there is no preloaded reference object that generated source may assume exists.

### Generated source: allowing `Part` does not allow `Part.read`

The import allowlist and operation denylist are separate. Source may use FreeCAD/Part/Sketcher/math to construct the allowed model, but `contracts.md:273` prohibits file operations and document lifecycle operations. `cad_run.source_contract()` explicitly rejects `read`, `insert`, `openDocument`, `loadFile` and related calls.

Consequently, code that imports an original STEP itself is not a compliant solution. Passing a path string, renaming a file or relying on globally accessible filesystem paths does not change that. Reference-document preloading, `build(doc, reference)` or a different builder environment would be new interfaces, not existing behavior.

### Checker: file access is allowed there, but a reference-aware fit checker is not present

The deterministic CLI/checker is not subject to the generated-source import allowlist. It already reads checker gold and reopens **generated** `model.FCStd`/`model.step`, with artifact hashes and independent reimport checks. It would be incorrect to say the checker is categorically forbidden from reading any STEP.

However, this does not provide the missing feature:

- `pilot-bundle` copies and verifies attachment bytes. Its integrity check is not STEP interpretation, reference loading, contact classification or play measurement.
- The existing reimport reader opens the generated artifacts; its `Part.read` call is not an original-reference attachment input.
- The frozen v3 gold reader admits specific analytical profiles/parameters and fixed predicates. It has no declared original-STEP reference, protected-perimeter-face set, convex/concave contact acceptance or fixture-play evaluator.

The original STEP files can reach an evidence bundle on disk **without** a modeling change. They cannot reach an operative reference-aware generation/checking path merely by being copied there. Adding that path and the required fit/contact checks is a capability change. Replacing an output artifact with the input STEP, treating checker gold as generator context or weakening evaluation to a bounding-box-only surrogate would invalidate the requested experiment.

### Engraved U1 numbering does not inherently require a font file

**Yes, simple engraved numerals are representable without a font file.** Numerals can be constructed from finite line/arc or rectangular-stroke sketches and cut as recessed features using allowed modeling operations. This is conceptually different from importing Draft/font infrastructure or tracing an arbitrary supplied logo. No particular font was requested; font absence alone is not an E3 reason.

This observation is not a generation result or proof of an arbitrary typography capability. The numbers must actually be engraved and readable, not merely named properties, painted labels or raised text. No font-specific workflow is authorized. The STEP reference/input and fit-checking blockers remain even if numbering is made entirely from existing pocket/sketch primitives.

## 3. User-given obligations and Astra rubric inventory

There are **no eligible requests for which a trial-ready fixed acceptance card can honestly be signed under these contracts**. The inventories below retain the requested U1/U2 criteria exactly, identify measurement/tolerance gaps, and specify the corresponding Astra judgment items. They are **not** enrollment, permission to extend the checker, a replacement design request or an assertion that the blocked measurements have been implemented.

### U1 — fixed user facts, not an authorized trial card

| Criterion from the user | Measurement/evidence needed | User-given limit / tolerance status | Astra Max item |
| --- | --- | --- | --- |
| Fit the confirmed NF-13CR interior | Installed holder/reference arrangement, including the tape at its actual mounting location, compared with the approved box reference. Envelope bounds are necessary but do not establish complete bottom/corner fit. | Nominal internal dimensions **245 × 365 × 140 mm**. No additional box-fit/manufacturing tolerance supplied. Do not use external dimensions, replace the box by invented geometry or subtract tape from every axis. | Correct product/dimensions; assess installed fit; flag absent interior/fit evidence rather than infer success. |
| Part Y is vertical | Compare the original part's Y direction in the seated pose to the agreed vertical direction. | Y-axis choice is fixed. Angular tolerance is not supplied; do not invent degrees or silently reuse a native-check numerical tolerance as a physical acceptance allowance. | Correct axis and upright pose; no substitution of a different longest-axis estimate. |
| No more than the specified play | Maximum free motion of the actual reference in the seated holder, using a user-agreed datum, directions and play convention. Bounding-box clearance alone does not establish this. | **Play ≤0.5 mm**, inclusive. No extra ± allowance is authorized. Peak-to-peak versus one-sided interpretation and measurement uncertainty remain unregistered. | Report measured play and method; reject an exceedance; mark unassessable if the required reference/method is absent. |
| Double-sided tape installation | Tape stack included at the intended mount and accounted for in installed clearances. | **0.5 mm nominal tape thickness**. No tape compression/thickness tolerance or mounting-location convention supplied. | Tape mount is feasible and accounted for; no invented zero-thickness tape or alternative fastener requirement. |
| Regular arrangement and engraved numbers | Inspect actual placement and recessed numeral geometry/readability for the holder positions. | Count is **unspecified**, not a maximum-capacity target. Engraving is required; no font, glyph size, depth or spacing tolerance has been supplied. | Regular arrangement; real, legible engraving associated with positions. Do not substitute mere label provision now that engraving was selected. |

Remaining U1 questions, relevant only if an unchanged-scope admissible path is established or a separate amendment is authorized:

1. Does ≤0.5 mm mean total peak-to-peak free play or another convention, in which directions and at what reference point? What measurement uncertainty/decision rule should apply at the limit?
2. What angular tolerance defines Y-vertical, and what installed clearance/interference and box-interior reference are acceptable for the requested fit? The product identity and nominal interior dimensions are **already answered**; do not ask them again.
3. Where is the 0.5 mm tape installed and what compression/thickness variation, if any, belongs in that assessment? If engraving has a critical size/depth/readability standard, supply it; otherwise retain user-final qualitative readability without inventing a dimensional threshold or a font requirement.

### U2 — fixed user facts, not an authorized trial card

| Criterion from the user | Measurement/evidence needed | User-given limit / tolerance status | Astra Max item |
| --- | --- | --- | --- |
| Store ten glass pieces standing in the requested arrangement | Ten unchanged reference pieces in the intended seated poses relative to the one storage-box deliverable; assess orientation, capacity and interference. | **10 pieces simultaneously**. This does not require exactly ten slots or prohibit additional capacity. Standing-direction/angular tolerance remains unspecified. | Ten fit in the requested standing arrangement; no count substitution or invented glass reference. |
| Correct glass reference and thickness | Actual STEP reference plus the user's stated thickness; a thickness-aware identification of the perimeter wall between the two broad faces. | **1.3 mm nominal glass thickness**; no thickness tolerance supplied. It is not the whole-file Z span. | Uses the supplied glass and stated thickness; no rectangular-plate surrogate or bounding-box-as-thickness claim. |
| Nothing contacts the peripheral edge face | Identify the **1.3 mm-thickness perimeter band** and evaluate its separation from the holder and the other pieces in the seated condition. | **No contact** is the stated condition. No numerical positive clearance or metrology tolerance supplied. The 1.3 mm is not an invented setback distance on the broad face. | No support/contact on that protected edge band; require face-specific evidence, not a render-only or bbox-only assertion. |
| Convex broad face may contact | Face-resolved contact/separation evidence distinguishing the two broad surfaces from the protected perimeter. | Contact on the convex face is **permitted**, not mandatory contact over its full area. No contact-area or pressure value supplied. | Does not incorrectly prohibit all convex-face support or permit edge contact by relabeling it. |
| Concave broad face has minimal contact | Identified concave face and documented contact locations/extent, judged against the user's agreed meaning of minimal. | **Minimal contact**, not automatically zero contact and not an invented area/percentage limit. No numerical criterion supplied. | Report contact rather than claiming an undefined optimum; user final judgment is required. |
| No rattle | Actual seated-reference play evidence or the user-agreed physical judgment. | Original no-rattle requirement remains. The user's **U1** ≤0.5 mm answer is not automatically a U2 tolerance. | Does not silently transfer the U1 limit; flags an undefined/unmeasured U2 play verdict. |

Remaining U2 questions:

1. What standing orientation/angular tolerance and no-rattle/play acceptance apply to this glass? Does the user intend U1's 0.5 mm limit to apply here as well, or a different definition? Do not assume either answer.
2. What gap/measurement-uncertainty rule establishes no contact at the identified perimeter band, and what variation around the nominal 1.3 mm thickness must be considered? The definition of the protected edge is **already answered**; only any ambiguity in mapping it to actual STEP faces remains to resolve.
3. What makes concave-face contact “minimal” for final acceptance: specified permitted regions, a quantitative bound, or an explicitly agreed human qualitative judgment? Do not equate it to zero or invent a percentage.

### Shared Astra Max rubric and consensus §5 gates

For any **actually eligible and pre-registered** roster, Astra Max is `openai-codex/gpt-6-astra`, thinking `max`, via omp. Its rubric items are the per-request rows above, plus evidence sufficiency, absence of fabricated dimensions/geometry/checks, and the existing native/editability/export/reimport gates. It must distinguish PASS, FAIL and unassessable evidence, not turn missing measurements into PASS. Numerical measurement must come from committed check evidence, not from estimating a render. An agent verdict cannot authorize a missing input channel, a new checker or an expanded shape class.

Keep consensus §5:

- Commit roster/order, request/input commitments, owner/judge, critical dimensions/tolerances, allowed defaults, routes/caps and rubric before trial.
- A successful task is **human-adopted**, passes the existing checks, and needs no edits or completes corrections **plus headless re-verification within 300 elapsed seconds from first edit**, including waits. Record initial generation wait separately in full task elapsed, active edit time and amount changed.
- A critical dimension error or fabrication in the **first proposed handover or any later handed-over artifact** irreversibly fails that task and the pilot, even if subsequently corrected quickly. Internal repair candidates keep their existing distinct treatment. Continue the fixed roster for complete measurement unless an independent operational stop applies.
- Failed, declined, non-adopted or unassessable enrolled tasks remain non-successes in the frozen denominator. Use only the separately agreed `ceil(0.7×N)` line for a positive frozen N; **N=0 is `not_run` with no success fraction or PASS**.
- Astra judges first; the **user's final visual/adoption/critical-error verdict overrides**, and both judgments are recorded. No LLM-only adoption or fatal-error sign-off.
- DPC-019 / FreeCAD 1.1.4 headless, the same frozen implementation, existing checks and no shape/capability expansion remain mandatory. Human edits follow the existing source/native-parameter and headless re-verification route; no GUI or CAE workflow is added.

## Why the new answers do not remove E3

The distinction is between **knowing the required numbers**, **delivering the actual geometric reference to the permitted path**, and **measuring the requested behavior with the fixed checker**. These are separate prerequisites. U1 now has its box, axis, play and tape values; U2 now identifies thickness and permitted/protected surfaces; U5 now has genuine pixels. The current contract still lacks the relevant reference/image input and reference-aware checks. Supplying truthful data does not secretly create those capabilities.

Any future allowance for attachment-derived initial facts, reference-only STEP loading/comparison or raster contour reconstruction must be explicit and reviewed before a new freeze; it must not be smuggled through `observations`, a copied file, generated imports, checker gold or a rewritten request. No such change is made or authorized by this review. For this pilot under unchanged scope, the correct result is exclusion/not-run, not an easier invented substitute.

Signed: **sol** (`openai-codex/gpt-6.1-sol`).
