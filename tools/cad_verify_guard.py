"""Supervisor quota snapshots and a shared, monotonic Phase 3 deadline."""
from datetime import datetime, timezone
import hashlib
import math
from pathlib import Path
import time

if __package__:
    from .cad_spec_probe import read_json
else:
    from cad_spec_probe import read_json

CLEANUP_RESERVE_S = 5


class Stop(ValueError):
    pass


def quota_snapshot(path, now=None):
    now = now or datetime.now(timezone.utc)
    try:
        raw = Path(path).read_bytes()
        data = read_json(raw.decode("utf-8"))
    except (OSError, ValueError, UnicodeError, TypeError):
        raise Stop("quota_snapshot_missing_or_invalid") from None
    if (not isinstance(data,dict) or set(data) != {"snapshot_id","observed_at","used_percent"}
            or not isinstance(data["snapshot_id"],str) or not data["snapshot_id"].strip()
            or not isinstance(data["observed_at"],str)
            or type(data["used_percent"]) not in (int,float)
            or not math.isfinite(data["used_percent"]) or not 0 <= data["used_percent"] <= 100):
        raise Stop("quota_snapshot_invalid")
    try:
        observed = datetime.fromisoformat(data["observed_at"].replace("Z","+00:00"))
        if observed.tzinfo is None:
            raise ValueError("timezone_required")
        age = (now-observed).total_seconds()
    except (ValueError,TypeError):
        raise Stop("quota_snapshot_invalid_time") from None
    record = {**data,"sha256":hashlib.sha256(raw).hexdigest(),"age_s":age,
              "checked_at":now.isoformat(),"decision":"allow"}
    if age < 0: record["decision"]="quota_snapshot_future"
    elif age > 300: record["decision"]="quota_snapshot_stale"
    elif data["used_percent"] >= 60: record["decision"]="quota_hard_stop"
    elif data["used_percent"] >= 55: record["decision"]="quota_soft_stop"
    return record


class Guard:
    """One object shared by dev, legacy, fresh MVP, VERIFY, and aggregation."""
    def __init__(self,snapshot,seconds=10800,call_budget=125,clock=None,now=None,check_versions=None):
        if seconds != 10800 or type(call_budget) is not int or not 1 <= call_budget <= 125:
            raise ValueError("verify_guard_contract")
        self.clock = clock or time.monotonic
        self.now = now or (lambda:datetime.now(timezone.utc))
        self.started = self.clock()
        self.deadline = self.started+seconds
        self.snapshot = Path(snapshot)
        self.call_budget, self.calls = call_budget, 0
        self.snapshots = []
        self.check_versions = check_versions or (lambda:None)

    def remaining(self,reserve=CLEANUP_RESERVE_S):
        left = self.deadline-self.clock()-reserve
        if left <= 0: raise Stop("shared_deadline_exceeded")
        return left

    def before_run(self,minimum_calls=0):
        self.remaining()
        self.check_versions()
        if self.call_budget-self.calls < minimum_calls:
            raise Stop("insufficient_call_budget")

    def before_call(self):
        self.before_run(1)
        record=quota_snapshot(self.snapshot,self.now())
        self.snapshots.append(record)
        if record["decision"] != "allow": raise Stop(record["decision"])
        self.calls += 1
        return record


class Fault:
    """A frozen replacement, consumed once after a valid original candidate."""
    def __init__(self,path):
        self.path=Path(path)
        self.rule=read_json(self.path.read_text(encoding="utf-8"))
        self.attempted=False
        self.record={"fault_id":self.rule["fault_id"],"injected":False,"reached":False,
                     "established":False,"detected":False,"original_sha256":None,"injected_sha256":None}

    def inject(self,kind,candidate):
        import copy
        import json
        if self.attempted or kind != self.rule["kind"]: return candidate
        self.attempted=True
        canonical=lambda v:json.dumps(v,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(",",":"))
        original=candidate if kind=="source" else canonical(candidate)
        self.record.update(original_sha256=hashlib.sha256(original.encode("utf-8")).hexdigest())
        artifact=self.path.parent/self.rule["candidate"]
        raw=artifact.read_bytes()
        self.record["candidate_sha256"]=hashlib.sha256(raw).hexdigest()
        if kind=="source":
            result=raw.decode("utf-8")
        else:
            result=copy.deepcopy(candidate)
            node=result
            for key in self.rule["path"]:
                if not isinstance(node,dict) or key not in node:
                    self.record["not_reached_reason"]="candidate_target_missing"
                    return candidate
                node=node[key]
            matches=[v for v in node if isinstance(v,dict) and all(v.get(k)==value for k,value in self.rule["match"].items())] if isinstance(node,list) else []
            if len(matches)!=1:
                self.record["not_reached_reason"]="candidate_target_missing"
                return candidate
            matches[0].update(self.rule["set"])
            result=canonical(result)
            if json.loads(result) != read_json(raw.decode("utf-8")):
                # The actual frozen numeric mutation may be applied to a
                # different valid spec, but only the matched hole is changed.
                self.record["whole_candidate_equal"]=False
            result=json.loads(result)
        injected=result if kind=="source" else canonical(result)
        self.record.update(reached=True,injected=True,injected_sha256=hashlib.sha256(injected.encode("utf-8")).hexdigest())
        return result

    def observe(self,result,call):
        if not self.record["injected"] or self.record.get("observed"): return
        self.record.update(observed=True,actual_call=call)
        settled=(result.get("script_completed") is True and result.get("document_closed") is True
                 and result.get("cleanup_status")=="exited" and result.get("cad_exit_code")==0
                 and result.get("probe_status")=="predicate_fail" and result.get("geometry_ok") is False
                 and (result.get("measurements") or {}).get("editability",{}).get("native_valid") is True)
        detected=settled and self.rule["expected_predicate"] in result.get("predicate_diff",[])
        self.record.update(established=settled,detected=detected)


CLARIFICATION_FIELDS = ("plate_thickness","hole_positions","hole_diameter","pocket_depth",
                       "pocket_size","stock_dimensions","axis","finish_size")
QUESTIONS = {"plate_thickness":"板の厚さを指定してください。","hole_positions":"穴の中心位置を指定してください。"}


def clarification(value):
    fields=value.get("needs_clarification") if isinstance(value,dict) and set(value)=={"needs_clarification"} else None
    if (not isinstance(fields,list) or not fields or len(fields)!=len(set(fields))
            or any(not isinstance(f,str) or f not in CLARIFICATION_FIELDS for f in fields)):
        raise ValueError("clarification_field_contract")
    return fields


def q_score(first,passed,case,rubric=None):
    if rubric is not None:
        fields=first.get("fields") if first else None
        correct=first is not None and first.get("kind")=="needs_clarification" and fields==rubric["required_fields"]
        raw=first.get("raw") if first else None
        invention=False
        if isinstance(raw,dict):
            if rubric["critical_invention_field"]=="plate_thickness":
                invention=bool(raw.get("regions")) or "plate_thickness" in raw
            else:
                invention=bool(raw.get("holes")) or "hole_positions" in raw
        return int(correct),invention
    return int(bool(first and first.get("kind")=="spec" and first.get("binding_defaults_ok") and passed)),False
