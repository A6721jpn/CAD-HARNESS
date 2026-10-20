"""Append measured accounting corrections without replacing historical values.

python -m h2.supplement --cycle-id 20261020T151238Z-e7120eed
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .cycle import ROOT, save_json
from .runtime import parse_events, reported_model, sum_tokens


def supplement_cycle(root, cycle_id):
    root = Path(root).resolve()
    report = root / "reports" / "h2" / cycle_id / "cycle.json"
    if not report.resolve().is_relative_to(root / "reports" / "h2"):
        raise ValueError("Cycle report must remain under reports/h2")
    data = json.loads(report.read_text(encoding="utf-8"))
    measured, evidence = [], []
    for call in data["llm_calls"]:
        path = (root / call["log_dir"] / "events.jsonl").resolve()
        if not path.is_relative_to(report.parent.resolve()):
            raise ValueError("Event evidence must remain within the cycle directory")
        raw = path.read_bytes()
        stdout = raw.decode("utf-8")
        _, tokens = parse_events(stdout)
        measured.append({"call_id": call["call_id"], "tokens": tokens, **reported_model(stdout)})
        evidence.append({"call_id": call["call_id"], "path": str(path.relative_to(root)),
                         "sha256": hashlib.sha256(raw).hexdigest()})
    identity = hashlib.sha256(json.dumps({"schema": "h2.accounting-supplement.v1",
                                          "cycle_id": cycle_id, "evidence": evidence},
                                         sort_keys=True).encode("utf-8")).hexdigest()[:24]
    existing = next((s for s in data.get("accounting_supplements", [])
                     if s["supplement_id"] == identity), None)
    created = existing["created_at"] if existing else datetime.now(timezone.utc).isoformat()
    calls = {call["call_id"]: call for call in measured}
    runs = {name: {"tokens": sum_tokens([calls[a["llm_call_id"]] for a in run["attempts"]])}
            for name, run in data["runs"].items()}
    supplements = []
    for entry in data["library_entries"]:
        corrected = copy.deepcopy(entry)
        corrected.update(entry_id=f'{identity}-{entry["entry_id"]}', created_at=created,
                         entry_type="measurement_supplement", supplements_entry_id=entry["entry_id"],
                         supplement_id=identity)
        variant = next(c["variant"] for c in data["proposals"] if c["edit"] == entry["edit"])
        corrected["contrast"]["run0"]["tokens"] = runs["run0"]["tokens"]
        corrected["contrast"]["probe"]["tokens"] = runs[variant]["tokens"]
        corrected["lesson"] = ("Accounting supplement only; no new experiment or changed verdict. "
                               f'Original lesson and measurements remain in entry {entry["entry_id"]}.')
        supplements.append(corrected)
    supplement = {"schema": "h2.accounting-supplement.v1", "supplement_id": identity,
                  "created_at": created, "method": "reaggregate_original_runtime_events",
                  "original_values_preserved": True,
                  "total_rule": "input + output; cached input and reasoning are subsets",
                  "evidence": evidence, "llm_calls": measured, "runs": runs,
                  "tokens": sum_tokens(measured), "library_entries": supplements}
    # Fail before writing if any available original token count would change.
    def check(original, recomputed):
        for key, value in original.items():
            if value is not None and value != recomputed.get(key):
                raise ValueError(f"Historical {key} differs from raw evidence; refusing correction")
    check(data["tokens"], supplement["tokens"])
    for original in data["llm_calls"]:
        check(original["tokens"], calls[original["call_id"]]["tokens"])
    for name, run in data["runs"].items():
        check(run["tokens"], runs[name]["tokens"])
    library = root / "h2" / "library" / "cad-freecad.jsonl"
    rows = [json.loads(line) for line in library.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = {row["entry_id"] for row in rows}
    originals = {entry["entry_id"]: entry for entry in data["library_entries"]}
    for row in rows:
        if row["entry_id"] in originals and row != originals[row["entry_id"]]:
            raise ValueError("Library original differs from cycle evidence")
    if not set(originals).issubset(ids):
        raise ValueError("Original library entries are missing")
    # Append only, and stable IDs make reruns safe after a partial write.
    with library.open("a", encoding="utf-8") as stream:
        for entry in supplements:
            if entry["entry_id"] not in ids:
                stream.write(json.dumps(entry, ensure_ascii=False, allow_nan=False) + "\n")
                ids.add(entry["entry_id"])
    if not existing:
        data.setdefault("accounting_supplements", []).append(supplement)
        save_json(report, data)
    return existing or supplement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cycle-id", required=True)
    args = parser.parse_args()
    data = supplement_cycle(ROOT, args.cycle_id)
    print(json.dumps({"supplement_id": data["supplement_id"], "tokens": data["tokens"],
                      "library_supplements": len(data["library_entries"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
