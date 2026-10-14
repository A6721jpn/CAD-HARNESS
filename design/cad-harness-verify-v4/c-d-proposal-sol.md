# C-D delegated proposals and review — sol

Status: independent proposal for three-party agreement, not execution authorization. Authority: `DECISIONS.md` USER 17:28 and addendum C, C-A2. Reviewed `c-d-proposal-gemini.md` (sections a–e). Proposed numbers below are delegated engineering choices, not measurements or user-specified manufacturing tolerances.

This review does not use pilot attachments, private holdout material, model calls or new CAD runs. S2 remains under review; S3 has not started. No commit.

## (a) U5 lenient fidelity — BLOCK as written; AGREE on the proposed numerical bounds

Gemini lines 17–29 add an unestablished separate-leaf topology, an unsupported pixel conversion, and an ambiguous claim that Astra performs geometric verification. The USER confirmed a cut-out logo part, not a surrounding plate; that does not by itself waive the existing solid-count gate or establish a component count. A nominal 50 mm height alone cannot determine pixels/mm: the committed foreground bounds and transform are needed.

Proposed C-D(a):

| Comparison | Minimum IoU | Maximum symmetric Hausdorff distance |
| --- | ---: | ---: |
| Original committed mask → canonical contour | 0.90 | 1.50 mm |
| Canonical contour → actual CAD material cross-section | 0.92 | 1.00 mm |

These are deliberately lenient acceptance choices at the registered nominal logo height of 50 mm, not predictions about the supplied raster. The nominal thickness remains 3 mm; both dimensions remain operative parameters. The former 100 × 100 mm plate is void. No leaf-gap, pixel-count, aspect-ratio or component-count estimate is adopted.

Required interpretation:

- Use the same frozen physical coordinate transform for both legs. No output-dependent rescaling, registration or best-fit alignment. Another requested nominal size needs its transform/card registered before preparation and freeze, not a wider bound selected after seeing an output.
- The CLI computes bounded metrics: IoU lower bound must meet its minimum; Hausdorff upper bound must meet its maximum. Insufficient numerical evidence is UNVERIFIED, not PASS. Astra judges the evidence and visual/request fidelity; it does not replace deterministic metrology. The user's visual decision remains authoritative.
- Minimum concave tool radius remains **at least 0.25 mm on actual output**, with the existing tool-access checks. Do not substitute R0.245 or pass a bound whose lower endpoint is below 0.25 mm.
- IoU alone cannot prove feature retention. Preserve the registered components, holes, relative placement and contour/material correspondence. No implicit smoothing, deletion, bridging or merging. Any allowed boundary approximation must be specified in the dev-frozen recipe and pass both fidelity legs and topology checks.
- Custodian-only, once-only preparation and its original/mask/software/transform/contour/topology/transformation hashes remain required. No implementer inspection or trial-dependent recipe adjustment.
- If preparation reveals disconnected retained material incompatible with the existing solid-count gate, report that conflict before freeze. Do not infer a detached-leaf exception, add a carrier, or change the requested deliverable. That topology-policy decision is outside delegation of fidelity thresholds.

These fidelity bounds are not dimensional/manufacturing tolerances for the 3 mm thickness, the 50 mm height, or any U1/U2/U4 dimension. They do not guarantee manufacturability or recognizable intent; native validity, tool constraints and human judgment remain separate gates.

## (b) Engraving size/depth — BLOCK as written; AGREE on 5.0 mm and 0.6 mm nominal defaults

Gemini lines 36–51 expand delegation from size/depth to mandatory placement rules and assert unsupported printer/CNC guarantees. The USER did not supply a nozzle, layer height, machining setup or strength criterion. An engraving depth alone cannot establish remaining-wall strength. Neither the ranges 3–8 mm / 0.3–1.0 mm nor the 1.5 mm standoff and ±0.2 mm allowance follow from the decision.

Proposed C-D(b):

- Default `height_mm = 5.0` in the registered font-outline convention; default recess `depth_mm = 0.6`. These are agent-chosen CAD targets, not a claim about universal legibility, printable operating ranges, structural integrity or a one-pass CNC operation. Keep them operative parameters; do not promise an unvalidated range.
- Use a licensed, digest-bound registered font and its actual outlines/counters. Unsupported glyphs require an explicit failure/clarification, not substitution. Production uses `fontTools` and native FreeCAD geometry; `_engravings` does **not** run FreeType. A separate renderer may be an independent development control.
- Placement is skill judgment constrained by actual geometry and the request: associate labels with their intended slots, keep the engraving on supported material, avoid fit/contact regions and unintended through-cuts, and preserve required dimensions. Global `Zmax`, a mandatory array-axis orientation, a fixed edge standoff or a universal numbering sequence is not introduced by this delegation. Expected labels and slot associations come from the registered request/card, not a judge's guess.
- If these defaults cannot fit safely, report infeasibility or obtain clarification under the frozen policy. Do not shrink, relocate or deepen them after inspecting pilot results to recover a pass.
- Bind the intended text/font/height/depth and slot mapping to the acceptance record. Compare the output to that intent, not merely to a model's own declarations. Existing `_engravings` reconstructs its expected cutter from the plan and requires `minimum_removed_mm3` and `depth_tolerance_mm` (`tools/cad_verify_v4_judges.py:596–652`); that establishes geometric consistency, not independently the correctness of the requested labels or these defaults.
- Register valid numerical-check bounds and volume evidence, including retained material below the recess; uncertain geometry remains UNVERIFIED. Do not relabel an unapproved ±0.2 mm manufacturing allowance as numerical error. Actual glyph fit, correct mapping and readability still require the frozen semantic/visual rubric.

No new user number is needed to choose the two delegated nominal defaults. No new physical tolerance or critical-error classification is silently assigned to them.

## (c) Fresh family counts/gates/budgets — BLOCK as written; AGREE on 43 generative items plus four admission controls

Gemini lines 66–74 leave the four-item stratum's gate ambiguous, do not explicitly exercise finite-face replacement in C4, reserve an unexplained fourth generation call for C4/C5, and omit model-judge calls. Its current-quota and weekly-capacity projection has no supporting usage ledger; a call count cannot be converted into a weekly quota percentage.

Proposed C-D(c), with no pooling across families:

| Family | Independently authored strata and counts | Full-pass gate; minimum per stratum | Generation-call ceiling | Astra-judge ceiling |
| --- | --- | --- | ---: | ---: |
| C1 STEP/reference fixtures | Prismatic references 4; stepped/oriented references 3; curved/irregular references 3, using the registered fixture operations | 8/10; respectively 3/4, 2/3, 2/3 | 30 | 10 |
| C2 contour-extrude | Convex profiles 3; connected-material profiles with holes/nested loops 4; notch/tool-access cases 3 | 8/10; respectively 2/3, 3/4, 2/3; additionally 10/10 verified minimum-R/tool constraints | 30 | 10 |
| C3 engraving | Numeric arrays 3; registered alphanumeric labels 3; dense layouts 2 | 7/8; respectively 2/3, 2/3, 2/2 | 24 | 8 |
| C4 direct edit | Planar/oblique offsets 2; curved offsets 2; finite-planar-face replacement/reconnection 2; adjacent-feature preservation cases 2 | 6/8; at least 1/2 in each stratum | 24 | 8 |
| C5 surface rebuild | Two-patch curved rebuilds 3; trimmed multi-patch spline rebuilds 4 | 5/7; respectively 2/3 and 3/4; every success verifies G2 and maximum deviation ≤0.005 mm | 21 | 7 |
| Admission controls, separate from generation | Corrupt STEP 1; open contour 1; independently proven fixed-geometry/tool infeasibility 1; unavailable registered glyph 1 | 4/4 correct pre-generation detection/refusal, with no generated deliverable | 0 | 0 |
| Total | 43 generative items + 4 controls = 47 entries | All family gates independently required | 129 | 43 |

The finite expansion reservation is therefore **172 non-exempt model invocations**, not 152. This is a proposal within the delegated additional-family budget, not a live allowance created by writing this file.

Rules needed to make those numbers meaningful:

1. Each complete generative request has one initial response, at most one shared P1 format repair and at most one R1 geometry repair: **at most three** generation invocations and two CAD attempts. No fourth response, extra clarification round or judge retry is implied. If the final S3 contract genuinely needs another route, agree and freeze that route/budget before authoring; never introduce it after exposure.
2. Reserve one Astra Max adjudication per generative entry, with no re-score to improve the outcome. A malformed/missing verdict is UNVERIFIED/non-success. A deterministic terminal failure may make the model judgment unnecessary, but its unused reservation is not transferred. Judge calls are charged and quota-checked like generator calls.
3. The four controls are deterministic admission checks, not four successful generations or eight justified model calls. Independently prove their expected invalidity. A difficult but valid request is not an admission fault; do not relabel it after observing a failure. If semantic model refusal is to be tested instead, register a separate model-refusal stratum and its call route before sealing.
4. Enrolled failures, refusals, UNVERIFIED, timeouts and unstarted cases remain in their registered denominators. For C2's additional 10/10 tool gate, missing/unverified radius or access evidence is not a pass and does not reduce the denominator. There must be zero falsely accepted invalid/critical-violating outputs in every family.
5. A family success means all of its frozen validity, native/export/reimport, operative-editability, dimensional, contact/clearance, topology and semantic gates as applicable—not only its aggregate threshold. Sampled curved thickness or sampled surface distance is not a global certificate. An unsupported certificate yields UNVERIFIED, not a weaker pass criterion. G2 plus deviation is not a general “Class-A” guarantee.
6. Freeze integrated code/skill/policy/recipes/judges/protocol first; then independent author/reviewer/custodian create and validate fresh requests, analytical gold and native controls. Reviewer validation includes positive controls and decisive violations of the case's gating metrics, with identities/hashes retained. No generation-model validation; no developer/pilot/old-holdout reuse, rewordings or scalar-only mutations. Final freeze binds exact order, cards, controls, denominators, custody and finite reservations. Any defect/exposure follows the existing retirement/new-cycle rule.
7. Keep the original **163-call unchanged-scope holdout**, its clocks, allocation and custody untouched. Pilot and benchmark reservations are separate; no borrowing, smoke, retake, overload hunt or automatic unlimited loop. The USER's absence of an upper additional-family ceiling does not remove per-manifest ceilings.
8. Before each live admission, require the frozen identities, full capture health, a valid reservation and fresh quota evidence: consult/admit no new calls at 55%; stop at 60%; missing/stale quota also stops. Record operational interruption and preserve unstarted entries. Current usable quota and actual token cost are unknown here; delete the “10–12% weekly capacity” prediction.

Proposed generator: **`openai-codex/gpt-6.1-sol`, thinking `xhigh`**, matching the current holdout identity in `tools/cad_verify_v4_s1.py:31–36`. Proposed judge: **`openai-codex/gpt-6-astra`, thinking `max`**. Pilot remains Astra Max generation plus Astra Max judgment and authoritative user visual/adoption; disclose that same-model relationship. No model is called by this proposal.

These are small, coverage-oriented cohorts. Their thresholds do not establish a population reliability rate or replace mandatory success on all five real requests.

## (d) Time limits — BLOCK as written; AGREE on extended subcaps as policy choices, with coherent enclosing clocks

Gemini lines 81–87 do not provide per-operation timing evidence. Dividing 22 tests' suite duration by 22 is not a measurement of CAD-operation latency: tests can run different numbers of operations and include unrelated overhead. The quoted S2/S3 ranges are not established by those suite totals; S3 is not implemented. Remove or label those claims as unmeasured estimates, not empirical results.

Actual existing development evidence, read without rerunning CAD: under `reports/verify-v4-s2-dev-20261014T085548Z/`, `offset-complete/ledger.jsonl` records compile **1.391 s**, verify **1.593 s**; `smooth-complete/ledger.jsonl` records compile **1.797 s**, verify **2.250 s**. These are specific supervised process wall intervals, not per-kernel-operation latency, a worst-case bound, a manual baseline or a time-saving result.

Proposed C-D(d) for the integrated expanded-capability profiles only:

| Active-work limit | Proposed seconds |
| --- | ---: |
| Episode | 1200 |
| Initial stage | 600 |
| Repair stage | 600 |
| Initial model-response cap | 450 |
| R1 model-response cap | 180 |
| Shared P1 response cap | 60 |
| Initial native CAD operation cap | 450 |
| Repair native CAD operation cap | 180 |
| Initial verification/reimport operation cap | 300 |
| Repair verification/reimport operation cap | 120 |
| Reserved cleanup | 30 |

The extension is an engineering allowance, **not** a measured requirement or a promise that S3 fits. The initial-stage subcaps are ceilings, not additive entitlements: every operation is clipped to the remaining stage/episode time after required reserves. The complete repair reservation is 180 + 60 + 180 + 120 + 30 = **570 s**, fitting the proposed 600 s stage; omit the P1 reserve if already consumed. Update stage admission and all downstream repair/reimport reservations together, not only the fields in Gemini's table. Initial processing may receive less than a subcap after earlier work; exhaustion is a scored failure, not permission to reset time.

Keep P1/R1/CAD counts unchanged. Preparation, verification, capture and cleanup inside an episode consume its applicable active clock; owned CAD children must be reaped. Do not hide preprocessing or child cleanup outside the accounting. Prerequisite custodian preparation outside the episode is logged separately and included in the benchmark protocol below.

Verified no-output `server_overloaded` rejection remains the only rule-#6 exemption: record the rejected attempt and full **600 s** wait, resend identical submitted bytes/model/options, no retry cap, no accepted-call/P/R consumption. Exclude that verified unavailable cycle from enclosing active clocks without resetting remaining budgets; include it in full operational wall time. Capture/quota/cancellation/identity stops still apply; no suite wall deadline or clipped wait is introduced.

Freeze this amendment only after agreement and independent development validation. It does not rewrite old evidence or change the 163-call unchanged-scope policy. Pilot correction/adoption still uses **300 elapsed seconds from first edit**, including waits; a 1200 s generation episode does not extend that correction window or erase a fatal first handover.

## (e) CAD-time baseline and durable dataset — BLOCK as written

Gemini lines 104–115 subtract with-harness elapsed/machine time from without-harness human-active time. Those are different quantities. GUI focus is not human work; thinking, reading a specification or editing a script can occur elsewhere, and a 15 s idle rule can discard legitimate engineering. Simply hiding the other construction tree does not remove learning when the same operator sees the same request twice. The proposed schema also lacks raw intervals, enrolled failures/censoring, preparation provenance, a protocol commitment and durable evidence custody.

### Proposed C-D(e): conditions and independent dataset

- Define the comparison as **manual headless FreeCAD scripting versus the AI/harness workflow**, not GUI CAD and not a same-model harness-only ablation. This retains a genuinely without-harness construction condition and preserves the headless workflow constraint. Do not market the resulting difference as the isolated causal contribution of the harness code.
- With harness: frozen `gpt-6.1-sol/xhigh` generator, isolated/closed stdin, unchanged request plus the authorized prepared runtime bundle, registered pipeline and fixed caps. Without harness: a qualified human engineers ordinary FreeCAD scripts using the same original request/assets and declared offline tools; no model, CAD-harness skill, planner, compiler, repair system, generated answer or fixture template. A neutral timestamp/stdout/stderr collector is measurement-only, not modeling assistance. The same frozen independent acceptance checks apply to both conditions.
- Use **20 fresh independent benchmark requests, four per new family = 20 pairs/40 condition records**. No U1–U5, dev fixtures, existing/new scored holdout requests or cosmetic variants. This is a separate time benchmark, not a replacement pilot. Commit protocol and integrated implementation before independent authoring; seal acceptance cards and input commitments before execution. Keep the required holdout → five-request pilot sequence; benchmark execution is a separate registered segment, without feeding its results back into either trial.
- Both arms start from identical source information and asset hashes, not a solved CAD tree or checker gold. Each does its own allowed construction/preparation; charge preparation work, including STEP facts, contour work and font processing, to the relevant workflow. The human must not receive a hidden gold model or a harness-generated solution.
- Use distinct qualified operators for the two arms of each pair. No operator sees both solutions for the same problem. Balance operator assignments across different tasks and randomize/counterbalance post-freeze execution slots: two harness-first and two manual-first per family. Freeze seed/order beforehand; run sequentially on DPC-019 to avoid resource contention. Named operator identities/qualifications are prerequisites, not synthetic substitute data.
- Use FreeCAD 1.1.4 and the frozen host/library identities in both conditions. A fresh document/process/workspace per arm; no cross-arm scripts or output reuse. Any permitted shared generic tools/training must be declared before exposure. Record load/cache/cold-start limitations rather than claiming they disappear.
- Use the proposed 1200 s active-work ceiling per arm, including that arm's operational preparation, with the same explicit provider-unavailability exclusion where applicable. The harness keeps its own stricter stage/call/CAD caps; a human may iterate ordinary scripts within the arm ceiling, with every run logged. Preserve all terminal outcomes and the correction/critical-error history. No extra time or substitution after seeing which arm fails.
- Freeze identical task-specific geometry/semantic criteria and blind the independent judge to condition where practicable. Masking filenames is not proof of perfect blinding: native feature trees may reveal workflow. Astra adjudication and named-human adoption remain separate from deterministic measurements.

### Clocks: compare like with like

| Quantity, collected for both conditions | Definition |
| --- | --- |
| Full operational wall | Monotonic duration from release of source packet to that condition's operator/custodian until qualified handover or terminal stop; includes preparation, waits, edits and checks |
| Workflow service elapsed | Union of the condition's operational intervals over the same work, excluding only prospectively classified research custody/freeze holds; includes thinking, ordinary idle/waits and every overload wait; not the active-budget clock |
| Human-active time | Explicit operator activity intervals covering reading, planning, coding, interaction, edits and review, independent of window focus; no automatic 15 s subtraction |
| Native CAD process wall | Union of actual supervised FreeCAD process intervals, including start/import/recompute/export and verification as tagged; not claimed to be kernel CPU time |
| Active-budget time | Existing budget clock with only the authorized unavailable-cycle exclusions; diagnostic/resource accounting, not user elapsed time |

Capture UTC, monotonic endpoints, boot/clock identity and timer resolution. Time each actual headless FreeCAD invocation directly in both arms. Use explicit activity/pause markers for labor; missing coverage is unknown, not assumed idle. Preserve underlying intervals; do not sum overlapping generation/CAD/edit/verification timers as total elapsed. CPU time, if unavailable, stays null and is not inferred from process wall time.

Custodian pre-freeze preparation must be timed **once**, not replayed for a favorable benchmark. Retain its preparation intervals and any intervening custody/freeze hold. Full wall includes that hold; the separately named service metric excludes only the preregistered research hold, never provider waits or human thinking. Counterbalancing refers to the post-freeze execution slots, not a claim that prerequisite custody work is order-balanced. Publish both clocks; do not silently call service time raw-input-to-delivery elapsed time or choose whichever reports a saving.

Use the same handover and acceptance endpoints in both arms. Keep the first handed-over artifact and every later edit/check; internal repair is not silently reclassified as a handover. Critical-dimension/fabrication history is immutable. The existing 300 s verified correction rule and authoritative human decision remain intact; no fatal first-handover error is repaired away statistically.

### Finite benchmark reservation and quality-aware comparison

For 20 with-harness tasks: at most **60 generator calls** (three per task). Manual arm: **zero generator/model-assistance calls**. Reserve **40 Astra Max judgments**, one per condition record, with no favorable re-score. Benchmark total: **100 non-exempt model invocations**, proposed as a separately registered allowance. Do not infer that the holdout-only unlimited allowance automatically authorizes another phase; the agreed final policy must expressly include this benchmark reservation. Expansion plus this benchmark would reserve **272** calls, separate from the original 163 and the separately frozen pilot reservation. No automatic transfer; fresh quota/identity/capture checks and rule #6 apply.

For each comparable metric, saving is `without − with`; percentage is `100 × (without − with) / without`. Compare wall with wall, service with service, labor with labor, and CAD-process wall with CAD-process wall. Preserve negative results. A zero baseline gives null reduction with `zero_baseline`, not zero or infinity; missing evidence propagates null with a reason.

Failed, refused, unstarted, UNVERIFIED, interrupted, non-adopted and timed-out arms remain enrolled. Preserve observed time-to-stop and right-censor completion time; do not describe early failure as fast completion. A pair lacking two qualified completions has null completion-time saving. Report enrolled/qualified/censored counts and per-arm success rates alongside any complete-pair descriptive statistics. Complete-pair timing is explicitly conditional; no overall whole-roster saving is asserted when required pairs are incomplete. Twenty purposively stratified pairs do not establish population productivity or Astra-pilot performance.

### Durable dataset, not just a local reports file

Keep Gemini's schema identifier `cad-harness.cad-time-benchmark.v1`, with a committed specification before use. Proposed per-experiment root: `reports/cad-time-benchmark/<experiment-id>/`; this path alone is **not** a durability guarantee.

| Evidence layer | Required content |
| --- | --- |
| Preregistration/manifest | Protocol/schema/code/skill/policy/judge/host hashes; corpus/custody/card commitments; allowed tools; condition/model definitions; task roster/strata/order/seed; operators; clocks/endpoints; caps/reservations; retention location |
| Canonical append-only events | Linked experiment/pair/task/arm/operation IDs; starts/ends and activity/hold classifications; quota/waits/stops; call charges/usage; preparation, native invocations, full stream references/hashes; first/final handover and edit/recheck history |
| Condition records | Input/bundle and source/native/STEP hashes; operator/model identities; status/reasons; applicable timing values and missingness; quality/rubric/adoption/fatal flags; accepted calls versus physical attempts; completion censoring |
| Derived dataset/CSV | Regenerable per-arm and paired rows referencing the sealed event-prefix/hash, matched-metric savings, zero/missing-baseline reasons, denominators and coverage; never an independently maintained counter |
| Durable custody | Relay-versioned schema/protocol, records and hash index, plus complete immutable raw/artifact bundles in a named backed-up store; verify retrieval/hash integrity and register location/retention before execution |

Corrections append a superseding event/record reference; retain the original evidence and avoid double-counting superseded rows. Do not overwrite a sealed run or put gold/artifacts into generator context. Record unknown/missing values as null with reasons; verified absence and not-applicable fields are distinct. An unenacted trial is `not_run`, not a successful zero-case dataset. No timing records, measured savings, storage provisioning or live authorization are created by this proposal.

## Remaining authority and release conditions

All five amended proposals need the required three-party agreement and binding into the final integrated manifest before fresh authoring/execution; this file is not that agreement. No extra user number is requested for delegated defaults, family gates or time ceilings.

C-A2 already fixes U1/U2 play at ≤0.5 mm **per side**, their angle tolerance at 3 degrees per side, U2 perimeter-band gap at ≥0.5 mm, and U4 thickness/unchanged outer dimensions at ±0.1 mm. These supersede earlier unresolved assumptions and are not softened by C-D. U1 tape location remains a real user question. U2 minimal concave-face contact remains Astra plus user qualitative judgment until answered, with no invented numerical gate. Any actual U5 topology conflict requires its own explicit resolution, not an assumption made in this review.

Before benchmark release, name the independent author/reviewer/custodian and operators, settle any required card evidence and identify verified durable storage. Missing prerequisites mean not_run/blocked authorization, never fabricated observations. Current usable quota, benchmark/manual timing and resulting savings remain unknown. S2 review continues; no S3 implementation, new CAD/model generation, pilot run or commit is performed here.
