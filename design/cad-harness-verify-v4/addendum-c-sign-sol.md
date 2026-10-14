# Addendum C sign-off — sol

**BLOCK — three non-numeric consistency/evidence fixes below.** Missing user numbers are on C-Q and are **not** reasons to stop offline S1 implementation.

Reviewed the complete `PLAN-V4-ADDENDUM-C.md` including C-EXIT, C-R1 and C-Q; the last two decision sections; Gemini's R1 and signature, including its re-sign. My `addendum-c-r1-sol.md` is already complete. This is a plan review only: no pilot attachments/private holdout opened, no live calls and no commit.

## User decisions accepted without qualification

- S1, then S2, then S3 implementation/review; all applicable fresh holdouts; final freeze and holdout execution; **one complete U1–U5 pilot under the final frozen implementation**. No pilot execution after S1 alone. This supersedes the staged-pilot alternative in my earlier R1.
- Existing exit gates **and all five user tasks PASS** are mandatory. No 70%-adoption shortcut, dropping a difficult task or collecting successes across versions.
- The user's stated critical values and five-minute correction rule remain unchanged. Astra Max judges first; the user's final verdict controls. Preserve human adoption, existing checks, corrections plus headless re-verification within the elapsed correction interval, and irreversible critical/fabrication failure at first proposed or later handover.
- C-R1-2's separately authorized budget/quota requirement and C-R1-3's custodian-only, once-per-attempt pre-freeze contour preparation are the correct directions. They authorize no implementation access to a pilot input and no automatic extra calls.

## B1 — remove C0's exception for changing the original holdout

**Finding:** C0 says new capabilities may enter the existing holdout if it is re-frozen before authoring. DECISIONS.md's USER 14:28 integrity clause says the existing 163-call holdout and its custody are unaffected. C-EXIT retains the existing gates; it does not authorize replacing that original cohort.

**Concrete fix:** replace C0's exception with:

> The original 163-call, unchanged-scope holdout and its custody/reservation remain unchanged. C1–C6 have separate fresh family cohorts and commitments. No C capability, item replacement, call borrowing or altered interpretation enters the original cohort. An altered/replacement original-scope trial would require a separate explicit user decision; this addendum does not authorize one.

Keep any already frozen original executable/manifest immutable. Do not change its file set or relabel an expanded result as that original trial.

## B2 — bind the raw-image fidelity chain, not only the final contour

**Finding:** C-R1-3 locks `contour.json` and a min-R report, but does not explicitly lock/check the original-image-to-contour transformation. A closed contour with a passing radius report could have lost a feature or changed the outline. Checking the generated extrusion only against that modified contour would certify the transformation against itself, not C6 fidelity against the image. A buffered polygon is not by itself proof of the user's contour or planar tool accessibility.

**Concrete fix:** add to C-R1-3:

> The custodian records and commits original image SHA, foreground/alpha mask SHA, the dev-frozen preparation recipe/software identity, pixel/physical transform and user scale, canonical contour SHA, topology/component correspondence and transformation report. The original/mask remain checker-only; the generator receives only approved typed contour/fact data. Judge both original-image/mask → canonical contour and canonical contour → output, using independently registered fidelity criteria and uncertainty. The min-R report is independently rechecked from geometry, not accepted as self-asserted metadata. No hole/component deletion, bridging, smoothing or radius modification is silently authorized. Missing acceptance values block final preparation/freeze, not dev-only implementation.

All missing numerical fidelity/scale values are on **C-Q2/Q7**, not non-numeric blockers. The preparation recipe is fixed on independent dev material before the custodian processes a pilot asset, with no interactive or automatic pilot-specific parameter search. An invalid preparation result is preserved as failure/incomplete evidence, not rerun with tuned settings in that attempt.

## B3 — make implementation lock and complete new-cycle evidence explicit

**Finding:** C-EXIT lists fresh authoring before final freeze, but should distinguish the **prior implementation/judge lock** from the final execution commitment. Its further-cycle rule also needs an explicit complete-roster/same-version rule and fresh validation for changed capabilities. Otherwise a new manifest alone could disguise validation on exposed material or aggregation of the best pilot outcomes from different cycles.

**Concrete fix:** add:

> After S1–S3 integration and reviews, lock the complete code, skill, preparation recipes and judges **before** independent family authoring/control validation. Final execution freeze then binds those unchanged locks, approved numeric cards, cohorts, custody, budgets and all five pilot inputs. A post-failure code/skill/judge change starts a separately authorized cycle: use independent fresh dev material, lock again, and obtain fresh blind validation for affected changed families before the new final manifest. Do not rerun exposed items as fresh evidence. Each pilot cycle evaluates the complete fixed U1–U5 roster once; exit requires all five successes in that same manifest/cycle. Retain every old outcome, interruption and charged cost; never combine successes from different cycles into a five-of-five pass.

Budget/quota behavior remains exactly C-R1-2. Implementers receive no original or derived pilot geometry for the next development cycle; any permitted relay of failure information must not become pilot-based fixtures/tuning. Report repeated use of the fixed user acceptance tasks as repeated acceptance attempts, not fresh independent pilot requests.

## C-Q and factual corrections — implementation continues

I updated **only the C-Q question section** of `PLAN-V4-ADDENDUM-C.md`; B1–B3 remain proposals here for consensus, not silently applied plan changes.

- Q1 now retains G3 and asks for the missing mathematical/numerical judging contract. Lack of a demonstrated general native G3 solver does **not** prove that G3 geometry is fundamentally impossible. Do not substitute G2 without an explicit user decision.
- Q2 asks for actual thickness/size/scale and whether a separate carrier is wanted; it no longer presupposes an extra rectangular plate. Q3 allows the user to say that no additional printer-envelope constraint exists.
- Q4–Q8 collect the remaining fit/play, orientation, edge-contact, thickness/preservation, image-fidelity and engraving acceptance questions without supplying defaults. Already given values are not asked again or widened.
- Q9 records pending new-family counts, gates, call budgets and model-judging reservations. Q10 records any genuinely needed resource-limit amendment; current limits apply until changed.

No numerical thresholds from either R1 draft become accepted defaults. In particular, the numeric image, engraving, ray-coverage, curvature, unchanged-dimension and face-count examples in Gemini's R1 are **not** consensus gates. Neither its extra plate assumption nor its optional generated Draft/font imports are adopted by this signature.

My prior read-only inventory observed **FreeCAD 1.1.4 / OCCT 7.8.1**, bundled Pillow **12.0.0**, and pythonocc **7.8.1.1**. Gemini's OCCT 7.7.x/Pillow 11.x statements should not be used as dependency pins. Available derivatives/building blocks are not a demonstrated G3 solver or a certified maximum-deviation judge. No installation or geometry experiment was performed for this re-sign.

## Start condition

The concrete offline work is listed in `s1-plan-sol.md`. Accepting B1–B3 supplies the non-numeric consistency rules needed for sign-off; C-Q answers may remain pending while implementing and testing on independent dev fixtures. They must be resolved before the relevant final pilot preparation/freeze. No S1 pilot, holdout authoring on unlocked code, live call, new budget or commit is authorized by this review.

Signed: **sol** (`openai-codex/gpt-6.1-sol`).

## C-R2 re-sign

**AGREE** on C-EXIT + C-R1 + C-R2 + C-Q. C-R2 resolves B1–B3. Offline S1 implementation may proceed on independent dev fixtures; C-Q remains pending for the relevant final preparation/freeze, without invented defaults. No live calls or commit authorized by this signature.
