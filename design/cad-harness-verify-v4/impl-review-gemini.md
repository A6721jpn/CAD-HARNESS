# Gemini Implementation Review: VERIFY v4 Phases 1–2

Verdict: **READY**

---

## 1. Review Summary & Findings

The Phase 1–2 implementation authored by Codex strictly complies with [`design/cad-harness-verify-v4/PLAN-V4-CONSENSUS.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v4/PLAN-V4-CONSENSUS.md), [`design/cad-harness-verify-v4/impl-notes-p12.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v4/impl-notes-p12.md), and the user's review criteria.

All 19 unit tests in `tools.test_verify_v4` pass deterministically in 1.2s without launching any external process. Historical v3 reconciliation accurately confirms 88 retained-segment calls and 109 total charged calls.

---

## 2. Core Audit Checklist

### A. Matches the Plan
- **Strict Ordering**: Implements Phase 1 (Cost Ledger) and Phase 2 (Skill/CLI consolidation) purely offline. Holdout and pilot remain unstarted (`not_run`).
- **CLI Facade**: [`tools/eval_verify_v4.py`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v4.py) provides unified offline commands (`preflight`, `ledger`, `request`, `run`, `aggregate`). Batch execution calls the exact same single-request path as interactive requests.
- **Skill Bundling**: [`skills/cad-harness-v4/`](file:///C:/dev/CAD-HARNESS/skills/cad-harness-v4/) cleanly encapsulates generic policy, unchanged modeling prose (`modeling.md`), and verbatim existing output contracts (`contracts.md`). Prompt bytes strictly consist of the user request plus skill bundle, with typed `<runtime_data>` for runtime factual state.
- **Historical Reconciliation**: Backfill accurately reconciles **88 retained-segment calls + 21 archived calls = 109 total charged calls** via verified SHA binding chains. Historical aggregate replay achieves `identical_summary: true` with all 8 threshold predicates matching.

### B. Null is Never Treated as 0
- **Nullable Aggregations**: [`tools/cad_verify_v4_ledger.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v4_ledger.py) enforces that `nullable_total()` returns `total = None` if any contribution is unknown, reporting `known_subtotal`, `expected`, `known`, `missing`, and `missing_reason` independently.
- **Token Usage**: Three historical calls with uncaptured token usage result in complete token totals remaining `null` with explicit `missing_reason: "missing_contributions"`, never truncated to zero.
- **Pricing**: In the absence of a user-supplied rate card, all pricing amounts remain `null` with `missing_reason: "no_user_rate_source"`. Disallows illustrative rates.
- **Operational Boundaries**: Run wall-clock duration is reported as `null` with explicit reason when process endpoints are unrecorded.

### C. Full Stdout/Stderr Stream Capture
- **Disk Archiving**: `StreamCapture` streams raw binary chunks directly to disk (`attempt-XXXX/stdout.bin` and `stderr.bin`) with incremental SHA-256 and byte accounting.
- **Bounded Memory**: Parser memory is strictly bounded by a 16 KiB sliding window (`TAIL_BYTES = 16384`), preventing in-memory bloat during long streams.
- **Completeness Classification**: Historical partial logs are transparently flagged as `missing_reason: "historical_tail_only"`, distinguishing verified complete streams from truncated legacy files.

### D. No Live Call Path
- **Enforced Isolation**: `tools/cad_verify_v4_agent.py` contains no subprocess or network launcher. Requests without an explicit `--replay` recording or injected mock runtime abort immediately (`Stop("p12_offline_only_replay_required")`).
- **Test Sandboxing**: `tools/test_verify_v4.py` patches `subprocess.run` and `subprocess.Popen` to raise `AssertionError("live process denied")`, guaranteeing no live calls can escape.
- **Zero Live Authorization**: `policy.json` explicitly sets `"live_authorized_calls": 0`. The CLI `freeze` command is disabled (`Stop("freeze_not_available_in_p12")`), and `--sealed-input` / `--tasks` are rejected.

### E. v3 Frozen Files Untouched
- **Clean Diff**: `git diff` against tracked repository files is completely empty.
- **Zero Mutation**: No v3 evaluator, driver, test, report, or frozen markdown file was modified. The v3 driver is loaded into an isolated private module namespace via `importlib` without monkey-patching the underlying imported module.

### F. No Overload-Robustness Claim
- **Explicit Invariant**: Overload recovery is consistently designated as **`UNVERIFIED`** across `preflight`, `request`, `run`, `policy.json`, and summary manifests.
- **Protocol Fidelity**: The 600-second backoff and byte-identical resend policy is implemented and tested with simulated clocks, but no premature claims of live recovery are made.

---

## 3. Conclusion

The Phase 1–2 codebase adheres to all consensus specifications and safety constraints. Gemini verdict: **READY**.
