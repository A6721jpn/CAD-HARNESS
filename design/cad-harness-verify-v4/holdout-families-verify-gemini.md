# Verification of Family Holdout Public Commitment — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Reviewed: `design/cad-harness-verify-v4/holdout-families-commitment.md` (authored by v4grok under Option B).  
References: `PLAN-V4-ADDENDUM-C.md` (§§ C-D(c), C-R3, C-R4), `c-d-proposal-sol.md`, and `DECISIONS.md` (§§ USER 14:07, 17:28, 21:09 JST).  
Invariants Observed: Option B strict custody observed; zero private card contents or test prompt texts were inspected or printed. Zero live calls, zero CAD runs, no commit.

---

## 1. Audit Checklist & Verification Evidence

### A. Counts, Strata, and Call Budgets Match Signed Addendum
- **Generative Family Holdout Cohort**:
  - Exactly 43 generative items across C1–C5 + 4 admission controls = **47 items total** (`holdout-families-commitment.md:7-17`).
  - Strata allocations match signed `c-d-proposal-sol.md:52-60` and `PLAN-V4-ADDENDUM-C.md:100` exactly:
    - C1: 10 items (Prismatic 4, Stepped/Oriented 3, Curved/Irregular 3), Gen cap 30, Astra cap 10.
    - C2: 10 items (Convex 3, Connected with holes 4, Notch/tool access 3), Gen cap 30, Astra cap 10.
    - C3: 8 items (Numeric 3, Alphanumeric 3, Dense 2), Gen cap 24, Astra cap 8.
    - C4: 8 items (Planar/Oblique 2, Curved 2, Finite replacement 2, Preservation 2), Gen cap 24, Astra cap 8.
    - C5: 7 items (Two-patch 3, Trimmed multi-patch 4), Gen cap 21, Astra cap 7.
    - Admission controls: 4 items (4/4 pre-generation refusal), Gen cap 0, Astra cap 0.
  - **Family Holdout Budget**: Strictly bound to 129 generation calls + 43 Astra judge calls = **172 non-exempt model calls** (`line 31`).
- **Benchmark Corpus**:
  - Exactly 20 pairs (4 per family C1..C5: B01–B20) = **40 condition records** (`lines 19-25`).
  - **Benchmark Budget**: Strictly bound to $\le 60$ with-harness generation calls, $\le 60$ bare-arm generation calls, and $\le 40$ Astra judge calls = **$\le 160$ model calls** (`line 33`), matching the agreed envelope (`PLAN-V4-ADDENDUM-C.md:112`).
- **Reservation Segregation**: All budgets are kept independent from the original 163-call holdout and pilot reservations, strictly governed by the 55% consult / 60% hard stop quota rules.

### B. Schema Versions & System Assets
- All schema `$id` values listed in `holdout-families-commitment.md:57-75` exist in `design/cad-harness-verify-v4/schemas/` and match the profile invariants.
- Private `DejaVuSansMono.ttf` and `LICENSE_DEJAVU` SHA-256 hashes (`lines 79-80`) match the committed font in `skills/cad-harness-v4/fonts/` (`602ec86b...` and `d75938de...`).

### C. Admission Control Claims Consistency
- The 4 admission controls (`AC-corrupt-step`, `AC-open-contour`, `AC-tool-infeasible`, `AC-unavailable-glyph`) establish 4/4 pre-generation refusals without invoking generation or judge calls (`lines 43-51`), matching `c-d-proposal-sol.md:59`.

### D. Generator and Judge Model Mappings
- Confirmed:
  - Holdout generator: `openai-codex/gpt-6.1-sol`, thinking `xhigh` (`line 35`).
  - Benchmark generator (both with-harness and bare arms): `openai-codex/gpt-6.1-sol`, thinking `xhigh` (`line 33`).
  - Judge across all phases: `openai-codex/gpt-6-astra`, thinking `max` (`line 35`).
  - Pilot generator is reserved for Astra Max only (per USER 14:07).

### E. Cryptographic Archive Verification & Zero Repo Leakage
- Recomputed SHA-256 of the sealed private archive `C:\dev\v4-holdout-private\families-v1\families-v1.sealed.zip` via independent read-only hashing:
  - Computed SHA-256: `588db92fa91cc276ff5d3dc13a7fdf16fa49395d6e420e6a81e0d56396c21dcf`
  - Computed size: `3206379` bytes.
  - Exactly matches `holdout-families-commitment.md:87`.
- Verified that zero private files or sealed bytes leaked into the working repository (`C:\dev\CAD-HARNESS-herdr`).

---

## 2. Conclusion

The family holdout public commitment authored by v4grok is fully reconciled with all consensus agreements, schemas, and quota budgets under Option B.

Gemini verdict: **SIGN**.
