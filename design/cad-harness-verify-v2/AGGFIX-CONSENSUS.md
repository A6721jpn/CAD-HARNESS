# AGGFIX CONSENSUS DRAFT (supervisor synthesis, 2026-10-13)

Base: codex's exact change in aggfix-codex.md (items 1-5), because the user ordered an explicit re-freeze as `verify-v2-reviewed-r1-aggfix` with FROZEN.md. Grok's blockers (digest / version / frozen_sha256 / load sha_mismatch) are each resolved by codex's archived-manifest binding: run records bind to SHA256.run-r1.json (byte-identical original, digest 129087752b...), while load() verifies the new aggfix manifest whose only file-hash delta is exactly {tools/eval_verify_v2.py, tools/test_verify_v2.py}; aggregate top-level version/sha_manifest/frozen_sha256 stay the original measurement identity, plus aggregation_identity.

Added from grok: (a) `run` must refuse any version ending `-aggfix` (Stop "aggfix_no_live_run"), with a unit test; (b) deadline_ok and the ended_elapsed_s>=10800 check stay exact; (c) the stored pair 525342.3589999999 - 514542.359 is the accepted test case.

No scoring/gold/threshold/order/runner/Probe change. No new Sol/CAD run.

Signers: append "AGREE <name> <JST time>" or COUNTER with exact change to this file's sign section via your aggfix-<you>.md (append a line "consensus: AGREE").
