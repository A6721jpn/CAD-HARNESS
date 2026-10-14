# Phase 3 review — v4grok

READY

Reviewed `impl-notes-p3.md` and `tools/cad_verify_v4_{freeze,live,pilot}.py`. No live model call, no CAD generation, no commit, no private holdout or pilot-user STEP/PNG opened.

`python -B -m unittest tools.test_verify_v3 tools.test_verify_v4 tools.test_verify_v4_freeze tools.test_verify_v4_pilot tools.test_verify_v4_live`: 92 tests, OK, 5.465 s.

Checked: live launch requires a holdout authorization of 163 calls, clock confirmation, and `independent_control_validation`; offline freeze is not authorization. Policy drift rejects resume/retake and borrowing. Overload exemption is only a complete `server_overloaded` stream with no assistant output, then a 600 s identical resend. Generator stdin is `DEVNULL`. Private holdout paths are rejected. The pilot CLI uses a 40,000 Unicode-character contiguous window and a 1-based physical-line locator, and fails E6/E7 without enrollment.

Not claimed: live omp, native CAD, overload recovery, or a fresh holdout. The attachment descriptor does not by itself prove dependency completeness.
