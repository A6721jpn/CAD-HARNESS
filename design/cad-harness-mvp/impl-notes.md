# CAD-HARNESS MVP implementation: DECISION-02 steps 1–5

Branch: `proto/cad-run`; base HEAD: `9da050d`. Completed 2026-10-12 JST.
Git writes are blocked in this sandbox. After one denied staging attempt, the supervisor
explicitly prohibited retries and delegated local commits to the host. No commit or push
was made; the exact host file groups are in COMMIT PLAN below.

## Implemented files and behavior

1. `skills/freecad-modeling/SKILL.md`, `tools/cad_agent.py`: modeling judgment is separate
   developer context. Every MVP interpretation/source/repair payload is the original user
   description, with identical SHA; schema, previous output and diagnostics are separate.
   Typed mode makes zero model/version calls. Description mode interprets to build-spec;
   unsupported geometry falls back to agent source within the same three-call budget.
   Invalid outputs consume calls. Three CAD attempts maximum; monotonic 900-second cap,
   CAD/verification limits clipped to remaining time and 300 seconds. A repeated spec stops.
   Production description preview requires confirmation before CAD, and can run without gold;
   typed/agent execution and evaluation require human gold. No JSON-equality extraction gate.
2. `tools/cad_spec.py`, `build-schema.json`, typed fixtures: strict finite/duplicate/unknown-field
   checks, mm/cm/m normalization, supported connectivity and interference checks; declarative
   rectangular prisms/stacks and stepped shafts, pockets, through holes and outer top R/C.
   Compiler selection uses geometry families, never case IDs, gold or description SHAs.
   Standalone deterministic build(doc) uses constrained Sketches and native PartDesign features.
3. `eval-v1/schema.json`, `P1.json`–`P5.json`, `tools/cad_spec_probe.py`: frozen requested texts
   and human grading targets, independent BRep measurements and thin native editability gate.
   Checks include valid single solid, world bbox/volume, rectangular sections, grouped cylinders,
   hole openings/axis emptiness, pocket floor/walls/sharp edges, shaft shoulders, and R/C targets.
   Used Profile links, native Tip/Body membership, driving constraints/feature properties and
   clean recompute gate editability; FlatFace advice is warning-only. No reference-solid gate.
4. `tools/cad_run_probes.py` and driver/worker/host plumbing: bounded predicate_details reuse
   the same measured comparisons; expected/actual, nulls, tolerances and stable sub-check IDs.
   At most 32 failures / 8192 UTF-8 bytes, each expected/actual at most 256 bytes; truncation
   is explicit. Existing legacy A/B predicates, values, tolerances and first-failure logic stay intact.
   Confirmed typed failure, compiler native failure, IO/runtime/probe exception/cleanup failures
   stop for human review; an unconfirmed interpretation can repair a settled geometry mismatch.
5. `tools/cad_run.py`, `tools/cad_run_freecad.py`, `tools/cad_verify_freecad.py`: fixed headless
   launch, MVP source-operation contract, profile/gold/spec/source/attempt/PID binding, FCStd and
   STEP export, then artifact-only verification in a fresh owned freecadcmd process. It imports
   neither builder nor compiler. FCStd rechecks native history and geometry; STEP rechecks
   geometry; both compare world bbox ±0.01 mm and volume relative 1e-4 against the built solid,
   including P1. Artifact SHA binding, document close and both owned process exits gate success.

## Verification

FreeCAD executable used exclusively:
`C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe`.
Observed version: 1.1.4 / 20260928 / commit 4fd3bf320d9566a27e60069fc8387448aaa3a094.
No GUI, Fusion, SolidWorks, Sol, codex exec, or external API was run. All model paths were mocks.

Final unit command (42 tests, all passed, 0.918 s):
```powershell
python -B -m unittest tools.test_cad_run tools.test_cad_agent tools.test_cad_spec tools.test_cad_spec_probe tools.test_cad_mvp
```
Contracts cover unchanged legacy A prompt SHA, separate TOML context, typed zero calls,
preview/evaluation, invalid-output/fallback budgets, deadline clipping, unchanged-spec stop,
expected/actual repair propagation, native/IO stop, gold/artifact binding, blind/wrong-size holes,
extra finish rejection, used editable dimensions, warning-only advice, and immutable world shape.
Compiler tests read held-out typed fixtures only; a read guard rejects eval-v1/description paths.

Final smoke command (13 expected outcomes, all passed):
```powershell
python -B tools\smoke_cad_mvp.py --run 20261012-release-mvp1
```
Measured summary: `reports/cad-run/20261012-release-mvp1/smoke-summary.json`,
2026-10-12 00:20:46.603 JST / 2026-10-11 15:20:46.603 UTC.
To rerun on the host, replace the run ID with a fresh name ending in `-mvp1`.

| Case | Measured mm³ | Gold mm³ | Expected / observed | FCStd + STEP reimport | Total ms |
| --- | ---: | ---: | --- | --- | ---: |
| legacy A good | 22239.9556819442 | 22239.9556819442 | pass / pass | legacy unchanged | — |
| legacy A broken, no fillet | 22500.0000000000 | 22239.9556819442 | fail / fail | not requested | — |
| legacy B good | 44613.1033168641 | 44613.1033168641 | pass / pass | legacy unchanged | — |
| legacy B broken, no chamfer | 44751.7699835308 | 44613.1033168641 | fail / fail | not requested | — |
| P1 | 22239.9556819442 | 22239.9556819442 | pass / pass | pass | 937 |
| P2 | 44613.1033168641 | 44613.1033168641 | pass / pass | pass | 1000 |
| P3 | 13948.6713819387 | 13948.6713819387 | pass / pass | pass | 781 |
| P4 | 25947.6106578831 | 25947.6106578831 | pass / pass | pass | 875 |
| P5 | 29607.3009183013 | 29607.3009183013 | pass / pass | pass | 891 |
| H_RECT_CHAMFER | 28791.5299306923 | 28791.5299306923 | pass / pass | pass | 1000 |
| H_RECT_FILLET | 55198.4565291079 | 55198.4565076749 | pass / pass | pass | 922 |
| H_RECT_STACK | 27295.8396206768 | 27295.8396206768 | pass / pass | pass | 890 |
| H_SHAFT | 15705.6070734588 | 15705.6070734588 | pass / pass | pass | 828 |

All nine MVP rows: one CAD attempt, zero LLM calls, distinct build/verification PIDs, closed
documents, normal exit code 0, native editability pass. Every reported quantity above is an
actual worker measurement. Per-case outputs are under `20261012-release-mvp1-<case>-mvp1/a1-mvp1`;
legacy outputs are under the summary directory. Gold formulas are display-only, never evaluated.
P1 retains the legacy volume band; other volume targets use relative 1e-4. No bar was loosened.

Held-out dimensions differ from P1–P5: 55×45×12/C0.7/D4.4; 72×46×17/R2.2;
67×43×7 plus 39×6.5×29/D4.5; shaft D22×27 + D13×41 at XY=(1.7,-2.3), bottom Z=2.5.
Four specs cover five recipe families; the chamfer spec also exercises the plain prism recipe.

505 pre-existing report files were hash-snapshotted before batch smokes and verified unchanged.
Legacy fixture A SHA: `3ad5c506d84739c4378ce80d9557800919e7c0dd6c8f46cb8ff1cbc3882393dd`.
Legacy fixture B SHA: `d2285e092e6aca2e5c83af47c2bedcd34d1b1d0b42896be423996fc63dafac14`.
`measure_rollout.py` SHA: `9ee8cff2527ae86040bc4b663c1505e2510b2e8d6a8da7065c5e7a2cd698f90d`.
A initial prompt SHA remains `ea2008c9dfdb3d1c9ff732dd5c373fd431064d53744e01db9cad8921e32cc641`.

## Deviations and honesty notes

- Local per-step commits could not be made. The supervisor owns the host commits below; no
  git write retry, permissions change or push was attempted after that instruction.
- Added the small offline test temp helper because Python 3.12 private TemporaryDirectory ACLs
  excluded the restricted token. It uses inherited ACLs only inside the writable test directory;
  production exec cwd/isolation behavior is unchanged. No sandbox relaxation or elevation.
- The skill-creator validator lacks its local PyYAML dependency. Frontmatter/name/description and
  the actual skill text were checked locally; no dependency was installed and no network used.
- FreeCAD Body.Shape is a separate BRep copy. Probe therefore measures the native Tip directly;
  a measurement copy receives its global placement, while the raw Tip solid binds native history.
  A development smoke exposed immutable Shape setters; it failed hard and the final batch passed
  after using a copy. STEP exports the Body's current Tip solid with the owning world placement.
- The held-out C0.7 gold formula initially used an incorrect corner coefficient. Independently
  integrating removed area 2(W+D)t−4t² over t=0..C gives (W+D)C²−4C³/3. Only that held-out
  target/formula was corrected before the final batch; P1–P5 gold and all tolerances stayed fixed.
- Earlier development runs are preserved in fresh -mvp1 directories, including the immutable
  Shape failure and early hash/Tip binding failures. They are not replaced by final-pass reports.
- These are implementation smokes, not DECISION-01's ten natural-description runs. Actual CLI
  instruction injection and Sol success rate remain unmeasured; step 6 was not authorized here.
- Held-out targets were authored analytically during implementation and have no separate human
  sign-off. Their provenance is explicitly `fixture` / `confirmed=false`; --eval rejects them.
  The signed DECISION-01 P1–P5 targets retain `human` / `confirmed=true`. Allowing analytic
  fixtures in the shared reader does not admit them to the natural-description acceptance suite.
- The required local dashboard was updated separately. Serve status is unavailable in the
  sandbox, so current tailnet delivery is unverified. Dashboard/tmp/reports are excluded from commits.

## COMMIT PLAN

Host-only local commits, in this order; stage only these exact paths, never whole directories.
These groups stage the final working files; later hooks in the driver depend on completing step 5.
No hashes exist yet. Do not stage unrelated untracked files or existing decision/proposal documents.

### Step 1 — `feat(cad): add MVP modes, separate skill context, and shared budgets`

```text
skills/freecad-modeling/SKILL.md
tools/cad_agent.py
tools/test_cad_agent.py
tools/test_cad_run.py
tools/test_support.py
```

### Step 2 — `feat(cad): compile validated typed specs into native FreeCAD models`

```text
tools/cad_spec.py
design/cad-harness-mvp/build-schema.json
tools/fixtures/cad_mvp_build.py
tools/test_cad_spec.py
tools/fixtures/mvp/P1.json
tools/fixtures/mvp/P2.json
tools/fixtures/mvp/P3.json
tools/fixtures/mvp/P4.json
tools/fixtures/mvp/P5.json
tools/fixtures/mvp/H_RECT_CHAMFER.json
tools/fixtures/mvp/H_RECT_FILLET.json
tools/fixtures/mvp/H_RECT_STACK.json
tools/fixtures/mvp/H_SHAFT.json
```

### Step 3 — `feat(cad): grade frozen human gold with independent geometry and editability probes`

```text
design/cad-harness-mvp/eval-v1/schema.json
design/cad-harness-mvp/eval-v1/P1.json
design/cad-harness-mvp/eval-v1/P2.json
design/cad-harness-mvp/eval-v1/P3.json
design/cad-harness-mvp/eval-v1/P4.json
design/cad-harness-mvp/eval-v1/P5.json
tools/cad_spec_probe.py
tools/test_cad_spec_probe.py
tools/fixtures/mvp/H_RECT_CHAMFER.gold.json
tools/fixtures/mvp/H_RECT_FILLET.gold.json
tools/fixtures/mvp/H_RECT_STACK.gold.json
tools/fixtures/mvp/H_SHAFT.gold.json
```

### Step 4 — `feat(cad): add bounded expected-actual diagnostics without changing legacy pass logic`

```text
tools/cad_run_probes.py
```
Driver classification/feedback hooks are in the step-1 file; their end-to-end mock tests are
staged with step 5 because that module also imports the artifact verifier.

### Step 5 — `feat(cad): export and independently reimport MVP CAD artifacts`

```text
tools/cad_run.py
tools/cad_run_freecad.py
tools/cad_verify_freecad.py
tools/test_cad_mvp.py
tools/smoke_cad_mvp.py
tools/fixtures/cad_run_a_broken_mvp.py
tools/fixtures/cad_run_b_broken_mvp.py
design/cad-harness-mvp/impl-notes.md
```

Exclude `reports/`, `.dashboard/`, `.tmp/`, every `__pycache__/`, `debug.log`, legacy fixtures,
`tools/measure_rollout.py`, and all other pre-existing/unrelated untracked files. No push.

## Fix round 2 and eval preparation — 2026-10-12

Supervisor committed steps 1–5 locally as `183826f..7353beb` on `proto/cad-run` and
reported 42 passing host tests. This round made no Git calls, permission changes or push.
Reviewed `grok-impl-review.md` FIX-FIRST; implemented items 1, 2, 3, 5, 6 and 7:

- Spec parsing accepts one optional JSON/untyped fence, using the source fence rules.
- The separate CLI contract and schema describe required six-number region bounds,
  bottom-up regions, full pierced-region hole Z, and unsupported overlapping cuts.
  Unspecified XY-center / bottom-Z=0 defaults are binding.
- `needs_clarification` consumes one invalid output and retries within the same three calls.
  Invalid output feedback is scrubbed and capped at 1536 UTF-8 bytes before context encoding,
  with an explicit truncation flag; the original description payload stays unchanged.
- Compiler-test isolation now guards Path.read_text, read_bytes and open.
- Only P1 provenance.source annotates outer volume_relative=1e-4 as non-gating metadata.
  All P1 gates are identical to the prior frozen gold; P2–P5 are byte-for-byte identical.
  P1 geometry remains relative=0.01 and V<22500; artifact reimport still uses relative=1e-4.
- Added H_LIVE_PROBE.txt: new 72×46×17/R2.2 block with a 19×13×3.5 pocket.
  A mock test verifies no-gold description preview makes one interpretation call and no CAD.

`tools/eval_mvp.py` preregisters P1,P2,P4,P5,P3, two fresh sequential runs each.
Every subprocess uses description mode + --eval + frozen human gold, an exclusive per-run
description file containing exactly the gold UTF-8 text, and a checked description SHA.
Run IDs are <prefix>-<case>-r1/r2-mvp1; inputs and their manifest are also in a fresh -mvp1
directory. No failed run is replaced. Each run records eval-run.json; aggregation writes
reports/aggregate-mvp-eval-v1[-suffix].json and .csv exclusively and refuses either existing
output before any driver launch. --aggregate-only reads a prefix or ten explicit existing IDs
and launches nothing. It preserves previously observed wall time / failures when available.
Per-run data include geometry, editability, reimport, wall seconds, Sol calls, CAD attempts,
failure class and provider turn.completed usage only. Missing/partial token totals are null
(empty CSV fields), never inferred from text length. Summary enforces 8/10 and every part≥1/2,
fresh description identity, three-call/attempt limits, 900 seconds, both process exits/closes,
and matching driver identities; launcher-owned records also retain full harness file hashes.
Mixed versions or missing unattempted runs cannot claim the bar, even with 9/10 passes.
An observed launcher failure is a completed miss; an absent run remains incomplete.
Driver-report-only aggregation cannot recover unrecorded
launcher overhead or every historic harness file hash; prefer the saved eval-run.json records.
The manifest's aggregate-only file snapshot describes the aggregation environment, not old CAD.

### Round-2 validation

```powershell
python -B -m unittest tools.test_cad_run tools.test_cad_agent tools.test_cad_spec tools.test_cad_spec_probe tools.test_cad_mvp tools.test_eval_mvp
python -B tools\smoke_cad_mvp.py --run 20261012-fix-r2-smoke-mvp1
```

55 unit tests passed, final rerun 1.816 s. Seven interpretation/guard/P1/live-preview tests and six
evaluation tests extend the prior 42. All description/evaluation/model paths were mocks.
The fresh authorized FreeCAD smoke returned exit 0, all 13 expected outcomes correct.
Summary: `reports/cad-run/20261012-fix-r2-smoke-mvp1/smoke-summary.json`.
Measured 2026-10-12 01:01:21.068 JST / 2026-10-11 16:01:21.068 UTC.

| Case | Measured mm³ | Gold mm³ | Expected / observed | Reimport | Wall ms |
| --- | ---: | ---: | --- | --- | ---: |
| A good | 22239.9556819442 | 22239.9556819442 | pass / pass | legacy | — |
| A broken | 22500.0000000000 | 22239.9556819442 | fail / fail | legacy | — |
| B good | 44613.1033168641 | 44613.1033168641 | pass / pass | legacy | — |
| B broken | 44751.7699835308 | 44613.1033168641 | fail / fail | legacy | — |
| P1 | 22239.9556819442 | 22239.9556819442 | pass / pass | pass | 954 |
| P2 | 44613.1033168641 | 44613.1033168641 | pass / pass | pass | 1046 |
| P3 | 13948.6713819387 | 13948.6713819387 | pass / pass | pass | 875 |
| P4 | 25947.6106578831 | 25947.6106578831 | pass / pass | pass | 984 |
| P5 | 29607.3009183013 | 29607.3009183013 | pass / pass | pass | 875 |
| H_RECT_CHAMFER | 28791.5299306923 | 28791.5299306923 | pass / pass | pass | 985 |
| H_RECT_FILLET | 55198.4565291079 | 55198.4565076749 | pass / pass | pass | 937 |
| H_RECT_STACK | 27295.8396206768 | 27295.8396206768 | pass / pass | pass | 891 |
| H_SHAFT | 15705.6070734588 | 15705.6070734588 | pass / pass | pass | 812 |

All nine MVP rows: editability pass, FCStd+STEP reimport pass, one CAD attempt, zero LLM
calls, closed documents, normal build/verification exits, cleanup exited. Only the fixed
FreeCAD_1.1.4-Windows-x86_64-py311 freecadcmd was used, headless. No GUI or external API.
All 1756 pre-existing report files remain hash-identical. Legacy A/B fixture and
measure_rollout.py hashes remain identical to the recorded hashes above; A prompt SHA test passes.

### Host-only live injection check and evaluation commands (not executed here)

From C:\dev\CAD-HARNESS, use a fresh run ID. This exact preview command has no gold or CAD:

```powershell
python -B tools\cad_agent.py --run host-live-probe-r2-mvp1 --mode description --description-file tools\fixtures\mvp\H_LIVE_PROBE.txt
```

Live injection remains UNCONFIRMED. Before scoring, the supervisor must see a schema-valid
build_spec preview with llm_calls=1, cad_attempts=0, no agent-source fallback, and the fixture
dimensions/finish. Mock success does not establish that the host CLI honors developer context.
No Sol, codex exec, external API or actual eval was run in this sandbox.

After that live check, these are prepared host commands, not reported measurements:

```powershell
python -B tools\eval_mvp.py --prefix host-mvp-eval-r2 --suffix r2
python -B tools\eval_mvp.py --aggregate-only --prefix host-mvp-eval-r2 --suffix r2-reaggregate
```

Check weekly usage before starting and between runs; the signed 60% stop remains supervisor
responsibility because no provider quota adapter is available. The CLI does not invent quota
telemetry. If stopped, preserve the preregistered runs and record incomplete as unmet.
No acceptance-rate claim is made from typed smokes or mocks. No bar was loosened.
Dashboard was updated separately; current Serve delivery is still unverified.

## COMMIT PLAN (round 2)

Host-only local commits; stage these exact final files only. No Git operation was attempted here.

### Round 2a — `fix(cad): repair interpretation contracts and preserve gold gates`

```text
tools/cad_agent.py
design/cad-harness-mvp/build-schema.json
design/cad-harness-mvp/eval-v1/P1.json
tools/test_cad_spec.py
tools/test_cad_spec_probe.py
tools/test_cad_mvp.py
tools/fixtures/mvp/H_LIVE_PROBE.txt
```

### Round 2b — `feat(cad): prepare fixed description MVP evaluation and aggregation`

```text
tools/eval_mvp.py
tools/test_eval_mvp.py
```

### Round 2c — `docs(cad): record round-two fixes and offline validation`

```text
design/cad-harness-mvp/impl-notes.md
```

Exclude reports/, .dashboard/, .tmp/, every __pycache__/, debug.log, legacy fixtures,
and unrelated files. No push. Round-2 status: FIX DONE uncommitted.
