# VERIFY v3 — codex R1 proposal

Basis: [BRIEF](BRIEF.md), [v2 RESULTS](../cad-harness-verify-v2/RESULTS.md), [results consensus](../cad-harness-verify-v2/RESULTS-CONSENSUS.md), and the unchanged [bar](../cad-harness-verify/PLAN-CONSENSUS.md). W1/K1 fail a direct derived-diameter proxy despite passing geometry; routing and final failure labels also need attention.
This is a design proposal. Dimensions below are proposed inputs and volumes are analytical values, not measurements or performance predictions.
Consensus must explicitly retain the named eval-v1/legacy regression exceptions: “fresh only” excludes all verify-v1/v2 holdouts from scoring **and tuning**. If it also excludes the mandated fixed regressions, resolve that conflict before freezing; do not silently redefine the bar.

## Minimal fix set

- **v3 editability:** introduce only an opt-in verify-v3 profile; keep v2 Body/Tip/used-link/active-driving construction reachability. Replace the roller's derived groove-bottom-diameter requirement with a semantic requirement for the requested radial depth; identify the actual groove feature and profile boundaries rather than search a bag of numbers.
- Accept direct depth on that used groove geometry, or outer-minus-inner radii, or half the outer-minus-inner diameters. Width may be direct groove length or the difference of its driven axial endpoints. Require both operands to belong to the relevant native geometry/dependency path; normalize only typed radius/diameter units.
- Record semantic parameter, target geometry, feature/link/sketch/constraint IDs, operand values, relation, and recomputed result. An expression may contribute only through resolvable native references to those operands. Reject ambiguous/opaque relations, reference/inactive dimensions, custom scalar properties, unrelated same-valued dimensions, and disconnected/origin-hub decoys. No arbitrary arithmetic combinations or source-name/description lookup.
- Preserve direct/diametric handling and all other existing shape checks. This is a finite proof of requested dimensions in supported native representations; it does not certify every possible edit across the whole history.
- **Calibration:** author separate new dev rollers, revolutions, and annular cuts; direct-depth and equivalent-radii positives; hard-coded/uncontrolled inner-radius, wrong width, disconnected construction, reference/inactive, and unrelated-dimension negatives. Check controlled parameter changes offline to verify that accepted proof changes the intended groove. Calibrate only on these dev/decoys, never on v1/v2 or proposed test items. Proposed dev previews: OD29/bore7/H37 roller, groove Z13..19/depth1.25 (source≤2 calls); plate62×44×11/central bore D7.5 (spec1); plate82×38/four D4.5 holes/offsets8.5,6.5/thickness missing (ask1). Previews perform no CAD and allow no tuning after freeze.
- **Routing:** make the interpretation contract prominently list the actual supported family/operations and require `unsupported` for anything outside them. Preserve schema validation: an invented family remains invalid and consumes the existing parse opportunity; never relabel it as a successful unsupported response. No family/schema extension, cohort hint, deterministic gold-based routing, or hidden retry.
- **Repair instructions:** preserve the initial source/spec target and native history; supply the actual failed semantic requirement and used-geometry evidence, with instructions permitting equivalent driving relations. Do not demand a redundant derived dimension that conflicts with an already constrained depth representation. Initial generation receives only the description and generic contract; repair feedback remains separated.
- **Diagnostics:** v3 records `geometry`, `editability`, `export`, and `reimport` phases separately. Preserve true/false/null checks and add explicit pass/fail/not_reached stage statuses, so a pre-export editability miss cannot appear as an executed reimport failure. Keep exception/cleanup/PID/SHA faults as harness stops. Save exact source/repair context artifacts plus hashes for attribution.

## Proposed fresh holdout

All dimensions are mm; solids use XY center and bottom Z=0 unless the pipe path says otherwise. The defaults item omits placement intentionally. User payloads contain geometry requirements only; cohort IDs, answers, predicates, and gold formulas are excluded. The following are the single shapes repeated with independent fresh episodes; N is fixed before results.

| New item / reps / bar class | Proposed description essentials | Independent analytical gold anchor |
| --- | --- | --- |
| G1 / 2 / V1 | Hollow Z roller OD46, bore D14, H54; groove Z23..33, radial depth3.5. | V=[(23²−7²)54−(23²−19.5²)10]π=24432.5π; width10, depth3.5, shoulders and open bore. |
| G2 / 2 / V2 | Centered solid rectangular taper, 56×36 to 28×18 over H44; linear proportional shrink, no twist. | V=44(2016+1008+504)/3=51744; midpoint42×27, endpoint/midpoint sections and slopes. |
| G3 / 2 / V3 | Quarter-turn XY pipe R38, OD18, ID12; (0,0,0) +X to (38,38,0) +Y. | V=855π²; bbox=[0,47,−9,38,−9,9]; normal annular sections, constant wall, open ends. |
| G4 / 2 / V4 | Open box84×58×28, wall/bottom5; rib Y=−2.5..2.5, XZ vertices(−37,5),(37,5),(37,20). | V=84×58×28−74×48×23+74×15×5/2=57495; cavity, wall/bottom, rib connection. |
| G5 / 2 / V5 | Flange OD108,H11,bore D26; six D7 holes on PCD82 from +X; two X-long12×4 top slots, depth3, centers(±20,−23). | V=29408.5π−288; all hole centers/openings, slot floors, driving PCD82. Slots lie inside the flange and clear the bore/PCD holes. |
| G6 / 3 / V6 | Plate104×70×16; two24×16 pockets depth5 at(±25,0); six D6 through holes at X=−34,0,34,Y=±25; top outer C1.2 only. | V=112640−864π−[174×1.2²−4×1.2³/3]=112391.744−864π; internal edges remain sharp. |
| S3 / 5 / S1 | Block74×54×20; central24×18 pocket depth6; top outer four edges R3, vertical edges sharp. | Lower stock Z0..14 V=55944; Y=0 XZ fillet centers(±34,17), X=0 YZ centers(±24,17), R3; full volume recorded/agreement only. |
| A4 / 3 / Q1 | Plate98×56×13 with central D12 through bore; placement omitted. | Default center/bottom; V=71344−468π; no unnecessary clarification. |
| A5 / 5 / Q2 | Plate86×46, thickness omitted; four D6.5 corner holes, offsets X10.5,Y9. | Ask only plate_thickness; no geometry gold/answer. |
| A6 / 5 / Q3 | Plate78×48×13 with two D9 through holes, locations omitted. | Ask only hole_positions; no geometry gold/answer. |
| C4 / 3 / outside bar | Plate88×52, four D7 corner holes, offsets X11,Y10; missing thickness. | Frozen answer “厚さは12。”; V=54912−588π; centers(±33,±16). |
| C5 / 3 / outside bar | Plate84×50×10, two D8 through holes, missing locations. | Frozen answer “穴中心は(23,0)と(-23,0)。”; V=42000−320π. |
| F4 / 2 / F1 | Same description bytes as G1; inject groove-omitting native source once. | Clean gold G1; wrong V=25920π; required roller predicates must detect the missing groove. |
| F5 / 2 / F2 | Same bytes as G5; inject source omitting the hole at(41,0) once. | Clean gold G5; wrong V=29543.25π−288; required hole predicate. |
| F6 / 2 / F3 | Same bytes as G6; change only hole(−34,−25) D6→D9 in schema-valid spec once. | Clean gold G6; wrong V=112391.744−1044π; required hole predicate. |

## Authoring, order, resources, and unchanged requirements

Author descriptions/answers/rubrics and independently derived full gold/semantic targets; a separate author reviews formulas and creates native positive/negative controls. The table's anchors are not sufficient gold by themselves: freeze all existing section/wall/void/bbox/native/reimport requirements too.
Lock acceptance recipes using dev/decoys before test controls are checked. A test-control disagreement stops preparation; correct fixture-only defects from the independent description, never gold/tolerance to a measurement. If acceptance code/rules must change, reproduce on new dev and replace the exposed proposed holdout before measurement.
C4/C5 preserve first-question scoring, frozen-answer byte/SHA binding (UTF-8 without BOM: description + one LF + answer), and completion/conditional Wilson tables outside bar_met. Keep v1/v2 documents, datasets, and results immutable; neither old failures nor old successes substitute for fresh episodes.
Run order: new dev previews≤4 calls → fixed legacy4 → fresh executions of fixed eval-v1 P1–P5×2 → G1..G6,S3 in rounds1/2 → G6,S3 round3 → S3 rounds4/5 → A4×3 → (A5,A6)×5 → (C4,C5)×3 → (F4,F5,F6)×2 → independent aggregate.
Retain N/bar: V1–V5≥8/10 and each≥1/2; V6≥2/3; S1≥4/5; Q1≥2/3; Q2/Q3 each≥4/5 with no critical invention; faults established/detected6/6, final≥4/6 and each≥1/2, source/spec repair success; MVP≥8/10 and each≥1/2; legacy4/4. C/dev remain outside the score.
With three new dev previews and the fixed regressions, this is 60 episodes and 51 core observations. Planned clean/forced-repair calls=83; explicitly set cap163: source14×4 + spec13×3 + ask10×1 + completion6×4 + MVP10×3 + dev4. These are reservation arithmetic, not a usage/time prediction.
Keep v2 P≤1 separately from R≤1, CAD≤2, actual repair after a settled eligible failure when guards permit, initial450/repair450 within900 s, and one shared3 h clock through aggregate/cleanup. Retain strict actual deadline boundaries and the reviewed duration-rounding fix; no counter/time reset.
Quota stays supervisor snapshot age≤5 min, 55% soft/60% hard; missing/invalid/future/stale snapshots stop. No token-to-quota estimates. Freeze/commit code, generic prompts, dev/test, proof rules, fault candidates, order, CLI/model/AGENTS identity, and SHA manifest before any Sol call; use new version/prefix/output paths.
I would **not change** MVP/eval-v1 gold/P1 exception band or default behavior, verify-v1/v2 behavior/results, numerical geometry tolerances, native/valid-solid and independent FCStd/STEP gates, N/bar, parse-versus-repair budgets, model/tools permissions, quota/clock rules, or fault reach/injection semantics. No CAE, GUI, model judges, schema expansion, extra live retries, or calibration on scored/old items.
Risks: incorrect semantic binding could admit unrelated decoys; expression/constraint equivalence is finite; offline parameter edits do not prove all future histories; small N retains wide Wilson intervals. Undefined proof should fail explicitly, never pass by numeric coincidence. FreeCAD remains the fixed 1.1.4 headless executable.
This turn writes this proposal only; no code/data edits, tests, native runs, Sol calls, freeze, aggregate, or git operations.

codex: R1 proposal (2026-10-13 12:07:53 JST)
