# Addendum B Independent Screening — Gemini

Applied PLAN-V4-UPDATE-U1 Addendum B criteria E3–E7 to all 25 candidates in `pilot-candidates.md` in file order.
E1 and E2 are superseded per Addendum B.
All listed JSONL files were checked read-only; all referenced attachments and dependency paths were inspected for existence and readability without running CAD or model generation.
Non-JSONL listed sources (SQLite) are rejected under E6 without guessing or format conversion.
Missing dependencies and attachments trigger E7.

| ID | Decision | Code | Evidence path |
| --- | --- | --- | --- |
| 1 | excluded | E3 | `C:\Users\backo\.codex\sessions\2026\07\24\rollout-2026-07-24T19-33-33-019f93b0-01ec-7182-a8dc-76d176064131.jsonl:9`; software evaluation & hemispherical tape model outside FreeCAD PartDesign single-body modeling scope; lacks critical dimensions beyond clarification (E4) |
| 2 | excluded | E3 | `C:\Users\backo\.codex\archived_sessions\rollout-2026-07-31T10-22-05-019fb5c3-a4a6-70a1-96d9-a4841d5a1752.jsonl:9`; extruding existing freeform STEP surface into solid and repairing disconnected outer edges outside FreeCAD PartDesign scope; directory `C:\dev\adhesive_designer\examples` |
| 3 | excluded | E3 | `C:\Users\backo\.codex\archived_sessions\rollout-2026-07-31T19-06-03-019fb7a3-5966-7943-aa69-82acedc20afc.jsonl:9`; Fusion 360 parametric modeling maintenance and surface matching outside FreeCAD scope |
| 4 | excluded | E3 | `C:\Users\backo\.codex\archived_sessions\rollout-2026-07-31T19-06-03-019fb7a3-5966-7943-aa69-82acedc20afc.jsonl:5668`; Fusion 360 freeform surface offset/thickening outside FreeCAD scope |
| 5 | excluded | E3 | `C:\Users\backo\.codex\archived_sessions\rollout-2026-07-31T19-06-03-019fb7a3-5966-7943-aa69-82acedc20afc.jsonl:7901`; Fusion 360 fillet tangent repair outside FreeCAD scope |
| 6 | excluded | E3 | `C:\Users\backo\.codex\sessions\2026\08\04\rollout-2026-08-04T18-02-05-019fcc02-38fd-72d1-bd64-7f04961996fc.jsonl:9`; extracting aesthetic surfaces from complex mouse STEP into stylized keychain outside FreeCAD PartDesign scope; attachment `C:\Users\backo\Downloads\コンフィギュレーション 1.step` readable |
| 7 | excluded | E3 | `C:\Users\backo\.codex\sessions\2026\08\04\rollout-2026-08-04T18-02-05-019fcc02-38fd-72d1-bd64-7f04961996fc.jsonl:384`; filling terminal/switch holes on complex STEP keychain model outside FreeCAD PartDesign scope; lacks dimensions (E4) |
| 8 | excluded | E7 | `C:\Users\backo\.codex\archived_sessions\rollout-2026-08-05T13-18-30-019fd024-f32b-75e2-a5f3-ae6023ffddbb.jsonl:9`; missing required selection image `C:\Users\backo\AppData\Local\Temp\codex-clipboard-eac97064-ad1c-418f-8a7c-6e43c70872b3.png`; complex surface feature defeaturing on STEP `C:\Users\backo\Downloads\main_V6,0805.step` also outside scope (E3) |
| 9 | excluded | E3 | `C:\Users\backo\.codex\archived_sessions\rollout-2026-07-31T19-06-03-019fb7a3-5966-7943-aa69-82acedc20afc.jsonl:23834`; solid thickening to match freeform surface and fillet tangent repair on STEP `C:\dev\MeltMouse_ME_Dev\01_Fusion_Mechanical_Design\01_Active\01_Upper Frame_v1.0_GP.step` outside FreeCAD PartDesign scope |
| 10 | excluded | E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a07ec8-98e7-7f50-84eb-61457277bdbd:01a07ec8-a485-7390-b09c-47cd8c03182f`; source is SQLite database, not listed JSONL; missing attachment `C:\Users\backo\Downloads\top_adhesive_tape (1).step` also observed (E7) |
| 11 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a07f44-8082-71e0-bfe3-69862d2704f3:01a07fa5-fb57-7692-ab6a-cee1a60595bd`; SolidWorks parametric chain rebuild outside FreeCAD scope; source is SQLite, not JSONL |
| 12 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a07f44-8082-71e0-bfe3-69862d2704f3:01a0800a-4d45-70e2-b4da-c1f2c9a36e83`; SolidWorks sketch dimension parameterization outside FreeCAD scope; source is SQLite, not JSONL |
| 13 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a08039-3e8a-7733-8d7b-2f7026ad5b04:01a08039-49dd-7532-ab51-c98574194e4d`; SolidWorks heavy B-rep edit outside FreeCAD scope; source is SQLite, not JSONL; missing attachment `G:\共有ドライブ\MIT Member\Development\自社プロダクト\MeltMouse\_dev\Mechanical\3D\_data\1.3mm\_top\_v2\_SDWS.SLDPRT` also observed (E7) |
| 14 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a08139-070a-7753-a9dc-f22109b02feb:01a083c6-bab4-7b33-94b0-37aa652ede93`; SolidWorks multi-STEP assembly origin alignment outside FreeCAD single-body scope; source is SQLite, not JSONL |
| 15 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a08139-070a-7753-a9dc-f22109b02feb:01a083d2-6a4d-7550-a137-19db54ffc6e7`; SolidWorks surface-sketch intersection projection outside FreeCAD PartDesign scope; source is SQLite, not JSONL |
| 16 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a08a0d-f2ff-75e3-b7a2-403f888363ad:01a08a0f-3290-7eb0-8e37-a9591bf07543`; SolidWorks rib creation on Upper Frame surface outside FreeCAD scope; source is SQLite, not JSONL |
| 17 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a08a0d-f2ff-75e3-b7a2-403f888363ad:01a08bee-b6b6-7e10-bc99-ff6c0bd1e9a5`; SolidWorks parting line surface split and draft outside FreeCAD scope; source is SQLite, not JSONL |
| 18 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a08efb-636f-7f13-9a46-024aacc1f5c0:01a08efb-6cc6-7081-bdce-5a54ea8314b1`; SolidWorks rib feature deletion in model tree outside FreeCAD scope; source is SQLite, not JSONL |
| 19 | excluded | E3, E6 | `C:\Users\backo\.codex\thread_history_1.sqlite:thread_items:01a0b30c-7c06-7c00-bc6a-74dd904790b0:01a0b30c-85d1-7342-b13c-bf45f869732e`; SolidWorks freeform surface joining and chamfer split outside FreeCAD scope; source is SQLite, not JSONL |
| 20 | excluded | E7 | `C:\Users\backo\.codex\sessions\2026\09\29\rollout-2026-09-29T13-08-48-01a0eb59-d6c2-71b0-9db3-6713b77cd67c.jsonl:257`; required context workflow file `C:\dev\CAD\CAD_modeling_workflow.md` is missing; multi-part rack assembly for external NF13 box also outside single-body scope (E3) and lacks critical dimensions (E4) |
| 21 | excluded | E7 | `C:\Users\backo\.codex\sessions\2026\09\29\rollout-2026-09-29T13-08-48-01a0eb59-d6c2-71b0-9db3-6713b77cd67c.jsonl:892`; required context workflow file `C:\dev\CAD\CAD_modeling_workflow.md` is missing; modifying multi-part rack assembly script to curve bottom also outside scope (E3) and lacks critical dimensions (E4) |
| 22 | excluded | E7 | `C:\Users\backo\.codex\sessions\2026\09\29\rollout-2026-09-29T13-08-48-01a0eb59-d6c2-71b0-9db3-6713b77cd67c.jsonl:1028`; required context workflow file `C:\dev\CAD\CAD_modeling_workflow.md` is missing; latch fillet reinforcement lacks radius (E4) and modifies assembly script (E3) |
| 23 | excluded | E7 | `C:\Users\backo\.codex\sessions\2026\09\29\rollout-2026-09-29T13-08-48-01a0eb59-d6c2-71b0-9db3-6713b77cd67c.jsonl:1291`; required context workflow file `C:\dev\CAD\CAD_modeling_workflow.md` is missing; hook chamfer lengthening and height increase lack dimensions (E4) and modify assembly script (E3) |
| 24 | excluded | E7 | `C:\Users\backo\.codex\sessions\2026\09\29\rollout-2026-09-29T13-08-48-01a0eb59-d6c2-71b0-9db3-6713b77cd67c.jsonl:1532`; required context workflow file `C:\dev\CAD\CAD_modeling_workflow.md` is missing; number plate insert lacks dimensions (E4) |
| 25 | excluded | E7 | `C:\Users\backo\.codex\sessions\2026\09\29\rollout-2026-09-29T13-08-48-01a0eb59-d6c2-71b0-9db3-6713b77cd67c.jsonl:1823`; required context workflow file `C:\dev\CAD\CAD_modeling_workflow.md` is missing; deleting ribs on number plate lacks dimensions (E4) and modifies uncommitted assembly script (E3) |

Selected: 0
Excluded: 25
N = 0 (pilot status: `not_run`)

Signed: Gemini (`google-antigravity/gemini-3.8-flash`).
