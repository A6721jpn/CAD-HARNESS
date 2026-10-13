# Gemini Implementation Review: VERIFY v3

Verdict: **BLOCK**

---

## 1. Executive Summary

Gemini has completed the authoring and validation of all independent native controls specified in [`native-controls-handoff.md`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/native-controls-handoff.md):
- Standalone native helper library: [`tools/fixtures/verify_v3_native.py`](file:///C:/dev/CAD-HARNESS/tools/fixtures/verify_v3_native.py)
- Dev matrix specification and sources: [`design/cad-harness-verify-v3/dev/native-matrix.json`](file:///C:/dev/CAD-HARNESS/design/cad-harness-verify-v3/dev/native-matrix.json) (8 positive IDs, 11 negative IDs, 2 parameter edit specs with exact analytic volume anchors $7039.875\pi$ and $7083.1875\pi$, and 21 runnable sources)
- Complete holdout controls across all 13 geometry cases: `test/{G1..G6,S3,A4,C4,C5,F4..F6}/{positive.py,negative.py,offline.json}`
- Fault candidates: `test/F4/candidate.py` and `test/F5/candidate.py`
- Empirical validation: All pre-check contracts (`eval_verify_v3.require_controls`) and headless smoke runs (`tools/smoke_verify_v3.py --run gemini-verify-v3-native-check-r3-mvp1`) executed and passed 100% across all 50 cases (21 dev matrix/edits + 26 holdout controls + 3 fault injections).

However, code review and headless C++ FreeCAD runtime testing revealed a **critical blocker** in [`tools/cad_verify_v3_probe.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py). Calling `s.getDriving(i)` on geometric constraints crashes FreeCAD's Sketcher with `ValueError: Invalid constraint id`. This prevents production evaluation of models using standard geometric constraints and must be resolved before freeze or live measurement.

---

## 2. Findings

### MUST (Blockers)

#### 1. FreeCAD Sketcher Crash in `active()` on Geometric Constraints
- **File / Lines**: [`tools/cad_verify_v3_probe.py:96`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L96), with crash call sites at lines 140, 158, 192, 359, and 385.
- **Description**:
  [`tools/cad_verify_v3_probe.py:96`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L96) defines:
  ```python
  def active(s, i): return s.getActive(i) and s.getDriving(i)
  ```
  In FreeCAD 1.1.4 C++ Sketcher (`Sketcher::SketchObject`), `s.getDriving(i)` is valid **only** for datum dimensional constraints (`Distance`, `DistanceX`, `DistanceY`, `Radius`, `Diameter`, `Angle`). Calling `s.getDriving(i)` on any non-dimensional geometric constraint (`Coincident`, `Horizontal`, `Vertical`, `Equal`, `Symmetric`, `PointOnObject`) immediately throws:
  ```
  <class 'ValueError'>: Invalid constraint id
  ```
- **Crash Call Sites**:
  1. **Line 140 (`attachment`)**:
     ```python
     for n, c in enumerate(s.Constraints):
         if not active(s, n): continue
         f = (getattr(c, 'First', -1), getattr(c, 'FirstPos', 0)) ...
         if c.Type == 'Coincident':
     ```
     `active(s, n)` is evaluated on all constraints in the sketch before checking `c.Type == 'Coincident'`. Any sketch containing geometric constraints crashes here.
  2. **Line 158 (`relation_axis`)**:
     ```python
     alignment = [x for n, x in enumerate(s.Constraints)
                  if active(s, n) and x.Type in ('Horizontal', 'Vertical') and x.First == c.First]
     ```
     Evaluates `active(s, n)` on constraint 0. If constraint 0 is `Horizontal`, `Vertical`, or `Coincident`, this raises `ValueError: Invalid constraint id`. (Empirically verified in headless `freecadcmd.exe`).
  3. **Line 192 (`driver_rows` Equal resolution)**:
     ```python
     for k, q in enumerate(s.Constraints):
         if q.Type != 'Equal' or not active(s, k): continue
     ```
     `Equal` is a geometric constraint, so `active(s, k)` crashes on any `Equal` constraint.
  4. **Line 359 (Symmetry check)**:
     ```python
     if c.Type != 'Symmetric' or not active(s, n) or len(v2.references(c, s.GeometryCount)) != 3: continue
     ```
     `Symmetric` is a geometric constraint; `active(s, n)` crashes on any `Symmetric` constraint.
  5. **Line 385 (Symmetry half-width coincidents)**:
     ```python
     links.append(any(active(s, k) and q.Type == 'Coincident' and ... for k, q in enumerate(s.Constraints)))
     ```
     Evaluates `active(s, k)` on all constraints in the sketch.
- **Empirical Traceback**:
  Tested against FreeCAD 1.1.4 C++ Sketcher runtime:
  ```
  File "tools/cad_verify_v3_probe.py", line 158, in relation_axis
    alignment=[x for n,x in enumerate(s.Constraints) if active(s,n) and x.Type in ('Horizontal','Vertical') and x.First==c.First]
  File "tools/cad_verify_v3_probe.py", line 96, in active
    def active(s,i):return s.getActive(i) and s.getDriving(i)
  ValueError: Invalid constraint id
  ```
- **Why Codex's unit tests did not detect this**:
  In [`tools/test_verify_v3.py:155,170,184`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v3.py#L155), mock `SimpleNamespace` objects define `getDriving = lambda i: True` indiscriminately, bypassing FreeCAD C++ Sketcher's constraint type check.
- **Required Fix**:
  Update [`tools/cad_verify_v3_probe.py:96`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L96) to check whether constraint `i` is dimensional before calling `s.getDriving(i)`:
  ```python
  def active(s, i):
      return s.getActive(i) and (s.getDriving(i) if s.Constraints[i].Type in v2.DIMENSIONS else getattr(s.Constraints[i], 'Driving', True))
  ```
  Alternatively, check constraint type or use `getattr(s.Constraints[i], 'Driving', True)` directly.

---

### SHOULD (Recommended Fixes)

#### 2. Realistic Mocking for Constraint `getDriving()` in Unit Tests
- **File / Lines**: [`tools/test_verify_v3.py:155,170,184`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v3.py#L155-L184)
- **Description**:
  The unit test mocks in `V3Contracts` supply a mock `getDriving` that returns `True` for all constraint IDs including `Equal` and `Coincident`. This masked the C++ Sketcher bug. Mocks should enforce FreeCAD API semantics by raising `ValueError("Invalid constraint id")` when called on non-dimensional constraint types.

#### 3. Guard Order Consistency for Constraint Types
- **File / Lines**: [`tools/cad_verify_v3_probe.py:140,158,181,385`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L140)
- **Description**:
  In line 181, `c.Type not in v2.DIMENSIONS` is checked before `active(s, n)`, which prevented crashes on that specific line. However, lines 140, 158, and 385 evaluate `active(s, n)` before checking `c.Type`. Even after fixing `active()`, placing the type check first is cleaner and more defensive.

---

### NIT (Minor Notes)

#### 4. Strict Exact Dictionary Equality in Smoke Runner
- **File / Lines**: [`tools/smoke_verify_v3.py:64`](file:///C:/dev/CAD-HARNESS/tools/smoke_verify_v3.py#L64)
- **Description**:
  `smoke_verify_v3.py` requires `offline.get('positive') == dict(geometry=True, editability=True)`. Any extra metadata keys (e.g. `reimport: False`) cause `Stop('offline_expectation_contract:'+c)`. Gemini's authored controls conform strictly to this requirement.

---

## 3. Plan & Requirement Checklist

| Area / Requirement | Status | Notes |
| :--- | :---: | :--- |
| **Independent Native Controls Handoff** | **PASS** | [`tools/fixtures/verify_v3_native.py`](file:///C:/dev/CAD-HARNESS/tools/fixtures/verify_v3_native.py), 13 geometry case controls (`positive.py`, `negative.py`, `offline.json`), `F4`/`F5` `candidate.py`, `dev/native-matrix.json` + 21 sources authored and smoke-passed. |
| **Probe Reachability & PCD** | **FAIL** | Blocked by `active()` crash on FreeCAD geometric constraints ([`tools/cad_verify_v3_probe.py:96`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L96)). |
| **Parse/Repair Budget Split & Guarantee** | **PASS** | [`tools/cad_verify_v3_guard.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_guard.py) enforces 60s parse repair vs 180s repair timeout; 450s initial / 450s repair stage split; guaranteed repair call flow in [`tools/cad_verify_v3_agent.py:298-314`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_agent.py#L298-L314). |
| **Clarify-Completion Cohort Outside bar_met** | **PASS** | `C4`/`C5` in group `"completion"` are marked `r["scored"] = False` and excluded from `bar_met` in [`tools/eval_verify_v3.py:613-636`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v3.py#L613-L636). |
| **Fresh Holdout Freeze & Gold Secrecy** | **PASS** | Description SHA bindings verified, no gold leaking into agent prompts ([`tools/cad_verify_v3_agent.py:95-97`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_agent.py#L95-L97)). |
| **Legacy & MVP Invariance** | **PASS** | Legacy A/B and MVP P1-P5 generation loops and evaluation paths intact and unchanged. |
| **No-Overwrite Aggregates** | **PASS** | [`tools/eval_verify_v3.py:642`](file:///C:/dev/CAD-HARNESS/tools/eval_verify_v3.py#L642) strictly blocks aggregate overwrite or symlink targets. Aggregate launches no new runs. |
| **Quota Guard & Global Deadline** | **PASS** | 10800s suite deadline, 163 call budget, 900s episode deadline correctly enforced by [`tools/cad_verify_v3_guard.py`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_guard.py). |

---

## 4. Next Action

Codex must apply the one-line fix to [`tools/cad_verify_v3_probe.py:96`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L96) to make `active(s, i)` safe for non-dimensional geometric constraints in FreeCAD 1.1.4 C++ Sketcher. Once applied, Gemini will re-review and issue `READY`.


---

## 5. Re-review

Verdict: **READY**

### Verification Summary

1. **Fix for `active()` on Geometric Constraints**:
   - Codex updated [`tools/cad_verify_v3_probe.py:19,97-100`](file:///C:/dev/CAD-HARNESS/tools/cad_verify_v3_probe.py#L19):
     ```python
     DATUM_TYPES = frozenset(('Distance', 'DistanceX', 'DistanceY', 'Radius', 'Diameter', 'Angle'))
     ...
     def active(s, i):
         # FreeCAD 1.1.4 rejects getDriving() for geometric constraints.
         if not s.getActive(i): return False
         return s.getDriving(i) if s.Constraints[i].Type in DATUM_TYPES else True
     ```
   - In FreeCAD 1.1.4 C++ Sketcher runtime (`freecadcmd.exe`), calling `probe.relation_axis()` and `probe.attachment()` on sketches with geometric constraints (`Horizontal`, `Vertical`, `Coincident`, `Equal`, `Symmetric`, `PointOnObject`) now succeeds without raising `ValueError: Invalid constraint id`.

2. **Unit Tests & Mock Improvements**:
   - Codex updated [`tools/test_verify_v3.py`](file:///C:/dev/CAD-HARNESS/tools/test_verify_v3.py) with `realistic_driving(sketch)`, enforcing that `getDriving()` raises `ValueError('Invalid constraint id')` for non-datum constraints, mirroring FreeCAD's C++ Sketcher API behavior.
   - Added `test_active_respects_freecad_datum_api_and_geometric_activity`, thoroughly verifying `active()` across 13 constraint types (`Distance`, `DistanceX`, `DistanceY`, `Radius`, `Diameter`, `Angle`, `Coincident`, `Horizontal`, `Vertical`, `Equal`, `Symmetric`, `PointOnObject`, `Parallel`).
   - All 16 unit tests in `tools/test_verify_v3.py` pass (`16 tests in 0.356s, OK`).

3. **Grok NIT Fix in `cad_run.py`**:
   - Cleaned up lines 143-146 in [`tools/cad_run.py`](file:///C:/dev/CAD-HARNESS/tools/cad_run.py#L143-L146) to remove redundant `"verify-v3"` check on the `verify-v2` fallback loader.

4. **Headless Native Checks (Fresh Prefixes)**:
   - **Dev Matrix & Parameter Edits**: `python -B tools/smoke_verify_v3.py --run gemini-verify-v3-dev-check-r4-mvp1 --dev-only` completed with exit code 0; all 21 rows passed (`ok: true`).
   - **Full Native Suite**: `python -B tools/smoke_verify_v3.py --run gemini-verify-v3-native-check-r4-mvp1` completed with exit code 0; all 50 rows passed (`ok: true`, 0 sol calls).
   - **Data Check**: `python -B tools/smoke_verify_v3.py --data-only` passed (18 cases, 60 episodes, planned 83 / max 163 calls).

All MUST findings have been resolved. The implementation is verified complete, correct, and ready for freeze and measurement.
