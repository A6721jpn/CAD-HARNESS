# CAD-HARNESS VERIFY v3 — PLAN-V3-CONSENSUS

This synthesis replaces the three R1 alternatives after grok/gemini sign-off and a supervisor local commit. Sources: [BRIEF](BRIEF.md), [codex R1](codex-r1.md), [grok R1](grok-r1.md), [gemini R1](gemini-r1.md), [v2 RESULTS](../cad-harness-verify-v2/RESULTS.md), and [v2 plan](../cad-harness-verify-v2/PLAN-V2-CONSENSUS.md). Only this document is written in this turn.
v2 scores remain historical: W1/K1 are 0/2 under their frozen gate. v3 changes requested-dimension proof, capability routing, and diagnostics; it does not claim a measured improvement.

## R2 crit — disagreements resolved

- Adopt codex's complete fresh G/S/A/C/F specification and independently checked formulas. Grok's alternative roller arithmetic is valid but its other shapes are unspecified; Gemini's table omits several placements/slots/rib details. They are not additional scored variants.
- Adopt grok's feature-attached depth proof and codex's typed difference relations; adopt Gemini's acceptance of equivalent representations. Reject a numerical OR-list of depth/derived diameter/radius, and reject unconditional half-width matching: the controlling geometry and relation must be proved.
- Reject Gemini's old DV1–DV6 calibration; only newly authored v3 dev/decoys may calibrate v3. Old verify-v1/v2 test items are excluded from both scoring and tuning.
- Correct the family list from the actual build-schema: rect_prism, rect_stack, stepped_shaft. A stepped_shaft with holes can pass JSON schema but fail the compiler's unsupported_shaft_operation capability check. Adopt grok's bypass of parse for this proven capability failure; codex's parse rule remains for genuine schema/format errors. No generic swallowing of validation errors.
- Resolve regression scope explicitly: fixed eval-v1 P1–P5 gold/P1 exception band and legacy A/B controls are the named regression exceptions to fresh-only, required by the unchanged bar. Reject replacement M1–M5 gold. They get fresh executions; previous results are not reused.
- Retain source/repair context archival from codex/Gemini, limited to separate episode artifacts with hashes. Reject full context expansion inside driver-run.json; other contexts retain existing hashes. This is part of diagnosing prompt versus model failure, with no extra model calls.
- Retain existing expected/actual geometry diagnostics during repair, including volume when it is a failed check; reject grok's blanket volume omission. Such feedback is distinct from prescribing an unstated derived value as a required driver or supplying full gold/correct source.

## Probe・成果物gate

Implement an opt-in verify-v3 profile and a new v3 evaluator/aggregate namespace. mvp-v1, verify-v1, verify-v2 and their default code paths remain unchanged. Reuse v2 Body/Tip/used Profile/Sections/Spine/ReferenceAxis resolution, including actual partial selections.
Seed consumed real geometry and uniquely resolved native axes. Only active/driving typed constraints connect geometry IDs≥0. Negative origin/axis/external IDs are anchors, never hubs; Radius/Diameter/unary constraints do not create edges. Reachable construction may supply evidence; disconnected/reference/inactive/custom scalar values cannot.
v3 gold identifies primary user-stated dimensions and their roles before fixtures are measured. For the roller require OD, bore, length, groove width, and radial depth. The derived bottom diameter remains geometric gold, not an independent required driving number. Preserve other profiles' existing native dimension checks and primary-dimension selection discipline.
OD/bore/length retain existing direct/typed diameter-radius handling. Replace roller width/depth flat-value checks with mandatory role proofs: depth=d; depth=outer_radius−inner_radius; depth=(outer_diameter−inner_diameter)/2; width=operative groove length or the difference of its driven axial boundaries. Centered half-width is allowed only with an active symmetry relation proving both boundaries and their center.
A direct depth distance must constrain a radial span between the actual outer and bottom boundaries; origin-only ends or a free chord do not suffice. Difference operands must control those same consumed groove/stock boundaries, with axis/placement resolved. Matching values elsewhere in even a reached sketch do not prove the role. Inoperative Length2/default properties do not count as groove controls.
Expression support is limited to resolvable references/aliases to accepted native drivers; no arbitrary expression search/evaluation or custom-property number harvesting. Record role, target geometry, feature/link/sketch/constraint/property path, operand types/values, relation, and recomputed mm result. Unresolved/ambiguous proof fails explicitly, not by numerical coincidence.
Calibrate on new dev positives: direct depth, radius/diameter differences, revolved profiles, annular cuts, construction depth lines, expression-linked outer radius, and symmetric half-width. Negatives: uncontrolled bottom boundary, wrong role/width, unrelated connected dimensions, disconnected loops/rays/unused sketch, inactive/reference dimensions, origin-only depth, and inoperative native properties.
Use dev roller OD29/bore7/H37, groove Z13..19/depth1.25; additional equivalent representations use that dev geometry, never a scored item. On disposable dev copies verify depth +0.5 and width +1 against independent analytic geometry and normal recompute. Live scoring does not add parameter-edit runs and does not certify all history edits.
Retain ±0.01 mm, axis1e-6, volume relative1e-4, optimal bbox, single valid solid/Body/native Tip/used sketches/normal recompute, all requested sections/walls/voids/cuts, and independent FCStd+STEP gold checks. Generation and verification own separate headless processes; full bbox/full volume agreement, document close, PID recovery, and normal exit remain mandatory.

## Unsupported routing・Parse/CAD repair・時計

Generic v3 interpretation instructions list the actual schema families and compiler operations; unrepresentable features must yield unsupported. No new schema family, capability, fixture/case/description lookup, or grading hints in initial payload/context.
Initial source-enabled interpretation accepts a well-formed unsupported response directly. Also allow source fallback before any CAD for JSON-schema-valid specs whose existing validator returns exactly unsupported_shaft_operation; validate schema first and record raw response, schema_valid, compiler_supported, capability code, and unsupported_origin=model|validator. This is a real unsupported→source path; report both origins separately.
The capability allowlist contains only unsupported_shaft_operation. Unknown family/field, malformed/duplicate/nonfinite JSON, or any other validation failure uses existing P handling. Do not use startswith(unsupported), infer capability from gold, or rewrite invalid output into a successful model response. Non-source routes retain existing validation handling; capability fallback is forbidden after the first CAD attempt.
Repair receives the actual failed source/spec, semantic role and driver evidence, and actual diagnostics. Explain acceptable equivalent driving forms; do not prescribe an unstated derived diameter, supply correct source, or add full gold models. Preserve the first actual CAD target during R.
P≤1 shared across initial/repair responses; R≤1 separate; v3 CAD≤2. Source cap4, spec3, ask1, completion4; default MVP limits remain unchanged. No second repair, correct-source splice, repeated fault injection, or budget reset.
Settled eligibility remains repair_reason=None and no harness_failure: next_actor=sol, diagnostic build/probe miss, no Probe exception, closed/exited, integer cad_exit; build miss needs measurement/predicate evidence. In-schema editability misses are eligible. Fault establishment additionally requires completed script, exit0, native-valid candidate and the designated geometry predicate miss.
If guards permit after a settled eligible miss, actually invoke R once. Record eligible/invoked/success/not-attempted reason. An eligible missed invocation without a guard reason is a harness stop. repair_time_reservation_lost is an episode time stop with partial data; the shared guard may permit later episodes, without resetting clocks/counters.
Keep 900 s/episode and initial450+repair450, including C question/answer and reimport. Repair reservation: R180+unused P60+build/export90+reimport90+cleanup30. Reserve cleanup30 in initial; clip each child to stage/episode/shared remaining time and FreeCAD≤300.
All dev/legacy/MVP/core/C/save/cleanup/aggregate share one monotonic10800 s clock. Start an episode only with ≥960 s remaining and required current/future call reservations. Keep exact saved timestamp equality, strict deadline/ended_elapsed_s boundaries, and the reviewed absolute1e-6 duration-rounding check. No clock substitution or deadline extension.

## Failure-phase diagnostics

New v3 classes: geometry_pre_export if geometry predicates fail; editability_pre_export if geometry passes but native/editability fails; export_failure for an actual export failure; reimport_verification_fail only for an actual independent reimport failure. Geometry takes precedence when both geometry and editability fail; preserve both predicate details.
Record build/geometry/editability/export/reimport stage statuses pass|fail|not_reached; unexecuted stage measurements are null. A diagnostic FCStd saved after a probe miss is not proof that STEP export or reimport ran. The all-gate pass is still false. Existing exception/launch/cleanup/PID/SHA stops remain harness stops.
Save the exact user payload and developer context actually submitted for source and repair calls as new per-call artifacts, bind their UTF-8 bytes to the existing prompt/context hashes, and store only paths/hashes in driver-run.json. No reconstruction from changed files, credential/config dump, or extra call. v1/v2 failure labels and reports are immutable.

## Clarify→凍結回答→完成（bar外）

A5/A6 each5: one actual question call, CAD0/P0/R0. Only the required field ID scores; invention/unsupported/invalid/other fields score0. A4 must apply default XY center/bottom Z0 without unnecessary questioning and pass final gates; later repair cannot rescue a wrong initial default/question score.
C4/C5 each3 are independent inputs. Save/fix the first-question artifact and rubric result; return the frozen answer only for the correct question. Wrong questions/inventions remain completion misses/not_reached in planned denominator3; ordinary model misses are completed observations, guard/time stops are incomplete.
Completion payload is description UTF-8 bytes + exactly one LF + answer bytes, no BOM or terminal LF in either file. Gold.description equals the concatenated payload; bind description/answer/payload SHA in gold, manifest, and reports. No session-resume machinery or added field-ID/gold/fixture hints.
Use the same 900/450 clocks/P1/R1/CAD2; extra clarification after the answer is a miss. Report initial question, post-answer first attempt, final gates, calls/usage/wall, completion per planned3 and conditional completion per correct question with separate Wilson95%. C/dev do not enter bar_met; common integrity/harness/guard stops still apply.

## Fresh holdout・解析gold（mm、体積mm³）

The following descriptions are verbatim bases. Append XY中心、下面Z=0。 then 単位mm。他の加工なし。 except G3/A4 omit the placement sentence. F4/F5/F6 copy the finished G1/G5/G6 description bytes exactly; do not append again or put injection text in payloads. No dimension-column, role, cohort, answer, or grading annotation is added.
G1–G5/F4/F5 require unsupported→source, including the logged validated-capability origin. G6/S3/A4/C completion/F6 are supported; no schema expansion. All shapes/dimensions below are proposed fresh inputs; formulas are analytic, not observations.

| ID / N / bar class | 説明本文 | Analytic gold / separate frozen answer |
| --- | --- | --- |
| G1 / 2 / V1 | Z軸の中空ローラー。外径46、長さ54、貫通穴直径14。外周のZ=23..33に幅10、半径深さ3.5の全周溝。 | V=24432.5π; bottom OD39 geometric consequence; sections Z11.5/28/43.5, shoulders/open bore; width10/depth3.5 role proofs. |
| G2 / 2 / V2 | 中実の四角テーパー。Z=0は56×36、Z=44は28×18。中心一致、ねじれなし、寸法は高さに対して線形に比例縮小。 | V=51744; Z22 section42×27; endpoint/midpoint sections, centers/directions/slopes. |
| G3 / 2 / V3 | XY平面で90度曲がる管。中心線R38、外径18、内径12。(0,0,0)から+X向きに出て(38,38,0)へ+Y向きで到着。両端開口、一定断面。 | V=855π²; bbox=[0,47,-9,38,-9,9]; initial/45°/final normal annular sections, wall/cavity. |
| G4 / 2 / V4 | 上面開口の箱。外形X=-42..42,Y=-29..29,Z=0..28、壁と底5。Y=-2.5..2.5の三角リブ、XZ頂点(-37,5),(37,5),(37,20)。 | V=57495; cavity74×48, wall/bottom5, rib thickness5/triangle/connection. |
| G5 / 2 / V5 | 円形フランジ外径108、厚さ11、中央通し穴D26。PCD82にD7通し穴6個、+Xから60度刻み。上面の長手Xの12×4・深さ3の矩形溝を中心(-20,-23),(20,-23)に。 | V=29408.5π−288; centers(41cos(kπ/3),41sin(kπ/3)),k0..5; floorsZ8; driving PCD82. |
| G6 / 3 / V6 | 104×70×16の板。上面に24×16深さ5の矩形ポケットを中心(-25,0),(25,0)に。D6通し穴をX=-34,0,34とY=-25,25の6点に。上面外周だけ脚1.2の面取り。 | V=112391.744−864π; floorsZ11, holes/voids/sharp inner edges, top-outer C1.2 only. |
| S3 / 5 / S1 | 74×54×20のブロック。上面中央に24×18深さ6の矩形ポケット。上面外周4辺だけR3、垂直辺は鋭く残す。 | Stock scope [-37,37]×[-27,27]×[0,14], V=55944; local R3 sections below; full volume record/agreement only. |
| A4 / 3 / Q1 | 98×56×13の板。中央にD12の通し穴。 | Default XY center/bottomZ0; V=71344−468π; initial no unnecessary question and final all gates. |
| A5 / 5 / Q2 | 86×46の板。四隅D6.5通し穴、穴中心は外形からX10.5 Y9。 | Rubric plate_thickness only; no geometry gold/answer. |
| A6 / 5 / Q3 | 78×48×13の板。D9通し穴2個。 | Rubric hole_positions only; no geometry gold/answer. |
| C4 / 3 / Q2 completion | 88×52の板。四隅D7通し穴、穴中心は外形からX11 Y10。 | plate_thickness; answer 厚さは12。; V=54912−588π; centers(±33,±16). |
| C5 / 3 / Q3 completion | 84×50×10の板。D8通し穴2個。 | hole_positions; answer 穴中心は(23,0)と(-23,0)。; V=42000−320π. |
| F4 / 2 / F1 | G1と同一bytes。 | Inject one contract-valid groove-omitting native source; clean G1 gold; wrong V=25920π; designated roller miss. |
| F5 / 2 / F2 | G5と同一bytes。 | Inject native source omitting the (41,0) hole once; clean G5 gold; wrong V=29543.25π−288; designated holes miss. |
| F6 / 2 / F3 | G6と同一bytes。 | After schema/semantic-valid spec, mutate only (-34,-25) hole D6→D9 once; clean G6 gold; wrong V=112391.744−1044π; designated holes miss. |

G1: [(23²−7²)54−(23²−19.5²)10]π=(25920−1487.5)π. G2: t=z/44, 44∫₀¹(56−28t)(36−18t)dt=51744. G3: π(9²−6²)×38π/2=855π²; P=((38+u)sinθ,38−(38+u)cosθ,v),36≤u²+v²≤81,θ∈[0,π/2] gives its bbox.
G4:84×58×28−74×48×23+74×15×5/2=57495; rib joins floor/wall at boundaries with no overlap volume. G5:π(54²−13²−6×3.5²)11−2×12×4×3=29408.5π−288. Slot radial range √(14²+21²)..√(26²+25²) clears bore13/outer54; lower hole Y gap 41√3/2−25>3.5.
G6:104×70×16−2×24×16×5=112640; holes864π; chamfer loss=(104+70)1.2²−4×1.2³/3=248.256. Holes/pockets are mutually disjoint and clear the outer band. S3 floorZ14 is below fillet bandZ17..20, so stock volume74×54×14=55944 is exact.
S3: Y0 XZ centers(±34,17), X0 YZ centers(±24,17), R3. At Z18.5 outer bounds are ±(34+1.5√3)/±(24+1.5√3); cavity halfwidths12/9. Corner-patch volume is not gold. A4:98×56×13−π6²×13. C4:88×52×12−4π3.5²×12. C5:84×50×10−2π4²×10.
Other bboxes as (Xhalf,Yhalf,Z0..H): G1=(23,23,54),G2=(28,18,44),G4=(42,29,28),G5=(54,54,11),G6=(52,35,16),S3=(37,27,20),A4=(49,28,13),C4=(44,26,12),C5=(42,25,10); surviving exterior extrema establish them. Fault volume deltas: F4 +1487.5π; F5 +134.75π; F6 −180π.
Full gold freezes all required faces/sections/bore/wall/void/finish/native-role/recompute/reimport predicates, not only these volume anchors. No counts of faces/edges/features substitute for requested geometry.

## Bar不変・順序・call枠

G1–G5→V1–V5 ≥8/10 and each≥1/2 plus the actual fallback path; G6→V6≥2/3; S3→S1≥4/5; A4→Q1≥2/3; A5/A6→Q2/Q3 each≥4/5 and zero critical invention. No post-result change to N/fractions.
F4/F5/F6→F1/F2/F3 establishment/designated detection6/6; final all gates≥4/6 and each≥1/2; both source and spec R success. Generation failure/not_reached stays in planned6; report pass/established and natural repair success/eligible separately. reached/injected true only when replacement is actually returned; target_missing retains false and its reason.
Fixed eval-v1 P1–P5×2 freshly executed under a new prefix stays ≥8/10 and each≥1/2 with original gold/P1 exception band; legacy A/B good/broken4 stays4/4 with no extra legacy Sol. bar_met requires core+regression51 complete, all success gates, consistent version, guard/deadline compliance, and no false pass. C/dev scores remain excluded.
Order: one3 h clock → new dev-live3 → legacy4 → eval-v1 P1,P1,P2,P2,P4,P4,P5,P5,P3,P3 → clean G/S → A → C → F → independent aggregate. Clean r1/r2 each G1..G6,S3; r3 G6,S3; r4/r5 S3; then A4×3,(A5,A6)×5,(C4,C5)×3,(F4,F5,F6)×2. Pre-register every ID/order/route/cap.
New dev previews: roller29/7/37,Z13..19,depth1.25 interpretation+source≤2; plate62×44×11/central D7.5 spec1; plate82×38/four D4.5 corner holes/offsetsX8.5,Y6.5/thickness missing ask1. All are unscored/P0/R0/CAD0; new dev only, no post-freeze tuning. Total60=dev3+legacy4+MVP10+clean18+A13+C6+F6.
Recomputed baseline83 calls=dev4+MVP10+G1–G5 20+G6 3+S3 5+A4 3+A5/A6 10+C12+F4/F5 12+F6 4. This reserves forced-fault R, no clean R/P; it is not an observation or quota/time forecast.
Explicit maximum163=source14×4+supported13×3+ask10×1+C6×4+MVP10×3+dev4. source14=G1–G5/F4/F5; supported13=G6/S3/A4/F6. Compute these sums from frozen run-order and reject mismatch; do not merely copy a previous cap or auto-increase it.
Independent run/aggregate bind expected IDs/N/roles/order/version/SHA and all artifact/driver identities. New names: version verify-v3-reviewed-r1, host prefix host-verify-v3-reviewed-r1, aggregate-verify-v3-host-reviewed-r1.json/csv. No overwrite or warm-start; an -aggfix version cannot start live runs.
Report initial/final phase statuses/gates, actual fallback origin, P/R purposes/stages/CAD attempts, fault SHA/reach/detection, reasons, failed-phase distribution, wall median/p95/max including misses, and provider fields individually summed with missing null retained. Wilson95%(z1.96) applies only to completed fixed cohorts/parts; no heterogeneous pooled general success rate.

## 実装・authoring・freeze・停止

Codex owns generic v3 implementation, the table's verbatim Japanese descriptions, separate answers/rubrics, schema/role gold and analytic expressions/numbers, and run-order. Grok independently re-derives every gold/formula and reviews requested-role/capability boundaries before measurements. Gemini authors hand-made native positive/negative/fault controls independently from descriptions, plus the new dev equivalence/decoy matrix; no generator outputs serve as hand-fixture gold.
Lock semantic rules using only new dev calibration before holdout controls are checked. Correct fixture-only defects from descriptions/analytic gold, not measured values. A holdout check requiring a rule/code change stops preparation: reproduce on new dev, recalibrate, and replace the exposed proposed holdout; do not tune on it. Record actual authors/independent reviews.
Phase2 is Sol-free. Minimum mocks cover semantic-role/decoy isolation, schema error versus the one allowed compiler-capability route, actual R after P/settled in-schema failure, episode time stop/shared clocks/caps, phase not_reached, and C byte/rubric contracts. TEMP follows test_support. Check new native positives/negatives/designated faults and legacy4; existing v1/v2 unit/profile regressions may run unchanged, not as v3 calibration.
Grok and Gemini review implementation/data once; address necessary findings and checks. Supervisor then local-commits the signed plan and selected implementation/data and freezes everything before any Sol, including dev. Do not invent unavailable author/reviewer sign-offs.
SHA freeze includes code/skill/build+gold schemas/Probe/generic contracts/CLI/model settings/inherited AGENTS, all dev/test/answers/rubrics/role rules/fault candidates and order. Record version/commits/manifest digest. Preserve old manifests and results byte-identically. Gold never enters initial context; compiler/driver may not look up case/description hash to generate a part.
FreeCAD only C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe headless; no GUI/CAE. Sol remains gpt-6.1-sol/xhigh/tools disabled/read-only under the frozen CLI identity. Supervisor alone runs Phase3 and supplies actual quota snapshots.
Before every actual model call inspect supervisor snapshot: missing/invalid/future/age>300 s stops; ≥55% soft stop prevents new calls pending supervisor judgment, ≥60% hard stop. Record actual percentage/time/identity/SHA, never infer percentage from tokens or reset budgets.
Quota/shared deadline/900 s/reservation exhaustion stops calls; preserve partial observations/all planned IDs; incomplete core means unmet bar and no incomplete-cohort CI. No additional N, adaptive calls, hidden retries, manual result replacement, or deadline grace.
First confirmed launch/save/export/reimport/Probe exception/cleanup/unrecovered PID/SHA mismatch/false-pass or harness defect stops the version. Model format/semantic/repair misses remain observations; missing semantic proof without an implementation exception is a native predicate miss eligible under the normal rules.
Gold disagreement: analytically re-derive from the frozen description and report expected/actual/formula. Arithmetic error in gold → STOP, no self-edit. Pre-Sol fixture/Probe defect → log and restart the entire offline batch; any holdout-driven rule/code adjustment follows the replacement rule above. After freeze, any measurement-affecting fix preserves failures and requires a new signed version and unused holdout.
NOT changed: eval-v1 gold/P1 exception/bar/eval_mvp behavior and default clarification retry; all v1/v2 data/code-path behavior/results; compiler schema and supported operations; numerical geometry tolerance/optimal bbox/full reimport and native integrity gates; N/bar, P/R/CAD/time budgets, model/tool permissions, quota policy and actual fault injection semantics. No LLM judge, CAE, positive-source repair splice, or tuning on old/scored items.
Risks: role misbinding/false-positive arithmetic, finite expression/constraint coverage, tight reserved time, and wide small-N intervals. Dev parameter edits validate supported proof forms; this bar certifies the listed single-Body tasks and bounded repair/frozen answers, not complete parametric-history behavior.

grok: AGREE 2026-10-13 13:05:02 JST

gemini: AGREE 2026-10-13 12:58:15 JST

codex: AGREE 2026-10-13 13:03:43 JST
