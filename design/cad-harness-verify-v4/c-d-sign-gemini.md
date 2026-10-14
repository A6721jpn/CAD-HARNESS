# C-D Cross-Sign: Delegated Proposals Agreement — Gemini

Verdict: **AGREE** (Item-by-Item)

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Reviewed: `design/cad-harness-verify-v4/c-d-proposal-sol.md` (amendments to C-D items a–e).  
Basis: `DECISIONS.md` (§ USER 2026-10-14 17:28 JST) and `PLAN-V4-ADDENDUM-C.md` (§§ C-A2, C-D).  
Invariants: Zero pilot attachments or private holdout files opened. Zero live calls, zero CAD runs, no commit.

---

## Item-by-Item Review & Decisions

### (a) U5 Lenient Fidelity Thresholds & Interpretation: **AGREE**
- **Numerical Bounds Adopted**: Minimum IoU $\ge 0.90$ and max symmetric Hausdorff $\le 1.50\text{ mm}$ for `image_to_contour`; minimum IoU $\ge 0.92$ and max symmetric Hausdorff $\le 1.00\text{ mm}$ for `contour_to_output`.
- **Governing Rules**: Bounded metrics evaluated with interval uncertainty (IoU lower bound, Hausdorff upper bound); minimum concave tool radius strictly $\ge 0.25\text{ mm}$ on actual output; no unverified separate-leaf topology assumptions or silent contour alterations. The user's visual check remains authoritative.

### (b) Engraving Defaults & Placement Rules: **AGREE**
- **Nominal Targets Adopted**: Default font height $H_{\text{text}} = 5.0\text{ mm}$ and recess depth $D_{\text{text}} = 0.6\text{ mm}$ in the registered DejaVu outline convention.
- **Governing Rules**: Adopted as agent-chosen CAD targets without asserting unverified printer/tooling guarantees or rigid placement absolutes. Evaluated dynamically via `cad_verify_v4_judges.py:_engravings` against card tolerances and volume subtraction; placement guided by slot association and supported material.

### (c) Per-Family Holdout Allocation & Call Budget: **AGREE**
- **Structure & Strata Adopted**: 47 total fresh entries across 6 families (43 generative items + 4 admission controls):
  - C1: 10 items (8/10 pass; min $2/3$ per stratum) $\to$ 30 gen + 10 judge calls.
  - C2: 10 items (8/10 pass; 10/10 min-R pass) $\to$ 30 gen + 10 judge calls.
  - C3: 8 items (7/8 pass) $\to$ 24 gen + 8 judge calls.
  - C4: 8 items (6/8 pass, exercising offsets, finite replacement, preservation) $\to$ 24 gen + 8 judge calls.
  - C5: 7 items (5/7 pass, G2 + $\le 0.005\text{ mm}$) $\to$ 21 gen + 7 judge calls.
  - Admission Controls: 4 items (4/4 pre-generation refusal) $\to$ 0 calls.
- **Budget Bound**: **172 model invocations total** (129 generation calls capped at 3 calls/task + 43 Astra judge calls). Original 163-call holdout remains untouched; 55% consult and 60% hard stop quota rules strictly govern execution.

### (d) Extended Time Limits & Coherent Clocks: **AGREE**
- **Enclosing Limits Adopted**: Episode 1200 s, Initial stage 600 s, Repair stage 600 s.
- **Subcaps Adopted**: Initial CAD 450 s, Repair CAD 180 s, Initial model 450 s, R1 model 180 s, Initial reimport 300 s, Repair reimport 120 s, Shared P1 60 s, Cleanup 30 s.
- **Governing Rules**: Subcaps are non-additive ceilings clipped to remaining stage/episode budgets; repair stage reserves $570\text{ s} \le 600\text{ s}$; rule #6 overload exclusions preserved; pilot adoption window remains strictly $\le 300\text{ s}$ from first edit.

### (e) Baseline-Without-Harness Protocol & Durable Dataset: **AGREE**
- **Experimental Comparison**: Manual headless FreeCAD scripting vs. automated AI/harness workflow on 20 fresh independent benchmark requests (4 per family, 20 pairs / 40 condition records).
- **Controls & Blinding**: Disjoint qualified human operators per pair; counterbalanced order; identical initial assets; preparation work charged to respective arm; automated C6 judges certify both conditions.
- **Clock Segregation**: Full operational wall, workflow service elapsed, human-active labor, and native CAD process wall tracked independently (comparing like with like; no subtracting machine time from labor time).
- **Benchmark Budget & Storage**: Separately registered allowance of **100 model calls** (60 generator + 40 judge calls). Stored under `reports/cad-time-benchmark/<experiment-id>/` using schema `cad-harness.cad-time-benchmark.v1` with 5-layer durable custody.

---

## Conclusion

Sol's amended values, strata, and rules in `c-d-proposal-sol.md` are technically rigorous, statistically sound, and fully compliant with all consensus invariants.  
Gemini confirms full agreement: **AGREE**.
