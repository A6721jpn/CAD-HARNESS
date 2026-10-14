# Phase 3 implementation — sol

## Status and generator

Generator: **`openai-codex/gpt-6.1-sol`, thinking `xhigh`, through omp**. This is not the Astra pilot judge. Both generator settings are fixed and checked by freeze/verify; ambient model-role defaults do not select the generator.

Implementation and offline verification are complete. No real model generation, real CAD execution, live trial, permanent execution freeze or commit was performed. The private holdout directory was not opened. The relay owns review, commit and the subsequent R2-2 lock/authoring/control-validation/final-freeze sequence.

Addendum B review: `u1b-sign-sol.md` is BLOCK with concrete window, E6/E7, critical-dimension and success-definition fixes. Independent screening: `pilot-select-b-sol.md`, 25 excluded, zero selected. Other agents' screenings/signatures were not consulted. Bundle preparation below does not approve B, establish attachment completeness or enroll a pilot.

## Changed interfaces

- `tools/eval_verify_v4.py`: adds immutable `freeze`, manifest-authorized `run --phase holdout`, and offline `pilot-bundle`. Recorded request/batch/aggregate paths remain available. The preflight contract comparison uses normalized text to tolerate checkout CRLF; all frozen file hashes still bind actual bytes. Existing skill/policy/modeling prose and v1–v3 files are unchanged.
- `tools/cad_verify_v4_freeze.py`: public-byte/host/runtime bindings, authorization validation, verification and single-use claim.
- `tools/cad_verify_v4_live.py`: live transport, exact raw capture, active-clock overload exclusion, shared call admission, isolated request/checker roots, fixed-cohort execution and unchanged v3 predicate/summary reuse. The MVP route retains its existing driver and three-call/three-CAD limits; other routes retain the existing P/R/CAD state machine. Frozen tools are copied into each isolated checker root so the existing runner's output-root and native-worker paths remain valid.
- `tools/cad_verify_v4_pilot.py`: deterministic whole-message JSONL window and explicitly declared attachment bundle, with integrity verification.
- New mock suites: `tools/test_verify_v4_{freeze,pilot,live}.py`.

## Freeze and authorization

`freeze --policy <policy.json> --holdout-commitment <public-commitment.json> --run-dir <unused-freeze-dir>` creates **`SHA256.json` and `manifest.json` in that new directory**, never overwriting a prior freeze. Without `--authorization`, it is an offline binding only and cannot launch a holdout. Current policy remains offline-zero; live permission is a separately frozen record, not a policy edit, environment variable or run-time authorization flag.

Optional inputs: `--authorization <authorization.json>`, `--quota-snapshot <absolute-path>`, `--omp <executable>`. The authorization JSON has schema `cad-harness.live-authorization.v4` and requires phase `holdout`, `charged_calls: 163`, `clock_confirmation: true`, generator `model`, host `DPC-019`, `independent_control_validation: true`, the public commitment's `holdout_commitment_sha256`, and the absolute `quota_snapshot` path. This evidence must be supplied by the authorized supervising workflow after real control validation; these instructions do not assert that validation has happened.

Bindings include the complete independently re-enumerated Python tool set, v4 skill bundle, original modeling skill, build/gold schemas, policy/ledger/rubric and plan/decision bytes; actual host/OS identity; resolved omp executable SHA/version; and public commitment SHA. FreeCAD identity includes the executable SHA and Windows PE version resource, without executing CAD. Live verification requires DPC-019 and observed FreeCAD 1.1.4. The SHA descriptor binds all manifest fields except its own SHA. Verification detects altered or missing bindings, added tool files, host/runtime drift and changed commitments. The absolute original freeze directory plus exclusive `manifest.claim.json` prevents normal reuse/relocation of the same authorization. Filesystem isolation remains procedural, not an adversarial security boundary.

## Public sealed-input contract

No hidden material was needed to implement this contract. The author/custodian must emit:

- Public commitment: schema `cad-harness.holdout-commitment.v4`, `cohort_sha256` equal to the released cohort JSON's SHA-256. Freeze reads/hashes this public file only, without following references.
- Released cohort: schema `cad-harness.holdout.v4`, nonempty `files` mapping bundle-relative filenames to SHA-256, and `entries`. Entries retain the existing 60-item v3 allocation/order, 51 scored entries, private scoring aliases, sequence/ID/group/case/round/route/min/max/scored/bar-class fields, plus `request` and `acceptance` filenames. The unchanged v3 order validator fixes denominators and the 163-call ceiling.
- Acceptance card: schema `cad-harness.acceptance.v4`, `request_sha256`, matching `route`, and checker-only `gold`, inline `rubric` and genuine frozen `answer` as appropriate. All file references are relative to the cohort directory and present in `files`. Offline entries declare `script` and `task`; optional gold uses the existing MVP checker. Fault entries declare `fault`, whose candidate file is also hash-bound. Checker gold case IDs match their scoring aliases. Nothing substitutes old tasks for an independently authored cohort.

`run --phase holdout --manifest <original-freeze-dir/manifest.json> --sealed-input <released-cohort.json> --run-dir <unused-run-dir>` verifies authorization before opening trial inputs. It verifies the cohort commitment, every declared file, card bindings and full fixed order before admission, and rechecks committed inputs before use. Linked/escaping paths are rejected. There is no resume, replacement, borrowing or retake path.

## Transport, clocks and evidence

Each generator process is a fresh `omp --print --mode json` invocation, with stdin `DEVNULL`, tools/rules/extensions/discovered skills/title/session/prewalk disabled. The frozen skill is the system prompt; the original request and permitted typed runtime facts are in a hashed payload file. Checker gold, later requests and acceptance cards are not model payloads. The frozen per-invocation config disables automatic retries/fallback, auxiliary inference, compaction and hidden instruction-trigger behavior. Actual argv, cwd, payload/config hashes and request/skill hashes are recorded before launch. No user configuration is modified.

The run admits at most 163 charged calls, reserves episode/future minima, checks identity and a fresh quota snapshot, consults/stops admission at 55%, and hard-stops at 60%; missing/stale quota stops. Snapshot publication is external: the CLI does not invent quota values. There is no suite wall deadline.

Only a structured `codex_error_info=server_overloaded` with a completely parsed stream and no assistant/final text is exempt. The rejected attempt and full 600-second wait are excluded from enclosing active clocks, with no reset of remaining limits, P/R or CAD slots. The identical argv/payload/config is resent without a retry cap. Output-bearing, unstructured, malformed and capture-interrupted failures are not exempt. Quota/identity/cancellation can interrupt waiting; partial waits are recorded and the run is incomplete. Recovery is VERIFIED only after a real rejection/full wait/accepted response, never from mocked transport or an overload-free run.

The append-only ledger records each physical attempt and wait. Both raw streams are drained directly to exclusive disk files, including partial bytes on transport failure; display/parser tails are bounded. Timeout/cancellation kills owned subprocesses. Capture/identity/uncontrolled CAD evidence failures stop the run; ordinary scored model misses continue. Active episode exhaustion is retained as incomplete evidence rather than converted into an overload-specific failure. Outcomes are not printed during the fixed cohort; summaries are derived after termination. Driver compatibility reports represent accepted logical invocations; the v4 journal is authoritative for physical retries and full wall time. Missing usage/prices remain null. Injected transports are labeled `unit_mock`, with fresh holdout `not_run` and overload robustness UNVERIFIED.

## Addendum B data CLI

`pilot-bundle --source-jsonl <listed.jsonl> --locator <1-based-physical-line> --request <verbatim-request.txt> --attachments <descriptor.json> --conversation-id <id> --run-dir <unused-bundle-dir>` does no enrollment, CAD or generation. The descriptor has schema `cad-harness.pilot-attachments.v4` and `required`, an explicit list of absolute required file/directory paths. Three-party screening must establish dependency completeness; an empty or incomplete declaration is not eligibility evidence.

The CLI excludes tool/system/analysis content, retains the contiguous suffix of complete preceding user/assistant text messages fitting 40,000 Unicode characters, and preserves text blocks without paraphrase. The locator is a physical line; the separately recorded ordinal is the count of response-item messages, not the JSONL record ordinal. Source/conversation identity, cut/bounds and hashes are retained. Attachments are recursively enumerated, copied and checked before/after; missing/unreadable/changed/linked/escaping dependencies fail E7. Source/locator failures fail E6. The private holdout path is rejected before traversal. Outputs: `request.txt`, `context.json`, `attachments.json`, copied attachments and `bundle.json`; `verify_bundle()` checks copies without reopening originals. Required dimensions/tolerances and adoption judgments still require pre-registration outside this preparation command.

## Exercised verification

- `python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live`: **92 tests PASS**. All model/CAD launches mocked or prohibited.
- Full synthetic 60-entry cohort, made only from existing public development records and injected transport: COMPLETE, 105 mock charged/model attempts, 218/218 streams complete, no stop, bar false. This exercises ordering, all route dispatches, ledger and summary; it is not a fresh holdout or quality measurement.
- Injected generation → existing spec compiler → mocked CAD/reimport artifacts → v3 artifact validation: passed, one mock charged call and one mock CAD attempt. No real native geometry was run or certified.
- Actual local Python child through the production pipe collector: stdin EOF, exit 0, exactly 50,001 stdout bytes including an invalid UTF-8 byte and five stderr bytes retained. No model/CAD process involved.
- Actual offline freeze CLI and verify in an automatically removed temporary directory: 68 bound files, authorization null; actual host DPC-019, FreeCAD PE version 1.1.4 observed without launching CAD.
- Actual pilot-bundle CLI and verification on temporary synthetic JSONL/attachment bytes: original request preserved, one prior message, one copied attachment. Temporary smoke data and failed-test directories created by this work were removed.

Limits: the installed omp provider stream and native CAD execution were not exercised live, as explicitly forbidden. No live quality, cost reduction or overload recovery is claimed. No real execution manifest or hidden input was created, changed or released. No commit was made.
