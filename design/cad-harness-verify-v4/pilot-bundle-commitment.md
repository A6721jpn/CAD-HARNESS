# Pilot bundle commitment (custodian, pre-freeze)

Option B / C-R1-3 / C-R2-2. One image-to-contour invocation. Zero model generation calls. This file is not a commit and does not authorize a pilot run.

The CLI prepare path accepts `evidence_mode` `independent_dev` only. The input-manifest schema also allows `custodian`. This run used `independent_dev`. The PNG is the pilot attachment, not a dev fixture.

## Recipe

- Recipe id: `rounding-recipe` (file stem of the dev fixture).
- Dev-frozen file: `reports/verify-v4-s1-dev-20261014T063456Z/fixtures/rounding-recipe.json`
- Dev-frozen file SHA-256: `d0551190868dad359fe0d7ad9c0a1b883563488a7fbe0a735771ced8a8c2300b`
- Applied file SHA-256: `8d7357059f143342a997a96eadecfc2d2cea6ea379b89e3e8f188e8d0f68ff8d`
- Applied canonical SHA-256 (sorted-key compact JSON of the recipe object): `cee52dd0eccb3ab800691eafbb00d6de026165b47931c912f979cc71f1882f69`
- Sole substitution: `scale.mm_per_pixel` `0.25` → `0.05`. Origin stays `[0, 0]`.
- Scale rule, fixed before the run and not iterated: `mm_per_pixel = 50 / frozen luminance-dark cell AABB height in pixels`, before rounding. Under the frozen foreground (luminance, dark, threshold 127) that span is 1000 px, the full frame. Luma is identically 0. Pre-rounding Y extent at this scale is 50.0 mm.
- Unchanged frozen fields: foreground luminance/dark/127, alpha `require-opaque`, simplify not allowed, rounding allowed with `radius_mm` 3, limits `max_deviation_mm` 1.3 and `approximation_tolerance_mm` 0.005, topology one component, holes preserved, islands rejected.
- `radius_mm` 3 is the frozen fixture fillet. It is not the 0.25 mm minimum-tool check. It was not changed.
- Thickness 3 mm is the C-R3-1 extrude default. It is not a contour-recipe field. No CAD was generated.

## CLI result

- Command: `tools/eval_verify_v4.py image-to-contour --profile c-s1 --asset-id logo --recipe rounding-recipe`
- Invocations: 1. Exit code 1.
- Status: `FAIL`. Error: `ValueError` `contour_nonopaque_image`.
- Software: FreeCAD 1.1.4 (`4fd3bf320d9566a27e60069fc8387448aaa3a094`), worker Python 3.11.14. The contour record was not written, so Pillow, NumPy, and Shapely versions were not recorded in provenance.
- `live_calls` 0. `live_cad_runs` 0. Document closed.
- Contour SHA-256: not produced. No `contour.json`.
- Mask SHA-256: not produced. No mask.
- Actual contour bounds and actual Y extent: not produced. Leg-1 was not produced. No IoU and no Hausdorff were computed. This is not a pass and not a fail against the C-D(a) numbers; the checks did not run.
- C-D(a) mask→contour limits, for the record only: IoU >= 0.90 and Hausdorff <= 1.5 mm.
- Contour→CAD: not run. C-D(a) limits for that leg, not measured: IoU >= 0.92 and Hausdorff <= 1.0 mm. Minimum R 0.25 mm on the actual output was not measured.

The frozen `require-opaque` policy stops before a mask or a contour when any alpha sample is not 255. That is what this PNG did (`alpha_all_opaque` false). No second run was made.

## Private artifacts

Directory: `C:\dev\v4-holdout-private\pilot-v1\`. Staging used for the CLI was deleted after these copies. No contour coordinates are in this file.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| rounding-recipe.json | 583 | `8d7357059f143342a997a96eadecfc2d2cea6ea379b89e3e8f188e8d0f68ff8d` |
| preparation-result.json | 738 | `396ebee23073bfe4be0d08dab1db1686fc6f1e92c9c57a61dd26e6c2c5bbe333` |
| transform-report.json | 1084 | `b255a4c62768900b7851b81e7097dda00fc43878cf90a04aa9500ce5d0b54b50` |
| min-r-report.json | 237 | `dd48de4702d6a2e25642d3ec92aa1dc4189ce8f0cac57e0907f4a231b198499e` |
| metadata.json | 528 | `5d6149b63cbcf2e14f156bc62925d151210c57793eeda1a62821ca31d7f25a54` |

## Pilot inputs

Hashed from `design/cad-harness-verify-v4/pilot-user/` at this drafting. Request text is not copied here.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| requests.md | 2542 | `a3a75986e005d18f9e2c734638b455adb8370b362095fcc4fe149bee3ae20593` |
| U1.step | 2695956 | `05f366a5e9a0bd7b451f063ef04ca10447b2028b09f81c734b01a6313a0cf8ae` |
| U2.step | 808687 | `a80d43f6180be313290647e94ae31e0a7c6f71658348252f09db733318791bd9` |
| U3.step | 2127563 | `3cdf4f1d3e9f3e83a7341a0d9e6f9ce2ce8e74c63d578bc27e8810a89ac6fd36` |
| U4.step | 7081133 | `d85327e5ce14ccc386d182f2d04b6d535fb49cd74c456bad6aa34e0be630c92a` |
| U5_logo.png | 39139 | `cff917e0b7e317eff88977aafea0379a99522e3ab120b36b7d73ee5626bfdd3b` |

## Pilot v2

One later image-to-contour invocation, after the fresh C2 cohort was recorded in `holdout-families-commitment.md`. The production recipe file was not edited. Zero model generation calls. No second attempt.

## Recipe

- Recipe file: `design/cad-harness-verify-v4/c2-production-recipe.json`
- File SHA-256: `ae1db1b48dfab10d9642c58d834068098f649855c00610cbfeb505c20bdbaf00`
- Bytes: 836
- Foreground: alpha channel, polarity light, threshold 128. Alpha policy `ignore`.
- Scale: `canonical_height_mm` 50.0, origin `[0.0, 0.0]`. Curve fit `periodic_cubic_biarc_v1`. Simplify not allowed. Rounding not allowed.
- Topology: one component, holes preserved, islands rejected.
- The same PNG bytes as the pilot-v1 input were used. SHA-256 `cff917e0b7e317eff88977aafea0379a99522e3ab120b36b7d73ee5626bfdd3b`, 39139 bytes. `evidence_mode` was `independent_dev`.

## CLI result

- Command: `tools/eval_verify_v4.py image-to-contour --profile c-s1 --asset-id logo --recipe c2-production-recipe.json`
- Invocations: 1. Exit code 1.
- Status: `FAIL`. Error: `ValueError` `contour_multiple_islands_one_solid_refused`.
- Software: FreeCAD 1.1.4 (`4fd3bf320d9566a27e60069fc8387448aaa3a094`), worker Python 3.11.14. Document closed. `gui_up` 0.
- `live_calls` 0. `live_cad_runs` 0.
- Contour SHA-256: not produced. No `contour.json`.
- Mask SHA-256: not produced. No mask record was written.
- Registration: not produced. No pixel-to-mm scale, origin, or image-height record.
- Leg-1 IoU and Hausdorff: not produced. They were not compared with C-D(a) mask→contour IoU >= 0.90 and Hausdorff <= 1.5 mm. This is not a pass against those limits.
- min-R report: not produced. The 0.25 mm minimum was not measured. No CAD body was built.
- Contour→CAD: not run. C-D(a) limits for that leg remain IoU >= 0.92 and Hausdorff <= 1.0 mm, unmeasured.

The production recipe rejects more than one island. This run stopped there. No contour coordinates are in this file.

## Private artifacts

Directory: `C:\dev\v4-holdout-private\pilot-v2\`. Staging used for the CLI was deleted after these copies.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| ledger.jsonl | 19499 | `b55358f670e6ac1688d5da00720918ae85d632e16bc35a4daebc2ffa2d47ca42` |
| native/result.json | 1079 | `7f10cc66ead4e9d22be20e4cbd88c3cfbe61ca69b92064b82919bc55b8eedfe8` |
| native.job.json | 1138 | `bfd5b94022486eb4edc255cabf1e9078bdc068120da1501be0a6e8fd9478f1a3` |
| native.ready.json | 390 | `cc91d9d82c05ca88d16254380076eab7ee0006bf65a20647eeb93d3e6e0bfcc1` |
| native.stderr.bin | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| native.stdout.bin | 934 | `b07c927556abb8c677bfb3418d6439454e04d1f08db391b0ee9a105a870b8e90` |
| summary.json | 1483 | `fd3f579d8ca6b05bfe22dd04809dc4b5bd4ffc2b250cf0b242dcfcdbda2cc0c6` |
