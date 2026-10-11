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
