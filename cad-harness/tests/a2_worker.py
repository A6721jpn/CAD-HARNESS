"""FreeCADCmd entry point. Always record failures; process exit alone is insufficient."""
import json
import os
from pathlib import Path
import sys
import traceback
import unittest

out = Path(os.environ["A2_OUTPUT"])
stage = os.environ["A2_STAGE"]
report = {"stage": stage, "pid": os.getpid(), "python": sys.version, "passed": False}
try:
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import FreeCAD as App
    import test_a2_native as tests
    report["freecad_version"] = App.Version()
    cls = tests.BuildTests if stage == "build" else tests.ReopenTests
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(cls)
    if stage == "build":
        import test_contracts
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(test_contracts))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report.update(passed=result.wasSuccessful(), tests_run=result.testsRun,
                  skipped=result.skipped, failures=result.failures, errors=result.errors,
                  measurements=tests.RECORDS)
    # Test objects in failures/errors are not JSON values.
    for key in ("failures", "errors", "skipped"):
        report[key] = [[str(test), detail] for test, detail in report[key]]
except BaseException:
    report["exception"] = traceback.format_exc()
    traceback.print_exc()
finally:
    (out / (stage + ".json")).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("A2_RESULT " + json.dumps({"stage": stage, "passed": report["passed"]}))
