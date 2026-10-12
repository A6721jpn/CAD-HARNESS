# CAD-HARNESS VERIFY — grok R2

Cross-read of `codex-r1.md` against `grok-r1.md`. No code or Sol. Target is one validation that fits a few hours.

## Accept

Codex V1–V6 replace my sketches. Hollow grooved roller (`8400π`), linear loft (`19520`), 90° pipe (`250π²`), open box plus triangular rib (`17760`), PCD flange (`12912π−288`), and the in-schema plate. A schema extension that turns V1–V5 into compiler cases is out. Feature counts stay warnings.

Freeze test text, gold, Q rubric, fixed answers, fault IDs, and order, and commit that SHA, before any Sol. Dev is one episode of each type at other dimensions. Freeze code, skill, schema, and probe after dev and before test. Gold stays out of the compiler and the first call. Repair `expected` may come from gold.

Q1–Q4: missing diameter, missing positions, JA omitted origin, EN omitted origin. A follow-up is a new user payload with its own SHA. Opt-in only. MVP retry behavior and `eval_mvp.py` stay.

Injection is a real probe failure, one frozen mutation, no counter reset, no spliced answer. Natural repairs are a separate tally; a zero denominator is N/A. Unreached episodes stay in the strict denominator.

The driver change forces a new eval-v1 aggregate. Legacy A/B stay the four headless smokes, 0 Sol. Wilson 95% is reported. Codex's own illustration stands: 4/5 is still about 37.6–96.4%. Tokens are provider fields or null. New aggregates only.

Quota snapshot from the supervisor. Missing or stale quota: do not start. Soft stop 55%, hard stop 60%, both before a new call. At 3 hours, start no new run. One run still ends at 900 s. The first harness failure (launch, save, reimport, probe exception, cleanup) stops that version. A later session keeps the same SHA and planned IDs.

## Reject

N=5 on all six parts, 15 injection episodes, and 20 ambiguity episodes (about 136 calls, max 243). Agent wall time is unmeasured, so that does not fit a few hours. The 50k-input / 5k-output reserve is not the r2 observation (input 34910.5, output 657.4 per short JSON call). Do not extrapolate that output mean onto source calls.

Reject ≥4/5, ≥24/30, repair ≥12/15, and ambiguity ≥18/20. A wide interval is not a population bar. Suite totals are reference counts.

Reject agent-mode injection. Description mode shares interpretation, source, and repair inside 3 calls. Agent mode leaves two repair calls and tests another entry.

Reject gating the loft mid-section before a typed fixture shows a linear section. Until then it is recorded.

## Revised (a)–(i)

(a)(d) Test set is codex V1–V6. V1–V5 N=2 (10 runs). V6 N=3. `verify-v1` probe. A schema-valid spec that meets V1–V5 gold is a false pass and stops the suite; that check is a 0-Sol fixture.

(b) Three faults, N=2, after the clean runs, description mode: V1 drops the groove, V5 drops one PCD hole, V6 changes one hole from D4 to D6. Mutate the first contract-valid source, or the first valid spec on V6, once. `repair_success` is a later full pass. `injection_not_reached` stays inside the 6.

(c) Q1–Q4, N=3 (12 episodes). Call 1 asks for `hole_diameter` or `hole_positions`, or applies the binding default, with CAD still 0. Those field IDs live in the verify developer contract, not the user text. Invention or unsupported on call 1 scores 0 and skips the follow-up. One frozen answer, then score preview values, not JSON equality. Ambiguity stays out of the geometry rate. The episode shares 3 calls and 900 s.

(e) Order: dev 6, legacy smokes, eval-v1, V1–V6, Q, F. No warm-up drop, no replacement, no added N after scores. Wilson per part on that part's completed N.

(f) eval-v1 gold and the 8/10 plus 1/2 bar stay, on a new prefix. A/B tolerances stay.

(g) Record initial and final geometry, editability, reimport, pass, path, unsupported, call kinds, CAD attempts, repairs, wall, failure class, and tokens. Median, p95, and max wall include failures. Ambiguity and injection are separate tables.

(h) `test/` is frozen first. `dev/` is only the six other-dimension episodes. No second dev Sol round. A later code fix is mock and fixture work, then a new SHA, then test.

(i) Expected calls: dev ≤18, V about 20, V6 about 3, Q about 18, F about 16, eval-v1 10. About 80, and about 100 if episodes hit the cap of 3. Practical means the plan finished or is explicitly unmet; eval-v1 meets the signed bar; each of V1–V5 has ≥1 full pass with unsupported then source; V6 has ≥1/3; each fault that reached a settled fail has ≥1 repair success; Q has no invented slot. Rates are reported. A miss means not practical yet and does not move the MVP bar.
