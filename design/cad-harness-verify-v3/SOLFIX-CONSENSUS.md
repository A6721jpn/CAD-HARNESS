# SOLFIX CONSENSUS DRAFT (supervisor synthesis, 16:27 JST)

Base: SOLFIX-BRIEF items 1–3 and 5, with codex COUNTER items 3–5 (exact structured classification, ≤3 transport attempts per logical call, bounded capture, conservative annotations). G5-r1 and G1-r2 stay completed failures as recorded (all three agree), with a separate `provider_rejected` annotation.

Resolved disagreements:
- **Clock (codex COUNTER 1, adopted).** Resume does NOT get a fresh 10800 s clock. It inherits the original absolute deadline_monotonic 545790.093, the 163 ceiling and the 54 spent calls (109 remain). If the deadline or cap is reached, the remaining IDs stay not_started and the bar is unmet. No extension.
- **A5-r5 (grok COUNTER plus the user's 16:20 order "retry A5-r5 with full stderr/exit capture", adopted).** Resume re-executes 14 IDs in frozen order:
  - A5-r5 first, then sequences 48–60.
  - The original A5-r5 partial artifacts and the original suite file (all 60 rows) stay byte-identical.
  - Segment 2 writes the re-execution under a new run dir suffix (`-resume1`) bound to the original row.
  - The original A5-r5 call produced no model output (verified `server_overloaded`), so it is not a model observation. The aggregate scores the segment-2 A5-r5 and reports the original partial as a provider-rejected attempt.
  - No completed ID (1–46) is re-executed.
- Re-freeze as `verify-v3-reviewed-r1-solfix` after archiving SHA256.run-r1.json. The aggregate binds segment 1 to the original manifest and segment 2 to the solfix manifest, using new output files.

Signers: append `consensus: AGREE <JST>` or `consensus: COUNTER <exact>` to your solfix-<you>.md.

## USER DECISION 16:39 JST (overrides retry items; no consensus needed)
- On a Sol `server_overloaded` rejection, wait 10 minutes and resend the byte-identical call. This is treated as normal and never causes an abnormal stop.
- There is no retry cap for overloaded. The wall/deadline and quota stops still apply.
- Overloaded attempts and waits do not count toward the Sol call budget (the 163 cap or P/R) and are not scored as failures. They are recorded separately: attempts, waits, session ids, error info.
- This replaces "≤3 transport attempts, 30/90 s backoff, counted toward 163" and "3 consecutive provider_unavailable → harness stop".

## USER DECISION 17:08 JST (deadline)
- The v3 deadline is extended to **20:00 JST** for the resumed segment. This overrides the inherited deadline_monotonic 545790.093 (about 18:08 JST).
- Implementation: the resume clock is derived from a wall-clock cutoff of 2026-10-13T20:00:00+09:00, converted once at resume start to an absolute monotonic deadline and recorded.
- Segment 1 keeps its original deadline_ok. Every other strict check is unchanged.

## USER DECISION 17:08 JST, update (supersedes the 20:00 entry above)
- **No deadline.** v3 continues until complete. The wall-clock/deadline stop is removed for the resumed segment.
- The quota stops stay: 55% soft (consult) and 60% hard stop. The per-episode 900 s stage budgets and all other checks are unchanged.
- Segment 1 keeps its original recorded deadline_ok. The aggregate reports segment 2 as `deadline: none (user decision 17:08)`.
