"""Strict edit validation and deterministic, measured composition."""
import copy
import json
import math

FEEDBACK_FIELDS = {"status", "failed_phase", "probe_status", "predicate_diff",
                   "message_code", "next_actor", "measurements", "cad_exit_code",
                   "script_completed", "cleanup_status", "timings_ms"}
SCALARS = {"set_max_attempts": "max_attempts", "set_feedback_fields": "feedback_fields",
           "set_reasoning_effort": "reasoning_effort"}


def validate_proposals(value, count):
    if not isinstance(value, dict) or set(value) != {"candidates"}:
        raise ValueError("Expected an object with candidates only")
    candidates = value["candidates"]
    if not isinstance(candidates, list) or len(candidates) != count:
        raise ValueError(f"Expected exactly {count} candidates")
    seen = set()
    for candidate in candidates:
        if (not isinstance(candidate, dict) or set(candidate) != {"edit", "rationale"}
                or not isinstance(candidate["rationale"], str) or not candidate["rationale"].strip()):
            raise ValueError("Each candidate needs edit and nonempty rationale")
        edit = candidate["edit"]
        if not isinstance(edit, list) or not edit:
            raise ValueError("edit must be a nonempty operation list")
        assigned = set()
        for operation in edit:
            if not isinstance(operation, dict) or set(operation) != {"op", "value"}:
                raise ValueError("Operations have only op and value")
            op, val = operation["op"], operation["value"]
            if not isinstance(op, str):
                raise ValueError("op must be a string")
            if op in ("add_rule", "add_snippet"):
                valid = isinstance(val, str) and bool(val.strip())
            elif op == "set_max_attempts":
                valid = type(val) is int and 1 <= val <= 4
            elif op == "set_feedback_fields":
                valid = (isinstance(val, list) and bool(val) and all(
                    isinstance(x, str) and x in FEEDBACK_FIELDS for x in val)
                    and len(val) == len(set(val)))
            elif op == "set_reasoning_effort":
                valid = isinstance(val, str) and val in ("low", "medium")
            else:
                valid = False
            if not valid:
                raise ValueError(f"Invalid operation: {op}")
            if op in SCALARS:
                if op in assigned:
                    raise ValueError("Repeated scalar assignment within one edit")
                assigned.add(op)
        # Operation order does not make otherwise identical edits distinct.
        key = json.dumps(sorted(edit, key=lambda x: json.dumps(x, sort_keys=True)), sort_keys=True)
        if key in seen:
            raise ValueError("Candidates must have distinct edits")
        seen.add(key)
    return candidates


def apply_edits(base, edits):
    """First (highest ranked) scalar assignment wins; additive values are deduplicated."""
    result = copy.deepcopy(base)
    assigned = set()
    for edit in edits:
        for operation in edit:
            op, value = operation["op"], copy.deepcopy(operation["value"])
            if op in ("add_rule", "add_snippet"):
                target = result["rules" if op == "add_rule" else "snippets"]
                if value not in target:
                    target.append(value)
            elif op not in assigned:
                assigned.add(op)
                target = result["executor"] if op == "set_reasoning_effort" else result
                target[SCALARS[op]] = value
    return result


def rank(run):
    tokens = run["tokens"]["total"]
    return (not run["geometry_pass"], run["attempt_count"],
            tokens if tokens is not None else math.inf, run["wall_ms"])


def verdict(base, probe):
    if not probe["geometry_pass"]:
        return "unsupported"
    # An unmeasured probe or infrastructure failure is not comparative evidence.
    if any(a["result"].get("next_actor") == "human" for a in base["attempts"]):
        return "confounded"
    if base["tokens"]["total"] is None or probe["tokens"]["total"] is None:
        return "confounded"
    comparisons = [int(probe["geometry_pass"]) - int(base["geometry_pass"]),
                   base["attempt_count"] - probe["attempt_count"]]
    for old, new in ((base["tokens"]["total"], probe["tokens"]["total"]),
                     (base["wall_ms"], probe["wall_ms"])):
        comparisons.append(1 if new < old * .9 else -1 if new > old * 1.1 else 0)
    return "supported" if min(comparisons) >= 0 and max(comparisons) > 0 else "unsupported"
