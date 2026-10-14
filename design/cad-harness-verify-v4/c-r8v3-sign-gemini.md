# C-R8v3 Sign-off: Topology Preservation & Non-Lossy Small Piece Scaling — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Reviewed: `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (§ C-R8v3, lines 156–159).  
Authority: `C:\dev\CAD-HARNESS-herdr\.tmp-cr8v3.md`, `PLAN-V4-ADDENDUM-C.md` (§§ C-R6, C-R7, C-R8v2).  
Invariants: Read-only audit; zero pilot attachments (`pilot-user/`) or private holdouts (`v4-holdout-private`) opened. Zero live model calls, zero CAD runs, no commit.

---

## Detailed File:Line Audit & Decisions

### 1. Withdrawal of the Lossy Speck Drop Rule (`PLAN-V4-ADDENDUM-C.md:157`): **SIGN**
- **Topology Integrity Restored**: Replaces the C-R8v2 sub-tool speck drop rule. Withdrawing automatic piece deletion fully upholds the core C-R6/C-R7 requirement that every disconnected component, piece count, and nesting hierarchy must be strictly preserved without deletion or bridging.
- **Outward Dilation within C-D(a) Envelope**: Permits small pieces to be enlarged outward via the certified approximation to achieve actual-output $R_{\min} \ge 0.25\text{ mm}$ tool passability, strictly bounded by the unchanged C-D(a) fidelity limits (Hausdorff $\le 1.50\text{ mm}$, IoU $\ge 0.90$).
- **Fail-Closed Refusal**: If a feature cannot achieve $R \ge 0.25\text{ mm}$ within C-D(a) bounds, it is treated as a refusal and an explicit stress FAIL; source pixel area alone is never used as an excuse to drop geometry without user authorization.

### 2. Retention of Paired Topology & Pinch Rules (`PLAN-V4-ADDENDUM-C.md:158-159`): **SIGN**
- **Paired Digital Topology**: Confirms the retention of the C-R8v2 digital topology convention (foreground 4-connected, background 8-connected) with deterministic boundary and nesting forest extraction.
- **Pinch Opening Invariant**: Confirms the local material-removal-only constraint at split diagonal corner contacts, preventing artificial bridge creation between distinct components.

---

## Conclusion
C-R8v3 enforces strict topological non-lossy preservation across all foreground pieces, aligns small-feature machinability with certified C-D(a) approximation bounds, and retains robust paired digital topology.  
Gemini confirms full agreement: **SIGN**.
