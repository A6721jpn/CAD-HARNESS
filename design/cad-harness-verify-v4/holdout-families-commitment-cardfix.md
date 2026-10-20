# Family holdout cardfix commitment — v4claude (signed proposal v2)

Custody: independent reviewer and custody signer **v4claude** (w8:p9, Claude Code, `claude-opus-5-5`). The separate private author was **v4claude-author-1** (isolated non-forked context, `claude-opus-5-5`, effort high requested, not attestable). The author did not review or sign its own work.

Private tree: `C:\dev\v4-holdout-private\families-cardfix-v3-author-2\`, the signed proposal v2. Reviewer evidence is in `C:\dev\v4-holdout-private\families-cardfix-v3-review-v4claude\`. Sol and Gemini do not open either.

This file is the public commitment for the cardfix revision of the 15 affected family items. It records method, counts, strata, statuses, limits and SHA-256 identities only. It holds no per-case geometry, card numbers, requests, values, seeds, coefficients, gold or private notes. It is immutable once published.

It supersedes, for those 15 entries only, the corresponding identities in `holdout-families-commitment.md`. That file is retained unchanged as history, and every other entry there is unchanged. Live calls 0. Model-generation and CAD-generation calls 0. This file does not commit, push, lock, authorize or admit live calls, and it is not a `final_v4_ready` claim.

## Authority

- `DECISIONS.md` (SHA-256 `243e2e39a59741a9dbc77be1b33bc32e37633017f9d27226616e72c66833a922`, 18066 bytes): USER 2026-10-20 sections "independent checker-card revision and reseal approved", "affected geometry and existing measurement-reference revision approved", and "15:13 JST — auxiliary precision redesign and v4claude appointment".
- Handoff `handoff-v4claude-20261020.md`, including its sections "NEW VERIFIED MANIFEST — author release" and "SIGNED v2".
- Only the auxiliary native-roundtrip volume maximum was reregistered, and only on the 11 c-s3 cards. Critical dimensions, the absolute 0.005 mm deviation, G2, validity, operative editability, complete chart/complement coverage, the selection tolerance, the source gate, the numerical-uncertainty budget, the bounds maximum and the c-s2 donor pair (0.02 mm / 0.08 mm³) are unchanged.

## Bound implementation

| Item | Identity |
|---|---|
| Interim implementation lock | `reports/verify-v4-claude-handoff-dev-20261020T0620Z/interim-lock/manifest.json`. `sha256_file` `4b9e9a7e975cafbdd35d82cac5a7b2437df915970ba43bb852415ee7ef0bc4b7`; raw manifest `a2bd2b05baac8427f732db90503cf4baeaa6bddcde99a3584c471540713b30ea`. Reviewer `verify-integrated-lock` EXIT 0, 2026-10-20T06:40:36Z–06:42:35Z |
| Canonical source map | `5ee94cd926f593d0dbcfc1225c59b00ed620a1942644e96182f524acd5dc6244`, 410 records. Rechecked 410/410 by the author at start, freeze, resume and end |
| HEAD / tree | `b673b9af8822d755822c64b8f0c5a6c7c5b80f0e` / `f6d5decccd90bbadea355a9c4172a2f51ba5849c` |
| Recipes | 5 (all bound in the lock) |
| Neutral proof | `9ac9261047082932a23bd2526951a88bb392423678cba9e6a416addb3714c4bd`, 5057 bytes, 10/10 PASS |
| Lock status | stage implementation, `offline_locked`, authorization null, `final_v4_ready` false, live_calls 0 |

## Counts and strata

Family totals are unchanged: 43 generative items + 4 admission controls; 20 benchmark pairs (4 per family). The cardfix revises 15 items: C5 7 generative + 4 benchmark (two_patch 5, trimmed_multi_patch 6), and C4 benchmark 4 (one per signed stratum). The other 48 families-v1 bundles and the 4 admission controls are unchanged and were re-admitted 48/48.

| Family | Role | Stratum | Items | Disposition (aggregate) |
|---|---|---|---:|---|
| C5 | generative | two_patch | 3 | prior selector registration; only the volume maximum rederived |
| C5 | generative | trimmed_multi_patch | 4 | prior selector registration; only the volume maximum rederived |
| C5 | benchmark | two_patch | 2 | prior selector registration; only the volume maximum rederived |
| C5 | benchmark | trimmed_multi_patch | 2 | prior selector registration; only the volume maximum rederived |
| C4 | benchmark | planar_oblique | 1 | fresh replacement (new arrangement) |
| C4 | benchmark | curved_offsets | 1 | fresh replacement (new arrangement) |
| C4 | benchmark | finite_planar_replacement | 1 | fresh replacement (new arrangement) |
| C4 | benchmark | preservation | 1 | retained unchanged; prior evidence bound and new independent gold added |

Roster, in families-v1 roster order restricted to the 15 affected entries. The roster source is `families-v1/roster.json` (SHA-256 `4f9339bd4d5c8c2257c5d7a57752d12a8fbcbb011b0e75802847e777af66b90b`):

| # | ID | Family | Role | Stratum | Profile |
|---:|---|---|---|---|---|
| 1 | C5-01 | C5 | generative | two_patch | c-s3 |
| 2 | C5-02 | C5 | generative | two_patch | c-s3 |
| 3 | C5-03 | C5 | generative | two_patch | c-s3 |
| 4 | C5-04 | C5 | generative | trimmed_multi_patch | c-s3 |
| 5 | C5-05 | C5 | generative | trimmed_multi_patch | c-s3 |
| 6 | C5-06 | C5 | generative | trimmed_multi_patch | c-s3 |
| 7 | C5-07 | C5 | generative | trimmed_multi_patch | c-s3 |
| 8 | B13 | C4 | benchmark_pair | planar_oblique | c-s2 |
| 9 | B14 | C4 | benchmark_pair | curved_offsets | c-s2 |
| 10 | B15 | C4 | benchmark_pair | finite_planar_replacement | c-s2 |
| 11 | B16 | C4 | benchmark_pair | preservation | c-s2 |
| 12 | B17 | C5 | benchmark_pair | two_patch | c-s3 |
| 13 | B18 | C5 | benchmark_pair | two_patch | c-s3 |
| 14 | B19 | C5 | benchmark_pair | trimmed_multi_patch | c-s3 |
| 15 | B20 | C5 | benchmark_pair | trimmed_multi_patch | c-s3 |

## Proposal and seal

| Item | Identity |
|---|---|
| Signed proposal v2 | `proposal-frozen.json` `f665255e79b21dcc871f3ceca644d50ca88f30d9af257fa6c722fcef8971ebc0`, 61271 bytes, schema `cad-harness.cardfix-preregistration.v4`, kind `complete_cardfix_v3_proposal_v2` |
| Freeze | 2026-10-20T08:04:13.150110Z, before any v2 native validation |
| Bound files | 280. Rollup `82e2e9069d0095365dbf8da40b6b3f9ab409c61c58eb7cfa6933aa858308cbd0`, the SHA-256 of the listing below as UTF-8 text, one line per file: `sha256  bytes  path`, sorted by path, LF-terminated |
| Supersedes | v1 `b4c6d21b1d72f5205fac3147554f1aaf0ac44ec00fd4b7e7e13fc5e87de227a5`: BLOCK, retained, 14/15 |
| Author report / provenance | `author-report.md` `2286540ad3b7e2764187f0b9ee15c5cd8bae8c15cd9bdbadf6ccc322cf40b978`; `PROVENANCE.json` `832516d88c2408e80462a57856fa0114bb30438d24faf31ec331315422e6c46d`; `PROVENANCE-addendum.json` `91501b313983648f18dbf156cd35d6ad8fa8ba641c2db805e46e9a811d38fe96` |
| Integrity snapshots | pre-freeze `f51b3200b97e2aa1802e6811eb10bcf81abf8eead90440bf23ae2525cc54e1b8`; post-controls `37ee528008416beb287d376cd0ab4b0ff6fb409407b60488f219654ecab9cad0` |
| Host admission | pre-freeze 15/15 `c22f1f0543d5effd83b416f1d139bfc3109691bde6e24ca1a185fe369c0fec24`; post-freeze 15/15 `2779161a12f1b99a41f32c9672d724390f965e5664325b4951ef7c6bd701a33f`; unaffected re-admission 48/48 |
| Native controls | `holdout-families-cardfix-controls-v4claude.md` (SHA-256 `169f918f71ec6c80c6a8d7c7c9e2bece4f7b70606cc6901b1177f6332d8a0f2d`): run2 15/15 full card; every decisive violation defeated on 15/15 |

Category rollups. Each is the same listing restricted to one category:

| Category | Files | Bytes | Rollup SHA-256 |
|---|---:|---:|---|
| cards_contexts | 30 | 61598 | `b1bc564286dac8212abb88c7ec5f74de6d20fc6565856217bfc40dbe5346f4c9` |
| source_assets_preparation | 143 | 988668 | `c3df4d029da493abeb2ead7966a6ef644282c356ec6a978af4f88be38b5702cd` |
| gold | 10 | 59508 | `7bfae3c1aea4f095c5798bb28bbfa69fbb0bab121dda812e39af3903e4c20d6d` |
| precision | 73 | 755626 | `259a80a7fcad068741cac215896b445826f12f3836f0b4a7a47f7027fb64f14f` |
| author_programs_and_admission | 24 | 90042 | `87f8fe863de3aeb9200cff2665a02ee7081ce04486b868e0afe3c57cb0ac6040` |

The category rule is applied to the bound paths:
- **cards_contexts**: `staged/**/card.json` and `staged/**/context.json`.
- **source_assets_preparation**: every other `staged/**` file (immutable reference/bundle STEP, manifest, prepared facts, recipe, plan, pair, request, schema shell, bundle).
- **gold**: `gold/**`.
- **precision**: `precision/**`.
- **author_programs_and_admission**: everything else.

## Auxiliary precision method (public method; per-card values private)

- **Name:** `frozen_uncertainty_closure_plus_representative_roundtrip_floor`, unit mm³.
- **Preregistration:** `5bc9df31429f2c24e8d63f9dadcc63e658bf7776e29d50a73938dff42a86ae98`, written 2026-10-20T07:58:00Z (file 07:58:44Z), before any v2 measurement. A first draft `4408b0ca8d814a819d17f5253d8d612fe076bef0de5ad70211b8339034917051` differed only in a mistyped time field. It supersedes the v1 preregistration `29494304fb3da0832fcd13a236c381d4f938df763474a1d81a9cfe6c4ede9775`.
- **Derivation and evidence:** derivation `5ca4680775b4ac7a35742e390c783b009c1ef21ceaa2caa733d10209eb80396a`; synthetic raw results `dfcae8e4bd88fe242da5eba06d8b366be96b59565d76a9907ae24f8fad800af6`.
- **Frozen semantics used** (`tools/cad_verify_v4_s3_judges.py`):
  - U = eps·(A_source + A_output) + 128·ulp(max(1, V_output)).
  - PASS iff d + U ≤ M; FAIL iff max(0, d − U) > M; otherwise UNVERIFIED.
  - d = |V(FCStd reopened) − V(STEP reimport)|, as measured by the frozen neutral adapter.
  - eps is the unchanged card numerical budget.
- **Registered maximum:**
  - M = eps·(A_ref + A_ref·(1+ρ)) + 128·ulp(max(1, V_ref·(1+ρ))) + δV, rounded up to 1e-6 mm³.
  - A_ref and V_ref are native preparation facts of each immutable reference STEP.
  - ρ = 0.01 is a declared, fail-safe area margin.
  - δV = max(K·D_abs, K·D_rel·A_ref, 1e-9 mm³) with K = 10.
  - D is the per-solid maximum of the FCStd/STEP/built volume disagreements and the default-vs-adaptive (OCC, ε 1e-9) integration gaps, measured over the synthetic set.
- **Synthetic set (author-built, none a case item):** 27 attempted, 26 measured, 1 invalid build excluded under the preregistered rule. Classes:
  - planar-sided, including boolean pockets: 6;
  - untrimmed split multi-patch roofs: 4;
  - axis-aligned boolean-trimmed spline roofs (common/cut): 4;
  - oblique-trimmed: 3;
  - curved-trimmed (cylinder/sphere common/cut): 4;
  - fused: 2;
  - quadrics: 3.
  - The maximum disagreement came from the curved-trimmed class (D_abs about 2.1e-3 mm³), giving one common δV of about 0.0215 mm³.
- **Preregistered caps on the method, all satisfied on 11/11 cards:**
  - The admitted true discrepancy at identity area (about 0.022–0.023 mm³) is ≤ the donor 0.08 mm³ intent; it is at most 29% of it.
  - The equivalent mean surface displacement (about 1.3e-5 to 2.2e-5 mm) is ≤ 10% of the unchanged 0.005 mm deviation bound.
  - U < 1 mm³ and 1 − U > M, so the +M+1 mm³ and absolute +1 mm³ controls stay decisive.
- **Not outcome-fitted:**
  - The formula, K, ρ, the class composition and the caps were fixed before measurement.
  - The measured d of the case items is not an input.
  - The author knew the v1 control outcomes and reviewer findings, and that is disclosed.

## Native controls (summary; full report in the controls file)

- run2 (single complete replacement for an interrupted run1, which is retained): pinned FreeCAD 1.1.4, frozen neutral adapter, full cards on FCStd AND STEP.
- Positive 15/15. +1 mm 15/15, +M+1 mm³ 15/15, absolute +1 mm³ 15/15, non-body 15/15 and uneditable 15/15 are all defeated. Independent gold 15/15.
- Full-card gate by stratum: C5 two_patch 5/5 and trimmed_multi_patch 6/6; C4 planar_oblique 1/1, curved_offsets 1/1, finite_planar_replacement 1/1 and preservation 1/1.
- No pooling. Each stratum and family gate stays independent, as signed in `c-d-proposal-sol.md`.

## Unchanged holdings verified

- **families-v1:** 1144 files matching the public listing in `holdout-families-commitment.md`; `families-v1.sealed.zip` `588db92fa91cc276ff5d3dc13a7fdf16fa49395d6e420e6a81e0d56396c21dcf`.
- **Original60:** cohort `45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65`, 37412 bytes; 91/91 files listed in `holdout-original-commitment.md` match bytes and SHA-256. Original 163 maximum unchanged.
- **Older private custody:** all 1927 files (families-v1, cardfix v1 and v2 trees) byte-identical before and after both author rounds.
- **C2:** cycle-3 recipe and data not rewritten.

## Retired and retained history

- **Retired C4 benchmark material** (families-v1, kept unmodified):
  - planar_oblique card `c14ddad3f97427fbfc9281478cd54fadaf198ae918ab4b9c9ae2a208def353b1`, reference `e4b2112523798ae1426e260fb90ddbc2e48ebf4e2eaea0c54f5d3d1706dadfab`;
  - curved_offsets card `065a2c94c0cca70a009f0dd9c5c2e6348acf35c9230fe03713395409d6c26401`, reference `c2b469a1cc137a2cb569fb28d0470c3f3e20f6168ebae406e9c034ee71efa231`;
  - finite_planar_replacement card `1a838809f38eddd4e2f49900992af2f0eeadc4f3666e0d2543bbc773efb05329`, reference `a1a3ed52d69e3559358a27bfd94dbc07233d7163c06e057500ae20d08dcd8050`.
- **v1 planar_oblique candidate (retired):** card `95028ceba66b6abe9f0d5eb3920e73237cf2025141197c938dca6ac250a65cf9`, reference `ab41588a2140488d96f35568c1130e5235fd06a8173811fd479e2aa15b2e0477`.
- **Retained proposals and results:**
  - C5 `2b0a59b0fbf5e47143eaa436f6a0036862acb3361fd0c26b28ce9020d3fbf70d` (0/11 full card, not relabelled);
  - C5 selector `80ea90bfd94523ccc8c14c5da6d8081f261ed32ee831aa84fe8ef43b0cde9034`;
  - C4 measure `3773069191a7aa7f686b30f453550bdca7c755341e35894c3151f8fbdd0e589a`;
  - C4 reachable `d9164e4625183d59af24139cf4beb185a143e5afe47040ad5c205dfd2eb61f55`.
- **Exposed history, never reused:** `83e9a2ce3b94fa2bcb8b560a444653ced2f74299b70c2cc40d2516f203076cba`, `77d53564173ef15ed9140ffed3586fb1f75d25838a5dbe25abad0418ecabde70`, `50dcd9918eb520016676150d3b94af404f4023f6a57055b7ed6250dd98af9fb1`.
- **Preservation item:** prior evidence bound (families-v1 card `f2614a246429c03f2dfdb24a3e8d6b51fc24a5200c40ed7d501eb006901d33cd`, reference `049cada40e196a42c67b1ab6c8a20daf1ceed263fd6f3fa235b9a300a741014d`; measure-1 card `804dd0cf0bfaddf27f38ef48327fdaf82a37eebbcb18cc7aaa3619adef720046`).

## Limits

1. **The volume floor is empirical, not a certificate.** It is dominated by one curved-boolean-trimmed synthetic solid, and a larger set could raise it.
2. **Independent aggressive probe.** One reviewer-owned tilted cylindrical cut, at about 3× the C5 reference area, had geometrically agreeing FCStd/STEP representations, yet exceeded both the floor and the unchanged 0.08 mm³ donor intent. Such an output would be non-PASS on the auxiliary check. That is consistent with the donor intent on other cards, but it is a representation-dependent false-negative risk (for example boolean-heavy bare-arm outputs) for the harness-vs-bare comparison.
3. **Sampled curved-offset scope.** The curved_offsets thickness is `sampled`, not a global certificate (C-D(c) rule 5).
4. **Common mode.** Author and reviewer share a model family; gold and native checks share the FreeCAD/OCCT kernel.
5. **Known outcomes and provenance.** v2 was authored with knowledge of the v1 outcomes and reviewer findings, which is disclosed. The first v2 control run was interrupted, and one complete replacement run was made.
6. 15/15 is not a universal precision guarantee, not `final_v4_ready`, not an authorization and not a final lock.

## Publication prerequisites still open

- Gemini's independent public-method/data review of this file and the controls file.
- The reviewer's SOURCE/CUSTODY verdict in `impl-review-launchers-v4claude.md`.
- Sol's explicit reviewed commit/push, excluding caches and private material, then the NEW post-push implementation lock.
- **No new deterministic sealed archive (zip) was created** for the cardfix tree, unlike the families-v1 seal convention. The binding is `proposal-frozen.json` plus the 280-file listing below. If a sealed archive is required, it is an open custody step, not done here.
- The live family, benchmark and pilot pools still require their own separate authorizations. None is granted by this file.

## SHA-256

`sha256  bytes  path` for every file bound in the signed proposal v2, with paths relative to the private tree:

```
832516d88c2408e80462a57856fa0114bb30438d24faf31ec331315422e6c46d  1100  PROVENANCE.json
c22f1f0543d5effd83b416f1d139bfc3109691bde6e24ca1a185fe369c0fec24  12471  admission/admission-prefreeze.json
d2dbee407fb80c815a38186250a3573829afeababf3ea68745cb491b837ef0f9  3769  admission/admit.py
e108602091b295fcd0eb66b2033e60b0aa8ab5e147019f7be4d1bbef1945ec29  2007  admission/readmit_unaffected.py
4fdb8dce31c32506b3d1bca4c51f78620edd5c707c70ae1955bd4f2a1a84fd39  14076  build_proposal.py
eed31de3bff6282cfa3d4159219c447babe488dd92e2232cf7c20e88d963422e  10631  c4-author/author_v2_child.py
e87b983b59877fc93d1072fce5626beaff4b9ecd02b52510bd6c4854a7cfbe2d  3799  c4-author/b13-v2-card-justification.md
3f1892cb15bceb78cf0f7353470e02576a3b3131b689228483c27b355a0c8ce8  382  c4-author/job-v2.json
8bd89a0668eb2f124b9e449601c5d4067e0ff1ec683f6f887a2033b7bd23e325  1219  c4-author/run-v2.job-record.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  0  c4-author/run-v2.stderr.txt
7fd2b22b548b9a3cef88658c8550a403dc4a79e874fa6455e3ad9b42de422d9b  47  c4-author/run-v2.stdout.txt
b05983863421a2a2da63853c7605c776155222d64a62f01b6e8749fa3bc19482  1642  c4-author/run_author_v2.py
6394db472096d23df5a8081830fb2ed2ba19bb142b2193987903239d4a02a60b  600  c4-author/transient-author-v2.json
5ecac5fc0d1771d4d791a5c6a0b0c0f598be9f14d519f4d462eb9bc0b1637dad  17963  controls/controls_child.py
9ab4de210be60b7ac5b6c96b7866bd71938ae02df3e2735f32cacad6f40ba5e0  2512  controls/run_controls.py
0bbbf915507a8c7d0fa48438a13147182e420ca02389111d89fb763cf84efcbd  3334  controls/summarize.py
b3419a79c80f67969f70369133ec75de2da96b1ba63bf20c23fde96c474a57ac  9680  gold/B13/gold-output.step
307fff88b1a7369410d6f1db8b6bb82a4f65008cf5799d04df1c33132b6b0802  926  gold/B13/gold.json
8e47ac69ce79e34a251ae6f4fc9f494777f3cb7be647a954036575e0489643a2  7248  gold/B14/gold-output.step
2fa1e725abbc2e2e29f8f8fa31df654f007412e46b06163d6c70fcb9d00bfcbd  1028  gold/B14/gold.json
88ad52cc17e0861a0b554bea4898c3c62ab5e84b7e263778baca24df7d91c399  9287  gold/B15/gold-output.step
c63370c4d33c42be16efd9671761d13446c419bd38e56d5efb4a25e54cd9e4c6  1023  gold/B15/gold.json
dbd75981e5668572f3a27e88fafeb5a1423c267fbf70c9e70efbfb795a89b6e2  12051  gold/B16/gold-output.step
b06cabb99d6a19b3784e5528c90fd224e1e1f194f801c112a7ae0aa42ed757d2  889  gold/B16/gold.json
0cb210ec61ed74422d0ae6e129c405dd527ce18b371e1c2b0bd467970e30e794  13451  gold/C5/c5-gold-recheck.json
e2ad4eb99ad6de0b60c9cb6a0a4bff6a31625985790086d07c1d68a492048a13  3925  gold/C5/c5_gold_child.py
f51b3200b97e2aa1802e6811eb10bcf81abf8eead90440bf23ae2525cc54e1b8  2760  integrity-prefreeze.json
8059abb22bda83f48547a354877d13b7d64f0c8c90098cf9e972d63b4714838e  2793  integrity.py
5ca4680775b4ac7a35742e390c783b009c1ef21ceaa2caa733d10209eb80396a  9005  precision/derivation-v2.json
6e73122a8a69223e47e0db22c20df79fbe43acf8c208197394ad9043e25cc8a2  3151  precision/derive_v2.py
78f0e8538e40427bf9945144b7e76161b30e28cfe5d01077fc64be1366bd6c92  118  precision/method-preregistration-v2.first-draft.sha256
5bc9df31429f2c24e8d63f9dadcc63e658bf7776e29d50a73938dff42a86ae98  6357  precision/method-preregistration-v2.json
8c9089b84d8ee1ba765cc081dcffb1bee02c8c4e09f5dba22074ddf7572a6f98  118  precision/method-preregistration-v2.sha256
87aaddd4c631276ea58e01c8c92b3aa998828391ce83409d0847f5138f1f8195  3614  precision/reference-facts/c5-reference-facts.json
8da4b51b4fa1b340d247a67f1986f47b2e6808c5a4f52e4da283b6cd36eddc68  1481  precision/reference-facts/job.json
101ceb5c8671d763f7a1f400db4cf79a5230d54d10f93f3b54b9af245919ebaf  1208  precision/reference-facts/run.job-record.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  0  precision/reference-facts/run.stderr.txt
4e3a5b22cafa084802fe9e697ce7715e22ff2117d9687c92d8adc2037388b907  15  precision/reference-facts/run.stdout.txt
32386f9a220b17be8a4e346ee24096c377791f8213a46c2a7b887ae91470581c  1191  precision/reference_facts_child.py
4adc364cec74c6d6c866a72bc3b05a0ada62a52d135ce15a0d9f2b0ed386b7f8  197  precision/synthetic/job.json
dfcae8e4bd88fe242da5eba06d8b366be96b59565d76a9907ae24f8fad800af6  28977  precision/synthetic/raw-results-v2.json
920a3adf1165442ab5c6966058d5c1480787cd308a93a1fa207ce58b0ab28ff9  1199  precision/synthetic/run-attempt0-syntaxerror.job-record.json
a40c5e4c01efb800c0b084a0b3fd81fb55ccdbce6a87a0bb59126e8704483b14  369  precision/synthetic/run-attempt0-syntaxerror.stderr.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  0  precision/synthetic/run-attempt0-syntaxerror.stdout.txt
d9968feeeff5dff34c6778a59645ba234a58d05141a5117ac7c7fadca5db3219  1198  precision/synthetic/run.job-record.json
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  0  precision/synthetic/run.stderr.txt
d96fccfa13ee5f02c6de9156e00239f5312bc7eab269e646bc2588e9caa8342b  1256  precision/synthetic/run.stdout.txt
e191fbe46fef9f3a937ac41b1203489fe116934a63eb8cb54015009776369901  3752  precision/synthetic/work/F_fuse0.FCStd
5d56a2efb85a49e617adbb6031edd5ef6cbed7410945aeb0f3720be86a9ed477  18459  precision/synthetic/work/F_fuse0.step
df3c2c477376c700f4d360c4de40e2f7eb38d9980761fe2fb752bdb2f14ddcd6  10306  precision/synthetic/work/F_fuse1.FCStd
1eba464fe081d582f90490bdc470e835c6bb2a860cfe8632a0ae3d25ac56f488  23546  precision/synthetic/work/F_fuse1.step
6be85077b6a2ea69f9a2f02a16b96ab17e7994fc3f52b426c5c352e0f0b97fee  2245  precision/synthetic/work/P_box_a.FCStd
4d68f058e24275ef630d103ccfe8d9d6eec96347d70f7c8a772f0a362f476f00  6845  precision/synthetic/work/P_box_a.step
ff4a19ec92b1edd75a870c9f108a404efc47e934a1d81fa55d1478eb1159d428  2362  precision/synthetic/work/P_box_rot.FCStd
33f752ac24c4d733bac523fdd4d94fb5e6161a256d1d7b555e057e1662475b1b  8769  precision/synthetic/work/P_box_rot.step
8927b26202b66e2b6e2d52604f0859e3a918795817943d4a52f73abc0990f6ad  2298  precision/synthetic/work/P_hex.FCStd
61e2773bfcfe7452b40204ee8f3171a50a5acc9f52698a784fe4679407b92a91  10774  precision/synthetic/work/P_hex.step
6377bfcdc16b11bf655e7c53574abcbcf1e8f06104e007cab6c6748e3022281e  2857  precision/synthetic/work/P_pocket0.FCStd
56c9e6c2d8879f314829c6c1eba7cc4eda278f9b1c3fb2ed506c4210d11781cb  11944  precision/synthetic/work/P_pocket0.step
f865947aeef0decfdef986169e1207c226ce1a617fa2145241ab01cdd1ab5e63  2845  precision/synthetic/work/P_pocket1.FCStd
9ee4abeeec44e4671bbab3e52f05e47b24a0a49188072ce468a4e66cc57f8ded  11961  precision/synthetic/work/P_pocket1.step
8f4604463ff5d49a0adb970f6e3f8c16da53880b4a60510b8c312d2bb2b32501  2081  precision/synthetic/work/P_wedge.FCStd
b41e9b8bfe65164f7db59467f63e32772946662e9b3362e0319f04be79900bbf  7009  precision/synthetic/work/P_wedge.step
274616301bda1034e498993911c78b159f4f4d1f9f8fb79a14a1a3eeda3fc510  1937  precision/synthetic/work/Q_cyl0.FCStd
1a9e582149bc10c25535dc10f49c120924ccc2db15c08ad78ec6aedec1d649e1  3530  precision/synthetic/work/Q_cyl0.step
d893fbfab0128a3c6fd34464a4e04b6720947f7ac86173d4ae3e116e35bb7ec7  1937  precision/synthetic/work/Q_cyl1.FCStd
2d721852570b3b5b30c4519a55253d87cb1ea97cb2f340d5a5bbb2ea7c29667f  3527  precision/synthetic/work/Q_cyl1.step
f8e9c0fa69599387bb82f77f6bf89ee52229211e353ddde2e0b80bc60098021a  1891  precision/synthetic/work/Q_sph.FCStd
cf658359a3ea97be2d9c47c31d2f080c3770fe930fbcff64f0569ab648f98c43  2103  precision/synthetic/work/Q_sph.step
613f8ef2da7aeace777823231345f3fbedd15a83e020b4cea907cfc942a701a4  3090  precision/synthetic/work/R_split0.FCStd
ab7e8f2698b655b00bbaa418d52bb77d3bf12514e68da11edf3d05de99326889  18549  precision/synthetic/work/R_split0.step
e6b6b256196a50bc7719f9b11f5e7db0bab7dc2b7e2ce23972fd435eed559d66  4689  precision/synthetic/work/R_split1.FCStd
17bd82ee7b32d4c3556c91824dea8861f7504cc5ce6bf9092a6004e15a99b1c3  31018  precision/synthetic/work/R_split1.step
15a2f2605391fc59fee7b17a36bf24a0ffa4a17f25096f423c837e145ca6c10f  5991  precision/synthetic/work/R_split2.FCStd
8109884c90efe51573d74f42bc56127e87b87adebe366714f862be50afef858e  45540  precision/synthetic/work/R_split2.step
16849e96db7b0738038612058320b0b259fd2c78b249f9a41b1a41a9fdbc3c02  7745  precision/synthetic/work/R_split3.FCStd
cf8c8eb6bcb746af94742bb49750cb462c8cffdb38f5c44bcf72ded034fa0bc3  67530  precision/synthetic/work/R_split3.step
a81acbda4dc1637883e6a9718957a8ca84bbe6481c8e430f3c88f6cccb2b7f4f  4051  precision/synthetic/work/TA_common0.FCStd
8a929ee0fcd8c450466e90dbbc8b1113957a320baa6154590f036590d29b26b4  12041  precision/synthetic/work/TA_common0.step
d55163e6a709e585a3a07465104c2f997344244a24410ae7beee1a0c1e9c3530  4247  precision/synthetic/work/TA_common1.FCStd
269106c03856ac9fd730b3a183604fa59fb6ab276897b4090525da34c6cfd45c  12259  precision/synthetic/work/TA_common1.step
a0c4f9560bc8bfe4a908625704abd7474b8c32f6bcc0fdf9a8dd3b973acfa266  5182  precision/synthetic/work/TA_cut0.FCStd
25d407ea30888e0fe11b590e5004a95a2565b89561a7ea43c0c179d07ab8462d  20269  precision/synthetic/work/TA_cut0.step
f35f6c80a030db48eb39680b0cc5d78db1ca5c6566890a0485393e9fb7058dcf  4147  precision/synthetic/work/TA_cut1.FCStd
fa22e16000ceac9aa4e64d13ff247e3f3211824cc9bce01f9ace154fcbf4c9d2  18822  precision/synthetic/work/TA_cut1.step
aac1e2dd25c20dc7d2d70e957f5f13aca3dba999da9c8b0f4ff036137982f6ab  22270  precision/synthetic/work/TC_common0.FCStd
5600d60bd0ba7a26912685ec98454e8b429107e083747d27dc21c7cbd8ca56c4  39035  precision/synthetic/work/TC_common0.step
81756de5603069b155ed576cbdce1335f8af8c2d5000539f38f55fc147fb9ed5  24542  precision/synthetic/work/TC_common1.FCStd
96260997f07a3afe46825efb13dc2209641179274f12bf8c6a204580aa536863  42179  precision/synthetic/work/TC_common1.step
de9160899a5a38a476ced7506f89ebb5e379c7f13e035ddb8465bd4132bdd005  12085  precision/synthetic/work/TC_cut0.FCStd
77ed9cbdd96594797b350583bb78fde8c113a29823d43b2b975d72b3170f7ff5  30001  precision/synthetic/work/TC_cut0.step
4b8372b81188731f7d5c2d30f911673e0a0b8a1e63bf872fe4a82738630aa5e2  13377  precision/synthetic/work/TC_cut1.FCStd
5fc80e85a2f1f6ff9dd55f9fee7073220adfd5fa21a996b0600f54dd3f13b827  26415  precision/synthetic/work/TC_cut1.step
91cbdce4759e2ced87d269822a49ba448f3339c4e0c6d74e000203784b763b0c  6551  precision/synthetic/work/TO_common0.FCStd
ddc33e52a203d3f11177db9a676febfd92d0e9addc9f028a973377f2982b4147  16239  precision/synthetic/work/TO_common0.step
afa99a49396f3415bf663200bd0c18360da1e6403f8e2ad6b9a09cb6e2273b7b  6994  precision/synthetic/work/TO_common1.FCStd
3ae15e00d5ccedc1def39f37e7f20eb4adbcdc1b2414030ffcba6db1d6693cc4  17407  precision/synthetic/work/TO_common1.step
9ebacaad39db7c21e02cac2296eebd099b7bb1c7a6e508e7d2744a425a04c519  5425  precision/synthetic/work/TO_cut0.FCStd
090763a7f8f7ee801751dde16385db8c8a213bfea06fe79416886504aa54ed8c  14715  precision/synthetic/work/TO_cut0.step
2fc92f1aa615234e6b74212180fd34ac20dfd3660673fe78cd80737c680dc678  1051  precision/synthetic/work/tmp.brep
309c1a2d1fef334357018c9145902f2a14fea0f5194378080b5cec0e1da4d4c2  9738  precision/synthetic_child_v2.py
f8d94985c35859b2d653ebf9b58ff7a261c059430c7acf4151be369e2cc053dc  2205  run_pinned.py
0f37abf72e0f396e62af937b91c6ed0c07b27d42610014f3e0f40956cd562132  128  scratch/manifest-check-freeze.json
0f37abf72e0f396e62af937b91c6ed0c07b27d42610014f3e0f40956cd562132  128  scratch/manifest-check-start.json
df905f5b3402abfca04bc1a421dd5a3fa5b51a0cc660c7de04b1dfa9abc4d12a  708  scratch/verify_manifest.py
3f95d97a7958de2499eb0325c1456500d80bc389a81eb71a16501b11113f4e01  2499  stage_c5_v2.py
5de30caef1830bbb8f0b859184bec8c2f5fa155ad973c1f35a4a53722516e7fc  9654  staged/benchmark/B13/bundle-source.step
7564f058325db54ecc5af41ee0dedb59d14701d1448329949dad004aad8f1b95  472  staged/benchmark/B13/bundle.json
160ad4631fe1dba0a69f9c25bc23025d999d3b1b225b8754f298708bdaed716a  2149  staged/benchmark/B13/card.json
e9da516da8992fd07ebd031ca16a3f06af78b06b03644ce8f3ff29a8bfd1d79c  530  staged/benchmark/B13/context.json
e01c7019bb1b3b333365444b9e00432f1509ce448c0a76a7cd7fd0e44dc45490  329  staged/benchmark/B13/manifest.json
ef11889e2d4daac2a8b28e909ba640530c76c887358fa47ab8762670feaede36  616  staged/benchmark/B13/pair.json
425c8af732aa0c34e5d7e579e8e27386ece71afbb85fa12304313d8bdd0f473c  602  staged/benchmark/B13/plan.json
faba3dbb59b503cce2846f5745e82ff72e7eb92b60f56ed5fc11c7447a406f9c  8293  staged/benchmark/B13/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  staged/benchmark/B13/recipe.json
5de30caef1830bbb8f0b859184bec8c2f5fa155ad973c1f35a4a53722516e7fc  9654  staged/benchmark/B13/reference.step
76d95ce1d03f875a6c7f3cd9e975de08553b347a313255cdf24a3ac1459ecb63  177  staged/benchmark/B13/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B13/schema-shell.fcstd
f65e532a94b8576492ff3317e222f96751861b453b60eb9d65967e79b8890265  7266  staged/benchmark/B14/bundle-source.step
df2ffa13e77b121b89d9465fffb2c9ea6f69571143fbb418eb1a136085ce9f4f  472  staged/benchmark/B14/bundle.json
71973ba58fcd2830c89a3c9061848a43d7ae1ac3a0918a8edc2ab187474b33aa  2436  staged/benchmark/B14/card.json
c262dc0c1eb7c6d99763b046d256c5664d23004dd5725394ea4b61b41a82e027  530  staged/benchmark/B14/context.json
8878b678982459b7758838ff35e6a6c44e319fdca74e7a5fd57ea5f9ac90853b  329  staged/benchmark/B14/manifest.json
42b0d19acc710f7d604f334424dc93dd5c8ff59a0d75b65965000d71c5898475  616  staged/benchmark/B14/pair.json
77a7b6e528dc947af730d6213173bd4087ecf2afcfe7a6fe58b53d45faa94cfb  571  staged/benchmark/B14/plan.json
d441c6e0e6a29052db393b42e0979a9196bc792d54102d1d8040e90f2786e209  6620  staged/benchmark/B14/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  staged/benchmark/B14/recipe.json
f65e532a94b8576492ff3317e222f96751861b453b60eb9d65967e79b8890265  7266  staged/benchmark/B14/reference.step
02a766a2fbddb17d0b84ba7e5d7e4d1468bee37d466fec591702ce1cb54d0403  163  staged/benchmark/B14/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B14/schema-shell.fcstd
84f19514cfab90a0b3c0db03808f9dffd7b416c0a956bd61718780d058d19850  9279  staged/benchmark/B15/bundle-source.step
e9d1df7139f92097c9488321cd0ece5a5f6139a01f687013443f3d9491666c78  472  staged/benchmark/B15/bundle.json
c23708dbe320187c1c8634f0dfd39833944789f43998d305e07f2d8a93423a4d  2411  staged/benchmark/B15/card.json
0d446df2a84cbe493e5c7a5f8222292e35c3694529f8d927c6f3dc7b40f15d9b  530  staged/benchmark/B15/context.json
cea677a5b46309dc62a6a77f75098626e7b8ed3fa6a3dda839caf4e22522da6f  329  staged/benchmark/B15/manifest.json
582bd89bc34391c8b9e358d62b28858e613ba79ee1282f6fb89be7ae2806a44a  627  staged/benchmark/B15/pair.json
f969e9f88dd164a8f8bea868060ec34d1661c3d840d8bad9956f7716acdf5b13  571  staged/benchmark/B15/plan.json
2bff41ba416f5768af382dda169320a8193f6cdd3fe6540e32d3f77ae2b798ba  7864  staged/benchmark/B15/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  staged/benchmark/B15/recipe.json
84f19514cfab90a0b3c0db03808f9dffd7b416c0a956bd61718780d058d19850  9279  staged/benchmark/B15/reference.step
aea01a960656356af2b40a3ebe67946a23874476f8c93e84858b3bf4fef80364  207  staged/benchmark/B15/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B15/schema-shell.fcstd
049cada40e196a42c67b1ab6c8a20daf1ceed263fd6f3fa235b9a300a741014d  12044  staged/benchmark/B16/bundle-source.step
106f68a07cf71a8ff34227e26afac3168e01b221057d56272f0a8b9d117848da  473  staged/benchmark/B16/bundle.json
804dd0cf0bfaddf27f38ef48327fdaf82a37eebbcb18cc7aaa3619adef720046  863  staged/benchmark/B16/card.json
ae28b1e7f3951aea94d4f0dad83a85bc21aab58de716a27376de735087b58f23  530  staged/benchmark/B16/context.json
bce622c24dffc9af6ffdf127c06c179cc17fc1470db9fb0113dc27ac484abc96  330  staged/benchmark/B16/manifest.json
0cf6f759cca45672283b440bcd27a86ed9c44642f4c2bd1cd08ba1dbd372c14b  614  staged/benchmark/B16/pair.json
74f1ce4221b75f36d58c7183286246078f9daed33c6bcff46a488a60be36a3ea  574  staged/benchmark/B16/plan.json
4adec95fbe2d3e609657b47fba3aae1dcfb2c539a273f3e1450b0a699ca333a3  10195  staged/benchmark/B16/prepared.json
530ffc635b92aae66356bc0e9cc66ca3ce4aad61231acb64c26222a8741b816c  176  staged/benchmark/B16/recipe.json
049cada40e196a42c67b1ab6c8a20daf1ceed263fd6f3fa235b9a300a741014d  12044  staged/benchmark/B16/reference.step
41923ab40f27f1645b242d2129e74c4f3b068206e918bf0f0ac1023d1cf75f0c  99  staged/benchmark/B16/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B16/schema-shell.fcstd
11ea4448789f8cc756e556164c672dc2e38c1d09cadd19423eb3bba0fc404e8f  18753  staged/benchmark/B17/bundle-source.step
1f2a46b2d5cc9cb434ad9befdbe3240e05c0e2d5d2b1da9399753c953efb9e36  473  staged/benchmark/B17/bundle.json
bc91a92c3e30e2513e5a99354d2305e4c70089fc48208bf6233279b4c4730b59  2786  staged/benchmark/B17/card.json
689a6c3e1da2f782339bc3fa19514731e82a4e2f59570a748be8d18d9b6c5a4a  1283  staged/benchmark/B17/context.json
d4f62c899ac873e6285d0b717b43e2d082f5eec4df2571edb151f259a42dd971  330  staged/benchmark/B17/manifest.json
ddfa6898132f8894ddffcde4e9a7a1a22877aa3ef9ef7850c9ce680c35716914  611  staged/benchmark/B17/pair.json
15d19641684c8896c7b56dd8b00c17432767fe5fd473c1fb0e1fee70de0a9956  1021  staged/benchmark/B17/plan.json
5a35552424fcfdb534273abfb29d4a4f9e4090d61d9a90029213b149dd92651a  19023  staged/benchmark/B17/prepared.json
11ea4448789f8cc756e556164c672dc2e38c1d09cadd19423eb3bba0fc404e8f  18753  staged/benchmark/B17/reference.step
d55aff543c2f831e2dcd95f3e6ef6589d578686a97ce0bccb0c4caad0d6ab20d  154  staged/benchmark/B17/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B17/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/benchmark/B17/step-recipe.json
80cc1cdb3a6d3f4a03c99f951bbaee9ae120922f5eed97b7de911b8d452584b3  18099  staged/benchmark/B18/bundle-source.step
cc8c3f3fb834c887ee40fb6cac9708e931e700db7a5d3245672d5c69f7c6eb47  473  staged/benchmark/B18/bundle.json
a1de62e07a85890b81b8d1bade21a139d62fb26cdc85b9a2f927ce10f27a56f2  2764  staged/benchmark/B18/card.json
bdb74b9dd6764f664130b25406078948d8729fc287303c220d3be31009e475ff  1283  staged/benchmark/B18/context.json
88f3855375650e10a1a72dd645f03467cc916ab1ccc2ec66a22a95ecfe00a324  330  staged/benchmark/B18/manifest.json
1626eba716ad908875e9b1970d650063f0436f5a8e297ddf88ef369746fe7aad  611  staged/benchmark/B18/pair.json
ff0f3372ebe0d6d39be1787222c4c1c7b69fb6c43c621ea27b18c20ed9c4161b  1021  staged/benchmark/B18/plan.json
a3a8c9c09a1dadaf9d65da2b475daa048559c3fc6705d819208ae3198c1b756a  18790  staged/benchmark/B18/prepared.json
80cc1cdb3a6d3f4a03c99f951bbaee9ae120922f5eed97b7de911b8d452584b3  18099  staged/benchmark/B18/reference.step
504a884636acfeed4b35b8d1ef52686b72894f6a1f8b3337cdb57c8a02e36c2f  154  staged/benchmark/B18/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B18/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/benchmark/B18/step-recipe.json
8a8b2bf232be006edac1831dd96f74985ab24f61a8ca54170419a82141d4d991  31712  staged/benchmark/B19/bundle-source.step
7d004de19705e532a1031dea6fa9af3878a0ce8da33278916b787e372d0f352f  473  staged/benchmark/B19/bundle.json
78c59d79af0887bb6521b5ccd3c8882bcb32bda895de8e66b8ccd8138f9b435d  3178  staged/benchmark/B19/card.json
b5444ec9d2f695174bfcd81c65cf398570e45f369396294b583d82730a60adf7  2023  staged/benchmark/B19/context.json
7823c5c58c6586f79927dd30510c0094090a8338d5c7f59e8fa5d075e1395cef  330  staged/benchmark/B19/manifest.json
5bbb51d4382a04003a7b55ee6a5decb05926ab3db060f0484c02194599fe6f7f  621  staged/benchmark/B19/pair.json
124e4f0dca825bee2139776ba47e3fcd669d713801cc47b3d3bfad37e3c4ad04  1705  staged/benchmark/B19/plan.json
68e788144252ebd1338c1eada16571be5478d7073d3f52b9519e92058cd73274  29576  staged/benchmark/B19/prepared.json
8a8b2bf232be006edac1831dd96f74985ab24f61a8ca54170419a82141d4d991  31712  staged/benchmark/B19/reference.step
23c3f717a9aa0d97ba5a7592ec81a9ad366fef63ab6b1c0dbcc5cd9acac12fba  164  staged/benchmark/B19/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B19/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/benchmark/B19/step-recipe.json
3cd82d042bb3b476f0a50b850cbf687baefb7393c0297ede691be7de936ac651  31981  staged/benchmark/B20/bundle-source.step
839c90dbc7cab65b37ab14ff335ed4634c3ce8f1735aa8e396672d660f758196  473  staged/benchmark/B20/bundle.json
3166b5699522316f3522c89f04f006262c09a56f5342eeb0a5356bec5275e166  3246  staged/benchmark/B20/card.json
b818a07918cb96b0c21b19cb39469610e9c38fbffaaee620b860ed99209d4192  2023  staged/benchmark/B20/context.json
aedbcfa9759462eb07bee5647c95380d77c1bcd5ad299ef86055deb1ac38c211  330  staged/benchmark/B20/manifest.json
e3937534a62c277d0d46bdc99e7cb7b91ecd6ef2526672c40eff1cdb59e6848b  621  staged/benchmark/B20/pair.json
e5a357410b531da8647d0bdf0a01214a95f4649eaefdcfd8add92ee1f2ea3590  1705  staged/benchmark/B20/plan.json
ec5f4ed67ac1f46c1afde64161f993c8aa466850da2b5b7a94a47b9f1073a803  29231  staged/benchmark/B20/prepared.json
3cd82d042bb3b476f0a50b850cbf687baefb7393c0297ede691be7de936ac651  31981  staged/benchmark/B20/reference.step
212d88acfdee6a34a3cfd72e919fbbb10ebe87dbb1ca1dc724fdb50fd77c45b1  164  staged/benchmark/B20/request.txt
70c204774ec667130daae32a4de006225dba4fd4f27ec04bfad1f399413b71c4  190  staged/benchmark/B20/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/benchmark/B20/step-recipe.json
c009c6cd06995e8b7389a89a068af07d6b5c953280c711e0b10cb03ebd37a0b0  18476  staged/generative/C5-01/bundle-source.step
6c3715e72437bfde20ad130531f10020b78b2dbb2c2d5c42dd24af7d62fce645  473  staged/generative/C5-01/bundle.json
508e3917dc809bccaa57da0e988b2f5636328c57a0ef65ccbae9ade8ab7609fe  2739  staged/generative/C5-01/card.json
3d5bc30559354a920df36b0d1ab3aabdc5c0e9baa07192929d77aaba3c67456a  1283  staged/generative/C5-01/context.json
17cc2325315392edb783d20ce8a303201b311106b345a1a892a9baa5094fd4b1  330  staged/generative/C5-01/manifest.json
e3f16c82689e06e4c4343e3337c66fa9b1edd220509cadf7e343fbd0a808e5c8  1021  staged/generative/C5-01/plan.json
1f1e42ed91c2773ba98cdc6e5fd9e1a8c9509e0198bc3c9f20303749ff6b553d  18620  staged/generative/C5-01/prepared.json
c009c6cd06995e8b7389a89a068af07d6b5c953280c711e0b10cb03ebd37a0b0  18476  staged/generative/C5-01/reference.step
f446dd2211be35e901a73546afcfb5b481d31988ea07b4a10feb801a625e71a6  156  staged/generative/C5-01/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-01/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-01/step-recipe.json
4acc6f7da8c65718afada97a53d5daebdd325426b66604727a363a0da9cc8cda  19417  staged/generative/C5-02/bundle-source.step
e2879c8f6ea850cd52561b643689828f0935c8177dee3e41f320d76e9140d05c  473  staged/generative/C5-02/bundle.json
4d718b2c06bb849ed8df49898f5e70a41084d4f9227b27e98e3ec76458df4221  2788  staged/generative/C5-02/card.json
51918f4e039232c2cb3b78f9b3d4ef81e61cb0cee0e61d8d476784103d01a293  1283  staged/generative/C5-02/context.json
28a926c0227b16edf63911eec6f45a75a9087f394f654c26aa783013bec8f0dc  330  staged/generative/C5-02/manifest.json
1b420a1da62e3b949fbcded1a30e16bba39541c6017ba104e023fbfd9b560de2  1021  staged/generative/C5-02/plan.json
929e7cf20537ac48f43d96352114c14a9d2f0a474ebd066fd3c8cd001e12fadd  18800  staged/generative/C5-02/prepared.json
4acc6f7da8c65718afada97a53d5daebdd325426b66604727a363a0da9cc8cda  19417  staged/generative/C5-02/reference.step
643e6ce13e0b22f76f582a74d0c7d98ddd2589c5ed23b9ecec37c721d2d6940c  156  staged/generative/C5-02/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-02/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-02/step-recipe.json
443b73de98cd88e8da9e41cbe254892629aa5024680240c69d0c618db09018fe  18677  staged/generative/C5-03/bundle-source.step
d65b8c041429223d229963a061455c7fdecd41d7f878f101afd30131106e1bf8  473  staged/generative/C5-03/bundle.json
5d3e0edbd3b43f57d1de8d384fbc5e446942d2690eefd136088f226faaec383f  2761  staged/generative/C5-03/card.json
a24f860e7cc27c0ccb7d45b831def4c05c5dc1855dd4fe3a894b6b5446787d05  1283  staged/generative/C5-03/context.json
a669fedfd479c98d402136366674c90f44900f5458d573da1514ddcc6c6cd1c5  330  staged/generative/C5-03/manifest.json
b2704f2624d891db6d2e9b912a4024d62e3e795c0d0871f2fdb1b75541c42abf  1021  staged/generative/C5-03/plan.json
17efcc6d7e9c4ca9aebf56484586190df54706fa99d7f288f9dc01f6b590f3de  18774  staged/generative/C5-03/prepared.json
443b73de98cd88e8da9e41cbe254892629aa5024680240c69d0c618db09018fe  18677  staged/generative/C5-03/reference.step
0f032da3995dfe67b3f7352bd78d871a667e6b4d12e4cf3d430ec4885a19e440  156  staged/generative/C5-03/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-03/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-03/step-recipe.json
0b11c5c1439398f9f48157e4dfbfd01391a8b2050ce0b0334a637d119388df33  30478  staged/generative/C5-04/bundle-source.step
9da6732fb120c70400bb9400eb69c644488282a22d1f9df9c0c9cae6f82284f7  473  staged/generative/C5-04/bundle.json
97c76c6d49b652231cffa2abac12d8472051dff36a367e443f8bf16c2b1be008  3200  staged/generative/C5-04/card.json
21eedae322031f5ef3ab76dadd87c81ab3e527d164da0a00656a6092e64ba7c9  2023  staged/generative/C5-04/context.json
41877089c71f7e8c32efc99e2a5cf4182da602b53dd5e58c8c0fd8038a23bb70  330  staged/generative/C5-04/manifest.json
147af68d271d075d9f62da2382a5871480eb7e1c4ad379d621c625e58094d890  1705  staged/generative/C5-04/plan.json
1d7ebf1ade2470d1e7284a4c93d21a56206deb7bde589089513f114774e1a180  29288  staged/generative/C5-04/prepared.json
0b11c5c1439398f9f48157e4dfbfd01391a8b2050ce0b0334a637d119388df33  30478  staged/generative/C5-04/reference.step
6d9a4dcba763b90c31bce83186b5473c69e2e1fecc38bacb542994b757613107  166  staged/generative/C5-04/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-04/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-04/step-recipe.json
afe05577681cef2b85e4ccf9e4752e47032cc1423c82abc1b8c3fdfe2263e42d  32038  staged/generative/C5-05/bundle-source.step
2abb6ddd5471f93650d126c0b020ad43b80dcabd72f7cf4d76ff4098bf9205cc  473  staged/generative/C5-05/bundle.json
629a7b6ab4b500f0a9cf302c68ba75a28be9bcaba703ae358e2166310085ed68  3226  staged/generative/C5-05/card.json
3682f3f93ef9a5151fa5101fd4fa0165afa7b4da1cefd314580a1e5fbb9ad3b1  2023  staged/generative/C5-05/context.json
c2d0983795615b1375f039d1be534b1eee850bb27471ff52f2e2888d6aca6140  330  staged/generative/C5-05/manifest.json
57c721840019c5c4c1f41c94d2326a92b6862b95e4e786cae8fbf1f60608a581  1705  staged/generative/C5-05/plan.json
d2b095b251962b00ac836635f8d57c3a5e765e5c03508f9485672e21fd48dc75  29662  staged/generative/C5-05/prepared.json
afe05577681cef2b85e4ccf9e4752e47032cc1423c82abc1b8c3fdfe2263e42d  32038  staged/generative/C5-05/reference.step
87eba8cd3d4a2b309832813660f3b9ea9b612efaf93403a6bdd1532285abaac0  166  staged/generative/C5-05/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-05/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-05/step-recipe.json
a244e806cb029eb4fc0897356e2741b76020df791906798e711f6652a260d9af  31654  staged/generative/C5-06/bundle-source.step
bbe6904bdbe28dc0c3cc18b111395f749001d004bb04a2ffc264849444ba9f60  473  staged/generative/C5-06/bundle.json
648fe5522e6472ca0fcb50ee8edf3cee62ce5c6586572d63ba433e73a91ec870  3178  staged/generative/C5-06/card.json
5c86747be9a63f6d6ffd61e07fad243aea347bb3572950113ee443c31a1a9711  2023  staged/generative/C5-06/context.json
0aa62a80c84716e594e5c99cb146cc9d5892d490b1f6ce746dcae2bc768b890c  330  staged/generative/C5-06/manifest.json
c81d8b495f173a28b99af4083854ba71cf965cce0b240b753913b5035d7932d2  1705  staged/generative/C5-06/plan.json
d80b66a463ff7059f99ddc80d6b04c91c967fc3e7f89ee5058caa0f66ea39554  29343  staged/generative/C5-06/prepared.json
a244e806cb029eb4fc0897356e2741b76020df791906798e711f6652a260d9af  31654  staged/generative/C5-06/reference.step
bdf5e2fafaa00e58ee423d9c358394aa9ba50709c689e6f21e274cb89fd1128a  166  staged/generative/C5-06/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-06/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-06/step-recipe.json
bfca140ad16e8de8a355135af037bcf05c3eeca0751d6b377c362cd5a15fa223  31702  staged/generative/C5-07/bundle-source.step
56d5018d9105b476f8279a745011f606d4da9c7cbf41d415a4154d36203e6d71  473  staged/generative/C5-07/bundle.json
b2c19afe4a975fcd3eabec57fbc3b683d7d04b56e56a3e17634fd4b19aab2fa6  3200  staged/generative/C5-07/card.json
058083dd99a32a876ecad52334b9b7b1efcd58a8e22a85955cdc0edd2bb6b32b  2023  staged/generative/C5-07/context.json
07907d52aa90e71791d46db81433454e91f94419726185d9df095b62bc18b86f  330  staged/generative/C5-07/manifest.json
f8b13e9366fd3b7edfc439b0b31487b0a0e524ef361c9e3a351054feb94e311c  1705  staged/generative/C5-07/plan.json
a7ed76e3ea714fe80cd3e6a0860b125c8f0e72126744e11b23438ea194197fcb  29596  staged/generative/C5-07/prepared.json
bfca140ad16e8de8a355135af037bcf05c3eeca0751d6b377c362cd5a15fa223  31702  staged/generative/C5-07/reference.step
424746534c6f9a86f85ae9f9843e857853e15a477e223d75ff0b6a62eedbae94  166  staged/generative/C5-07/request.txt
80d0e5ca53d6086e010ce0368aed02be8c8ef839558918fbee03b6f55af618d3  190  staged/generative/C5-07/schema-shell.fcstd
482ba4ef594c006be075f63c73e73f08e7bb6c413e4a39be072febbcdf902879  176  staged/generative/C5-07/step-recipe.json
f1b51a201c5465d4181bcb50ca27653cf4692bc9f8bb40ac564510b4696e363b  3269  staging-log-v2.json
```
