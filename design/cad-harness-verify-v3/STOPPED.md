# v3 STOPPED — harness stop (2026-10-13 15:57 JST)

- Run host-verify-v3-reviewed-r1: 46 of 60 episodes completed, then a harness stop: `harness:missing_report_or_artifact`.
- Trigger: q-A5-r5. Its single Sol call (question) exited with code 1 after about 4 s. The cause was not recorded; quota showed 0% used and codex login status was OK. The guard then stopped all remaining episodes: A5-r5, A6-r5, C4/C5 x3 and F4–F6 x2, all not_started.
- Aggregate: reports/aggregate-verify-v3-host-reviewed-r1.json. complete=false, bar_met=false. The thresholds that were met are source, complex, stock, defaults, ambiguity, mvp and legacy. Faults was not met because 0 of 6 fault episodes were reached.
- Completed parts: P1–P5 2/2 each; legacy 4/4; G1 1/2; G2–G4 2/2; G5 1/2; G6 3/3; S3 5/5; A4 3/3; A5 4/4 and A6 4/4 of the completed episodes (4/5 each counting the stopped r5). G1-r2 and G5-r1 failures are not yet analysed.
- Per the user's order, we stop here: no RESULTS consensus, no rerun, no v4. Any rerun needs a new prefix (and, per the rules, possibly a new version) after the user switches accounts.
