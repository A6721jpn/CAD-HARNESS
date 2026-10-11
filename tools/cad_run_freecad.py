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


def execute(app, builder, model_path, emit, probe_fn=None, task_id=TASK_A):
    """The actual exception boundary, also exercised with a fake App in unit tests."""
    probe_fn = probe_fn or SPECS[task_id]["probe"]
    result = {"task_id": task_id, "timings_ms": dict.fromkeys(("build", "recompute", "probe", "save")),
              "status": "failed", "failed_phase": None, "code_owner": None,
              "next_actor": None, "script_completed": False, "probe_pass": None,
              "probe_status": "not_run", "measurements": None, "predicate_diff": None,
              "document_closed": False, "owned_pid": os.getpid(),
              "gui_up": getattr(app, "GuiUp", None), "freecad_version": list(app.Version())}
    doc, phase, owner = None, "launch", "harness"
    emit("ready", {"owned_pid": result["owned_pid"], "gui_up": result["gui_up"]})
    try:
        if result["gui_up"] != 0 or result["freecad_version"][:3] != ["1", "1", "4"]:
            raise RuntimeError("unsupported_runtime")
        if app.listDocuments():
            raise RuntimeError("startup_documents")
        doc = app.newDocument("CadRunA" if task_id == TASK_A else "CadRunB")
        phase, owner = "build", "script"
        with stage(result, "build"):
            body = builder(doc)
        if body is None or body.Document != doc or body.TypeId != "PartDesign::Body":
            raise ValueError("build_contract")
        if set(app.listDocuments()) != {doc.Name}:
            raise ValueError("build_document_contract")
        owner = "harness"
        with stage(result, "recompute"):
            doc.recompute()
        emit("event", {"phase": "build", "event": "build_finished", "status": "ok"})
        phase, owner = "probe", "probe"
        with stage(result, "probe"):
            observed = probe_fn(doc, body)
        result.update(probe_pass=observed["probe_pass"],
                      probe_status="pass" if observed["probe_pass"] else "predicate_fail",
                      measurements=observed["measurements"], reference=observed.get("reference"),
                      predicate_diff=[k for k, passed in observed["predicates"].items() if not passed])
        if not result["probe_pass"]:
            result.update(failed_phase="probe", code_owner="script", next_actor="sol")
        emit("event", {"phase": "probe", "event": "probe_finished",
                      "status": "ok" if observed["probe_pass"] else "failed",
                      "data": {"predicate": observed["predicates"]}})
        phase, owner = "build", "harness"
        with stage(result, "save"):
            doc.saveAs(str(model_path))
            if not Path(model_path).is_file():
                raise OSError("model_missing")
        result["script_completed"] = True
        if result["failed_phase"] is None:
            result["status"] = "ok"
    except Exception as exc:
        result["status"] = "failed"
        if result["failed_phase"] is None:
            result.update(failed_phase=phase, code_owner=owner,
                          next_actor="sol" if owner == "script" else "human",
                          error_type=type(exc).__name__)
            if phase == "probe":
                result.update(probe_pass=None, probe_status="exception")
        else:
            result["save_error_type"] = type(exc).__name__
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
            result = execute(App, builder, Path.cwd() / "model.FCStd", emit,
                             task_id=request.get("task_id", TASK_A))
        except Exception as exc:
            result = {"status": "failed", "failed_phase": "launch", "code_owner": "harness",
                      "next_actor": "human", "script_completed": False, "probe_status": "not_run",
                      "probe_pass": None, "document_closed": False, "owned_pid": os.getpid(),
                      "error_type": type(exc).__name__}
        result.setdefault("timings_ms", dict.fromkeys(("build", "recompute", "probe", "save")))
        result.update(task_id=request.get("task_id", TASK_A), schema="cad-harness.cad_run.worker.v0",
                      attempt_id=request["attempt_id"], script_sha256=request["script_sha256"])
        with (Path.cwd() / "worker-result.json").open("x", encoding="utf-8") as output:
            json.dump(result, output, allow_nan=False)
    # FreeCAD's console recipe consumes empty stdin and exits; raw CAD exit is host-owned.


if __name__ == "__main__" or ("FreeCAD" in sys.modules and (Path.cwd() / "request.json").is_file()):
    main()
