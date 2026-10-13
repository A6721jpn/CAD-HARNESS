# VERIFY v2 implementation review

Read-only pass, 2026-10-13 08:38 JST, against `PLAN-V2-CONSENSUS.md` (grok AGREE 2026-10-13 00:21:58 JST). Uncommitted tree. No code edits. No FreeCAD, Sol, or unittest runs. The host counts at the end are `impl-notes.md` records.

## Verdict

READY

MUST: none.

## Tracked diff

`git diff --stat` is three files, +25/−9.

- `tools/cad_run.py:106` adds probe profile `verify-v2`. `load_gold` dispatches to `cad_verify_v2_probe` at 139–150. `verification_timeout_s` is required in 1..300 only for that profile (157). `verify_artifacts` uses `request["verification_timeout_s"]` with default 300 (333).
- `tools/cad_run_freecad.py:143–144` and `tools/cad_verify_freecad.py:18–22` load the v2 probe only when `probe_profile` is `verify-v2`.

`cad_agent.py`, `cad_verify_probe.py`, `cad_verify_guard.py`, `cad_spec.py`, `cad_spec_probe.py`, `eval_mvp.py`, and eval-v1 are absent from that diff. MVP episodes in this suite still call `cad_agent.run_mvp_driver` (`tools/eval_verify_v2.py:439–440`).

## Aligned

### Probe reachability

`tools/cad_verify_v2_probe.py` seeds non-construction geometry from Profile, Sections, and Spine subnames (37–57, 118–125) and a unique ReferenceAxis construction axis (126–137). An Edge match that is not exactly one real geometry raises `unsupported_verify_v2_ambiguous_geometry` (54–55). `references` keeps indexes with `0 <= i < GeometryCount` (60–62). Edges require an active constraint whose `Driving` attribute is true and whose type is in `RELATIONS` (15–16, 68–70). Radius and Diameter sit in `DIMENSIONS` (17) and do not create edges. A driving dimension is counted only when every referenced geometry is in the reached set (152–160). Half-value match stays `v1.close` at 0.01 mm (162). `native_valid` is stored before the dimension checks (141).

`tools/test_verify_v2_native.py:31–57` asserts Diameter 60 only for the chain path `[0, 2, 1]`. Isolated construction, an origin link to −1, a non-driving reference, and an inactive constraint do not count 60. The saved v1 V5 reopen asserts geometry, editability, value 60, and a path longer than 1 (13–27). Those tests were not re-run in this review.

### Parse, repair, deadline

`question`, `interpretation`, `source`, `parse_repair`, and `repair` are separate counters, one each (`tools/cad_verify_v2_guard.py:37`, 46–57). Route caps are source 4, spec 3, ask 1, completion 4 (`tools/cad_verify_v2_agent.py:42–45`). The first CAD attempt sets `generation_closed` (guard 64–69). Repair starts only when `attempts == 1`, then `begin_repair` (guard 71–77, agent 256–260). A later CAD failure breaks with `cad_repair_failed` (agent 256–257). The repair contract forbids an unsupported or clarification fallback (agent 83). Unsupported during repair raises `unsupported_route` (178–179). A parse during repair merges the previous feedback (204).

`Fault.inject` returns the candidate unchanged once `attempted` is true (`tools/cad_verify_guard.py:95`). `reached` and `injected` are set together on a successful match (125). `observe` requires `predicate_fail`, `geometry_ok` false, and `native_valid` true (128–136).

The episode clock is 900 s with 450 s stage windows (guard 31–33). `begin_repair` requires 450 s remaining (74–75). Repair Sol timeout is 180 s and repair CAD timeout is 90 s (79–84). The suite clock is 10800 s. `before_episode` requires 960 s remaining (20–23). Aggregate binding requires `deadline_monotonic - started_monotonic == 10800` (`tools/eval_verify_v2.py:542`). `deadline_ok` requires the monotonic clock to be before the deadline and `wall_s < 10800` (572). An episode at or above 900000 ms becomes `episode_deadline_exceeded` (agent 274–275).

When `repair_eligible` is true and the repair count is 0, the agent writes `harness_repair_not_invoked` unless the reason contains `quota_`, `sha_`, `agents`, `deadline`, `reservation`, or `budget` (agent 269–273). `record` re-derives eligibility and sets `harness:repair_not_invoked` when that slot was skipped (`tools/eval_verify_v2.py:341–348`).

### Completion cohort

Completion entries in `design/cad-harness-verify-v2/run-order.json` are `scored: false`. `summarize` builds `core` from scored rows and sets `bar_met` from the 51-row thresholds (`tools/eval_verify_v2.py:490`, 504–524). C2 and C3 live in `summary["completion"]` (508–515). Wilson for a C part stays null unless every planned row of that part completed (513). `completion_reached` becomes true only inside `invoke`, after `before_call`, when the route is completion and the purpose is interpretation (agent 95–101). A wrong or invented first question breaks with `completion_initial_question_miss` and leaves the prompt on the description (169–171). A later clarification breaks with `completion_additional_question` (175–177). Gold `description` must equal the description, or `description + "\n" + answer` on the completion route (51–54).

### Holdout, gold, exclusive outputs

On-disk `description.txt` bodies end with 「単位mm。他の加工なし。」. W3 and A1 omit 「XY中心、下面Z=0。」. 「寸法列はX×Y（3つ目はZ）。」 does not appear in the test payloads. Description SHA-256 pairs match: K1 and W1 `035a1dd33ac00fa82df0b5449ed80eb3b3a240ac826d44a1446beebbfb217a62`, K2 and W5 `0adcb4da674e082da1b11ae66d231d58f8283023f039080835d3e345ea5fb1d3`, K3 and W6 `b331927aa26d35e1ebee0b3b4b8d52e53dd409e727565676fcd7a27fabc0041b`. Volume targets: W1/K1 53758.93348822854, W2 39200, W3 6158.63314627976, W4 33280, W5/K2 66041.94128460104, W6/K3 81743.99719019869, S2 45500, A1 53057.522203923065, C2 35539.92930917844, C3 29115.27881988345. W5 `key_dimensions_mm` includes 72 (`test/W5/gold.json:171`).

The first Sol context is `developer_context(skill, contract, previous)` with `previous` None (agent 70, 84). Gold goes to `cad_run.py --gold` (223–226). `run` refuses a manifest whose version does not start with `verify-v2-reviewed-` or whose CLI is missing (`tools/eval_verify_v2.py:132–135`). Aggregates are `reports/aggregate-verify-v2-<suffix>.json/.csv` and refuse an existing path or a symlink (533–534). JSON uses `eval_verify.write_json` (`open("x")`, `tools/eval_verify.py:36–38`, bound at `eval_verify_v2.py:38`). The CSV opens with `"x"` (585). `driver-run.json` opens with `"x"` (agent 279).

### Quota and order

`quota_snapshot` stops on missing or invalid input, age < 0, age > 300, `used_percent >= 60`, and `used_percent >= 55` (`tools/cad_verify_guard.py:20–46`). Each scored call row requires decision `allow`, age in 0..300, and `used_percent < 55` (`tools/eval_verify_v2.py:224–226`). `before_call` runs before `budget.call` (agent 95–96).

`run-order.json` has `planned_calls` 83 and `max_calls` 163. The v2 Guard rejects a call budget outside 1..163 (`tools/cad_verify_v2_guard.py:12–15`). Aggregate requires `real_calls <= call_budget <= 163` (`tools/eval_verify_v2.py:570`).

## SHOULD

1. `tools/cad_verify_v2_agent.py:254`. After `repair_reason`, a spec attempt with `editability_ok` false replaces the reason with `compiler_native_failure` and raises. A settled in-schema editability miss on W6, S2, A1, a completion build, or K3 never reaches `begin_repair`. Source-route misses still follow `cad_agent.repair_reason` (`tools/cad_agent.py:219–230`). `record` repeats the same exclusion (`tools/eval_verify_v2.py:344`). The episode stays a miss, so this branch cannot make `bar_met` true. The plan’s settled-repairable rule still calls for that reserved repair.

2. `tools/eval_verify_v2.py:175`. `harness_failure` returns `"harness:"+code` when the message contains `repair_time_reservation_lost`. `record` stores that as `stop_reason` (320). `run` then sets `stopped` and skips later episodes (449). `bar_met` requires `not stopped` (524). The agent leaves `repair_time_reservation_lost` as written because the reason contains `reservation` (agent 272). The plan treats loss of the 450 s repair reservation as a time stop. This path stops the version.

## NIT

1. `tools/cad_verify_v2_guard.py:80`. `parse_repair` Sol timeout is 60 s during the initial 450 s stage as well as during repair. The plan’s unused-P 60 s bank is the repair stage. An initial parse can stop early and the episode stays a miss.

2. `tools/cad_verify_v2_probe.py:143–149`. Feature `Length`, `Length2`, `Radius`, `Size`, and `Size2` are collected whenever the property exists. `impl-notes.md` records that an unused `Length2` default of 5/10 once satisfied a missing driving dimension, and the fixture source was set to Type=0 with `Length2=0`. Gold and gates stayed as written.

3. `tools/cad_verify_v2_guard.py:14–15`. The constructor passes `min(call_budget, 125)` into the v1 Guard, then assigns `self.call_budget = call_budget`. v1 `before_call` reads `self.call_budget`, so the effective cap is the requested budget up to 163.

4. `tools/cad_verify_v2_guard.py:40–44`. `remaining()` subtracts the 30 s reserve inside the stage window. After an initial stage that uses the full 450 s, `begin_repair` can still pass and the usable repair remainder is 420 s. The 180 + 90 + 90 + 30 breakdown still fits in the episode.

5. `tools/eval_verify_v2.py:340` and `:354`. Pass walls are strict `< 900` and, for ask, `< 450`. A sample that lands on the boundary is a miss.

6. `tools/cad_verify_v2_guard.py:17`. v2 `Guard.remaining` defaults the reserve to 30 s. MVP episodes in this suite receive that Guard (`tools/eval_verify_v2.py:439–440`). v1 `CLEANUP_RESERVE_S` is 5 (`tools/cad_verify_guard.py:13`). The shared clock stops earlier. MVP’s own 900 s / 3-call driver is unchanged.

7. `design/cad-harness-verify-v2/test/W5/gold.json:99`. One hole coordinate is `4.408728476930472e-15`, inside the ±0.01 mm tolerance of 0. `key_dimensions_mm` still lists 72 (line 171).

8. `tools/cad_verify_v2_agent.py:102–105`. `subprocess.TimeoutExpired` leaves the call row without `exit`. The handler at 261 records the exception. This is a triage gap.

9. `tools/eval_verify_v2.py:132–135`. The on-disk `SHA256.json` is the phase2 uncommitted manifest. Live run raises `supervisor_reviewed_freeze_required` until a reviewed freeze binds the CLI. `freeze` writes that path with exclusive create (`eval_verify_v2.py:84`). Archive the phase2 manifest before the reviewed freeze. Leave v1 aggregates in place.

## Host records

`impl-notes.md` records unit discover as 90 tests, 84 PASS and 6 native skip; native v2 3/3; DV3 native 3/3; smoke r3 41/41; legacy 4/4; mock 60 episodes with mock calls 82. This review did not re-run them.

verdict: READY
