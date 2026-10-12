# VERIFY Phase 2 implementation — FIX4 DONE, uncommitted

Binding plan: `PLAN-CONSENSUS.md`, signed Codex/Grok R3b, supervisor commit `f0e8953`.
Implementation snapshot: 2026-10-12, `C:\dev\CAD-HARNESS`. No Git commands, staging,
commit, push, or real Sol calls were made. The host must perform the review and commits.

**Current status: FIX4 DONE — Grok/Gemini READY; SHOULD 1 applied; all 74 unit tests and F1–F3 smokes pass.**
`Fault.inject.reached` is now true only when the replacement is returned with `injected=true`.
A missing/non-unique target keeps reached/injected=false and candidate_target_missing recorded.
Only the guard, its unit test and these notes changed in FIX4. All data/gold/other source files
are byte-identical; the original stale SHA is retained. Ordinary Python passed 71 tests and
the authorized headless native runner passed the remaining three; seven fresh fault outcomes
all matched expectations. Existing Grok/Gemini reviews are READY, with only Grok SHOULD 1
implemented as instructed. Host local commits and current SHA/version freeze remain pending.
No Sol or Git operation; detailed FIX4 results and the final COMMIT PLAN follow below.

**FIX3 history — full offline 47/47, legacy 4/4 and all 73 unit tests passed.**
Only verify-v1 now measures `optimalBoundingBox(False,False)` for every bbox and both
FCStd/STEP reimports. MVP mvp-v1 is unchanged. Authorized follow-on corrections cover the
used normalized construction axis, serialized circular-section representation and F3's
manual fault source. Gold, tolerances, descriptions, registered fault/spec and every other
fixture remain unchanged. Failed r1/r2/r3 attempts are preserved; final r4 started from the
first outcome and passed all 47. Ordinary Python ran 70 unit tests and skipped three native
tests; the fixed headless FreeCAD executable separately passed those three. Legacy4 passed.
All 27 original protected files are byte-identical. FIX3 results and COMMIT PLAN are below.
No Git, local commit or Sol call. Initial SHA is preserved but stale; supervisor implementation
review, host local commits and a fresh SHA/version freeze remain required before Phase 3.

**FIX2 history — DV3 geometry/gold agree; ordinary BoundBox is conservative.**
Description-only analytic bbox [0,38,-7,31,-7,7] is confirmed. A native fixture-vs-description
test passes on the unchanged positive fixture using precise geometric bounds, cap centers,
cap normals/radii and volume. Both the original Revolution and an independent native Frenet
pipe return the same oversized ordinary BoundBox used by the Probe; their precise bounds
match the analytic derivation. Fixture geometry is not the cause of this bbox disagreement.
No fixture source, gold, tolerance, gate or Probe code was changed in FIX2. Its fixture-only
scope cannot fix the measurement choice, so the full smoke/legacy/unit batches were not
restarted. Detailed evidence and the one added native sanity test are recorded below.

**FIX1 history:** The supervisor
authorized the pre-freeze DV2 Probe exception fix. Its traceback was diagnosed, only the
VERIFY Probe was fixed, a reproducing unit test was added and passed, and the full offline
batch was restarted from its beginning under a new prefix. DV2 positive/negative then
passed their expected outcomes. The restarted batch stopped at DV3 positive: Xmax expected
38 mm, measured 41.13090361111099 mm; Ymin expected -7 mm, measured -10.130903611110973 mm
(both tolerance ±0.01 mm). No gold, fixture, tolerance, or gate was changed. Remaining native
outcomes, legacy4 and the full post-fix unit run were withheld at the explicit measured-value
stop. Phase 3 remains blocked. Details and updated COMMIT PLAN are in the FIX1 log below.

**Initial Phase 2 history, before supervisor FIX1 authorization:** The first offline native smoke batch stopped at dev/DV2
positive: `probe_status=exception`, `error_type=ValueError`, geometry/editability/volume
measurements null. This is a Probe failure, not an observed replacement volume for gold.
The batch was stopped immediately; no gold, fixture, tolerance, or gate was changed
after that result. Remaining native cases and the four legacy offline smokes were not
run. No later successful run replaces this failure. The supervisor must resolve this
stop condition and review the implementation before authorizing a live frozen version.

## Implemented surface

- Separate `test/` and `dev/` corpora. Test descriptions are the signed table text in
  UTF-8, without BOM, quotation marks, appended hints, or trailing newline. Each geometry
  case has human analytic gold, a standalone hand-authored native positive/negative
  source, and expected offline outcomes. Dev dimensions and wording are different.
  Q2/Q3 have field-ID rubrics and positive/negative response fixtures, no geometry gold
  and no CAD. F1/F2 have frozen full native replacement sources; F3 has a frozen numeric
  mutation and candidate spec plus an independent manual native negative.
- `run-order.json` preregisters 54 episodes: three dev pilots (at most four calls), four
  legacy smokes, ten fresh MVP description runs, 18 V/S clean runs, 13 Q runs, six fault
  episodes. Minimum/planned calls 71; maximum 125. V/S, Q, fault, MVP and dev are separate.
- `cad_verify_probe.py` implements the verify-v1 world BRep predicates and consumed
  native-link editability. It measures the requested annular sections/shoulders, taper
  endpoints and midpoint, curved pipe normal sections/open lumen, box walls and triangle
  rib, flange hole centers/openings/slots, rectangular pockets and top outer R/C.
  Correct planar B-spline representations are measured as planes. Missing/unsupported
  gold predicates fail. Face/edge/native feature counts are measurements, not acceptance
  targets. Compiler/generator/fixtures are not imported by the Probe.
- S1 gold uses only the exact `[-29,29] × [-21,21] × [0,12]` stock intersection volume
  29232 mm³ and the local four-quarter-circle R2 checks, including the two central
  vertical sections at Z=15. Whole volume is still measured and used for FCStd/STEP
  agreement; no corner-patch whole-volume formula is an S1 acceptance target.
- Final native editing success requires one Body, a used native Tip, consumed Sketch
  links (including Loft sections and an actually referenced construction axis), requested
  driving dimensions and clean recompute. An unused Sketch cannot supply dimensions.
  `measurements.editability.native_valid` reports the structural gate separately from
  requested-dimension preservation. A missing requested feature can retain a normal
  native structure while failing its requested dimension and geometry gates; it never
  becomes a final success. This distinction is used for the fault's settled initial fail.
- Driver/worker/export/reimport plumbing supports opt-in `verify-v1`. Artifact-only
  verification remains a separate owned headless process with no builder/compiler import.
  The evaluator rechecks source, gold, artifact and on-disk report bindings and process exits.
- VERIFY clarification accepts necessary field IDs in developer context and stops.
  `--first-response-only` means exactly one interpretation and zero CAD, including invalid,
  unsupported or invented outputs. Q1 records the first spec's binding placement defaults
  separately from its final geometry gate. Q2/Q3 score only the expected missing field.
  The user payload remains the original description on interpretation, fallback and repair.
- One-shot fault injection occurs only after a contract-valid original candidate. Original,
  replacement and candidate SHA, fault ID, actual call and observed fail are recorded.
  The injected flag never forces Probe failure. A false pass or missing prescribed fault
  detection stops the version. Repair uses the actual injected candidate and real diagnostics,
  with shared counters and no correct-source substitution.
- `cad_verify_guard.py` checks a supervisor-written quota snapshot immediately before every
  real call: strict three-field JSON, valid percent/time, age at most 300 s, future timestamp
  rejected, 55% soft stop and 60% hard stop. No automatic quota fetch or token-to-percent
  estimate. The shared monotonic 10800 s clock spans dev, regression, test, cleanup and
  independent aggregation. Run limits are clipped to 900 s; CAD/reimport to 300 s and
  remaining run time. Five seconds are reserved before starting an operation.
- `eval_verify.py run` uses the frozen order, fresh prefix, sequential fresh runs, maximum
  dev four calls, all planned IDs and stop reasons. `aggregate` launches nothing and writes
  new JSON/CSV only. It separates initial/final geometry/editability/reimport/pass, routes,
  Q scores/inventions, fault reached/established/detected/final pass, conditional repair,
  parse repair, provider usage fields (missing stays null), and failure-inclusive wall times.
  Wilson 95% uses z=1.96 and is absent for incomplete batches/parts. No general JA/EN rate
  is inferred. The old MVP ten-run bar and gold remain the regression requirement.
- `SHA256.json` fingerprints 133 data/code/skill/schema/plan files and inherited AGENTS
  identities. It is the immutable **initial pre-fix review snapshot**;
  `local_commit=pending_supervisor` is explicit. It is not evidence of a commit, a completed
  smoke suite, or permission to start Phase 3. Do not overwrite this stopped snapshot.
  FIX1 changes its Probe/test hashes, so it is now stale as a runtime freeze; the unchanged
  data hashes remain evidence. No replacement SHA manifest was written without supervisor
  handling of the pre-freeze revision.

## Verification actually performed

All 66 unit tests passed, 3.131 seconds, process exit 0:

```powershell
$PreviousVerifyTemp = $env:TEMP
$PreviousVerifyTmp = $env:TMP
try {
    $env:TEMP = 'C:\dev\CAD-HARNESS\.tmp\unittest-mvp1'
    $env:TMP = $env:TEMP
    python -B -m unittest tools.test_cad_run tools.test_cad_agent tools.test_cad_spec tools.test_cad_spec_probe tools.test_cad_mvp tools.test_eval_mvp tools.test_cad_verify
    if ($LASTEXITCODE -ne 0) { throw 'Unit regression failed' }
} finally {
    $env:TEMP = $PreviousVerifyTemp
    $env:TMP = $PreviousVerifyTmp
}
```

Tests use `tools/test_support.py`'s inherited-ACL temporary directories. Model/process
calls are mocks. Contracts include first-response/no-follow-up/default MVP retry,
snapshot age/percent/budget/deadline boundaries, one-shot source/spec faults followed
by ordinary repair, false-pass stop, unused dimension decoys, Wilson incomplete rules,
immutable output files and unsupported predicates. Unit tests do not certify the native
geometry or the complete live evaluator workflow.

Offline command actually run, exit 1:

```powershell
python -B tools\smoke_cad_verify.py --run 20261012-phase2-native-r1-mvp1
```

FreeCAD ran successfully in this sandbox, exclusively with
`C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe`.
Observed stdout version: 1.1.4 / 20260928. No GUI or other CAD application was launched.
Smoke summary: `reports/cad-run/20261012-phase2-native-r1-mvp1/smoke-summary.json`.
Batch stop observed at 2026-10-12 08:18:24 UTC / 17:18:24 JST.

| Dev case | Expected geometry | Geometry / editing / reimport | Actual full mm³ | Scoped mm³ | Outcome |
| --- | --- | --- | ---: | ---: | --- |
| DQ1 positive | pass | pass / pass / pass | 37052.21023641287 | — | expected |
| DQ1 negative | fail | fail / fail / not run | 36706.63504451799 | — | expected; native structural gate passed |
| DS1 positive | pass | pass / pass / pass | 52753.54932433188 | 39468 | expected |
| DS1 negative | fail | fail / fail / not run | 53048.00000000001 | 39468 | expected; native structural gate passed |
| DV1 positive | pass | pass / pass / pass | 35707.342100701586 | — | expected |
| DV1 negative | fail | fail / fail / not run | 37573.44813693393 | — | expected; native structural gate passed |
| DV2 positive | pass | null / null / not run | null | — | **STOP: Probe ValueError** |

The complete offline plan has 47 outcomes (32 native V/S/Q1 outcomes, eight Q2/Q3
rubric outcomes with CAD=0, seven native fault outcomes). Six expected outcomes and
one Probe exception were observed; 40 outcomes remain unrun. Legacy A/B good/broken
four-smoke regression is also unrun in this phase. Test V2 midpoint, all other test
profiles, and prescribed real native F1/F2/F3 detection remain unverified. No natural
description success rate or live provider usage was measured.

DV2 failed record:
`reports/cad-run/20261012-phase2-native-r1-mvp1/dev-DV2-positive-mvp1/result.json`.
It records `failed_phase=probe`, `code_owner=probe`, `next_actor=human`,
`cad_exit_code=0`, `document_closed=true`, `cleanup_status=exited`, owned PID 1752.
There is no traceback or measured gold comparison in the worker output; the exact
ValueError origin is not established. Do not guess a new gold value from this result.

The 27 protected baseline files were SHA checked after the stop and were all unchanged:
MVP decisions/status/notes, all eval-v1 gold/schema, `eval_mvp.py`, compiler and MVP Probe,
legacy probes/fixtures, `measure_rollout.py`, modeling skill, and the signed VERIFY plan.
Baseline evidence is `.tmp/verify-phase2/baseline.json` (not a commit artifact).
Default MVP `needs_clarification` retry is covered by the passing old unit regression.

## Supervisor diagnostic and offline commands — no Sol

Do not continue the stopped smoke batch or overwrite its reports. Diagnose the missing
DV2 measurement first. This standalone host diagnostic prints the exception traceback;
it uses the same frozen hand fixture/gold and the required headless executable. It is
provided for the supervisor and **was not executed after the stop**.

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
$FreeCADCmd = 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe'
$DebugDirectory = 'C:\dev\CAD-HARNESS\.tmp\verify-DV2-host-debug-r1'
if (Test-Path -LiteralPath $DebugDirectory) { throw 'Choose a fresh debug directory' }
New-Item -ItemType Directory -Path $DebugDirectory | Out-Null
$DebugScript = Join-Path $DebugDirectory 'probe-debug.py'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$DebugSource = @'
import sys, runpy, traceback
from pathlib import Path
import FreeCAD as App
sys.path.insert(0, 'C:/dev/CAD-HARNESS/tools')
import cad_verify_probe
folder = Path('C:/dev/CAD-HARNESS/design/cad-harness-verify/dev/DV2')
doc = App.newDocument('VerifyDV2Diagnostic')
try:
    body = runpy.run_path(str(folder / 'positive.py'))['build'](doc)
    doc.recompute()
    print(cad_verify_probe.probe(doc, body, cad_verify_probe.load_gold(folder / 'gold.json')))
except Exception:
    traceback.print_exc()
finally:
    App.closeDocument(doc.Name)
'@
[System.IO.File]::WriteAllText($DebugScript, $DebugSource, $Utf8NoBom)
$BlankConfig = '<?xml version="1.0" encoding="UTF-8"?><FCParameters><FCParamGroup Name="Root"/></FCParameters>'
[System.IO.File]::WriteAllText((Join-Path $DebugDirectory 'user.cfg'), $BlankConfig, $Utf8NoBom)
[System.IO.File]::WriteAllText((Join-Path $DebugDirectory 'system.cfg'), $BlankConfig, $Utf8NoBom)
& $FreeCADCmd --user-cfg (Join-Path $DebugDirectory 'user.cfg') --system-cfg (Join-Path $DebugDirectory 'system.cfg') $DebugScript
```

After the supervisor resolves the stop under the binding plan and reviews a new
candidate, use fresh offline prefixes and preserve this failed version's evidence:

```powershell
python -B tools\smoke_cad_verify.py --run host-verify-phase2-reviewed-r1-mvp1
if ($LASTEXITCODE -ne 0) { throw 'STOP: native fixture/Probe disagreement; preserve gold and reports' }
python -B tools\smoke_cad_mvp.py --run host-verify-phase2-legacy-r1-mvp1 --group legacy
if ($LASTEXITCODE -ne 0) { throw 'STOP: legacy regression failed' }
```

Code/data changed during a later review must not silently reuse this SHA snapshot or
failed reports. The supervisor decides the replacement freeze/version before any Sol;
this phase made no automatic revision following the stop.

## COMMIT PLAN — messages and selected paths, host only

These are the final proposed Phase 2 commits, not completed commits. Grok and Gemini
implementation reviews are READY; FIX4 applies only the supervisor-selected SHOULD 1.
FIX3 full offline/legacy gates and FIX4 all-unit/fault regression checks pass. Host local
commits and a current SHA/version freeze remain required before live acceptance.
Stage only the listed paths. No push. Do not stage `.dashboard/`, `.tmp/`, reports,
`__pycache__/`, the prior signed plan/proposals, or any unrelated working-tree files.
The new test/dev directories contain only the newly authored VERIFY case files.

1. `test(cad): add frozen VERIFY test and dev corpora and native fault candidates`

   ```text
   design/cad-harness-verify/test/
   design/cad-harness-verify/dev/
   design/cad-harness-verify/gold-schema.json
   design/cad-harness-verify/run-order.json
   tools/fixtures/verify_native.py
   ```

2. `feat(cad): add tight VERIFY probes, used native links and supervisor guards`

   ```text
   tools/cad_verify_probe.py
   tools/cad_verify_guard.py
   tools/cad_agent.py
   tools/cad_run.py
   tools/cad_run_freecad.py
   tools/cad_verify_freecad.py
   ```

3. `feat(cad): add fixed VERIFY runner, independent aggregate and offline contracts`

   ```text
   tools/eval_verify.py
   tools/smoke_cad_verify.py
   tools/test_cad_verify.py
   tools/test_verify_dv3_native.py
   design/cad-harness-verify/SHA256.json
   design/cad-harness-verify/SHA256-initial-pre-fix.json (host-created archive)
   design/cad-harness-verify/grok-impl-review.md
   design/cad-harness-verify/gemini-impl-review.md
   design/cad-harness-verify/impl-notes.md
   ```

`SHA256.json` is the preserved initial failed-preflight fingerprint, now stale. Group 3 must
stage a supervisor-reviewed current freeze rather than presenting that old snapshot as READY.
The host archive/re-freeze commands below preserve the original fingerprint. Native-test
supplemental coverage remains a process-only option; no evaluator CODE edit was authorized.
There is no
commit SHA from this implementation turn. Inherited AGENTS identities are recorded,
not copied into generation context. The global `C:/Users/backo/.codex/AGENTS.md` was
verified as its central-config symbolic link. Root AGENTS.md was absent and not recreated.

## Phase 3 host commands — READY reviews; host commits and current SHA/version freeze pending

The following commands describe the implemented interface. **Do not run them against the
current stale SHA snapshot.** FIX3 completed all offline gates and FIX4 passed the requested
regressions. Grok/Gemini implementation/data reviews are READY. Complete selected host
local commits and SHA/version freeze first. No extra review/model
calls or success-driven reruns are part of the batch.

The supervisor can archive the original snapshot and run the unchanged evaluator's freeze
CLI on the host. These commands have not been executed here. Both original and replacement
files must be preserved; an existing archive aborts this step. Freeze uses exclusive creation
and never overwrites. This block is the exact default CLI sequence:

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
if (Test-Path -LiteralPath design\cad-harness-verify\SHA256-initial-pre-fix.json) { throw 'STOP: freeze archive exists' }
Rename-Item -LiteralPath design\cad-harness-verify\SHA256.json -NewName SHA256-initial-pre-fix.json -ErrorAction Stop
python -B tools\eval_verify.py freeze
if ($LASTEXITCODE -ne 0) { throw 'STOP: current freeze failed' }
python -B -c "from tools.eval_verify import load,ROOT; manifest,order=load(ROOT); print('Current SHA and inherited AGENTS match:',len(manifest['files']),'files')"
if ($LASTEXITCODE -ne 0) { throw 'STOP: current freeze verification failed' }
# Perform the selected local commits according to COMMIT PLAN before any Phase 3 call.
```

Gemini SHOULD 2 (adding the native test to evaluator CODE) is outside the requested change;
`eval_verify.py` remains byte-identical. The default CLI freeze covers its existing registered
runtime/data/test list and omits `tools/test_verify_dv3_native.py`. To retain the earlier
documented supplemental native-test coverage without a source edit, replace only the freeze
line above with this process-only invocation of the same `freeze` CLI handler, **before** a
new SHA file exists; do not run both freeze commands:

```powershell
python -B -c "from tools import eval_verify as e; e.CODE += ('tools/test_verify_dv3_native.py',); raise SystemExit(e.main(['freeze']))"
if ($LASTEXITCODE -ne 0) { throw 'STOP: supplemental current freeze failed' }
```

Restore TEMP/TMP after unit tests: production model work directories must be outside the
repository. In a host PowerShell terminal, the supervisor writes a snapshot using the
actually observed provider percent and UTC timestamp. Refresh with a new real observation
within five minutes throughout the run; do not reuse an old observation or invent a value.

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
$QuotaDirectory = 'C:\dev\CAD-HARNESS\.tmp\verify-supervisor'
New-Item -ItemType Directory -Path $QuotaDirectory -Force | Out-Null
$QuotaPath = Join-Path $QuotaDirectory 'quota.json'
function Write-VerifyQuotaSnapshot {
    param([Parameter(Mandatory=$true)][double]$ObservedUsedPercent)
    if ([double]::IsNaN($ObservedUsedPercent) -or [double]::IsInfinity($ObservedUsedPercent) -or $ObservedUsedPercent -lt 0 -or $ObservedUsedPercent -gt 100) { throw 'Invalid observed percent' }
    $Snapshot = @{
        snapshot_id = [guid]::NewGuid().ToString()
        observed_at = [DateTimeOffset]::UtcNow.ToString('o')
        used_percent = $ObservedUsedPercent
    } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($QuotaPath, $Snapshot, [System.Text.UTF8Encoding]::new($false))
}
# Invoke Write-VerifyQuotaSnapshot with the supervisor's actual observed percent.
# In a second terminal, keep updating the same file with actual fresh observations.
python -B -c "from tools.eval_verify import load,ROOT; load(ROOT); print('SHA and inherited AGENTS match')"
if ($LASTEXITCODE -ne 0) { throw 'STOP: freeze mismatch' }

# Only for a reviewed, committed READY candidate; a fresh prefix is mandatory.
python -B tools\eval_verify.py run --prefix host-verify-v1-reviewed-r1 --quota-snapshot $QuotaPath --call-budget 125
# Independent aggregation launches no Sol or CAD. It must finish under the same 3h clock.
python -B tools\eval_verify.py aggregate --prefix host-verify-v1-reviewed-r1 --suffix host-reviewed-r1
```

`run` performs the preregistered dev → legacy → fresh eval-v1 → clean V/S → Q → F order.
Do not separately launch `eval_mvp.py` as another batch; the new runner already runs the
required fresh fixed ten through its unchanged MVP path and unchanged gold/bar. The old
10/10 report is not a substitute. A quota/time/harness stop leaves remaining IDs uncompleted;
aggregation is diagnostic and cannot turn that into a bar pass. The shared deadline is
the stored host monotonic clock, so independent aggregation is for that same running host
session, not after a reboot or transferred to another machine.

## Dashboard and permission evidence

The required dashboard-builder created and updated `.dashboard/public/index.html` using
the explicitly required Rams skill. This is the only public file, with 30 s re-fetch and
separate live/data update clocks. Parent `tailscale serve status --json` was denied at
the protected tailscaled pipe. No Serve configuration, junction, permission, existing
publication, Funnel, or public tunnel was changed; there is no verified tailnet URL.
The supervisor must inspect existing Serve settings before any unique project publication.
The completed FIX3 offline gates, preserved stopped attempts and remaining supervisor
review/commit/freeze requirements are reported on the dashboard.

## FIX1 log — supervisor-authorized pre-freeze Probe fix, then measured-value STOP

The supervisor explicitly distinguished the DV2 exception from a gold-vs-measurement
disagreement and authorized Probe-only repair, one reproducing unit test and a fresh full
offline rerun. No Sol or Git commands were used. The frozen data and prior reports were
preserved. Only `tools/cad_verify_probe.py`, `tools/test_cad_verify.py` and these notes changed.

### Diagnosis and bounded fix

Headless traceback diagnostic used the specified FreeCADcmd, the unchanged dev/DV2
positive and gold, and a fresh `.tmp/verify-phase2-fix1/` directory. Captured traceback:
`.tmp/verify-phase2-fix1/traceback.txt`; stdout: `.tmp/verify-phase2-fix1/stdout.txt`.
The actual diagnostic exited 0 because its exception handler printed the traceback;
`DIAGNOSTIC_DOCUMENTS_CLOSED True` confirms document cleanup. That exit was not a Probe pass.

```text
cad_verify_probe.probe -> measure_shape -> taper -> segment_present
cad_verify_probe.py:78
    lo, hi = sorted(v.dot(direction) for v in pts)
ValueError: too many values to unpack (expected 2)
```

The straight B-spline path appends three interior samples to its two endpoints. Unpacking
all five projections into two variables raised the exception. The fix computes minimum
and maximum projection after the same existing collinearity check. Segment extent limits,
gap coverage, length tolerances, requested shape checks and all final gates are unchanged.
For ordinary line edges with two endpoints, min/max has the same result as the former sort.

The new single unit test `VerifyTests.test_straight_bspline_samples_preserve_segment_coverage`
uses mock B-spline edges with five sampled points. It tests one complete edge, two contiguous
edges, a gap and a curved edge. Before the fix it reproduced the same ValueError (one test,
three failing subtests, exit 1). After the fix it passed (one test, 0.001 seconds, exit 0).

```powershell
$PreviousVerifyTemp = $env:TEMP
$PreviousVerifyTmp = $env:TMP
try {
    $env:TEMP = 'C:\dev\CAD-HARNESS\.tmp\unittest-mvp1'
    $env:TMP = $env:TEMP
    python -B -m unittest tools.test_cad_verify.VerifyTests.test_straight_bspline_samples_preserve_segment_coverage
} finally {
    $env:TEMP = $PreviousVerifyTemp
    $env:TMP = $PreviousVerifyTmp
}
```

### Fresh full native rerun and exact stop values

Executed from the beginning, with no prior run reused:

```powershell
python -B tools\smoke_cad_verify.py --run 20261012-phase2-fix1-native-r1-mvp1
```

Exit 1; stop observed 2026-10-12 08:36:05 UTC / 17:36:05 JST. Summary:
`reports/cad-run/20261012-phase2-fix1-native-r1-mvp1/smoke-summary.json`.
Eight outcomes were as expected: DQ1±, DS1±, DV1± and DV2±. Dev/DV2 positive measured
30169.333333333336 mm³, exactly its frozen gold target, and passed geometry, editing and
independent FCStd/STEP reimport. DV2 negative measured 31944.0 mm³ and failed as intended,
with a valid native structural gate.

The ninth outcome, **dev/DV3 positive**, returned a settled `predicate_fail` with measured
values, not an exception. This activated the supervisor's explicit STOP condition:

| Predicate | Frozen expectation | Actual measurement | Tolerance / outcome |
| --- | ---: | ---: | --- |
| bbox.x_max | 38 mm | 41.13090361111099 mm | ±0.01 mm; fail |
| bbox.y_min | -7 mm | -10.130903611110973 mm | ±0.01 mm; fail |
| Requested used driving dimension | 31 mm | null | mandatory dimension not found; fail |
| Whole volume | 4398.142461235445 mm³ | 4398.142461235451 mm³ | relative 1e-4; pass |

Full expected bbox is `[0,38,-7,31,-7,7]`; full measured bbox is
`[-3.8857805861880495e-15,41.13090361111099,-10.130903611110973,31.000000000000014,-7.000000000000015,7.0000000000000036]`.
The deviations in Xmax and Ymin are approximately 3.13090361111 mm. The record shows one
valid solid, native structural gate true, geometry/editability false, CAD exit 0,
document_closed true and cleanup_status exited. Reimport was not run for this failed positive.
Evidence: `reports/cad-run/20261012-phase2-fix1-native-r1-mvp1/dev-DV3-positive-mvp1/result.json`.
No assertion is made here about the ultimate cause of these measured bbox deviations;
the measured-value stop was honored before further diagnosis or code/data adjustments.

There are 38 of the 47 offline outcomes remaining unrun. The four requested legacy smokes
and the full post-fix unit regression were not launched after the STOP. The earlier 66-unit
pass remains historical evidence only; this FIX1 turn adds one passing reproducer, not a
claimed 67-test full-suite execution. No test acceptance/live run or provider usage was measured.

### Updated COMMIT PLAN and freeze status

The three original proposed Phase 2 commit groups above remain the selected path plan:
the Probe fix belongs to group 2; the added unit and these updated notes belong to group 3.
The current SHA file is the initial review snapshot and must not be presented as a current
READY freeze. All 131 manifest-listed files other than the Probe and its test remained
byte-identical at FIX1; this includes all descriptions, gold, rubrics, native sources,
faults, tolerances, manifest ordering, compiler, MVP Probe, evaluator behavior and modeling
skill. Original report evidence and `SHA256.json` were not overwritten. The 27 original
protected MVP/legacy/plan files also remain unchanged.

If the supervisor records FIX1 as a separate local commit, its exact group is:

```text
message: fix(cad): handle sampled straight B-spline edges in VERIFY Probe
paths:
tools/cad_verify_probe.py
tools/test_cad_verify.py
design/cad-harness-verify/impl-notes.md
```

Do not stage `.tmp/verify-phase2-fix1/`, reports, dashboard, caches or an automatically
rewritten SHA snapshot. No local commit exists from this turn. Further DV3 diagnosis,
any additional Probe fix and a replacement pre-freeze SHA remain supervisor decisions.

The specified FreeCAD executable ran in the sandbox, so host execution was not required
for this fix. After the DV3 stop is resolved by the supervisor, the still-required commands
are the full native smoke with another fresh prefix, the four legacy smokes and the full
unit command already documented above. They must not be treated as executed FIX1 results:

```powershell
python -B tools\smoke_cad_verify.py --run host-verify-after-DV3-r1-mvp1
if ($LASTEXITCODE -ne 0) { throw 'STOP: positive fixture disagrees with frozen gold' }
python -B tools\smoke_cad_mvp.py --run host-verify-after-DV3-legacy-r1-mvp1 --group legacy
if ($LASTEXITCODE -ne 0) { throw 'STOP: legacy regression failed' }
# Then run the full unit command above, with scoped TEMP/TMP redirection.
```

**FIX1 outcome: DV2 exception fixed; STOP DV3 positive measured bbox mismatch.**

## FIX2 — analytic re-derivation from the frozen dev description

The supervisor authorized analytic verification of DV3 gold first, a description-faithful
fixture-only correction if gold is confirmed, a fixture-vs-description sanity test, and a
fresh full offline batch. No observation is an input to the following derivation.

Sole source: `dev/DV3/description.txt`, verbatim:

> 中心線R31でXY上を直角に曲がる外径14、内径9の管。始点(0,0,0)、接線+X、終点(31,31,0)、接線+Y。両端開口。単位mm。

Thus centerline R=31, outer radius a=14/2=7, inner radius b=9/2=4.5, turn angle π/2.
The specified start/end tangents put the bend center at (0,R,0). With 0≤θ≤π/2,
centerline `C(θ)=(R sinθ, R(1−cosθ), 0)` has tangent `(cosθ,sinθ,0)`, so it starts at
(0,0,0) toward +X and ends at (31,31,0) toward +Y. A normal cross-section point is

```text
P(θ,u,v) = ((R+u) sinθ, R−(R+u) cosθ, v)
b² ≤ u²+v² ≤ a²
```

Since `R−a=24>0` and sinθ/cosθ are nonnegative in this interval, the full outer extrema are:

- Xmin=0 at θ=0; Xmax=R+a=38 at θ=π/2,u=a,v=0.
- Ymin=R−(R+a)=−7 at θ=0,u=a,v=0; Ymax=R=31 at θ=π/2.
- Zmin=−a=−7 and Zmax=a=7 at u=0,v=±a.

These outer-boundary points remain part of the annulus; the inner bore removes none of
the extrema. The description-only bbox is therefore **[0,38,−7,31,−7,7] mm**, exactly
the existing gold. The earlier measured [0,41.13,−10.13,31,−7,7] was not used to derive
any term and is not a reason to change gold. The open caps are x=0 centered at (0,0,0)
and y=31 centered at (31,31,0), with radii 7 and 4.5 in their respective normal planes.
The cross-check volume is `π(a²−b²)·(πR/2) = 4398.142461235445 mm³`.

Gold, tolerances and gates are retained unchanged. Fixture inspection and any source
correction must preserve precisely these centerline, normal section, bore and cap conditions.

### FIX2 finding: the fixture-only premise does not hold

Observed 2026-10-12 08:58:46 UTC / 17:58:46 JST. All inspections/tests used only the
specified headless `FreeCAD_1.1.4-Windows-x86_64-py311/bin/freecadcmd.exe`, no GUI/Sol/Git.
An unchanged-geometry inspection, saved under `.tmp/verify-phase2-fix2/`, found that
FreeCAD exposes both ordinary `BoundBox` and `optimalBoundingBox()` for this native solid.
The two APIs returned the following on the **same unchanged fixture solid**:

| Coordinate | Description-derived target | Original ordinary BoundBox | Original optimalBoundingBox |
| --- | ---: | ---: | ---: |
| Xmin | 0 | -3.8857805861880495e-15 | -3.8857805861880495e-15 |
| Xmax | 38 | 41.13090361111099 | 38.000000000000014 |
| Ymin | -7 | -10.130903611110973 | -7.0000000000000036 |
| Ymax | 31 | 31.000000000000014 | 31.00000000000001 |
| Zmin | -7 | -7.000000000000015 | -7.000000000000014 |
| Zmax | 7 | 7.0000000000000036 | 7.000000100000004 |

The ordinary bounds conservatively enclose the exact surface. Their excess is a measurement
representation issue; neither a dimensional arithmetic error in gold nor a physical oversize
proved in the fixture. Its exact native solid is valid and has volume 4398.142461235451 mm³.
The fixture's native Revolution ReferenceAxis is normalized by FreeCAD to `['Axis']`; this
also explains why the existing Probe's `Axis<number>`-only construction-dimension tracing
does not collect its 31 mm constraint. That tracing behavior was observed and not modified.

An independent, description-only AdditivePipe candidate was constructed in scratch files:
an annular YZ profile at the origin, a constrained quarter-circle XY spine centered at
(0,31,0), Frenet mode and Constant transformation. It has no gold/Probe lookup and was
not installed into the frozen fixture corpus. The candidate is a valid native solid,
all objects up-to-date, volume 4398.142461235451 mm³. It gives **the same ordinary bbox
oversize** despite a different construction and precise bounds
`[-9.999999572450312e-08,38.00000010000001,-7.000000100000002,31.00000009999988,-7.0000001000000145,7.000000100000004]`.
This rules out correcting the reported bbox just by replacing Revolution with a correctly
oriented Frenet sweep. No incorrect tube dimensions were substituted to force an ordinary
boundbox match. The scratch candidate is diagnostic evidence, not a revised positive.

Evidence files:

```text
.tmp/verify-phase2-fix2/inspection-stdout.txt
.tmp/verify-phase2-fix2/inspection-stderr.txt
.tmp/verify-phase2-fix2/comparison-stdout.txt
.tmp/verify-phase2-fix2/comparison-stderr.txt
.tmp/verify-phase2-fix2/candidate.py
.tmp/verify-phase2-fix2/sanity-stdout.txt
.tmp/verify-phase2-fix2/sanity-stderr.txt
```

The native fixture-vs-description sanity test is `tools/test_verify_dv3_native.py`.
It reads **only the frozen dev description**, derives R/OD/ID and the bbox/volume from it,
builds the unchanged original fixture, and checks a valid single solid, precise world
bbox, both open annular cap centers, outward normals, inner/outer radii and areas.
It does not read gold, import the compiler or invoke the VERIFY Probe; it is an independent
sanity test and not a replacement or weakening of any production acceptance predicate.
It passed: one test, 0.205 seconds, native process exit 0, documents_closed true.

Actual native test command, config files created in a fresh diagnostic directory:

```powershell
$FreeCADCmd = 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe'
& $FreeCADCmd --user-cfg C:\dev\CAD-HARNESS\.tmp\verify-phase2-fix2\user.cfg --system-cfg C:\dev\CAD-HARNESS\.tmp\verify-phase2-fix2\system.cfg C:\dev\CAD-HARNESS\tools\test_verify_dv3_native.py
```

The process's `DV3_NATIVE_SANITY_RESULT` was `{"passed":true,"tests":1,"documents_closed":true}`.
The precise bbox used in this independent test differs from analytic extrema only at kernel
tolerance scale (~1e-7 mm). It does not make the ordinary-boundbox VERIFY gate pass.

**STOP reason:** Gold is analytically correct and the original positive already builds the
described solid. Fixing the Probe's ordinary-bbox measurement and its normalized native-axis
tracing is outside the supervisor's fixture-source-only FIX2 scope. No fixture correction
was justified, and the stopped raw Probe measurement remains unchanged. A new full native
batch, legacy4 and full unit rerun would still hit that unchanged gate; they were not launched.
The separate one-test description sanity result is not a claimed full regression result.

### FIX2 changes, integrity and COMMIT PLAN

Changes from the FIX2 starting state are only the new native sanity test and these notes
(plus the required dashboard update). All 133 pre-existing manifest-listed files remain
byte-identical to the FIX2 baseline, including every positive/negative fixture, all gold,
descriptions, tolerances, ordering, Probe, compiler and runtime driver/evaluator code.
Prior failed smoke reports and the stale original review SHA snapshot are preserved.
No revised freeze, real Sol run, Git operation, external publication or permission change.

The original proposed Phase 2 commit group 3 now additionally includes
`tools/test_verify_dv3_native.py`. If the supervisor records this bounded diagnosis separately:

```text
message: test(cad): validate DV3 native fixture against frozen description
paths:
tools/test_verify_dv3_native.py
design/cad-harness-verify/impl-notes.md
```

Do not stage `.tmp/`, reports, dashboard, caches or the scratch Frenet candidate. The added
test runs under the fixed FreeCADcmd and skips when the FreeCAD module is unavailable in
ordinary Python; it is executed explicitly as shown above. A future review/freeze must include
the new test if it is retained. There is no new runtime SHA or local commit from this turn.

**FIX2 outcome: STOP DV3 conservative bbox measurement requires Probe scope.**

## FIX3 — authorized tight bbox and Probe measurement corrections

Supervisor scope: use tight/optimal bbox for all verify-v1 checks and FCStd/STEP agreement;
retain gold/tolerances and the MVP mvp-v1 Probe. Subsequent fixture defects may be corrected
only after description-only analysis; Probe measurement defects may be fixed/logged and
the entire offline batch restarted. No new gold or intended geometry is authorized.

### FIX3 corrections and preserved stopped attempts

1. VERIFY's local `bounds` uses `Shape.optimalBoundingBox(False,False)` on the specified
   FreeCAD 1.1.4 API, disabling triangulation and tolerance padding. Every shape/face/section
   bbox and section plane sizing uses this API. A missing API is an exception, never an
   ordinary-boundbox fallback. Both reimports already dispatch to the selected profile,
   so their bbox agreement now uses the same tight measurements. No MVP Probe edit.
   Mock reproduction proves the flags and MVP's original conservative measurement.
   Native curved-pipe tests show [0,38,-7,31,-7,7] within existing 0.01 mm tolerance, while
   ordinary bounds retain Xmax=41.13090361111099 and Ymin=-10.130903611110973.
2. Fresh full batch `20261012-phase2-fix3-native-r1-mvp1` stopped after eight expected
   outcomes at DV3 positive: geometry=true, editability=false; only requested driving
   dimension 31 mm was missing. Headless inspection shows FreeCAD normalizes the consumed
   `(Sketch,['Axis0'])` reference to `['Axis']`, with exactly one construction line. VERIFY
   now follows this unambiguous used reference; ambiguous unnumbered references do not
   collect arbitrary construction values. A mock covers sole `Axis`, ambiguous `Axis`,
   indexed `Axis0`, built-in `H_Axis` and an unused 99 mm decoy. Gold/axis geometry unchanged.
3. Fresh full batch `20261012-phase2-fix3-native-r2-mvp1` again stopped after eight expected
   outcomes at DV3 positive: construction geometry and editing=true, but FCStd reimport's
   middle normal section failed. STEP passed every geometry check. Saved FCStd/OCC section
   returns two closed degree-1 B-splines (3953/3736 poles), not `Part.Circle` objects, for
   the same analytic circular loops. Measured perimeters 43.98229251769421 and
   28.2743305475467 mm differ from analytic 2*pi*7=43.982297150257104 and
   2*pi*4.5=28.274333882308138 by less than 0.000005 mm; centers match the analytic
   [31*sin(pi/4),31*(1-cos(pi/4)),0]. This follows directly from the already derived normal
   section P(theta,u,v), u^2+v^2=r^2, so gold is confirmed independently of this observation.
   VERIFY now measures these polyline representations: closed loop, center, plane, every
   span's endpoint radius and exact radial minimum, measured normal, original circumference
   and only-requested-loop checks. Arbitrary curved B-splines are not accepted by this fix.
   Linear/axis/circumference tolerances remain 0.01 mm/1e-6/0.01 mm. No loop check is removed.
   A save/reopen native test reproduced the failed original gate then passed after the Probe
   fix; wrong radius and wrong plane are rejected. Native tests: 3 passed in 0.826 s,
   documents_closed=true. FreeCAD's process exit alone is not the native unittest verdict;
   `DV3_NATIVE_SANITY_RESULT.passed` is checked (a failing script also exits process 0).

Observed through 2026-10-12 09:30:15 UTC / 18:30:15 JST. Reproduction evidence in
`.tmp/verify-phase2-fix3/`: bbox-native stdout/stderr, axis stdout/stderr, sections stdout/stderr,
section-api stdout/stderr and section-test-red2/green stdout/stderr. The first red attempt
used an algebraically equivalent midpoint expression whose roundoff selected exact circles;
the reproducer now uses the Probe's original sin/cos expression and records the real gate fail.
Stopped full batch summaries and all original result/artifact files are retained under their
distinct prefixes. Initial full unit discovery passed 70 tests (two native skips) in 3.172 s;
new normalized-axis and reopened-section reproductions were added afterward, so a final
all-unit rerun is still required. Full native restart, legacy4, integrity audit and final
COMMIT PLAN/results remain pending; this entry does not claim a complete offline suite.

### FIX3 r3 — F3 manual fault fixture defect, analytic derivation before source correction

Fresh full batch `20261012-phase2-fix3-native-r3-mvp1` stopped at outcome 46, F3 manual
negative. First 45 outcomes match their expected results; every V/S/Q1 and fault-base positive
passed geometry, editing and independent FCStd/STEP reimport. F1/F2 injected candidates
failed their prescribed checks. F3's manually authored negative incorrectly reused V6's
`omit_finish=True` negative, so real holes passed and finish/volume failed instead. The
frozen F3 fault/candidate unambiguously specify first hole center (-36,-27), diameter 4->6,
with every other dimension, pocket and top outer chamfer preserved. No forced detector
failure or replacement gold is appropriate. Compiled F3 candidate was still unrun at stop.

Description-only re-derivation, before changing any fixture (2026-10-12 09:32:42 UTC):
110*76*12 stock=100320 mm^3; two disjoint 26*18*5 pockets remove 4680 mm^3; six diameter-4,
height-12 holes remove 6*pi*2^2*12=288*pi mm^3. All pockets/holes are disjoint and remain
clear of the external chamfer. For height z=12-c+t, 0<=t<=c=0.8, the outer chamfer retains
rectangle (110-2t)*(76-2t), so integrate removed horizontal area
`110*76-(110-2t)*(76-2t)=2*(110+76)*t-4*t^2` over 0..c. Removed chamfer volume is
`(110+76)*c^2-4*c^3/3=118.35733333333334 mm^3`. Description-derived target is
`100320-4680-288*pi-118.35733333333334=94616.86398243281 mm^3`, exactly unchanged gold.
Original bbox [-55,55,-38,38,0,12] is unchanged by these internal cuts/top edge finish.
The prescribed F3 mutation adds hole removal `pi*(3^2-2^2)*12=60*pi`, giving independent
fault volume **94428.36842321743 mm^3**, while retaining all other features. These terms
come from description and preregistered numeric mutation, not the stopped measurement.

Only `test/F3/manual-negative.py` will be corrected from omit-finish to wrong-first-hole
(existing hand fixture code increases that radius by exactly 1 mm). Frozen fault rule,
candidate spec, description, gold, tolerances and all other fixture sources are preserved.
A minimal source contract test will ensure that this manual native control represents
the sole registered mutation and keeps its prescribed chamfer. Then the full batch restarts
from its first outcome with prefix `20261012-phase2-fix3-native-r4-mvp1`.

### FIX3 final results — full restart, legacy4, all units and integrity

All required offline checks completed on the same final code and fixture state. No further
measurement mismatch occurred. Final native summary measured at 2026-10-12 09:35:03.943977 UTC;
integrity audit completed through 09:37:21 UTC / 18:37:21 JST. All commands used `python -B`.

| Check | Result | Evidence |
| --- | --- | --- |
| Fresh full offline r4 | **47/47 expected**, exit 0, no stop | `reports/cad-run/20261012-phase2-fix3-native-r4-mvp1/smoke-summary.json` |
| Legacy A/B good/broken | **4/4 expected**, exit 0 | `reports/cad-run/20261012-phase2-fix3-legacy-r1-mvp1/smoke-summary.json` |
| All Python unit discovery | **70 passed**, 3 native skips, 73 discovered, 2.529 s, exit 0 | `.tmp/verify-phase2-fix3/units-final-stdout.txt`, `units-final-stderr.txt` |
| Explicit headless native tests | **3/3 passed**, 0.807 s, documents closed, process/verdict exit 0 | `.tmp/verify-phase2-fix3/native-final-stdout.txt`, `native-final-stderr.txt` |
| Protected-file/hash audit | **27/27 protected unchanged**, only four expected FIX3 baseline changes | `.tmp/verify-phase2-fix3/integrity-audit.json` |

All 73 tests were thus executed and passed across ordinary Python and the authorized native
environment. Discovery skips are not counted as native test success. This is offline evidence,
not a live description/model success rate. Model calls, provider tokens and quota consumption
were not measured; real Sol calls remain zero.

Full native smoke consists of 32 geometry-positive/negative V/S/Q1 outcomes, eight Q2/Q3 rubric
outcomes with CAD=0, and seven native fault controls/candidates. All 39 CAD attempts have a
valid native structure and completed owned headless process/document cleanup. All 19 positives
also pass `eval_verify.result_pass`, including independent FCStd/STEP verification, distinct
worker/verifier PIDs, both process exits and closed documents. All 20 native negatives fail
their intended geometry checks; structurally normal editing is separately recorded. Fault
F1 missing groove, F2 missing PCD hole and F3 first oversized hole trigger their frozen
predicates. F3 manual and compiler candidates both measure 94428.36842321744 mm^3, matching
the independently derived mutation volume; finish remains present. No detection flag forces
these raw Probe outcomes, and no correct-source substitution was used.

Legacy results: A good=22239.9556819442 mm^3, A broken=22500; B good=44613.103316864086,
B broken=44751.769983530765. Good cases pass, broken cases fail their original mvp-v1 Probe.
`eval_mvp.py`, `cad_spec.py`, `cad_spec_probe.py`, eval-v1 gold/bar and legacy fixtures remain
byte-identical; the default MVP clarification retry unit also passes unchanged.

Commands actually run after the final fixture correction:

```powershell
python -B tools\smoke_cad_verify.py --run 20261012-phase2-fix3-native-r4-mvp1
python -B tools\smoke_cad_mvp.py --run 20261012-phase2-fix3-legacy-r1-mvp1 --group legacy

$PreviousVerifyTemp = $env:TEMP
$PreviousVerifyTmp = $env:TMP
try {
    $env:TEMP = 'C:\dev\CAD-HARNESS\.tmp\unittest-mvp1'
    $env:TMP = $env:TEMP
    python -B -m unittest discover -s tools -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw 'STOP: unit tests failed' }
} finally {
    $env:TEMP = $PreviousVerifyTemp
    $env:TMP = $PreviousVerifyTmp
}

$FreeCADCmd = 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe'
$NativeOutput = @(& $FreeCADCmd --user-cfg C:\dev\CAD-HARNESS\.tmp\verify-phase2-fix3\user.cfg --system-cfg C:\dev\CAD-HARNESS\.tmp\verify-phase2-fix3\system.cfg C:\dev\CAD-HARNESS\tools\test_verify_dv3_native.py)
$NativeExit = $LASTEXITCODE
$NativeOutput
$NativeLine = @($NativeOutput | Where-Object { $_ -like 'DV3_NATIVE_SANITY_RESULT *' })
if ($NativeExit -ne 0 -or $NativeLine.Count -ne 1) { throw 'STOP: native test verdict missing' }
$NativeVerdict = $NativeLine[0].Substring('DV3_NATIVE_SANITY_RESULT '.Length) | ConvertFrom-Json
if (-not $NativeVerdict.passed -or -not $NativeVerdict.documents_closed -or $NativeVerdict.tests -ne 3) { throw 'STOP: native tests failed' }
```

The invocation was orchestrated by Python subprocess with stdout/stderr captured to the
listed fresh files and a mandatory parsed native verdict. The block above gives the exact
equivalent host commands. FreeCAD runs in this sandbox; host execution was not needed to
obtain these results. Future smoke reruns must use new prefixes, not overwrite r4 or legacy r1.

FIX3 baseline covers 135 files (initial manifest files, the added native test and SHA itself).
Only four baseline entries changed: VERIFY Probe, VERIFY mock tests, the native DV3 test and
F3 manual-negative source. The notes/dashboard are outside that fingerprint scope. All gold,
descriptions, tolerances, rubrics, registered fault rules/candidate specs, other fixtures and
run-order are byte-identical, as is the signed plan. The 27 original protected files all
remain unchanged. The original `SHA256.json` bytes and failed r1/r2/r3 artifacts are retained.
No replacement runtime SHA, Git operation, local commit, external publication or live run
was made. A supervisor current freeze must include the new native test as documented above.
Final read-only `eval_verify.load(ROOT)` correctly rejects the preserved old snapshot with
`sha_mismatch:design/cad-harness-verify/test/F3/manual-negative.py`; it cannot silently launch
the changed pre-freeze implementation as that original version.

### FIX3 updated COMMIT PLAN

The main three proposed Phase 2 groups above now include all FIX3 changes: F3's corrected
manual control is in group 1; tight boxes, normalized used axis and serialized section
measurement are in group 2; both reproduction tests and these notes are in group 3. Stage
only a reviewed current `SHA256.json`, after preserving the original snapshot on the host.
No stale SHA is a READY freeze. If FIX3 is recorded as a separate follow-up local commit:

```text
message: fix(cad): measure tight VERIFY boxes and serialized native geometry
paths:
tools/cad_verify_probe.py
tools/test_cad_verify.py
tools/test_verify_dv3_native.py
design/cad-harness-verify/test/F3/manual-negative.py
design/cad-harness-verify/impl-notes.md
```

Do not stage `.tmp/`, dashboard, reports, caches or unrelated files. The host still owns the
prescribed one implementation/data review, selected local commits and SHA/version freeze.
After these, use the Phase 3 commands above with a fresh prefix and supervisor-maintained
real quota observations; they have not been launched in this offline implementation turn.

**FIX3 outcome: FIX3 DONE uncommitted.**

## FIX4 — Grok SHOULD 1 only, fault reach accounting

Supervisor scope: existing [Grok review](grok-impl-review.md) and
[Gemini review](gemini-impl-review.md) are READY. Apply only Grok SHOULD 1; no other code,
gold, data, fixture, evaluator or Probe changes. Both reviews describe the same premature
`reached=true` accounting. Other SHOULD/NIT items were not implemented. The completed
review evidence is retained verbatim; no new review or real Sol call was made.

### Change and minimal regression test

`tools/cad_verify_guard.py` changes exactly two lines in `Fault.inject`: original-candidate
hash recording no longer marks reached, and the final successful-replacement record update
sets reached=true alongside injected=true, immediately before returning that replacement.
The existing missing-path/non-unique-match returns still return the original object with
`not_reached_reason=candidate_target_missing`, reached=false and injected=false. Attempted
remains true, preserving one-shot/no-retry behavior; hash recording, fault mutation,
settled detection, evaluator bar, deadline and quota decisions are unchanged.

One added test covers missing path, no matching hole and multiple matching holes. Each case
returns the original unchanged candidate, retains the reason and false reach/injection flags,
and does not retry on a later matching candidate. It reproduced three failed subtests before
the fix (1 test, 0.003 s, exit 1) and passed after it. The existing successful source/spec
injection-and-repair test additionally checks both reached and injected=true for F1/F2/F3.
Targeted regression after the fix: 2 tests, 0.119 s, exit 0. Red evidence is preserved at
`.tmp/verify-phase2-fix4/unit-red-stdout.txt` and `unit-red-stderr.txt`.

### Final all-unit and native fault smoke results

Observed 2026-10-12 10:36:49.471348 UTC (fault summary), integrity check through
10:38:49 UTC / 19:38:49 JST. All required checks passed on the final FIX4 state:

- All unit discovery: 74 tests discovered, **71 passed**, three native skips, 2.180 s, exit 0.
  TEMP/TMP were redirected to `.tmp/unittest-mvp1`, using `tools/test_support.py`'s inherited
  workspace ACLs. Evidence: `.tmp/verify-phase2-fix4/units-final-stdout.txt`, `units-final-stderr.txt`.
- The remaining native units: **3/3 passed**, 0.796 s, documents_closed=true, native process
  exit 0 and explicit parsed unittest verdict true. Evidence: `native-final-stdout.txt` and
  `native-final-stderr.txt` in the same diagnostic directory. All 74 units were therefore
  executed and passed across the two environments. FreeCAD logged that empty diagnostic
  config files were malformed and continued with an empty configuration; the recorded
  unittest verdict, rather than process exit alone, establishes test success.
- Fault-only offline smoke: **7/7 expected**, process exit 0, stop_reason=null, real Sol calls=0.
  Fresh prefix `20261012-phase2-fix4-fault-r1-mvp1`; summary
  `reports/cad-run/20261012-phase2-fix4-fault-r1-mvp1/smoke-summary.json`.
  The temporary adapter `.tmp/verify-phase2-fix4/smoke-faults.py` executes the existing
  `cad_run.run_attempt`/compiler/Probe/verifier functions and the actual corrected
  `Fault.inject`/`observe`, without modifying the permanent smoke CLI. F1/F2 original
  source controls pass before their frozen replacement is injected; F3 validates and
  builds the original spec before the frozen numeric mutation. The independent F3 manual
  negative is also checked. No fault flag forces a failure.

| Fault smoke | Raw geometry / editing / reimport | Volume mm^3 | Prescribed detection |
| --- | --- | ---: | --- |
| F1 positive | pass / pass / pass | 26389.378290154265 | control passes |
| F1 injected source | fail / fail / not run | 27143.36052701581 | roller |
| F2 positive | pass / pass / pass | 40276.24434315142 | control passes |
| F2 injected source | fail / pass / not run | 40433.3239758309 | holes |
| F3 positive spec | pass / pass / pass | 94616.86398243284 | control passes |
| F3 manual negative | fail / pass / not run | 94428.36842321744 | holes |
| F3 injected spec | fail / pass / not run | 94428.36842321744 | holes |

All seven attempts retain valid native structure and settled process/document cleanup.
The three positives pass the evaluator's strict final gates, including separate owned
FCStd/STEP verification. For each actual F1/F2/F3 injection, reached/injected/established/
detected are all true; source and numeric replacement bytes/values match their frozen
candidates. The observer's call ordinal 1 is an offline candidate ordinal, not a Sol call.
This smoke does not claim a live repair rate or model success rate. Prior FIX3 full 47/47
and legacy4 evidence is preserved; those broader smokes were not rerun for this metadata-only
change. No additional test feature or permanent smoke option was added.

Commands actually run, with exact equivalent host unit commands:

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
$PreviousVerifyTemp = $env:TEMP
$PreviousVerifyTmp = $env:TMP
try {
    $env:TEMP = 'C:\dev\CAD-HARNESS\.tmp\unittest-mvp1'
    $env:TMP = $env:TEMP
    python -B -m unittest discover -s tools -p 'test_*.py'
    if ($LASTEXITCODE -ne 0) { throw 'STOP: unit tests failed' }
} finally {
    $env:TEMP = $PreviousVerifyTemp
    $env:TMP = $PreviousVerifyTmp
}
python -B .tmp\verify-phase2-fix4\smoke-faults.py --run 20261012-phase2-fix4-fault-r1-mvp1
if ($LASTEXITCODE -ne 0) { throw 'STOP: fault offline smoke failed' }
```

That smoke prefix was executed and is now occupied; any repeat requires a new prefix.
The adapter is diagnostic only and must not be staged. The exact fixed native command was
orchestrated with `subprocess.run`, captured stdout/stderr and a checked JSON verdict:

```powershell
$FreeCADCmd = 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe'
$NativeOutput = @(& $FreeCADCmd --user-cfg C:\dev\CAD-HARNESS\.tmp\verify-phase2-fix4\user.cfg --system-cfg C:\dev\CAD-HARNESS\.tmp\verify-phase2-fix4\system.cfg C:\dev\CAD-HARNESS\tools\test_verify_dv3_native.py)
$NativeExit = $LASTEXITCODE
$NativeOutput
$NativeLine = @($NativeOutput | Where-Object { $_ -like 'DV3_NATIVE_SANITY_RESULT *' })
if ($NativeExit -ne 0 -or $NativeLine.Count -ne 1) { throw 'STOP: native test verdict missing' }
$NativeVerdict = $NativeLine[0].Substring('DV3_NATIVE_SANITY_RESULT '.Length) | ConvertFrom-Json
if (-not $NativeVerdict.passed -or -not $NativeVerdict.documents_closed -or $NativeVerdict.tests -ne 3) { throw 'STOP: native tests failed' }
```

FreeCAD ran successfully in this sandbox, only via the mandated headless executable;
host execution was not required. No GUI, Sol, Git, commit, push, freeze rewrite or live
Phase 3 run. The archive/default `python -B tools\eval_verify.py freeze` sequence and the
current-manifest validation command are specified in the host section above. They are
instructions for the supervisor, not actions performed in this turn.

### FIX4 integrity and final COMMIT PLAN

The FIX4 baseline fingerprints 249 existing tools/design/skill/dashboard files, including
both reviews and the original SHA. Only `tools/cad_verify_guard.py`, `tools/test_cad_verify.py`
and these notes changed. All frozen test/dev data, gold, rubrics, registered faults/specs,
fixture sources, signed plan, Probe, evaluator code, reviews and dashboard remain byte-identical.
All 27 original protected files are unchanged. Audit evidence is under
`.tmp/verify-phase2-fix4/`; runtime reports and temporary diagnostic files are excluded
from commits. The pre-fix SHA is still byte-identical and stale, pending supervisor archive
and creation of a current manifest. No gold/data adjustment was made.

The final three Phase 2 commit groups above are current: corrected reach accounting is in
group 2; its regression test, reviews, final notes and host-created SHA/archive are in group 3.
If a separate FIX4 follow-up commit is desired after the preceding implementation commits:

```text
message: fix(cad): count fault reach only after successful injection
paths:
tools/cad_verify_guard.py
tools/test_cad_verify.py
design/cad-harness-verify/impl-notes.md
```

Stage only the listed paths for each group; exclude `.tmp/`, reports, caches, dashboard and
unrelated changes. Grok/Gemini READY review files are existing evidence, not modified in
FIX4. No new review call is needed for the requested scope. Complete host commits and the
fresh SHA/version freeze before any Phase 3 batch, using a fresh run prefix and real quota
observations as documented above. Gemini SHOULD 2 and all other review items are untouched.

**FIX4 outcome: FIX4 DONE uncommitted.**
