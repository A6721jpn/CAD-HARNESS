# Integrated lock reissued against committed HEAD — sol

Reissued and verified. No implementation source was changed, no commit was made, and no live/model-generation calls were made. Neither `pilot-user/` nor `v4-holdout-private` was opened.

## New lock identity

- **Bound HEAD:** `6f832af0474e148c42975f4e48df0a7263b0332b`.
- Bound tree: `ee60794f97ea92184d5f60a4c6e9532b79f7ae21`.
- Manifest: `reports/verify-v4-integrated-relock-20261014T153013Z/integrated-lock-head/manifest.json`.
- **Manifest SHA-256:** `6a92bbbccb2f8861b401e3dfb488dd9c70074c9dfb4477a7e34b511abf113542`.
- `SHA256.json` SHA-256 / manifest `sha256_file`: `f9bad43f37d09ea0328e667f58aebdc869655800c6ac9a84855280e1e67ae9eb`.
- Profiles: `original`, `c-s1`, `c-s2`, `c-s3`; 197 source/cache records and 20,155 SDK records.
- Authorization remains **null**, `final_v4_ready` remains **false**, and `live_calls` is **0**.

## Proof reuse decision

**Previous proof reused: NO.** The byte comparison found seven changed and nineteen added repository Python bytecode caches relative to the previous lock. The implementation source files were unchanged, but executable cache bindings were not; the old proof therefore did not qualify for reuse. No cache was deleted, restored or relabeled to force acceptance.

The existing independent development inputs, cards, checker contexts and submitted FCStd/STEP artifacts were retained. Their native checks were rerun with fresh execution-time bindings: all ten C1–C5 bare/harness commands exited 0 and passed, covering twenty independently reopened representation judgments. No CAD-generation model was called, and no pilot/holdout was run.

Fresh proof: `reports/verify-v4-integrated-relock-20261014T153013Z/neutral-proof-head.json`, SHA-256 `de45e7d36493dcf9128d9860bc8615e3f0c9d8860a89a0020ec15a3e032bbd71`.

## Observed verification

- Actual `integrated-lock` command: **exit 0**, 109.475454 seconds.
- Actual `verify-integrated-lock` command against the new manifest: **exit 0**, 61.329116 seconds.
- Full stdout/stderr, bound-byte differences, fresh checker runs and `relock-summary.json` are retained under `reports/verify-v4-integrated-relock-20261014T153013Z/`.

This replaces the prior HEAD's lock for the requested implementation-lock prerequisite; it does not grant live authorization or final v4 readiness. Any subsequent HEAD or bound-byte change requires another valid lock. This task did not rerun the unrelated full regression suites or alter existing implementation files.
