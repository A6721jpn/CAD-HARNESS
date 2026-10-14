# C-D(e) Benchmark Amendment Sign-off & Bare-Arm Protocol — Gemini

Verdict: **AGREE**

Agent: Gemini (`google-antigravity/gemini-3.8-flash`).  
Authority: User Decisions 2026-10-14 21:09 JST (`DECISIONS.md`) and `PLAN-V4-ADDENDUM-C.md` (§ C-D(e) amendment).  
Invariants: Zero pilot attachments or private holdout files opened. Zero live calls, zero CAD runs, no commit.

---

## 1. Decision on User 21:09 Amendment
Gemini confirms full **AGREE** on replacing human operators with the same-model bare agent (Codex without harness).  
*Rationale*: Eliminates human subject recruitment variance, operator fatigue, and skill confounding; isolates the exact causal efficiency contribution of the harness scaffolding versus unassisted model generation. The benchmark result will explicitly disclose that it measures harness-vs-bare-agent performance rather than human drafting hours saved.

---

## 2. Concrete Proposal: Bare-Arm Operating Envelope

| Parameter | Specification for Bare Codex Arm | Control & Justification |
| --- | --- | --- |
| **Model Identity** | `openai-codex/gpt-6.1-sol`, thinking `xhigh` | Identical to with-harness generator; zero model capability discrepancy. |
| **System Prompt & Skills** | Minimal base coding agent prompt only; **NO** `cad-harness-v4` skills, **NO** `c-s1`/`c-s2` skills, **NO** `contracts.md`. | Tests bare agent capability from natural-language engineering requests. |
| **Allowed Tools** | Standard scratchpad shell (`bash`) and file I/O within an isolated scratch directory. | Allows agent to write Python scripts and run them locally. No harness CLI tools or evaluation oracles. |
| **FreeCAD Access** | Headless CLI execution via `freecadcmd.exe` or `python.exe` on DPC-019. | Agent executes its own standalone Python script to generate CAD models. |
| **Active Time Ceiling** | **1200 seconds** per task arm. | Identical to with-harness episode ceiling; Rule #6 overload exclusion applies. |
| **Model Calls per Task** | **At most 3 model calls** per task. | Matches with-harness arm budget (initial + up to 2 repair/execution turns). |
| **Handover Contract** | Writes final `model.FCStd` and `model.step` to a designated output folder. | Sealed by neutral collector at task completion or 1200 s timeout. |
| **Judging & Rubric** | Evaluated by the **exact same frozen C6 judges and Astra Max card**. | Identical geometric tolerance gates and user visual check; no relaxed bar. |

---

## 3. Revised Call Budget Allocation (20 Benchmark Pairs)

With the bare-arm model calls explicitly budgeted, the benchmark allocation for 20 pairs (40 condition records) is:

| Workflow Arm | Tasks / Condition Records | Call Multiplier | Subtotal Model Calls |
| --- | ---: | ---: | ---: |
| **With-Harness Arm** | 20 tasks | 3 calls/task max | 60 generator calls |
| **Bare-Arm (Without Harness)** | 20 tasks | 3 calls/task max | 60 generator calls |
| **Astra Max Judge Adjudication** | 40 condition records (20 pairs) | 1 call/record | 40 judge calls |
| **Total Benchmark Reservation** | **20 Pairs (40 Records)** | — | **160 model invocations** |

*Accounting Note*: Replaces the earlier 100-call estimate. 160 calls is finite, fully accounted under C-R1-2, and governed by the standing 55% consult / 60% hard stop quota rules.
