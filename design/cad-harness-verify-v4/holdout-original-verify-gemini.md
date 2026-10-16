# Verification of Original 60-Item Holdout Public Commitment — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Verification Target: Public records authored by v4grok (at HEAD `6788faf`):
- `design/cad-harness-verify-v4/holdout-original-commitment.json`
- `design/cad-harness-verify-v4/holdout-original-commitment.md`  
Authority: `.tmp-gemini-orig60.md` and `design/cad-harness-verify-v4/impl-notes-p3.md` (§ Public sealed-input contract).  
Invariants Observed: Strict read-only check of PUBLIC records only. Zero access to `C:\dev\v4-holdout-private` or `pilot-user/` attachments; zero inspection of in-progress launcher changes. Zero live model generation calls, zero live CAD runs, no commit.

---

## 1. Audit Checklist & Verification Evidence

### A. Schema & Freeze Contract Compliance
- In `design/cad-harness-verify-v4/holdout-original-commitment.json:2-5`:
  - `schema`: `"cad-harness.holdout-commitment.v4"`
  - `profile`: `"original"`
  - `cohort_sha256`: `"45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65"`
  - `cohort_bytes`: 37412
- In `tools/cad_verify_v4_freeze.py:259-270`:
  - `freeze()` reads `commitment_path`, derives `sha256` via `_file_sha()`, and records `manifest["commitment"]`.
  - Independent hashing confirms `holdout-original-commitment.json` has SHA-256 `d87165cebd273de13fc1e7796cb2bc58fffb4e88a6d1f71665194d8866493a7f` (1069 bytes), matching `holdout-original-commitment.md:101`.
- In `tools/cad_verify_v4_live.py:503-505` (`load_cohort`):
  - Validates `commitment.get("schema") == "cad-harness.holdout-commitment.v4"` and `commitment.get("cohort_sha256") == ledger.file_sha(path)`.
  - All fields expected by freeze and live cohort loading are present, properly typed, and consistent.

### B. 60 Entries, Allocation, and Frozen Order
- In `holdout-original-commitment.json:6-9` and `holdout-original-commitment.md:13-22`:
  - Total entries: exactly 60 entries.
  - Scored: exactly 51 entries.
  - Unscored previews (dev): exactly 3 entries (D1, D2, D3).
  - Unscored completion: exactly 6 entries (C4 rounds 1–3, C5 rounds 1–3).
- Group breakdown strictly preserves the v3 structure:
  - `dev`: 3 entries (0 scored)
  - `legacy`: 4 entries (4 scored: A-good, A-broken, B-good, B-broken)
  - `mvp`: 10 entries (10 scored: P1, P2, P4, P5, P3 × 2 rounds)
  - `geometry`: 18 entries (18 scored: G1–G5 × 2 rounds, G6 × 3 rounds, S3 × 5 rounds)
  - `q`: 13 entries (13 scored: A4 × 3 rounds, A5 × 5 rounds, A6 × 5 rounds)
  - `completion`: 6 entries (0 scored: C4 × 3 rounds, C5 × 3 rounds)
  - `fault`: 6 entries (6 scored: F4–F6 × 2 rounds)
  - Sum: 60 entries total, 51 scored.
- Allocation and order:
  - Validated against `cad-harness.verify-order.v3` / `eval_verify_v3.validate_order` (`holdout-original-commitment.md:63`).
  - Order integrity verified by successful execution of `load_cohort` at HEAD `6788faf` (`line 92`).

### C. Call Budgets & 163-Call Ceiling
- In `holdout-original-commitment.json:10-11`:
  - `planned_calls`: 83
  - `max_calls`: 163
- Matches `impl-notes-p3.md:32,41` and the signed Phase 3 plan:
  - Retains the unchanged 163-call hard ceiling.
  - Zero calls borrowed from the family holdout reservation (172 calls) or benchmark envelope (160 calls).

### D. Original Scope Isolation (No C1–C5 Items)
- In `holdout-original-commitment.json:3`: `profile: "original"`.
- In `holdout-original-commitment.md:11`:
  - Confirmed: *"Scope is the unchanged v3 allocation. No C1-C5 capability items were added."*
  - The 90 declared files in the cohort file map (`lines 106–196`) reside exclusively in original task directories (`completion/`, `dev/`, `fault/`, `geometry/`, `legacy/`, `mvp/`, `q/`).
  - Zero C1–C5 capability items or benchmark items are present.

### E. Admission Controls as `independent_control_validation` Evidence
- In `holdout-original-commitment.json:17-35`:
  - `independent_control_validation`: `true`
  - All 16 offline admission checks report complete passing results:
    - `load_gold`: 24/24
    - `description_binding`: 24/24
    - `completion_binding`: 2/2
    - `rubric_positive`: 5/5
    - `rubric_negative`: 5/5
    - `rubric_invention_trap`: 5/5
    - `source_contract`: 6/6
    - `fault_inject`: 3/3
    - `spec_schema`: 2/2
    - `hash_collisions_v3_mvp`: 0
    - `hash_collisions_families_v1`: 0
    - `native_fixture_pass`: 24/24
    - `offline_good_pass`: 2/2
    - `offline_broken_fail`: 2/2
    - `fault_candidate_fail_includes_expected_predicate`: 3/3
    - `loader`: pass
- In `tools/cad_verify_v4_freeze.py:243`:
  - `_authorization()` requires `value.get("independent_control_validation") is True`.
  - The documented evidence in the commitment satisfies this prerequisite without substituting old tasks.

### F. Zero Coordinate, Prompt, Rubric, or Answer Leaks
- In `holdout-original-commitment.json`:
  - Contains strictly high-level counts, metadata strings, boolean status flags, and admission fraction counts.
  - Zero prompt texts, rubric contents, answers, or coordinate data exist.
- In `holdout-original-commitment.md`:
  - Contains summary tables, schema versions, admission results, and file SHA-256 / byte mappings (`lines 104–196`).
  - No prompt requests, evaluation rubrics, answers, or geometric vertex coordinates `[x, y]` are leaked.

### G. Operational Guard Invariants
- In `holdout-original-commitment.json:12-16`:
  - `live_calls`: 0
  - `model_generation_calls`: 0
  - `head`: `"6788faf53601443b23b21ad40f53d5a0bde001c8"`
  - `authorization`: `null`
  - `final_v4_ready`: `false`
- In `holdout-original-commitment.md:5`:
  - Explicit confirmation: *"This file is not a live authorization. authorization stays null. final_v4_ready stays false."*
  - Live authorization is not created or claimed.

---

## 2. Conclusion

The public original holdout commitment (`holdout-original-commitment.json` and `.md`) authored by v4grok complies in full with the public sealed-input contract, preserves the original 60-item scope and 163-call ceiling, provides complete admission-control validation evidence, and leaks no private content.

Gemini verdict: **SIGN**
