# v4claude launcher/cardfix review — public receipt

Reviewer: **v4claude**, pane w8:p9, Claude Code, model `claude-opus-5-5` (Opus 5.5), effort high, worktree `C:/dev/CAD-HARNESS-herdr`, branch `herdr/v4`, HEAD `b673b9af8822d755822c64b8f0c5a6c7c5b80f0e`. Appointed by USER 2026-10-20 15:13 JST (`DECISIONS.md`, last section). This file is public: it holds method, roles, statuses and hashes only. It has no private values, geometry, cards, gold, requests, coefficients or notes.

## 1. Orientation receipt (2026-10-20T06:22Z)

Scope this turn: orientation and role setup **only**. No authoring, validation, FreeCAD run, model/provider call, source/schema/policy/recipe/judge/DECISIONS edit, commit, push or lock.

Authority read:

| Document | SHA-256 at read |
|---|---|
| `handoff-v4claude-20261020.md` | `b9b54507f7720335cb21b81f77f0d7c8f1e38938a98d25e35d970e498d962401` |
| `DECISIONS.md` (incl. USER 15:13 JST section) | `243e2e39a59741a9dbc77be1b33bc32e37633017f9d27226616e72c66833a922` |

Also read: the public sections 20–30 of `impl-review-launchers-v4grok.md` (aggregates only) and the "Remaining work" section of `impl-notes-launchers.md`.

Understood boundaries:
- The old interim lock `ef8333d1…` and source digest `b896e106…`/410 records are HISTORY. **No authoring or validation until sol's NEW verified implementation manifest (all 5 recipes) actually verifies.** As of 06:22Z no new manifest or new lock directory existed under `design/` or `reports/`. Status: **WAITING**.
- Nothing was sent to w8:p8/v4grok, and nothing will be. The old agent was not contacted.
- Private custody root reachable: `C:\dev\v4-holdout-private\`. The three labelled directories named in the handoff exist. Only top-level directory names were listed. No private file contents were opened in this step. `pilot-*` and `pilot-user/` were not opened and will not be.
- Frozen semantics noted: Shape.BoundBox selector enclosure (`_bounds`/`_output`), `_epsilon`/`_maximum` value+error≤target, `native_roundtrip` volume error eps·(ΣArea)+roundoff, the native_evidence exact-bool/finite-nonnegative contract, and the SourceC5 single-positive-volume-solid gate before fit. Only the auxiliary native-roundtrip volume maximum or numerical-error budget may be reregistered. Every other threshold stays unchanged.

## 2. Author/reviewer role separation

| Role | Identity | Scope | Model / effort |
|---|---|---|---|
| Independent reviewer and final custody signer | v4claude, this session (w8:p9), session `95ff8003-2412-470c-a845-26f5e4ce61a7` | Reviews the FROZEN author output. Runs independent analytic/native controls. SIGNs or BLOCKs. Never edits author cards and never authors cards/values/C4 cases. | `claude-opus-5-5`, high |
| Private card/precision/C4 author | **v4claude-author-1**: a fresh, non-forked Claude Code Agent-tool subagent (general-purpose) inside this session. No new pane, worktree, profile, settings or permission change. It does not inherit the reviewer's context. Its session-internal handle is kept by the reviewer and is not published. | After the new manifest only: private-only scripts/data under the custody root, the auxiliary precision derivation, fresh same-condition C4 cases, and the frozen complete proposal. Must not sign or review its own output. | Requested `model=opus`, `effort=high`. Self-reported `MODEL_ID: claude-opus-5-5`. The effort level is the requested parameter; the agent cannot attest it. |

Author setup handoff (role-setup only, no data): SHA-256 `e99c0a2b8cf3e8829e96b0568844178602ab3d34dc77872604b862825ad8d908`, 831 bytes. The prompt forbade reading files, running commands or authoring. The author reply was exactly the requested five lines: role author, model `claude-opus-5-5`, files read none, ready and awaiting verified-manifest instruction. The harness logged 1 tool use, which is the hand-back call itself. No other tool activity occurred.

Disclosed limits:
- **Same-model common mode.** Author and reviewer are both Opus 5.5, so shared blind spots are possible. Mitigation: reviewer controls will be built from analytic/native evidence (pinned FreeCAD 1.1.4 headless, independent closed-form gold), not from the author's constructor or judge agreement. The reviewer will not reuse author scripts as its control constructor.
- **Same host session.** The author is isolated by context, not by process or account. The reviewer can see the author's outputs only through files the author writes and its hand-back reports. The reviewer will review frozen, hashed outputs only.
- If author context isolation turns out to be insufficient at authoring time, the reviewer will report it as a concrete role prerequisite. It will not fall back to self-authoring or self-signing.

## 3. Status at 06:22Z (superseded by section 4)

- Status then: WAITING for sol's NEW verified implementation manifest. No card, value, case, precision budget or control had been authored or validated by either role.

## 4. New manifest: independent verification and author release (2026-10-20)

Handoff re-read with its new section "NEW VERIFIED MANIFEST — author release". Handoff SHA-256 at read: `90e86f7918f7c617573799b902fde9ace242219e7b9e46220fe793d17ba8d207`. DECISIONS is unchanged at `243e2e39…`.

Reviewer's own run of `eval_verify_v4.py verify-integrated-lock --manifest reports/verify-v4-claude-handoff-dev-20261020T0620Z/interim-lock/manifest.json`, with `-B` and `dont_write_bytecode`: **EXIT 0**, stderr empty, 2026-10-20T06:40:36Z–06:42:35Z. Results checked from the output and the files:

| Item | Observed |
|---|---|
| `sha256_file` = SHA-256 of `SHA256.json` | `4b9e9a7e975cafbdd35d82cac5a7b2437df915970ba43bb852415ee7ef0bc4b7` (both match) |
| Canonical digest of `manifest.files` | `5ee94cd926f593d0dbcfc1225c59b00ed620a1942644e96182f524acd5dc6244`, 410 records (recomputed by reviewer) |
| DECISIONS binding in `files` | `243e2e39…`, 18066 bytes; matches the live file |
| HEAD / tree | `b673b9af…` / `f6d5decc…`; live HEAD matches |
| Recipes | 5 |
| stage / status / authorization / final_v4_ready / live_calls | implementation / offline_locked / null / false / 0 |
| Neutral proof | `9ac92610…`, 5057 bytes; matches the file |
| Raw `manifest.json` SHA-256 (for reference) | `a2bd2b05baac8427f732db90503cf4baeaa6bddcde99a3584c471540713b30ea` |

**Author released** (v4claude-author-1, the same isolated context as section 2) at about 06:45Z. Release instruction SHA-256 `8a4739f3eb51de76803ede6833dac980d48cef0578b0c36a9bef7c865392beec`, 7427 bytes; this binds every manifest identity above. Scope: handoff steps 1–6 only, written to one new private custody directory. Repository, reports and caches are write-forbidden. No model, provider or network call. Pinned FreeCAD 1.1.4 headless only. Only the auxiliary native-roundtrip volume maximum or error budget may change. The complete proposal must be frozen and hashed before native validation. The author may not review or sign its own work.

## 5. Status at release (superseded by section 6)

- Author was RUNNING (private). The reviewer did not read in-progress output.

## 6. Independent review of author proposal v1 — **BLOCK** (2026-10-20)

Author hand-back received at 07:39:43Z. Frozen proposal SHA-256 `b4c6d21b1d72f5205fac3147554f1aaf0ac44ec00fd4b7e7e13fc5e87de227a5`, frozen 2026-10-20T07:11:27.033069Z, binding 272 files. Author: v4claude-author-1, `claude-opus-5-5`, effort high requested. The author did not review or sign its own work. The reviewer edited no author file. Old proposals, failures and exposed history are retained.

Precision method (name only, values private): `frozen_uncertainty_closure_plus_measured_roundtrip_floor`, unit mm³. It reregisters only the c-s3 native_roundtrip volume maximum. The numerical budget, bounds maximum, c-s2 donor pair and every other threshold are unchanged.

Author-reported native controls (pinned FreeCAD 1.1.4, frozen neutral adapter, both representations):

| Control | PASS | FAIL | UNVERIFIED |
|---|---|---|---|
| Positive full card | 14 | 1 | 0 |
| +1 mm translation defeats predicate | 15 | 0 | 0 |
| +1 mm³ beyond maximum defeats predicate | 15 | 0 | 0 |
| Non-body defeats predicate | 15 | 0 | 0 |
| Uneditable (logic + actual artifact) defeats predicate | 15 | 0 | 0 |

The author table counts B13 as the one positive FAIL. Its actual status is UNVERIFIED (see F1). Full-card gate by stratum: C5 two_patch 5/5, trimmed_multi_patch 6/6; C4 planar_oblique **0/1**, curved_offsets 1/1, finite_planar_replacement 1/1, preservation 1/1. **Total 14/15. This is not pooled into a success.** Host admission 15/15 before and after freeze; 48/48 unaffected families-v1 bundles re-admitted.

Reviewer-independent controls (reviewer-written code in a separate private reviewer directory; no author program or repository judge reused for the geometry checks):

| Check | Result |
|---|---|
| Freeze integrity | 272/272 bound files unchanged. None modified after freeze. Preregistration < synthetic measurement < freeze < controls start (UTC order verified). |
| Manifest binding | Proposal binds `4b9e9a7e…` / `5ee94cd9…` (410) / `b673b9af…` / `243e2e39…` / `9ac92610…`. 3056/3056 adapter code bindings equal manifest `files[]`. |
| Private history | 1927 older custody files byte-identical before and after the author run. families-v1 has 1144 files; sealed archive `588db92f…` unchanged. |
| Native reopen (15/15) | 1 PartDesign::Body with Tip, valid single solid in both FCStd and STEP. Round-trip differences at floating-point level. |
| Registered maximum recomputation | 11/11 recomputed from immutable reference areas equal the card values. |
| Violation artifacts | Real geometry, not mocks: +1 mm shift, +M+1 mm³ and +1 mm³ volume changes, no-Body document. |
| Gold cross-check | C5: sampled output↔reference distance at floating-point level, consistent with the frozen merge design; the unchanged source is rejected. C4: reviewer ray chords 64/64 inside expected range ± tolerance on both representations. |

Findings:
- **F1 BLOCKING — C4 planar_oblique positive control UNVERIFIED** (`continuous_projected_domain_coverage_incomplete`, both representations). The reviewer reproduced it independently. The projected coverage equals the declared domain to floating-point rounding only (Hausdorff ~1e-15 mm), and the frozen exact coverage predicate rejects it. The geometry is correct; the certificate is undecidable for that card's measurement frame. It stays UNVERIFIED. A replacement must be a fresh same-stratum item whose registered certificate is decidable under the frozen judge. Downgrading the same item's certificate after observing UNVERIFIED is not acceptable (C-D(c) rule 5).
- **F2 BLOCKING — precision floor basis not representative.** The measured round-trip floor came from 24 author-made synthetic solids with no boolean- or intersection-trimmed spline faces. The reviewer's own synthetic solids (independent of every case) show that Shape.Volume integration error and FCStd↔STEP volume differences on trimmed faces are many orders of magnitude above that floor. They are comparable to or above the admitted true-discrepancy allowance. Geometrically correct, boolean-built outputs could then be falsely FAILed or UNVERIFIED, biasing the harness-vs-bare benchmark. This concerns the certified basis, not any control outcome.
- **F3 minor — retained preservation item has no gold binding** in the proposal; its prior independent gold or evidence must be bound by hash.
- Accepted with disclosure: the curved_offsets card uses `sampled` scope, the same as the item it replaces and the signed generative convention; it is not a global certificate (rule 5). The c-s2 donor pair is decidable. Transient adapter copies outside the private root were byte-identical (code-binding check) and removed.

Same-model limit: author and reviewer are both Opus 5.5. The reviewer's controls used its own synthetic solids, its own ray and coverage code, and closed-form volumes.

**Verdict: BLOCK. No signature.** No commitment (`holdout-families-commitment-cardfix.md`) and no controls report has been written. Status: awaiting a superseding author proposal (section 7) or a USER decision.

## 7. Superseding author round v2 released (2026-10-20)

Under the USER 15:13 JST authority (same-condition C4 replacement; preregistered auxiliary-precision redesign), the reviewer returned the BLOCK findings to the same isolated author as requirements, without designing any card. The reviewer sent the instruction text in its message to the author and keeps the file in its private directory: SHA-256 `fac3651ef810bfdd37ce750193daa348ca573111ae1f3049af604e9f4f13e346`, 4955 bytes. It requires:
- a fresh planar_oblique item with a certificate decidable under the frozen judge, and no weaker-scope substitution;
- a new precision preregistration whose synthetic set spans boolean- and intersection-trimmed spline faces, written before any new measurement, with disclosure that the v1 outcomes are known;
- a B16 gold binding;
- the complete v2 proposal frozen before native validation, with all 15 items re-controlled.

v1 stays immutable history with its 14/15. The bound manifest, rules and prohibitions are unchanged. The author must not use the reviewer's scratchpad. Author status at release: RUNNING (private).

## 8. Independent review of author proposal v2 — **SIGN** (2026-10-20)

Proposal v2 SHA-256 `f665255e79b21dcc871f3ceca644d50ca88f30d9af257fa6c722fcef8971ebc0`, frozen 2026-10-20T08:04:13.150110Z, binding 280 files. It supersedes v1 `b4c6d21b…`, which keeps its BLOCK as history. Author: v4claude-author-1, `claude-opus-5-5`, effort high requested (no context can attest effort). Reviewer: v4claude, separate context. The author did not review or sign its own work, and the reviewer edited no author file.

Precision method (name only; values private): `frozen_uncertainty_closure_plus_representative_roundtrip_floor`, unit mm³. Preregistered at 07:58:44Z, before any v2 measurement; a first-draft hash differing only in a timestamp field is disclosed. Only the c-s3 native_roundtrip volume maximum changes. The numerical budget, bounds maximum, c-s2 donor pair and all physical, quality, coverage and editability thresholds are unchanged.

The method itself caps the admitted true discrepancy: at most the donor 0.08 mm³ intent, and a mean displacement of at most 10% of the unchanged 0.005 mm deviation bound. It also requires both decisive volume controls to stay decisive. All caps hold on all 11 cards. Synthetic basis: 26 author-built solids across planar, split-roof, axis-, oblique- and curved-boolean-trimmed, fused and quadric classes; 1 invalid build was excluded under the preregistered rule. None is a case item.

Execution: the first controls run was interrupted by an API rate limit on the author context, which is not an outcome. Its 409 files are retained as history. Under reviewer instruction there was exactly one complete replacement run (run2: exit 0, empty stderr, 1368.6 s, started after the freeze). Fields on the 11 items both runs completed are identical.

Native controls, run2 (pinned FreeCAD 1.1.4, frozen neutral adapter, full cards on FCStd and STEP):

| Control | PASS | FAIL | UNVERIFIED |
|---|---|---|---|
| Positive full card | 15 | 0 | 0 |
| +1 mm translation defeats predicate | 15 | 0 | 0 |
| +M+1 mm³ defeats predicate | 15 | 0 | 0 |
| Non-body defeats predicate | 15 | 0 | 0 |
| Uneditable (logic + actual artifact) defeats predicate | 15 | 0 | 0 |
| Absolute +1 mm³ secondary defeats predicate | 15 | 0 | 0 |
| Independent gold agreement | 15 | 0 | 0 |

Full-card gate by stratum: C5 two_patch 5/5, trimmed_multi_patch 6/6 (7 generative + 4 benchmark); C4 planar_oblique 1/1 (fresh), curved_offsets 1/1, finite_planar_replacement 1/1, preservation 1/1. **15/15.** Host admission 15/15 before and after freeze; 48/48 unaffected families-v1 bundles re-admitted. Counts and strata are unchanged: 43 generative + 4 refusal controls, 20 benchmark pairs, and C4 benchmark 4 signed strata with 1 each.

Reviewer-independent controls (reviewer-written code, separate private reviewer directory):

| Check | Result |
|---|---|
| Freeze integrity | v2 280/280 and v1 272/272 bound files unchanged; none modified after freeze. Order verified: preregistration < measurement < freeze < run1 < run2. |
| Lock binding | Proposal binds `4b9e9a7e…` / `5ee94cd9…` (410) / `b673b9af…` / `243e2e39…` / `9ac92610…`. run2 adapter code bindings 3056/3056 equal manifest `files[]`. |
| Native reopen | 15/15: 1 PartDesign::Body with Tip, valid single solid in FCStd and STEP. Round-trip differences at floating-point level. |
| Registered maxima | 11/11 recomputed from immutable reference areas with the preregistered formula equal the card values. |
| Violation artifacts and predicates | Real geometry (+1 mm shift, +M+1 / +1 mm³ volume, no-Body document, frozen-parameter probe). Each defeats `native_roundtrip`, the body requirement or editability as intended, on 15/15. |
| Gold cross-check | C5: sampled output↔reference distance at floating-point level; the unchanged source is rejected. C4: reviewer ray chords 64/64 inside expected range ± tolerance on both representations for every thickness item, including the fresh planar_oblique item at its analytic value. |
| Precision cross-check | Reviewer-owned tilted/vertical cylinder-cut solids: FCStd/STEP geometry identical to ~1e-12 mm. Volume differences are integration error and lie below the registered floor. |
| Unchanged holdings | 1927 older custody files byte-identical. families-v1 1144 files; sealed `588db92f…`. Original60 cohort `45bb80a5…` / 37412 bytes, plus 91/91 commitment-listed files matching bytes and SHA-256. C2 recipe/data not rewritten. |

Findings F1–F3 (section 6) are resolved:
- **F1:** the fresh planar_oblique item uses the signed C4-01 continuous form, with decidability argued before freeze; no weaker-scope substitution.
- **F2:** representative preregistered floor with caps.
- **F3:** prior B16 evidence bound by hash, plus a new independent gold.

Disclosed limits (not blocking):
1. The volume floor is empirical, not a certificate, and is dominated by one curved-trimmed solid. One aggressive reviewer probe solid, a tilted cylindrical cut at about 3× the reference area, exceeded both the floor and the unchanged 0.08 mm³ donor intent. Such an output would be non-PASS on this auxiliary check, consistent with the donor intent other cards apply.
2. curved_offsets uses `sampled` thickness, the same as the item it replaces and the signed convention; it is not a global certificate (C-D(c) rule 5).
3. Same-model common mode (both Opus 5.5); gold solids share the OCC kernel. Reviewer controls used independent code, rays and closed forms.
4. v1 transient tool copies used the reviewer's session scratchpad. That is history: they were byte-identical and removed. v2 did not.

**Verdict: SIGN** — v4claude, independent reviewer and custody signer, for proposal v2 `f665255e…` under implementation lock `4b9e9a7e…`. This signs the private card, precision and C4 data and their controls only. It is not a final-v4-ready claim, a lock, an authorization or a live-call admission. Gemini's public-method review, sol's commit/push, the NEW post-push implementation lock and fresh quota gates all still apply. Live calls 0; generation calls 0.

Not yet written, per the current instruction to publish this aggregate receipt only: the new public commitment `holdout-families-commitment-cardfix.md` and the aggregate controls report `holdout-families-cardfix-controls-v4claude.md`. Both can be produced from this signed proposal on request. Private per-case geometry, values, gold and notes stay in custody. (Superseded by section 9: both are now published.)

## 9. Publication and independent SOURCE/CUSTODY review — **SIGN** (2026-10-20)

Handoff re-read through its section "SIGNED v2" (handoff SHA-256 at read `2c4bc71ec678846faa167fb7c631c29270dcdba5ba392327c11b7b6c2e335d0c`). DECISIONS is unchanged at `243e2e39…`. There was no reauthoring and no rerun. Nothing was sent to w8:p8.

### 9.1 Published public aggregate documents (immutable)

| Document | SHA-256 | Bytes |
|---|---|---:|
| `holdout-families-commitment-cardfix.md` | `253e2a9f367b14bcd412d458c14c84850112e27e4fd6d253a2b110821a35be7f` | 46178 |
| `holdout-families-cardfix-controls-v4claude.md` | `169f918f71ec6c80c6a8d7c7c9e2bece4f7b70606cc6901b1177f6332d8a0f2d` | 13402 |

Both are generated from the signed frozen proposal v2 `f665255e…` and its retained run2 evidence. The commitment binds the controls file by hash. It also binds:
- the full 280-file `sha256 bytes path` listing, rollup `82e2e9069d0095365dbf8da40b6b3f9ab409c61c58eb7cfa6933aa858308cbd0`;
- category rollups for cards/contexts, source assets/preparation, gold, precision and author programs;
- the 15-item roster (id, family, role, stratum, profile only) and the role/implementation identities;
- the unchanged original60 (cohort `45bb80a5…`, 91/91 files) and families-v1 (1144 files, sealed `588db92f…`) holdings;
- retired and retained history.

The section 8 limits are carried in both files: the empirical floor dominated by one curved-trimmed solid; the independent aggressive probe exceeding both the floor and the donor intent despite geometric agreement; sampled curved-offset scope; model and kernel common mode; known v1 outcomes; and the interrupted-first-run provenance.

No per-case geometry, card numbers, requests, values, seeds, coefficients, gold or notes are published. A pre-publication scan found only hashes of author synthetic-solid names and request-file hashes, following the existing commitment convention.

Open publication prerequisite identified, not invented: no deterministic sealed archive (zip) exists for the cardfix tree, unlike the families-v1 seal. The binding is `proposal-frozen.json` plus the listing. Gemini review, sol's commit/push and the new post-push lock remain open.

### 9.2 Source/custody review scope and method

The reviewer read the actual current bytes and the full working-tree diff against HEAD `b673b9af…` (374+/54−) of:
- `tools/cad_verify_v4_bare.py`, `tools/cad_verify_v4_bare_windows.py`, `tools/cad_verify_v4_benchmark.py`, `tools/cad_verify_v4_family_live.py`;
- `tools/test_verify_v4_bare.py`, `tools/test_verify_v4_bare_windows_native.py`, `tools/test_verify_v4_benchmark.py`, `tools/test_verify_v4_family_live.py`, `tools/test_verify_v4_freeze.py`;
- `design/cad-harness-verify-v4/schemas/bare-isolation-smoke.schema.json`.

It also read the unchanged dependencies they rely on: `cad_verify_v4_c2_recipe.py`, `cad_verify_v4_contours.py` / `cad_verify_v4_inputs.py` (recipe hashing), `cad_verify_v4_trials.verify_trial` and `cad_verify_guard.py`.

All 10 reviewed files are bound in lock `4b9e9a7e…` / `5ee94cd9…` and equal it byte for byte. Analysis was read-only plus small read-only checks. No suite was rerun and no source was edited.

### 9.3 Findings

| Area | Observation | Status |
|---|---|---|
| Bare token rights | The child token is built from `DeriveCapabilitySidsFromName("registryRead")`; the derivation must yield exactly one SID equal to the registered registryRead SID. After creation, while the child is still suspended, `_verify_token` reads TokenCapabilities: count must be 1, the SID must match, and the attributes must include ENABLED with only MANDATORY/ENABLED_BY_DEFAULT alongside, otherwise reject. Then the AppContainer SID must match and the LPAC AccessCheck must pass. The receipt records the observed (not requested) count, SIDs and attributes. `registry_read_token_scope` admits only that exact shape. Derived SID arrays stay alive through attribute use and are freed per element. | OK — registryRead is the sole capability |
| Win32k exception | Mitigation `1<<32` (extension points disabled) applies always. `1<<28` (Win32k disabled) is dropped only when the resolved executable equals the staged, inventory-validated pinned FreeCAD `bin/python.exe`. `cmd.exe` children keep both. Child-process creation is restricted (attribute 0x2000e = 1), and jobs are one-process and kill-on-close. Real Win32 regressions read the mitigation policies back from the processes. | OK — minimal pinned-FreeCAD-Python-only exception |
| Scratch/temp containment | The bootstrap resolves the native `GetTempPathW` and refuses any path outside the scratch cwd before creating it. Scratch overlapping the installed source or the runtime is refused. Read inputs must be private single-link copies inside scratch. Drive-volume queries are denied, and the protocol and benchmark limitations disclose that `cmd del` is therefore unavailable. | OK |
| ACL handling | Only task-private read-only nodes (the staged runtime and private inputs) receive a fresh protected DACL: a package read/execute grant, a package write/delete deny, supervisor full control and OWNER_RIGHTS READ_CONTROL. This prevents inherited scratch write grants. Every touched object is restored from held original descriptors and verified as exact SDDL/control; any failure keeps durable recovery evidence and is never claimed as cleanup. No installed or shared path is modified. | OK |
| Shared ACL residue (actual) | 0 leftover `CADBare.*` AppContainer profiles in the current user's mappings, and 0 `*.security-recovery.json` files under `C:\dev` or the user temp directory. The current-source receipt reports `source_security_unchanged`, `cleanup_restored`, `setup_failure_restored` and `owner_setup_and_temp_cleanup_restored` true. | OK |
| Admission of isolation evidence | Benchmark admission and `_validate_isolation_streams` reject any demonstration carrying `zero_capabilities`, and require `registry_read_only` true plus the exact token scope on the native, shell and timeout processes. The schema forbids `zero_capabilities` and pins the SID and attributes. ToolLoop refuses any non-mock action whose receipt lacks a verified registryRead-only token. | OK — fail-closed |
| Canonical C2 recipe path/callers | `validate_active_c2_prepared` now compares each contour row's `recipe_sha256` and the canonical hash of its embedded recipe with `c2_recipe.load(ROOT)["canonical_sha256"]` `f91da523…`. The loader byte-pins `c2-production-recipe-cycle3.json` (`af0a2e13…`) and the sole registration (`944567b1…`) with a race recheck. The removed literal `af0a2e13…` was the raw file digest, while contour rows store the canonical digest (`contours._hash`, `inputs.canonical_sha`). The reviewer confirmed that all 14 admitted C2 prepared records in custody carry `f91da523…`: the repair admits them, and the old literal would have rejected them. Callers are `family_live.validate_published_files` and `benchmark.validate_bound_inputs`; `s1` loads the same pinned recipe. Regressions reject the raw-file digest and forged, inactive and mixed recipes. | OK — correctness repair, recipe/data unchanged |
| Live admission | `trials.verify_trial` requires the bound authorization, registration, execution identity and quota snapshot. It re-verifies the integrated lock (`authorization` must be null in the lock) and checks OMP identity, unchanged source files and the unchanged public commitment. The quota guard soft-stops at ≥55% and hard-stops at ≥60%. The current lock has authorization null and `final_v4_ready` false. | OK — fail-closed; no live admission exists |
| Actual-source control binding | The reused current native receipt `reports/verify-v4-launchers-review-gemini/reseal-native/bare-isolation-receipt.json` binds `isolation_sha256` `f7bb489f…` and `supervisor_sha256` `be8d7be3…`. These equal the current `cad_verify_v4_bare_windows.py` and `cad_verify_v4_bare.py`, and `native_smoke_sha256` `27c2c8a2…` equals the current native test file. The cardfix run2 adapter code bindings are 3056/3056 equal to the lock. | OK |
| Reused suites | Gemini reseal host: 640 tests = 461 PASS, 179 SKIP (native-only), 0 FAIL/ERROR (2026-10-19T18:09–18:12Z). Gemini reseal native (pinned FreeCAD): 519 tests = 518 PASS, 1 SKIP (OS symlink privilege), 0 FAIL/ERROR (18:12–19:35Z). Parent native-4 and host results match (`impl-notes-launchers.md`). The only lock-bound file modified after these suites started is DECISIONS (06:19:10Z), and the lock-to-lock diff against `b896…` is DECISIONS only. The suites therefore cover the current executable bytes and were not rerun. | OK |

Non-blocking notes for sol (no fix requested):
1. While a read-only node is held, its fresh protected DACL also omits SYSTEM and Administrators ACEs. This is intended, task-private and exactly restored. An interrupted run is recoverable only from the retained recovery file.
2. The benchmark limitation that `cmd del` is unavailable on the bare arm (because volume queries are denied) is a real workflow difference. It is disclosed in the protocol and results limitations and should stay visible in RESULTS.
3. The 179 host skips are native-gated tests. Native coverage of those paths comes from the single 519 native run.

### 9.4 Verdict

**SOURCE/CUSTODY: SIGN.** v4claude (independent reviewer) signs this review for:
- implementation lock `4b9e9a7e975cafbdd35d82cac5a7b2437df915970ba43bb852415ee7ef0bc4b7`;
- canonical source map `5ee94cd926f593d0dbcfc1225c59b00ed620a1942644e96182f524acd5dc6244` (410);
- HEAD `b673b9af8822d755822c64b8f0c5a6c7c5b80f0e`;
- the repaired source and regressions listed above;
- the published `holdout-families-commitment-cardfix.md` `253e2a9f…` and `holdout-families-cardfix-controls-v4claude.md` `169f918f…`;
- the data signature in section 8 (proposal v2 `f665255e…`).

Limits:
- This is a read-only review reusing existing current-source evidence; no suite was rerun.
- Windows behaviour is proven on this host and build only (Windows 11 build 26200).
- The section 8 data limits apply unchanged.
- Same-model common mode with the data author applies to the data signature, not to this source review. This reviewer authored no source.

This is not an authorization, a lock, live admission or `final_v4_ready`. Still required, in order:
1. Gemini's independent public-method/data review of the two published files.
2. Sol's explicit reviewed commit/push, excluding caches, private material and reports.
3. The NEW post-push implementation lock.
4. Only then the conditionally authorized original-163 maximum, under fresh 55% consult / 60% stop and the frozen original authority.

The family, benchmark and pilot pools need their own separate authorizations. No commit, push, lock, live, model- or CAD-generation call, or source/permission change was made by v4claude. P8 was not contacted.
