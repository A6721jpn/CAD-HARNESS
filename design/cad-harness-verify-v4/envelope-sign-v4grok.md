# Bare-arm envelope — v4grok

Verdict: **AGREE**

Reviewed `c-de-amend-sign-sol.md`. No code edit, no commit, no live call, no CAD run. `pilot-user/` was not opened. This agreement does not authorize a run and does not amend `PLAN-V4-ADDENDUM-C.md`.

## Amendment

AGREE with `c-de-amend-sign-sol.md:3-7`. `DECISIONS.md:70-71` and `PLAN-V4-ADDENDUM-C.md:105-108` replace the human construction arm with the same Codex model and the same requests, without `cad_run`, CAD-harness skills or contracts, or the harness CLI. Bare-arm model calls need their own reservation. Construction-operator and human-engineering-time fields are not-applicable. A required human judge or adoption identity stays applicable. RESULTS state harness-versus-bare-agent performance, not human hours saved.

`c-de-amend-sign-sol.md:7` matches `batch2-v4grok.md:74-82`: the earlier sign left the envelope open, and the 100-call total had counted a zero-call manual arm.

## Envelope

AGREE to the counter-proposal in `c-de-amend-sign-sol.md:9-37` as the bare-arm operating envelope required by `PLAN-V4-ADDENDUM-C.md:106`.

- Model: both arms `openai-codex/gpt-6.1-sol`, thinking `xhigh` (`c-de-amend-sign-sol.md:15`). That is the same model on both arms, as `DECISIONS.md:71` requires. It is the with-harness generator already named for this benchmark, not a new user model.
- Inputs: same verbatim request and original assets; no CAD-harness skills, contracts, harness CLI, or harness-derived facts given only to one arm (`c-de-amend-sign-sol.md:16`). Preparation is charged to the arm that does it.
- Tools: noninteractive shell and file I/O in an isolated scratch workspace; no network fetch, package install, GUI, model delegation, harness modules, `cad_run`, harness CLI, or evaluation oracles (`c-de-amend-sign-sol.md:17`). The harness repository is not mounted. This is the tools clause `PLAN-V4-ADDENDUM-C.md:106` left open. It corrects `c-de-amend-sign-gemini.md:23`, which named `bash` on this Windows host.
- FreeCAD: DPC-019, FreeCAD 1.1.4, headless, through the pinned bundled `python.exe` (`c-de-amend-sign-sol.md:18`). Version 1.1.4 is the version named in `PLAN-V4-ADDENDUM-C.md:106`. The pin rejects an unbound host `python.exe`. It is tighter than `c-de-amend-sign-gemini.md:24`, which allowed `freecadcmd.exe` or `python.exe`.
- Time: 1200 active operational seconds per arm/task (`c-de-amend-sign-sol.md:19`). That ceiling is the episode limit already in `c-d-proposal-sol.md:89`, applied to both arms. User authority to extend time is `DECISIONS.md:64`. Nested harness stage limits stay. The 600 s identical resend is the existing rule `#6` in `DECISIONS.md:7-9`, not a new wait.
- Calls: at most three non-exempt model invocations per arm/task, counting each assistant continuation after tool results (`c-de-amend-sign-sol.md:20`). The harness keeps initial / shared P1 / R1. There is no fourth wrap-up call. This is an agent ceiling under the call-count item in `PLAN-V4-ADDENDUM-C.md:106`. It is not a user-specified call count. It rejects reading `c-de-amend-sign-gemini.md:26` as two repairs plus unlimited tool continuations.
- Handover: `model.FCStd`, `model.step`, and reproducible source, taken by a neutral collector (`c-de-amend-sign-sol.md:21`). Timeout or missing artifacts stay failed or incomplete.
- Same cards: same frozen targets, numerical bounds, reopen gates, and Astra Max rubric (`c-de-amend-sign-sol.md:22`). The adapter must not require a harness plan, proxy, or harness feature name, and it must not be filled by running the harness constructor. The fixture check at `c-de-amend-sign-sol.md:24` is a freeze prerequisite. It adds no user dimension or tolerance.

## Reservation

AGREE to the proposed reservation in `c-de-amend-sign-sol.md:29-33`: 20 × 3 = 60 with-harness, 20 × 3 = 60 bare-arm, 40 × 1 = 40 Astra, total 160 non-exempt invocations. The 20 pairs and the schema `cad-harness.cad-time-benchmark.v1` are the existing C-D(e) corpus (`c-d-proposal-sol.md:117`, `PLAN-V4-ADDENDUM-C.md:102`). The extra 60 is the bare-arm budget line `PLAN-V4-ADDENDUM-C.md:107` required. Nothing is borrowed from the original 163. Quota consult at 55% and stop at 60% is `DECISIONS.md:63`. These ceilings are agent proposals. They are not user measurements, prices, or observed savings (`c-de-amend-sign-sol.md:35`).

`c-de-amend-sign-gemini.md:32-43` has the same 160 arithmetic with looser arm rules. This AGREE adopts sol's rules at `c-de-amend-sign-sol.md:15-24`, not that looser wording.

No live calls, CAD, private holdout access, or commit.
