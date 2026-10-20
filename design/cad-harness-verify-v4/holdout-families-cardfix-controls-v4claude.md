# Cardfix v3 native controls — v4claude (signed proposal v2)

Public aggregate report. This file holds the method, counts, statuses, hashes and limits only. It holds no per-case geometry, card numbers, requests, values, seeds, coefficients, gold or private notes. It is immutable once published: corrections go in a new file or in `impl-review-launchers-v4claude.md`. The older reports `holdout-families-cardfix-controls.md` and `holdout-families-cardfix-controls-analytical.md` (v4grok) are retained unchanged as history.

Live calls 0. Model-generation and CAD-generation calls 0. This is not a lock, not an authorization, not live admission and not a `final_v4_ready` claim.

## Identities

| Item | Identity |
|---|---|
| Implementation lock (verified by the reviewer, EXIT 0, 2026-10-20T06:40:36Z–06:42:35Z) | `reports/verify-v4-claude-handoff-dev-20261020T0620Z/interim-lock/manifest.json`; `sha256_file` `4b9e9a7e975cafbdd35d82cac5a7b2437df915970ba43bb852415ee7ef0bc4b7`; canonical `files[]` `5ee94cd926f593d0dbcfc1225c59b00ed620a1942644e96182f524acd5dc6244` (410 records); HEAD `b673b9af8822d755822c64b8f0c5a6c7c5b80f0e`; 5 recipes; DECISIONS `243e2e39a59741a9dbc77be1b33bc32e37633017f9d27226616e72c66833a922`; neutral proof `9ac9261047082932a23bd2526951a88bb392423678cba9e6a416addb3714c4bd` |
| Signed proposal v2 | `f665255e79b21dcc871f3ceca644d50ca88f30d9af257fa6c722fcef8971ebc0`, 61271 bytes, 280 bound files, frozen 2026-10-20T08:04:13.150110Z |
| Superseded proposal v1 (BLOCK, retained) | `b4c6d21b1d72f5205fac3147554f1aaf0ac44ec00fd4b7e7e13fc5e87de227a5`; v1 controls summary `b445e211e50a62439e88fe8d71416a7ca564da468ab7527e3de1654111700c90` |
| Author | v4claude-author-1: an isolated, non-forked Claude Code context, `claude-opus-5-5`, effort high requested (not attestable). Release instruction `8a4739f3eb51de76803ede6833dac980d48cef0578b0c36a9bef7c865392beec`; v2 instruction `fac3651ef810bfdd37ce750193daa348ca573111ae1f3049af604e9f4f13e346` |
| Reviewer / custody signer | v4claude (w8:p9), `claude-opus-5-5`, separate context. Signed in `impl-review-launchers-v4claude.md` section 8 |
| Runtime | Pinned FreeCAD 1.1.4 (`20260928`, Python 3.11.14, OCCT 7.8.1), headless; the frozen neutral adapter `artifact-verify` |

## Control run provenance

- **run1** launched 2026-10-20T08:04:20Z, after the freeze. It was interrupted at about 08:25:04Z, when the author context was terminated by an API rate limit and its background shell was killed. That is not a control outcome. All 409 transient files are retained privately (`controls/run1-interrupted/`, 411 files with list and rollup; rollup `11c8abefd18791601c4ab60826392dcc719b9ecc9be2b99267665270d4b31996`). The author did not inspect run1 outcomes before run2.
- **run2** was the single complete replacement, under reviewer instruction: 2026-10-20T11:12:29.548Z–11:35:18.170Z, 1368.6 s, return code 0, stdin closed, stderr empty (`e3b0c442…`). run2 child `5ecac5fc0d1771d4d791a5c6a0b0c0f598be9f14d519f4d462eb9bc0b1637dad`, job `e13243d24c90ae65f4914c53fe9432b8302be6e92324f7b7bdb22dababfd2aa9`, stdout `8e2d911356585ffd79055088f55c54bdaaf115256802ff951b4d9251442bbcec`. No other rerun.
- On the 11 items both runs completed, every compared field is identical (comparison record `9704b93f4536c9adafb806ed8d47b93ea7566c98e957a0af53bb1c820faaba76`).
- Transient tool copies (the frozen tools refuse private paths) were placed outside the repository and the private root and then deleted. The 3056/3056 adapter code bindings in run2 equal the lock `files[]`.

## Control set (preregistered in the frozen proposal)

| Control | Definition (aggregate) |
|---|---|
| Positive | The editor builds a PartDesign Body with a registered operative parameter. Then: save FCStd, export STEP, frozen neutral adapter reopen/recompute/operative probe/STEP reimport, and the FULL card judged on BOTH representations, plus the worker round-trip check |
| +1 mm translation | Body translated +1 mm, exported and reimported; the full judge with measured evidence must FAIL |
| +M+1 mm³ | Body scaled to volume V+M+1 mm³, where M is that card's registered maximum; native_roundtrip must FAIL |
| Absolute +1 mm³ (secondary, reported) | Body scaled to V+1 mm³; must FAIL |
| Non-body | Part::Feature document; the adapter must refuse it (`native_single_output_body_required`) |
| Uneditable | Logic (editable false must FAIL) and an actual artifact whose probe targets a frozen read-only property: the adapter reports `editability_ok` false and status FAIL |
| Independent gold | Agreement with gold derived independently of both the constructor and the judges |

## Results, run2

| Control | PASS | FAIL | UNVERIFIED |
|---|---:|---:|---:|
| Positive full card (both representations) | 15 | 0 | 0 |
| +1 mm translation defeats predicate | 15 | 0 | 0 |
| +M+1 mm³ defeats predicate | 15 | 0 | 0 |
| Absolute +1 mm³ secondary defeats predicate | 15 | 0 | 0 |
| Non-body defeats predicate | 15 | 0 | 0 |
| Uneditable (logic + actual artifact) defeats predicate | 15 | 0 | 0 |
| Independent gold agreement | 15 | 0 | 0 |

Full-card gate by stratum:

| Family | Stratum | PASS / items |
|---|---|---:|
| C5 | two_patch | 5/5 |
| C5 | trimmed_multi_patch | 6/6 |
| C4 | planar_oblique (fresh replacement) | 1/1 |
| C4 | curved_offsets (fresh replacement) | 1/1 |
| C4 | finite_planar_replacement (fresh replacement) | 1/1 |
| C4 | preservation (retained) | 1/1 |
| **Total** | | **15/15** |

Which predicate each violation defeated (reviewer-extracted from the retained full check objects):

| Violation | c-s3 (11) | c-s2 (4) |
|---|---|---|
| +1 mm translation | `native_roundtrip` FAIL 11/11 | `native_roundtrip` FAIL 4/4. `preserved_region` also FAILs on 3, and `thickness_distribution` also on 2 of those |
| +M+1 mm³ | `native_roundtrip` FAIL 11/11 | `native_roundtrip` FAIL 4/4 (plus `preserved_region` on 2) |
| Non-body | adapter error `native_single_output_body_required` 11/11 | 4/4 |
| Uneditable | logic judge FAIL and actual artifact `editability_ok` false, FAIL, 11/11 | 4/4 |

Host admission (`validate_judge_card`, `validate_context`, family card requirements, `load_bundle`, control-plan validity) was 15/15 before freeze and 15/15 after freeze. Re-admission of the 48 unaffected families-v1 bundles was 48/48.

## Reviewer-independent controls

These ran in reviewer-written code under a separate private reviewer directory. They reuse no author program, and no repository judge for the geometry checks.

| Check | Result |
|---|---|
| Freeze integrity | v2: 280/280 bound files unchanged, 0 modified after freeze. v1: 272/272 unchanged |
| Order | Preregistration v2 07:58:44Z < synthetic measurement 07:59:55Z < freeze 08:04:13Z < run1 08:04:20Z < run2 11:12:29Z |
| Native reopen | 15/15: exactly one PartDesign::Body with Tip in the body, and a valid closed single solid in both the FCStd and STEP representations. FCStd/STEP volume and tight-bounds differences at floating-point level |
| Registered maxima | 11/11 c-s3 maxima recomputed from the immutable reference areas with the preregistered formula equal the card values |
| Violation artifacts | Real geometry, not mocks: +1.0 mm bounds shift; +M+1 / +1 mm³ volume deltas; documents without a Body |
| Gold cross-check | C5: sampled output↔reference distance at floating-point level in both directions, consistent with the frozen merge design; the unchanged source is rejected (face count), so a no-op cannot pass. C4: own ray chords 64/64 inside expected range ± tolerance on both representations for every thickness item, the fresh planar_oblique item exactly at its analytic value |
| Precision cross-check | Reviewer-owned trimmed and tilted/vertical cylinder-cut solids (not cases): FCStd/STEP geometry identical to ~1e-12 mm; volume differences are integration error, below the registered floor except the one disclosed outlier |
| Held history | 1927 older private custody files byte-identical before and after both author rounds |

Reviewer evidence identities (private files, SHA-256): `review-v1.md` `ec5cf814cbeac8d753c0fcc20566656f45d11a99ca87ae9e9d3e05af974c2a03`; `review-v2.md` `49943d3ab8500b2d36d61d4146ca46ac298051cddc59a7bb7b00045998ff14f5`; `review-native-1.json` `2ea56b52faae18274100bf4c4d9ba88845ae302c1e6d1aaeaca455075f4448bb`; `review-native-v2.json` `20cef6226be5efb88959d33bb3ce943033161c6aab81c452c50eada5c7564a7b`; `b13-coverage.json` `388322b0ef747389190a02599038bc412447e97a278a499df7ba5b754bc8ee2d`; probes `probe-1.json` `c2e81dbec0a4bc5a26b8649680a81ab9c06a5a33076c99db4136ee5f7dc6625b`, `probe-subbox.json` `025e3bf324d2a46d23eb793d0743a22b39609cc751877b2cb23f25a9e7868465`, `probe-hole.json` `5a15ce9dceb42bd7f601be934b89608f41c4049d0f15dec01642ac0f3562f3cc`, `hole-adaptive.json` `2772edfa630597e4f8e5497a85a95d7d28b2aade35bea4203a5d4e2d9c5dbfde`; history snapshot/rechecks `3ae57e3717f9d110bd3cf35750105c9f8cc35701275d2fdf2c2b3e92d1c0c9c0`.

## run2 artifact identities

- `controls/run2/` (private): 293 files, 193546696 bytes. Rollup `ca6976655c1abc083faa2c890c7f9725a86411a3eb6633efc5b99266e96c0777` (SHA-256 of sorted `sha256  bytes  relative-path` lines).
- `summary-full.json` `008166626a9866bbf896a8aae31357ec65f795a5aeceb68bc0ad264338c23fc8`; `native.job-record.json` `54691b4c9e5eb7d990f2ba9934e2e470c2a4f76980a5b961c758626f62d84b8b`; `transient-record.json` `05810ff7c1a684dc6bccdea69c306c334b70265f137a590f7dcf10fb49435c7a`; `host-listing.json` `5e068488d8bf31e5f6e6d2cabee3d28e8874f8453de65e8def5a5ee07dadc8a2`.
- Full per-item check objects (`out/<id>/row.json`):

```
824f3e40c94f24e9daff07142e54d60c9fe22647ca11e5fddbb55e32599e63f8  B13
23c2f4b06cf4849e9b46ea5b64b528755bc1e0ecd0c46de43d29af09a6bdba06  B14
7525acb2167eb9838892d9ca5d750befdbf29d7c37ea9d0811164922a642fae1  B15
5d8d703f4585caee39e8ed90f63684ece97eb06f361d7e20af54105e8980d785  B16
4511dd6ded0819f16b858b3d000720092deed5d9860dc330392cef655d439ad1  B17
a518023ad498eb1bd2f3ddefecdf9ab702c47088194d355cab9eebbdb0165548  B18
5932b34a53a2c1f96df336f8d3e4bce57cd46a8d391eb20b51d466068e255a58  B19
fec48fdb82f0f28ea0f278eed53c4d9aeec38d332977bf409790a3c57fd42f7e  B20
a02842cbaf31b99b5c9899d26082f61805ed6f1128a5fba0e14823d1c2be33b5  C5-01
29085baa27acf6a7ea1b7327ca53b319e988e44f767ecb1864a98841dca9cf92  C5-02
1787b33561288fe8ae13920bcd48da6bf629020e03fda907ddd88cd3730104c6  C5-03
8ba339f937eb9b37ed2c3df5ff9b7774346a2fd47ca72ac2107cb5e7b2d44527  C5-04
4e43565d7000d2717781c3407a5f8f4415fc8ecfbb5cc5929c9175057714d5d6  C5-05
6f45324a315489df36798a8ebc171b9d682b24b6c45148842c2dc2f3a8f32094  C5-06
401463aaf422a179050866beff1e8c101068a59cdaf991017bbc5d7715bd2799  C5-07
```

## History retained (not relabelled)

- **v1** (`b4c6d21b…`): full-card 14/15, BLOCK. The planar_oblique positive control was UNVERIFIED with `continuous_projected_domain_coverage_incomplete`. The reviewer reproduced that the projected coverage equals the domain to floating-point rounding only (Hausdorff ~1e-15 mm), with the frozen exact predicate rejecting it. v1's volume floor was not representative of trimmed/boolean faces, and the retained preservation item had no gold binding.
- C5 proposal `2b0a59b0…`: 0/11 full card stays as recorded. Selector proposal `80ea90bf…` is retained. C4 proposals `37730691…` (measure) and `d9164e46…` (reachable) are retained.
- Exposed history is never reused: `83e9a2ce…`, `77d53564…`, `50dcd991…`.
- Older v4grok reports and proposals are unchanged.

## Limits (must accompany any use of these results)

1. **The volume floor is empirical, not a certificate.** The auxiliary c-s3 native_roundtrip volume maximum rests on 26 author-built synthetic solids (1 invalid build excluded under the preregistered rule). The measured floor is dominated by a single curved-boolean-trimmed solid, and a larger set could raise it.
2. **Independent aggressive probe.** One reviewer-owned tilted cylindrical cut, at about 3× the C5 reference area, had geometrically agreeing FCStd/STEP representations, yet its Shape.Volume round-trip difference exceeded both the registered floor and the unchanged 0.08 mm³ donor intent. An output of that kind would be scored non-PASS on this auxiliary check. That is consistent with the donor intent the other cards apply, but it is a representation-dependent false-negative risk (for example for boolean-heavy bare-arm outputs) that reviewers of the benchmark must weigh.
3. **Sampled curved-offset scope.** The curved_offsets card uses `sampled` thickness (same scope as the item it replaced and the signed generative convention). It is not a global thickness certificate (C-D(c) rule 5).
4. **Common mode.** Author and reviewer are the same model family (Opus 5.5), and gold solids and native checks share the FreeCAD/OCCT kernel. Reviewer controls used independent code, ray casting and closed forms, but cannot remove kernel common mode.
5. **Known outcomes and provenance.** The v2 precision preregistration was written knowing the v1 control outcomes and the reviewer findings. That is disclosed in the preregistration, which is hashed before any v2 measurement; a first draft differing only in a timestamp field is also hashed. The first v2 control run was interrupted, and exactly one complete replacement run was made.
6. 15/15 on these controls does **not** prove a universal precision guarantee and does not establish `final_v4_ready`, an authorization or a final lock.
