# A0: 2部品の参照経路の実測記録

2026-10-18、branch v5。FreeCAD 1.1.3 / build 20260725、同梱 Python 3.11.14。
pass はこの単純モデルとインストールでの実測に限る。A0 全体、GUI 編集、他バージョン、形状変更全般の参照安定性は未検証。

| 段 | 判定 | 実測 |
|---|---|---|
| (a) | pass | 別文書の App::Part に PartDesign::Body と Spreadsheet を各1個。式駆動 AdditiveBox と半径2 mmの SubtractiveCylinder 貫通穴。各40×20×8 mm、体積6299.469035085125 mm³、有効な単一ソリッド。 |
| (b) | pass | PartDesign::CoordinateSystem の AttachmentSupport を穴の下側円周 Hole.Edge14 に設定。MapMode=Concentric、AttachmentOffset.Base.z=Dimensions.param_H により穴上面中心 (20,10,8) mm。 |
| (c) | pass | 参照元・所有文書を保存後、App::Link.setLink(part) で外部文書の App::Part を参照。2個とも形状と体積を確認。 |
| (d) | pass | native Assembly::AssemblyObject と Assembly::JointGroup、配布済み JointObject の GroundedJoint と Fixed joint を生成。コネクタ設定と solve() が headless で動作。 |
| (e) | pass | 部品1の L を40→60 mm。recompute と solve() 後、datum は (20,10,8)→(30,10,8) mm。部品2の Link.Placement.x は0→10 mm、両穴中心のワールド座標が (30,10,8) mm で一致。 |
| (f) | pass | 新しい FreeCADCmd プロセスで3文書を開き、強制再計算、保存前寸法・体積・位置と比較。solve() 前後のワールド座標も一致。 |

位置比較の許容差は 1e-6 mm。親子とも GuiUp=0。終了コード0だけでは成功とせず、各段の JSON status と測定 assertion で判定した。依存段が失敗した場合は unknown、生の例外と traceback を残す。GUI シンボル欠如は unsupported とする。最終実行には GUI 必須の段はなかった。

## 必要だった API

この版の datum プロパティ名は Support ではなく AttachmentSupport。
L は Spreadsheet の A1、式用別名は param_L。L 単体は Invalid alias になる。
Spreadsheet は App::Part 内で Body と同階層に置いた。外部 Link は参照される文書と所有文書の両方を先に保存する。

インストール済み Mod/Assembly の AssemblyTests/TestCore.py、JointObject.py、UtilsAssembly.py、CommandCreateAssembly.py を参照した。
JointObject は FreeCAD の検索経路から import。FreeCADGui の import、ワークベンチ GUI 起動、ViewProvider 作成は行っていない。

- `doc.addObject("Assembly::AssemblyObject", "Assembly")` → `<Assembly object>`
- `assembly.newObject("Assembly::JointGroup", "Joints")` → `<Joint Group>`
- `JointObject.GroundedJoint(ground, Link1)` → `<JointObject.GroundedJoint object at 0x00000157F42A2010>`
- `JointObject.Joint(joint, 0)` → `<JointObject.Joint object at 0x00000157F42A2C10>`
- `joint.Proxy.setJointConnectors(joint, [[Link1, ["Body.HoleLCS.", "Body.HoleLCS."]], [Link2, ["Body.HoleLCS.", "Body.HoleLCS."]]])` → `None`
- `assembly.solve()` → `0`

JointObject.Joint(joint, 0) は JointType=Fixed。参照は Link を起点とする Body.HoleLCS. の2本。ground は Link1 を固定する。solve() の戻り値は整数0で、0を assertion で検査した。プロキシのメモリアドレスは実行ごとに変わる。

## 実行コマンド

作業ディレクトリは C:\cad-harness\work\repo。最終実行ではホスト Python を生出力のバイト保存用に使用。CAD処理と子プロセスはいずれも指定 FreeCADCmd と同梱 Python。

```powershell
python a0/probes/run_datum_link_joint_probe.py a0/probe-artifacts/datum-link-joint/final
```

実際のコマンド、明示設定した環境変数、終了コード:

```json
{
  "command": [
    "C:/Users/NGGmo/AppData/Local/Programs/FreeCAD 1.1/bin/FreeCADCmd.exe",
    "C:/cad-harness/work/repo/a0/probes/datum_link_joint_probe.py"
  ],
  "environment": {
    "A0_DATUM_PROBE_DIR": "C:/cad-harness/work/repo/a0/probe-artifacts/datum-link-joint/final",
    "A0_DATUM_PROBE_MODE": "create"
  },
  "exit_code": 0
}
```

親 PID=27772、子 PID=38396。子も同じ exe と probe を使い、A0_DATUM_PROBE_MODE=reopen を設定。親子とも終了コード0。

再現時は final の代わりに未作成の出力先を指定する。プローブの直接実行も可能:

```powershell
$env:A0_DATUM_PROBE_DIR = 'C:\cad-harness\work\repo\a0\probe-artifacts\datum-link-joint\rerun'
$env:A0_DATUM_PROBE_MODE = 'create'
& 'C:\Users\NGGmo\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe' 'C:\cad-harness\work\repo\a0\probes\datum_link_joint_probe.py'
```

## 途中の失敗

初回から試行4までは、上記の直接実行コマンドに `1> a0/datum-probe.stdout.log 2> a0/datum-probe.stderr.log` を付けた。出力先環境変数は順に datum-link-joint、datum-link-joint/attempt-2、datum-link-joint/attempt-3、datum-link-joint/attempt-4。いずれも exe 終了コードは0。ログは PowerShell の UTF-16 とエラー装飾を含む。最終ランナーは stdout/stderr をバイトのまま保存する。

| 試行 | 観測と修正 |
|---|---|
| 1 | (a) ValueError: Invalid alias。L を param_L に変更。(b)〜(f) は依存段未成功のため unknown。 |
| 2 | TypeError: Object of type Quantity is not JSON serializable。段の結果を最後まで出せず、試行全体の判定は無効。Quantity を文字列化して修正。 |
| 3 | (a) pass、(b) AttributeError: 'Part.Feature' object has no attribute 'Support'、(c) RuntimeError: Owner document not saved、(d)〜(f) unknown。AttachmentSupport と所有文書の事前保存に修正。 |
| 4 | 全段 pass。その後 solve 戻り値0と再読込直後の座標比較を assertion に追加し、最終実行でも全段 pass。 |

生ログと例外: [試行1](probe-artifacts/datum-link-joint/attempt-1.stdout.log)、[試行2 stdout](probe-artifacts/datum-link-joint/attempt-2.stdout.log)、[試行2 stderr](probe-artifacts/datum-link-joint/attempt-2.stderr.log)、[試行3](probe-artifacts/datum-link-joint/attempt-3.stdout.log)、[試行4 JSON](probe-artifacts/datum-link-joint/attempt-4/result.json)。試行時点の例外行番号は現在のスクリプトと異なる。
API確認用 inspect_datum_api.py は一度、存在しない getExtensions() 呼出しで AttributeError となった。呼出しを除いて再実行し、AttachmentSupport と solve の存在を確認した。

## 最終実行の生の出力

[stdout.log](probe-artifacts/datum-link-joint/final/stdout.log) の全文。Markdown 用の改行は LF。子の stdout/stderr と child_result も親 JSON に含む。

```text
A0_STAGE {"a": {"status": "pass", "data": {"parts": [{"document": "ProbePart1", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": null}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": null}], "expressions": [["Height", "Dimensions.param_H"], ["Length", "Dimensions.param_L"], ["Width", "Dimensions.param_W"]]}}}
A0_STAGE {"b": {"status": "pass", "data": {"datums": [{"type": "PartDesign::CoordinateSystem", "support": "[(<PartDesign::SubtractiveCylinder>, ('Edge14',))]", "map_mode": "Concentric", "expressions": [[".AttachmentOffset.Base.z", "Dimensions.param_H"]], "position_mm": [20.0, 10.0, 8.0]}, {"type": "PartDesign::CoordinateSystem", "support": "[(<PartDesign::SubtractiveCylinder>, ('Edge14',))]", "map_mode": "Concentric", "expressions": [[".AttachmentOffset.Base.z", "Dimensions.param_H"]], "position_mm": [20.0, 10.0, 8.0]}]}}}
A0_STAGE {"c": {"status": "pass", "data": {"links": [{"type": "App::Link", "linked_document": "ProbePart1", "linked_object": "Part", "shape_valid": true, "volume_mm3": 6299.469035085125}, {"type": "App::Link", "linked_document": "ProbePart2", "linked_object": "Part", "shape_valid": true, "volume_mm3": 6299.469035085125}]}}}
FreeCAD 1.1.3, Libs: 1.1.3R20260725 (Git shallow)
(C) 2001-2026 FreeCAD contributors
FreeCAD is free and open-source software licensed under the terms of LGPL2+ license.

Recompute......
						(4 %)	
						(9 %)	
						(14 %)	
						(19 %)	
						(23 %)	
						(28 %)	
						(33 %)	
						(38 %)	
						(42 %)	
						(47 %)	
						(52 %)	
						(57 %)	
						(61 %)	
						(66 %)	
						(71 %)	
						(76 %)	
						(80 %)	
						(85 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(4 %)	
						(9 %)	
						(14 %)	
						(19 %)	
						(23 %)	
						(28 %)	
						(33 %)	
						(38 %)	
						(42 %)	
						(47 %)	
						(52 %)	
						(57 %)	
						(61 %)	
						(66 %)	
						(71 %)	
						(76 %)	
						(80 %)	
						(85 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(4 %)	
						(9 %)	
						(13 %)	
						(18 %)	
						(22 %)	
						(27 %)	
						(31 %)	
						(36 %)	
						(40 %)	
						(45 %)	
						(50 %)	
						(54 %)	
						(59 %)	
						(63 %)	
						(68 %)	
						(72 %)	
						(77 %)	
						(81 %)	
						(86 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(4 %)	
						(9 %)	
						(13 %)	
						(18 %)	
						(22 %)	
						(27 %)	
						(31 %)	
						(36 %)	
						(40 %)	
						(45 %)	
						(50 %)	
						(54 %)	
						(59 %)	
						(63 %)	
						(68 %)	
						(72 %)	
						(77 %)	
						(81 %)	
						(86 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(2 %)	
						(4 %)	
						(6 %)	
						(8 %)	
						(10 %)	
						(13 %)	
						(15 %)	
						(17 %)	
						(19 %)	
						(21 %)	
						(23 %)	
						(26 %)	
						(28 %)	
						(30 %)	
						(32 %)	
						(34 %)	
						(36 %)	
						(39 %)	
						(41 %)	
						(43 %)	
						(45 %)	
						(47 %)	
						(50 %)	
						(52 %)	
						(54 %)	
						(56 %)	
						(58 %)	
						(60 %)	
						(63 %)	
						(65 %)	
						(67 %)	
						(69 %)	
						(71 %)	
						(73 %)	
						(76 %)	
						(78 %)	
						(80 %)	
						(82 %)	
						(84 %)	
						(86 %)	
						(89 %)	
						(91 %)	
						(93 %)	
						(95 %)	
						(97 %)	
						(100 %)	
								
MbD: Assembling system. 
MbD: Convergence = 0
Time = 0
Recompute......
						(1 %)	
						(3 %)	
						(5 %)	
						(6 %)	
						(8 %)	
						(10 %)	
						(12 %)	
						(13 %)	
						(15 %)	
						(17 %)	
						(18 %)	
						(20 %)	
						(22 %)	
						(24 %)	
						(25 %)	
						(27 %)	
						(29 %)	
						(31 %)	
						(32 %)	
						(34 %)	
						(36 %)	
						(37 %)	
						(39 %)	
						(41 %)	
						(43 %)	
						(44 %)	
						(46 %)	
						(48 %)	
						(50 %)	
						(51 %)	
						(53 %)	
						(55 %)	
						(56 %)	
						(58 %)	
						(60 %)	
						(62 %)	
						(63 %)	
						(65 %)	
						(67 %)	
						(68 %)	
						(70 %)	
						(72 %)	
						(74 %)	
						(75 %)	
						(77 %)	
						(79 %)	
						(81 %)	
						(82 %)	
						(84 %)	
						(86 %)	
						(87 %)	
						(89 %)	
						(91 %)	
						(93 %)	
						(94 %)	
						(96 %)	
						(98 %)	
MbD: Assembling system. 
MbD: Convergence = 0
Time = 0
						(100 %)	
								
MbD: Assembling system. 
MbD: Convergence = 0
Time = 0
A0_STAGE {"d": {"status": "pass", "data": {"api": [{"call": "doc.addObject(\"Assembly::AssemblyObject\", \"Assembly\")", "return": "<Assembly object>"}, {"call": "assembly.newObject(\"Assembly::JointGroup\", \"Joints\")", "return": "<Joint Group>"}, {"call": "JointObject.GroundedJoint(ground, Link1)", "return": "<JointObject.GroundedJoint object at 0x00000157F42A2010>"}, {"call": "JointObject.Joint(joint, 0)", "return": "<JointObject.Joint object at 0x00000157F42A2C10>", "joint_type": "Fixed"}, {"call": "joint.Proxy.setJointConnectors(joint, [[Link1, [\"Body.HoleLCS.\", \"Body.HoleLCS.\"]], [Link2, [\"Body.HoleLCS.\", \"Body.HoleLCS.\"]]])", "return": "None"}, {"call": "assembly.solve()", "return": "0"}], "references": ["(<App::Link object>, ['Body.HoleLCS.', 'Body.HoleLCS.'])", "(<App::Link object>, ['Body.HoleLCS.', 'Body.HoleLCS.'])"], "parts": [{"document": "ProbePart1", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "world_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]}}}
Recompute......
						(4 %)	
						(9 %)	
						(13 %)	
						(18 %)	
						(22 %)	
						(27 %)	
						(31 %)	
						(36 %)	
						(40 %)	
						(45 %)	
						(50 %)	
						(54 %)	
						(59 %)	
						(63 %)	
						(68 %)	
						(72 %)	
						(77 %)	
						(81 %)	
						(86 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(4 %)	
						(9 %)	
						(13 %)	
						(18 %)	
						(22 %)	
						(27 %)	
						(31 %)	
						(36 %)	
						(40 %)	
						(45 %)	
						(50 %)	
						(54 %)	
						(59 %)	
						(63 %)	
						(68 %)	
						(72 %)	
						(77 %)	
						(81 %)	
						(86 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(1 %)	
						(3 %)	
						(5 %)	
						(6 %)	
						(8 %)	
						(10 %)	
						(12 %)	
						(13 %)	
						(15 %)	
						(17 %)	
						(18 %)	
						(20 %)	
						(22 %)	
						(24 %)	
						(25 %)	
						(27 %)	
						(29 %)	
						(31 %)	
						(32 %)	
						(34 %)	
						(36 %)	
						(37 %)	
						(39 %)	
						(41 %)	
						(43 %)	
						(44 %)	
						(46 %)	
						(48 %)	
						(50 %)	
						(51 %)	
						(53 %)	
						(55 %)	
						(56 %)	
						(58 %)	
						(60 %)	
						(62 %)	
						(63 %)	
						(65 %)	
						(67 %)	
						(68 %)	
						(70 %)	
						(72 %)	
						(74 %)	
						(75 %)	
						(77 %)	
						(79 %)	
						(81 %)	
						(82 %)	
						(84 %)	
						(86 %)	
						(87 %)	
						(89 %)	
						(91 %)	
						(93 %)	
						(94 %)	
						(96 %)	
						(98 %)	
MbD: Assembling system. 
MbD: Convergence = 51233629.214608639
MbD: Convergence = 1.9112891065167329e-08
MbD: Convergence = 4.0705895881706084e-24
Time = 0
						(100 %)	
								
MbD: Assembling system. 
MbD: Convergence = 0
Time = 0
A0_STAGE {"e": {"status": "pass", "data": {"before": {"parts": [{"document": "ProbePart1", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "world_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]}, "solve_return": "0", "after": {"parts": [{"document": "ProbePart1", "L_mm": "60.0 mm", "length_mm": 60.0, "volume_mm3": 9499.469035085125, "datum_mm": [30.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "world_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [10.0, 4.932439087451337e-31, 0.0]]}}}}
A0_STAGE {"f": {"status": "pass", "data": {"command": ["C:\\Users\\NGGmo\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\FreeCADCmd.exe", "C:\\cad-harness\\work\\repo\\a0\\probes\\datum_link_joint_probe.py"], "exit_code": 0, "stdout": "FreeCAD 1.1.3, Libs: 1.1.3R20260725 (Git shallow)\n(C) 2001-2026 FreeCAD contributors\nFreeCAD is free and open-source software licensed under the terms of LGPL2+ license.\n\nImporting project files......\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nPostprocessing......\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nImporting project files......\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nPostprocessing......\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nImporting project files......\n\t\t\t\t\t\t(25 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(75 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nPostprocessing......\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nRecompute......\n\t\t\t\t\t\t(4 %)\t\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(40 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(59 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(95 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nRecompute......\n\t\t\t\t\t\t(4 %)\t\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(40 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(59 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(95 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nRecompute......\n\t\t\t\t\t\t(1 %)\t\n\t\t\t\t\t\t(3 %)\t\n\t\t\t\t\t\t(5 %)\t\n\t\t\t\t\t\t(6 %)\t\n\t\t\t\t\t\t(8 %)\t\n\t\t\t\t\t\t(10 %)\t\n\t\t\t\t\t\t(12 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(15 %)\t\n\t\t\t\t\t\t(17 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(20 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(24 %)\t\n\t\t\t\t\t\t(25 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(29 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(32 %)\t\n\t\t\t\t\t\t(34 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(37 %)\t\n\t\t\t\t\t\t(39 %)\t\n\t\t\t\t\t\t(41 %)\t\n\t\t\t\t\t\t(43 %)\t\n\t\t\t\t\t\t(44 %)\t\n\t\t\t\t\t\t(46 %)\t\n\t\t\t\t\t\t(48 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(51 %)\t\n\t\t\t\t\t\t(53 %)\t\n\t\t\t\t\t\t(55 %)\t\n\t\t\t\t\t\t(56 %)\t\n\t\t\t\t\t\t(58 %)\t\n\t\t\t\t\t\t(60 %)\t\n\t\t\t\t\t\t(62 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(65 %)\t\n\t\t\t\t\t\t(67 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(70 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(74 %)\t\n\t\t\t\t\t\t(75 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(79 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(82 %)\t\n\t\t\t\t\t\t(84 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(87 %)\t\n\t\t\t\t\t\t(89 %)\t\n\t\t\t\t\t\t(91 %)\t\n\t\t\t\t\t\t(93 %)\t\n\t\t\t\t\t\t(94 %)\t\n\t\t\t\t\t\t(96 %)\t\n\t\t\t\t\t\t(98 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nMbD: Assembling system. \nMbD: Convergence = 0\nTime = 0\nA0_STAGE {\"f\": {\"status\": \"pass\", \"data\": {\"measurement\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}, \"solve_return\": \"0\", \"after_solve\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}}}}\nA0_DATUM_RESULT {\"probe\": \"datum-link-joint-headless\", \"mode\": \"reopen\", \"pid\": 38396, \"python\": \"3.11.14 | packaged by conda-forge | (main, Oct 13 2025, 14:00:26) [MSC v.1944 64 bit (AMD64)]\", \"freecad\": [\"1\", \"1\", \"3\", \"20260725 (Git shallow)\", \"Unknown\", \"2026/07/25 04:52:02\", \"grafted,grafted\", \"145529fe741292ff0b3977a01195bf0247425794\"], \"gui_up\": 0, \"artifact_dir\": \"C:\\\\cad-harness\\\\work\\\\repo\\\\a0\\\\probe-artifacts\\\\datum-link-joint\\\\final\", \"stages\": {\"f\": {\"status\": \"pass\", \"data\": {\"measurement\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}, \"solve_return\": \"0\", \"after_solve\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}}}}}\nRecompute......\n\t\t\t\t\t\t(1 %)\t\n\t\t\t\t\t\t(3 %)\t\n\t\t\t\t\t\t(5 %)\t\n\t\t\t\t\t\t(6 %)\t\n\t\t\t\t\t\t(8 %)\t\n\t\t\t\t\t\t(10 %)\t\n\t\t\t\t\t\t(12 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(15 %)\t\n\t\t\t\t\t\t(17 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(20 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(24 %)\t\n\t\t\t\t\t\t(25 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(29 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(32 %)\t\n\t\t\t\t\t\t(34 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(37 %)\t\n\t\t\t\t\t\t(39 %)\t\n\t\t\t\t\t\t(41 %)\t\n\t\t\t\t\t\t(43 %)\t\n\t\t\t\t\t\t(44 %)\t\n\t\t\t\t\t\t(46 %)\t\n\t\t\t\t\t\t(48 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(51 %)\t\n\t\t\t\t\t\t(53 %)\t\n\t\t\t\t\t\t(55 %)\t\n\t\t\t\t\t\t(56 %)\t\n\t\t\t\t\t\t(58 %)\t\n\t\t\t\t\t\t(60 %)\t\n\t\t\t\t\t\t(62 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(65 %)\t\n\t\t\t\t\t\t(67 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(70 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(74 %)\t\n\t\t\t\t\t\t(75 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(79 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(82 %)\t\n\t\t\t\t\t\t(84 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(87 %)\t\n\t\t\t\t\t\t(89 %)\t\n\t\t\t\t\t\t(91 %)\t\n\t\t\t\t\t\t(93 %)\t\n\t\t\t\t\t\t(94 %)\t\n\t\t\t\t\t\t(96 %)\t\n\t\t\t\t\t\t(98 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\n", "stderr": "", "child_result": {"probe": "datum-link-joint-headless", "mode": "reopen", "pid": 38396, "python": "3.11.14 | packaged by conda-forge | (main, Oct 13 2025, 14:00:26) [MSC v.1944 64 bit (AMD64)]", "freecad": ["1", "1", "3", "20260725 (Git shallow)", "Unknown", "2026/07/25 04:52:02", "grafted,grafted", "145529fe741292ff0b3977a01195bf0247425794"], "gui_up": 0, "artifact_dir": "C:\\cad-harness\\work\\repo\\a0\\probe-artifacts\\datum-link-joint\\final", "stages": {"f": {"status": "pass", "data": {"measurement": {"parts": [{"document": "ProbePart1", "L_mm": "60.0 mm", "length_mm": 60.0, "volume_mm3": 9499.469035085125, "datum_mm": [30.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "world_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}, "solve_return": "0", "after_solve": {"parts": [{"document": "ProbePart1", "L_mm": "60.0 mm", "length_mm": 60.0, "volume_mm3": 9499.469035085125, "datum_mm": [30.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "world_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}}}}}}}}
A0_DATUM_RESULT {"probe": "datum-link-joint-headless", "mode": "create", "pid": 27772, "python": "3.11.14 | packaged by conda-forge | (main, Oct 13 2025, 14:00:26) [MSC v.1944 64 bit (AMD64)]", "freecad": ["1", "1", "3", "20260725 (Git shallow)", "Unknown", "2026/07/25 04:52:02", "grafted,grafted", "145529fe741292ff0b3977a01195bf0247425794"], "gui_up": 0, "artifact_dir": "C:\\cad-harness\\work\\repo\\a0\\probe-artifacts\\datum-link-joint\\final", "stages": {"a": {"status": "pass", "data": {"parts": [{"document": "ProbePart1", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": null}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": null}], "expressions": [["Height", "Dimensions.param_H"], ["Length", "Dimensions.param_L"], ["Width", "Dimensions.param_W"]]}}, "b": {"status": "pass", "data": {"datums": [{"type": "PartDesign::CoordinateSystem", "support": "[(<PartDesign::SubtractiveCylinder>, ('Edge14',))]", "map_mode": "Concentric", "expressions": [[".AttachmentOffset.Base.z", "Dimensions.param_H"]], "position_mm": [20.0, 10.0, 8.0]}, {"type": "PartDesign::CoordinateSystem", "support": "[(<PartDesign::SubtractiveCylinder>, ('Edge14',))]", "map_mode": "Concentric", "expressions": [[".AttachmentOffset.Base.z", "Dimensions.param_H"]], "position_mm": [20.0, 10.0, 8.0]}]}}, "c": {"status": "pass", "data": {"links": [{"type": "App::Link", "linked_document": "ProbePart1", "linked_object": "Part", "shape_valid": true, "volume_mm3": 6299.469035085125}, {"type": "App::Link", "linked_document": "ProbePart2", "linked_object": "Part", "shape_valid": true, "volume_mm3": 6299.469035085125}]}}, "d": {"status": "pass", "data": {"api": [{"call": "doc.addObject(\"Assembly::AssemblyObject\", \"Assembly\")", "return": "<Assembly object>"}, {"call": "assembly.newObject(\"Assembly::JointGroup\", \"Joints\")", "return": "<Joint Group>"}, {"call": "JointObject.GroundedJoint(ground, Link1)", "return": "<JointObject.GroundedJoint object at 0x00000157F42A2010>"}, {"call": "JointObject.Joint(joint, 0)", "return": "<JointObject.Joint object at 0x00000157F42A2C10>", "joint_type": "Fixed"}, {"call": "joint.Proxy.setJointConnectors(joint, [[Link1, [\"Body.HoleLCS.\", \"Body.HoleLCS.\"]], [Link2, [\"Body.HoleLCS.\", \"Body.HoleLCS.\"]]])", "return": "None"}, {"call": "assembly.solve()", "return": "0"}], "references": ["(<App::Link object>, ['Body.HoleLCS.', 'Body.HoleLCS.'])", "(<App::Link object>, ['Body.HoleLCS.', 'Body.HoleLCS.'])"], "parts": [{"document": "ProbePart1", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "world_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]}}, "e": {"status": "pass", "data": {"before": {"parts": [{"document": "ProbePart1", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "world_datums_mm": [[20.0, 10.0, 8.0], [20.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]}, "solve_return": "0", "after": {"parts": [{"document": "ProbePart1", "L_mm": "60.0 mm", "length_mm": 60.0, "volume_mm3": 9499.469035085125, "datum_mm": [30.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "world_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [10.0, 4.932439087451337e-31, 0.0]]}}}, "f": {"status": "pass", "data": {"command": ["C:\\Users\\NGGmo\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\FreeCADCmd.exe", "C:\\cad-harness\\work\\repo\\a0\\probes\\datum_link_joint_probe.py"], "exit_code": 0, "stdout": "FreeCAD 1.1.3, Libs: 1.1.3R20260725 (Git shallow)\n(C) 2001-2026 FreeCAD contributors\nFreeCAD is free and open-source software licensed under the terms of LGPL2+ license.\n\nImporting project files......\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nPostprocessing......\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nImporting project files......\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nPostprocessing......\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nImporting project files......\n\t\t\t\t\t\t(25 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(75 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nPostprocessing......\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nRecompute......\n\t\t\t\t\t\t(4 %)\t\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(40 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(59 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(95 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nRecompute......\n\t\t\t\t\t\t(4 %)\t\n\t\t\t\t\t\t(9 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(40 %)\t\n\t\t\t\t\t\t(45 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(54 %)\t\n\t\t\t\t\t\t(59 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(90 %)\t\n\t\t\t\t\t\t(95 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nRecompute......\n\t\t\t\t\t\t(1 %)\t\n\t\t\t\t\t\t(3 %)\t\n\t\t\t\t\t\t(5 %)\t\n\t\t\t\t\t\t(6 %)\t\n\t\t\t\t\t\t(8 %)\t\n\t\t\t\t\t\t(10 %)\t\n\t\t\t\t\t\t(12 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(15 %)\t\n\t\t\t\t\t\t(17 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(20 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(24 %)\t\n\t\t\t\t\t\t(25 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(29 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(32 %)\t\n\t\t\t\t\t\t(34 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(37 %)\t\n\t\t\t\t\t\t(39 %)\t\n\t\t\t\t\t\t(41 %)\t\n\t\t\t\t\t\t(43 %)\t\n\t\t\t\t\t\t(44 %)\t\n\t\t\t\t\t\t(46 %)\t\n\t\t\t\t\t\t(48 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(51 %)\t\n\t\t\t\t\t\t(53 %)\t\n\t\t\t\t\t\t(55 %)\t\n\t\t\t\t\t\t(56 %)\t\n\t\t\t\t\t\t(58 %)\t\n\t\t\t\t\t\t(60 %)\t\n\t\t\t\t\t\t(62 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(65 %)\t\n\t\t\t\t\t\t(67 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(70 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(74 %)\t\n\t\t\t\t\t\t(75 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(79 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(82 %)\t\n\t\t\t\t\t\t(84 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(87 %)\t\n\t\t\t\t\t\t(89 %)\t\n\t\t\t\t\t\t(91 %)\t\n\t\t\t\t\t\t(93 %)\t\n\t\t\t\t\t\t(94 %)\t\n\t\t\t\t\t\t(96 %)\t\n\t\t\t\t\t\t(98 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\nMbD: Assembling system. \nMbD: Convergence = 0\nTime = 0\nA0_STAGE {\"f\": {\"status\": \"pass\", \"data\": {\"measurement\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}, \"solve_return\": \"0\", \"after_solve\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}}}}\nA0_DATUM_RESULT {\"probe\": \"datum-link-joint-headless\", \"mode\": \"reopen\", \"pid\": 38396, \"python\": \"3.11.14 | packaged by conda-forge | (main, Oct 13 2025, 14:00:26) [MSC v.1944 64 bit (AMD64)]\", \"freecad\": [\"1\", \"1\", \"3\", \"20260725 (Git shallow)\", \"Unknown\", \"2026/07/25 04:52:02\", \"grafted,grafted\", \"145529fe741292ff0b3977a01195bf0247425794\"], \"gui_up\": 0, \"artifact_dir\": \"C:\\\\cad-harness\\\\work\\\\repo\\\\a0\\\\probe-artifacts\\\\datum-link-joint\\\\final\", \"stages\": {\"f\": {\"status\": \"pass\", \"data\": {\"measurement\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}, \"solve_return\": \"0\", \"after_solve\": {\"parts\": [{\"document\": \"ProbePart1\", \"L_mm\": \"60.0 mm\", \"length_mm\": 60.0, \"volume_mm3\": 9499.469035085125, \"datum_mm\": [30.0, 10.0, 8.0]}, {\"document\": \"ProbePart2\", \"L_mm\": \"40.0 mm\", \"length_mm\": 40.0, \"volume_mm3\": 6299.469035085125, \"datum_mm\": [20.0, 10.0, 8.0]}], \"link_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"world_datums_mm\": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], \"link_placements_mm\": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}}}}}\nRecompute......\n\t\t\t\t\t\t(1 %)\t\n\t\t\t\t\t\t(3 %)\t\n\t\t\t\t\t\t(5 %)\t\n\t\t\t\t\t\t(6 %)\t\n\t\t\t\t\t\t(8 %)\t\n\t\t\t\t\t\t(10 %)\t\n\t\t\t\t\t\t(12 %)\t\n\t\t\t\t\t\t(13 %)\t\n\t\t\t\t\t\t(15 %)\t\n\t\t\t\t\t\t(17 %)\t\n\t\t\t\t\t\t(18 %)\t\n\t\t\t\t\t\t(20 %)\t\n\t\t\t\t\t\t(22 %)\t\n\t\t\t\t\t\t(24 %)\t\n\t\t\t\t\t\t(25 %)\t\n\t\t\t\t\t\t(27 %)\t\n\t\t\t\t\t\t(29 %)\t\n\t\t\t\t\t\t(31 %)\t\n\t\t\t\t\t\t(32 %)\t\n\t\t\t\t\t\t(34 %)\t\n\t\t\t\t\t\t(36 %)\t\n\t\t\t\t\t\t(37 %)\t\n\t\t\t\t\t\t(39 %)\t\n\t\t\t\t\t\t(41 %)\t\n\t\t\t\t\t\t(43 %)\t\n\t\t\t\t\t\t(44 %)\t\n\t\t\t\t\t\t(46 %)\t\n\t\t\t\t\t\t(48 %)\t\n\t\t\t\t\t\t(50 %)\t\n\t\t\t\t\t\t(51 %)\t\n\t\t\t\t\t\t(53 %)\t\n\t\t\t\t\t\t(55 %)\t\n\t\t\t\t\t\t(56 %)\t\n\t\t\t\t\t\t(58 %)\t\n\t\t\t\t\t\t(60 %)\t\n\t\t\t\t\t\t(62 %)\t\n\t\t\t\t\t\t(63 %)\t\n\t\t\t\t\t\t(65 %)\t\n\t\t\t\t\t\t(67 %)\t\n\t\t\t\t\t\t(68 %)\t\n\t\t\t\t\t\t(70 %)\t\n\t\t\t\t\t\t(72 %)\t\n\t\t\t\t\t\t(74 %)\t\n\t\t\t\t\t\t(75 %)\t\n\t\t\t\t\t\t(77 %)\t\n\t\t\t\t\t\t(79 %)\t\n\t\t\t\t\t\t(81 %)\t\n\t\t\t\t\t\t(82 %)\t\n\t\t\t\t\t\t(84 %)\t\n\t\t\t\t\t\t(86 %)\t\n\t\t\t\t\t\t(87 %)\t\n\t\t\t\t\t\t(89 %)\t\n\t\t\t\t\t\t(91 %)\t\n\t\t\t\t\t\t(93 %)\t\n\t\t\t\t\t\t(94 %)\t\n\t\t\t\t\t\t(96 %)\t\n\t\t\t\t\t\t(98 %)\t\n\t\t\t\t\t\t(100 %)\t\n\t\t\t\t\t\t\t\t\n", "stderr": "", "child_result": {"probe": "datum-link-joint-headless", "mode": "reopen", "pid": 38396, "python": "3.11.14 | packaged by conda-forge | (main, Oct 13 2025, 14:00:26) [MSC v.1944 64 bit (AMD64)]", "freecad": ["1", "1", "3", "20260725 (Git shallow)", "Unknown", "2026/07/25 04:52:02", "grafted,grafted", "145529fe741292ff0b3977a01195bf0247425794"], "gui_up": 0, "artifact_dir": "C:\\cad-harness\\work\\repo\\a0\\probe-artifacts\\datum-link-joint\\final", "stages": {"f": {"status": "pass", "data": {"measurement": {"parts": [{"document": "ProbePart1", "L_mm": "60.0 mm", "length_mm": 60.0, "volume_mm3": 9499.469035085125, "datum_mm": [30.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "world_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}, "solve_return": "0", "after_solve": {"parts": [{"document": "ProbePart1", "L_mm": "60.0 mm", "length_mm": 60.0, "volume_mm3": 9499.469035085125, "datum_mm": [30.0, 10.0, 8.0]}, {"document": "ProbePart2", "L_mm": "40.0 mm", "length_mm": 40.0, "volume_mm3": 6299.469035085125, "datum_mm": [20.0, 10.0, 8.0]}], "link_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "world_datums_mm": [[30.0, 10.0, 8.0], [30.0, 10.0, 8.0]], "link_placements_mm": [[0.0, 0.0, 0.0], [10.0, 0.0, 0.0]]}}}}}}}}}
Recompute......
						(1 %)	
						(3 %)	
						(5 %)	
						(6 %)	
						(8 %)	
						(10 %)	
						(12 %)	
						(13 %)	
						(15 %)	
						(17 %)	
						(18 %)	
						(20 %)	
						(22 %)	
						(24 %)	
						(25 %)	
						(27 %)	
						(29 %)	
						(31 %)	
						(32 %)	
						(34 %)	
						(36 %)	
						(37 %)	
						(39 %)	
						(41 %)	
						(43 %)	
						(44 %)	
						(46 %)	
						(48 %)	
						(50 %)	
						(51 %)	
						(53 %)	
						(55 %)	
						(56 %)	
						(58 %)	
						(60 %)	
						(62 %)	
						(63 %)	
						(65 %)	
						(67 %)	
						(68 %)	
						(70 %)	
						(72 %)	
						(74 %)	
						(75 %)	
						(77 %)	
						(79 %)	
						(81 %)	
						(82 %)	
						(84 %)	
						(86 %)	
						(87 %)	
						(89 %)	
						(91 %)	
						(93 %)	
						(94 %)	
						(96 %)	
						(98 %)	
						(100 %)	
								
Recompute......
						(4 %)	
						(9 %)	
						(13 %)	
						(18 %)	
						(22 %)	
						(27 %)	
						(31 %)	
						(36 %)	
						(40 %)	
						(45 %)	
						(50 %)	
						(54 %)	
						(59 %)	
						(63 %)	
						(68 %)	
						(72 %)	
						(77 %)	
						(81 %)	
						(86 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(4 %)	
						(9 %)	
						(13 %)	
						(18 %)	
						(22 %)	
						(27 %)	
						(31 %)	
						(36 %)	
						(40 %)	
						(45 %)	
						(50 %)	
						(54 %)	
						(59 %)	
						(63 %)	
						(68 %)	
						(72 %)	
						(77 %)	
						(81 %)	
						(86 %)	
						(90 %)	
						(95 %)	
						(100 %)	
								
Recompute......
						(1 %)	
						(3 %)	
						(5 %)	
						(6 %)	
						(8 %)	
						(10 %)	
						(12 %)	
						(13 %)	
						(15 %)	
						(17 %)	
						(18 %)	
						(20 %)	
						(22 %)	
						(24 %)	
						(25 %)	
						(27 %)	
						(29 %)	
						(31 %)	
						(32 %)	
						(34 %)	
						(36 %)	
						(37 %)	
						(39 %)	
						(41 %)	
						(43 %)	
						(44 %)	
						(46 %)	
						(48 %)	
						(50 %)	
						(51 %)	
						(53 %)	
						(55 %)	
						(56 %)	
						(58 %)	
						(60 %)	
						(62 %)	
						(63 %)	
						(65 %)	
						(67 %)	
						(68 %)	
						(70 %)	
						(72 %)	
						(74 %)	
						(75 %)	
						(77 %)	
						(79 %)	
						(81 %)	
						(82 %)	
						(84 %)	
						(86 %)	
						(87 %)	
						(89 %)	
						(91 %)	
						(93 %)	
						(94 %)	
						(96 %)	
						(98 %)	
						(100 %)	
								

```

stderr は0バイト（空）。完全な構造化結果は [result.json](probe-artifacts/datum-link-joint/final/result.json)、子プロセスの結果は [reopen-result.json](probe-artifacts/datum-link-joint/final/reopen-result.json)。最終 FCStd 3文書も同じ場所に保存。GUIで開く検証はしていない。

既存 compatibility.json の a0_remaining_integration は広い未検証項目を含むため unknown のまま保持し、今回の参照経路を独立した check に追加した。既存ファイルの削除は行っていない。
