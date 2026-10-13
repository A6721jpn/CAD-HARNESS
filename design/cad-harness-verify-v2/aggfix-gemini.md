# CAD-HARNESS VERIFY v2 Aggfix Review (Gemini, 2026-10-13 10:48 JST)

Reference: [`design/cad-harness-verify-v2/AGGFIX-BRIEF.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/AGGFIX-BRIEF.md)

## Verdict: AGREE

Gemini agrees with the Option A minimal fix design proposed in `AGGFIX-BRIEF.md`.

---

## Technical Assessment & Concurrence

### 1. Float Rounding Bug (`deadline_monotonic - started_monotonic`)
- **Diagnosis Confirmed**: In [`reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/suite-run.json`](file:///C:/dev/CAD-HARNESS/reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/suite-run.json#L9-L10), `started_monotonic = 514542.359` and `deadline_monotonic = 525342.3589999999`. The IEEE 754 64-bit float subtraction yields `10799.999999999942`, which fails exact equality `!= 10800` by $\approx 5.82 \times 10^{-11}$ seconds.
- **Approved Fix**: Replace line 547 of [`tools/eval_verify_v2.py`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v2.py#L547):
  ```python
  # Old:
  or observed["deadline_monotonic"]-observed["started_monotonic"]!=10800): raise ValueError("suite_record_binding")
  # New:
  or abs((observed["deadline_monotonic"]-observed["started_monotonic"])-10800) > 1e-6): raise ValueError("suite_record_binding")
  ```
- A $1\,\mu\text{s}$ ($10^{-6}$ s) tolerance cleanly absorbs floating-point representation noise while strictly enforcing the 3-hour limit against real drift (e.g., 10799.9 s or 10801 s).

### 2. Unit Test
- Concur with adding a dedicated test in [`tools/test_verify_v2.py`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v2.py) verifying:
  - `deadline_monotonic - started_monotonic = 10799.999999999942` is **accepted** ($\Delta \approx 5.82 \times 10^{-11} \le 10^{-6}$).
  - `deadline_monotonic - started_monotonic = 10799.9` is **rejected** ($\Delta = 0.1 > 10^{-6}$, raises `ValueError("suite_record_binding")`).
  - `deadline_monotonic - started_monotonic = 10801.0` is **rejected** ($\Delta = 1.0 > 10^{-6}$, raises `ValueError("suite_record_binding")`).

### 3. Manifest Preservation & Binding Architecture
Gemini confirms the brief's archived manifest approach as sound and necessary. The exact dual-manifest verification logic should be:
1. **Archive Original Run Manifest**:
   - Copy current [`design/cad-harness-verify-v2/SHA256.json`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v2/SHA256.json) byte-identically to `design/cad-harness-verify-v2/SHA256.run-r1.json` (SHA-256 `129087752bd9a9fb4060dbd96bea58157dbb5dc1adc42c4dd7c1be4db84132d8`, version `verify-v2-reviewed-r1`).
2. **Re-freeze Aggfix Version**:
   - Re-freeze to produce fresh `design/cad-harness-verify-v2/SHA256.json` with `version: "verify-v2-reviewed-r1-aggfix"` using `--codex codex.exe`.
3. **Dual-Binding in `aggregate()`**:
   - `load(root)` enforces `verify_frozen(root, manifest)` against the new `SHA256.json` (verifying workspace integrity on disk).
   - If `design/cad-harness-verify-v2/SHA256.run-r1.json` exists, load `run_manifest` and check:
     - `observed["version"] == run_manifest["version"]` (`"verify-v2-reviewed-r1"`)
     - `observed["sha_manifest"] == sha(SHA256.run-r1.json)` (`129087752b...`)
     - `plan["sha_manifest"] == sha(SHA256.run-r1.json)` (`129087752b...`)
     - `observed["frozen_sha256"] == run_manifest["files"]`
     - Per-episode driver identities check against `run_manifest["files"]`.
     - **Scope Guard**: assert `{k for k in set(manifest["files"]) | set(run_manifest["files"]) if manifest["files"].get(k) != run_manifest["files"].get(k)} <= {"tools/eval_verify_v2.py", "tools/test_verify_v2.py"}`.
   - If `SHA256.run-r1.json` does not exist, default `run_manifest = manifest` to preserve backward compatibility for standard unpatched runs.

### 4. Non-Overwrite Output
- Aggregation outputs strictly to fresh files:
  - `reports/aggregate-verify-v2-host-reviewed-r1-aggfix.json`
  - `reports/aggregate-verify-v2-host-reviewed-r1-aggfix.csv`
- Neither file exists; no existing aggregates are overwritten.

### 5. Scope Boundaries
- **No changes** to scoring formulas, analytic gold values, bar thresholds, prompt payloads, run order, runner dispatch, or FreeCAD/Sol execution.
- All 60 completed episodes in `reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/` remain untouched.
- `FROZEN.md` documentation will accurately record the float-rounding fix, git diff, and rationale.

consensus: AGREE 2026-10-13 10:59:00 JST
