# C-R8 Sign-off: 4-Connected Topology & Stress Cases 02/10 Feasibility — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Reviewed: `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (§ C-R8, lines 145–150).  
Authority: `C:\dev\CAD-HARNESS-herdr\.tmp-cr8.md`, `PLAN-V4-ADDENDUM-C.md` (§§ C-D(a), C-R6, C-R7).  
Invariants: Read-only audit; zero pilot attachments (`pilot-user/`) or private holdout files (`v4-holdout-private`) opened. Zero live model calls, zero CAD runs, no commit.

---

## 1. Author Confirmation: Intent of Stress Cases 02 and 10

As author of the C-R7 generic stress suite (`dev-c2-stress/generate.py`):
- **Case 02 (`case02_sharp_corners.png`)**: **INTENDED FEASIBLE**. Designed as an 8-pointed star badge with acute notches and central cutout. The corner-only pixel touches were an incidental byproduct of discrete rasterization at acute $25^\circ$ angles, not a deliberate non-manifold refusal case.
- **Case 10 (`case10_mixed_crescent_stars.png`)**: **INTENDED FEASIBLE**. Designed as an astronomical crescent moon with tapering tips and three detached stars. The diagonal contacts at the crescent cusps resulted from the asymptotic tapering of the outer and inner circular arcs to zero thickness, not a deliberate defect injection.
- Both cases are intended to represent valid physical logo geometry and should pass the pipeline under the 4-connected topology rule.

---

## 2. Detailed File:Line Audit & Decisions

### A. Factual Diagnosis of Non-Manifold Pixel Touches (`PLAN-V4-ADDENDUM-C.md:146`): **SIGN**
- Confirms the observation in `impl-notes-c2-cycle3.md`: exact-cell polygonization flags pixels sharing only a diagonal vertex as `contour_nonmanifold_pixel_contact`.
- Resolves the missing specification in the stress manifest regarding topological connectivity conventions for corner contacts.

### B. Deterministic 4-Connected Topology Convention (`PLAN-V4-ADDENDUM-C.md:147`): **SIGN**
- Establishes a uniform, recipe-declared 4-connected foreground convention.
- Splitting diagonal corner touches into distinct boundary vertices separates ambiguous pinch points into distinct loops/components without fabricating artificial 8-connected bridges, fully complying with C-R6 and C-R7 anti-bridging rules.

### C. Pinch-Opening Within C-D(a) Fidelity Bounds (`PLAN-V4-ADDENDUM-C.md:148`): **SIGN**
- Authorizes the certified curve fit to open the split pinch point via material removal only, enabling physical cutter passability ($R \ge 0.25\text{ mm}$ on actual output) while remaining strictly bounded by the agreed C-D(a) fidelity limits (Hausdorff $\le 1.50\text{ mm}$, IoU $\ge 0.90$).
- Enforces fail-closed behavior: if tool clearance cannot be achieved within the C-D(a) fidelity envelope, the case is refused with a specific error code and fails the stress gate; it is never silently widened or waived.

### D. Retention of 14/14 Stress Gate (`PLAN-V4-ADDENDUM-C.md:149-150`): **SIGN**
- The stress suite gate remains strict: all 14 cases must pass both fidelity legs, solid validity, and actual-output $R_{\min} \ge 0.25\text{ mm}$ tool access checks prior to custodian execution on U5.

---

## Conclusion
C-R8 mathematically resolves diagonal pixel rasterization artifacts via an uncompromised 4-connected topology rule, correctly recognizes Cases 02 and 10 as intended feasible designs, and preserves strict actual-output tool clearance without post-hoc tolerance widening.  
Gemini confirms full agreement: **SIGN**.
