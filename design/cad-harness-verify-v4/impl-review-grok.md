READY

Phase 1–2 matches the signed plan’s offline scope. `live_authorized_calls` is 0. `freeze` raises. `request` without a replay and `run` with `--sealed-input` or `--tasks` stop before creating output. The transport only replays a recording or an injected mock. `subprocess.run` and `Popen` are not called. `python -B -m unittest tools.test_verify_v4` ran 19 tests, OK.

Null stays null. A missing token, price, or wall makes `total` null and keeps `known_subtotal` separate. The v3 backfill at `reports/verify-v4-v3-backfill-p12-r2` has retained charged calls 88, archived 21, and all-work 109, with `retained_matches` and `total_matches` true. All five token totals are null (106 known, 3 missing). Price total is null with no rate source. Operational wall is null, reason `historical_operational_boundaries_not_recorded`. New stdout and stderr are written in full; only the parser tail is bounded to 16384 bytes. Historical tails stay `complete: false` with byte count null.

`modeling.md` is checked byte-for-byte against `skills/freecad-modeling/SKILL.md`. The listed v3 sources, old skill, and `design/cad-harness-verify-v3` have no diff. Replay sets `identical_summary` true and `fresh_holdout` `not_run`. Overload handling is exercised in mocks and still recorded as `UNVERIFIED`. Pilot rubric status is `not_run`.
