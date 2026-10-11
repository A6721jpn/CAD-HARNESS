# CAD-HARNESS MVP impl review (grok, 2026-10-12)

Reviewed DECISION-02 steps 1–5 in the working tree against DECISION-01/02/03 and the three sign notes. No code was run. Smoke figures below are impl-notes.md's record, not a re-measurement.

Clean against the signed bar: `cad_spec.py` selects `rect_prism` / `rect_stack` / `stepped_shaft` plus a `finish` field. It has no P1–P5, gold, or description-SHA branch. Held-out fixtures use other dimensions, tag all five recipe names, and `test_cad_spec.py` refuses `eval-v1` reads. The Sol argv payload is the user text (`cad_agent.py` `exec_argv`); skill, schema, and diagnostics go through `developer_instructions`. Gold stays out of the compiler and the first call. Probe gates are ±0.01 mm, volume relative 1e-4, and P1's GOAL_VOLUME band (`volume.relative` 0.01 and `< 22500`). Editability is one Body, sketch-backed Pad/Pocket/Revolution profiles, Tip solid, driving dimensions with half-size allowed, and clean recompute. FlatFace is warning-only. FCStd and STEP are rechecked in a second freecadcmd. Typed failure, compiler native failure, and export/reimport/cleanup stop at human. Budgets are 3 Sol calls, 3 CAD attempts, 900 s, CAD clipped to 300 s.

## Findings

1. MUST-FIX `tools/cad_agent.py:445`. Spec parsing feeds the raw final file to `cad_spec.read_json`. `source_from_final` (`cad_agent.py:117-121`) already strips one Markdown fence, and this path does not. A schema-valid `build_spec` wrapped in ```json fails JSON parsing, consumes a call, and can repeat until `call_limit` with zero CAD attempts. Those runs would count as misses and are not geometry results. Strip one optional fence, then parse, using the same rules as `source_from_final`.

2. SHOULD-FIX `tools/cad_agent.py:411-412`. The contract says region z is optional (`x_min,x_max,y_min,y_max[,z_min,z_max]`). `build-schema.json` `bounds6` requires six numbers, and `cad_spec.py:121-155` also requires bottom-up region order, hole `z` equal to the pierced region's z, and no pocket/hole overlap. Those rules appear only as `ValueError` text after a failed call. State them in the contract string so a correct first spec is not spent as a repair.

3. SHOULD-FIX `tools/cad_agent.py:451-459`. `needs_clarification` is re-raised and ends the run while calls remain. P1 does not state the origin; the contract's center/Z=0 default is what resolves it. Treat this response as one consumed invalid output and continue, and say in the contract that those defaults are binding.

4. SHOULD-FIX `tools/cad_agent.py:79-84` and `:162-169`. `-c developer_instructions` round-trips in a mock only. DECISION-02 says live injection is unconfirmed. Before the scored 10, run one live exec and accept it only if the model returns schema-shaped JSON. A channel that codex ignores would make all 10 runs interpretation noise.

5. NIT `tools/cad_agent.py:460`. `invalid_output` is the full model text inside the next developer context. Cap it before `context_config`, or a long reply hits `context_argv_limit` (`cad_agent.py:170-171`) and drops the remaining repairs.

6. NIT `tools/test_cad_spec.py:16`. The held-out guard patches `Path.read_text` only. `read_bytes` / `open` would not trip it. The compiler does not use those today.

7. NIT `design/cad-harness-mvp/eval-v1/P1.json:8-10`. `tolerances.volume_relative` is 1e-4, while the gate is `volume.relative` 0.01 plus `upper_exclusive` 22500 (`cad_spec_probe.py:213-216`). The probe uses the inner field. Delete or annotate the outer 1e-4 so it is not read as the P1 bar.

verdict: FIX-FIRST
