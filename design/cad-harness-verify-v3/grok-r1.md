# VERIFY v3 — grok R1

Bar fractions stay those in `design/cad-harness-verify/PLAN-CONSENSUS.md`: source ≥8/10 and each ≥1/2, complex ≥2/3, stock ≥4/5, defaults ≥2/3, ambiguity each ≥4/5 with zero critical inventions, faults established and detected 6/6, final repair ≥4/6, each fault ≥1/2, and both spec and source repair. MVP stays ≥8/10 and each ≥1/2. Legacy stays 4/4. Completion stays outside `bar_met`. v2 is unmet only because W1 and K1 are 0/2: geometry passed, and the gate required a direct driving 34 while the model drove the stated depth 3.

## 1. Editability

v3 gold lists the user-stated quantity and its role. A derived diameter the description does not state is not a required driving value. The groove specimen is not a v2 item: outer diameter 36, length 40, bore 8, groove width 6, radial depth 2. The bottom diameter 32 is recorded as a derived consequence, not as `edit.driving_dimension`. Volume is `11912π` from `π*((18²−4²)*40−(18²−16²)*6)`, frozen before Sol, not fitted to FreeCAD.

A role passes only when a reached, active, driving constraint carries the stated value, or half of a diameter or width, and the constrained geometry is attached to the feature that makes the corresponding face. Radial depth passes when that driving distance spans the outer-radius geometry and the groove-bottom geometry, both reached from the used profile. A construction line is allowed. An expression that sets the outer radius equal to an already accepted outer-radius constraint is attachment, not a second number. Radius and Diameter still do not create graph edges. Negative origin and axis ids are still not hubs.

Reject a free number, a reference or inactive constraint, a depth on a sketch that is not the feature profile, and a depth whose other end is only the origin. Calibrate offline on new dev decoys at outer diameter 28 and depth 2.5, not on v1 or v2 files and not on the scored 36/2 specimen. Positives: direct diameter, half radius, depth distance, expression-linked radius, construction line. Negatives: disconnected diameter, non-driving, inactive, unused sketch, origin-only end. A mismatch stops the freeze. Do not edit gold to the measured solid. mvp-v1 and the v1 probe stay as they are. v3 is a new probe profile.

## 2. Unsupported routing and repair text

A well-formed `unsupported` response, and a schema-valid spec whose family cannot represent a required feature (a `stepped_shaft` axial hole, or any current family asked for a groove, sweep, or shell), switches to source and does not spend the parse slot. Malformed JSON still uses the one parse call. Schema families are not extended.

The repair call names the failed role and the driving values the probe already found, and it says an equivalent driving form of the requested dimension is acceptable. It does not supply the derived diameter, the volume, or a correct source. Caps stay source 4, spec 3, ask 1, completion 4. Parse 1 and repair 1 stay separate. CAD attempts stay 2. No second repair and no correct-source splice.

## 3. Diagnostics

If the probe fails before STEP export, the failure class is `editability_pre_export` or `geometry_pre_export`, not `verification`. Export failure and reimport mismatch stay separate classes. When export did not run, reimport is `not_reached` and a null `export_ms` is not a comparison failure. v2 rows keep their historical labels.

## 4. Fresh holdout

New ids, new dimensions, human Japanese, no BOM. Analytic volumes only. Author and freeze before any Sol call. v1 and v2 cases are not scored and are not tuning data.

| Cohort | Ids | N | Route | Gate |
| --- | --- | --- | --- | --- |
| source | G1–G5 | 2 | unsupported → source | ≥8/10 and each ≥1/2 |
| complex | G6 | 3 | in-schema | ≥2/3 |
| stock | T2 | 5 | in-schema | ≥4/5; stock scope only |
| defaults | D1 | 3 | in-schema | ≥2/3 |
| ambiguity | D2, D3 | 5 | one question, no CAD | each ≥4/5, inventions 0 |
| faults | H1, H2 source; H3 spec | 2 | one injection, not in the description | 6/6, final ≥4/6, each ≥1/2, both kinds |
| mvp | M1–M5 | 2 | in-schema | ≥8/10 and each ≥1/2 |
| legacy | A/B good and broken | 4 | unchanged offline smokes | 4/4 |
| completion | C4, C5 | 3 | outside `bar_met` | report only |

G1 is the 36/40/8/6/2 groove. H1 reuses G1’s clean description bytes and injects the missing groove once. G2–G5, G6, T2, D, M, and C4/C5 are different shapes and numbers, with volumes written as closed forms at freeze. Dev is three unscored previews plus the offline decoys, at most 4 calls, and no parse, repair, or CAD. Planned and max call slots are computed into the new run-order from these caps. The v2 figures 83 and 163 are not reused. New prefix and new aggregate files. Do not overwrite v2 reports.

## Unchanged

Tolerances stay ±0.01 mm, axis 1e-6, and volume relative 1e-4. Quota stays 55% soft and 60% hard, with no automatic fetch. Episode time stays 900 s and the phase clock stays 10800 s, including the v2 450/450 split. The compiler schema, mvp-v1 probe, v1 probe, v2 gold, and v2 scores stay. No LLM judge. No gold fitted to a measured solid. Completion does not enter `bar_met`. Full prompt-text archival is out of this fix; context hashes already exist.
