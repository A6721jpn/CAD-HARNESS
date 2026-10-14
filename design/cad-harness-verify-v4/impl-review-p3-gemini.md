# Gemini Implementation Review: VERIFY v4 Phase 3

Verdict: **READY**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).
Reviewed:
- `design/cad-harness-verify-v4/impl-notes-p3.md`
- `tools/eval_verify_v4.py` (uncommitted diff)
- `tools/cad_verify_v4_freeze.py`
- `tools/cad_verify_v4_live.py`
- `tools/cad_verify_v4_pilot.py`
- `tools/test_verify_v4_freeze.py`
- `tools/test_verify_v4_pilot.py`
- `tools/test_verify_v4_live.py`

Verification: Ran full test suite via `python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live`. All **92 tests PASS** deterministically in 5.25s.
No live model calls were launched, no CAD processes were executed, no git commit was made, and `C:\dev\v4-holdout-private` was not opened.

---

## 1. Audit Checklist & Findings

### A. 163-Call Budget & #6 Overload Policy
- **Budget Enforcement**: `LiveGuard` in `tools/cad_verify_v4_live.py` strictly bounds execution to `call_budget = 163`. Invocations reserve a charged slot prior to launch (`before_call()` raises `Stop("insufficient_call_budget")`).
- **Overload Classification**: Only an authentic provider rejection (`codex_error_info=server_overloaded`) with verified complete stream parsing and zero assistant/final output is classified as `provider_rejected = True` (`exempt = True`). Output-bearing errors or malformed streams are never exempt.
- **Clock Exclusion**: Verified overload cycles (rejection transport plus 600-second backoff) are explicitly subtracted from enclosing active stage and episode deadlines via `self.clock.exclude()`, while full elapsed wall-clock duration is recorded in the ledger.
- **Identical Resend**: The identical command argv, payload file, and configuration are resent without an arbitrary retry cap. Interruptions during wait safely decrement the reserved slot. Overload recovery is certified only upon real rejection $\to$ 600s wait $\to$ accepted response.

### B. Complete Stdout/Stderr Capture to Disk
- **Direct-to-Disk Streaming**: `stream_process()` and `ledger.StreamCapture` stream raw binary chunks (8192 bytes) directly to `attempt-XXXX/stdout.bin` and `stderr.bin` across separate daemon threads.
- **Interruption Safety**: In-flight process terminations, timeouts, or cancellations drain remaining pipe buffers and record byte totals and SHA-256 digests. If stream draining fails, an `OSError("capture_drain_did_not_finish")` halts execution immediately.
- **Bounded In-Memory Tail**: In-memory inspection and display are strictly bounded by `TAIL_BYTES = 16384`, preventing heap exhaustion during extended runs.

### C. Null is Never Treated as Zero
- **Nullable Aggregations**: Usage counters, billing metrics, and elapsed durations utilize `ledger.unknown_usage()`, `ledger.nullable_total()`, and `ledger.price()`. Missing values propagate as `null` with explicit missing reasons (e.g., `"invoice_not_provided"`, `"transport_or_capture_incomplete"`).
- **Zero Baseline Protection**: R3-2 is fully enforced: baseline token comparisons with $\Sigma v3 = 0$ evaluate to `null` with reason `"zero_baseline"` rather than executing division by zero or reporting false savings.

### D. Authorization Strictly Derived from Frozen Manifest
- **Cryptographic Binding**: `freeze` generates immutable `manifest.json` and `SHA256.json` binding all 68 repository tool and policy files, skill bytes, public commitment SHA, and host environment.
- **Explicit Authorization Contract**: Live execution (`run --phase holdout`) requires an authorization record conforming to `cad-harness.live-authorization.v4`. It validates:
  - `phase: "holdout"`
  - `charged_calls: 163`
  - `clock_confirmation: true`
  - `independent_control_validation: true`
  - Generator model `openai-codex/gpt-6.1-sol` with thinking `xhigh`
  - Target host `DPC-019` and FreeCAD PE version `1.1.4`
  - Matching public commitment hash and valid absolute quota snapshot path.
- **No Ambient Bypass**: CLI flags, environment variables, or ad-hoc overrides cannot inject live authorization.

### E. Model & Context Isolation
- **Request-Plus-Skill Boundary**: Generator subprocesses are invoked as fresh `omp --print --mode json` processes with `--no-tools --no-lsp --no-pty --no-extensions --no-skills --no-rules --no-title --no-session --no-prewalk`.
- **Clean Payload**: System instructions consist strictly of the frozen skill bundle (`SKILL.md`, `modeling.md`, `contracts.md`). User payload contains only `request` and permitted typed `runtime_data`.
- **Zero Leakage**: Checker gold, acceptance cards, future cohort items, and private holdout directories are completely excluded from the generator's environment and input paths. Checker evaluation executes in an isolated temporary root.

### F. Quota Governance (55% / 60%)
- **Snapshot Gate**: `LiveGuard.check()` queries `quota_snapshot()` before every episode and logical call.
- **Thresholds**: A 7-day usage level $\ge 55\%$ triggers consult/halt (`"consult"`), and $\ge 60\%$ triggers a hard stop (`"hard_stop"`). Stale snapshots (>300 seconds old) or missing files halt admission (`"stale_snapshot"`).

### G. Prohibition of Resume and Retake Paths
- **Single-Use Manifest Claim**: `claim()` in `cad_verify_v4_freeze.py` writes an exclusive `manifest.claim.json` upon launch. If already claimed, any subsequent run attempt immediately aborts with `Stop("manifest_already_claimed")`.
- **Immutable Run Directories**: All output run directories are created exclusively (`O_CREAT | O_EXCL`). There are no `resume`, `rerun`, or retake options in the holdout runner.

### H. Addendum B Pilot Bundle Engine (40k Unicode Window & E6/E7 Checks)
- **Unicode Window Accounting**: `tools/cad_verify_v4_pilot.py` extracts a contiguous suffix of complete preceding user/assistant message turns fitting within `WINDOW_CHARS = 40000` Unicode characters (using `len(text)`). Tool calls, tool outputs, and system metadata are stripped.
- **Physical Line Locators**: Evaluates locators as 1-based physical lines in the source JSONL. Unresolvable locators, multi-conversation files, or non-JSONL files (e.g., SQLite) cleanly fail under `E6`.
- **Dependency Closure**: Recursively inspects and copies all declared attachments. Missing files, broken links, or directory escapes trigger `E7`.
- **Procedural Shield**: Any path referencing `v4-holdout-private` is intercepted and rejected prior to filesystem traversal.

---

## 2. Conclusion

The Phase 3 implementation authored by Codex fulfills all architectural requirements, safety bounds, and consensus decisions without deviation.
Gemini verdict: **READY**.
