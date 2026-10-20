"""D15 repeated-run summaries and deterministic decisions (no LLM calls)."""
import math
from statistics import mean, stdev

from .runtime import TOKEN_KEYS, sum_tokens


def distribution(values):
    if not values or any(v is None for v in values):
        return {"mean": None, "std": None}
    return {"mean": mean(values), "std": stdev(values) if len(values) > 1 else 0.0}


def cache_metrics(tokens):
    total, cached = tokens["input"], tokens["cached_input"]
    ratio = cached / total if total and cached is not None and 0 <= cached <= total else None
    return {"cached_input": cached, "uncached_input": tokens["uncached_input"],
            "cached_input_ratio": ratio, "uncached_input_ratio": 1 - ratio if ratio is not None else None}


def summarize(names, runs):
    samples = [runs[name] for name in names]
    tokens = sum_tokens([{"tokens": run["tokens"]} for run in samples])
    count = sum(run["geometry_pass"] for run in samples)
    return {"n": len(samples), "run_names": names, "pass_count": count,
            "pass_rate": count / len(samples), "geometry_pass": count == len(samples),
            "attempt_count": sum(run["attempt_count"] for run in samples), "tokens": tokens,
            "wall_ms": sum(run["wall_ms"] for run in samples), "cache": cache_metrics(tokens),
            "infrastructure_failure": any(a["result"].get("next_actor") == "human"
                                          for run in samples for a in run["attempts"]),
            "statistics": {"attempts": distribution([r["attempt_count"] for r in samples]),
                           "wall_ms": distribution([r["wall_ms"] for r in samples]),
                           "tokens": {key: distribution([r["tokens"][key] for r in samples])
                                      for key in TOKEN_KEYS}}}


def rank_group(group):
    def known(value):
        return value if value is not None else math.inf
    stats = group["statistics"]
    return (-group["pass_rate"], stats["attempts"]["mean"],
            known(stats["tokens"]["total"]["mean"]), known(stats["wall_ms"]["mean"]))


def decide(base, probe):
    """D15: rate first; equal rate needs >10% saving larger than both sample SDs."""
    result = {"rule": "D15", "verdict": "unsupported", "qualifying_metrics": []}
    if base["n"] != probe["n"] or base["infrastructure_failure"] or probe["infrastructure_failure"]:
        return {**result, "verdict": "confounded", "reason": "incomplete_or_infrastructure_failure"}
    if probe["pass_rate"] < base["pass_rate"]:
        return {**result, "reason": "lower_pass_rate"}
    if probe["pass_rate"] > base["pass_rate"]:
        return {**result, "verdict": "supported", "qualifying_metrics": ["pass_rate"]}
    missing = False
    for metric, old, new in (
            ("tokens", base["statistics"]["tokens"]["total"], probe["statistics"]["tokens"]["total"]),
            ("wall_ms", base["statistics"]["wall_ms"], probe["statistics"]["wall_ms"])):
        if any(v is None for v in (old["mean"], old["std"], new["mean"], new["std"])):
            missing = True
            continue
        saving = old["mean"] - new["mean"]
        if saving > old["mean"] * .1 and saving > max(old["std"], new["std"]):
            result["qualifying_metrics"].append(metric)
    if result["qualifying_metrics"]:
        result["verdict"] = "supported"
    elif missing:
        result.update(verdict="confounded", reason="missing_comparison_metrics")
    else:
        result["reason"] = "no_saving_exceeds_ten_percent_and_noise"
    return result
