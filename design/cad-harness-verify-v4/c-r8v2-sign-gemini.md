# C-R8v2 Sign-off: Standard Digital Topology, Pinch Constraints & Sub-Tool Specks — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Reviewed: `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (§ C-R8v2, lines 150–156).  
Authority: `C:\dev\CAD-HARNESS-herdr\.tmp-cr8v2.md`, `PLAN-V4-ADDENDUM-C.md` (§§ C-D(a), C-R6, C-R7).  
Invariants: Read-only audit; zero pilot attachments (`pilot-user/`) or private holdouts (`v4-holdout-private`) opened. Zero live model calls, zero CAD runs, no commit.

---

## Detailed File:Line Audit & Decisions

### 1. Paired Digital Topology Convention (`PLAN-V4-ADDENDUM-C.md:151`): **SIGN**
- **Mathematical Soundness**: Binds the standard paired digital topology convention: foreground 4-connected with background 8-connected.
- **Topological Invariants**: Deterministically derives the component/hole/nesting forest from this adjacency, bound in the recipe and independently checked in both fidelity legs. Preserves manifold, closed, and separated boundaries in native and STEP outputs.

### 2. Pinch Opening & Global Approximation Scope (`PLAN-V4-ADDENDUM-C.md:152`): **SIGN**
- **Material-Removal Constraint**: Restricts local split corner opening to material removal only, preventing artificial dilation across pinch points.
- **Global Approximation Bound**: Re-affirms that global curve approximation may adjust boundaries inward or outward strictly within the unchanged C-D(a) fidelity limits (Hausdorff $\le 1.50\text{ mm}$, IoU $\ge 0.90$).
- **Anti-Bridging Integrity**: Strictly prohibits artificial bridging, component merging, mask tampering, or post-scoring repairs.

### 3. Explicit Sub-Tool Speck Rule (`PLAN-V4-ADDENDUM-C.md:153`): **SIGN**
- **Physical Machinability Grounding**: A disconnected piece with area smaller than a $\varnothing 0.50\text{ mm}$ disc (area $< \frac{\pi}{4}(0.5)^2 \approx 0.196\text{ mm}^2$) is geometrically impossible to machine with a tool of radius $R_{\min} = 0.25\text{ mm}$ while satisfying $R \ge 0.25\text{ mm}$.
- **Declared, Transparent Dropping**: Explicitly drops sub-tool specks under a declared recipe rule, with every dropped speck fully accounted (count, area, location) in the transformation report.
- **Unwaived Fidelity Accounting**: Both fidelity legs score against the full original mask including dropped specks, ensuring dropped area penalizes IoU and Hausdorff distance.
- **Fail-Closed Gate**: Any other component failing $R \ge 0.25\text{ mm}$ within C-D(a) bounds is refused as a stress failure.

### 4. Stress Suite Gate Retention (`PLAN-V4-ADDENDUM-C.md:154-155`): **SIGN**
- Retains all 14 generic stress cases with expected geometric pass outcomes, honoring Gemini's author confirmation that Cases 02 and 10 represent intended feasible designs.
- Preserves audit history and records user notification regarding sub-tool speck removal.

---

## Conclusion
C-R8v2 establishes a mathematically well-posed topology contract, cleanly bounds pinch opening, provides an objective, transparent rule for unmachinable sub-cutter specks without silent masking, and maintains strict actual-output tool checks across all 14 stress cases.  
Gemini confirms full agreement: **SIGN**.
