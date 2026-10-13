"""CAD worker for fixed task probes; ordinary Python imports do not load CAD."""
from contextlib import contextmanager
from datetime import datetime, timezone
import time
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys

if __package__:
    from .cad_run_probes import (TOL, GOAL_VOLUME, BOX_KEYS, near, bbox, numeric_predicates,
                                 matches, rectangle_segments, covers, inner_predicate,
                                 link, edge_record, probe, SPECS, TASK_A)
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from cad_run_probes import (TOL, GOAL_VOLUME, BOX_KEYS, near, bbox, numeric_predicates,
                                matches, rectangle_segments, covers, inner_predicate,
                                link, edge_record, probe, SPECS, TASK_A)


@contextmanager
def stage(result, name):
    started = time.monotonic()
    try:
        yield
    finally:
        result["timings_ms"][name] = (time.monotonic() - started) * 1000


def worker_row(kind, payload):
    return {"kind": kind, **payload, "ts": datetime.now(timezone.utc).isoformat()}


def execute(app, builder, model_path, emit, probe_fn=None, task_id=TASK_A,
            step_path=None, generator="agent", profile=None):
    """The actual exception boundary, also exercised with a fake App in unit tests."""
    probe_fn = probe_fn or SPECS[task_id]["probe"]
    result = {"task_id": task_id, "timings_ms": dict.fromkeys(("build", "recompute", "probe", "save")),
              "status": "failed", "failed_phase": None, "code_owner": None,
              "next_actor": None, "script_completed": False, "probe_pass": None,
              "probe_status": "not_run", "measurements": None, "predicate_diff": None,
              "document_closed": False, "owned_pid": os.getpid(),
              "gui_up": getattr(app, "GuiUp", None), "freecad_version": list(app.Version())}
    if profile=="verify-v3":
        result["stage_statuses"]=dict.fromkeys(("build","geometry","editability","export","reimport"),"not_reached")
        result["stage_measurements"]=dict.fromkeys(result["stage_statuses"])
    doc, phase, owner = None, "launch", "harness"
    emit("ready", {"owned_pid": result["owned_pid"], "gui_up": result["gui_up"]})
    try:
        if result["gui_up"] != 0 or result["freecad_version"][:3] != ["1", "1", "4"]:
            raise RuntimeError("unsupported_runtime")
        if app.listDocuments():
            raise RuntimeError("startup_documents")
        doc = app.newDocument("CadRunA" if task_id == TASK_A else "CadRunB")
        phase, owner = "build", "harness" if generator == "compiler" else "script"
        with stage(result, "build"):
            body = builder(doc)
        if body is None or body.Document != doc or body.TypeId != "PartDesign::Body":
            raise ValueError("build_contract")
        if set(app.listDocuments()) != {doc.Name}:
            raise ValueError("build_document_contract")
        owner = "harness"
        with stage(result, "recompute"):
            doc.recompute()
        if profile=="verify-v3":result["stage_statuses"]["build"]="pass"
        emit("event", {"phase": "build", "event": "build_finished", "status": "ok"})
        phase, owner = "probe", "probe"
        with stage(result, "probe"):
            observed = probe_fn(doc, body)
        result.update(probe_pass=observed["probe_pass"],
                      probe_status="pass" if observed["probe_pass"] else "predicate_fail",
                      measurements=observed["measurements"], reference=observed.get("reference"),
                      predicate_diff=[k for k, passed in observed["predicates"].items() if not passed])
        result.update({key: observed.get(key) for key in
                       ("predicate_details", "geometry_ok", "editability_ok", "skill_warnings")})
        if profile=="verify-v3":
            for key,flag in (("geometry","geometry_ok"),("editability","editability_ok")):
                result["stage_statuses"][key]="pass" if observed.get(flag) is True else "fail"
                result["stage_measurements"][key]=observed.get("measurements") if key=="geometry" else (observed.get("measurements") or {}).get("editability")
        if not result["probe_pass"]:
            compiler_native = profile != "verify-v3" and generator == "compiler" and observed.get("editability_ok") is False
            result.update(failed_phase="probe", code_owner="harness" if compiler_native else "script",
                          next_actor="human" if compiler_native else "sol")
        emit("event", {"phase": "probe", "event": "probe_finished",
                      "status": "ok" if observed["probe_pass"] else "failed",
                      "data": {"predicate": observed["predicates"]}})
        phase, owner = "build", "harness"
        with stage(result, "save"):
            doc.saveAs(str(model_path))
            if not Path(model_path).is_file():
                raise OSError("model_missing")
        if step_path is not None and result["probe_pass"]:
            phase, owner = "export", "harness"
            tick = time.monotonic()
            if profile=="verify-v3":result["stage_statuses"]["export"]="fail"
            try:
                import Part
                # Body.Shape contains the current Tip solid in its world placement.
                Part.export([body], str(step_path))
                if not Path(step_path).is_file() or Path(step_path).stat().st_size == 0:
                    raise OSError("step_missing")
                if profile=="verify-v3":result["stage_statuses"]["export"]="pass"
            finally:
                result["export_ms"] = (time.monotonic() - tick) * 1000
        result["script_completed"] = True
        if result["failed_phase"] is None:
            result["status"] = "ok"
    except Exception as exc:
        result["status"] = "failed"
        if profile=="verify-v3" and phase=="build" and result["stage_statuses"]["build"]!="pass":result["stage_statuses"]["build"]="fail"
        if result["failed_phase"] is None:
            result.update(failed_phase=phase, code_owner=owner,
                          next_actor="sol" if owner == "script" else "human",
                          error_type=type(exc).__name__)
            if phase == "probe":
                result.update(probe_pass=None, probe_status="exception")
        else:
            result["save_error_type"] = type(exc).__name__
        if phase == "export":
            result["export_error_type"] = type(exc).__name__
        emit("event", {"phase": phase, "event": phase + "_finished", "status": "failed"})
    finally:
        if doc is not None:
            try:
                app.closeDocument(doc.Name)
                result["document_closed"] = not app.listDocuments()
            except Exception as exc:
                result["close_error_type"] = type(exc).__name__
        if not result["document_closed"]:
            result["status"] = "failed"
            if result["failed_phase"] is None:
                result.update(failed_phase="cleanup", code_owner="harness", next_actor="human")
    return result


def main():
    request = json.loads((Path.cwd() / "request.json").read_text(encoding="utf-8"))
    with (Path.cwd() / "worker-events.jsonl").open("x", encoding="utf-8") as stream:
        def emit(kind, payload):
            stream.write(json.dumps(worker_row(kind, payload), allow_nan=False) + "\n")
            stream.flush()
        try:
            import FreeCAD as App
            def builder(doc):
                source = Path.cwd() / "input.py"
                if hashlib.sha256(source.read_bytes()).hexdigest() != request["script_sha256"]:
                    raise ValueError("input_hash_mismatch")
                namespace = runpy.run_path(str(source))
                return namespace["build"](doc)
            probe_fn, step_path = None, None
            if request.get("probe_profile") in ("mvp-v1","verify-v1","verify-v2","verify-v3"):
                if request["probe_profile"] == "verify-v3":
                    from cad_verify_v3_probe import load_gold, probe as spec_probe
                elif request["probe_profile"] == "verify-v2":
                    from cad_verify_v2_probe import load_gold, probe as spec_probe
                elif request["probe_profile"] == "verify-v1":
                    from cad_verify_probe import load_gold, probe as spec_probe
                else:
                    from cad_spec_probe import load_gold, probe as spec_probe
                gold_path = Path.cwd() / "gold.json"
                if hashlib.sha256(gold_path.read_bytes()).hexdigest() != request["gold_sha256"]:
                    raise ValueError("gold_hash_mismatch")
                gold = load_gold(gold_path)
                if gold["case_id"] != request["task_id"]:
                    raise ValueError("gold_task_mismatch")
                probe_fn = lambda doc, body: spec_probe(doc, body, gold)
                step_path = Path.cwd() / "model.step"
            result = execute(App, builder, Path.cwd() / "model.FCStd", emit, probe_fn,
                             task_id=request.get("task_id", TASK_A), step_path=step_path,
                             generator=request.get("generator", "agent"), profile=request.get("probe_profile"))
        except Exception as exc:
            result = {"status": "failed", "failed_phase": "launch", "code_owner": "harness",
                      "next_actor": "human", "script_completed": False, "probe_status": "not_run",
                      "probe_pass": None, "document_closed": False, "owned_pid": os.getpid(),
                      "error_type": type(exc).__name__}
        result.setdefault("timings_ms", dict.fromkeys(("build", "recompute", "probe", "save")))
        result.update(task_id=request.get("task_id", TASK_A), schema="cad-harness.cad_run.worker.v0",
                      attempt_id=request["attempt_id"], script_sha256=request["script_sha256"])
        result.update({key: request.get(key) for key in
                       ("probe_profile", "gold_sha256", "spec_sha256", "generator")})
        with (Path.cwd() / "worker-result.json").open("x", encoding="utf-8") as output:
            json.dump(result, output, allow_nan=False)
    # FreeCAD's console recipe consumes empty stdin and exits; raw CAD exit is host-owned.


if __name__ == "__main__" or ("FreeCAD" in sys.modules and (Path.cwd() / "request.json").is_file()):
    main()
