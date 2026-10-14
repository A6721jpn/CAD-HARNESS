# C-R7 Sign-off: Cycle 2 Closure, Stress-Suite Gate & Cycle 3 Contour Hardening — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Reviewed: `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (§ C-R7, lines 138–144).  
Authority: `DECISIONS.md:61` (USER 17:28 JST), `PLAN-V4-ADDENDUM-C.md` (§§ C-D(a), C-R4, C-R6), and consensus release hygiene.  
Invariants Observed: Read-only audit; zero pilot attachments (`pilot-user/`) or private holdouts (`v4-holdout-private`) opened. Zero live model calls, zero CAD runs, no commit.

---

## Detailed File:Line Audit & Decisions

### 1. Cycle 2 Clean Closure & Audit Preservation (`PLAN-V4-ADDENDUM-C.md:139`): **SIGN**
- **Zero Live Spend**: Confirms that Cycle 2 is closed prior to the live freeze with exactly 0 generation calls and 0 judge calls charged.
- **Audit Integrity**: The single custodian run on U5 failed with `contour_curve_fit_error_budget_unattainable` under `c2-production-recipe-cycle2.json` (`0b6d09b6...7e04`) due to the internal 1-pixel biarc fitting limit. Records (Cycle-2 C2 cohort now retired, pilot v3 records) are immutably preserved in history under `reports/`.

### 2. Pre-Registration of Generic Stress Suite Gate (`PLAN-V4-ADDENDUM-C.md:140`): **SIGN**
- **Hygiene & Blindness**: Mandates that before any custodian run on U5, agents pre-register and hash-lock a generic stress suite of synthetic raster test cases (thin strokes, sharp corners, dense curve mixes, anti-aliased RGBA edges, multi-piece compounds, and nested holes). Zero geometry or pixels are taken from `pilot-user/U5_logo.png`.
- **Pre-Execution Gate**: The Cycle 3 recipe must pass 100% of the stress suite (both fidelity legs, actual-output $R_{\min} \ge 0.25\text{ mm}$ and tool access, solid validity, and neutral checker both arms) before the custodian runs U5.

### 3. Fitting Budget Alignment with User Decision 17:28 (`PLAN-V4-ADDENDUM-C.md:141-142`): **SIGN**
- **Authority Reconciled**: Under USER 17:28 Decision (`DECISIONS.md:61`), the logo requires rough matching, and model correctness takes precedence. The internal 1-pixel biarc fitting threshold was an agent-chosen algorithm parameter, not a user constraint.
- **Fidelity-Bounded Fallback**: Cycle 3 allows an error bound tied to the agreed lenient C-D(a) fidelity limits (Hausdorff $\le 1.50\text{ mm}$, IoU $\ge 0.90$) rather than an arbitrary 1-pixel constraint.
- **Preservation of Invariants**: Confirms that $50\text{ mm}$ final height, single registration across both legs, topology preservation, valid solids, and actual-output $R \ge 0.25\text{ mm}$ / tool-access checks remain strictly enforced. Concave corners cannot be left as raw zero-radius pixel notches or silently rounded post-scoring.

### 4. Controlled Staging Pipeline (`PLAN-V4-ADDENDUM-C.md:143-144`): **SIGN**
- Confirms the disciplined staging order: Sol implements on generic synthetic fixtures only $\to$ Gemini reviews $\to$ new recipe and lock $\to$ v4grok authors fresh blind C2 cohort under Option B $\to$ one custodian U5 run $\to$ C-R4 combined commit, final lock, quota verification, live runs, and pilot trial.

---

## Conclusion
C-R7 correctly diagnoses the curve-fitting failure, establishes an independent stress-suite validation gate, aligns fitting budgets with USER 17:28 and C-D(a) without weakening actual-output tool checks, and maintains strict Option B custody.  
Gemini confirms full agreement: **SIGN**.
