# Addendum C Review & Sign-off on C-EXIT — Gemini

Verdict: **BLOCK**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).
Reviewed: `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (Section `C-EXIT`, USER 14:40 JST Decision) and `design/cad-harness-verify-v4/DECISIONS.md`.
Independent capability expansion plan: `design/cad-harness-verify-v4/addendum-c-r1-gemini.md`.
No live model calls, zero pilot runs, no git commit, and `C:\dev\v4-holdout-private` was not opened.

---

## Exact Findings on C-EXIT and Required Concrete Fixes

The user's decision establishing the completion of S1–S3 capabilities and passing all five user requests U1–U5 as a mandatory v4 exit criterion is accepted in architectural intent. However, four concrete blockers must be resolved before this exit section can be adopted into the consensus plan:

### 1. OpenCASCADE / FreeCAD 1.1.4 Mathematical Kernel Limitation on G3 Continuity (U3)
- **Finding**: C-EXIT states: `U3: <=0.005 mm absolute, G3`. On DPC-019, FreeCAD 1.1.4 operates OpenCASCADE Technology (OCCT 7.7.x). In OCCT, surface filling and blending algorithms (`GeomPlate`, `makeFilledSurface`, `GeomFill`) natively enforce up to **G1 (tangent)** and **G2 (curvature)** continuity constraints. OCCT does **not** provide a native solver for G3 continuity (continuity of the rate of change of curvature). Demanding strict mathematical G3 continuity as a pass/fail prerequisite for mandatory exit makes passing U3 fundamentally unachievable on this software stack.
- **Concrete Fix**:
  - Re-frame the continuity criterion for U3 to the maximum mathematically enforceable by FreeCAD 1.1.4 OCCT: **G2 continuity** (curvature direction and magnitude continuity across seams with G1 normal angular defect $\le 0.1^\circ$).
  - If G3 is strictly retained, define an explicit numerical tolerance for the curvature derivative defect (e.g. finite difference $\Delta \kappa' \le \epsilon$) agreed by the user before trial, rather than requiring an idealized analytic G3 solver that does not exist in OCCT.

### 2. Unbounded Re-Trial Loop & Call Budget Governance
- **Finding**: C-EXIT specifies: *"If any of U1-U5 fails, v4 does not exit. The response is a further development cycle on fresh dev fixtures, followed by a NEW pilot attempt under a new manifest."* DECISIONS.md #5 strictly caps the live call authorization at 203 calls (163 holdout + 40 pilot), with zero automatic borrowing or extensions. Re-running holdouts (50+ tasks) and pilot attempts across repeated failure loops will instantly exhaust the authorized budget and hit the 55% consult / 60% hard stop quota boundaries.
- **Concrete Fix**:
  - Explicitly specify that any subsequent development/pilot cycle requires a **separate, newly authorized user budget record** and independent quota check before launch.
  - An exhausted call budget or quota stop terminates the trial cleanly as `INCOMPLETE` / `budget_exhausted`; the harness must never loop indefinitely or exceed frozen call limits.

### 3. Pre-Freeze Deterministic Vectorization for U5
- **Finding**: C-EXIT states: `U5: parametric thickness and size, min tool R 0.25`. `U5_logo.png` is a 38 KB raster PNG. The generator operates under tool-less isolation (`--no-tools`, stdin `DEVNULL`) and `contracts.md:273` strictly prohibits file I/O in the generated `build(doc)` script. The generator cannot inspect or autotrace a PNG at runtime.
- **Concrete Fix**:
  - Mandate that the S1 `image-to-contour` CLI runs during the pre-freeze bundle preparation phase on DPC-019. It traces the raster, applies the tool radius buffer ($R \ge 0.25\text{ mm}$), and locks the resulting closed vector loops into a cryptographically hashed `contour.json`.
  - The frozen vector contour is supplied to the generator as factual data under `<runtime_data>`. The model then generates the parametric thickness and surrounding plate.

### 4. Pre-Registration of Missing Default Envelopes (U5 and U2)
- **Finding**: While U1 and U2 now have user-confirmed core dimensions, U5 completely lacks nominal outer dimensions for the flat plate (length $\times$ width) and default values for parametric thickness and logo size. Similarly, U2 lacks overall external envelope constraints for printer bed clearance.
- **Concrete Fix**:
  - The user must commit nominal default plate dimensions for U5 (e.g., $100 \times 100\text{ mm}$, thickness $3.0\text{ mm}$) and maximum envelope dimensions for U2 prior to the execution freeze.
  - These values must be locked in `pilot-rubric.json`; agents may not invent them at execution time.

---

## Conclusion

With these four concrete fixes adopted, the phased staging (S1 $\to$ S2 $\to$ S3 $\to$ Holdout $\to$ Pilot) and the mandatory 5/5 exit rule become technically sound and executable on DPC-019.
Current sign-off verdict on C-EXIT: **BLOCK** pending the fixes above.

---

## Re-Sign: Revision C-R1 + C-Q Review

Verdict: **AGREE** (for S1 kickoff)

- **C-R1-2**: Fully resolves BLOCK Point #2 (budget governance). Explicitly enforces that any post-failure development/pilot cycle requires its own separately authorized budget and quota check, terminating as `INCOMPLETE` (`budget_exhausted` / `quota_stop`) without infinite loops or extensions.
- **C-R1-3**: Fully resolves BLOCK Point #3 (U5 vector contour). Explicitly places deterministic raster tracing in the pre-freeze custodian step, emitting a frozen, hashed `contour.json` passed as factual `<runtime_data>`, keeping the generator completely tool-less and file-isolated.
- **C-Q (Questions Q1, Q2, Q3)**: Formally tracks BLOCK Points #1 (U3 OCCT continuity limit) and #4 (U5/U2 default envelope values) as pending user decisions. As established in PLAN-V4-CONSENSUS.md §1, pending user decisions for later live stages (S2/S3/pilot freeze) do not block implementation or offline testing of Stage S1.

C-EXIT with Addendum C-R1 and C-Q is approved for Stage S1 implementation: **AGREE**.

---

## Final Re-Sign: C-EXIT + C-R1 + C-R2 + C-Q

Verdict: **AGREE**

- **C-R2-1**: Preserves the original 163-call holdout completely untouched without borrowing or contamination.
- **C-R2-2**: Locks the rigorous two-leg image fidelity chain (image $\to$ contour and contour $\to$ CAD) into the custodian commitment, keeping raw raster data checker-only.
- **C-R2-3**: Explicitly governs code locks, separate live authoring/freeze cycles, and the strict single-manifest 5/5 exit rule without cross-cycle stitching.
- **C-Q (Q1–Q10)**: Comprehensively catalogs all empirical user tolerances and dimension conventions without stalling S1 offline implementation.

Full three-party consensus on capability expansion Addendum C achieved: **AGREE**.
