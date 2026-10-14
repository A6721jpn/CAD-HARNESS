# Independent user-pilot screening — sol

## Decision

**U1 and U2 are scope-compatible candidates only conditionally; neither is ready for enrollment because critical acceptance values are unresolved. U3, U4 and U5 are excluded by E3.** U5 also lacks its required logo reference (E7). Do not freeze N=5 merely because five requests were supplied. A final roster and N remain pending; there can be at most two scope-compatible candidates under this screen. Unresolved candidates must not be run with agent-chosen numbers or tolerances.

This screen is independent: no other party's screen or signature was consulted. Original request text and attachments were not changed. No generation call, pilot execution or commit was made. The only native inspection was headless bounding-box measurement of U1/U2, explicitly allowed by this task.

## Evidence and interpretation

- Sources: `pilot-user-requests.md`, and **`design/cad-harness-verify-v4/pilot-user/requests.md`** with the four STEP files beside it. The intake's `pilot-user/` paths are relative to this design directory, not the repository root. The initial root-relative shell lookup failed; resolving the actual directory established that the files are present, not E7-missing.
- All five intake request bodies equal their original request bodies. Original `requests.md`: 1,920 bytes; SHA-256 `f386afc7a3a05bb9b3e5600e912bd0f7ee7df7a3fac8ee5467c65d27d24062df`, matching the intake.
- Each STEP was opened read-only for hashing; its byte count and SHA-256 match the intake's recorded commitment. U1: 2,695,956 bytes; U2: 808,687; U3: 2,127,563; U4: 7,081,133. Header inspection does not establish model validity, completeness or functional suitability.
- Scope authority: `PLAN-V4-CONSENSUS.md` §§4–5 and `design/cad-harness-verify-v3/PLAN-V3-CONSENSUS.md:53-69`. Existing families include rectangular stock/stack/shaft and the established roller, straight taper, bent tube, ribbed open box and circular flange source families. “FreeCAD can theoretically do it” is not permission to add a shape or verification capability.
- E4 is not automatically triggered by every omitted number: it excludes missing critical information that cannot be supplied through the existing clarification route. That route's frozen field IDs are in `tools/cad_verify_guard.py:139-149`; they do not express arbitrary fit/play tolerances, protected face selections, logo provenance or surface-continuity acceptance. Genuine user answers obtained **before** roster/rubric commitment may close the intake gaps without rewriting the original request. Do not add a new runtime clarification capability.
- E6's historical JSONL dependency is not imposed on these new, directly user-supplied requests. Their verified original request file is available; a missing old conversation is not grounds to discard this intake. No old context or earlier assistant-generated dimensions were imported.

### Read-only bounding-box observation

FreeCAD **1.1.4**, `Part.read()` followed only by `Shape.BoundBox`; process exit 0, stderr empty. No document, construction, fitting, export or geometric modification was performed. Both inspected input hashes were unchanged afterward. Temporary script/configuration files were removed.

| Reference | X span, mm | Y span, mm | Z span, mm |
| --- | ---: | ---: | ---: |
| U1.step | 53.957325489 | 69.768082939 | 17.623446493 |
| U2.step | 62.731982639 | 115.040563307 | 23.558035948 |

These are ordinary axis-aligned bounding-box spans in the original file pose, not optimal bounds, principal axes, wall/glass thicknesses, fit clearances or user-approved design dimensions. U1/U2 declare millimetre length units. In particular, the U2 Z span must **not** be used as glass thickness, and its file name/header alone must not be used to declare that the user attached the wrong object. Bounding boxes cannot prove contact locations or a no-rattle fit.

## Per-request E3–E7 screen

| ID | Unchanged scope class / E3 | E4 | E6 | E7 | Decision and evidence |
| --- | --- | --- | --- | --- | --- |
| U1 | Conditional ribbed-box/rectangular-stock holder, using the supplied enclosure only as an unchanged reference. The request does not require recreating its freeform surfaces. No automatic approval for conformal freeform fitting or a new assembly workflow. | Unresolved: NF13 identity/accepted interior geometry, installed fit/play and alignment tolerances. Public-source decision below. | Source available; no historical extraction needed. | U1.step present/readable, declared hash/size match. NF13 dimensional/reference dependency is not yet a committed, user-adopted input. | **HOLD; not selected, E4 unresolved** and reference closure pending. Evidence: intake U1 lines 5–15; `pilot-user/requests.md:2-3`; `pilot-user/U1.step`; measured bounds above. |
| U2 | Conditional box-with-partitions/slots in the existing ribbed-box/rectangular family. Ten unchanged glass references for acceptance do not require an assembly deliverable. No approval to generate new freeform mating surfaces or substitute a rectangular plate for the actual reference. | Unresolved: seating orientation, protected edge faces, acceptable play and edge separation. The existing runtime questions cannot settle all of these. | Source available; no historical extraction needed. | U2.step present/readable, declared hash/size match. This does not yet establish which faces are the protected glass edges. | **HOLD; not selected, E4 unresolved.** Evidence: intake U2 lines 17–27; `pilot-user/requests.md:4-5`; `pilot-user/U2.step`; measured bounds above. |
| U3 | **E3:** arbitrary freeform design-surface merging/reconstruction with G3 continuity and bounded surface deviation is outside the fixed families and checks. Not the established straight taper or bent-tube class. | The user supplied 0.005 mm absolute deviation and G3. Do not replace these with the harness's other tolerances. Surface/retained-boundary selection and a continuity verification convention are not fully specified, but E3 already decides eligibility. | Source available. | U3.step present/readable, declared hash/size match; no native surface verification was performed. | **excluded — E3.** Evidence: intake U3 lines 29–39; `pilot-user/requests.md:6-7`; `pilot-user/U3.step`. A supplied tolerance does not expand capability. |
| U4 | **E3:** offsetting an arbitrary freeform underside to a top surface, healing connected features and preserving surrounding feature dimensions is a new freeform editing class. | Nominal thickness 2 mm is supplied; thickness/preservation tolerances and target/support face boundaries are not. They cannot be invented, but resolving them would not remove E3. | Source available. | U4.step present/readable, declared hash/size match; no offset, topology edit or thickness measurement was performed. | **excluded — E3.** Evidence: intake U4 lines 41–51; `pilot-user/requests.md:8-9`; `pilot-user/U4.step`. |
| U5 | **E3:** an arbitrary Apple-logo silhouette and its CNC-constrained contour are not one of the fixed stock/source shape classes merely because the result is a thin extrusion. No logo-specific tracing/contour capability may be added. | Thickness, logo-size definition/value and contour/dimensional tolerances are missing. The supplied minimum tool R0.25 mm is not a license to invent a contour or fillet every boundary by that amount. | Original request available; no historical extraction needed. | **E7:** no exact logo asset/source/geometry has been supplied or frozen. The isolated tool-less generator cannot perform the requested web search. | **excluded — E3, E7; dimensional questions also unresolved.** Evidence: intake U5 lines 53–63; `pilot-user/requests.md:10-11`; explicit no-attachment intake. No logo was guessed, traced or generated. |

E5 does not exclude any of the five as a duplicate. This screen does not replace another real request with an easier synthetic one.

## U1 public-spec decision

**For the current acceptance rule, fetched catalogue numbers are research evidence, not automatically user-given critical dimensions. Treat U1's box-dimension acceptance as unresolved E4 until the user adopts the exact product/source/values.** The explicit product reference permits researching a source; it does not waive addendum B's requirement that critical dimensions/tolerances come from the request/context, reinforced by this task's “request text and user-given values” restriction.

A verified public specification can subsequently become an allowed, immutable reference attachment **after that user confirmation and before freeze**, with its exact source bytes/hash and product identity recorded. That requires neither generator internet tools nor invented dimensions. Merely putting a web page URL in this screen does not create such a bundled attachment or authorize its values in the rubric.

Observed public evidence: [TRUSCO Orange Book, JEJ Astage NF-13CR, JAN 4991068143975](https://www.orange-book.com/ja/c/products/index.html?itemCd=NF13CR++++++++++++++++++++++++1469), accessed for this screen. It lists effective internal width/depth/height **245 × 365 × 140 mm**, and external dimensions **287 × 435 × 145 mm**. This is a distributor's identified product listing, not an assertion that the user's box is that exact variant or that its complete interior is a rectangular prism. The internal dimensions are the relevant candidate reference, not the external ones. No manufacturing tolerance, bottom taper, corner geometry or adhesive allowance is established by those three numbers. None is adopted below as an already authorized pass value.

## Acceptance cards for the two scope-compatible candidates

These are the fixed **request-derived obligations**, not executable/final rubrics: every unresolved numerical tolerance remains a QUESTION FOR THE USER. No default ±0.01 mm, arbitrary print clearance, wall thickness, material, printer bed size, slot count for U1, font or label size is added. Attachment-derived observations remain identified as measurements, not silently promoted to user requirements.

### U1 — conditional holder card

| Critical item, from U1 | Measurement / judgment method for a later trial | Acceptance / tolerance |
| --- | --- | --- |
| Enclosure stands with its longitudinal direction vertical | Identify the user-confirmed reference direction and compare its installed direction to vertical using the reference STEP and handed-over placement/measurement evidence. | Vertical as requested. **QUESTION U1-Q2:** which reference axis/feature defines that direction, and what angular error is permitted? Longest bounding-box span alone is not sufficient authority. |
| Holder fits the actual NF13 box | Compare the installed holder/reference arrangement and adhesive stack against the user-confirmed box interior, including relevant bottom/corner/taper constraints. Bounding-box containment is necessary evidence, not proof of a close physical fit. | Fits the named actual box. **QUESTION U1-Q1/Q3:** accepted box reference and allowed installed clearance/interference; no numerical bound selected. |
| Enclosure does not rattle in the holder | Measure or have the user judge free play in the agreed seated condition using the actual reference, with an agreed translational/angular or physical assessment. Do not infer friction/contact pressure from a STEP bounding box. | No rattle as requested. **QUESTION U1-Q3:** definition, permitted play and assessment method. |
| Arrangement is regular and each position can be numbered | Inspect the arrangement's repeating relation and the usable association of a number with each enclosure position; user checks that the proposed numbering provision fulfills the request. | Regular arrangement and numbering provision; neither maximum capacity nor already embossed numbers is required by the text. **QUESTION U1-Q4:** quantitative regularity/alignment tolerance and what makes the numbering provision acceptable; no font/size/mechanism is prescribed here. |
| 3D-printable holder can be attached with double-sided tape | Existing model/export/reimport checks plus user review of the proposed tape mounting and installed fit evidence. No requirement for screws, an added tape recess or another mounting method. | The stated print/tape use must remain possible. **QUESTION U1-Q3:** tape thickness/installation allowance if it affects the critical fit. No material, load case or print tolerance is invented. |

### U2 — conditional glass-storage card

| Critical item, from U2 | Measurement / judgment method for a later trial | Acceptance / tolerance |
| --- | --- | --- |
| Accommodates 10 supplied glass pieces at once | Assess 10 unchanged reference pieces in their intended seated positions relative to the single storage-box deliverable; check capacity and mutual interference in the recorded measurement/placement evidence. | Capacity for **10 simultaneously**, an exact test count. The text does not require that a design with additional capacity be rejected or that exactly 10 separate slots exist. |
| Glass pieces are arranged standing in the requested sideways orientation | Compare confirmed reference directions and the seated arrangement against the user's intended standing direction. | Standing as requested. **QUESTION U2-Q1:** which orientation and permitted angular deviation? The attachment's Z span is not sheet thickness or a standing instruction. |
| Glass edge faces touch nothing | Identify the user-confirmed protected face set, then evaluate minimum separation from the holder and other stored pieces in the agreed seated condition using surface-distance/section evidence and user review. No contact at protected edges, including unidentified bevel/edge-transition regions, may be waved through. | No edge-face contact. **QUESTION U2-Q2:** protected face identification and minimum gap/tolerance/uncertainty that establish non-contact. No invented clearance value. |
| Pieces do not rattle | User-agreed geometric/free-play evidence or human physical judgment of the stated storage condition; do not substitute a generic tight slot or claim frictional retention from bounds alone. | No rattle as requested. **QUESTION U2-Q3:** permitted translation/rotation, acceptable broad-face contact and assessment method. |
| Printable storage-box deliverable | Existing FreeCAD/native/export/reimport checks and user assessment of the intended storage use. | No new material, wall thickness, capacity, CAE/load requirement or manufacturing-process test is introduced. Missing fit tolerance remains U2-Q2/Q3, not a chosen printing default. |

The measurement descriptions above specify evidence to agree before trial; they do not claim that a new arbitrary-surface fit/contact checker already exists or authorize implementing one. If faithful fulfillment/evaluation requires a new freeform shape or unsupported verification capability, exclude that candidate under E3 rather than silently approximating the attachment or expanding the harness.

Existing shared handover gates remain unchanged: human-final adoption, existing checks, no edits or corrections plus re-verification within 300 elapsed seconds from first edit including waits, and the irreversible critical-dimension/fabrication failure rule at first proposed or later handover. These are not substitutes for missing per-task tolerances. Astra judges first; the user's final verdict controls.

## Questions for the user

### Needed to finalize the two conditional candidates

1. **U1-Q1 — NF13 identity and reference:** Is the intended box the cited JEJ Astage NF-13CR/JAN 4991068143975, and do you approve that catalogue's identified internal dimensions as the box reference? If not, provide the exact product/source. For the requested close fit, provide/confirm the relevant actual bottom/corner/taper geometry or measurements; catalogue bounding dimensions alone do not define it.
2. **U1-Q2 — upright direction:** Which axis or identifiable enclosure feature defines the longitudinal direction to stand vertically, and what angular tolerance is acceptable?
3. **U1-Q3 — close fit, rattle and tape:** What box/holder clearance or interference and maximum enclosure play are acceptable, how should no-rattle be assessed, and what installed tape thickness/allowance must that fit include? If the criterion is human qualitative judgment rather than a numerical limit, explicitly confirm the agreed assessment before the trial.
4. **U1-Q4 — regular arrangement and numbering:** What alignment/spacing tolerance and criterion for usable per-position numbering should the judge use? The request delegates arrangement design; no particular count, numbering technology, font or label dimension is assumed.
5. **U2-Q1 — reference and orientation:** Confirm that the supplied U2.step is the intended glass reference and identify its intended standing orientation. Its recorded file name and bounding-box spans do not establish flatness, thickness or a mismatch. What angular tolerance should apply?
6. **U2-Q2 — protected edges:** Identify which faces/transitions count as the protected edge surfaces, and specify the minimum separation and tolerance/measurement uncertainty for “nothing touches.” Do not rely on an agent-selected edge clearance.
7. **U2-Q3 — no-rattle and permitted contact:** Specify acceptable play and its assessment method, and confirm where broad-face contact is permitted while every protected edge stays clear. This clarifies the existing request; it does not prescribe a clamp, liner, material or new load requirement.

### Missing inputs recorded for excluded requests — answers do not remove E3

- **U3:** no question is needed to decide current exclusion. For any separately authorized freeform work, identify the intended merge/retained boundaries and the acceptance definition for G3 and the supplied 0.005 mm bound. Do not run it in this pilot by relaxing either value.
- **U4:** no question is needed to decide current exclusion. Thickness/preserved-dimension tolerances and exact affected/unchanged feature selections remain absent; do not choose them. Clarification alone would not make arbitrary surface offset/healing in scope.
- **U5:** which exact official/user-approved logo asset, initial logo-size definition/value, thickness and contour/dimensional tolerances would be authoritative? Any future asset must be fetched and provenance/hash-frozen before an isolated invocation; the generator must not invent it or browse. Supplying that asset and those values still would not authorize the new silhouette/CNC class in the unchanged pilot.

No final roster, pass fraction or N is frozen by this file. Only the user can supply the missing acceptance facts; this screen adds no substitute tasks or requirements.

Signed: **sol** (`openai-codex/gpt-6.1-sol`).
