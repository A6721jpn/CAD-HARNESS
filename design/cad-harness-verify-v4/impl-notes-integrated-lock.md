# C-R3 integrated implementation lock — sol

C-R3 is signed **AGREE** in `c-r3-sign-sol.md`. The neutral checker and the integrated implementation lock are implemented and exercised locally. This is implementation evidence only: **authorization is null, final_v4_ready is false, and live_calls is 0**. No pilot, holdout, benchmark, CAD-generation model call, Astra judgment or worktree commit was performed. Neither `pilot-user/` nor `v4-holdout-private` was opened.

## Actual lock

Evidence root: `reports/verify-v4-integrated-dev-20261014T140454Z/`.

- Manifest: `integrated-lock-final/manifest.json` under that evidence root.
- `manifest.json` SHA-256: `bfc35e23e8627f4aafa4c81efa5f5ee2244a0c4ac7e3c51f8023c60b1a2813f3`.
- `SHA256.json` SHA-256, also recorded as the manifest's `sha256_file`: `09ce0ca18fff2fd676cf6c7174bcca48919b4847c4ffae252f4924a47f554f6e`.
- Bound HEAD: `1512304a5a3624aae7486bf7b2e081a6692e2e54`.
- Bound tree: `961ece600d255cfd7fdd25833869734e09103c05`.
- Bound repository root: `C:\dev\CAD-HARNESS-herdr`.
- Stage/status: `implementation` / `offline_locked`.

This is not a claim that HEAD contains the new uncommitted implementation. The lock binds the actual working-file bytes and each covered file's scoped HEAD blob identity. Its raw-byte overlay records 101 clean, 66 modified and 11 untracked entries; these include pre-existing work and are not a list of edits made by this task. No worktree Git index or history was changed. Integrity tests create their own isolated temporary Git histories.

The single valid integrated lock covers `original`, `c-s1`, `c-s2` and `c-s3`, including all four actual preflight results, 178 working implementation/source/cache records, the original/S1/S2 immutable archive bytes, skill and policy identities, contracts/schemas, compilers, recipes and judges. It additionally binds 20,155 SDK executable-source/cache/library/configuration files, including 7,318 existing bytecode caches, four registered recipe files and 130 transitive development-proof dependencies.

The registered `DejaVuSansMono.ttf` is bound explicitly with its license:

- Font SHA-256: `602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3`.
- `LICENSE_DEJAVU` SHA-256: `d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e`.

## Neutral artifact checking

New CLI surfaces are `judge-artifacts`, `integrated-lock` and `verify-integrated-lock` in `tools/eval_verify_v4.py`. The first accepts a native FCStd file and a separately exported STEP file through a hash-bound artifact bundle; it does not require a construction plan, compiler result, harness feature name, harness proxy class or a property named `PoleOffsets`.

Both arms use byte-identical judge cards and checker-only measurement context. That context contains only immutable source identity/selected surface registration, fixed contour registration and intended engraving/font/baseline measurements. It is not a build plan and is not generator input. S1 source references can be independently declared by the card, and supported S1 measurements can coexist. Source-only image-to-contour checks do not demand irrelevant candidate placement data.

FCStd and STEP are reopened and scored separately through the existing stage metric kernels and their original card thresholds. The native document must have the existing valid single-body/single-solid structure and recompute state. Generic property or sketch-dimension edits must visibly affect the selected output, or genuinely invalidate that output, then restore it. Merely changing metadata or an already-empty auxiliary object cannot prove editability. An independent document's unrelated `BuildStatus` wording is not treated as a harness token.

Checking does not save, repair or reconstruct the submitted artifacts. Python feature code must be explicitly declared and hash-bound before restoration; ordinary native Pad/Pocket files need no such extension. The SDK/source-cache snapshot is captured by the collector before launching the child and rechecked before/after native work and by the collector afterward. This prevents a later SDK identity capture from laundering a demonstration produced by different executable bytes. Python `-B` does not disable cache reads, so caches are included rather than assumed irrelevant.

C3 uses a separately authored, registered checker STEP stock baseline, not named candidate history or a candidate-derived filling of its recess. Actual registered glyph material, retained counters, depth and backing stock are measured using the same card-derived tolerances. The shared counter-stock correction applies to the owned harness path as well as neutral checking.

Implementation files:

- `tools/cad_verify_v4_artifacts.py`: artifact admission, native open/recompute, generic operative edit/restore and independent representation checks.
- `tools/cad_verify_v4_artifact_judges.py` and the existing `cad_verify_v4_judges.py`: plan-free measurement admission and shared metric kernels.
- `tools/cad_verify_v4_runtime.py`: executable SDK and repository/extension bytecode identities.
- `tools/cad_verify_v4_integrated.py`: HEAD/working-overlay binding, all-profile preflight, proof/recipe/runtime closure and strict zero-live verifier.
- `tools/cad_verify_v4_worker.py`, `cad_verify_v4_s1.py` and `eval_verify_v4.py`: existing owned native process, closed stdin, durable ledger/raw streams and CLI integration.
- `schemas/artifact-bundle.schema.json`, `artifact-context.schema.json` and `integrated-lock.schema.json`: strict new data contracts.

The original generation routes and per-stage owned-plan checks remain their legitimate generation paths; the new neutral checker is not a replacement constructor or a compatibility alias.

## Independent native demonstration

`dev-integrated/generate.py` authors development inputs/cards before constructing either arm. `dev-integrated/independent_native_models.py` uses FreeCAD/Part/Sketcher/math rather than harness constructors. The bare C1-C4 documents use ordinary native features; the bare C5 document has its own independent analytic feature/module and a real `InteriorLift` parameter. It uses neither a harness fitter nor a harness proxy/plan. Dimensions, polynomial coefficients, fonts and tolerances are development choices, not pilot-derived values or adopted user manufacturing tolerances.

The admitted current-source results are in `checks-v5/`:

| Development family | Bare FCStd / STEP | Harness FCStd / STEP | Exercised common measurements |
| --- | --- | --- | --- |
| C1 | PASS / PASS | PASS / PASS | Imported STEP facts/reference clearance, solid, bounds, volume and native roundtrip |
| C2 | PASS / PASS | PASS / PASS | Actual minimum radius/tool access, both fidelity legs, dimensions and native roundtrip |
| C3 | PASS / PASS | PASS / PASS | Registered glyph recess/counters/depth/backing stock, bounds and native roundtrip |
| C4 | PASS / PASS | PASS / PASS | Thickness distribution, unchanged source dimensions, preserved cavity region, face count, validity and native roundtrip |
| C5 | PASS / PASS | PASS / PASS | Merged-face count, bounded surface deviation, G1/G2, outside-region preservation, validity and native roundtrip |

All ten checker commands exited 0; all twenty independently reopened representation judgments passed. Each native operative probe restored its geometry. These are developer-authored fixture checks, not generated benchmark responses, an agent CAD-time baseline or evidence of pilot success.

The admitted proof packet is `neutral-proof-current.json`, SHA-256 `72d34f948d4302d78448276faf7d5275e71a96b0bebdd526c1d7c54e6e05c753`. It binds the same card/context/source/prepared bytes for both arms, current implementation hashes, submitted artifacts and actual per-run SDK/cache snapshots. Older checks and failed attempts remain audit history and are not the lock's admitted demonstration.

## Verification actually run

| Final suite | Run | Passed | Skipped | Seconds |
| --- | ---: | ---: | ---: | ---: |
| Host | 177 | 176 | 1 | 100.315 |
| Pinned native runtime | 103 | 103 | 0 | 194.226 |

The sole skip is the existing Windows symlink-privilege control. Original v3/v4/freeze/pilot/live tests and existing S1/S2/S3 tests were retained and exercised. The new suites cover wrong geometry/registration/source, glyph identity/depth/counters, unsupported certificates, metadata-only and empty-auxiliary edits, arbitrary independent status wording, native sketch edits, FCStd/STEP disagreement, changed HEAD/working bytes, authorization escalation, missing recipes/font/license/proof dependencies, canonical recipe commitments, executable cache changes, stale execution runtime and contradictory native evidence.

Host integrity tests use synthetic independent files and injected identity records; they do not claim CAD acceptance. Actual geometry and lifecycle evidence comes from the pinned native runs and the ten CLI checks above.

Native environment: FreeCAD 1.1.4, Python 3.11.14, OCCT 7.8.1. The final native command enabled `CAD_VERIFY_S1_NATIVE`, `CAD_VERIFY_S2_NATIVE`, `CAD_VERIFY_S3_NATIVE` and `CAD_VERIFY_ARTIFACT_NATIVE`, and used the independently generated `source-s1`, `source-s2` and `source-s3` fixture directories. Exact executable/module argv arrays and paths are recorded in `integrated-smoke-summary.json`.

Final full logs under the evidence root:

- `host-suite-green.stdout.bin` / `host-suite-green.stderr.bin`.
- `native-suite-final-green.stdout.bin` / `native-suite-final-green.stderr.bin`.
- Each `checks-v5/<family>-<arm>/` retains its ledger, job, SDK snapshot, readiness evidence, complete native stdout/stderr, result and summary; command-level streams are retained alongside them.
- `integrated-lock-final/` retains its identity worker evidence and raw streams.

The actual `integrated-lock` command exited 0 in 123.611326 seconds. The actual `verify-integrated-lock` command exited 0 in 60.563755 seconds. Their complete command stdout/stderr are `integrated-lock-final-create.*.bin` and `integrated-lock-final-verify.*.bin`. Both stdout streams have SHA-256 `f43d5b5e0f0fab26b8fa90af836fbafa626b98eae7ce018e55f1b06d2765278b`. Earlier fixture/API/inventory-contract failures were corrected before these final green results; failed logs were not relabeled or discarded.

## Limits and relay handling

- The lock records integrity and local provenance, not a signature, hard OS sandbox, complete operating-system image or portable environment. Explicitly bound Python feature dependencies are executable trusted code. External linked FCStd documents and arbitrary external multi-module Python feature packages are not supported by this adapter; ordinary native features and an independent single-module feature were exercised.
- Real-case measurement registration and C3 checker stock must be independently fixed before scoring. The checker does not infer missing acceptance data, invent geometry or obtain pilot attachments. Unsupported S3 surface domains retain the existing nonrational/nonperiodic rectangular polynomial-spline certification limits and remain UNVERIFIED rather than being promoted to PASS.
- No new user tolerance, fresh cohort, pilot result or live authorization follows from these development numbers. Consensus section 5 gates and separate future family/benchmark reservations remain unchanged. The future holdout/bare generator is the agreed `openai-codex/gpt-6.1-sol` with `xhigh`; the configured pilot generator/judge is `openai-codex/gpt-6-astra` with `max`. None of these generation or judgment calls was invoked here.
- A change to HEAD invalidates this lock even if source bytes are unchanged. **After the relay commits, issue a new integrated lock against that new HEAD before fresh family authoring.** The existing proof is reusable only while all its bound implementation, input, card, recipe, extension, cache and SDK bytes remain unchanged; otherwise regenerate the affected native evidence. Do not silently rewrite old proof bindings.
- The evidence uses absolute root-anchored paths. Preserve the report bundle and referenced inputs together; a worktree commit alone does not preserve ignored runtime evidence. This task made no commit.
