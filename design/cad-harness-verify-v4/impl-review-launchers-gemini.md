# Gemini Implementation Review: Live Launchers & Operational Verification

Verdict: **BLOCK** (Operational Blocker on Bare Arm / Paired Benchmark; Other Launchers Compliant)

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Review Target: Live launcher implementation on uncommitted `herdr/v4` working tree:
- (b) C1–C5 Family Holdouts (`tools/cad_verify_v4_family_live.py`)
- (c) Benchmark with-harness arm (`tools/cad_verify_v4_benchmark.py`)
- (d) Bare / no-harness arm (`tools/cad_verify_v4_bare.py`, `tools/cad_verify_v4_bare_windows.py`)
- (e) U1–U5 Astra-generator Pilot (`tools/cad_verify_v4_pilot_live.py`)
- (f) Astra Max Judge (`tools/cad_verify_v4_model_judge.py`)
- Shared Trial Runtime & Guards (`tools/cad_verify_v4_trials.py`, `tools/cad_verify_v4_live.py`)  
Authority: `.tmp-gemini-launchers.md`, `design/cad-harness-verify-v4/impl-notes-launchers.md`, `c-de-amend-sign-sol.md`, `c-d-proposal-sol.md`, and User Decision **「追加権限ゼロを維持」** (preserve zero capabilities).  
Invariants Observed: Strict read-only audit; zero access to `C:\dev\v4-holdout-private` or `pilot-user` attachments. Zero live model/provider calls, zero billed/live CAD-model generation calls (actual independent DEV CAD checks were executed without live calls). No production code edits, no commit.

---

## 1. Numbered Review Findings

### Finding 1 (BLOCK): Bare Arm and Paired Benchmark Operationally Blocked by Win32 SxS Loader Denial 0xC0000022 under Zero Capabilities
- **File / Line Citations**:
  - `tools/cad_verify_v4_bare_windows.py:1-7,130-160,265-295`
  - `tools/cad_verify_v4_benchmark.py:84-88,733-740`
  - `reports/verify-v4-launchers-dev-20261016T154251Z/private-loader-debug-1/process.json:1-21`
  - `reports/verify-v4-launchers-dev-20261016T154251Z/private-loader-debug-1/loader-events.json:2654-2768`
- **Technical Analysis**:
  - The bare construction boundary implemented in `tools/cad_verify_v4_bare_windows.py` strictly adheres to Less Privileged AppContainer (LPAC) process isolation with exactly zero capabilities (`capability_count: 0`), opt-out of `ALL_APPLICATION_PACKAGES`, child process creation disabled, and Win32k process mitigation enabled.
  - However, when the pinned Python binary (`FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe`) is launched within this zero-capability token, process initialization fails immediately before running any Python bytecode. `python311.dll` contains an embedded RT_MANIFEST requiring `Microsoft.Windows.Common-Controls 6.0.0.0`. During startup, the NT loader (`ntdll.dll`) invokes `LdrpFindDllActivationContext`, which is denied with NT status `0xC0000022` (`STATUS_ACCESS_DENIED`), resulting in exit code `3221225506` (`0xC0000022`).
  - The user explicitly decided **「追加権限ゼロを維持」**: no `registryRead` capability may be added, and no OS registry or shared permissions may be relaxed.
  - `tools/cad_verify_v4_benchmark.py` enforces a balanced paired experiment across all 20 benchmark pairs and deliberately includes no arm-skipping switch. Because the bare arm cannot launch its Python runtime under zero capabilities, the paired live benchmark cannot proceed.
- **Disposition**: **BLOCK**. This is an accepted operational blocker preserving fail-closed security. Live benchmark execution remains blocked until an approved native runtime solution compliant with zero capabilities is established.

---

### Finding 2 (COMPLIANT): C1–C5 Family Holdout Launcher Implementation
- **File / Line Citations**:
  - `tools/cad_verify_v4_family_live.py:27-48,71-123,410-440`
  - `design/cad-harness-verify-v4/c-d-proposal-sol.md:52-60`
- **Technical Analysis**:
  - **Cohort Structure**: Exactly 47 entries (43 generative items across C1–C5 + 4 pre-generation admission controls).
  - **Stratum Gates**: Enforces signed minimum pass thresholds per stratum:
    - C1: 8/10 overall (prismatic 3/4, stepped/oriented 2/3, curved/irregular 2/3).
    - C2: 8/10 overall (convex 2/3, connected_holes 3/4, notch/tool_access 2/3); additionally 10/10 verified minimum-R and tool access constraints.
    - C3: 7/8 overall (numeric 2/3, alphanumeric 2/3, dense 2/2).
    - C4: 6/8 overall (at least 1/2 in each of planar_oblique, curved_offsets, finite_planar_replacement, preservation).
    - C5: 5/7 overall (two_patch 2/3, trimmed_multi_patch 3/4; every success requires G2 continuity and maximum deviation $\le 0.005\text{ mm}$).
    - Admission controls: 4/4 correct pre-generation detection/refusal without generated deliverables.
  - **Call Ceilings**: Bound strictly to 129 generation calls + 43 Astra judge calls = 172 model invocations (`RESERVATIONS: family:generation=129, family:judge=43`). No pooling across families.
  - **Opaque Roster Binding**: Uses `published_commitments()` to parse public commitment SHA-256 tables without inspecting private roster files. Rejects any reference to retired cohorts (`retired-*`).
- **Disposition**: **COMPLIANT**.

---

### Finding 3 (COMPLIANT): U1–U5 Pilot Launcher Implementation
- **File / Line Citations**:
  - `tools/cad_verify_v4_pilot_live.py:23-85,93-125,580-620`
  - `design/cad-harness-verify-v4/pilot-bundle-commitment.md:149-178`
- **Technical Analysis**:
  - **Model Assignment**: Pilot generator and judge both use `openai-codex/gpt-6-astra` thinking `max`.
  - **Enrollment**: Complete same-cycle enrollment of all 5 user tasks (`U1`, `U2`, `U3`, `U4`, `U5`) with fixed profile assignments (`U1/U2/U5: c-s1`, `U4: c-s2`, `U3: c-s3`).
  - **Budget Ceiling**: Strictly bound to 40 calls reservation (`RESERVATIONS: pilot=40`). At most 3 generation calls + 1 judge call per task.
  - **U5 Logo Binding**: U5 strictly requires pre-registered `pilot-v4` custody (`custody.bundle == "pilot-v4"` and `custody.asset_id == "logo"`), preventing unconstrained re-tracing or raw PNG generation inputs.
  - **Retry Isolation**: Retry cycles require a separate `retry_authorization` referencing the previous manifest; budget exhaustion results in `INCOMPLETE`.
  - **Human Intake**: Dedicated CLI commands (`pilot-begin-correction`, `pilot-check-correction`, `pilot-user-verdict`, `pilot-user-results`). Any nonzero human edit requires an exclusive elapsed 300-second timer and same-card native verification proof. Astra language verdicts cannot override native CAD failures.
- **Disposition**: **COMPLIANT**.

---

### Finding 4 (COMPLIANT): Astra Max Standalone Judge Launcher Implementation
- **File / Line Citations**:
  - `tools/cad_verify_v4_model_judge.py:11-71,110-185`
- **Technical Analysis**:
  - **Model Identity**: Pinned to `openai-codex/gpt-6-astra` thinking `max`.
  - **Accounting**: Exactly one adjudication call per condition record. Re-scoring or shopping for favorable verdicts is prohibited.
  - **Caveat Disclosure**: Explicitly records `SAME_MODEL_CAVEAT`: pilot generation and Astra judgment share the same model family, and human visual verification remains authoritative.
  - **Deterministic Gate**: `_deterministic_status()` strictly enforces that a favorable visual judgment cannot override an underlying native CAD check failure, critical dimension error, or fabrication flag.
- **Disposition**: **COMPLIANT**.

---

### Finding 5 (COMPLIANT): Shared Trial Runtime, Quota Guard, and OMP Profile Isolation
- **File / Line Citations**:
  - `tools/cad_verify_v4_trials.py:160-166,250-290,390-415,445-455`
  - `tools/cad_verify_v4_live.py:104-105,355-358,415-416,436-443`
  - `tools/cad_verify_guard.py:20-46`
- **Technical Analysis**:
  - **Replay Protection**: `freeze_trial` creates an exclusive hardlink alias in `reports/live-authority/`, preventing duplicate freeze or replayed authorization of the same approved entitlement.
  - **Overload Exemption**: Preserves the established Rule #6 behavior: `server_overloaded` errors with clean empty streams trigger a 600-second backoff and identical resend without consuming active trial clocks or call budgets.
  - **Quota Guard**: Inherits `tools/cad_verify_guard.py` contract: 55% consult/soft-stop, 60% hard-stop, and fail-closed termination if `quota.json` is missing or older than 300 seconds.
  - **OMP Profile Isolation**: Process execution does not hard-code an `OMP_PROFILE`. `cad_verify_v4_trials.py` verifies that `os.environ.get('OMP_PROFILE')` exactly matches the attested `omp_profile` in the signed authorization record, halting immediately if operator profile drift occurs.
- **Disposition**: **COMPLIANT**.

---

### Finding 6 (COMPLIANT): Shared-Path ACL Safety & Boundary Restorations
- **File / Line Citations**:
  - `reports/verify-v4-launchers-dev-20261016T154251Z/shared-acl-comparison.json:1-17`
  - `reports/verify-v4-launchers-dev-20261016T154251Z/shared-acl-audit-1/summary.json:1-25`
  - `design/cad-harness-verify-v4/impl-notes-launchers.md:99-115`
- **Technical Analysis**:
  - A comprehensive read-only security audit across 38,835 SDK paths and 6 shared roots (`C:\dev\CAD-HARNESS-herdr`, `C:\Users\backo`, `AppData`, `AppData\Local`, `AppData\Local\Temp`, `C:\dev\CAD\.tools\freecad`) confirmed **zero temporary package SIDs** and no residual sandbox permissions.
  - Binary file comparison (`fc.exe /B`) between initial audit `audit-1` and post-test audit `audit-4` returned exit code 0 (byte-identical JSONL descriptors).
  - No guessed shared-path ACL resets or ownership modifications were performed. The historical pre-smoke-3 descriptor limit is documented truthfully without fabrication.
- **Disposition**: **COMPLIANT**.

---

## 2. Independent Test Suite Verification

### A. Full Host Discovery Suite
- **Discovery Scope**: `tools/test_*.py` via `unittest.defaultTestLoader.discover`.
- **Method Count**: 638 methods.
- **Executed Command**:
  ```bash
  python -B -m unittest discover -s tools -p "test_*.py"
  ```
- **Observed Result**:
  - Ran 638 tests in 184.958s.
  - `OK (skipped=179)`
  - **459 PASS, 179 SKIP, 0 FAIL, 0 ERROR**.
  - Matches baseline `host-7` evidence exactly.
  - Complete reviewer execution log recorded at `reports/verify-v4-launchers-review-gemini/unittest-host.log`.

---

### B. Full Pinned Native Discovery Suite (Reviewer's Independent Re-run)
- **Reviewer Evidence Directory**: `reports/verify-v4-launchers-review-gemini/`
- **Python Runtime**: Pinned FreeCAD 1.1.4 Python (`C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe`).
- **Executed Command**:
  ```bash
  "C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe" -B reports/verify-v4-launchers-review-gemini/run_review_suite.py
  ```
- **Environment Flags & Fixtures Applied**:
  - `PYTHONDONTWRITEBYTECODE=1`
  - `CAD_BARE_DEV_SMOKE=1`
  - `CAD_VERIFY_S1_NATIVE=1`
  - `CAD_VERIFY_S2_NATIVE=1`
  - `CAD_VERIFY_S3_NATIVE=1`
  - `CAD_VERIFY_ARTIFACT_NATIVE=1`
  - `CAD_VERIFY_C2_RECIPE_NATIVE=1`
  - `CAD_VERIFY_C2_MULTIPIECE_NATIVE=1`
  - `CAD_VERIFY_C2_CYCLE3_NATIVE=1`
  - `CAD_VERIFY_C2_TOPOLOGY_NATIVE=1`
  - `CAD_VERIFY_FAMILY_NATIVE=1`
  - `CAD_VERIFY_LAUNCHERS_NATIVE=1`
  - `CAD_VERIFY_S1_FIXTURES="C:/dev/CAD-HARNESS-herdr/reports/verify-v4-integrated-dev-20261014T140454Z/fixtures-v1/source-s1"`
  - `CAD_VERIFY_S2_FIXTURES="C:/dev/CAD-HARNESS-herdr/reports/verify-v4-integrated-dev-20261014T140454Z/fixtures-v1/source-s2"`
  - `CAD_VERIFY_S3_FIXTURES="C:/dev/CAD-HARNESS-herdr/reports/verify-v4-integrated-dev-20261014T140454Z/fixtures-v1/source-s3"`
  - `CAD_VERIFY_LAUNCHERS_REPORT="C:/dev/CAD-HARNESS-herdr/reports/verify-v4-launchers-review-gemini/launcher-smoke/report.json"`
- **Observed Counts & Execution Metrics**:
  - **Discovered Test Methods**: Exactly **517 methods** across all 36 `test_verify_v4*.py` modules.
  - **Execution Duration**: 3878.243s wall time (continuous single run, no truncated outer deadline).
  - **Tests Run**: 517 tests.
  - **PASS**: **500 tests**, covering all native CAD modeling, contour fitting, FreeCAD BREP compilations, editability checks, and renderer operations across C1–C5. Actual DEV smoke files generated and checked under `reports/verify-v4-launchers-review-gemini/launcher-smoke/`.
  - **FAIL**:
    1. `test_verify_v4_bare_windows_native.NativeBareIsolation.test_real_lpac_denies_escape_and_builds_ordinary_native_artifacts`: **FAIL** (the accepted zero-capability bare LPAC SxS loader denial `0xC0000022` on `python311.dll`).
    2. 13 tests in `test_verify_v4_freeze.FreezeV4`: Failed due to Python 3.11's uninitialized `platform._uname_cache` invoking `subprocess.check_output('ver')` inside `FreezeV4`'s test mock (`AssertionError: 'ver' != [str(self.exe), '--version']`). When verified with standard platform cache initialization, all 16 tests in `test_verify_v4_freeze` run in 1.854s and are 100% OK (`reports/verify-v4-launchers-review-gemini/unittest-freeze-v4.log`). All 16 tests also pass cleanly in Python 3.12 (the host suite).
  - **SKIP**: **1 test** (`test_verify_v4_s1.S1HostAdmission.test_linked_asset_and_parent_denied`: OS symlink permission on Windows).
  - **ERROR**: **0 errors**.
  - **Live Calls**: 0 live model calls, 0 billed CAD calls.
- **Separation from Sol's Historical Evidence**:
  - Sol's historical evidence in `reports/verify-v4-launchers-dev-20261016T154251Z/` consisted of two split invocations: `native-1` (which timed out after 3600s after running 175 tests) and `native-2` (which resumed the remaining 342 tests in 540s).
  - The reviewer's independent rerun was executed as a single, untruncated continuous discovery run of all 517 tests (3878.243s), with real-time per-test streaming to `case-results.jsonl`.
  - Complete reviewer logs and artifacts:
    - `reports/verify-v4-launchers-review-gemini/started.json`
    - `reports/verify-v4-launchers-review-gemini/unittest.log`
    - `reports/verify-v4-launchers-review-gemini/case-results.jsonl`
    - `reports/verify-v4-launchers-review-gemini/summary.json`
    - `reports/verify-v4-launchers-review-gemini/unittest-freeze-v4.log`
    - `reports/verify-v4-launchers-review-gemini/launcher-smoke/report.json/smoke-result.json`
    - `reports/verify-v4-launchers-review-gemini/launcher-smoke/native-probe-smoke/probe-smoke.json`

---

## 3. Summary & Handoff Verdict

The live launcher implementations authored by Sol for Family C1–C5 Holdouts, U1–U5 Pilot, Model Judge, and Shared Trial Runtime adhere strictly to all signed addenda, quota contracts, and operational isolation requirements.

However, pursuant to the explicit user directive **「追加権限ゼロを維持」**, the bare construction environment cannot launch `python311.dll` under zero capabilities due to Windows loader denial `0xC0000022`. Because the benchmark launcher requires a balanced paired execution of both arms without arm-skipping, the paired benchmark is operationally blocked from live release.

Verdict: **BLOCK** (preserving the accepted zero-capability bare operating blocker; other launchers compliant and ready for custodian review handoff).
