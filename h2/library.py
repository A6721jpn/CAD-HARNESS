"""Present append-only measurement corrections as one lesson per original entry."""
import copy


def materialize_library(rows):
    originals = {}
    for row in rows:
        if row.get("entry_type") != "measurement_supplement":
            if row["entry_id"] in originals:
                raise ValueError("Duplicate original library entry id")
            originals[row["entry_id"]] = copy.deepcopy(row)
    for row in rows:
        if row.get("entry_type") != "measurement_supplement":
            continue
        target = originals.get(row["supplements_entry_id"])
        if target is None:
            raise ValueError("Measurement supplement has no original entry")
        for field in ("domain", "task_id", "cycle_id", "edit", "verdict"):
            if row[field] != target[field]:
                raise ValueError(f"Supplement changes original {field}")
        for side in ("run0", "probe"):
            tokens = target["contrast"][side]["tokens"]
            for key, value in row["contrast"][side]["tokens"].items():
                if value is None:
                    continue
                if tokens.get(key) is not None and tokens[key] != value:
                    raise ValueError("Conflicting supplemented token count")
                tokens[key] = value
        target.setdefault("measurement_supplements", []).append({
            key: row[key] for key in ("entry_id", "supplement_id", "created_at")})
    return list(originals.values())
