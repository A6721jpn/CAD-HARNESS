# Harness² CAD MVP

`LIBRARY_ONLY`, k=1. Base settings are read afresh each cycle and never rewritten.
Run0 does not receive library entries; only the proposer receives a snapshot from
before the cycle. All CAD attempts run sequentially through the unchanged
`tools/cad_run.py` and its fixed probes. No v4 imports are used.

Run a real repeated cycle from h2lead's shell:

    python -m h2.cycle --task A-box-pocket-fillet --candidates 3 --repeats 3 -m gpt-6.1-sol

Run stub unit tests, without FreeCAD or LLM calls:

    python -m unittest discover -s h2/tests -v

Reports: `reports/h2/<cycle_id>/cycle.json`, including per-call tokens, per-run
attempts and geometry results, stage timings, total timings, proposals,
composition decisions and appended library entries. Prompts and Codex events
stay under this report directory. Generated CAD scripts and CAD outputs live
under `reports/cad-run/h2/<cycle_id>/`. The library is append-only at
`h2/library/cad-freecad.jsonl`.

The default and maximum LLM budget is 100 calls (`--max-llm-calls`). Exhaustion or errors save
partial results and return a nonzero process exit. A completed experiment can
have a failed geometry result: the report's geometry flag is derived solely
from `probe_status == "pass"`, separately from experiment completion. Group
geometry_pass means every repetition passed; pass_rate reports partial success.

`--repeats` defaults to 1. One full baseline warmup run is excluded from comparison
statistics (its calls still count toward the budget and overall cost). Then base
runs N times, the proposer receives all N baseline traces, and candidate runs
rotate c1,c2,c3 for each repetition. A supported composition runs N times too.
All calls are sequential. Each group records pass rate, sample means and sample
standard deviations for attempts, token components and time (SD=0 for N=1).
`groups` contains comparison summaries; `runs` retains every individual trace.

D15 replaces the original single-run support rule: pass rate must not decrease,
and either pass rate increases or the mean token/time saving exceeds both 10%
of the baseline mean and the larger of the two sample SDs. The cost conditions
are OR, not AND. Missing required evidence is confounded. Composition is kept
only if its repeated confirmation also has D15 support against the baseline;
otherwise the best supported individual edit is selected without another run.

Every call and group records cached and uncached input (input minus cached),
and groups report aggregate cache-hit ratios. Warmup cannot force the provider
to give identical cache hit rates; `cache_policy` records this limitation.
`comparison_tokens` and `comparison_wall_ms` exclude warmup and proposal costs;
top-level totals include every stage, including warmup and the proposer.

Proposal JSON uses `candidates`, each with `edit` (a list of `{op, value}`) and
`rationale`. Only the five operations in SPEC are accepted. Scalar conflicts
take the higher ranked edit's setting; additive guidance is combined. A failed
composition reuses the already measured highest ranked supported single probe,
without an additional run. If no edit is supported, the original baseline is
selected without a composition run.

Infrastructure intervention makes comparisons `confounded`; unknown token
values stay null. D15 can establish support from a higher pass rate or a known
qualifying metric even if another metric is unavailable.
When available, total is input plus output, with cached/reasoning subsets never
double counted. CLI defaults to explicitly selecting `gpt-6.1-sol` with `-m`.
Reported runtime model identity takes precedence; otherwise the explicit CLI
selection is recorded with model_source=explicit_cli_argument and a reason
that runtime identity was not reported. Historical null model records are
unchanged. Guidance snippets are prompt content,
never evaluated by the orchestrator. A scalar conflict does not erase a
candidate's measured verdict; conflict details are recorded separately.
