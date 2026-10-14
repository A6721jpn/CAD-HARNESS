# Batch 2 — v4grok

Read-only review. No code edit, no commit, no live call, no CAD run. `pilot-user/` attachments were not opened.

This sign is not final v4 authorization, a pilot result, or a holdout result. Both implementation locks keep `authorization` null and `final_v4_ready` false.

## S1

Verdict: **SIGN**

Reviewed `impl-notes-s1.md` and the tools it names: `tools/cad_verify_v4_inputs.py`, `cad_verify_v4_worker.py`, `cad_verify_v4_contours.py`, `cad_verify_v4_text.py`, `cad_verify_v4_compile.py`, `cad_verify_v4_plans.py`, `cad_verify_v4_judges.py`, `cad_verify_v4_s1.py`, plus the named facade modules.

- Lock receipt `reports/verify-v4-s1-dev-20261014T063456Z/implementation-lock-verification.json:1-7` matches the notes: `verified_offline_implementation_lock`, manifest SHA256 `75a6a374a66e3ad7c53f4647bac90c45d92ecabe89a9d260e810fe94bc782337`, profile `c-s1`, authorization null, `final_v4_ready` false, 98 bound files, 5028 native-runtime files. The manifest file's own SHA256 is that value. Forged non-null authorization is rejected as `capability.authorization:type` (`implementation-lock-verification.json:31-33`).
- `skill_sha256` `05f9949cd1d5b29dd79fe2bf451990027ae3ce0d72d8f5badd53fb6cd2e7ca6f` is the lock's bundle field (`implementation-lock-v4/manifest.json:108`), not the raw `c-s1.md` bytes. The lock binds `skills/cad-harness-v4/c-s1.md` to `e7eb4a5f6e4037bd1b9e1d2c92fa580c8db057a4990fa4b3ae9624886e623024` (`manifest.json:33`), which matches the current file. Policy `715bc5dc6d739ab9500c28dee565b2573172b489692abc072e50184079a699f0` matches `capability-policy.json`. Font `602ec86b8948cfcd956482fe64f94c36c867770149ef2f791d4613f443bcecb3` and license `d75938dec098f06f0ac3c00853065d94f020be1c3c62ef1dc2975ba15b4d9b0e` match `skills/cad-harness-v4/fonts/`.
- `original-profile-snapshot.zip` SHA256 `763fb69bdef88cb3ba62c7fb646ebcc3bd16e80585356bd732eefeddf506447d`, zip size 316045 bytes, 68 bound files plus `snapshot.json`. The notes' skill `df6a2ff9df096e7be5815957318f00684810fd79422d203d6fcdf42c9de25109` and policy `c5a301e3944dae3211fbffed3f7456c6712bd7558ebfc9fa8bea29d1ac69b5aa` are the preflight identity in `reports/verify-v4-s2-dev-20261014T085548Z/gate-smoke.json:52`, not the raw file hashes. Raw `policy.json` in the zip is `c8a3eb5c2e40c20f9b6d6aeb568422dce2bd3ab99446c4c078e4befb67969f14`, the same as the current file and the lock binding.
- Integer Rec.601 is `(299R+587G+114B+500)//1000` in `tools/cad_verify_v4_contours.py:614-618` and `tools/cad_verify_v4_judges.py:309-312`. Infeasible contour work is a refusal (`cad_verify_v4_contours.py:381`, `:722`). `pilot-user` and `v4-holdout-private` are rejected before use (`cad_verify_v4_inputs.py:19`, `cad_verify_v4_s1.py:64`, `cad_verify_v4_contours.py:691`).
- Judges reopen actual geometry. `reference_play` returns UNKNOWN when the datum penetration is uncertain and does not treat disconnected free samples as a path (`cad_verify_v4_judges.py:549-588`). Engraving depth is the plan value checked against the card's `depth_tolerance_mm` and `minimum_removed_mm3` (`cad_verify_v4_judges.py:596-651`). There is no hardcoded 0.3–1.0 mm band and no U1–U5 dimension in these tools.
- Raster-chain evidence matches the notes: volume `2961.0973355292326` mm³, bounds delta `4.440892098500626e-16` mm, radius interval lower `2.9999899999999893` mm and upper `3.0000099999999894` mm (`reports/verify-v4-s1-dev-20261014T063456Z/raster-chain-cli/summary.json:50`, `:278`, `:392-393`). Those are dev measurements.
- Holdout generator `openai-codex/gpt-6.1-sol` / xhigh and pilot `openai-codex/gpt-6-astra` / max are recorded with authorization null (`tools/cad_verify_v4_s1.py:31-36`).

Host command named in the S2 notes, which includes the S1 host modules, was re-run here: 127 tests, 1 skipped, OK, 7.169 s. `tools/test_verify_v4_s2.py` contributes 8 tests, so the S1 notes' 119-test command is that suite without `tools.test_verify_v4_s2`. The FreeCAD native suite was not re-run in this review. The author's 22 native tests and 23.511 s are not restated as a new measurement.

The S1 lock does not bind current HEAD. Twelve bound paths differ now, including `tools/cad_verify_v4_{agent,compile,freeze,inputs,pilot,plans,s1,worker}.py` and `tools/eval_verify_v4.py`. `impl-notes-s1.md:120` already says later S2/S3 edits invalidate that snapshot and require a new integrated lock. `cad_verify_v4_contours.py`, `cad_verify_v4_judges.py`, and `cad_verify_v4_text.py` still match the S1 lock. This sign accepts the S1 stage. It does not make the old lock a HEAD certificate.

## S2

Verdict: **SIGN**

Reviewed `impl-notes-s2.md` and the tools it names: `tools/cad_verify_v4_s2_edit.py`, `cad_verify_v4_s2_judges.py`, `cad_verify_v4_s2_contracts.py`, and the listed shared facade.

- Lock receipt `reports/verify-v4-s2-dev-20261014T085548Z/implementation-lock-verification.json:1-11` matches the notes: manifest SHA256 `74c818b6b40409f5a707b541b53b374255f4f37544a0d5c44e6e6c23c20de10b`, 117 files, 5028 native-runtime files, authorization null, `final_v4_ready` false. Forged authorization is `s2.capability.authorization:type`; a rebound code copy is `s1_implementation_file_binding_mismatch` (`implementation-lock-verification.json:34-44`).
- `skill_sha256` `4332a59f49cad4920ca91bc246ac613427d9e8c073b898ea0111a188502b6cc6` is the bundle field (`implementation-lock/manifest.json:127`). The lock binds `c-s2.md` to `87940be81d9dfec7dd4fbe7bf59bf50b9d80d2c33814638dcb864adf4d0cfcdf` (`manifest.json:45`), which matches the current file. Policy `3f07a0f7480fae2cc5bf4b08beca9e7db90e0b3e9225a29b3097d7c906af64fd` matches `policy-c-s2.json`. `s1-profile-snapshot.zip` is SHA256 `f1f0276822bea29e1da951a449b2ff5203c989e7a204cc1e721f0de0124bb816`, zip size 935955 bytes, 98 bound files plus `snapshot.json`. The original-profile zip hash is unchanged.
- Offset uses `BRepOffset_MakeOffset.SetOffsetOnFace` (`cad_verify_v4_s2_edit.py:186-194`, `:341`). Replacement requires planar supports, builds an unrestricted analytic halfspace, then rejects a patch that does not cover the resulting face (`cad_verify_v4_s2_edit.py:346-390`). Kernel history is OCCT identity, separate from geometric overlap (`cad_verify_v4_s2_edit.py:254-312`). A failed proxy clears Shape before the new result (`cad_verify_v4_s2_edit.py:439-457`).
- S2 canonicalizes a quantized normal component of zero to `0.0` (`cad_verify_v4_inputs.py:358-363`, `cad_verify_v4_s2_edit.py:133`). The stored physical normal is the unquantized vector (`cad_verify_v4_inputs.py:366`). S1 signatures are not passed through that replacement.
- Thickness: missing or multiple hits are not a thickness (`cad_verify_v4_s2_judges.py:266-267`). A continuous certificate is only the convex planar prism case; otherwise global extrema stay null and the status is UNVERIFIED (`cad_verify_v4_s2_judges.py:408-418`). Axis extents use `optimalBoundingBox(False, False)` (`cad_verify_v4_s2_judges.py:81-89`). `cad_verify_v4_s2_judges.py` does not import the editor or the compiler.
- Worker stdout is UTF-8 (`cad_verify_v4_worker.py:337-338`).
- Evidence volumes and roundtrip deltas match the notes. Planar offset volume `1721.716814692821` mm³, bounds delta 0, volume delta 0 (`offset-complete/summary.json:48`, `:830-831`). Tilted replacement volume `1916.1168146928223` mm³, bounds delta `4.973799150320701e-14` mm, volume delta `1.8189894035458565e-12` mm³ (`replacement-complete/summary.json:48`, `:818-819`). B-spline volume `1783.1669628642242` mm³, bounds delta `4.126682995320152e-09` mm, volume delta `2.1056621335446835e-08` mm³ (`smooth-complete/summary.json:48`, `:715-716`). The request replay records 3 replay responses, 2 CAD attempts, 4 deterministic operations (3 PASS, 1 FAIL), 8/8 captures, and `5.75199999997858` s (`request-complete/summary.json:1744-1748`, `:1980-2004`). Episode/initial/repair limits in that run are 900/450/450 s (`request-complete/summary.json:1754-1756`). Dev-only roundtrip volume acceptance 0.01 mm³ is the card bound in those summaries (`offset-complete/summary.json:1107`), not a user tolerance.

The host command in `impl-notes-s2.md:56-57` was re-run here: 127 tests, 1 skipped, OK, 7.169 s. The author's 7.445 s was not reproduced as a timing claim. The native 59-test suite was not re-run.

Nine S2 lock paths differ on current HEAD: `DECISIONS.md`, `PLAN-V4-ADDENDUM-C.md`, and `tools/cad_verify_v4_{agent,inputs,pilot,plans,s1,worker}.py`, `tools/eval_verify_v4.py`. `cad_verify_v4_s2_edit.py`, `cad_verify_v4_s2_judges.py`, and `cad_verify_v4_s2_contracts.py` still match the lock. `impl-notes-s2.md:133` already requires a new review lock after further edits. S3 files exist in the tree after this lock. The sentence "S3 was not started" (`impl-notes-s2.md:3`) is true of that lock and is not a description of HEAD. This sign accepts the S2 stage and that lock. It does not accept HEAD as the locked bytes.

## C-U5

Verdict: **SIGN**

`PLAN-V4-ADDENDUM-C.md:72-84` is the quote in `u5-defaults-sol.md:29-41`. Gemini withdraws the plate-as-CNC-benchmark claims, the ratio ≈0.83, the 2.5–3 mm gap, ±0.2 mm, ±0.5 mm, R0.245, and the parametric ranges (`u5-defaults-gemini.md:103-112`) and agrees to that quote.

Operative defaults after this sign, read with C-A2:

- Nominal thickness 3 mm and nominal logo total height 50 mm. Logo height is the Y extent of the committed contour, aspect ratio preserved, bounding box centred. These match `DECISIONS.md:57`.
- Minimum tool R stays 0.25 mm (`PLAN-V4-ADDENDUM-C.md:80`).
- The 100 × 100 mm plate in `PLAN-V4-ADDENDUM-C.md:74` is not an operative outline. `DECISIONS.md:57` and `PLAN-V4-ADDENDUM-C.md:88` void it. This sign does not restore that plate.
- No invented IoU, Hausdorff, placement tolerance, or operating range is adopted from `u5-defaults-gemini.md:10-22` or `:89-98`.

## C-A2

Verdict: **SIGN**

`PLAN-V4-ADDENDUM-C.md:87-95` matches `DECISIONS.md:56-65`. U5 is a cut-out logo part. Thickness 3 mm and logo height 50 mm stay. U1 and U2 play are <= 0.5 mm per side and the angle is 3 degrees per side. The U2 perimeter-band gap is >= 0.5 mm. `DECISIONS.md:60` applies ±0.1 mm to the 2 mm thickness and to the unchanged outer dimensions; `PLAN-V4-ADDENDUM-C.md:87` points at that full text. Items (a)–(e) are delegated to three-party agreement. The 19:47 tape decision is recorded at `PLAN-V4-ADDENDUM-C.md:104` and `DECISIONS.md:67-68`: location is not pass/fail, and the 0.5 mm tape thickness must fit. U2 minimal concave-face contact stays Astra plus the user's visual check, with no numeric gate (`DECISIONS.md:65`, `PLAN-V4-ADDENDUM-C.md:104`).

## C-D

Verdict: **SIGN**

The adopted summary at `PLAN-V4-ADDENDUM-C.md:96-102` matches `c-d-proposal-sol.md`, which is the text gemini agreed item by item.

- (a) Mask→contour IoU >= 0.90 and Hausdorff <= 1.5 mm; contour→CAD IoU >= 0.92 and Hausdorff <= 1.0 mm; same frozen transform; R >= 0.25 mm on the actual output (`c-d-proposal-sol.md:13-24`). These are not thickness or height tolerances.
- (b) Engraving defaults 5.0 mm height and 0.6 mm depth (`c-d-proposal-sol.md:37`).
- (c) 10+10+8+8+7 = 43 generative items, plus 4 admission controls. Generation ceilings 30+30+24+24+21 = 129. Astra ceilings 10+10+8+8+7 = 43. Total 172 (`c-d-proposal-sol.md:52-61`). Original 163-call holdout stays untouched (`c-d-proposal-sol.md:72`).
- (d) Episode 1200 s, initial stage 600 s, repair stage 600 s, and the subcaps in `c-d-proposal-sol.md:87-99`. The repair reservation 180+60+180+120+30 = 570 s fits the 600 s stage (`c-d-proposal-sol.md:101`).
- (e) As agreed at 19:33: 20 pairs, schema `cad-harness.cad-time-benchmark.v1`, 60 with-harness generator calls plus 40 Astra calls = 100, and a manual arm with zero model calls (`c-d-proposal-sol.md:117`, `:142`).

The human-operator requirement in `PLAN-V4-ADDENDUM-C.md:102` and the zero-model-call manual arm in `c-d-proposal-sol.md:142` are not operative after the C-D(e) amendment below. The 100-call figure counted a zero-call manual arm, so it is not the complete benchmark reservation once that arm makes model calls.

## C-D(e) amendment (USER 21:09)

Verdict: **SIGN**

`PLAN-V4-ADDENDUM-C.md:105-108` records `DECISIONS.md:70-71`. The without-harness arm is Codex, the same model as the with-harness arm, on the same requests, with no `cad_run`, no CAD-harness skills, and no harness CLI. The amendment also excludes harness contracts, which is the same exclusion. Human-operator fields are not applicable. The manual arm's "zero model calls" rule is void, and those calls need their own budget line. RESULTS must say the comparison is harness versus bare agent, not human time saved.

The operating envelope is still open. `PLAN-V4-ADDENDUM-C.md:106` requires the three parties to agree tools, FreeCAD 1.1.4 headless access, time ceiling, call count, handover, and the same cards before the freeze. This sign does not adopt the numbers in `c-de-amend-sign-gemini.md:19-43` (1200 s, 3 calls per task, 160 total). Those figures are not in the addendum.

No live calls, CAD, private holdout access, or commit.
