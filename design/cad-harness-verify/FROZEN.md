# VERIFY v1 FROZEN

- version: verify-v1-reviewed-r1
- implementation commit: b339f9d (FIX1-4; reviews grok READY + gemini READY)
- plan commit: f0e8953 (PLAN-CONSENSUS codex+grok AGREE)
- manifest: design/cad-harness-verify/SHA256.json (133 files, sha256 d03406333a4a01fdae336c8582f71cb2f3d6edd9a9a7c01b78d92366a2069edc); pre-fix snapshot archived as SHA256-initial-pre-fix.json
- frozen at: 2026-10-12 19:43 JST (supervisor, DPC-019)
- host checks: 74 unit tests OK (3 native skips); offline 47 + legacy 4 + F1-F3 7 PASS per impl-notes.md
- Phase 3 prefix: host-verify-v1-reviewed-r1; no edits to test/, gold, rubric, faults, code after this commit. Any later fix = new version + fresh holdout.
