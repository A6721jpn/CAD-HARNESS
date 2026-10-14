# C-D(e) amendment and bare-arm envelope — sol

## USER 21:09 amendment: AGREE

`DECISIONS.md:70–71` and `PLAN-V4-ADDENDUM-C.md:105–108` supersede the manual-human construction arm: same Codex model and requests, without `cad_run`, CAD-harness skills/contracts or harness CLI. Bare-arm model calls require their own reservation. Construction-operator and human-engineering-time fields become not-applicable, not zero; any required human judge/adoption identity remains applicable. RESULTS must describe **harness-versus-bare-agent performance**, not human hours saved.

AGREE with `batch2-v4grok.md:74–82`: signing the amendment does not settle its operating envelope. The earlier human-operator prerequisite and 100-call total are superseded/incomplete for this comparison. Gemini's 1200 s, three calls/task and 160 calls are proposals, not USER values or already adopted three-party decisions.

## Bare-arm envelope: COUNTER-PROPOSAL to Gemini's wording

I support **1200 active seconds, at most three counted model invocations per arm/task, and 160 benchmark calls as proposed ceilings**, subject to all three agreeing the complete protocol below before freeze. This signature does not authorize execution or amend the addendum itself.

| Item | Proposed frozen rule |
| --- | --- |
| Model / sessions | Both arms use `openai-codex/gpt-6.1-sol`, thinking `xhigh`, with the same pinned provider/model/options. Fresh isolated sessions per arm/task; no other arm's history, outputs or checker gold. Record model/provider identity and cache/order effects rather than claiming exact causal isolation. |
| Prompts / inputs | Same verbatim request and original committed assets. Common non-CAD safety/base instructions; no CAD-specific skills in the bare arm, including predecessor modeling skills or repository CAD instructions. No harness contracts, implementation, archived helpers, prepared solutions or hidden cards. Harness-derived facts/contours are not silently given to the bare arm: it must derive what it needs from the same original information. Record and charge each arm's preparation. |
| Tools | Noninteractive shell and file I/O in an isolated scratch workspace; read-only access to its committed source assets and the frozen offline FreeCAD/library/documentation inventory. No network fetching, package installation, GUI, model subprocesses/delegation, harness modules/proxies, `cad_run`, harness CLI or evaluation oracles. Ordinary offline API introspection and self-authored CAD scripts/self-checks are allowed. Do not mount the harness repository or its Python path into this workspace. |
| FreeCAD | DPC-019, FreeCAD **1.1.4**, through the pinned bundled Python: `C:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/python.exe`. Headless, closed stdin, owned processes and captured streams. A bare `python.exe` must not accidentally select host Python; an alternative executable requires its own verified/pinned identity before freeze. |
| Time | Propose **1200 active operational seconds per arm/task**, with identical preregistered boundaries/accounting for both arms. Include model/tool/CAD/preparation/collection work; preserve the harness's nested stage limits rather than granting extra stages. Retain full wall time and separately tagged custody/research holds. Verified rule-#6 unavailable cycles alone receive their established active-clock exemption: full 600 s wait, identical resend, uncapped; no budget reset or clipped wait. No independent suite wall ceiling that defeats that rule. |
| Model-call accounting | Propose **three non-exempt invocations maximum** per arm/task. Count every assistant continuation after tool results, including inspection, repair, parsing and finalization—not one whole shell/agent session as one call. Tool executions themselves are timed/logged, not additional model calls unless they invoke a model, which is forbidden. The bare arm may allocate its three invocations freely; the harness retains its initial/shared-P1/R1 rules. Three calls are not two guaranteed repair rounds plus unlimited tool continuations. No fourth wrap-up invocation. |
| Handover | Bare agent supplies ordinary native `model.FCStd`, `model.step`, and reproducible source/dependencies in the designated output directory. A neutral collector records first explicit handover, later artifacts, hashes and full streams; it neither builds nor repairs the model. Freeze how a terminal tool-producing response submits artifacts without needing a fourth model call. Timeout/unsubmitted/missing/invalid artifacts remain failed or incomplete records, not salvaged successful handovers. |
| Same cards / judging | Same frozen source assets, geometric/semantic targets, numerical bounds, native editability/reopen gates and Astra Max rubric for both arms. Checking occurs outside the stopped bare construction session; no private-card feedback to help it iterate. The neutral artifact adapter must not require a harness plan, a harness proxy class, `PoleOffsets` by name, or harness-specific feature history to pass a bare artifact. It must prove the same requested geometry and operative-native behavior independently, with no inferred/made-up geometry. |

**Freeze prerequisite:** demonstrate the common artifact/checker adapter on independent fixtures for both construction methods. Existing stage-specific verification cannot simply be pointed at a bare FCStd if it requires a harness-generated plan or proxy. Do not waive the same-card gates or quietly run the harness constructor to fill that gap. This is a protocol/implementation prerequisite, not a request for another user dimension or tolerance.

### Proposed finite reservation — not yet adopted

| Reservation | Proposed maximum |
| --- | ---: |
| With-harness generation: 20 tasks × 3 | 60 |
| Bare-agent generation: 20 tasks × 3 | 60 |
| Astra adjudication: 40 condition records × 1 | 40 |
| Benchmark total | **160 non-exempt model invocations** |

The additional bare-arm **60** is explicit; no borrowing from the original 163-call holdout, new-family reservation or pilot. One adjudication per record, no favorable re-score. All non-exempt unsuccessful/aborted invocations are charged conservatively; verified overload exemptions do not imply free provider billing. Fresh quota evidence is required: consult/admit no new calls at 55%, stop at 60%, stop on missing/stale evidence. No quota percentage, price or observed saving is invented here.

Retain the agreed independent 20-pair corpus/custody, balanced order, full capture and durable `cad-harness.cad-time-benchmark.v1` evidence. Replace human-construction fields with agent/tool-session identities and timings; preserve any actual human judgment fields. Compare wall with wall and matched operational/CAD metrics, never machine elapsed with human-active time. Keep failures, interruptions and unstarted cases enrolled; unfinished completion-time savings are null, and zero baseline reduction is null with `zero_baseline`. Keep first-handover critical-error history and the existing correction/adoption gates. Same-model pairing removes the human-skill confound, but provider variability, context, tools, preparation and workflow differences remain; results apply to these frozen envelopes, not a universal or exact causal saving.

**Disposition:** amendment signed AGREE; envelope counter-proposed with the numerical ceilings above still pending explicit three-party agreement. No live/model/CAD run, pilot/private attachment access, code edit or commit for this review.
