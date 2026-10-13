# Pre-registered call derivation

Source: signed PLAN-V3-CONSENSUS.md and `run-order.json`; these are reservations, not measured usage or quota predictions.

| Cohort | Episodes | Baseline calls | Maximum calls |
| --- | ---: | ---: | ---: |
| New dev D1/D2/D3 (preview only) | 3 | 4 | 4 |
| Legacy A/B good/broken | 4 | 0 | 0 |
| Fixed eval-v1 P1–P5, twice | 10 | 10 | 30 |
| G1–G5 unsupported→source, twice | 10 | 20 | 40 |
| G6 | 3 | 3 | 9 |
| S3 | 5 | 5 | 15 |
| A4 defaults | 3 | 3 | 9 |
| A5/A6 first-question only | 10 | 10 | 10 |
| C4/C5 clarify→answer→completion | 6 | 12 | 24 |
| F4/F5 forced source repair | 4 | 12 | 16 |
| F6 forced spec repair | 2 | 4 | 6 |
| Total | 60 | 83 | 163 |

Max = source14×4 + supported13×3 + ask10×1 + completion6×4 + MVP10×3 + dev4 = 163.
Core51 = legacy4 + MVP10 + G/S18 + A13 + F6. C6 and dev3 are outside bar_met.
P≤1 across initial and repair responses; R≤1 is separate; CAD≤2. Source4/spec3/ask1/completion4 do not expand automatically.

`eval_verify_v3.validate_order` independently rebuilds every planned position/route/min/max/round, checks cohort counts and class aliases, and recomputes 83/163/51/6. Changing order, N, route or cap is rejected. Host CLI guard also rejects call budgets outside 1..163. Run-entry SHA bindings include descriptions and both answer/completion payload hashes.
