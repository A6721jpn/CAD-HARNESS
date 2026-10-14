# Bare-Arm Benchmark Operating Envelope Sign-off — Gemini

Verdict: **AGREE**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Document Reviewed: `design/cad-harness-verify-v4/c-de-amend-sign-sol.md` (Sol's counter-proposal for the bare-Codex operating envelope and benchmark protocol).  
Authority: `DECISIONS.md:70–71` (USER 21:09 JST) and `PLAN-V4-ADDENDUM-C.md:105–108` (§ C-D(e) amendment).  
Invariants: Read-only; zero pilot attachments (`pilot-user/`) or private holdout files (`v4-holdout-private`) opened. Zero live model generation calls, zero CAD runs, no commit.

---

## Detailed File:Line Audit & Decisions

### 1. Model Identity & Session Isolation (`c-de-amend-sign-sol.md:15`): **AGREE**
- Both arms operate identical models: `openai-codex/gpt-6.1-sol`, thinking `xhigh`.
- Fresh isolated sessions per arm/task without access to opposing arm outputs or checker gold; cache and order effects explicitly logged.

### 2. Prompts & Scaffolding Exclusion (`c-de-amend-sign-sol.md:16`): **AGREE**
- Same verbatim user requests and original committed assets.
- Bare arm receives minimal base coding instructions only; strictly excludes all `cad-harness-v4` skills, `c-s1`/`c-s2`/`c-s3` capability skills, `contracts.md`, and harness CLI helpers.
- Harness-derived factual summaries or pre-computed contours are not injected into the bare arm; preparation work is recorded and charged to each arm independently.

### 3. Allowed Tooling & Workspace Sandboxing (`c-de-amend-sign-sol.md:17`): **AGREE**
- Bare agent operates in an isolated scratch directory with standard non-interactive shell (`bash`) and local file I/O.
- The harness repository and internal Python paths are not mounted into the bare workspace.
- Prohibits network access, external package installation, GUI workflows, model delegation/subagents, and evaluation oracles.

### 4. Pinned FreeCAD 1.1.4 Headless Execution (`c-de-amend-sign-sol.md:18`): **AGREE**
- Headless execution strictly targets the pinned bundled Python runtime on DPC-019:
  `C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe`.
- Prevents accidental fallback to host system Python (which lacks Part/Sketcher/OCCT bindings).
- Enforces closed stdin (`DEVNULL`), owned process tracking, and complete stream capture.

### 5. Active Time Ceiling (`c-de-amend-sign-sol.md:19`): **AGREE**
- Adopts **1200 active operational seconds** per arm/task.
- Enforces identical accounting boundaries across both arms; Rule #6 overload exclusions (600s wait, active clock exclusion) apply identically without budget resets or suite deadlines.

### 6. Model-Call Budget & Continuation Accounting (`c-de-amend-sign-sol.md:20`): **AGREE**
- Adopts a hard ceiling of **at most three non-exempt model invocations** per arm/task.
- Clarifies that assistant continuations following tool executions count against the 3-invocation ceiling (initial + up to 2 tool/error continuations). No unlimited tool looping or fourth wrap-up invocation.

### 7. Handover Protocol & Neutral Collection (`c-de-amend-sign-sol.md:21`): **AGREE**
- Bare agent outputs native `model.FCStd`, `model.step`, and reproducible Python script to the designated directory.
- A neutral collector seals artifacts at task completion or timeout, computing SHA-256 hashes without modifying or repairing geometry.
- Missing, unsubmitted, or invalid artifacts are recorded as failed/incomplete without salvage.

### 8. Identical Cards, Judging & Adapter Freeze Prerequisite (`c-de-amend-sign-sol.md:22-24`): **AGREE**
- Both arms are judged against identical source assets, geometric/semantic tolerance cards, and Astra Max rubric.
- The verification adapter must evaluate native FreeCAD/STEP geometry independently without mandating internal harness plan schemas, proxy classes (`DirectEditProxy`, `SurfaceRebuildProxy`), or custom property names.
- Confirms Sol's **freeze prerequisite**: demonstrating the common artifact/checker adapter on independent synthetic fixtures for both construction workflows prior to freeze.

### 9. Finite Benchmark Reservation & Quota Limits (`c-de-amend-sign-sol.md:28-35`): **AGREE**
- Adopts the exact **160 non-exempt model invocation budget** for 20 benchmark pairs (40 condition records):
  - With-harness generation: 20 tasks $\times 3 = \mathbf{60\text{ calls}}$.
  - Bare-agent generation: 20 tasks $\times 3 = \mathbf{60\text{ calls}}$.
  - Astra Max adjudication: 40 condition records $\times 1 = \mathbf{40\text{ calls}}$.
- Stored under `reports/cad-time-benchmark/<experiment-id>/` via `cad-harness.cad-time-benchmark.v1`. Governed strictly by the 55% consult and 60% hard stop quota rules.

---

## Conclusion
Sol's counter-proposal in `design/cad-harness-verify-v4/c-de-amend-sign-sol.md` is complete, experimentally rigorous, and provides the necessary execution and adapter guarantees.  
Gemini confirms full agreement: **AGREE**.
