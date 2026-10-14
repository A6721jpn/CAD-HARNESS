# Pilot Rubric Audit & Sign-off — Gemini

Verdict: **SIGN**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Audited: `design/cad-harness-verify-v4/pilot-rubric.json` (drafted by custodian v4grok).  
Authority Documents:
1. `design/cad-harness-verify-v4/DECISIONS.md` (USER 12:58, 14:07, 14:40, 14:57, 17:28, 19:47, 21:09 JST)
2. `design/cad-harness-verify-v4/pilot-user-requests.md` (request texts and user answers; read-only text, no attachments opened)
3. `design/cad-harness-verify-v4/PLAN-V4-ADDENDUM-C.md` (§§ C-A, C-A2, C-U5, C-R3-1, C-D(a), C-D(b), C-R5v2)
Invariants: Read-only audit; zero pilot attachments (`pilot-user/`) or private holdouts opened. Zero live calls, no commit.

---

## 1. Number-by-Number Traceability Audit

Every numeric value and threshold in `pilot-rubric.json` was cross-checked against the authority sources:

### General & Exit Structure
- **5 Tasks Mandatory Exit**: Verified against `DECISIONS.md:45` (USER 14:40) and `PLAN-V4-ADDENDUM-C.md:17` (C-EXIT).
- **Judge Roles**: Astra Max preliminary scoring (`openai-codex/gpt-6-astra:max`) with user visual override verified against `DECISIONS.md:16-18, 25, 48`. Same-model caveat explicitly noted (`pilot-rubric.json:18`).

### U1 Criteria
- **NF-13CR Inner Dimensions**: $245 \times 365 \times 140\text{ mm}$ verified against `pilot-user-requests.md:72` (catalogue specification, user-confirmed).
- **Play Tolerance**: $\le 0.5\text{ mm}$ per side verified against `DECISIONS.md:58` and `PLAN-V4-ADDENDUM-C.md:88`.
- **Y-Vertical Angular Tolerance**: $3^\circ$ per side verified against `DECISIONS.md:58` and `PLAN-V4-ADDENDUM-C.md:88`.
- **Double-Sided Tape Thickness**: $0.5\text{ mm}$ accommodated in fit verified against `DECISIONS.md:68` and `PLAN-V4-ADDENDUM-C.md:104`.
- **Tape Placement**: Explicitly classified as non-pass/fail per `DECISIONS.md:68` and `PLAN-V4-ADDENDUM-C.md:104`.
- **Engraving Defaults**: $5.0\text{ mm}$ height and $0.6\text{ mm}$ depth verified against `PLAN-V4-ADDENDUM-C.md:99` (C-D(b)) and `c-d-sign-gemini.md`. Correctly labeled as agent-chosen defaults.

### U2 Criteria
- **Glass Thickness**: $1.3\text{ mm}$ verified against `pilot-user-requests.md:73` and `DECISIONS.md:59`.
- **Capacity**: Exactly 10 pieces verified against `pilot-user-requests.md:21`.
- **Perimeter Edge Band**: Zero contact on $1.3\text{ mm}$ band verified against `pilot-user-requests.md:73`.
- **Perimeter Band Gap**: $\ge 0.5\text{ mm}$ verified against `DECISIONS.md:59` and `PLAN-V4-ADDENDUM-C.md:88`.
- **Play & Angle Tolerances**: Play $\le 0.5\text{ mm}$ per side and standing angle $3^\circ$ per side verified against `DECISIONS.md:59` and `PLAN-V4-ADDENDUM-C.md:88`.
- **Convex Face Contact**: Allowed per `pilot-user-requests.md:73` and `DECISIONS.md:59`.
- **Envelope Limit**: "No maximum outer size" verified against `DECISIONS.md:53` and `PLAN-V4-ADDENDUM-C.md:61`.
- **Concave Face Contact**: Kept as Astra + user visual judgment with no numeric gate invented, verified against `DECISIONS.md:65` and `PLAN-V4-ADDENDUM-C.md:95, 104`.

### U3 Criteria
- **Continuity Standard**: G2 continuity (not G3) verified against `DECISIONS.md:51` and `PLAN-V4-ADDENDUM-C.md:59`.
- **Absolute Surface Deviation**: $\le 0.005\text{ mm}$ verified against `pilot-user-requests.md:33`, `DECISIONS.md:51`, and `PLAN-V4-ADDENDUM-C.md:59`.

### U4 Criteria
- **Wall Thickness**: $2\text{ mm}$ verified against `pilot-user-requests.md:45`.
- **Tolerance**: $\pm 0.1\text{ mm}$ on $2\text{ mm}$ thickness and on unchanged surrounding outer dimensions verified against `DECISIONS.md:60` and `PLAN-V4-ADDENDUM-C.md:88`.

### U5 Criteria
- **Deliverable Geometry**: Cut-out logo part (not a plate with aperture; $100 \times 100\text{ mm}$ plate voided) verified against `DECISIONS.md:57` and `PLAN-V4-ADDENDUM-C.md:88, 111`.
- **Thickness & Height Defaults**: $3\text{ mm}$ thickness and $50\text{ mm}$ logo total height (contour Y extent, aspect ratio preserved) verified against `PLAN-V4-ADDENDUM-C.md:74, 76, 88, 111`. Correctly labeled as agent-chosen defaults.
- **Minimum Tool Radius**: $R \ge 0.25\text{ mm}$ on actual output section verified against `pilot-user-requests.md:57` and `PLAN-V4-ADDENDUM-C.md:80, 98, 111`.
- **Fidelity Bounds**:
  - Leg 1 (`image_to_contour`): IoU $\ge 0.90$, Hausdorff $\le 1.5\text{ mm}$ verified against `PLAN-V4-ADDENDUM-C.md:98`.
  - Leg 2 (`contour_to_output`): IoU $\ge 0.92$, Hausdorff $\le 1.0\text{ mm}$ verified against `PLAN-V4-ADDENDUM-C.md:98`.

---

## 2. Conclusion

Zero untraceable or invented numbers were found. All metrics, thresholds, tolerances, and qualitative visual fallback entries in `pilot-rubric.json` faithfully trace to the authorized user decisions and signed consensus addenda.

Gemini verdict: **SIGN**.
