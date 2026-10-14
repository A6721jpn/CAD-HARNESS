# VERIFY v4 Proposal: Gemini (plan-r1-gemini)

## 1. Executive Summary & Core Alignment

VERIFY v4 operationalizes the findings of the three-party committee ([`COMMITTEE-CONCLUSION-20261014.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v4/COMMITTEE-CONCLUSION-20261014.md)) under the user's priority order:
1. **Cost Measurement**: Complete token, time, and price accounting in a unified ledger, with nulls preserved and rates sourced.
2. **Consolidation**: Rules in skills, deterministic execution in CLI; raw user prompt contains only the design brief and skill context.
3. **Reproduction**: A single uninterrupted blind run on an unseen fresh holdout (one manifest, zero mid-run repairs or retakes).
4. **Real Design Pilot**: Pre-registered practical utility trial on real engineering tasks with strict acceptance criteria (>=70% usable with <=5 min edits, zero critical dimension errors).

Constraints are strictly honored: headless FreeCAD 1.1.4 on DPC-019 only, no shape/capability expansion, full stdout/stderr capture, 55%/60% quota stops, and 600 s overload retries.

---

## 2. Concrete Deliverables (1–4) & Execution Order

Execution follows a strict dependency chain where observation tools precede evaluation runs:

```
[Phase 4.1: Cost Ledger & Pricing] ──> [Phase 4.2: Skill & CLI Packaging]
                                                  │
                 ┌────────────────────────────────┴────────────────────────┐
                 ▼                                                         ▼
[Phase 4.3: Fresh Holdout Blind Run]                     [Phase 4.4: Real Design Pilot Trial]
```

### Deliverable 1: Unified Cost & Telemetry Ledger (Phase 4.1)
- **Token telemetry**: Capture all model turn usage fields (`input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens`), fixing the v3 defect where geometry calls returned `null`.
- **Wall-clock breakdown**: Active execution wall time, provider backoff wait time (`provider_wait_s`), and system queue latency recorded per call and per episode.
- **Pricing module**: Deterministic pricing calculator referencing `pricing.json`. Missing tokens or undocumented rate models evaluate strictly to `null` with a documented reason (never coerced to `0`).

### Deliverable 2: Skill & CLI Consolidation (Phase 4.2)
- **Skill package**: Move all modeling contracts, parameter schemas, clarification rules, and repair guidance into `skills/freecad-modeling/SKILL.md` (or dedicated `skills/freecad-v4/`).
- **Prompt purification**: The model payload consists solely of the user design brief and the skill system prompt. No procedural evaluation rules, scoring criteria, or harness harness-management text are passed in the prompt.
- **Single CLI entrypoint**: Deterministic workflow encapsulated in `tools/cad_verify_v4.py` (or subcommands in `eval_verify_v4.py`) supporting single-command invocation for both synthetic evaluation and real user tasks.
- **Pass criterion**: Single CLI command accepts a design request text and returns complete CAD artifacts (`.FCStd`, `.step`, `result.json`) without external human prompting.

### Deliverable 3: Fresh Holdout Reproduction Suite (Phase 4.3)
- **Dataset**: Fresh 60-episode test suite across the 6 core v3 families (Geometry G1–G6, Stock S3, Defaults/Ambiguity A4–A6, Completion C4–C5, Forced Faults F4–F6, Dev D1–D3) with novel dimensional and topological parameterizations within frozen v3 capability limits.
- **Strict Blind Run**: Single freeze (`SHA256.json`), single uninterrupted run segment. No interim inspection, no post-hoc prompt tuning, no segmented recovery.
- **Pass criterion**: 100% completion (60/60) with `bar_met == True` against pre-registered v3 thresholds in one pass.

### Deliverable 4: Real Design-Work Pilot Trial (Phase 4.4)
- **Pilot Dataset**: 10 realistic, practical engineering design briefs representing actual parts (turned stepped shafts, mounting baseplates, bearing housings, spacers/bushings).
- **Trial Protocol**: Blind model execution followed by human engineering review and measured manual modification.
- **Pre-registered Pass Criteria**:
  - $\ge 70\%$ of tasks classified as *Adopted As-Is* (0 min edit) or *Adopted with Minor Fix* ($\le 5$ min edit in FreeCAD GUI).
  - $0\%$ tolerance for critical functional dimension errors or fabricated features (causes immediate task failure).

---

## 3. File & CLI Layout

```
design/cad-harness-verify-v4/
├── BRIEF.md                          # Phase requirements
├── COMMITTEE-CONCLUSION-20261014.md   # Upstream consensus
├── PLAN-V4-CONSENSUS.md              # Binding signed plan
├── pricing.json                      # Documented token rates & pricing schema
├── gold-schema.json                  # Frozen holdout schema
├── run-order.json                    # Frozen 60-episode order
├── holdout/                          # Unseen test cases (G1..G6, S3, A4..A6, C4..C5, F4..F6, D1..D3)
│   └── <case_id>/                    # {description.txt, gold.json, positive.py, negative.py, ...}
├── pilot/                            # Real engineering pilot tasks
│   ├── tasks.json                    # 10 pre-registered design briefs
│   ├── rubric.json                   # Inspection checklist & time limits
│   └── evaluation-ledger.json        # Trial results & edit duration records
├── SHA256.json                       # Cryptographic freeze manifest
├── FROZEN.md                         # Authoritative provenance record
└── RESULTS.md                        # Final outcome report

tools/
├── cad_verify_v4_agent.py            # Purified prompt runner, 16KB stream capture, token recorder
├── cad_verify_v4_guard.py            # Budget counter, quota stops, wall/wait timer
├── cad_verify_v4_probe.py            # BRep & native editability verifier (unchanged v3 rules)
├── eval_verify_v4.py                 # CLI entry point: freeze, run, pilot, aggregate
└── test_verify_v4.py                 # Offline unit regression suite
```

### CLI Commands
- `python -B tools/eval_verify_v4.py freeze --version verify-v4-r1 --codex <cli-path>`
- `python -B tools/eval_verify_v4.py run --prefix host-v4-r1 --quota-snapshot <path> --call-budget 163`
- `python -B tools/eval_verify_v4.py pilot --prefix host-v4-pilot --tasks design/cad-harness-verify-v4/pilot/tasks.json --call-budget 40`
- `python -B tools/eval_verify_v4.py aggregate --prefix <prefix> --suffix <suffix>`

---

## 4. Unified Ledger Schema

The ledger captures cost, time, and output telemetry at Call, Episode, and Suite levels in `reports/cad-run/<run_id>/cost-ledger.json` and aggregate JSON:

```json
{
  "schema": "cad-harness.cost-ledger.v4",
  "run_id": "host-v4-r1-G1-r1-mvp1",
  "pricing_source": "https://openai.com/api/pricing/ (retrieved 2026-10-14, gpt-4o/o1 reference rate)",
  "rates_per_million": {
    "input": 5.00,
    "cached_input": 2.50,
    "output": 15.00,
    "reasoning_output": 15.00
  },
  "calls": [
    {
      "call_index": 1,
      "logical_call": 1,
      "transport_attempt": 1,
      "purpose": "interpretation",
      "stage": "initial",
      "tokens": {
        "input_tokens": 12450,
        "cached_input_tokens": 8192,
        "cache_write_input_tokens": 0,
        "output_tokens": 850,
        "reasoning_output_tokens": 620
      },
      "wall_ms": {
        "request_ms": 12340.5,
        "backoff_wait_ms": 0.0,
        "queue_latency_ms": 120.0,
        "total_ms": 12460.5
      },
      "cost_usd": {
        "input_cost": 0.032065,
        "cached_input_cost": 0.020480,
        "output_cost": 0.012750,
        "total_cost": 0.065295,
        "cost_status": "calculated"
      },
      "transport": {
        "stdout_bytes": 4512,
        "stderr_bytes": 0,
        "exit_code": 0,
        "provider_rejected": false
      }
    }
  ],
  "episode_summary": {
    "total_calls": 2,
    "total_tokens": {
      "input": 28500,
      "cached_input": 16384,
      "output": 3200,
      "reasoning_output": 2100
    },
    "total_wall_s": 45.2,
    "total_wait_s": 0.0,
    "total_cost_usd": 0.165430,
    "cost_completeness": "complete"
  }
}
```

*Rule on Missing Values*: If any token counter cannot be parsed from stream headers/metadata, `tokens` is set to `null`, `total_cost` is set to `null`, and `cost_status` is marked `"missing_provider_tokens"`. No zero substitution.

---

## 5. Blind Holdout Authoring & Isolation Protocol

To ensure true scientific replication without data snooping:
1. **Blind Generator Role**: Gemini authors the holdout parameter sets, natural language briefs, and FreeCAD verification definitions in `design/cad-harness-verify-v4/holdout/`.
2. **Offline Validation Only**:
   - Holdout geometry is validated exclusively using offline geometric solvers in FreeCAD Python scripts (confirming target BRep volume, manifold solids, Euler-Poincare characteristics, and constraint solvability).
   - `python -B tools/smoke_verify_v4.py --data-only` validates schema conformance, rubric bindings, and SHA manifests.
   - **Zero Model Calls**: No test item prompt is ever evaluated against Sol or any LLM prior to suite freeze.
3. **Cryptographic Sealing**:
   - Manifest `SHA256.json` hashes all descriptions, gold standards, native controls, and tool scripts.
   - The evaluation suite is committed and pushed before running.
4. **Uninterrupted Execution**:
   - The holdout runs end-to-end in a single process invocation.
   - If a failure occurs, it is recorded. No pausing for mid-run bug fixes, no intermediate cherry-picking, and no multi-segment splicing.

---

## 6. Real Pilot Trial: Task Sourcing & Pre-Registered Rubric

### Task Sourcing (10 Real-World Engineering Requests)
- 10 distinct mechanical parts fitting the frozen compiler/source capabilities:
  - 3 turned stepped transmission shafts with retaining ring / seal grooves (e.g., DIN 5480 shaft segments).
  - 3 CNC aluminum mounting/adapter baseplates with counterbore hole patterns and pocket reliefs.
  - 2 turned flange bushings/spacers with concentric center bores and axial bolt holes.
  - 2 precision bearing positioning housings with internal stop shoulders.
- Input texts are raw engineering specifications (dimensions, functional tolerances, mounting interfaces) as provided by human engineers, without CAD hints or synthetic prompt scaffolding.

### Pre-Registered Evaluation Rubric
Each completed model is evaluated against four sequential gates:
1. **Build Gate (Automated)**: Headless build in FreeCAD 1.1.4 produces valid, manifold solid without topological errors (`exit_code == 0`).
2. **Dimension Fidelity Gate (Automated & Manual Inspection)**:
   - Zero tolerance on specified critical interface dimensions (bore diameters, shaft step lengths, bolt circle diameters match requested values within $\pm 0.01\text{ mm}$).
   - Any hallucinated feature, unrequested hole, or dimensional fabrication yields an immediate **FAIL (Fatal)**.
3. **Parametric Editability Gate (Automated)**:
   - Driving dimensions exist as accessible parameters in sketches or feature properties.
   - Modifying a primary functional dimension (e.g., shaft OD by $+2\text{ mm}$) recomputes cleanly without breaking model topology.
4. **Human Usability & Edit Time Gate (Manual Trial)**:
   - An engineer inspects the generated FreeCAD model in the GUI:
     - **Class A (Adopted As-Is)**: 0 minutes edit. Production ready.
     - **Class B (Minor Touch-up)**: $\le 5$ minutes edit (e.g., adjusting a cosmetic fillet or adding an unconstrained annotation).
     - **Class C (Rejected / Major Rework)**: $> 5$ minutes edit or topological regeneration needed.
   - **Pilot Target**: $\ge 70\%$ Class A or Class B (with Class C $< 30\%$).

---

## 7. Call Budget Allocation

| Task Cohort | Episodes | Calls / Episode (Min–Max) | Total Planned Calls | Max Budget Ceiling |
|---|---|---|---|---|
| Synthetic Holdout (Core + Legacy + Dev) | 60 | 1–4 | 83 | 163 |
| Real Design Pilot Trial | 10 | 1–4 | 20 | 40 |
| Overload / Transport Contingency Reserve | - | - | - | 17 |
| **Total V4 Campaign Ceiling** | **70** | - | **103** | **220 calls** |

- The Guard initializes with a hard ceiling of **220 calls**.
- Sol overload retries (`server_overloaded`) follow the established solfix policy: 600 s wait, byte-identical resend, uncharged to call budget and P/R slots.

---

## 8. Stop Rules & Invariants

- **Quota Stops**:
  - Soft threshold at **55%**: Process suspends, logs snapshot, and requests supervisor consultation.
  - Hard threshold at **60%**: Immediate clean shutdown of the suite.
- **Provider Overload**: Uncapped 600 s backoff and byte-identical resend on exact `server_overloaded`. Wall-clock wait is tracked in the ledger.
- **Stage & Episode Deadlines**:
  - Maximum 900 s per episode.
  - 450 s initial stage budget; 450 s repair stage budget.
  - 180 s Sol timeout for repair calls; 90 s CAD build/reimport timeout.
- **Suite Execution Invariant**:
  - Single uninterrupted monotonic clock for the holdout run.
  - Any unhandled exception or manifest mismatch terminates the run with a clear diagnostic state. No live database patching or selective re-execution.

---

## 9. Required User Decisions

Before final plan signing and execution, three explicit decisions are requested from the user:

1. **Pilot Task Origin**:
   - *Option A (User-Supplied)*: The user provides the 10 real engineering task descriptions from actual ongoing work.
   - *Option B (Catalog-Sourced)*: The planning team sources 10 standardized industrial parts from JIS/ISO mechanical engineering handbooks matching the capability profile.
   - *(Recommendation: Option A for maximal ecological validity).*

2. **Pricing Rate Standard**:
   - *Option A (Published Reference Rate)*: Bind rates to official published API schedules for equivalent frontier models (e.g. OpenAI o3/gpt-4o tier: $5.00/M in, $2.50/M cached in, $15.00/M out).
   - *Option B (Null Rate Ledger)*: Record exact token usage only, leaving dollar costs as `null` with reason `"internal_compute_cluster_unbilled"`.
   - *(Recommendation: Option A to fulfill the brief's cost measurement mandate).*

3. **Pilot Evaluation Protocol**:
   - *Option A (User Hands-on)*: The user (or an assigned design engineer) performs the GUI inspection and timed $\le 5$ min editing trial.
   - *Option B (Pair-Agent Protocol)*: One agent presents the generated model, while a second independent reviewer agent simulates the engineer inspection against pre-registered CAD rubrics.
   - *(Recommendation: Option A).*
