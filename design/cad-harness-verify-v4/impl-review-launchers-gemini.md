# Gemini Implementation Review: Live Launchers & Operational Verification

Verdict: **SIGN** (Live Launchers, Public Cardfix Revision & Neutral Proof Verified; Ready for Reviewed Commit/Push & Final Post-Push Lock)

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Review Target: Live launcher implementation on uncommitted `herdr/v4` working tree:
- (b) C1–C5 Family Holdouts (`tools/cad_verify_v4_family_live.py`)
- (c) Benchmark with-harness arm (`tools/cad_verify_v4_benchmark.py`)
- (d) Bare / no-harness arm (`tools/cad_verify_v4_bare.py`, `tools/cad_verify_v4_bare_windows.py`)
- (e) U1–U5 Astra-generator Pilot (`tools/cad_verify_v4_pilot_live.py`)
- (f) Astra Max Judge (`tools/cad_verify_v4_model_judge.py`)
- Shared Trial Runtime & Guards (`tools/cad_verify_v4_trials.py`, `tools/cad_verify_v4_live.py`)  
Authority: `.tmp-gemini-launchers.md`, `design/cad-harness-verify-v4/impl-notes-launchers.md`, `c-de-amend-sign-sol.md`, `c-d-proposal-sol.md`, and User Decisions (2026-10-17 14:40, 2026-10-18 00:06, 2026-10-18 quota-reset, 2026-10-20 card revision & reseal, and 2026-10-20 auxiliary precision redesign & v4claude appointment).  
Invariants Observed: Strict read-only audit; zero access to `C:\dev\v4-holdout-private` or `pilot-user` attachments. Zero live model/provider calls, zero billed/live CAD-model generation calls (actual independent DEV CAD checks were executed without live calls). No production code edits, no commit.

---

## 1. Numbered Review Findings

### Finding 1 (RESOLVED): Bare Arm and Paired Benchmark Boundary & Containment
- **File / Line Citations**:
  - `tools/cad_verify_v4_bare_windows.py:1-7,130-160,265-295,593-596,801-807`
  - `tools/cad_verify_v4_bare.py:25-45,55-75,340-365`
  - `tools/cad_verify_v4_benchmark.py:84-88,733-740,850-856`
  - `reports/verify-v4-launchers-review-gemini/final-native/bare-isolation-receipt.json:1-85`
- **Technical Analysis**:
  - The bare construction boundary strictly implements Less Privileged AppContainer (LPAC) process isolation with `registryRead` as the sole capability, opt-out of `ALL_APPLICATION_PACKAGES`, child process creation disabled, and kill-on-close job objects.
  - Pursuant to USER 2026-10-18 00:06 JST, a narrow Win32k process mitigation exception is applied strictly to the pinned FreeCAD Python host, while shell children (`cmd.exe`) strictly retain Win32k disable.
  - The previous `0xC0000022` (SxS loader denial) and `0xC0000409` (temp directory resolution exception) are completely resolved: `PYTHON_BOOTSTRAP` dynamically queries `GetTempPathW`, verifies containment within `_scratch`, and precreates it safely.
  - Task-private read-only nodes (`inputs/`, `runtime/`, `read_files`) receive a non-inherited protected DACL, preventing parent write grant inheritance.
  - The expectation of executing `cmd.exe del` at scratch root was diagnosed as an overconstraint due to `cmd.exe del`'s internal invocation of `GetVolumeInformationW("C:\\")`. The test asserts that drive-root volume metadata access is denied with access denied (`0xC0000022`), verifies binary shell file operations (`copy /b`, `type`, `ren`), proves transient file deletion natively via Python `ToolLoop`, and publishes a transparent generic limitation disclosure.
- **Disposition**: **RESOLVED / COMPLIANT**.

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

## 2. Independent Test Suite Verification (Historical Review Evidence)

### A. Full Host Discovery Suite (Historical Rerun)
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
  - Reviewer execution log: `reports/verify-v4-launchers-review-gemini/unittest-host.log`.

---

### B. Full Pinned Native Discovery Suite (Historical Rerun)
- **Reviewer Evidence Directory**: `reports/verify-v4-launchers-review-gemini/`
- **Python Runtime**: Pinned FreeCAD 1.1.4 Python (`C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe`).
- **Executed Command**:
  ```bash
  "C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe" -B reports/verify-v4-launchers-review-gemini/run_review_suite.py
  ```
- **Observed Counts & Execution Metrics**:
  - Discovered methods: 517 methods across 36 modules.
  - Execution duration: 3878.243s wall time.
  - Status: 500 PASS, 1 FAIL (`0xC0000022` on bare lpac test before Win32k exception), 13 failures in `FreezeV4` due to cold platform cache mock artifact (which ran 100% OK in isolation), 1 SKIP (`test_linked_asset_and_parent_denied`).
  - Historical reviewer log: `reports/verify-v4-launchers-review-gemini/unittest.log`.

---

## 3. Intermediate Review Records (2026-10-18 Historical)

*(Retained for auditing: sections 3–5 document intermediate diagnostics and initial blocker resolutions).*

- **SxS Loader Denial (0xC0000022)**: Resolved by authorized Win32k exception for pinned FreeCAD Python + `registryRead` capability.
- **Temp Path Resolution (0xC0000409)**: Resolved by dynamic `GetTempPathW` scratch resolution and safe precreation in `PYTHON_BOOTSTRAP`.
- **Input Overwrite Hole**: Resolved by fresh, non-inherited protected DACL on task-private read-only nodes.
- **Shell Del Overconstraint**: Resolved by asserting drive-root volume metadata denial (`GetVolumeInformationW` returns FALSE with access denied) and proving deletion natively via Python `ToolLoop`.

---

## 4. Prior Intermediate Review Records (2026-10-18 Historical)

*(Retained for auditing: sections 4.A–4.F document intermediate diagnostics before final resolution).*

### A. Review of User Decision 2026-10-18 00:06 JST
In `design/cad-harness-verify-v4/DECISIONS.md:91-95`, the user explicitly authorized a narrow process-level Win32k mitigation exception strictly for the private pinned FreeCAD host process.

### B. Audit of Intermediate Evidence (`reports/verify-v4-win32k-dev-20261018T0006JST/`)
- `host-1/summary.json`: 640 tests = 461 PASS, 179 SKIP, 0 FAIL, 0 ERROR (elapsed 204.547s).
- `native-1/summary.json`: 519 tests = 517 PASS, 1 FAIL, 1 SKIP, 0 ERROR (elapsed 4988.375s).
- The prior `0xC0000022` SxS loader denial on `python311.dll` was completely eliminated by the authorized Win32k exception + `registryRead` capability.

### C. Technical Analysis of Abort 0xC0000409 (PID 54556)
- RTTI evidence in `crash-exception-type.txt:78-81` proved the originally thrown exception object was `std::filesystem::filesystem_error`, which escaped `MainPy.cpp` because `PyInit_FreeCAD()` catches only `const Base::Exception&`.

### D. LPAC Diagnostic Evidence vs. Host Experiment Limits
- In `reports/verify-v4-win32k-dev-20261018T0006JST/private-environment-probe/`, actual LPAC child executions with production token, job containment, ACLs, and mitigations were probed. Both probe variants aborted with `0xC0000409`.

### E. Source-Binding Digest at Prior Intermediate Snapshot
- Worktree HEAD: `b673b9af8822d755822c64b8f0c5a6c7c5b80f0e`.
- Prior integrated sources digest: `SHA-256: 3227f8c15c26b96f7331ee5f5590f7109c1f97d647cc2abe331159a95728349d`.

---

## 5. Prior Review: Root-Level Shell DEL Diagnosis (2026-10-18 Historical)

### A. Actual Evidence on Root-Level `cmd.exe DEL`: Drive-Root `C:\` Access Denial
- Retained CDB trace (`shell-delete-api-trace-3/debugger.stdout:67-79`) proved the failure call stack: `cmd.exe`'s internal `del` command invokes `KERNELBASE!GetVolumeInformationW` on system drive root `\??\C:\` with `access=0x100000` (`SYNCHRONIZE`).
- `ntdll!NtOpenFile` returns `0xC0000022` (`STATUS_ACCESS_DENIED`), causing `GetVolumeInformationW` to fail with `ERROR_ACCESS_DENIED`. `cmd.exe` aborts `del` immediately before `DeleteFileW` is ever invoked.
- `shell-workdir-diagnosis/summary.json` proved that even inside a subdirectory, `del` fails identically because `GetVolumeInformationW` queries drive root `C:\` regardless of path depth.

### B. Independent Contract Ruling on `cmd.exe DEL` vs. Signed Envelope
- Signed addendum `c-de-amend-sign-sol.md` (Tools rule 17) promises noninteractive shell and file I/O in an isolated scratch workspace without access to external files. Full file lifecycle operations (create, read, write, rename, and delete/unlink) are fully and natively supported in Python via `os.remove()` and `pathlib.Path.unlink()`.
- Demanding that `cmd.exe del` succeed inside the LPAC boundary was an **OVERCONSTRAINT**, as it would require granting access to external host volume metadata (`C:\`), violating the isolation envelope.

---

## 6. Resolution of Bare Containment & Intermediate Verification (2026-10-18 Historical)

- Dynamic temp directory resolution and protected input DACL verified.
- Intermediate native rerun: `final-native/summary.json` (519 tests, 518 PASS, 1 SKIP, 0 FAIL/ERROR).

---

## 7. Intermediate Review: C2 Recipe Binding Alignment & Reseal Verification (2026-10-20 Historical)

- Reused dual raw/canonical recipe policy via `c2_recipe.load(ROOT)` in `tools/cad_verify_v4_family_live.py`.
- Verified interim lock `reports/verify-v4-reseal-dev-20261019T1635Z/interim-lock/` (`f70257...`).
- Measured source-binding digest: `SHA-256: 637126b8887b5106f2d97a6daf856a441cd1bd69904d51f2868ec4ecc1a63316` (old `DECISIONS.md` `d4473c...`).
- Independent test suite executions:
  - `reseal-host/summary.json`: 640 tests = 461 PASS, 179 SKIP, 0 FAIL/ERROR (183.391s).
  - `reseal-native/summary.json`: 519 tests = 518 PASS, 1 SKIP, 0 FAIL/ERROR (4952.156s).

---

## 8. Prior Review: Re-Auth Reseal & Authority Append Verification (2026-10-20 Historical)

- Documented interim lock `reports/verify-v4-authority-reseal-dev-20261020T0050Z/interim-lock/` (`ef8333...`).
- Measured source-binding digest: `SHA-256: b896e1064d2eb25df8ac6663bcc1059a42db36a6a55571bb9e0b80cbf341c920` (DECISIONS `d0d534...`).
- Bound neutral proof: `reports/verify-v4-authority-reseal-dev-20261020T0050Z/neutral/neutral-proof.json` (`e8e781...`, 5,077 bytes).

---

## 9. Prior Review: Auxiliary Precision Redesign, v4claude Appointment & Interim Handoff (2026-10-20 Historical)

- Documented interim lock `reports/verify-v4-claude-handoff-dev-20261020T0620Z/interim-lock/` (`4b9e9a...`).
- Measured source-binding digest: `SHA-256: 5ee94cd926f593d0dbcfc1225c59b00ed620a1942644e96182f524acd5dc6244` (410 records; DECISIONS `243e2e...`).
- Bound neutral proof: `reports/verify-v4-claude-handoff-dev-20261020T0620Z/neutral/neutral-proof.json` (`9ac926...`, 5,057 bytes, 10/10 PASS).

---

## 10. Gemini Final Public Method & Data Review: Signed Cardfix v2 Publication — **SIGN** (2026-10-20)

- **Reviewer Active Model Identity**: Gemini (`google-antigravity/gemini-3.8-flash`).
- **Review Date**: 2026-10-20.
- **Review Scope & Authority**:
  - Authority: `.tmp-gemini-launchers.md`, `design/cad-harness-verify-v4/DECISIONS.md` (USER 2026-10-20 sections through 15:13 JST), `handoff-v4claude-20261020.md`, and `impl-notes-launchers.md`.
  - Targets Reviewed in Full:
    1. `holdout-families-commitment-cardfix.md`: SHA-256 `253e2a9f367b14bcd412d458c14c84850112e27e4fd6d253a2b110821a35be7f` (46,178 bytes).
    2. `holdout-families-cardfix-controls-v4claude.md`: SHA-256 `169f918f71ec6c80c6a8d7c7c9e2bece4f7b70606cc6901b1177f6332d8a0f2d` (13,402 bytes).
    3. `impl-review-launchers-v4claude.md`: Sections 8 (DATA SIGN for proposal v2 `f665255e...`) and 9 (SOURCE/CUSTODY SIGN for interim lock `4b9e9a...`).
    4. Verified Interim Lock: `reports/verify-v4-claude-handoff-dev-20261020T0620Z/interim-lock/manifest.json` (`sha256_file`: `4b9e9a7e975cafbdd35d82cac5a7b2437df915970ba43bb852415ee7ef0bc4b7`).
    5. Bound Neutral Proof: `reports/verify-v4-claude-handoff-dev-20261020T0620Z/neutral/neutral-proof.json` (`9ac9261047082932a23bd2526951a88bb392423678cba9e6a416addb3714c4bd`, 5,057 bytes, 10/10 PASS).
- **Final Verdict**: **SIGN** (All Live Launchers, Public Method, Revised Cardfix Data & Controls Verified Green; Ready for Reviewed Commit/Push & Final Post-Push Lock).

### A. Technical Audit of Public Method & Cardfix Commitment
1. **User Authority & Invariance**:
   - USER 15:13 JST authorized exclusively the auxiliary native-roundtrip volume maximum / numerical-error budget reregistration on a measured basis, and problematic C4 replacement under identical conditions.
   - All physical requested dimensions, absolute 0.005 mm surface deviation, G2 continuity, operative editability, bounds maximum, and c-s2 donor pair (0.02 mm / 0.08 mm³) remain strictly unchanged.
   - Original 60 items / 91 files in `holdout-original-commitment.md` and original 163 maximum call reservation are untouched. No live call borrowing across pools.
2. **Chronology & Binding Verification**:
   - Preregistration v2 `5bc9df...` (07:58:44Z) < synthetic measurement (07:59:55Z) < freeze `f665255e...` (08:04:13Z) < run1 (08:04:20Z) < run2 (11:12:29Z).
   - Proposal v2 (`f665255e...`, 61,271 bytes) was frozen and hash-bound before any v2 native validation run.
3. **Counts, Strata, and Roster Preservation**:
   - Exactly 15 affected items revised: C5 (5 two_patch, 6 trimmed_multi_patch = 11 items); C4 (4 benchmark items, 1 per signed stratum).
   - 48 unaffected items + 4 refusal admission controls were re-admitted 48/48.
   - Total 43 generative + 4 controls and 20 benchmark pairs remain strictly enrolled without pooling.
4. **Empirical Precision Method & Independence**:
   - Formula $M = \text{eps}\cdot(A_{\text{ref}} + A_{\text{ref}}(1+\rho)) + 128\cdot\text{ulp}(\max(1, V_{\text{ref}}(1+\rho))) + \delta V$ derived from 26 measured synthetic solids across 7 geometric classes ($K = 10, \rho = 0.01$).
   - Preregistered caps: admitted true discrepancy $\le 0.08\text{ mm}^3$ donor intent (at most 29% of it); mean surface displacement $\le 10\%$ of 0.005 mm bound; +M+1 mm³ and absolute +1 mm³ controls stay decisive on all 11 cards.
   - Independent of case item model outputs: measured case item $d$ was not an input.
5. **C4 Fresh Replacements & Retained Preservation**:
   - Fresh cases (B13 planar_oblique, B14 curved_offsets, B15 finite_planar_replacement) satisfy signed capability scope without weaker-scope substitution.
   - Retained preservation (B16) binds prior evidence and independent gold.
6. **Native Controls Verification (run2)**:
   - Full cards judged on both FCStd and STEP representations: Positive 15/15 PASS.
   - Decisive violations (+1 mm translation, +M+1 mm³ volume, absolute +1 mm³ volume, non-body document, uneditable artifact) all defeated 15/15.
   - Independent gold cross-checks: 15/15 PASS. Full-card gate by stratum: 15/15 PASS.

### B. Evaluated Method Limits (Non-Blocking Disclosures)
1. *Empirical Floor & Aggressive Probe*: The volume floor is dominated by one curved-boolean-trimmed solid. The aggressive reviewer probe (tilted cylindrical cut at ~3× area exceeding floor and 0.08 mm³) is a known representation-dependent false-negative risk (for example on boolean-heavy bare-arm outputs), but consistent with donor intent on other cards and does not relax or compromise any physical gate.
2. *Sampled Curved-Offset Scope*: Documented as `sampled` thickness per C-D(c) rule 5, not a global certificate.
3. *Archive / Seal Contract Analysis*: The cardfix tree binds `proposal-frozen.json` plus the 280-file listing (rollup `82e2e9...`). No deterministic zip archive is required by the cardfix contract (unlike the older families-v1 seal convention, which remains intact at `588db92f...`).
4. *Common Mode*: Author and reviewer contexts share the Claude Opus 5.5 model family; reviewer controls mitigated this via independent closed forms and ray chords.

### C. Reused Independent Cold Test Suite Evidence
- **Host Discovery Suite (`reseal-host/summary.json`)**: 640 tests = **461 PASS, 179 SKIP, 0 FAIL, 0 ERROR** in 183.391s. Status: **PASS**.
- **Pinned Native Discovery Suite (`reseal-native/summary.json`)**: 519 tests = **518 PASS, 1 SKIP, 0 FAIL, 0 ERROR** in 4952.156s. Status: **PASS**.
- **Reviewer Bare Isolation Receipt (`reseal-native/bare-isolation-receipt.json`)**: Confirmed returncode 0, real FreeCAD artifacts, LPAC token verified, `registryRead` sole capability.
- Reused unchanged-code test evidence; explicitly not rerun after this documentation review.

### D. Exact Current Source-Binding Digest & File Hashes
- **Measured Worktree HEAD**: `b673b9af8822d755822c64b8f0c5a6c7c5b80f0e`.
- **Integrated Sources Count**: Exactly **410 files**.
- **Current Canonical JSON SHA-256 (`integrated._sources(ROOT)` with `-B`)**:
  `SHA-256: 5ee94cd926f593d0dbcfc1225c59b00ed620a1942644e96182f524acd5dc6244`.
- **Historical Source Digests for Audit**:
  - Section 8 snapshot: `b896e1064d2eb25df8ac6663bcc1059a42db36a6a55571bb9e0b80cbf341c920` (DECISIONS `d0d534...`)
  - Section 7 snapshot: `637126b8887b5106f2d97a6daf856a441cd1bd69904d51f2868ec4ecc1a63316` (old DECISIONS `d4473c...`)
  - Section 6 snapshot: `43494d9828cb226d3b08e5f1ae3110e5771a7fb1a3eaa51f366d6b60f10e42ac`
  - Section 5 snapshot: `3227f8c15c26b96f7331ee5f5590f7109c1f97d647cc2abe331159a95728349d`
- **Launcher Implementation & Test File Digest Table (Current Measured Bytes)**:

| SHA-256 Digest | Bytes | Relative Path |
| :--- | ---: | :--- |
| `f7bb489f3a24c24835fc3e591b3e3f3afd7edead02bf926c32d238d20b4e5c75` | 51488 | `tools/cad_verify_v4_bare_windows.py` |
| `be8d7be3b862cc44d39ea9d6708d309f6604d85aff97fbc67cf290a5233e29da` | 29121 | `tools/cad_verify_v4_bare.py` |
| `5b76012a31e4e2e74bb7407e3a7895b3fbf852f77a723501c880749f6dfd3c46` | 83930 | `tools/cad_verify_v4_benchmark.py` |
| `4bf19a85e479c1e73c8e383b8dd1c16c30cb9ffa1c09b5f1e4bc71a2cb44a529` | 33907 | `tools/cad_verify_v4_family_live.py` |
| `842916b5dff78a0e7ca2267d9fad41a9d4e4580c0678ffe38f4c2be137c0a6ca` | 53166 | `tools/cad_verify_v4_pilot_live.py` |
| `96e89d66bc0768a984022b9695174404b81efbfa31bbc516992292e78125da3b` | 12487 | `tools/cad_verify_v4_model_judge.py` |
| `50b4cd49f856357500862ad65ab5c9f130337eb77eea7fc8cb07d6cbf501e1c5` | 53388 | `tools/cad_verify_v4_trials.py` |
| `54526d09981e43c2aca312bcb404160edde72df55882a3c39119d11e9625b8a5` | 40926 | `tools/cad_verify_v4_live.py` |
| `86fd36eb8c99e66547e29adf81f5940cfefcfc24a01168099339757f981ab01b` | 35343 | `tools/eval_verify_v4.py` |
| `3c94cc9772eb8c7814d19592c7b31606984f5ce2d80fd74f66b82e8843129777` | 36503 | `tools/test_verify_v4_bare.py` |
| `27c2c8a2f09cd778e5c8ece79267654658e821838966324209c9e48c114b132e` | 32774 | `tools/test_verify_v4_bare_windows_native.py` |
| `e454129e2a64fac28d13c145b017f8945c32058f57ea0aca5838df016590e744` | 31358 | `tools/test_verify_v4_benchmark.py` |
| `ce6c9fe2bf956ae99764b5478b359cea3f14a1e0f10d5bccd2080ab0d19a6fd0` | 49991 | `tools/test_verify_v4_family_live.py` |
| `cebf052e79c8aedc6fe7987fff7c7159dd417db70845be7165176c8a6b588fb8` | 19536 | `tools/test_verify_v4_freeze.py` |

---

### E. Final Operational Roadmap & Conclusion
All launcher modules (C1–C5 Family Holdouts, Benchmark With-Harness and Bare Arms, U1–U5 Pilot, Astra Max Standalone Judge, and Shared Trial Runtime), the public cardfix commitment, aggregate controls report, and interim implementation lock (`4b9e9a...`) are completely verified and green. All operational blockers are resolved without rights expansion.

This review confirms method, data, and launcher readiness. It is **NOT** an authorization, a live-call admission, or a `final_v4_ready` claim. The sequence remains:
1. Sol explicit reviewed commit and push on `herdr/v4` excluding `__pycache__`, private custody files, reports, and `.tmp` files.
2. Issuance and authoritative verification of a NEW post-push implementation lock containing all 5 recipes.
3. Conditional admission of the original 163-call maximum live budget under fresh quota verification (consult at 55%, hard stop at 60%).
4. Separate operational authorizations for family, benchmark, and pilot live pools (zero budget borrowing).

Final Verdict: **SIGN**
