# Family holdout commitment — v4grok

Custodian: v4grok, sole holdout author (option B). Private tree: `C:\dev\v4-holdout-private\families-v1\`. This file is the public commitment. It records counts, strata, schema versions, admission-control results, call budgets, and SHA-256 identities. Live calls: 0. This task does not commit and does not re-issue the integrated lock.

## Counts

43 generative items + 4 admission controls = 47. Benchmark corpus: 20 pairs, 4 per family C1..C5. Roster schema `cad-harness.family-roster.v1`, `live_calls` 0.

| Family | Profile | Generative | Benchmark pairs | Generation ceiling | Astra ceiling | Generative strata |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| C1 | c-s1 | 10 | 4 | 30 | 10 | Prismatic references (prismatic) 4; stepped/oriented references (stepped_oriented) 3; curved/irregular references (curved_irregular) 3 |
| C2 | c-s1 | 10 | 4 | 30 | 10 | Convex profiles (convex) 3; connected-material profiles with holes (connected_holes) 4; notch/tool-access cases (notch_tool_access) 3 |
| C3 | c-s1 | 8 | 4 | 24 | 8 | Numeric arrays (numeric) 3; registered alphanumeric labels (alphanumeric) 3; dense layouts (dense) 2 |
| C4 | c-s2 | 8 | 4 | 24 | 8 | Planar/oblique offsets (planar_oblique) 2; curved offsets (curved_offsets) 2; finite-planar-face replacement/reconnection (finite_planar_replacement) 2; adjacent-feature preservation (preservation) 2 |
| C5 | c-s3 | 7 | 4 | 21 | 7 | Two-patch curved rebuilds (two_patch) 3; trimmed multi-patch spline rebuilds (trimmed_multi_patch) 4 |
| Admission | separate | 4 | 0 | 0 | 0 | Corrupt STEP 1; open contour 1; fixed-geometry/tool infeasibility 1; unavailable registered glyph 1 |
| Total |  | 47 | 20 | 129 | 43 | 43 generative + 4 controls |

Benchmark strata, from the roster:

- C1: Prismatic references (prismatic) 2; stepped/oriented references (stepped_oriented) 1; curved/irregular references (curved_irregular) 1
- C2: Convex profiles (convex) 2; connected-material profiles with holes (connected_holes) 1; notch/tool-access cases (notch_tool_access) 1
- C3: Numeric arrays (numeric) 2; registered alphanumeric labels (alphanumeric) 1; dense layouts (dense) 1
- C4: Planar/oblique offsets (planar_oblique) 1; curved offsets (curved_offsets) 1; finite-planar-face replacement/reconnection (finite_planar_replacement) 1; adjacent-feature preservation (preservation) 1
- C5: Two-patch curved rebuilds (two_patch) 2; trimmed multi-patch spline rebuilds (trimmed_multi_patch) 2

Signed stratum gates and the C5 cohort sentence are at `c-d-proposal-sol.md:54-59`. The C5 gate remains that signed sentence (`c-d-proposal-sol.md:58`). Family gates are independent. There is no pooling and no borrowing from the original 163-call unchanged-scope holdout or from the benchmark reservation (`c-d-proposal-sol.md:72`, `PLAN-V4-ADDENDUM-C.md:100`, `PLAN-V4-ADDENDUM-C.md:112`).

## Call budget

Family reservation: 129 generation calls + 43 Astra judge calls = 172. Per-family ceilings are the table above (C1 30+10, C2 30+10, C3 24+8, C4 24+8, C5 21+7, admission controls 0+0). Quota consult at 55 percent and stop at 60 percent (`DECISIONS.md:63`).

Benchmark reservation, agreed envelope (`PLAN-V4-ADDENDUM-C.md:112`): with-harness generation ≤60, bare-arm generation ≤60, Astra judge ≤40, total ≤160. Both arms use `openai-codex/gpt-6.1-sol` thinking `xhigh`. The judge is `openai-codex/gpt-6-astra` thinking `max` (`DECISIONS.md:15-16`, `DECISIONS.md:24-25`, `PLAN-V4-ADDENDUM-C.md:117`). Each private pair record uses schema `cad-harness.cad-time-benchmark.v1`, `same_card_both_arms` true, `status` `not_run`, and null timings. The comparison labeled for RESULTS is harness-vs-bare-agent. Authoring this corpus is not execution authorization.

Holdout generator: `openai-codex/gpt-6.1-sol` / `xhigh`. Astra Max is the judge. Astra Max generation stays the pilot generator only.

## Admission

63 generative and benchmark items were admitted by `cad_verify_v4_artifact_judges.validate_context` and `cad_verify_v4_artifacts.load_bundle` before this C2 retirement. Every bundle has `evidence_mode` `independent_dev` and `output_object` null. These bundles are pre-generation schema shells. No generation ran. The 14 retired C2 bundles remain that history in `retired-c2-v1/`. The cycle-1 fresh C2 bundles were admitted again by the same two checkers after preparation with `c2-production-recipe.json`, and those bundles are now history in `retired-c2-cycle1/`. The cycle-2 C2 bundles were admitted by the same two checkers. No model generation ran.

The four admission controls were replayed with the pinned FreeCAD 1.1.4 interpreter. Each remained refused, and the reason codes matched `admission/results.json`:

| Control | Checker | Result |
| --- | --- | --- |
| AC-corrupt-step | `cad_verify_v4_inputs.inspect_step` | admitted false; `ValueError` `ambiguous_step_length_unit` |
| AC-open-contour | `cad_verify_v4_judges.planar_geometry` | admitted false; `ValueError` `judge_open_loop` |
| AC-tool-infeasible | `cad_verify_v4_judges.tool_access` | admitted false; status `FAIL`; `tool_access_FAIL` |
| AC-unavailable-glyph | `cad_verify_v4_artifact_judges.validate_context` | admitted false; `ValueError` `glyph_coverage` |
| AC-unavailable-glyph text outline | `cad_verify_v4_text.text_outline` | `ValueError` `font_glyph_coverage:81` |

Admission-control gate: 4/4 pre-generation refusal, with no generated deliverable. Generation calls 0. Astra calls 0.

## Schema versions

Frozen schema file `$id` values used for admission:

- `cad-harness.judge-card.v4c`
- `cad-harness.s2-judge-card.v4c`
- `cad-harness.s3-judge-card.v4c`
- `cad-harness.artifact-context.v4`
- `cad-harness.artifact-bundle.v4`
- `cad-harness.inputs.v4c`
- `cad-harness.inputs.v4c.c-s2`
- `cad-harness.inputs.v4c.c-s3`
- `cad-harness.prepared.v4c`
- `cad-harness.prepared.v4c.c-s2`
- `cad-harness.prepared.v4c.c-s3`
- `cad-harness.step-recipe.v4c`
- `cad-harness.step-recipe.v4c.c-s2`
- `cad-harness.step-recipe.v4c.c-s3`
- `cad-harness.step-facts.v4c`
- `cad-harness.step-facts.v4c.c-s2`
- `cad-harness.step-facts.v4c.c-s3`
- `cad-harness.contour.v4c`
- `cad-harness.contour-source.v4c`

Instance documents carry the `schema` const required by those files. The c-s2 and c-s3 judge-card, input, prepared, recipe, and step-facts files require profile `c-s2` or `c-s3` while their instance `schema` const stays the unsuffixed value (`cad-harness.judge-card.v4c`, `cad-harness.inputs.v4c`, `cad-harness.prepared.v4c`, `cad-harness.step-recipe.v4c`). Benchmark pair records use `cad-harness.cad-time-benchmark.v1`. That identifier is the signed dataset name; no JSON schema file for it is in the frozen schema directory. Custodian indexes use `cad-harness.family-roster.v1` and `cad-harness.family-admission-results.v1`.

Private `DejaVuSansMono.ttf` copies: 13. Each matches `skills/cad-harness-v4/fonts/DejaVuSansMono.ttf` SHA-256 `602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3`. Each `LICENSE_DEJAVU` matches SHA-256 `d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e`.

## Integrated lock

Authoring used the interim lock as evidence history. Bound HEAD in `impl-notes-integrated-lock-head.md:7` is `6f832af0474e148c42975f4e48df0a7263b0332b`. Manifest SHA-256 in `impl-notes-integrated-lock-head.md:10` is `6a92bbbccb2f8861b401e3dfb488dd9c70074c9dfb4477a7e34b511abf113542`. Authorization on that lock is null, `final_v4_ready` is false, and `live_calls` is 0 (`impl-notes-integrated-lock-head.md:13`). Worktree HEAD while this commitment was written: `6f832af0474e148c42975f4e48df0a7263b0332b`. C-R4 (`PLAN-V4-ADDENDUM-C.md:115-117`, signed in `c-r4-sign-v4grok.md`) keeps this interim lock as evidence. The operative lock is the one re-issued against the joint commit of the lock notes and this commitment at the final freeze.

## Sealed archive

`families-v1.sealed.zip` is inside the private directory. SHA-256 `588db92fa91cc276ff5d3dc13a7fdf16fa49395d6e420e6a81e0d56396c21dcf`. Bytes 3206379. Members: 708. Member names are lexicographic POSIX paths. ZIP timestamp is 2026-01-01 00:00:00. Compression is deflate level 9. The archive contains the other private files from that seal and omits its own filename. It is unchanged by this C2 retirement and by the cycle-2 retirement. It does not contain the fresh C2 cohort, the cycle-2 cohort, or the `retired-c2-v1` or `retired-c2-cycle1` copies. The sealed tree had 709 private files including the archive. The live private tree now has 999 files.


## C2 retirement and fresh cohort

The previous C2 generative items C2-01..C2-10 and the C2 benchmark pairs B05..B08 are retired. Their bytes were moved, not edited, to `retired-c2-v1/`. `retired-c2-v1/RETIRED.txt` marks that directory as history. Those items are not the active cohort. The sealed archive above remains the pre-retirement snapshot and is not rebuilt.

The cycle-1 fresh cohort used the same ids and the same signed strata. Those bytes now live in `retired-c2-cycle1/` and are not the active cohort. Generative: convex C2-01..C2-03, connected_holes C2-04..C2-07, notch_tool_access C2-08..C2-10. Benchmark: convex B05 and B08, connected_holes B06, notch_tool_access B07. Counts stay 10 generative items and 4 benchmark pairs. Other families and the four admission controls are unchanged.

Each contour in that cycle-1 cohort was prepared from an independent synthetic transparent RGBA mark by the unmodified production recipe `design/cad-harness-verify-v4/c2-production-recipe.json`. File SHA-256 `ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00`. Bytes 836. `rounding.allowed` is false. Canonical height is 50 mm. Live calls: 0. The 14 fresh bundles were admitted by `cad_verify_v4_artifact_judges.validate_context` and `cad_verify_v4_artifacts.load_bundle`, with `evidence_mode` `independent_dev` and `output_object` null. This file records no contour coordinates.

Retired list:

| Id | Role | Stratum | History directory |
| --- | --- | --- | --- |
| C2-01 | generative | convex | `retired-c2-v1/generative/C2-01` |
| C2-02 | generative | convex | `retired-c2-v1/generative/C2-02` |
| C2-03 | generative | convex | `retired-c2-v1/generative/C2-03` |
| C2-04 | generative | connected_holes | `retired-c2-v1/generative/C2-04` |
| C2-05 | generative | connected_holes | `retired-c2-v1/generative/C2-05` |
| C2-06 | generative | connected_holes | `retired-c2-v1/generative/C2-06` |
| C2-07 | generative | connected_holes | `retired-c2-v1/generative/C2-07` |
| C2-08 | generative | notch_tool_access | `retired-c2-v1/generative/C2-08` |
| C2-09 | generative | notch_tool_access | `retired-c2-v1/generative/C2-09` |
| C2-10 | generative | notch_tool_access | `retired-c2-v1/generative/C2-10` |
| B05 | benchmark_pair | convex | `retired-c2-v1/benchmark/B05` |
| B06 | benchmark_pair | connected_holes | `retired-c2-v1/benchmark/B06` |
| B07 | benchmark_pair | notch_tool_access | `retired-c2-v1/benchmark/B07` |
| B08 | benchmark_pair | convex | `retired-c2-v1/benchmark/B08` |

## C2 cycle 2

The cycle-1 fresh cohort was moved, not edited, from the original ids to `retired-c2-cycle1/`. `retired-c2-cycle1/RETIRED.txt` marks that directory as history. It had been prepared with `design/cad-harness-verify-v4/c2-production-recipe.json`, SHA-256 `ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00`, 836 bytes. It is not the active cohort. `retired-c2-v1/` and the sealed archive are unchanged.

The active cohort uses the same ids and the same signed strata. Generative: convex C2-01..C2-03, connected_holes C2-04..C2-07, notch_tool_access C2-08..C2-10. Benchmark: convex B05 and B08, connected_holes B06, notch_tool_access B07. Counts stay 10 generative items and 4 benchmark pairs. Other families, the four admission controls, and the roster item identities are unchanged.

Each active contour was prepared from an independent synthetic transparent RGBA mark by the unmodified cycle-2 recipe `design/cad-harness-verify-v4/c2-production-recipe-cycle2.json`. File SHA-256 `0b6d09b67c67a050de5247e9c28f95abc454ee33b2c8cef604f5839ea7dc7e04`. Bytes 847. `rounding.allowed` is false. Topology preserves components, holes, and islands. Canonical height is 50 mm. Live calls: 0. The 14 bundles were admitted by `cad_verify_v4_artifact_judges.validate_context` and `cad_verify_v4_artifacts.load_bundle`, with `evidence_mode` `independent_dev` and `output_object` null. No model generation ran. This file records no contour coordinates.

Multi-piece items, from source topology only: C2-03 has 2 components and 0 holes; C2-07 has 2 components and 2 holes; C2-10 has 2 components and 0 holes; B08 has 2 components and 0 holes. Separate pieces stay separate solids in one document. No bridges, backing, or joins were added.

## SHA-256

`sha256  bytes  path` for every file under `families-v1`, including the sealed archive.

```
b8ce04081e6778799da824b4c833cbe7b42876699528a2635bb6d49031f2cc55  327  admission/AC-corrupt-step/manifest.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  admission/AC-corrupt-step/recipe.json
26bc00aab228090c3200c04badb0b00620df848f2fef515cd61dff8a07e85a7c  62  admission/AC-corrupt-step/reference.step
f20db243addccb988d6c8395c3d2d91e88dda0cba6bba08b1f54f6e27f4f94f3  788  admission/AC-open-contour/contour.json
5c5b916af2d0a64e0f758ae95b9bd3e32d40cb1462dbb26bba440729cb0328e0  522  admission/AC-open-contour/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  admission/AC-open-contour/mark.png
226db9a7edb03319f6cf43651d28811b8ff0fab1e84997be45c1e877a025f4bb  1810  admission/AC-open-contour/prepared.json
54ee28ead5e9b3e7935c968a34a622911902377bc880d2f6f3f21f5386d24527  2151  admission/AC-tool-infeasible/contour.json
4037d40ad0f5bef368d531cfeaefc94ef4cf34b8b2809b968a831f4c69f07a03  523  admission/AC-tool-infeasible/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  admission/AC-tool-infeasible/mark.png
3098ee06f7ffd45a69f4dfc58db56a13c4757d34b8b213ed051dfc96223a437b  3457  admission/AC-tool-infeasible/prepared.json
290b2718103b711f442114b71ec6d7b9ffd1a4b5f6ff9849425dc967dd09b31d  6870  admission/AC-unavailable-glyph/baseline.step
449859557fbf9ed2bf6df1d64482cfec0814ff3a4df73a72872dc183ba03f60c  360  admission/AC-unavailable-glyph/card.json
bde1677843a6fb7038f8d55e208b8c47b5e3754a48707a4bc90d2b26433fa76d  717  admission/AC-unavailable-glyph/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  admission/AC-unavailable-glyph/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  admission/AC-unavailable-glyph/font/LICENSE_DEJAVU
76b4e1deb1aeecd5c56bd846b78207548a69abd5dc5653fd88650ebcd20dabc4  819  admission/AC-unavailable-glyph/manifest.json
4e6f05379b856c44a0748cc6da683b22e9b8f504199b2b3d2ea303cf36106d79  5401  admission/AC-unavailable-glyph/prepared.json
af9d6a02a16f1e69f70dc514e8dc1fc5aeaa0894106b420f276b683c9572b3fa  985  admission/results.json
8c4d17c0ae2a152214d601e379cb7d8e3b0dfea239a22a6b7d4a662942554e59  11993  benchmark/B01/bundle-source.step
8a0d7c2fc70031dfd87fa04aea3890085c5508d67e4de6251479d59cd463e977  473  benchmark/B01/bundle.json
bf205903a85e8d2af2721ad3fa548861c718b0192ccbcdc48d8dfbea9bcd13e3  1225  benchmark/B01/card.json
56896c1ff9895308737bceed8e75d35146186e59c3abebceca2f707c673b45ed  530  benchmark/B01/context.json
3d064a3c8faa8a79a6ee562de1a16b808b3c0301917d8aed76dbcd62b2bf075b  330  benchmark/B01/manifest.json
2fe5a21b7bc074da3f607fa1f5e8eba12f21d8974d6db59d79788ff3cd035865  611  benchmark/B01/pair.json
f3c25045a5f6f2f76aee12380c1a9ce3e08930bae3c2eb274a44cd89284f4e1f  8635  benchmark/B01/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B01/recipe.json
8c4d17c0ae2a152214d601e379cb7d8e3b0dfea239a22a6b7d4a662942554e59  11993  benchmark/B01/reference.step
5053836158833d15f253783994e1f4c0becbf19bf0044b9f94a5f3e3005f3f37  153  benchmark/B01/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  benchmark/B01/schema-shell.fcstd
b16668a87321737f5bbdaece5aca87ae12a40017b49d38061ffc6b7453d97162  6904  benchmark/B02/bundle-source.step
dac8c922af840134934038b0871b860aab2add9968f28f9e23e9b428bdc76182  472  benchmark/B02/bundle.json
fda59fe734d9a4092fe44f3c1c9344f0221781cc624184deb9c3f137cdc2abd4  1137  benchmark/B02/card.json
8fb2ed51e09838c07add78cacf8c3906c2d534c2165942ab33fde2f73725a3c0  530  benchmark/B02/context.json
42ab34fe3fdaae6730c775a22383470192c2c5ac0b93107292dec55592db78d9  329  benchmark/B02/manifest.json
b9739ab461e55aa6f30e4100c4a67b56785b9942bd2a095a8110bbaa05bea492  618  benchmark/B02/pair.json
654c8a66005294e972811da245ff5c382b92fd4ed0f6028aebb046fab95ca1db  6743  benchmark/B02/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B02/recipe.json
b16668a87321737f5bbdaece5aca87ae12a40017b49d38061ffc6b7453d97162  6904  benchmark/B02/reference.step
57c760adde30d6bf8c2dbccbac3c71922625b714b2ba9fe6a680bdb15579400e  156  benchmark/B02/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  benchmark/B02/schema-shell.fcstd
79126b5ac5acad46d0166734c430560d9ac8272cf4f434ed432a7e494ba00d77  15238  benchmark/B03/bundle-source.step
868357cb351b8c5bdb8915bd65192649a4893ee76348433437605733a6f865e8  473  benchmark/B03/bundle.json
0dd934a71468b7f2b9259673936880581f20d3e4e3afb859aed487e9f1e0ee5e  1244  benchmark/B03/card.json
d2cf80d0b3dd652ab6d6ea191bea3a94ab39c5142aa4c51c6f807c52c61d8c70  530  benchmark/B03/context.json
009b7a224a6834e95d0c303705521f1df7952b20696c8b8f382799eee0f44fcb  330  benchmark/B03/manifest.json
a26579b5c3d27f1cda2f71f5746f890c01c6035a60314f7e11dceb18502282ee  618  benchmark/B03/pair.json
e4bbeca7c40f39d9f67a042e30cdb554187e9c03b2811e860a3b18c1cffb3854  11329  benchmark/B03/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B03/recipe.json
79126b5ac5acad46d0166734c430560d9ac8272cf4f434ed432a7e494ba00d77  15238  benchmark/B03/reference.step
c488db54630c12e67f8a1f47cb3b61290d726ffe3c1d9aac4598c3d0eae62b34  162  benchmark/B03/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  benchmark/B03/schema-shell.fcstd
e2415f95ea9dece4de9ceef06518eb5cd660009ecf5a018f27f735dea746b6bd  6906  benchmark/B04/bundle-source.step
fd489174d22db76dae44c3548407bafe48880fa134a8d8a83224f3d87222a2d5  472  benchmark/B04/bundle.json
acbcac33ce9ff771bf5a9659f86c4e105a6471a6ca34bdfb165ba8dc9b5f51da  1198  benchmark/B04/card.json
59563eb91283bd6e441d0c461dbb3df2f48d51beedf28473f984be48bd5d7624  530  benchmark/B04/context.json
6019dd4210754654a9fc8a77595f24fba5eed67531a7e47e0ea5d61e1b4e91f1  329  benchmark/B04/manifest.json
4b64e9413abcf98010d9818ab76d8f0e677d39980b31aa327ad7d448cd2c71b5  611  benchmark/B04/pair.json
f65ec8d226be2474c62893a7e79660fec21f38db4bb3d1900cd06c15159ee2fc  5386  benchmark/B04/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B04/recipe.json
e2415f95ea9dece4de9ceef06518eb5cd660009ecf5a018f27f735dea746b6bd  6906  benchmark/B04/reference.step
cb641113b3d561d05753ae70003dce35f019c7d561784af3345c82a5b3b3ad4e  154  benchmark/B04/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  benchmark/B04/schema-shell.fcstd
9bd76e068a7c82b0deb80cc9ff697d402e15929ba608173ed3c69b0321daa2e2  289  benchmark/B05/bundle-carrier.step
9bd76e068a7c82b0deb80cc9ff697d402e15929ba608173ed3c69b0321daa2e2  289  benchmark/B05/bundle-source.step
9470134c6a7305c7d3d767a480b2a77d7e94b5e90bb2a7bb29e879184ba90860  471  benchmark/B05/bundle.json
c12f25ad83e6c921188b49a5135c1d35b251b80c4e73f1944f652211172f602f  1234  benchmark/B05/card.json
4e316b313f8bdab12902c1af59db29e10d65cce104834767ec1842a61deb9139  531  benchmark/B05/context.json
c6c2ecc39ddd4e33ae5784b155c4c06596cf22cca5ce6121d55b6bd37a20e53a  317  benchmark/B05/manifest.json
e71e8b6106a49d03eff75132f9f8d8fb1f722c61485d3aa758fa825b804cbf58  1747  benchmark/B05/mark.png
0e516d2a22452c60b662714b69185c22760d5f006ab623e39a88ebbdd18fa937  608  benchmark/B05/pair.json
f1f2cb914ce5b201d4b0b2f4a2235f800cff0a10f078744f35fcdf3c792618fb  157654  benchmark/B05/prepared.json
bcc4ff3fb1868902e1fc8836b76c1c2a85c165c448ad5bcd73032905c132c684  353  benchmark/B05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  benchmark/B05/schema-shell.fcstd
657c8c5e5cee8ae522a00fe2635958f6b1237a19b21ae4dc91bf0b442ce71a8c  289  benchmark/B06/bundle-carrier.step
657c8c5e5cee8ae522a00fe2635958f6b1237a19b21ae4dc91bf0b442ce71a8c  289  benchmark/B06/bundle-source.step
8920d531800f44d9c55a9a00053f4c0f7b1a1e3a6f654545876922a5d2016d77  471  benchmark/B06/bundle.json
e992103d9d2c3573e90bec72279ebde31fcd01c550473e2e6d09ae5597a680e5  1234  benchmark/B06/card.json
32553571206063f48a9a619b0a0d6ac2cf20678c5a1fe8eab310c613a8147b7a  531  benchmark/B06/context.json
aa3b725b51982c93bd8b44b4b2170ccd6dbd0156a5da4b2f17abc44ba8588040  317  benchmark/B06/manifest.json
ee46dd10a40a927bfd18b1ae69158fdfd2c4dd4422b36ab0d7f269cf54c68374  2422  benchmark/B06/mark.png
50803d92b8df1550a225334cf785eb41421b28b574a17b6a0de4d5e4653fa829  617  benchmark/B06/pair.json
74f9ba41a04f02f5f98c986d7544dba3c04a65c39a58b259eef212de0519df09  266628  benchmark/B06/prepared.json
f2174e7326b87607c47686bee135b322a43b256dbd4aeca8e3dbc73fe14b5e26  369  benchmark/B06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  benchmark/B06/schema-shell.fcstd
d03adc207d4458c77b3187c0f38110ac83b819d6bd8124af1103718507313c0d  289  benchmark/B07/bundle-carrier.step
d03adc207d4458c77b3187c0f38110ac83b819d6bd8124af1103718507313c0d  289  benchmark/B07/bundle-source.step
016097964bde5485986c18c199066640c14c2e1b58f1ceaab4f3bbb35a2ae395  471  benchmark/B07/bundle.json
f62c6e8822460b29a9bb33753241464086d4cb83ac4b1f7fd0d503968d6d159e  1236  benchmark/B07/card.json
aa6b3b7788f22a76045e2c27bce767fc2cd58ef9f3f4273f565f2344b58e66f5  531  benchmark/B07/context.json
5b8b7897edbfeb3e53ca0217d826809c06a04f161f91925c633f3e5f442a86e2  317  benchmark/B07/manifest.json
c119d484e64622d5d23a81fb64639c9e0e0f10bfc200fdd0c9c9ef366fbba7cc  2117  benchmark/B07/mark.png
e4bdc9a81f93362762a443434f817ea57e620347585f87c6747421ebb1318db8  619  benchmark/B07/pair.json
bcf5ca289007c425da31a60fac73f22971bb8fdd1523557e70a09ddc495ca359  222134  benchmark/B07/prepared.json
0896e100afef93e394454f300720fcbe8569dae6ad55b73661fb759e566d0475  374  benchmark/B07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  benchmark/B07/schema-shell.fcstd
1ec93a50656715316956f676d818c678453915eb1a310077807a0cf71087152d  289  benchmark/B08/bundle-carrier.step
1ec93a50656715316956f676d818c678453915eb1a310077807a0cf71087152d  289  benchmark/B08/bundle-source.step
7c64d4a4009ca5fc9983aee7c80831bc8726527062e339148c35ffe8119d2c02  471  benchmark/B08/bundle.json
3692c365297e2cd6127bbb5cb8ec3281c5f626a744696c0890539b25450012f5  1234  benchmark/B08/card.json
7ace664614f4725eb195279145e5cc8853891cc35b39fca1f364db6c7f1a6690  531  benchmark/B08/context.json
456e31d25ce0f65083bd329941417e4b2a31f32e6f409509e5e0064c72095234  317  benchmark/B08/manifest.json
413a3cd753e8e6fa95a642a7d9e60f62c9d1765a8a0df6109100cae951209ae1  2001  benchmark/B08/mark.png
ec7768ea03b3f3e78098fc36de84368c76701dd33bb1e7297548eac5f250c5bc  608  benchmark/B08/pair.json
69c4ebce272be6613d4cee464bd6b668dd43c915fa54c7f2d3f560477d1e74eb  235573  benchmark/B08/prepared.json
68f8fa9834e2d3766ea74ad904e7091db3695d65e43c8eba5a292bb780a79470  353  benchmark/B08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  benchmark/B08/schema-shell.fcstd
2311d753682b24d15a9f665c44a297d4bbfc82c7ca812124206a4affea80dc73  6868  benchmark/B09/baseline.step
2311d753682b24d15a9f665c44a297d4bbfc82c7ca812124206a4affea80dc73  6868  benchmark/B09/bundle-source.step
48def130bbc43e4441435a543968dda792775e6ed37177e866ae93b9009036b2  472  benchmark/B09/bundle.json
c19c6d6a7ea03b9b38ef6e70428c1960f5b8369bb140f5bbe3dd56ed31bf55bf  949  benchmark/B09/card.json
0e536e5a8acf3ff86fdadaed72153d633986ed804bb13b7a33c88fa11723150a  719  benchmark/B09/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  benchmark/B09/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  benchmark/B09/font/LICENSE_DEJAVU
a215a523fb4eb7967242b988f3fd46734e5a56c3aff05f7090b107b3e679daf4  813  benchmark/B09/manifest.json
847fb47b97f4a874eac62944d614de56f4df750c8216e5b997865e5aa000aa82  609  benchmark/B09/pair.json
8ec75f7b9f6415c563901aed5c88d5191a750f806f4f97e3b4613b1237216b33  5413  benchmark/B09/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B09/recipe.json
c50e5e095d19b923cc338e36ae4b1df5bfb23d7b1dd664452323641a5402f3c3  298  benchmark/B09/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B09/schema-shell.fcstd
a576c0ec33e88ea6be6752c42f5e8065e93cc5c1a066d29a1ee1131c1e7bc619  6870  benchmark/B10/baseline.step
a576c0ec33e88ea6be6752c42f5e8065e93cc5c1a066d29a1ee1131c1e7bc619  6870  benchmark/B10/bundle-source.step
7af6cb1b8d926ece6b81659c466f9d2120a1bb3ad539599e6a190ce792e437e2  472  benchmark/B10/bundle.json
47c827a3347007b1432141cf7bae49274f15a298b2290ed53ff2c862d7b68992  949  benchmark/B10/card.json
aff3a24289d78f4a853e963390698658f60fb41f0cba05dd8eddd07e0c65864c  719  benchmark/B10/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  benchmark/B10/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  benchmark/B10/font/LICENSE_DEJAVU
7a5ccceae970e1273bad07deb512228e3c5b07c3a9965372bcdc93dd5991eac4  813  benchmark/B10/manifest.json
80676f7274acea254c1bb8678aa7bff5ffb99bfb33e67e043991722a45a39f2a  614  benchmark/B10/pair.json
f394d8f8893651bcc0e7c2606f9a4831f59b17ac4c0eb13c26300db31706a97e  5435  benchmark/B10/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B10/recipe.json
7bd8be63949c91806ae4999e9457113c1c2fc1d2dcbb878595d5e3fa5fdb7459  303  benchmark/B10/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B10/schema-shell.fcstd
1243209646816d602eb7b48c9ed3fba1990828cba8eda58f615a447e0d5d467e  6870  benchmark/B11/baseline.step
1243209646816d602eb7b48c9ed3fba1990828cba8eda58f615a447e0d5d467e  6870  benchmark/B11/bundle-source.step
7fd820d68cec72bff10c6136a0277d2b6a604e1a4068b4aff738351b124cf467  472  benchmark/B11/bundle.json
a784ed0b49def61bf27c719fa8078e3b6ad0806173781a18cb7d25007e8ea7bb  949  benchmark/B11/card.json
eda82eb9687cbf9164e9beb30239b63c1d2b71413bad4d6241bd425dbe9499e5  723  benchmark/B11/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  benchmark/B11/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  benchmark/B11/font/LICENSE_DEJAVU
c07cb49aae666ceabf4d6e1f605495c7bb17e11999c2ba6a46b91315bb4add22  817  benchmark/B11/manifest.json
937ae98ed30217e73a1eae57e6c015356f7ce25a2ac444bfd6f98c1c701167ed  607  benchmark/B11/pair.json
13210a9dd7b02bd3578ae787d66d9be96e8d67c7e2c5c2bb96d5b41b6a2abed3  5413  benchmark/B11/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B11/recipe.json
44bd0d6e2beb51eea8d808e0e6e556adfeb90d584b96b9f04dc64fc46f4ea6a7  300  benchmark/B11/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B11/schema-shell.fcstd
3d4dcca5c11634cbb813d3937d2a38217255d196b224f5c92e240d7d196b1cab  6870  benchmark/B12/baseline.step
3d4dcca5c11634cbb813d3937d2a38217255d196b224f5c92e240d7d196b1cab  6870  benchmark/B12/bundle-source.step
4e673d793638028de436a854710db4d4cb33fa2276ed8f4be5de3853c7e572fd  472  benchmark/B12/bundle.json
4d790c133c38794bf260ec477272bddfa7836619af4861b9a7f94b50d87056ba  949  benchmark/B12/card.json
5db3bb77fd4a1ee3bbffaa2907aa3b58d0ffd7e875b8eb2fb85b544dea0662c6  719  benchmark/B12/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  benchmark/B12/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  benchmark/B12/font/LICENSE_DEJAVU
4bbc38ec964e45223c507497686daee1a915dcd654c1a2811e90ff449ac2f743  813  benchmark/B12/manifest.json
1c17cd8c4cbfa1ac097a125457bd5eb989889dc6a8678c68a35e460ca6748341  609  benchmark/B12/pair.json
f3a18ece80ad5e4ba3905a1faf9c54f7fbc88a8df0586fa6296cbab63f9b7f44  5401  benchmark/B12/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  benchmark/B12/recipe.json
68ef456d0dcf0f5227d6a51c97d35509f2c160043808dc010559b3259a7f81d6  298  benchmark/B12/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B12/schema-shell.fcstd
e4b2112523798ae1426e260fb90ddbc2e48ebf4e2eaea0c54f5d3d1706dadfab  6870  benchmark/B13/bundle-source.step
d32f8f8e8c884825fb76b1bafb9d4cbc05d40f8c0e7aef87b4e43b4813297203  472  benchmark/B13/bundle.json
c14ddad3f97427fbfc9281478cd54fadaf198ae918ab4b9c9ae2a208def353b1  1634  benchmark/B13/card.json
de04701a64e1f1a7eed23cfdcc4b4a868c403be7dcbf6419f3202698d856f150  530  benchmark/B13/context.json
49d292ac1ee2e24d9cf17c005405a64cee67fbf2db4fd55ced82fd67b472ea69  329  benchmark/B13/manifest.json
b33f80d3ff4b07686325a8485827c3709266ff0fb974de009b8225b2e642327f  616  benchmark/B13/pair.json
99897ab21e87301104f38b55e0c8f0581a316eb113e3372cd1300ff779dac901  6272  benchmark/B13/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  benchmark/B13/recipe.json
e4b2112523798ae1426e260fb90ddbc2e48ebf4e2eaea0c54f5d3d1706dadfab  6870  benchmark/B13/reference.step
58b7ac3efbfb5c943b607de947a310a61b5b275cb53eea9dd69c0e723116c89b  88  benchmark/B13/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B13/schema-shell.fcstd
c2b469a1cc137a2cb569fb28d0470c3f3e20f6168ebae406e9c034ee71efa231  4964  benchmark/B14/bundle-source.step
a2cdf3fc321fe13e1d0bc3bed09075171d5150fc121b5c48226ca4e96de80e1e  472  benchmark/B14/bundle.json
065a2c94c0cca70a009f0dd9c5c2e6348acf35c9230fe03713395409d6c26401  1432  benchmark/B14/card.json
245a684b53249dfe3059aab1347ff977c824916b745e0ec66327aadf8283ccb6  530  benchmark/B14/context.json
ab21eef88f7f234b9515826576ecc5254f5712248dd7e904bcb8b132fb89d68e  329  benchmark/B14/manifest.json
f31d4394a0b563d028aa329bd03fce6e456d2fe83e09de119dc829625925dd0a  616  benchmark/B14/pair.json
fac25ded8d9c135f9628450d83fccadeed139514ebf25264ed374a19f108bb4b  4990  benchmark/B14/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  benchmark/B14/recipe.json
c2b469a1cc137a2cb569fb28d0470c3f3e20f6168ebae406e9c034ee71efa231  4964  benchmark/B14/reference.step
f59dc02b35daca141604be984f65a7445fffc3778cb99c3bc50bb2a93092e11a  115  benchmark/B14/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B14/schema-shell.fcstd
a1a3ed52d69e3559358a27bfd94dbc07233d7163c06e057500ae20d08dcd8050  6870  benchmark/B15/bundle-source.step
cc51419112c5b7889f63133cf37253546892190170f7340b3ef3e254c9c234ad  472  benchmark/B15/bundle.json
1a838809f38eddd4e2f49900992af2f0eeadc4f3666e0d2543bbc773efb05329  845  benchmark/B15/card.json
d9d79e595ee0f3914734f5e805d929572dbfc4efe5fa6ad97a00040b4ca3bb51  530  benchmark/B15/context.json
3596fc88192421467da50dd90e876387eeccb9f68158ef8fbcf8680fe782bc19  329  benchmark/B15/manifest.json
9bb07fe1d59cf3743818e04215f518e9dcad0f4f5c8013d3550bfe7eac9de877  627  benchmark/B15/pair.json
5b9087ff29cf39b6fba6aed15fc2b6e9d87fc2f94db7fe72bbec67a69bd24dc1  6212  benchmark/B15/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  benchmark/B15/recipe.json
a1a3ed52d69e3559358a27bfd94dbc07233d7163c06e057500ae20d08dcd8050  6870  benchmark/B15/reference.step
3896dea02858c300ded5834aae899043328e0b602b5534e727f0d979f2214d91  106  benchmark/B15/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B15/schema-shell.fcstd
049cada40e196a42c67b1ab6c8a20daf1ceed263fd6f3fa235b9a300a741014d  12044  benchmark/B16/bundle-source.step
106f68a07cf71a8ff34227e26afac3168e01b221057d56272f0a8b9d117848da  473  benchmark/B16/bundle.json
f2614a246429c03f2dfdb24a3e8d6b51fc24a5200c40ed7d501eb006901d33cd  662  benchmark/B16/card.json
b8353892714e981eb4b42879a5564f13cab4db0cf6719e776b31433801aa9cbb  530  benchmark/B16/context.json
bce622c24dffc9af6ffdf127c06c179cc17fc1470db9fb0113dc27ac484abc96  330  benchmark/B16/manifest.json
bdd591ac0e880323bc98af0ae293935105742d6ef3ca6196f7aae26e770302f2  614  benchmark/B16/pair.json
4adec95fbe2d3e609657b47fba3aae1dcfb2c539a273f3e1450b0a699ca333a3  10195  benchmark/B16/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  benchmark/B16/recipe.json
049cada40e196a42c67b1ab6c8a20daf1ceed263fd6f3fa235b9a300a741014d  12044  benchmark/B16/reference.step
41923ab40f27f1645b242d2129e74c4f3b068206e918bf0f0ac1023d1cf75f0c  99  benchmark/B16/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B16/schema-shell.fcstd
3a1093fc579da0d8bcc696ee4dda549324e818e3a52f6b27cef39327acda5456  5725  benchmark/B17/bundle-source.step
4a5bab142206b8c18f946fc6cb493353078dca171164ba9932fa1fce712788e4  472  benchmark/B17/bundle.json
89eb0ad1eb35852b0dd0a550b9a734bc053210c5c18a5c992ae8c67e5c61f105  3360  benchmark/B17/card.json
27f84276e2aca7d96cf726f670348f5ca5a999346ba3d9f6ac35f9c114791df0  1156  benchmark/B17/context.json
6db36d4ba94f2b9afc4fceab9e44651c06ebd59a3e32ed64e3f5398e6671fe97  329  benchmark/B17/manifest.json
27d74aa04e2913618ca935b55a56f7bd525edd01f27e8551534be6d6c7d184f3  611  benchmark/B17/pair.json
7390d276170726f1621a03ba443360d64f79583c2bb727acda662c79e26a30ec  5001  benchmark/B17/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  benchmark/B17/recipe.json
3a1093fc579da0d8bcc696ee4dda549324e818e3a52f6b27cef39327acda5456  5725  benchmark/B17/reference.step
46df5e8b291b90d9bc806251bb69f7719eca79f42786305bc1fcbabad8276ed7  114  benchmark/B17/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B17/schema-shell.fcstd
a5d8ef1dd6483247c7f2bad53a4737995cde66d873432a4b6ad97fe13bc7481b  5709  benchmark/B18/bundle-source.step
dbb9820f131b632682a668fc2238e4f11c1c7c4a50659bf8581512deb8dab9ee  472  benchmark/B18/bundle.json
d738f23785515fd2ce37960ed0b6e1fd4b740c4590fc66a0e5bc6317f9b87469  3372  benchmark/B18/card.json
fcd1d80d1c38f484b0d46878b476a16892e0e3ca85be41e3c8b50c4884ed28f0  1156  benchmark/B18/context.json
6444a01522a3facf3e2eec4629cb6149dec9c061ef5f29ecdf4de95843bbef1d  329  benchmark/B18/manifest.json
b5c90882eb6eda65bfaa739db6290c6ec3390718f713adac3c2fd9c3d5ce70c1  611  benchmark/B18/pair.json
50318066d68d6dd843e548f7e0f3f6a18d98db18b35d1fa509706f6ed1f4a92b  5004  benchmark/B18/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  benchmark/B18/recipe.json
a5d8ef1dd6483247c7f2bad53a4737995cde66d873432a4b6ad97fe13bc7481b  5709  benchmark/B18/reference.step
3a8a3d16e842bce3e977f8b00545f43ca057333ab2b150713d268291e6599f15  114  benchmark/B18/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B18/schema-shell.fcstd
91dbf67f228158ac119e6ac46603d775a0c0f75833cbcf95e0ae841bbd57424b  9076  benchmark/B19/bundle-source.step
6f32a01c1d1fe400941496025bb47658da0254d0a942f6dd1b3f33b21a641612  472  benchmark/B19/bundle.json
476d2422c2e67fe04025598326540eb5af3b94dedba02ba650b790533d6d7602  6783  benchmark/B19/card.json
e6da8e74181ba99ab45554512f3833ae07cfa33fe42414e24d818e310fc6b040  1846  benchmark/B19/context.json
0a79dd0dff33bb10f3391eca89a4e5fd0d645bca15a1ff25970fff1d9b68687f  329  benchmark/B19/manifest.json
f20810ae0f5da21b5ed400f0a879815fc4110c9b441bc89ddd3a27e0b8602cb6  621  benchmark/B19/pair.json
cadfad526cc816b71a93add0e2aa98fdb08d7f9df911969c63eb968967cf02f2  8521  benchmark/B19/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  benchmark/B19/recipe.json
91dbf67f228158ac119e6ac46603d775a0c0f75833cbcf95e0ae841bbd57424b  9076  benchmark/B19/reference.step
03f75e791089f1fdf11c8855e0e7d94d2e0b871d6aec8c6ff5faeb7f215e633d  129  benchmark/B19/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B19/schema-shell.fcstd
fc97f58f2dc3e434c219ef33a607b2a0d378b52ad35fff121b178e565fa03e75  9076  benchmark/B20/bundle-source.step
826ecd197b6608ad7ea02a0095c3534803457ae57c208f959a3e497af223ad02  472  benchmark/B20/bundle.json
75871790e4b43c995ead0182751243ece740196754235977b66a0cedb88fa8f7  6425  benchmark/B20/card.json
43c824b16798b21409132e0e1fc79779974b6cc07aceeb57919a9ec4cc12e026  1846  benchmark/B20/context.json
058000064f304b99c9ce8212c0465c43aa80665e4304c48792b2f8a735764b1e  329  benchmark/B20/manifest.json
9c8a53a56ed807109c228ce8453f1ab7f7b342a448ad54c7e35f7a86517d051b  621  benchmark/B20/pair.json
8a9f4dc11cf9039438d1f265283a1f1555da4737adae43a73f733926dbd0c612  8589  benchmark/B20/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  benchmark/B20/recipe.json
fc97f58f2dc3e434c219ef33a607b2a0d378b52ad35fff121b178e565fa03e75  9076  benchmark/B20/reference.step
307c124669e82934fc6fb71e87192be8054f59a268af0248122422249086da37  129  benchmark/B20/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  benchmark/B20/schema-shell.fcstd
588db92fa91cc276ff5d3dc13a7fdf16fa49395d6e420e6a81e0d56396c21dcf  3206379  families-v1.sealed.zip
bdb3fc904c01b54cd2f702e151ea20993b7501d10414ed7f2b090da008c0c5d8  6859  generative/C1-01/bundle-source.step
2ea742200e5407fcafcee33a0144c43054e0a8f6d7539e0906da67c9430ca3d3  472  generative/C1-01/bundle.json
8a5773f9c3e21f8c7bc64aaa826121507dc829b6e842a42c1298d4404b7551aa  1156  generative/C1-01/card.json
c33cf38ac142dea414218f615569bcb6c388716451490b2295a705f265e480c0  530  generative/C1-01/context.json
9ae2a7d0335ac6d1b11975162a33ceba5cdecb241031e9319598ebd3d903f900  329  generative/C1-01/manifest.json
719ec39db2f1954628bbe94fadb9feab6b58dcb876f3c84100592bc3b59362d4  5351  generative/C1-01/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-01/recipe.json
bdb3fc904c01b54cd2f702e151ea20993b7501d10414ed7f2b090da008c0c5d8  6859  generative/C1-01/reference.step
23b265a0936cff3969ac280b39eb74358a5e35a9788aa53c8a64ecf76cc0b8e7  314  generative/C1-01/request.txt
3bb095845b32b6b7c98c1bbe3f60b9016fb6c689fbedd3f19591faac43fb5799  190  generative/C1-01/schema-shell.fcstd
443404d85c6a9d5098033adb065754790411269157e0d118e1d773a54fe54a16  6868  generative/C1-02/bundle-source.step
0a005cfc0cb994a074cbc3c43a62904a14a95032c3ec41aee8f3c2238cdcecf3  472  generative/C1-02/bundle.json
183c9f96b91b731d01c495d97b79dc9bda6dfea6d4ddda568c8100a34bc02d38  1155  generative/C1-02/card.json
0b74645dfd8a589ad7c25242a574715c0c84441d3c6ad70bd906b7612f7dbb98  530  generative/C1-02/context.json
3616c4903bd25e14ece2d39d992e68abb041c64598774b30220bbaff2e803094  329  generative/C1-02/manifest.json
f7fc0ebba7881324317ee23275a209c54b5be48321d21d8fee5d415d95d5a18d  5371  generative/C1-02/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-02/recipe.json
443404d85c6a9d5098033adb065754790411269157e0d118e1d773a54fe54a16  6868  generative/C1-02/reference.step
23b265a0936cff3969ac280b39eb74358a5e35a9788aa53c8a64ecf76cc0b8e7  314  generative/C1-02/request.txt
3bb095845b32b6b7c98c1bbe3f60b9016fb6c689fbedd3f19591faac43fb5799  190  generative/C1-02/schema-shell.fcstd
cddf00a725e39d96f06b3257202ed6f2850954a683a0599e1d32c081d4a3106b  6868  generative/C1-03/bundle-source.step
b7c245e303331466372a3fa07d561ad54911ab0fc6858fa7ea40f7e3cc8debb8  472  generative/C1-03/bundle.json
ed40dd16fd54fc1da0d04a67e96c1d15a0764ca00055e0ad3117c8ff963f8836  1140  generative/C1-03/card.json
af86937bd0bfc3b6f7bc5192dc606a8577b5d04f7e75405b2272aa6cf93be0b4  530  generative/C1-03/context.json
79d7c0f625a414835a63277d99c0c3eb0df2bb81a313f13414dab52ce665230e  329  generative/C1-03/manifest.json
81d96c3f12609aba5be6b6b70840b1215defccd2aebb83923c7274268a3b633a  5431  generative/C1-03/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-03/recipe.json
cddf00a725e39d96f06b3257202ed6f2850954a683a0599e1d32c081d4a3106b  6868  generative/C1-03/reference.step
23b265a0936cff3969ac280b39eb74358a5e35a9788aa53c8a64ecf76cc0b8e7  314  generative/C1-03/request.txt
3bb095845b32b6b7c98c1bbe3f60b9016fb6c689fbedd3f19591faac43fb5799  190  generative/C1-03/schema-shell.fcstd
1e5857cabc3d356cf1da7bd98672e25f91985c3e400387fda008d9ccec47e777  6868  generative/C1-04/bundle-source.step
df97fbc588587c7ffbc2c857646b1b33c44577235977cfbde9aaefaf8e43d44f  472  generative/C1-04/bundle.json
1a4d55d22a07fceed87b83980a85e217ee3677ad6b40978c4dd696ae47516e1d  1155  generative/C1-04/card.json
ee33a711488bd9dce94a8e6130febd9b825834b49e9efd849e5541fc62a2dea3  530  generative/C1-04/context.json
2cb2b8979419a05dfa19372b1ef75b2e849d362d4ac3b6b977e4de13f20ee48e  329  generative/C1-04/manifest.json
65efc811bf9dd75f5062a5bcf5482f66e5a39ceb5e935fec68f3f7a1eef78bb0  5411  generative/C1-04/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-04/recipe.json
1e5857cabc3d356cf1da7bd98672e25f91985c3e400387fda008d9ccec47e777  6868  generative/C1-04/reference.step
23b265a0936cff3969ac280b39eb74358a5e35a9788aa53c8a64ecf76cc0b8e7  314  generative/C1-04/request.txt
3bb095845b32b6b7c98c1bbe3f60b9016fb6c689fbedd3f19591faac43fb5799  190  generative/C1-04/schema-shell.fcstd
3327851a37c8779e43d8af42746b72abc598f5410624ee8153cab41a5772495f  12731  generative/C1-05/bundle-source.step
2180f6e9b164ce7f8edc6ec54a598d2741dd7038dfe640fb64c1cf62861be7b4  473  generative/C1-05/bundle.json
ab8dfaad05de532bacabcf6308f6052ed120ddaf089635544bb56ea2f43eaa25  1213  generative/C1-05/card.json
274820b8c0d317ea05256c557c62dffa877e45677abd1d5f3fdd400833efe2cf  530  generative/C1-05/context.json
44103352a9fe3bcc6a90d1109c482d92fa2e7916621ef5ab417b72277b1a59dd  330  generative/C1-05/manifest.json
5363c63acc0a87e2e46b77969dc139299c2f40a17ad1c6f52ce53800e403ad09  9159  generative/C1-05/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-05/recipe.json
3327851a37c8779e43d8af42746b72abc598f5410624ee8153cab41a5772495f  12731  generative/C1-05/reference.step
c02932edbfa108754312f12c745c8b9dd97d0b28e367539d5c9314cc704e556a  321  generative/C1-05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C1-05/schema-shell.fcstd
7e134118c355b13754eee3799820395dd5ac386abbd9376daaed192320d19b76  6894  generative/C1-06/bundle-source.step
1bcd95228dd20196143b948b08152b29ff51150d45ac9c8d66d5d3243cca33b8  472  generative/C1-06/bundle.json
ea10a0b7fb03618915feec2ba36bf383bfed9f1047939a3344d4674f4e7dc180  1124  generative/C1-06/card.json
5dec68e8668cada29538077f9284639b9a0b659425847579c26252af94d45479  530  generative/C1-06/context.json
b67e36d73cf83a0d032aec4a24e877b703f28130056c6d49dabed8f3a3d2e134  329  generative/C1-06/manifest.json
dc649d6a69696be1a011135c938aba766adcc664fd2917b34f21bde66bb29f7a  6761  generative/C1-06/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-06/recipe.json
7e134118c355b13754eee3799820395dd5ac386abbd9376daaed192320d19b76  6894  generative/C1-06/reference.step
9289791c4e0bd774efc5046535e413b2636e43107b63d2ace1d803cf43b57119  324  generative/C1-06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C1-06/schema-shell.fcstd
34f43fd03cd6dde6618d3706128e417f1254fee66a07807b9d00d96ace6d5144  7572  generative/C1-07/bundle-source.step
558cf6bfe5e03737f2b10bba349496af285c7282af5457b7e141222cbc627f09  472  generative/C1-07/bundle.json
1b5ac18f0e159555d32a4bfa556e5ecb01a4f8d60f6a8f4c3bccd30c9e7fb7bb  1221  generative/C1-07/card.json
93b96b59d0e959807b6c6137ada279cf1bb81b0f4af24f3ac2ea93d871b88b2d  530  generative/C1-07/context.json
5bdc30b938efe3374b894347089e2041846e832a61025d63d988e45381c057f8  329  generative/C1-07/manifest.json
5ee5fe572c7916dce78288cf1037e110f271caaedb4ee78eeeb1238a64545358  7187  generative/C1-07/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-07/recipe.json
34f43fd03cd6dde6618d3706128e417f1254fee66a07807b9d00d96ace6d5144  7572  generative/C1-07/reference.step
6d4a1865b04244c244d86b405b2e1afbddce5f18bb2ba6dae91d3cc93853392b  333  generative/C1-07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C1-07/schema-shell.fcstd
1a309e9a7aebd5887a47bc1baec02c92f25736ddeead245244292722ca98d1fa  8310  generative/C1-08/bundle-source.step
10dc7175f5d4a94ac08e8d698cefd9c95d72816653afecdcb260522d35032e69  472  generative/C1-08/bundle.json
9393fcaac428980da7564af4948bdcbb26bead45b0a182a379ba50862147ff90  1172  generative/C1-08/card.json
5b0486ce263b1ff351ef2b236fe0badb246017ee9d24115f9888d14341d90db2  530  generative/C1-08/context.json
442cfde7b807c4463beb79b44a527169a4dc698a9583c777215e0f037156b991  329  generative/C1-08/manifest.json
34e09de853467f7f3b11449142ff5f581b635acd8984999690a31b1ba5f617ff  6239  generative/C1-08/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-08/recipe.json
1a309e9a7aebd5887a47bc1baec02c92f25736ddeead245244292722ca98d1fa  8310  generative/C1-08/reference.step
698245a8643077400b5960276abf7194269257faf168562e69e6d64522d84c83  338  generative/C1-08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C1-08/schema-shell.fcstd
2e4bda7ac2f7312363506e212c1ec71e518e72199e8680101b6eabb8d46bdcbc  13795  generative/C1-09/bundle-source.step
7824c95551df18fc1c134572ef04a290c845c4c5e6e99e3234b33aec9a6d3a28  473  generative/C1-09/bundle.json
dca75a88dea8f5d06d21f6b1176fb271ae1f374492c5fb848f261f9417242204  1227  generative/C1-09/card.json
09381e24d325222052460da33d1feedc30a3b0096d2004a5faca846a8d6e0180  530  generative/C1-09/context.json
e0d10c637cdc3f76baa7f1eabb654654616a1bea27db6d47aca45adb015bcd75  330  generative/C1-09/manifest.json
29d9b11866f77fd43223d289866adcdcfb3d6c03c12b211ed73319ec32de8532  10513  generative/C1-09/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-09/recipe.json
2e4bda7ac2f7312363506e212c1ec71e518e72199e8680101b6eabb8d46bdcbc  13795  generative/C1-09/reference.step
7761dfbe2b55fb23f2a06d1062838fdf5eaf8737f165c434f0c2eede57e275ed  331  generative/C1-09/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C1-09/schema-shell.fcstd
11569a76fef6d80bb2ab7542e1fb89fa73bc74c64918a6e94124e45e9a954dc6  9758  generative/C1-10/bundle-source.step
2450609591404489ba1f3654333e5d1af2ebaa2e94ace94e8fe1155d63941847  472  generative/C1-10/bundle.json
019557202fffd41ff84d10268258bdf4c19f1ffab99de271b96bedf4633dfead  1177  generative/C1-10/card.json
683a0c642fc4d6c2ada6ee81eebf770815e5e960ed8e3418419bf62eb8fe6b43  530  generative/C1-10/context.json
a8acae1aea5183260796831c36f201159a376076657ea2f9a9f23b95305085fc  329  generative/C1-10/manifest.json
b4b8cd94db46dce9577acae46ca09347a38ceb50cb90f8856e91c8a823be4d1c  7023  generative/C1-10/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C1-10/recipe.json
11569a76fef6d80bb2ab7542e1fb89fa73bc74c64918a6e94124e45e9a954dc6  9758  generative/C1-10/reference.step
b50e2c54d2883de6785beedc765a908fb9b6a3729bcbafd0b8d52da93135b8ca  334  generative/C1-10/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C1-10/schema-shell.fcstd
9d594e9a1412046b8f899e6648ffe67e1046db04de24c909e6493a8bf427d338  293  generative/C2-01/bundle-carrier.step
9d594e9a1412046b8f899e6648ffe67e1046db04de24c909e6493a8bf427d338  293  generative/C2-01/bundle-source.step
512a76a6e86dfa1bee5f5ddac0481a4cd57847141382a7e284dbbc40cbe63e24  471  generative/C2-01/bundle.json
c16103b811b77dd6f5ff0bf0f3616f89e26861331b2a6130fad36074a56a0782  1232  generative/C2-01/card.json
db7df15208d2f89dddd5d2fc46d2b0d519967a72245c292424797795c3c4f1f0  531  generative/C2-01/context.json
cd89b5d2b20904c35e6bfac2b79332ab46d8ca867ef61d14b7dce062e3cb0800  317  generative/C2-01/manifest.json
9dd97c52dd7c350777f022c536d3ca7e992bf93aaf517185eeebec9ce53f9394  1548  generative/C2-01/mark.png
a9d7c1f154d14b12cf97f19c0ad6e88ecdcc1f77755654ef9034a3aaa552b736  156964  generative/C2-01/prepared.json
8ca5c7ca5bfaaf129e96f12881253537f5535431523c54cfff3d9467ef0a97dd  353  generative/C2-01/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-01/schema-shell.fcstd
6045dc89dcb8f8d92f006aa86fedb8a25e586c53cc903c2534c908aab8620eb9  293  generative/C2-02/bundle-carrier.step
6045dc89dcb8f8d92f006aa86fedb8a25e586c53cc903c2534c908aab8620eb9  293  generative/C2-02/bundle-source.step
9c5b3697a1dcbbe8e7e9c9b21b42b748caa02da88cd9aae6b0de4b39c40b042b  471  generative/C2-02/bundle.json
c71860eed113bb64a1fe14cc8a76450472c7da962252fa20820986ca6a2ffb5e  1233  generative/C2-02/card.json
60f286aa519c8c60e7ab08001d27a09be5d48f22f275370daf3477cba5f0169a  531  generative/C2-02/context.json
e14100abe8420180d4ee26e6d4b4bef27ff7cbf32ba1fd05ca6e2e431d1ad2da  317  generative/C2-02/manifest.json
b873f6949509310383ee2c59bd2d89b7b74846e48d55e1e89d329869634b37bd  1508  generative/C2-02/mark.png
eeba741d771c61da6102ebf238694851fcd2f60b145a7751ce16114d65d6e8f0  108707  generative/C2-02/prepared.json
4e83c6e157b20034d053d0a35b3f7a78f7dba54bd6256824182a10ca29baf0df  353  generative/C2-02/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-02/schema-shell.fcstd
6cdd6d752b12fe705a23f8820a33da46dd32a14bb6db062389b2d272c155a9e4  293  generative/C2-03/bundle-carrier.step
6cdd6d752b12fe705a23f8820a33da46dd32a14bb6db062389b2d272c155a9e4  293  generative/C2-03/bundle-source.step
44b78a16e21262b44894142b7b40ac9d389d3749ff50ccb6649c9e4db5fd6a8f  471  generative/C2-03/bundle.json
1875ec5e4d4aa4f02c35caa907932a0b8b3f01cde47275cc139cc3c5db558a5d  1233  generative/C2-03/card.json
a089eec1a56b2deb568de2bb05c2d3169fdeae269fe0c34fc795688421543a79  531  generative/C2-03/context.json
2831fbf5b299bf285e1b9d24e961ddc53432e6074bc96b0b904bb56ea23e417f  317  generative/C2-03/manifest.json
cdfe05c1e070389f5ab9638121b6977a57a226c5e9974e721023e38509444bc0  1900  generative/C2-03/mark.png
f23ee9b576805fef72755e8d88d03a4d7e72d9f445d5faae40b32068ebe6ec39  212317  generative/C2-03/prepared.json
5ca45b6736d09b2fc03297a4f2b001aa2e476f467fd3976bb9f03b07855f93f2  353  generative/C2-03/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-03/schema-shell.fcstd
7997c9833c4b95b7cef6f7d5abf58ff7d9a3fde56a3846c7dc3008d3741f1bed  293  generative/C2-04/bundle-carrier.step
7997c9833c4b95b7cef6f7d5abf58ff7d9a3fde56a3846c7dc3008d3741f1bed  293  generative/C2-04/bundle-source.step
7d1bd123819a5c368b4567bd7e50b22d5037b16370ba180b71b578185ec3d9d4  471  generative/C2-04/bundle.json
eae5040c0803427c0066cdb740e403663f4334d8381a09b0ffea42cdaf4d734a  1234  generative/C2-04/card.json
235f9d7ace236e348f4f01364ccbf6ce091835bc8837fb12b81dca319db7265c  531  generative/C2-04/context.json
f65d9a9dcb553e389f0d435e27b89404deaa9620aba5c885602015cec7ecfc31  317  generative/C2-04/manifest.json
83377adc609f854aaf96ca9740019fa35538c3c985b66400b8573a8ace730e04  2126  generative/C2-04/mark.png
0f043b1049c52d82db82579558103c840d74124200825a7dc0cad1ddd9c36bcf  262353  generative/C2-04/prepared.json
906c8a598498cab7f14e39424b6c271bfd2153a23ead24f7aa483b56f71a4865  369  generative/C2-04/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-04/schema-shell.fcstd
70cdd47cd54204de59fec06ee21092f082005a402e404a825d1610bbbc1837c2  293  generative/C2-05/bundle-carrier.step
70cdd47cd54204de59fec06ee21092f082005a402e404a825d1610bbbc1837c2  293  generative/C2-05/bundle-source.step
2780631740cc5ace14c666ac63b52f633acc5045c64d9052e0ff0156f1ea1f53  471  generative/C2-05/bundle.json
cc9935ff92bca1a0b0c53c56a08ec0bd6a923784d5558c830eb49720ad5b70ed  1234  generative/C2-05/card.json
8ff11e96c9e5f07493b4c02d55e6a7ef5c5eed7e1229e487f56ec1e278367a69  531  generative/C2-05/context.json
87c740b3433d839517bccfa85a8fb0e9a82b1231736092caf06d6790716515e4  317  generative/C2-05/manifest.json
8f7ff4699e45790f4592cdda94454f3f84362054d3e19772ad7df058d2af6303  1994  generative/C2-05/mark.png
180f2ae293f194f10623bb9feba930bf797a3909b565dad376efa300fa28e7b9  222050  generative/C2-05/prepared.json
b9f88eef1fb3c6a949a9da45bdf1c1d3e9082404045871dde33a0480d29cc30c  369  generative/C2-05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-05/schema-shell.fcstd
29aaff6dbc1bf1055760bad95dbcf13e08e624aae85fcbc5a79a5980ba9249aa  293  generative/C2-06/bundle-carrier.step
29aaff6dbc1bf1055760bad95dbcf13e08e624aae85fcbc5a79a5980ba9249aa  293  generative/C2-06/bundle-source.step
c087970bc71d348c2ced837ed62cd9eb56dbe44adcb813c6d60dcba3886e6677  471  generative/C2-06/bundle.json
ac4c83e50a7393ea6cd48c7b6daaa35a00a8b28cf9cbb5340fd18cda0be9634a  1235  generative/C2-06/card.json
eb712bcdf6c21aa9c90efbbaf4c59c894751619eb150a9f1e7e5e9926f419fd9  531  generative/C2-06/context.json
c307afd78e7034e06ff2aa7bb7b4a84354edc1607339e4cf8f9c408f3ee9fca8  317  generative/C2-06/manifest.json
3beb14b41786dd1d5651f134a7351780b90e0e12ae39ea3300a0ad4c96615ab4  1939  generative/C2-06/mark.png
924afc446be850a78275e273d55b2b094f01b1b76c8f9a72c66e598804c897aa  220433  generative/C2-06/prepared.json
b700effd9c971f80037af4b977bc1bedae6365b9c506550e4844987ec25956a2  369  generative/C2-06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-06/schema-shell.fcstd
c26aeb2008cb19e850e63826caadd0db6117d36cf19991873968234a5f5ed4c7  293  generative/C2-07/bundle-carrier.step
c26aeb2008cb19e850e63826caadd0db6117d36cf19991873968234a5f5ed4c7  293  generative/C2-07/bundle-source.step
6fa8138bf9ead045f1abae0e0a8eaf249c68de063127616b00ff420dea667b54  471  generative/C2-07/bundle.json
2dd622b74b3a8961891c025a5d7ef37dfbef49bd48c7597906ca8093346833a4  1236  generative/C2-07/card.json
f8165d63b7b98c4f693e9587158a39e58840c67e8b5da40f6795031f9eed76c5  531  generative/C2-07/context.json
0b1905264c3f3c7a73cd13b20e45c7e1b5acf75abb1b7d765706e0b1125ae6a1  317  generative/C2-07/manifest.json
6933516f7955cf1a995257ca070c7caff43850c52d9f62194ea1f996b9bf4d7e  2967  generative/C2-07/mark.png
0b349f4479ed3695d05b2644be9e1f80b1bf47cfb63ddbaeed421421d0a1bdfd  383191  generative/C2-07/prepared.json
a95149be85afad8adb0279c094d9f2fd4c4b2ef1d2b94afa63f65aef2d7b8832  369  generative/C2-07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-07/schema-shell.fcstd
ea1b8b13172f84cbbe6742607b9c3dd1f66d2283d31554b155962ddb9bb0848b  293  generative/C2-08/bundle-carrier.step
ea1b8b13172f84cbbe6742607b9c3dd1f66d2283d31554b155962ddb9bb0848b  293  generative/C2-08/bundle-source.step
1f3726baa2427ddf4285555cf00d991d5f631e30db11b3f3aeb41edce7f7476e  471  generative/C2-08/bundle.json
63f28331309c22cd844c507034a46c45f79f5f6f7b8b95c92dd03b19f3f3cad0  1234  generative/C2-08/card.json
34ea874892d1c32456b9ef5fdcf5115430b25771f0b6702c3d91a9621a7e997e  531  generative/C2-08/context.json
10b38e88f3a454319598d296f84a6a9b1cabe251ae8760b617e4cd35a986d2c2  317  generative/C2-08/manifest.json
b3dbccab3f3ce5817c98e96cc4cb8e855f92dac675fc09285504e798d8a7778c  2260  generative/C2-08/mark.png
2a770caacf91265280a6dea1309871fd3f1df2029915f066b0eb8ef46928e727  192390  generative/C2-08/prepared.json
09cdf62216d3cbc35747311226465a2380adc59adcddbd4e7c46e6e6f44cbb7c  374  generative/C2-08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-08/schema-shell.fcstd
fa7d1b0f205467155210a85f2d31f5143794a96656df9dce5d5fe81f422cbcc2  293  generative/C2-09/bundle-carrier.step
fa7d1b0f205467155210a85f2d31f5143794a96656df9dce5d5fe81f422cbcc2  293  generative/C2-09/bundle-source.step
e9fb6682844ed8b02283b5f932f28f52a27f92bbca5b8f5a3e8a3187b1487b08  471  generative/C2-09/bundle.json
813c9752c7136702a76f79935b46b4aab5b644d75a31ffd2f2297052b3866247  1234  generative/C2-09/card.json
5a6a361d585caad0d4b0c62ba2afb84b974c129ad3b02c5e9b1471007862f5d3  531  generative/C2-09/context.json
4d8d63a866692f48bdca62c3e17fddf710f86974504a651fb484b0263b9d04ab  317  generative/C2-09/manifest.json
7608d47f4939d81bede0af0398440f84b711be6c3f2b71c355735ac0e9b351e8  2299  generative/C2-09/mark.png
0de7338ab14a53475ee95f07d077e440d520b41e19e1b33f74dd5d4436198680  189574  generative/C2-09/prepared.json
98e49779b9a2473dbea0390435b337b66c768d5571bbe34435945de985d09a34  374  generative/C2-09/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-09/schema-shell.fcstd
766451786faa0ec5ab1690edff4703d71f29f5ab9cfa2530a94a7bc5cc7fb1d0  293  generative/C2-10/bundle-carrier.step
766451786faa0ec5ab1690edff4703d71f29f5ab9cfa2530a94a7bc5cc7fb1d0  293  generative/C2-10/bundle-source.step
37f48f2e3936f6ac1584adddc6deadf50fe69e696cb680f01ea2e9ce467e90c6  471  generative/C2-10/bundle.json
62878e2f3174f6e56a31775a7c151b136bcadaa2dbe173b1860f6ccc9206b4be  1235  generative/C2-10/card.json
7dbfc36fb2d040feb8a38e4e72137e54c25c8921169df14cc3e633b194737996  531  generative/C2-10/context.json
ff71098a95b42bc25397530a11f84c8b7a99fec80301e6ba7dcd5361adffe1fb  317  generative/C2-10/manifest.json
98bb17fd3d0a76733580c21087f78573c503d97416aabfeab0b1380deb5abfb1  2655  generative/C2-10/mark.png
27ba2f6de8be0a05fbfc741db638f35b64da0c2308899380dd76f547e8c65e06  279157  generative/C2-10/prepared.json
c9afc00332c2743589a2dc356b7c245db1d1417d44dec08e5a84578210cb1700  374  generative/C2-10/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C2-10/schema-shell.fcstd
ccfaa54fbab02daca642f4e18152eadbd80676e1c818dff38bf436fb5df0c952  6870  generative/C3-01/baseline.step
ccfaa54fbab02daca642f4e18152eadbd80676e1c818dff38bf436fb5df0c952  6870  generative/C3-01/bundle-source.step
3bcb281a0b277a50350a0a6c256c2de9be1976cd01c505ec72290df46aa41bd2  472  generative/C3-01/bundle.json
e16839754d68f51731bb8c8c36a0b2e16bdb56ca5bca8695d4fa3aeec38e1c02  949  generative/C3-01/card.json
5fc2ee6e9d57a512435489ecdc24b8f0f5c423ef729ef9ca82e3d3a7b28509ba  719  generative/C3-01/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-01/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-01/font/LICENSE_DEJAVU
e5911561c0022325587bbb21c1f90f4f656f52922ec2f31a7942aa141bf58520  813  generative/C3-01/manifest.json
49bce8e6fd9781607bfc2dbd269588c607eaa168dc6d1b785a947cf24dfa4ca8  5347  generative/C3-01/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-01/recipe.json
1dae23fd9dc6ff7a399b33d7c956ec18ddd24dd4531277feb99a44083616c251  283  generative/C3-01/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-01/schema-shell.fcstd
9c9a6729374eb12072d0036a0d3708bde5af9d1f2bd0f1757e0858fb41ade41f  6870  generative/C3-02/baseline.step
9c9a6729374eb12072d0036a0d3708bde5af9d1f2bd0f1757e0858fb41ade41f  6870  generative/C3-02/bundle-source.step
ee4fd6c0b48c125208cb7fbd27a796b44cf34a1f2bc1d64f61a7c22b533ea857  472  generative/C3-02/bundle.json
2339450ee067bf1a64c0a3b57742570bc233e85d56e5b8832e36d7fbc4e5d908  949  generative/C3-02/card.json
3e37365853db3bca5821ca3438d0bb074efe7f8aad425b5876056d2171c8eae0  719  generative/C3-02/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-02/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-02/font/LICENSE_DEJAVU
090cc6dc53cbd2e0e8530e68f7968a74e46cacab47d9db70916e3c683672a08e  813  generative/C3-02/manifest.json
a15bdb13f826de21e33609c6586e869ae8d13d172f73f7a2fd03a422df0cc32c  5409  generative/C3-02/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-02/recipe.json
c11e44f34db356dee56b338f6ad7bf4c7df8dbd4458e9a2643a63f4c98e1e713  283  generative/C3-02/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-02/schema-shell.fcstd
33d5e4367369bcfd41652658cd0cde57c65990a6a47c3740398ccc62fa995639  6870  generative/C3-03/baseline.step
33d5e4367369bcfd41652658cd0cde57c65990a6a47c3740398ccc62fa995639  6870  generative/C3-03/bundle-source.step
6d0e4125e87416607bb1c01c30d677d7758daaa92b475ba0c69f9212b1a84dee  472  generative/C3-03/bundle.json
9790abfaba33d9d350ae3154580a53b96c36eb03eb51726984550dc062d8b3bd  949  generative/C3-03/card.json
6466f6868fa91591f2846944c6338a1ce49bdc38f39d1f1bfb08ad579756341c  719  generative/C3-03/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-03/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-03/font/LICENSE_DEJAVU
2e7e9e984620cc06d6bb0a46e68454b88d4798bcc87adb9334e94e1c567028aa  813  generative/C3-03/manifest.json
852de14b1cb631970d280ca54b1f5a8e409a523a9a0291f72fae7f66cc73051a  5423  generative/C3-03/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-03/recipe.json
1b5dacd5ea43f36b9100d371a78f15c3781579ff79ce917f7b353f9fa27c9a11  283  generative/C3-03/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-03/schema-shell.fcstd
c7f67c60b2594244ca8ab95e7ca6156e64a07b02d83cef6f44c35fbc1c33c0be  6870  generative/C3-04/baseline.step
c7f67c60b2594244ca8ab95e7ca6156e64a07b02d83cef6f44c35fbc1c33c0be  6870  generative/C3-04/bundle-source.step
29f9b3f599be5ace573cd195e6e5c5471528333903947c6111f60a4b2c9da011  472  generative/C3-04/bundle.json
e16839754d68f51731bb8c8c36a0b2e16bdb56ca5bca8695d4fa3aeec38e1c02  949  generative/C3-04/card.json
4973cc88b05f62036097290f053d4388bf598006ba684f28ea9acff5fedef6bf  719  generative/C3-04/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-04/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-04/font/LICENSE_DEJAVU
cc3fa7b7dfd0db80cdec037a8c164e058e51073540c3175290b312b78a36f203  813  generative/C3-04/manifest.json
082ed636a4472933cefa8f12829a8d82a9aa38dc9d36241ecc6a3797fcc02eb8  5347  generative/C3-04/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-04/recipe.json
a3dd5bd28b72565700ee2b9a1af1637dc49852a2a22b8d9ec56c018baa7ec5a0  288  generative/C3-04/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-04/schema-shell.fcstd
05fc45b6be0c009e1ab50e05fcb6afda0c21d578cdeff9a087953831ebacce1b  6870  generative/C3-05/baseline.step
05fc45b6be0c009e1ab50e05fcb6afda0c21d578cdeff9a087953831ebacce1b  6870  generative/C3-05/bundle-source.step
69ae1e148fc0c17a24ef9f4418f632a849a2180ae83b0ce4776d686901a3ec09  472  generative/C3-05/bundle.json
2339450ee067bf1a64c0a3b57742570bc233e85d56e5b8832e36d7fbc4e5d908  949  generative/C3-05/card.json
d1d83e4cef15978846917c927ccf90348ab32128a920c13f6bf8ce1f294f4248  719  generative/C3-05/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-05/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-05/font/LICENSE_DEJAVU
c2dc4947a2f1a7eab54458311e2716c29fc39b264a785640d7b0f5c60863f0fc  813  generative/C3-05/manifest.json
59d2c884c778c7b0ed6a5ed13d1af082cf44f34a2a9a2705259c3c729b0a3a72  5409  generative/C3-05/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-05/recipe.json
0600e35f27619796c8f3ecb5ea7470c745cf4a7bccdc42b7397ed287b0649ef2  288  generative/C3-05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-05/schema-shell.fcstd
1cdbfa2c59455ce19117326260b328f8105e79a928d30ffdffa5476b7ee386a3  6870  generative/C3-06/baseline.step
1cdbfa2c59455ce19117326260b328f8105e79a928d30ffdffa5476b7ee386a3  6870  generative/C3-06/bundle-source.step
38393a760e0d7c8319b7aba339cff8e5faa855c46fa66bac536c38bfdf48fa04  472  generative/C3-06/bundle.json
67ea6075c6b67c03eb4433f4cca6805f102d8efeec5bd63866308fc5e021039a  949  generative/C3-06/card.json
6af093f089f25f52f850dc72aa875fd34585b31647e286ae0c8dda9fb1a0fad9  719  generative/C3-06/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-06/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-06/font/LICENSE_DEJAVU
353bbbbaf615e897fd454ce868312a9baf337c38810af9b4541b63cf627949bb  813  generative/C3-06/manifest.json
b5071c4f8eed6069300addc944df994d56769d761200fa2b1a10ac7fa6c6144e  5437  generative/C3-06/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-06/recipe.json
8972d621b044a2eda613c150c7147f1651d63f11ad31fee48bc368fc2a47fc69  288  generative/C3-06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-06/schema-shell.fcstd
3a257ba57a80832c8d9cdce1035b987c074338958c740ba2398832c09546970f  6870  generative/C3-07/baseline.step
3a257ba57a80832c8d9cdce1035b987c074338958c740ba2398832c09546970f  6870  generative/C3-07/bundle-source.step
518e14093062963805084c41be738e79955c7a28fed08395801a71edb6aa56bf  472  generative/C3-07/bundle.json
764e6f8441d172433b24e817b2c1d1d3b41b06694048d78291b1a22734080433  949  generative/C3-07/card.json
a5b99b1a9fefd8bef64e6c662201212ce1a9674599e8f599b1aab85c059b57dc  723  generative/C3-07/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-07/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-07/font/LICENSE_DEJAVU
0958941c3f5523b76bd81946a75d3f9aac999a858536b2416f5d00f31bf2dad0  817  generative/C3-07/manifest.json
300ea2661d393287f03e5bddef628bbeb6b1156838265afc5e779a578e747854  5373  generative/C3-07/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-07/recipe.json
ddeaa9666be074b90f65af6e808266d337f0bb5d5e595d1495e1e668a9ed8d01  285  generative/C3-07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-07/schema-shell.fcstd
20bf2dee6cc7cd0a7b644a5f434d9a2b96f6748d983e083d4ea4c6415afe9ae2  6870  generative/C3-08/baseline.step
20bf2dee6cc7cd0a7b644a5f434d9a2b96f6748d983e083d4ea4c6415afe9ae2  6870  generative/C3-08/bundle-source.step
da37f6eaf6ebca2ab86c2d131b004c23a0d2a7228a610e12dac95f9633f6549c  472  generative/C3-08/bundle.json
91b1de91a4f7836dca6447589f08eadf5679accbec723d70a65bc22b47423e9a  949  generative/C3-08/card.json
f2812a419924df5b2f8db4d70f0573976ed80494e734207a0789ffbff498d7da  723  generative/C3-08/context.json
602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3  340240  generative/C3-08/font/DejaVuSansMono.ttf
d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e  4816  generative/C3-08/font/LICENSE_DEJAVU
94e9c34c16d0979cc196ecdc958ed87243ecd1519e13e740d88f36228a7c7d9e  817  generative/C3-08/manifest.json
65b63a5e02fbcc56c2e42ec0b648629361b98de96f009fbb8e8b289698f00d65  5375  generative/C3-08/prepared.json
02bef49364418ec768cd549b493cd81ca359b841e2b4ceb6e831bba589416a99  176  generative/C3-08/recipe.json
902e9dbdad97f1359f471096d1012a1ffe0d58a7114e230a844f0be56f7a0dc0  285  generative/C3-08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C3-08/schema-shell.fcstd
7bedad96f746b76c4b8d2cf2f3417fa97e44452d7c60c3eaaf3369cd21ee9da0  6870  generative/C4-01/bundle-source.step
6dbc48b440c5776acb4e492ea149b2445ff3d681f805bccedb664644be8ebe37  472  generative/C4-01/bundle.json
9519a9189c350ee432e19f5b94d2c27ba2ab9e60d5183182ce4260db742628e7  1826  generative/C4-01/card.json
4f3f940a972f1db434f9e0d3559cfe6456096b1080013180f57d05353b3e4eec  530  generative/C4-01/context.json
c54ce4cb12c1d972511478d524fcf4d8422041d372cb33600010f6ce0aa1515e  329  generative/C4-01/manifest.json
49ae75fca790b5a06a3730d9aec083030a705994ddcee07d72f73746b5595086  6214  generative/C4-01/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-01/recipe.json
7bedad96f746b76c4b8d2cf2f3417fa97e44452d7c60c3eaaf3369cd21ee9da0  6870  generative/C4-01/reference.step
394c3a733a617b9f16eabce27e07d90c1bdf728063d91add8df19c017366ae3e  125  generative/C4-01/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  generative/C4-01/schema-shell.fcstd
f02f518a25aa98802bf63a7ae59daea60d7dbb88dd34613ac17e7ead959a5cff  7647  generative/C4-02/bundle-source.step
5fc00942a4cf8ddf30806994ed8a35efb854197362cf551aeebdf6098f9721e3  472  generative/C4-02/bundle.json
6da55a579d4893e5a46b288f2a6c07d9bc99f187155dac5ffb1212cfdcc2f8de  2021  generative/C4-02/card.json
c046907d7b1ac4ad75e3a1bee61d5a315e8cf89201bbc6524a7065e521a6e5b1  530  generative/C4-02/context.json
c21f9cdbccf4ada7ecc1b163c1589ac5f501c9ff667d6a782d933f375599396a  329  generative/C4-02/manifest.json
df214a602247cf1301dde6cc0a14c9fe75b5a5ad0fa7f7f480a9fda59b85bf04  6804  generative/C4-02/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-02/recipe.json
f02f518a25aa98802bf63a7ae59daea60d7dbb88dd34613ac17e7ead959a5cff  7647  generative/C4-02/reference.step
57add32de6684c4eeb5e083bcc81f82f3354611385d9b9d856e8b8e493c46578  148  generative/C4-02/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-02/schema-shell.fcstd
88e9e2780f30cc6e4e83b40fe199b38a1466766e5c5a853d614fa88bb788308d  4964  generative/C4-03/bundle-source.step
322800739f74e7785b3d56cd29e9c9ab05bdb94efa2f6127dd19989089bcfc3e  472  generative/C4-03/bundle.json
fbc54a0dea2122444413424843c1554c1f6823721a5173453a628d4ac4aa25a2  1814  generative/C4-03/card.json
fbd816942c8bbec600046ed2fdb133184cae6a22dd667984a276c15c44ade421  530  generative/C4-03/context.json
43b1f2226a275130c468000d55c6c6783fc4505a327153a4b0bd332dd5929efd  329  generative/C4-03/manifest.json
0ff93b5b22b38ace40c41ecef239090b6ca7aa9735f6fe35e9f3a7c194db1fb4  5003  generative/C4-03/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-03/recipe.json
88e9e2780f30cc6e4e83b40fe199b38a1466766e5c5a853d614fa88bb788308d  4964  generative/C4-03/reference.step
014618a140f126c1b8cc2acecdd15cb7c08c079cd5edfc9d65f17013fe5229ac  151  generative/C4-03/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-03/schema-shell.fcstd
7af278c86ced6db756c7f1a221959933edb7e114dd55412e9266cd157d1e7a2e  4964  generative/C4-04/bundle-source.step
56cc2b343c973848f61dd913f63d503644b138dc5dc6a05125b272055d568643  472  generative/C4-04/bundle.json
5f96155a07730d955c3f042af774f7a7b521590873d5604d0e0c6ca5fff35f66  1822  generative/C4-04/card.json
6f3881b879d6a240911a18f00bad26c1f3cf506029433e88cc3013fef2d34617  530  generative/C4-04/context.json
bb996f2e197032be70a4c17ce49dc7edd24ffd3cc5bb0e4c69c7431805902d0d  329  generative/C4-04/manifest.json
5d3fd1ef9db7d714e5e04896d26c72862c0ad6ca0260ce7950f2b67c146f89e9  4991  generative/C4-04/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-04/recipe.json
7af278c86ced6db756c7f1a221959933edb7e114dd55412e9266cd157d1e7a2e  4964  generative/C4-04/reference.step
658c951fd63189eb44139b6e1128fc711b3419ae6fc8ebc1fabca2587428501d  151  generative/C4-04/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-04/schema-shell.fcstd
bbcf6120f40d60ea405ca996220f45b237eeba7721870cb3fb88c7f4669d6fa3  6870  generative/C4-05/bundle-source.step
60dd72a50dc53265ce8b76f998739d0dc957701154ba627af6b8f008351ace82  472  generative/C4-05/bundle.json
6aa1d80ab29dac6cf2bffa17923b06738c6bf4433284621ea516aac73b9cbb64  1380  generative/C4-05/card.json
8355f5ea9f38d2dac686127475c659221bb8481bf1ce6efe2f7e624566762b92  530  generative/C4-05/context.json
ed904f26c46dc706113593f8ac6aa82e827ad8fba18b399141a222cece7265ed  329  generative/C4-05/manifest.json
abef849eb95c80de2b90db8578b95d678e7d61fccf7e0df65fc3dc9de8ce06df  6230  generative/C4-05/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-05/recipe.json
bbcf6120f40d60ea405ca996220f45b237eeba7721870cb3fb88c7f4669d6fa3  6870  generative/C4-05/reference.step
a172c5418c81ec1da0155ecd32e40fc46c845d045025aa6cd5bb0bd4abed098d  176  generative/C4-05/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-05/schema-shell.fcstd
bc28ac3bafeac7e400265de89a71c4dc808fe8962ea32d6395e1d2322b5b5a51  6870  generative/C4-06/bundle-source.step
aaf9ee401e5b90468fd4324b7f2972c3f1d03e134b21a364386a6c595dd6f223  472  generative/C4-06/bundle.json
3d15424d89aa3265be51ca85cf9d6dec21fc2a1b6674056b11fc0806d9ea6b9e  1379  generative/C4-06/card.json
1dd1057d8973930369abab706bac357cf2f0362297a53cec41447127a1345054  530  generative/C4-06/context.json
9a6d22704e808870326e04e3a555f03c4970851349e9d0f69bb1422bc99a3caf  329  generative/C4-06/manifest.json
029a64d20857674c494128c1e1af5c370b7b6663e2721f0013fb2c71e7779333  6164  generative/C4-06/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-06/recipe.json
bc28ac3bafeac7e400265de89a71c4dc808fe8962ea32d6395e1d2322b5b5a51  6870  generative/C4-06/reference.step
37d3384d172e2944efd92d6b84e896c9a09ca982cb53e6aa5713a65b555f7020  176  generative/C4-06/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-06/schema-shell.fcstd
0d77290262c6fdf976b1709d44ed546d64ff52c98e76a1c19d320efab5f0e164  12053  generative/C4-07/bundle-source.step
aa24bbd290603b0c996180c5f28290d7a40f114f73a21f96d6eea0a72d516584  473  generative/C4-07/bundle.json
a274610e1ad109af409fc9701926a82caa351c0b3d852ec43ae34ca9d5b70f00  1043  generative/C4-07/card.json
1c76ce8617b681cd3e8d6111c165c9548117362c29a8c877294bfd13cc219432  530  generative/C4-07/context.json
e53100ad0356f3a93b1916a069b4faf26973035610146ef89b7435c0fca155eb  330  generative/C4-07/manifest.json
61f0df9cdc47be1d737f953451be5df85da90ec3b3295dd21fbbbe2094e99e3a  10149  generative/C4-07/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-07/recipe.json
0d77290262c6fdf976b1709d44ed546d64ff52c98e76a1c19d320efab5f0e164  12053  generative/C4-07/reference.step
2a7621d7172a7105ff1834492c1ff6d96b6c21df2f145c29e68f15ddb5e5b019  115  generative/C4-07/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-07/schema-shell.fcstd
d76b12b078b2ecf9487404efe61b2701fb741fcbe6fea736ce436eb8fe1f9f15  12012  generative/C4-08/bundle-source.step
c2c82cc7987db7fdc95358ac9afdd0cc605067c5338d14fdd7c027185d3aeb21  473  generative/C4-08/bundle.json
692a1b6395f8b90b485498ac6c2c128c126b7d21302e7e4115017f59ffa0e566  1043  generative/C4-08/card.json
6e90d5389d0e30335306218ae9c2cde201548b815a10cf62c7dc6b9c20570b45  530  generative/C4-08/context.json
b5180122fdb70279d414650759eb38c1dce161135e3aea673f8322f200f0b48a  330  generative/C4-08/manifest.json
2f0afe2db96657de1ed40a92f1b38b255c9c3ca17fb2708bb132791000f7bc8d  10139  generative/C4-08/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  generative/C4-08/recipe.json
d76b12b078b2ecf9487404efe61b2701fb741fcbe6fea736ce436eb8fe1f9f15  12012  generative/C4-08/reference.step
9625b95efb7e1e3992969edce5a2c731d227a14fe3b30a577ce1d364da34fdd1  112  generative/C4-08/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C4-08/schema-shell.fcstd
a9f71495da8b99cbea118cf322880f8904672e4c7a9e913b8fc57925a04885c9  5699  generative/C5-01/bundle-source.step
ce10d591f875fe7cab261948ed4ed5ead097d50b52b9851c450a38e8e3692897  472  generative/C5-01/bundle.json
528e083d31511b673cec82b9942660eaeaabf4918422df31664b5eb65423362c  3443  generative/C5-01/card.json
c46e589334a4f08470739af723efdecc46271e492af79d488ca2c7219c8a88cc  1156  generative/C5-01/context.json
938430efd8a87297f70c6baee1aba9c9e8a622feaced5a42479c5d2517abc2ab  329  generative/C5-01/manifest.json
8f8185d7b4ec566eef33dacfa241e7b38b71df5ff6661b2f7dd60bd4b6cc11a6  5112  generative/C5-01/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-01/recipe.json
a9f71495da8b99cbea118cf322880f8904672e4c7a9e913b8fc57925a04885c9  5699  generative/C5-01/reference.step
3482d14a658bc5bf98c94fb561fa40a7fe332dc409f1e54739dfb5d85e30e0e3  260  generative/C5-01/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-01/schema-shell.fcstd
a3ed5b5fd4b512b3727404ae5beacb08b1d2d4776fc58f12b28b11293903b056  5699  generative/C5-02/bundle-source.step
fe99a6e30fad1af26732db0bffe3cf3ec0421531da763b8def3e1bda65b1f885  472  generative/C5-02/bundle.json
d97dd10208d90f30ca594fa62124aae9c8f4e53e516ee4f2922519ad29d74763  3384  generative/C5-02/card.json
f7035c6ab043e45751750970296c7d84e0f138e505138a5c2c86b01f7f7cb404  1156  generative/C5-02/context.json
6f025440b80a9f484352a3ebbf990900245615659616012b24f9a5cc04bab808  329  generative/C5-02/manifest.json
ec5b83c20a9de92e46d4bc6b75e55190c6db738d186a2983117099e5eb494a3e  5054  generative/C5-02/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-02/recipe.json
a3ed5b5fd4b512b3727404ae5beacb08b1d2d4776fc58f12b28b11293903b056  5699  generative/C5-02/reference.step
6021466b5377ca51968c5183753f41aa66155ec7a0eddf433289df7506f77a58  260  generative/C5-02/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-02/schema-shell.fcstd
dc4647f84ee12b1497bf702172c33a52a0e63818d6ef665b70c8ab025d59b637  5699  generative/C5-03/bundle-source.step
a8656acb5b9a9d2ea7f2e129c75e57f775744c141ab4bc31a0c423f69679128f  472  generative/C5-03/bundle.json
a74b6c51d78768572b046a36a719a6b06e01a78fb06217a21995740f0a62f881  3404  generative/C5-03/card.json
ca8e6fcaabf3da1fb40977faa7e0763ed1ce3ae6435fb0745e770b70b055c4d1  1156  generative/C5-03/context.json
7b6fa0695ef980b3712df1ad75f02e3a3078bbf5ebc214794d2c618106dbaa9c  329  generative/C5-03/manifest.json
654138c6d4290c7714ff2995423368f97a0a4291b7649fd4e96b4a196202c62b  5054  generative/C5-03/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-03/recipe.json
dc4647f84ee12b1497bf702172c33a52a0e63818d6ef665b70c8ab025d59b637  5699  generative/C5-03/reference.step
3482d14a658bc5bf98c94fb561fa40a7fe332dc409f1e54739dfb5d85e30e0e3  260  generative/C5-03/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-03/schema-shell.fcstd
3ff0ef5bbabe23ab21d46339ecabfb84bcb1f7cb7640060cb75266c7d535c9ab  9085  generative/C5-04/bundle-source.step
c9ced4428b18e725ec5c702f3e7d9934cdbdb7c343352a27d90ea8179a47286b  472  generative/C5-04/bundle.json
6c62e6082b1a7260aa2d2ae1129ad4d1282c8869a87f7cc9b80437584d44bbc7  6520  generative/C5-04/card.json
9c2bb7d4702c89131affecd5a11a17f71251206e772b257eaa1ce9dc19d47967  1846  generative/C5-04/context.json
aa85214eede6a930c3b82e049b425db0708714f3142a0e02cecbfe2bc463bc83  329  generative/C5-04/manifest.json
c7658bf27b6af8bde1bd1786df77303d4c6f56b0f2c0c291be3aba94bfa327ad  8620  generative/C5-04/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-04/recipe.json
3ff0ef5bbabe23ab21d46339ecabfb84bcb1f7cb7640060cb75266c7d535c9ab  9085  generative/C5-04/reference.step
f91ea93f4ea6779ad98569e5fb20674b906b397f0e8a06e24fe8c68446352260  270  generative/C5-04/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-04/schema-shell.fcstd
fc86ae7e15c826b70b96c578b9ed872e6ec394bb40b000194eb3abd05a71b3ac  9085  generative/C5-05/bundle-source.step
7e2b317717e6f21950ac406fc9c1fab1fc63cc70304ad0b2b533cb9e8413c3e1  472  generative/C5-05/bundle.json
1d86422b906e71967942482491768d8365eace626075977b26861c65c406473e  6432  generative/C5-05/card.json
1652f1ab308d047865253e5562efeeb28e91e8396c65abb5d8a04e48df33492f  1846  generative/C5-05/context.json
058e74c34228cc50225056c7f3c08784af1ae577d70d6e7a6ae2a4221cf01c17  329  generative/C5-05/manifest.json
ebea60405e0656192d4158fe70054edd3438269296b68275d2c42a9a926c5e99  8375  generative/C5-05/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-05/recipe.json
fc86ae7e15c826b70b96c578b9ed872e6ec394bb40b000194eb3abd05a71b3ac  9085  generative/C5-05/reference.step
4cf77b4a055de07a93e1d626f40c1a9ee2e85878fa0c871c3007f6d375edfbac  270  generative/C5-05/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-05/schema-shell.fcstd
0ff08f62e8ce2c1fbcd82f51c225f3c653ff597743d7c2b2b234745af15fe0ef  9086  generative/C5-06/bundle-source.step
4a68bed1e1ce81b6f79fb2542d93d5b73c2b768d099fe5d7d808afb65ee5c4fb  472  generative/C5-06/bundle.json
9d5f0c1f68d5d96234f8c5ca4e7850e4e5f40ac6c4f856a03b5c53fa1ffef158  6490  generative/C5-06/card.json
4822e72e12d66f97b67570be10d370448198abb09d41ff8e1a28cee4a07c04bd  1846  generative/C5-06/context.json
9d3448794ab6b9ddfe341f12ba435acaa31674e709d776284e523793a991a449  329  generative/C5-06/manifest.json
8c2045b442674b5045121301812673eab1aec3612bc4fc5ca0abe746bf3bf0f1  8426  generative/C5-06/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-06/recipe.json
0ff08f62e8ce2c1fbcd82f51c225f3c653ff597743d7c2b2b234745af15fe0ef  9086  generative/C5-06/reference.step
f91ea93f4ea6779ad98569e5fb20674b906b397f0e8a06e24fe8c68446352260  270  generative/C5-06/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-06/schema-shell.fcstd
8dfbb1c1fd142b209a05e77b9f6cccda090833ad036de7a5168ffe3fab30326b  9085  generative/C5-07/bundle-source.step
6c4efd4108a071095443a77b4cac280031b4d4df7a2fd505a703632ed795b74a  472  generative/C5-07/bundle.json
8490cb7d2a2e54a7d842bb7d9af501baa16fa198dfb4930c9a37d3858ff099cd  6435  generative/C5-07/card.json
7baa17d4bf096f954607e7501c357ca0d06d25f841ab7000be7bccd5d7b61c78  1846  generative/C5-07/context.json
afb7354513eb5b463cb17140e3fecbadf8129e98e87a145af4443c8dff8f6be1  329  generative/C5-07/manifest.json
2a893df2d43a38235fb9b2b29ae423f9982adc3f8144f55cf0293b878bae9063  8589  generative/C5-07/prepared.json
cae2c5cb7ed6f81d0af6015ae5be88852b75f1131db93c7e3f6589ec901b83d2  176  generative/C5-07/recipe.json
8dfbb1c1fd142b209a05e77b9f6cccda090833ad036de7a5168ffe3fab30326b  9085  generative/C5-07/reference.step
4cf77b4a055de07a93e1d626f40c1a9ee2e85878fa0c871c3007f6d375edfbac  270  generative/C5-07/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  generative/C5-07/schema-shell.fcstd
7ae945738161b5ebc1143448ac5cee99f2492ff8fcff6f669fafc46930b5540a  480  retired-c2-cycle1/RETIRED.txt
a2c49a8117ff526a11674b8f46438856ef3e1bfd861ec9ee1bcfccc5ece9804d  287  retired-c2-cycle1/benchmark/B05/bundle-carrier.step
a2c49a8117ff526a11674b8f46438856ef3e1bfd861ec9ee1bcfccc5ece9804d  287  retired-c2-cycle1/benchmark/B05/bundle-source.step
4cbe26139e54fcdbafc827dec6f4469287d61a96234c9868c648cfa498a441fa  471  retired-c2-cycle1/benchmark/B05/bundle.json
f3c0535100b2482096c0d14377d9fb7d9152dc65a2d47bd0349a3e2a22a3f800  1233  retired-c2-cycle1/benchmark/B05/card.json
6778362c469642a4c5a02c748d2686b9780f78bc56d650fbe5d16a575c7d5642  531  retired-c2-cycle1/benchmark/B05/context.json
bff5c3c3fa00025725c062739f74e1bd9388756a079c46577d9787a8276f0b53  317  retired-c2-cycle1/benchmark/B05/manifest.json
7a30298ce8987aa96fe541042203dcd27caf514d3a6c335e8d2d2093166d31b8  1467  retired-c2-cycle1/benchmark/B05/mark.png
6d89be112883359bec3be07414703d4cba819d4172803bfc0437306a7df43c33  608  retired-c2-cycle1/benchmark/B05/pair.json
0612b13d5e2490235e9addb2c4cca2fcbe6bf7ccef8c9a26d116f98fbfc8f9fe  141289  retired-c2-cycle1/benchmark/B05/prepared.json
5d816a675afd3f21c4dbbf8d6178d73916b268f9af70ae2a7f76c42ef6180347  267  retired-c2-cycle1/benchmark/B05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/benchmark/B05/schema-shell.fcstd
ba561d0ecd36e8e11c5a271035ab7bba96ba5d7eaa404782ff452733aa69c543  287  retired-c2-cycle1/benchmark/B06/bundle-carrier.step
ba561d0ecd36e8e11c5a271035ab7bba96ba5d7eaa404782ff452733aa69c543  287  retired-c2-cycle1/benchmark/B06/bundle-source.step
08fde1e37aaea9cacab423720e3d5d44107c6d741541f7d64a0546157030ac01  471  retired-c2-cycle1/benchmark/B06/bundle.json
dff58af7ab9820099257ef2d0d8503ef403bce5d0430dff2f22bda30e90da709  1232  retired-c2-cycle1/benchmark/B06/card.json
390c6c55b699bbbadf4ab09428db55bd43161aff0a81c115994fb552fc6aa9e3  531  retired-c2-cycle1/benchmark/B06/context.json
75faf3ddad70ac49ba67893c6c9cffcbdb1348e9423230d1b8168344f9d63042  317  retired-c2-cycle1/benchmark/B06/manifest.json
847f52c65388e7e2e50edb9e28ffc36e8452f92881aace199d359c1d059b8c9f  2277  retired-c2-cycle1/benchmark/B06/mark.png
026938a509043e483a507a34757568ded53d0ddd58a7d1cf377684159337d3e2  617  retired-c2-cycle1/benchmark/B06/pair.json
dd31ce69021c54f499f1eba9cfabee00a6c315c4e21ed395927c23ebf7ff75af  276534  retired-c2-cycle1/benchmark/B06/prepared.json
f6991cb3684ba96e359a4a892f71e49dc324121aa87b1b02b148a432c064de76  286  retired-c2-cycle1/benchmark/B06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/benchmark/B06/schema-shell.fcstd
b96bf45d51f4dcfda91f22204725b5754c39f38d4ef891b1f30d06a9e382e1ca  287  retired-c2-cycle1/benchmark/B07/bundle-carrier.step
b96bf45d51f4dcfda91f22204725b5754c39f38d4ef891b1f30d06a9e382e1ca  287  retired-c2-cycle1/benchmark/B07/bundle-source.step
7c196dcd4cbfe3254ff93030562ad3509e325b57a111d1a405774679e1d6cf4c  471  retired-c2-cycle1/benchmark/B07/bundle.json
54e23ac0dcf256ecc2fe8b796be7fdf32699d9a8e796ced7ec25da8715d699c3  1232  retired-c2-cycle1/benchmark/B07/card.json
f23b09f56deae89b68fec8f433172b28de246223c2fc23a1de12ff504bca1d89  531  retired-c2-cycle1/benchmark/B07/context.json
19676cf9e6961e79fa62ec2b127d1a147e75af94f9709d4bc358261273288802  317  retired-c2-cycle1/benchmark/B07/manifest.json
7be46db2f2eec2fc10f6d135183a692c558e871fdac62e8869df9ffc602d3564  1924  retired-c2-cycle1/benchmark/B07/mark.png
e5efb14f35fe2f074615989fffee164d792b122eb63852c269cc9d605b46ebf6  619  retired-c2-cycle1/benchmark/B07/pair.json
446441708f7c961481403756820c6c0ec2c39723feaf2573889da9a203585c2c  172692  retired-c2-cycle1/benchmark/B07/prepared.json
2dd69d593cd719e8ff4d7fb5b1851581cc878c8cedad5fa54b91799d83bf55aa  292  retired-c2-cycle1/benchmark/B07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/benchmark/B07/schema-shell.fcstd
f28152ae976a53ae84dbc9487ba08d922a4f12c198d254b73d28496c9c805e10  287  retired-c2-cycle1/benchmark/B08/bundle-carrier.step
f28152ae976a53ae84dbc9487ba08d922a4f12c198d254b73d28496c9c805e10  287  retired-c2-cycle1/benchmark/B08/bundle-source.step
11f9674a8ccf19706015a0b2d6f2fd67fe0f2be24f6813df0033b38276796598  471  retired-c2-cycle1/benchmark/B08/bundle.json
e2b9f96152257f479cd8a91a82aa7eed782a7f49a487874c000b1ae847a8164e  1232  retired-c2-cycle1/benchmark/B08/card.json
f97f534471bbe0ba0a1df756e6e1e194a6f8351c6bf03d2cbf73899e1d2bede0  531  retired-c2-cycle1/benchmark/B08/context.json
c13aec8f0734b5862ee473b7ec98bc017b8f3f839ca178a4d51a2f00777d3146  316  retired-c2-cycle1/benchmark/B08/manifest.json
8cc72628857dcbfb63728b5dee9636a2713d4a1fc3e88c0d625682d9c082784a  919  retired-c2-cycle1/benchmark/B08/mark.png
60fc16ffac17659854b7b1b540352e499309f57164984cdb7cb9781b8d7ce1d8  608  retired-c2-cycle1/benchmark/B08/pair.json
0a32545c8999c8546f8838156f6522b0ebfc5e0cf7443388c004e3fe07a4167b  100279  retired-c2-cycle1/benchmark/B08/prepared.json
0430d224e3d429ffd23e3b96476085367470fb6f093044c6f0fab5e1e65af182  267  retired-c2-cycle1/benchmark/B08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/benchmark/B08/schema-shell.fcstd
8ab40385738ebf9523bbf0d05114ccc4ae6dd1e3519f552b53a1b178373173d2  291  retired-c2-cycle1/generative/C2-01/bundle-carrier.step
8ab40385738ebf9523bbf0d05114ccc4ae6dd1e3519f552b53a1b178373173d2  291  retired-c2-cycle1/generative/C2-01/bundle-source.step
b53ada550bbb40a01a5ef200f63edb1014f639ecbd1039d8eeb6991cc80f01a4  471  retired-c2-cycle1/generative/C2-01/bundle.json
a3b658b70744df7620e53d84909d63fd0b435facd67452303b66333daf76325c  1233  retired-c2-cycle1/generative/C2-01/card.json
d2d3021bc9f8d8310d084285c5465bdbbdb748fe98382095a942061dda80b938  531  retired-c2-cycle1/generative/C2-01/context.json
e2a3d043fb12ac7fdc223acd68d4e310c1a62615c86f44935fa0cea5263f267c  317  retired-c2-cycle1/generative/C2-01/manifest.json
27344ee5c07519cee2ca20b044beb725c8bc553fdfbb2224055c643555ba9497  1401  retired-c2-cycle1/generative/C2-01/mark.png
d4a6c44be03e37bd73b3c43956211b61472b895f4228b99f13631326f7947b4a  119324  retired-c2-cycle1/generative/C2-01/prepared.json
20f387f01a88c9c83a5989a6d14901eb834fd71f05c27f590876a78c52cbd617  267  retired-c2-cycle1/generative/C2-01/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-01/schema-shell.fcstd
2aa0d87684205fe9862d5fb9dae5bfafd709a7519b71e425d8b7f4a579b12871  291  retired-c2-cycle1/generative/C2-02/bundle-carrier.step
2aa0d87684205fe9862d5fb9dae5bfafd709a7519b71e425d8b7f4a579b12871  291  retired-c2-cycle1/generative/C2-02/bundle-source.step
c71908e3b6e365febd21173ca530ae5641239ccb3daa443161709c1b0379623e  471  retired-c2-cycle1/generative/C2-02/bundle.json
5a6abf3dedf6de5da39125b5c9fc7fcc22144628026042dad3483e852b1d8acf  1234  retired-c2-cycle1/generative/C2-02/card.json
2878b02a92fcbaf49075faff6282e63c17d778454f46b3021baf8b69b352a091  531  retired-c2-cycle1/generative/C2-02/context.json
016c35264bf6b23a288c0fd4bdd0e78c91dc383a638a566789c598ee97dbb775  317  retired-c2-cycle1/generative/C2-02/manifest.json
3102245d3678698814a4c437669773950ed55b7644519fd67b5f3ef57ee36851  1134  retired-c2-cycle1/generative/C2-02/mark.png
b0e51e206cb10eb573b84ed71299bc1166e71ef439b6377d2c91a0811896468a  68638  retired-c2-cycle1/generative/C2-02/prepared.json
5b45ce0a7961fe4ab4462a31824b1753e90777a64b56cf3ea75ab5658c42b8d1  267  retired-c2-cycle1/generative/C2-02/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-02/schema-shell.fcstd
0b5da090c0707f418deb235ba712f573d278a9112fad2e11b4960637b9dc9307  291  retired-c2-cycle1/generative/C2-03/bundle-carrier.step
0b5da090c0707f418deb235ba712f573d278a9112fad2e11b4960637b9dc9307  291  retired-c2-cycle1/generative/C2-03/bundle-source.step
edf6caa11ae5fb8a9fbe88c6c01677c77fec757c672ecb1b4de3438b41884d33  471  retired-c2-cycle1/generative/C2-03/bundle.json
6f3dc3632e56ee2b2fa4083dc8b80bb613363850cc7a2fc5b15cc4e5c69715db  1232  retired-c2-cycle1/generative/C2-03/card.json
0487dd30a4a69708783260c2940b9162b0f2ff471e3bf2e1c85e2b1f04916f40  531  retired-c2-cycle1/generative/C2-03/context.json
3f7d633af5eb8b38f1e0184298b4e7a0db0a2afd4c21a46b9c5df50bb5311d0f  317  retired-c2-cycle1/generative/C2-03/manifest.json
2c00ce07b42076eeab1c8f06f3a30b0f3f1b3fd580a8d60d298835f40321deac  1240  retired-c2-cycle1/generative/C2-03/mark.png
7a5e0bc2052faa880cc61c9c299c33ef5fdaccea0b0237493e38d57bf72e88ef  64493  retired-c2-cycle1/generative/C2-03/prepared.json
010fdf2a09fd4b2ff14bca6e22a519498e647e60a7d1cbf0ff1a4c181912d022  267  retired-c2-cycle1/generative/C2-03/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-03/schema-shell.fcstd
701b039a80f898cddce315f87c7cc028588c3b56209fa8969c02e81dc83530d8  291  retired-c2-cycle1/generative/C2-04/bundle-carrier.step
701b039a80f898cddce315f87c7cc028588c3b56209fa8969c02e81dc83530d8  291  retired-c2-cycle1/generative/C2-04/bundle-source.step
f507a811a4183cf19da63baa6c91f37b981cd0a876e8f4fc791c431c48e51ef0  471  retired-c2-cycle1/generative/C2-04/bundle.json
19e3c47d97dd5fe1174309fa93d4eb6a4cad1431deffc6b5a9a1b34b1974ffde  1232  retired-c2-cycle1/generative/C2-04/card.json
0604a3336ed0f1dde6cde50db54210ec92b9e1dc434f0d07fb4bab3d4d000ad1  531  retired-c2-cycle1/generative/C2-04/context.json
e094492a448b41c92ca6b6c8e746c6d399c17a1540b6a128fcc9289ca35394b1  317  retired-c2-cycle1/generative/C2-04/manifest.json
251d649e12d24e3cad59ce307ff567116f342172b6d3da2b783f879f02651eba  1963  retired-c2-cycle1/generative/C2-04/mark.png
ca7a701a24ae2026e2623fc9ebce4902b2739dd6a437cccc869af244d0461f9a  219868  retired-c2-cycle1/generative/C2-04/prepared.json
a908c805cb000111539db625f27ee0acb337f273ae0fa07ac66a56973415d193  286  retired-c2-cycle1/generative/C2-04/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-04/schema-shell.fcstd
69a164fee5839349f1e0f44d7b2413cc6250fd8008eba003189c67da98dda5ef  291  retired-c2-cycle1/generative/C2-05/bundle-carrier.step
69a164fee5839349f1e0f44d7b2413cc6250fd8008eba003189c67da98dda5ef  291  retired-c2-cycle1/generative/C2-05/bundle-source.step
b49d47e3049a5d7f4eb01804a3ad2f45a986a952666b1fc6194092a2378b3e06  471  retired-c2-cycle1/generative/C2-05/bundle.json
77411ef0b4ef6343470dee2be256140ba27f169f769625fae575910822ca66e6  1233  retired-c2-cycle1/generative/C2-05/card.json
c2e9d310917ffa3553c2777fd81665beb348db3c8c9e31929b7dddd2997b89a5  531  retired-c2-cycle1/generative/C2-05/context.json
2e038db6adea3ec91c7c59280450ca26d6fc8236ae3ffc92b2a8113efeb3e727  317  retired-c2-cycle1/generative/C2-05/manifest.json
7d0bdabfe3c3937536f431aa83d4c7339976f05b56031ecb9f2981c03c06b1d8  1781  retired-c2-cycle1/generative/C2-05/mark.png
9811797345633a8eed1d4ee432759e8b1acda1ba4bcea8bb345973610cd6d425  183581  retired-c2-cycle1/generative/C2-05/prepared.json
fc21d83ed54f2612ef2e036112161d446d58658f91a354ec50e999a5c52c155c  286  retired-c2-cycle1/generative/C2-05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-05/schema-shell.fcstd
f305c27949ee293b23252158dc0cd3b72c97f6ec3327284f2e6b24ae1fa9a47b  291  retired-c2-cycle1/generative/C2-06/bundle-carrier.step
f305c27949ee293b23252158dc0cd3b72c97f6ec3327284f2e6b24ae1fa9a47b  291  retired-c2-cycle1/generative/C2-06/bundle-source.step
26c46ee5509b6d1c54c2349932ba9910c84200743e8135d095fa53354afe04b7  471  retired-c2-cycle1/generative/C2-06/bundle.json
df44f1a4828766ed2c4daeddb6cf0e97115663c01b3c7407117cff462dd150fd  1234  retired-c2-cycle1/generative/C2-06/card.json
12d13a52ff75de557ff6aa08430390927f677fa1e3a3936b341d9d135896a961  531  retired-c2-cycle1/generative/C2-06/context.json
5cbeebc070a416a3a010e38377f25479c03d8f9b4f4c2c6b1207b8bb5237b56c  317  retired-c2-cycle1/generative/C2-06/manifest.json
0f6c36d3f8349ea7b28534680bd131c37fd5f3732c3eaa2d4bf917e86cd0c627  1757  retired-c2-cycle1/generative/C2-06/mark.png
ab82dcd03f69252ab105821a3c8154d78e187db6ea892a35de2b122968523fea  133997  retired-c2-cycle1/generative/C2-06/prepared.json
1319a5f7e0d3e85986e7e8c3ce66cb1a8ec624ab7254d479f301a2708e0b672a  286  retired-c2-cycle1/generative/C2-06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-06/schema-shell.fcstd
e774f34c2759e1c708c57f3bdbc920ccab2ab8582301fa7294b92bb2c01f39d7  291  retired-c2-cycle1/generative/C2-07/bundle-carrier.step
e774f34c2759e1c708c57f3bdbc920ccab2ab8582301fa7294b92bb2c01f39d7  291  retired-c2-cycle1/generative/C2-07/bundle-source.step
70e08b4fde0982d8537eaea134eb296c51c2c1a6f3ad3899394263526f4f00b9  471  retired-c2-cycle1/generative/C2-07/bundle.json
2017a62fa19bfc7b4d117b138c9dc7d9be0eacc4f4dfd614c1527836ab94ef82  1232  retired-c2-cycle1/generative/C2-07/card.json
b3bd447415d3256d5b59c3b9d7f7769ee5c6c7afe05c42f8d13ad511d4f7bb7d  531  retired-c2-cycle1/generative/C2-07/context.json
6244799b1d5a6318cab4cee68776b9e6a580a6c068c1c84a0acda6f15a889a5a  317  retired-c2-cycle1/generative/C2-07/manifest.json
9bd40e3fb445b59754fe9b882090adbfe57383f8893fd2306fb4dff52c629f8b  1510  retired-c2-cycle1/generative/C2-07/mark.png
49f7121c1017847cfe2566fd3d1898e35c0966708c46cff076f92b0212b4ac8b  188887  retired-c2-cycle1/generative/C2-07/prepared.json
06b8290d54a98230f28f2e6af5889162af743064269c89b1c60f8aa8623b5d4d  283  retired-c2-cycle1/generative/C2-07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-07/schema-shell.fcstd
0c321cab8819dc21bb5cb63e5a40e0557cae42682a87841b54729fd324d1644c  291  retired-c2-cycle1/generative/C2-08/bundle-carrier.step
0c321cab8819dc21bb5cb63e5a40e0557cae42682a87841b54729fd324d1644c  291  retired-c2-cycle1/generative/C2-08/bundle-source.step
1df85d392c77a9da19643b2b303e70bd4803390be5a6faf94dbc38d77fbf36f3  471  retired-c2-cycle1/generative/C2-08/bundle.json
96603752d6f723094b69bc8724bd262ef821029122d2f48f8c6fa97b32e6f800  1232  retired-c2-cycle1/generative/C2-08/card.json
9fe04aeef958977c148acbc23225e418be7cf73715d7f2824cedb928490a0f7b  531  retired-c2-cycle1/generative/C2-08/context.json
22548f3c93410274a6bebdd6b271b0c414553659cadcd523eb05a7f7139b65bd  317  retired-c2-cycle1/generative/C2-08/manifest.json
671fbda1035ae638817254c401f22d6b6ce688727ec40e0924f4f99e97f78e84  1937  retired-c2-cycle1/generative/C2-08/mark.png
07543c936342c01a885f3d50021ea7224b4bf742371a7b4f8b06c2d45d5792b3  161067  retired-c2-cycle1/generative/C2-08/prepared.json
aaea540e9a420ddd91c01c90cca0f4fa95febd7ce05b76e910c51fd795be29a9  292  retired-c2-cycle1/generative/C2-08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-08/schema-shell.fcstd
800e6bdeab02e574727dd697827d67f8be4381eb5497d2cf0b60387eb7b59a5b  291  retired-c2-cycle1/generative/C2-09/bundle-carrier.step
800e6bdeab02e574727dd697827d67f8be4381eb5497d2cf0b60387eb7b59a5b  291  retired-c2-cycle1/generative/C2-09/bundle-source.step
bbd8c3084ea12b02cd90368b9e17efb1fb5005e63118acf58393fd34f4c53122  471  retired-c2-cycle1/generative/C2-09/bundle.json
5d37fab610cd1d6a11571ce95d3901e55495ee830165cffd1cc2835f31de8df0  1232  retired-c2-cycle1/generative/C2-09/card.json
7be188b22c22f9fef83bb5c40f83c88f273ffa4857c6cc813fa059ae987427ee  531  retired-c2-cycle1/generative/C2-09/context.json
93de3a779dcb0f12da0b877f044e9e96f8a05c43d620a577b5ca884bd161d4c5  317  retired-c2-cycle1/generative/C2-09/manifest.json
0d58cd1ea83c4d8d85bbd3274ed860bfb4af52e9391f57d1108a92deb86579ed  2004  retired-c2-cycle1/generative/C2-09/mark.png
3150a35875c018e6c1068bc34f9e2b39e564f2fb91c5b70324bb6ff40fe25962  186508  retired-c2-cycle1/generative/C2-09/prepared.json
d93c43e7f5b3d50336e43a52a17e18b0211ea1a229e577737f7edf69e3c985ea  292  retired-c2-cycle1/generative/C2-09/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-09/schema-shell.fcstd
80d14113f0a3f502357a08b78d99255d296642d5aef12c6540fe57275a649b33  291  retired-c2-cycle1/generative/C2-10/bundle-carrier.step
80d14113f0a3f502357a08b78d99255d296642d5aef12c6540fe57275a649b33  291  retired-c2-cycle1/generative/C2-10/bundle-source.step
6cd14fcd21f6454f563809fb9aa33fdf02df0841bf9e356b63a4e89ef5fd2fca  471  retired-c2-cycle1/generative/C2-10/bundle.json
6ddfacdac2c1300647b3063292688fecad5458400b115d0763f508cc005aa3ef  1232  retired-c2-cycle1/generative/C2-10/card.json
b58fac9caeaa9995b3cb4d117717741dcd98cdc4ad4d9e923465178fa69f3dc3  531  retired-c2-cycle1/generative/C2-10/context.json
e58a8f4a90fde91ebe165a65af11955f5ea27c2d38ae1927c8d86b2284c7b49e  317  retired-c2-cycle1/generative/C2-10/manifest.json
776c85bbb7d9e91f2a264dfaa680854adf912128148950f5f3597a392f809f0d  1942  retired-c2-cycle1/generative/C2-10/mark.png
0edb9903eba21f6e1ef2dcc1fe274959a55804173665faa0e9ad53dd9232c43b  154028  retired-c2-cycle1/generative/C2-10/prepared.json
06452f691b09a4748bdc20e0fab810d54b4437e55bcb97dc31eb2f7525d74d03  292  retired-c2-cycle1/generative/C2-10/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-cycle1/generative/C2-10/schema-shell.fcstd
426c59dbb04d96bd790969a26844082707d091b50e43e08bf42f17f6450ea49b  386  retired-c2-v1/RETIRED.txt
2f6069414fad735872a7005776e7ac1277f92fcda5c3e1111f7efcc5a237a74a  6868  retired-c2-v1/benchmark/B05/bundle-carrier.step
2f6069414fad735872a7005776e7ac1277f92fcda5c3e1111f7efcc5a237a74a  6868  retired-c2-v1/benchmark/B05/bundle-source.step
94eab4b9d0704066d878ac65008a99668ad901fbb6d940bfc6f514e8a73bc79c  472  retired-c2-v1/benchmark/B05/bundle.json
30bf4e9d9ea6ff42a960c7246ead68835b1f6476e2a0457b7d65974b21e51a65  1221  retired-c2-v1/benchmark/B05/card.json
b7ee0d1a3ef50b30f065e8c206a017a830a04957871875b049dbc80e8083abe9  534  retired-c2-v1/benchmark/B05/context.json
8bf223bf9b0ac0537dfd72813c241f5c711e87c8ac5070a03a2d60b845078cbc  2081  retired-c2-v1/benchmark/B05/contour.json
27aecda35f83c5f0d79d6b88a97f824ea53fddcc4c65285008b8c395c34fb12a  523  retired-c2-v1/benchmark/B05/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/benchmark/B05/mark.png
a34b758973888463e99c6956fcd4cd75914992a4894fc49d83ee61f0237700ab  608  retired-c2-v1/benchmark/B05/pair.json
13f18727f7dffe00572e00f6705263426dbe39dd8fb8ce2d5af2cf80f6f888e3  3387  retired-c2-v1/benchmark/B05/prepared.json
6fe7622688bd7f21bd106e6ec32d4d8c18237a5d41eb280093543739d973845c  76  retired-c2-v1/benchmark/B05/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  retired-c2-v1/benchmark/B05/schema-shell.fcstd
670070d70db5c403b9277c618b082fa64f120a18f4b28213ec13d7dbcbb48d71  6868  retired-c2-v1/benchmark/B06/bundle-carrier.step
670070d70db5c403b9277c618b082fa64f120a18f4b28213ec13d7dbcbb48d71  6868  retired-c2-v1/benchmark/B06/bundle-source.step
3ad23da72de03e138dc04bf188e4ebd4382ca4d3c0ede540510d14ea7444b4c2  472  retired-c2-v1/benchmark/B06/bundle.json
3d96e586b9d29526915be40bbcfc3db47fd987c33520c916f62f2da47493b775  1222  retired-c2-v1/benchmark/B06/card.json
c651d0528696833b3ce9ed244e5040b1f51f9228d8722f4451324f0e2c5cc60e  534  retired-c2-v1/benchmark/B06/context.json
b758bf755bbd26db1bcff90cbfe3108928094c971142bceeb5fea2386656a037  3163  retired-c2-v1/benchmark/B06/contour.json
4dddd9395a18a8364f201f5dde7b334a3e75f5501d6978bc99ae9aded2233455  523  retired-c2-v1/benchmark/B06/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/benchmark/B06/mark.png
7d2f28a05a6c6a9384951db74bff424fd1f30d9c14059bbb9cb0c4bd3da3c2ce  617  retired-c2-v1/benchmark/B06/pair.json
427a7643bbb544c078540d1937f1a0ab1a992253df6b1d9972a2ba13d3f0697d  4749  retired-c2-v1/benchmark/B06/prepared.json
a7de97589f4295085bd45d89f3a0de7eed0cfe84641758ba8abbd763e253a7c0  85  retired-c2-v1/benchmark/B06/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  retired-c2-v1/benchmark/B06/schema-shell.fcstd
d53d5d81a1fd0c9ff1ae91470fd60b77e8c61f515c5e46af90aaed227d02f9c8  6868  retired-c2-v1/benchmark/B07/bundle-carrier.step
d53d5d81a1fd0c9ff1ae91470fd60b77e8c61f515c5e46af90aaed227d02f9c8  6868  retired-c2-v1/benchmark/B07/bundle-source.step
1b74a3019cc18e5ac2cd5a2988c9992655d1881ce08dd89c0fc74163daecfcbf  472  retired-c2-v1/benchmark/B07/bundle.json
605a3c83575947c23e2e6f731d9e2295239f6c1ec2e65c0b407d0e725d044ef3  1222  retired-c2-v1/benchmark/B07/card.json
4ab565592baff2bb8a3711254c2b9d2ad5a5a6e95fee8cf2d4dcfb2bca4fba85  534  retired-c2-v1/benchmark/B07/context.json
321c39aab4338048cdbb682373d11d537257414ea31c05fddcdd5d51924d7cdf  3995  retired-c2-v1/benchmark/B07/contour.json
127ac35b0fda9242986c190b6cddddae14e349d53c96dc47509fa4ef595dd3ae  523  retired-c2-v1/benchmark/B07/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/benchmark/B07/mark.png
d5183da5f831bcff283bfc6a7b78a96793120110f6ff18d5ab65ec27e6e2aaed  619  retired-c2-v1/benchmark/B07/pair.json
249f4f0b3d4bdc941e796a1804de0627e0041ff97207907304dfc32a05a57796  5717  retired-c2-v1/benchmark/B07/prepared.json
836e2d8cda2f28408ec8eced35ce5a6447bab14834f21c675bbf27c4e161cccc  87  retired-c2-v1/benchmark/B07/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  retired-c2-v1/benchmark/B07/schema-shell.fcstd
a76e0334f96c70ea560bccf50790c3f05ae42b55652f11ff0b5b401bae9ac1c0  6868  retired-c2-v1/benchmark/B08/bundle-carrier.step
a76e0334f96c70ea560bccf50790c3f05ae42b55652f11ff0b5b401bae9ac1c0  6868  retired-c2-v1/benchmark/B08/bundle-source.step
1538811369dcce2446b5ef2a7a492ff6422f323289dcba428c2c5f4455fa3138  472  retired-c2-v1/benchmark/B08/bundle.json
fee591a5b64205463e3cbc7ed63e76be1279f4e13f8b481bc23392bc8f5b0588  1252  retired-c2-v1/benchmark/B08/card.json
c097d5eed80046fe29dc420c364216bb7c2f7a28eb1fc65ade3d0ad6f957db0e  534  retired-c2-v1/benchmark/B08/context.json
6ac83e0315caaeb8cacab48d05aaad182dc090f5e445a97feb435a63a94c3e9a  883  retired-c2-v1/benchmark/B08/contour.json
6a2b1aad9db1f049d21cd7b26045d2eb96307ad85015f2be9fb07b961d140d65  522  retired-c2-v1/benchmark/B08/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/benchmark/B08/mark.png
de1819ea5cbe7316dbcc8673373b4f8f87ff9cdca1bf5ee750274f2acd26f93c  608  retired-c2-v1/benchmark/B08/pair.json
169cc829207e7c78b08283f63cbd3350eb4d9eb5d082dd0d4b9a93d2dc674728  1893  retired-c2-v1/benchmark/B08/prepared.json
0bd5fa600b0856397c8194ad4c0ca173a5ae65a9dcd0ac52ba675727ea41daed  76  retired-c2-v1/benchmark/B08/request.txt
3b928f82b9444a047714e8651238e947aab111ffd082061f4b2495e7dcaae73c  190  retired-c2-v1/benchmark/B08/schema-shell.fcstd
77fee13c427666f67cfce328ac64fcdaab6e8181eace135afbe3a2de3a118c6c  6888  retired-c2-v1/generative/C2-01/bundle-carrier.step
77fee13c427666f67cfce328ac64fcdaab6e8181eace135afbe3a2de3a118c6c  6888  retired-c2-v1/generative/C2-01/bundle-source.step
e8a8e346063aa793f5c60347e0f7bf25aac08b99306353acf4b27351795af541  472  retired-c2-v1/generative/C2-01/bundle.json
ac244b48cb2b49f3935bf414cb7c0a1e38c499e04bf499e7106f20502530084c  1220  retired-c2-v1/generative/C2-01/card.json
172e29a020469b98c5173548a7515722a76d7e301abe9495f07765e8f72393ef  534  retired-c2-v1/generative/C2-01/context.json
439883fc5a865447dcaef3d99983f411186a25a5a181e222e148f42d0aa94fd1  2085  retired-c2-v1/generative/C2-01/contour.json
b0b7aa6e1bfd73b3399a55dfa06fd528b75dee2b5284be49054f172c5982ee9e  523  retired-c2-v1/generative/C2-01/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-01/mark.png
4151598314353f5ba5c1225f9eac3491f84bc0f6c35702a9c57df50e0b8f4d21  3391  retired-c2-v1/generative/C2-01/prepared.json
7b1b7036b84cd4249c1087c1213c59982d15f39a5e152b5c2cc3098d1f4c6693  272  retired-c2-v1/generative/C2-01/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-01/schema-shell.fcstd
cbde7c6c49cc38409f951dd5055299baf617b28d6561cd563ff9e0f580c08939  6888  retired-c2-v1/generative/C2-02/bundle-carrier.step
cbde7c6c49cc38409f951dd5055299baf617b28d6561cd563ff9e0f580c08939  6888  retired-c2-v1/generative/C2-02/bundle-source.step
b66fce8cf9d4c3a8a321fe1cb7f2f043f80f7dda79d0976c6a4ada89543ddecf  472  retired-c2-v1/generative/C2-02/bundle.json
9e40605a776e924e60fd86aedf488f3bb432bc03cd603028697f2152b17c3077  1220  retired-c2-v1/generative/C2-02/card.json
a81d7752d7d9d2ee7462d5dd7b1096381ebe4acbd0c70e56f1518071d9b1febc  534  retired-c2-v1/generative/C2-02/context.json
aead5df6204e77caf2e72d28b2a39515dbb4b0d0528d14e8c0a6801ae1e7a11b  2084  retired-c2-v1/generative/C2-02/contour.json
ea08cd95c3a4d4decb010510023b40574ea34cf1f0e17b4097fe3159570b3c5d  523  retired-c2-v1/generative/C2-02/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-02/mark.png
c70fc479f440eae27012486cc6fee644bfc7b8d478c1d72287f75e259230df86  3390  retired-c2-v1/generative/C2-02/prepared.json
81cc6772f6171b8445e0aab24172e9d105a0a13972c369f317b43175069ce4b1  272  retired-c2-v1/generative/C2-02/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-02/schema-shell.fcstd
b5f31451174f28c8d66b5188b253b61772c6ad6392e4fbbfd8fb25daee363634  6888  retired-c2-v1/generative/C2-03/bundle-carrier.step
b5f31451174f28c8d66b5188b253b61772c6ad6392e4fbbfd8fb25daee363634  6888  retired-c2-v1/generative/C2-03/bundle-source.step
cc3e62d2a98be39a85139a645237d9b2ad691063feda04102285a89d1ae994d0  472  retired-c2-v1/generative/C2-03/bundle.json
be539e283ccae5f510ff1a9ce2e893381814c7637c9f6c590457c3777038f308  1252  retired-c2-v1/generative/C2-03/card.json
82ff76a96ace814289e45e045e2d9aaea02997fa3c06bbe93a9c584365842808  534  retired-c2-v1/generative/C2-03/context.json
a91a1dbb922215001bebf2b93d3e89e7c3ada838461a777d0d9a816ee49ace16  869  retired-c2-v1/generative/C2-03/contour.json
8e6de728aa80c74e1312be224735d409b24bff763315576810de4112e83304c3  522  retired-c2-v1/generative/C2-03/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-03/mark.png
6cfcba8e91013c7a3486947b2cec6bde062ef2527dcf89cac237d5ad27a6861e  1879  retired-c2-v1/generative/C2-03/prepared.json
f1878076473562ae8912a41f98fefb955b870fb6b440ef2786e509ded08572ee  259  retired-c2-v1/generative/C2-03/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-03/schema-shell.fcstd
d69fe1df3115b7221b91afa9eff4d63bb48089db189bb2f98f8cce9d80b322fc  6888  retired-c2-v1/generative/C2-04/bundle-carrier.step
d69fe1df3115b7221b91afa9eff4d63bb48089db189bb2f98f8cce9d80b322fc  6888  retired-c2-v1/generative/C2-04/bundle-source.step
0b5e184c9d456a3f3a71533d903e3754fc22ba973c08a9e9270f1c00cd9e0186  472  retired-c2-v1/generative/C2-04/bundle.json
fb3d0e2e95517097b868281cd44ad7e7b2725995828e4cc27888be1f10a92ecb  1222  retired-c2-v1/generative/C2-04/card.json
984c5f3a83138c7ce7ccd35975f525d7a635ae410b42e096101176565533d19f  534  retired-c2-v1/generative/C2-04/context.json
326846e5238a2f3b6e1c9f9b919c38cb7bac858bfd6c88b266c8850fc9626c4f  2620  retired-c2-v1/generative/C2-04/contour.json
1146cbd6f82f0c6a4fe6727f285f01f2929f4347e4f4365b0b35bb2f44558a3e  523  retired-c2-v1/generative/C2-04/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-04/mark.png
df1df368ce754243956ed023ef72f82d47fdfb0701c50e3c1418eea148191925  4066  retired-c2-v1/generative/C2-04/prepared.json
2eda18a067c16f30d5f31aa297c3c218e4a12be20bf1cd13c4b6924418e5e38c  267  retired-c2-v1/generative/C2-04/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-04/schema-shell.fcstd
51919b128d72ce35206c7ae8a0f01d7d2267e0858155b3505d32c007ce3c4cb7  6888  retired-c2-v1/generative/C2-05/bundle-carrier.step
51919b128d72ce35206c7ae8a0f01d7d2267e0858155b3505d32c007ce3c4cb7  6888  retired-c2-v1/generative/C2-05/bundle-source.step
082ae0777a140a46e9f1fa9e0f9ef91589931525fca3b909e0505358aa26ee6b  472  retired-c2-v1/generative/C2-05/bundle.json
3b853f83273724466effa76d04bd1e9177d6441c9bc8bb6a038b9da81bc34d1c  1222  retired-c2-v1/generative/C2-05/card.json
30d89c5c5c567298092897b0de227ceb020ac3140539fa8ee7f4cb939adf9e5b  534  retired-c2-v1/generative/C2-05/context.json
397fca275a29e673b412154a3010f2bd88cd25c4b0e13a42ae772e905253467b  3165  retired-c2-v1/generative/C2-05/contour.json
54ff274721ebb47a763cc147060229f8a9f91110577cde4cc10c84353c18d335  523  retired-c2-v1/generative/C2-05/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-05/mark.png
2bdcf0fc3f035e135eef1bcf6177f9a9e6f52e24c1c9f64d99f17771794f8cd4  4751  retired-c2-v1/generative/C2-05/prepared.json
b8be4a8fd462a9d5e7fd3d931a8432072f5e9e1e8007c8d8ccfb258c67fab95f  268  retired-c2-v1/generative/C2-05/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-05/schema-shell.fcstd
1de5555d846b9d9a7bff2e6ef30f2a31068c0ae63a544dd80160db7d9be00a49  6888  retired-c2-v1/generative/C2-06/bundle-carrier.step
1de5555d846b9d9a7bff2e6ef30f2a31068c0ae63a544dd80160db7d9be00a49  6888  retired-c2-v1/generative/C2-06/bundle-source.step
aa73e6aef1e1b1e46445f3701d14c49ec2c6a27971a3b967979a5928ee9ff6aa  472  retired-c2-v1/generative/C2-06/bundle.json
8685eb7603d4150c358d08b3a84968a0b402e3355b0d15cd800346109fc24697  1222  retired-c2-v1/generative/C2-06/card.json
0a8cf65b79a6bdd4702d88f45d942046982d1950ec4dcc6dbff33316b38ac47c  534  retired-c2-v1/generative/C2-06/context.json
ed77c9b753d1e1c9ec26ca348c49bbbb37b05fdf15fddd47dd839d29dedf0585  2632  retired-c2-v1/generative/C2-06/contour.json
55c65ff73e456179ee2f1f5c2b072734fe40f4867bfe82ca0f2048ae12ecadd2  523  retired-c2-v1/generative/C2-06/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-06/mark.png
eaafe7ec8f33ca3f6e55cd4364710fbeaf74f2ebef0c64556d96b21bb011714b  4078  retired-c2-v1/generative/C2-06/prepared.json
546155f05952e49a1e58a1ec51c847e318ce3d27aea57f2ed1ad12a01ca8b991  274  retired-c2-v1/generative/C2-06/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-06/schema-shell.fcstd
3e5e6f28dc570a9e3a874eec4baaee0aeb5fa6617c8d48e67bf86d992bc27f28  6888  retired-c2-v1/generative/C2-07/bundle-carrier.step
3e5e6f28dc570a9e3a874eec4baaee0aeb5fa6617c8d48e67bf86d992bc27f28  6888  retired-c2-v1/generative/C2-07/bundle-source.step
7cf0d42cd7c82e965b064442378a06c7fbfb0643f23a7a8e6357fb78ceb1f88f  472  retired-c2-v1/generative/C2-07/bundle.json
cec2e412e71144e27c6737c4fbf9283b0c68a7a0d80853dd68c6bcaa3189b9aa  1222  retired-c2-v1/generative/C2-07/card.json
693a8d4f465215a22f24c15d72a2670b4b5d71f7e93735afad5dcd1432cfa2a9  534  retired-c2-v1/generative/C2-07/context.json
9fd8260c2d33aaca8bef49e7d6904deff2bc2dbee78e3ab82dbdb799cf127f69  3170  retired-c2-v1/generative/C2-07/contour.json
324c9a45cc9dd61b7d00eab46a31ab8d24ea8667187340e6f37ff774978442cd  523  retired-c2-v1/generative/C2-07/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-07/mark.png
4b41ff920b294da015d65121d6beb98e30433a905a77f46ecc117bdb9e940ff8  4756  retired-c2-v1/generative/C2-07/prepared.json
7fc3d79f445e8d804a5e2ebcbf3882ddf39abc4d1c3b0f6739e45364d0a860d9  275  retired-c2-v1/generative/C2-07/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-07/schema-shell.fcstd
bcfea8258f52d59f544eebc691fb518919ffdb42fc32f674a8f094a375d67f81  6888  retired-c2-v1/generative/C2-08/bundle-carrier.step
bcfea8258f52d59f544eebc691fb518919ffdb42fc32f674a8f094a375d67f81  6888  retired-c2-v1/generative/C2-08/bundle-source.step
094c2d834ae41358c7cf17d950e05af32464cd910f11d413492f15334a591da6  472  retired-c2-v1/generative/C2-08/bundle.json
f08e423c536b25b740a49cdc33af17cd6da46a0ce5e4c9f1541c49039fc74b1e  1221  retired-c2-v1/generative/C2-08/card.json
879b10f3cb5e2b5c34bd89afaa1f55f48a340f9c84d1ca545254ca0849a804d9  534  retired-c2-v1/generative/C2-08/context.json
3ff5983fb237c42e1b0ddd2561eb28236e8a7f2da38a1c4acabc7dcdf57670d7  3937  retired-c2-v1/generative/C2-08/contour.json
92e29536b2d572bd809b93105733a8db87fdede6d1f7a509763eb1cbe80f9e7d  523  retired-c2-v1/generative/C2-08/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-08/mark.png
6c684955d38f61d5e7bba086abcfd8a9f8de3aa07a1823b6bce4a5ef0e43028a  5659  retired-c2-v1/generative/C2-08/prepared.json
d90129dd7eb691fedc02e2d9a6c9f297796ca5bb648bdf9fc4b13ae3d6f78645  279  retired-c2-v1/generative/C2-08/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-08/schema-shell.fcstd
730b5f2faa093f58e014d589421d763dd8f00f521a223ec1f19f9535a701b4e3  6888  retired-c2-v1/generative/C2-09/bundle-carrier.step
730b5f2faa093f58e014d589421d763dd8f00f521a223ec1f19f9535a701b4e3  6888  retired-c2-v1/generative/C2-09/bundle-source.step
9304beb451eab62c9361d63ac6070027a545e5d6968c6183a173477b1081f24e  472  retired-c2-v1/generative/C2-09/bundle.json
900316c198a339e44cabfd51a53e46fead2ec9390aadfeb298cb2a461591917d  1222  retired-c2-v1/generative/C2-09/card.json
4d36edaa9779b604677ec5e52fb989924d8169a7a89481c0a43f08f1871cacac  534  retired-c2-v1/generative/C2-09/context.json
423cb20f6ea2d96f7991f15e18bb9ddf4787faed3a6421750dac32b2361280bd  3936  retired-c2-v1/generative/C2-09/contour.json
44470d829ba7d18a97d98c108f3f2e5c6f65a1ef5acfeaf56b6a8911e35b0139  523  retired-c2-v1/generative/C2-09/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-09/mark.png
cddc6f9d8a435788d4a86631108c7798200fa33a2e628e09bc63631148383e80  5658  retired-c2-v1/generative/C2-09/prepared.json
ca30df0f777d1da9ad87cdbfef28189db66075bbb918a4cf7c285de741c3f7c7  279  retired-c2-v1/generative/C2-09/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-09/schema-shell.fcstd
7a72b3f2c309e0d9e59cb576eb6e9251219214dfa4828e716d606061cefcdccd  6888  retired-c2-v1/generative/C2-10/bundle-carrier.step
7a72b3f2c309e0d9e59cb576eb6e9251219214dfa4828e716d606061cefcdccd  6888  retired-c2-v1/generative/C2-10/bundle-source.step
45ea39c23891e0e9a733f3ce7182ed86467c5a700f107206a97d79386adb3391  472  retired-c2-v1/generative/C2-10/bundle.json
50e0690f14d2db65c2fab3163a9257e476d6e8039a6e80bc80941d13c1d0d108  1222  retired-c2-v1/generative/C2-10/card.json
375418a1a9ae0effa0253c705f510dca105e5437e6b8979415a092aa51ea1c82  534  retired-c2-v1/generative/C2-10/context.json
7b3abc02428230c0b31143c8866414e26ea62bf2d8dcc3e428d0340fa8c5a8a3  3941  retired-c2-v1/generative/C2-10/contour.json
5dbee52ff13c9216aed51e5700c1c8a23ceac6a5e2a6a3086975ba044c3073b4  523  retired-c2-v1/generative/C2-10/manifest.json
b1ff9c8ea3a780bad09b346c423d2d0e46815926879b18e841d928376a946640  69  retired-c2-v1/generative/C2-10/mark.png
97c82ff8fa413921f69e52196f45fbf5d0da44c99b3758ae1c73b278466c3b76  5663  retired-c2-v1/generative/C2-10/prepared.json
f045fe12ba765e7311a66a7f7b5e71d4fb295d3c7fa489c2efff38be1a68ad62  279  retired-c2-v1/generative/C2-10/request.txt
02c6606214687924bf61ca8b22af95f508447a971ad007d065089e8a19c47fa8  190  retired-c2-v1/generative/C2-10/schema-shell.fcstd
4f9339bd4d5c8c2257c5d7a57752d12a8fbcbb011b0e75802847e777af66b90b  9745  roster.json
```
