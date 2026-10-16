# Original holdout commitment - v4grok

Custodian: v4grok, sole holdout author (option B). Private tree: `C:\dev\v4-holdout-private\original-v1\`. This file is the public record. It lists counts, strata, schema versions, admission-control results, the call ceiling, and SHA-256 identities. It contains no item text, coordinates, rubrics, or answers.

Live calls: 0. Model generation calls: 0. This file is not a live authorization. `authorization` stays null. `final_v4_ready` stays false. The admission results below are the evidence a later authorization record can cite as `independent_control_validation`. No authorization JSON was written.

Worktree HEAD while this commitment was written: `6788faf53601443b23b21ad40f53d5a0bde001c8`. The loader used is `tools/cad_verify_v4_live.py` `load_cohort` at that HEAD.

## Counts

60 entries. 51 scored. 3 unscored previews (dev). 6 completion, unscored. Planned calls 83. Maximum calls 163. Profile `original`. Scope is the unchanged v3 allocation. No C1-C5 capability items were added. No calls were borrowed from the family reservation or the benchmark envelope.

| Group | Entries | Scored |
| --- | ---: | ---: |
| dev | 3 | 0 |
| legacy | 4 | 4 |
| mvp | 10 | 10 |
| geometry | 18 | 18 |
| q | 13 | 13 |
| completion | 6 | 0 |
| fault | 6 | 6 |
| Total | 60 | 51 |

## Allocation

Rounds of one case share one request, one acceptance card, and one route. Bar class is the private scoring alias. Dev and completion are unscored, so their bar class is null.

| Group | Case | Rounds | Route | Min | Max | Scored | Bar class |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| dev | D1 | 1 | source | 2 | 2 | false | null |
| dev | D2 | 1 | spec | 1 | 1 | false | null |
| dev | D3 | 1 | ask | 1 | 1 | false | null |
| legacy | A-good | 1 | offline | 0 | 0 | true | A-good |
| legacy | A-broken | 1 | offline | 0 | 0 | true | A-broken |
| legacy | B-good | 1 | offline | 0 | 0 | true | B-good |
| legacy | B-broken | 1 | offline | 0 | 0 | true | B-broken |
| mvp | P1 | 1,2 | mvp | 1 | 3 | true | P1 |
| mvp | P2 | 1,2 | mvp | 1 | 3 | true | P2 |
| mvp | P4 | 1,2 | mvp | 1 | 3 | true | P4 |
| mvp | P5 | 1,2 | mvp | 1 | 3 | true | P5 |
| mvp | P3 | 1,2 | mvp | 1 | 3 | true | P3 |
| geometry | G1 | 1,2 | source | 2 | 4 | true | V1 |
| geometry | G2 | 1,2 | source | 2 | 4 | true | V2 |
| geometry | G3 | 1,2 | source | 2 | 4 | true | V3 |
| geometry | G4 | 1,2 | source | 2 | 4 | true | V4 |
| geometry | G5 | 1,2 | source | 2 | 4 | true | V5 |
| geometry | G6 | 1,2,3 | spec | 1 | 3 | true | V6 |
| geometry | S3 | 1,2,3,4,5 | spec | 1 | 3 | true | S1 |
| q | A4 | 1,2,3 | spec | 1 | 3 | true | Q1 |
| q | A5 | 1,2,3,4,5 | ask | 1 | 1 | true | Q2 |
| q | A6 | 1,2,3,4,5 | ask | 1 | 1 | true | Q3 |
| completion | C4 | 1,2,3 | completion | 2 | 4 | false | null |
| completion | C5 | 1,2,3 | completion | 2 | 4 | false | null |
| fault | F4 | 1,2 | source | 3 | 4 | true | F1 |
| fault | F5 | 1,2 | source | 3 | 4 | true | F2 |
| fault | F6 | 1,2 | spec | 2 | 3 | true | F3 |

## Schema versions

- Public commitment: `cad-harness.holdout-commitment.v4`
- Released cohort: `cad-harness.holdout.v4`
- Acceptance cards: `cad-harness.acceptance.v4`
- Order checked by the frozen validator: `cad-harness.verify-order.v3`, profile `verify-v3`
- Checker gold: `cad-harness.verify-gold.v3` for source, spec, completion, fault, and dev source/spec; `cad-harness.gold.v1` for mvp and offline
- Ask and completion rubrics, inline on the card: `cad-harness.verify-q.v1`
- Fault rules: `cad-harness.verify-fault.v1`
- F6 candidate: `cad-harness.build-spec.v1`

## Admission

Controls ran offline against the released bytes. No model process and no live transport ran. Native checks used the existing FreeCAD 1.1.4 fixture and probe tooling.

| Control | Result |
| --- | --- |
| `load_gold` | 24/24 |
| Description bytes equal the request, except completion | 24/24 |
| Completion binding (request, answer, full description) | 2/2 |
| Rubric `q_score` positive | 5/5 score 1, invention false |
| Rubric `q_score` negative | 5/5 score 0, invention false |
| Rubric invention trap | 5/5 score 1, invention true |
| `source_contract` on offline scripts and source-fault candidates | 6/6 |
| `Fault.inject` reached and hash-bound | 3/3 |
| F6 build-spec schema, correct spec and candidate, before the correct spec was dropped | 2/2 |
| Hash intersection with v3 test/dev and mvp eval-v1 text, json, and py | 0 |
| Hash intersection with `families-v1` | 0 |
| Native fixture probe, every released gold | 24/24 pass |
| Offline good scripts | 2/2 pass |
| Offline broken scripts | 2/2 fail (A-broken: volume, pockets, editability; B-broken: volume, holes, editability) |
| F4 candidate | fail, predicates include volume |
| F5 candidate | fail, predicates include volume |
| F6 mutated fixture, spec not compiled | fail, predicates include holes |
| `load_cohort` at HEAD 6788faf | pass, 60 entries |

The unreleased F6 correct spec was deleted after the inject control. It is not in the cohort file map. The released F6 candidate remains hash-bound through the fault card.

`independent_control_validation` evidence: pass. That boolean is not an authorization record.

## SHA-256 identities

Released cohort `cohort.json`: SHA-256 `45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65`. Bytes 37412.
Public commitment JSON: SHA-256 `d87165cebd273de13fc1e7796cb2bc58fffb4e88a6d1f71665194d8866493a7f`. Bytes 1069.
Released file map: 90 files, plus `cohort.json`.

| Path | Bytes | SHA-256 |
| --- | ---: | --- |
| cohort.json | 37412 | `45bb80a58c4c692a16b2039bff576f9c8db582ab1cc66ce48aed3bd4a3258c65` |
| completion/C4/acceptance.json | 703 | `dd160188a2db14da94f3cf0c49a17cdfa2c3d0120e4fba928beee05f1061243b` |
| completion/C4/answer.txt | 16 | `61d6d7f512fdd6dd23bf266aeb7c66805192f2e19aa4b66bd5f55194bed95499` |
| completion/C4/gold.json | 2332 | `6c4d659e71fc16355df58def8e09d96aa7ac3b63d7acdb9d25e391038e98b002` |
| completion/C4/request.txt | 142 | `bc1b556c1f1c272efcd04df98d8035d86346d3e2219b345a36ba13373aa503b4` |
| completion/C5/acceptance.json | 711 | `d6cb9f2bb373638923fe75a59efdb4971764b20b10ef553ad3b57993bf5c2463` |
| completion/C5/answer.txt | 27 | `bcc7f845f14039c41dba168784df360565e49429d9796406ddd166f6b10e77ca` |
| completion/C5/gold.json | 2353 | `45daec27697899754021c5b18bfe3a3733eeab422384714a8b1dd2bf0a2cd56c` |
| completion/C5/request.txt | 157 | `61dc883a33c2b99577f878a06b2ea44e52d864bf9c070193ac61adcd3871d284` |
| dev/D1/acceptance.json | 220 | `58ae3b2d9a4104b58cbccf6ea494d84d210943388daeebac556284cfe85a55a3` |
| dev/D1/gold.json | 2022 | `88abe7939d33093e9dfc4ecc7f3092c30d5234ca7f1c3639e6cbf85ceab69fbe` |
| dev/D1/request.txt | 182 | `d9eb560e336029072752900e37a4305ca3ef6a7038a6f3dc79b9ebb2ff07e043` |
| dev/D2/acceptance.json | 218 | `a900e1575fcc4d8cd1fbcec97cafbbdf5f7c39bf0322fddd0053d48b8f066e92` |
| dev/D2/gold.json | 2200 | `fe7f4fc1c10fb7e869f7b249b20cc1a973d9fb7025ee8abc1dee4bb17c643d93` |
| dev/D2/request.txt | 132 | `2c5e61390a93b524186bf45d95954356ca0c753daba98cb9dd928c020f67aa51` |
| dev/D3/acceptance.json | 643 | `0a81a861cf4cea7a3793eb431eae1461e4c421c7bdfb1de80bebaa16a6b6576d` |
| dev/D3/request.txt | 128 | `fb367010e57143b458039b1bfe59b8c02cba7212d6035b0065f1ab7a34015df2` |
| fault/F4/acceptance.json | 237 | `a7ae724e1a65305a2b5943a9c31968c642f864e09cf0702e44012e34ce275c58` |
| fault/F4/candidate.py | 695 | `be313e5f83c208a2e06f8725268989db1117b53dfab576edf8ef8da2fe168711` |
| fault/F4/fault.json | 195 | `c5322f9841b46cebc972523476d5d5a02c34f412793398b77f24542e69dce969` |
| fault/F4/gold.json | 2018 | `dbd27e18060efbcb13bf88017d32ec46dacd31d044019ad8379a53569c5a1405` |
| fault/F4/request.txt | 181 | `8e672f760e65047e42b9ebe9d82d753611bc03a9acacd32e6efab31b3d716ad4` |
| fault/F5/acceptance.json | 237 | `8afd4c251e50b2a91b73972cca62cfe43391bbf1797ee471b0799127ebdb8521` |
| fault/F5/candidate.py | 883 | `60f16361c2a36b961880ec323406ac290fbfdc11c51ad24b603c89b8917976ca` |
| fault/F5/fault.json | 195 | `1522b33e8bb321d0844ba9f5e42d1b907a931f22077ea25f811e8d980518c186` |
| fault/F5/gold.json | 3806 | `549e2db5b9eb7fb3ec5c07d0234b2d2fb9cce389c5d98d52de8f66b95da8715f` |
| fault/F5/request.txt | 275 | `c7c77b378fe6bfc10d4a4afdbe22e2368448531ce78585d68b547738cf1315ed` |
| fault/F6/acceptance.json | 235 | `948cfd2173aa36d19906465aaf839c2b1ec2442519f208fde6acc2fc7aab6338` |
| fault/F6/candidate.json | 939 | `00f4e796bf88940a875395c0fae793583427997c1e3fc24b45d0d986e18a272e` |
| fault/F6/fault.json | 377 | `00204f55668bfa6a55526c96c03cd129ce2205f41a7d032e2681176a99ff4c35` |
| fault/F6/gold.json | 3735 | `a78c0cc1ea6dcc8ed8047f6b18f91599dd2a173f4e6e43b0de61b31facd15966` |
| fault/F6/request.txt | 201 | `43a788e7bf8b781c772c9edb5553a429490f2e2589f10f3b37e1dc1ef3de5e92` |
| geometry/G1/acceptance.json | 206 | `df80eaea0789ed11d34b0620889206088a302bab7f2ef892f8a5a2d651b0960c` |
| geometry/G1/gold.json | 2018 | `bd46988534a2ac3cb65e719d0e0199d723a52102930bb92ca7ed1773815dc76a` |
| geometry/G1/request.txt | 181 | `8e672f760e65047e42b9ebe9d82d753611bc03a9acacd32e6efab31b3d716ad4` |
| geometry/G2/acceptance.json | 206 | `8409233b6688f8e4948a4fc02d7611808cf43df84b21ffa6a83df28e9f76c710` |
| geometry/G2/gold.json | 1771 | `4ad7950d5536635dbfccb5429ba23d8ab41100ba3c978e7ad66b1ba1b84b63d8` |
| geometry/G2/request.txt | 188 | `1b63635cfd654cb424c0462b35b86fb583a0f642f75d5db51e71281e62935d20` |
| geometry/G3/acceptance.json | 206 | `8da39e98d42d03763d1316382a9b27fce79e649dc77a13b645c6417258e4eded` |
| geometry/G3/gold.json | 1552 | `5941fd67b02c36abb6162e15a1629c58665993a4597fb4bbdf972692ab158153` |
| geometry/G3/request.txt | 220 | `92f6a52dd25fa4f0c3c62272871d502a70209c30e06eee6d227f12f0490407d9` |
| geometry/G4/acceptance.json | 206 | `8b779a01537c2f75eb8705159a54a6c92b4a4a3819b8703a71e1019debd6de8b` |
| geometry/G4/gold.json | 1991 | `d6e6950cd4533a8cabad837716a06ff4a616e9c11d722d57adfa5035ae83d692` |
| geometry/G4/request.txt | 257 | `28fa57846a1055e10a9782278d6bd0372d26f2dda4e3737781e53977c4d0e3f8` |
| geometry/G5/acceptance.json | 206 | `116bf26f5e73e773f125db912376a7332b944aa5f4f1a4952734ecb4a6878e31` |
| geometry/G5/gold.json | 3806 | `8835c5b4ec6052b5c36e79bb3843f9211df5fee081a58b8d46537e55771d56ce` |
| geometry/G5/request.txt | 275 | `c7c77b378fe6bfc10d4a4afdbe22e2368448531ce78585d68b547738cf1315ed` |
| geometry/G6/acceptance.json | 204 | `0c5f99ce68c297ec776312f02312ee787584142fe81688b5cd62ef0b6735290b` |
| geometry/G6/gold.json | 3735 | `136c0ebd5e63036558365f45e6ac5ea3b8a5af73afc08085e290bc0b2fb9a0f7` |
| geometry/G6/request.txt | 201 | `43a788e7bf8b781c772c9edb5553a429490f2e2589f10f3b37e1dc1ef3de5e92` |
| geometry/S3/acceptance.json | 204 | `cbfa1f3e280c647ad0a068c69facd156d7126682ada5f94e03106635b408cebe` |
| geometry/S3/gold.json | 2327 | `8c37abe588a34e09695cbbca26c8730c8a42a273cbf6a7713139ea1751c81b12` |
| geometry/S3/request.txt | 139 | `b6cf7bb295cea214f1f1f11501bc426bdda2b18fca9b58256992b9b0e38a3719` |
| legacy/A-broken/acceptance.json | 274 | `ebf90776b8f75092277c6d99d775f0b2bc0a4de656e53722dbb43318bade6cb9` |
| legacy/A-broken/gold.json | 1269 | `70a5d9230acdb64a035f1e7944e67cf208844cba7f3c8ef8d3027a9f165b7003` |
| legacy/A-broken/request.txt | 141 | `1086a2c2b987a9ea424b8b7e3642f30386acd04e79a539f91989c5ea296e8474` |
| legacy/A-broken/script.py | 2907 | `7abed09df18adcb2576c3cf6deb343498c1133f274b15d3d77f8ac657611a963` |
| legacy/A-good/acceptance.json | 268 | `e90b6e37b4cdf4991f10fde311d45279a33ff2aa61f6017cc12b5049116b661f` |
| legacy/A-good/gold.json | 1267 | `9a51e7767b30223447f8d635a2df43522f9daadcc1733d75c8ef836a2b75898e` |
| legacy/A-good/request.txt | 141 | `1086a2c2b987a9ea424b8b7e3642f30386acd04e79a539f91989c5ea296e8474` |
| legacy/A-good/script.py | 2973 | `ebb809d3066deedd4c1040c5d24a8c5910bc309104fa159be18a02bfce7f295e` |
| legacy/B-broken/acceptance.json | 274 | `c6625b0c14ce37a86389e73d6fd8a54d9ad12aa71f77ced4606ae983aa599711` |
| legacy/B-broken/gold.json | 1423 | `5042aced91eb4d9f8d8651db3bfe65cf661e7a53fb4edf24c853a5ea18136232` |
| legacy/B-broken/request.txt | 144 | `32a81d9ed3ea2bee41f5b3cf6f941a776e367581dcb94ab98d0258e47c16b5a6` |
| legacy/B-broken/script.py | 3043 | `d1a2ac3711fdc95af94060993ce67d5f979198315373c4d7b4d796f314f2be7e` |
| legacy/B-good/acceptance.json | 268 | `388f38ae1065047cb06df6b1b497e61ce4ce8c4907ac2cd23cf5a7cb57f5fa26` |
| legacy/B-good/gold.json | 1421 | `6554087b535df32292c3cf7a910c2eb6e4b1708183e6fd8d0ca602a786473c86` |
| legacy/B-good/request.txt | 144 | `32a81d9ed3ea2bee41f5b3cf6f941a776e367581dcb94ab98d0258e47c16b5a6` |
| legacy/B-good/script.py | 3043 | `a22ecb3610e02df68eabd1df2a847ce532cd76d9ee3123f06fb19a75a88d1a30` |
| mvp/P1/acceptance.json | 198 | `50101ff08471f38e8543fe4e7b0dfb4eba47d670a80bb662039f10f72b7ab49d` |
| mvp/P1/gold.json | 1265 | `a4072d82ab72601c054350f6f286410fd7e09552e8c92e5990140c3404131c6d` |
| mvp/P1/request.txt | 141 | `89f012ca87c403275663ac7e26c9e7931ad890687b412ffee81b0473f91c90e0` |
| mvp/P2/acceptance.json | 198 | `8595dc0d1b870a8e630d5078ae4729463a9232af9b82fca36c69fac695caf26e` |
| mvp/P2/gold.json | 1756 | `68c2699f5d3b18f86c77f9b10e42f9189ae53df99dfe70eaeb48ba07514a7f4c` |
| mvp/P2/request.txt | 172 | `f2270e2aae0fa0edbcd3a742cacac0c8e909ef1842d7b97518ab2b84fff5f826` |
| mvp/P3/acceptance.json | 198 | `8fceb2c9f5546b1e7c6f332ade2bd6046b86e97a8b1f2c36601555a581b07e48` |
| mvp/P3/gold.json | 1257 | `e138db1262ba628eb39d050b2ec5e88696f1f87bf8fad7d54027086df084108a` |
| mvp/P3/request.txt | 134 | `70ba541d88663d30953889b498df9818379b5a2ed131614bdd0d1f8230ce716e` |
| mvp/P4/acceptance.json | 198 | `b75d279521c63c88d4bc0c1a65771bec0c07bb01416bb8af423d64979ad2d564` |
| mvp/P4/gold.json | 1056 | `a75d137b351b9fa600beb2e21b76e68933baa9050f3702e7e17ed7b4635b8a5e` |
| mvp/P4/request.txt | 107 | `8d5fefc3c43c048df4fc86ca046e635e523155a0bbc860b7c4e3b6d2c79dfa5d` |
| mvp/P5/acceptance.json | 198 | `38b9c311e8e0c1d4167d921653a2810ba505c1d6bb4ef140909beedfaf99f006` |
| mvp/P5/gold.json | 1259 | `025ec01f123b1d3702ca404173997f069a6bb493a3536c24ebd81a0a1b8a58c4` |
| mvp/P5/request.txt | 133 | `a877724e804182aa93c2e8fda15bb47bfcdd4e6adf3f9d54045ce3ef453d8d0c` |
| q/A4/acceptance.json | 197 | `8d815a149df96a315f0b377c55f3e0f2c6b14ee421169508131914d89aed9331` |
| q/A4/gold.json | 2196 | `7d0d8bde47c2d18a240d1db87a9ea6d4d1a5fdd595d47cb24f9064b4d82c1e34` |
| q/A4/request.txt | 132 | `fd80e31b9639d78dc1f2d330155de8992c52fab41c05e70e1c4d494e229f9dab` |
| q/A5/acceptance.json | 628 | `aab3bd1785ec43070aacfeb89b531f797b780abc122dbc26f7e1d5f281dc62ec` |
| q/A5/request.txt | 120 | `d2749fca113e212f6c79bfbaf0c1e61d6e5d3a66818879586bf46f94f9cf5cce` |
| q/A6/acceptance.json | 624 | `fc8b9132fe36da993fc16d4cffc5020be29a56a5289fecf2d15c0d7495ca82f6` |
| q/A6/request.txt | 111 | `4c1baa7d4560a4ccb7c73e8c65c7f8f9a9f5786ba316d1a57fc6e59ccffa659b` |
