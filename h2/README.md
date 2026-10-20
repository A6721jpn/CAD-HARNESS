# Harness² CAD MVP

`LIBRARY_ONLY`, k=1. Base settings are read afresh each cycle and never rewritten.
Run0 does not receive library entries; only the proposer receives a snapshot from
before the cycle. All CAD attempts run sequentially through the unchanged
`tools/cad_run.py` and its fixed probes. No v4 imports are used.

Run a real cycle (requires approval from h2lead for phase #1b):

    python -m h2.cycle --task A-box-pocket-fillet --candidates 3

Run stub unit tests, without FreeCAD or LLM calls:

    python -m unittest discover -s h2/tests -v

Reports: `reports/h2/<cycle_id>/cycle.json`, including per-call tokens, per-run
attempts and geometry results, stage timings, total timings, proposals,
composition decisions and appended library entries. Prompts and Codex events
stay under this report directory. Generated CAD scripts and CAD outputs live
under `reports/cad-run/h2/<cycle_id>/`. The library is append-only at
`h2/library/cad-freecad.jsonl`.

The default LLM budget is 20 calls (`--max-llm-calls`). Exhaustion or errors save
partial results and return a nonzero process exit. A completed experiment can
have a failed geometry result: the report's geometry flag is derived solely
from `probe_status == "pass"`, separately from experiment completion.

Proposal JSON uses `candidates`, each with `edit` (a list of `{op, value}`) and
`rationale`. Only the five operations in SPEC are accepted. Scalar conflicts
take the higher ranked edit's setting; additive guidance is combined. A failed
composition reuses the already measured highest ranked supported single probe,
without an additional run. If no edit is supported, the original baseline is
selected without a composition run.

Defaults for ambiguous cases: unknown total tokens or baseline infrastructure
intervention make comparisons `confounded`; unknown token values stay null.
When available, total is input plus output, with cached/reasoning subsets never
double counted. Model null uses the configured Codex model and is recorded as
null rather than guessing its identity. Guidance snippets are prompt content,
never evaluated by the orchestrator. A scalar conflict does not erase a
candidate's measured verdict; conflict details are recorded separately.
