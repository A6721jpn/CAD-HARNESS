# A1 型・識別子

`contract.schema.json` の `$defs` が PlateSpec / Operation（計画書のOp）/
Observation / Revision / Job の正規契約です。JSON Schema Draft 2020-12の
構造と、以下の必須拡張で定義します。各型の入口は `#/$defs/PlateSpec` など。
外部ライブラリ・FreeCAD・ネットワークを使いません。

```python
from schemas import load, validate, apply_parameters, transition_job

plate = load("PlateSpec", "fixtures/plate_valid.json")
patch = load("Operation", "fixtures/operation_valid.json")
candidate = apply_parameters(plate, [patch])
job = load("Job", "fixtures/job_valid.json")
running = transition_job(job, "running")
```

`cad-harness` を作業ディレクトリまたはPythonの探索パスに置きます。
全入口は未知キーと不正値を拒否し、元データを変更しない独立したJSON値を返します。
`ValidationError` は値のパスと条件を示します。`load` は重複キーとNaN/Infinityも拒否します。
Pythonクラスを別に二重定義せず、JSON Schemaを型の唯一の定義としています。

## 寸法・意味ID・操作

寸法表現は `100 mm` / `100.125 mm` の文字列です。単位省略、cm/mへの変換、
角度・面積・指数表記は受け入れません。計算はDecimalで行います。
PlateSpecは中心矩形と対称貫通2穴の固定テンプレートで、L/W/T/D/eを要求します。
L=80–180、W=30–80、T=4–16、D=4–12、e=12–25 mm（端点を含む）。
さらに e>D/2、W>D、L−2e>D を要求します。現在の範囲内では3不等式は常に成立しますが、
契約に明記し独立して検査します。範囲外の形状を不等式だけで許可しません。

`plate.main`、`Params.L/W/T/D/e/P`、`Body.BaseSketch/Pad/HoleSketch/Pocket`、
`mount.left/right` を意味IDとして固定します。Face1等のトポロジ番号は対象IDに使えません。
native object対応表の値にはネイティブ名を格納し、ラベルとは分離します。
Operationはタグ付き3択です。`create_body` はL/W/Tと中心矩形、`add_hole_group` は
D/eと対称貫通2穴を指定します。`set_parameters` はhole_diameterとplate_thicknessの
少なくとも一方だけを受け入れます。余分な操作・引数は拒否します。
`apply_parameters` は最新PlateSpecへのM2 patch専用で、L/W/eを保持し各中間値も検査します。
create_body/add_hole_groupの実行・ネイティブ生成はA2の範囲です。

## Revision・Job・Observation

Revisionはrevision_id、document_id、base_revision、candidate_id、base_policyを持ちます。
初版はbase/candidateともnull、派生は両方のIDを要求し、自己参照を拒否します。
base_policyはrequire_currentまたはsnapshotです。既定を暗黙挿入せず明示入力を要求します。
この契約だけでは参照先の実在性、循環、hash、ライブ版との一致は判定しません。

Jobはrequest_id、操作列、Revision、現在stateと履歴を持ちます。
queued→running→validated→committedのみを正常経路とし、各非終端から
failed/cancelled/unknownへ移れます。4つの終端状態からの遷移・再遷移は拒否します。
unknownからの回復・再送の永続化はA4で設計するため、A1では公開を許可しません。
履歴はqueued開始、末尾はstateと一致し、全隣接遷移を検査します。
JobとRevisionのdocument_idは一致必須。validated/committedにはcandidateが必要です。
状態名の検証はCAD検証・採用の実行や合格証明ではありません。

Observationは識別 `identification`、状態 `state`、実測 `measurements`、
検証 `validation`、視覚 `visual` の5群を必須にします。状態に変更前後・Pの式・
独立/従属変数を持ち、実測は要求値から分離します。不正形状の実測結果も記録できます。
検証の5項目はpass/fail/unknownと空でない根拠を持ちます。
visualはreadyなら同じrevisionの上面図と等角図を1枚ずつ要求し、
failed/unknownなら理由と空の画像列を要求します。画像失敗は形状合格に読み替えません。
fixtureの数値・native対応名は合成データです。CAD試験・画像生成は未実施なのでunknownです。

## 必須拡張と実装範囲

標準JSON Schemaだけでは寸法文字列の数値比較や履歴遷移を表せません。
他言語の利用者も以下を実装して初めて同じ契約になります。

| キーワード | 意味 |
| --- | --- |
| x-mm-range | mm文字列の数値部を十進数として、指定した閉区間と比較 |
| x-geometry | dimensionsの各変数にtermsの係数を掛けた総和がgreater_thanより厳密に大きいこと。conditionはエラー説明 |
| x-job-history / x-transitions | queued開始・state一致と遷移表に基づく全履歴検証 |
| x-job-links | 文書ID一致、validated/committedには非nullのcandidate_id |
| x-revision-links | base/candidateのnull整合性と自己base禁止 |
| x-observation-links | ready画像のrevision一致とtop/isometricの組合せ |

`validation.py` は同梱スキーマで使う標準キーワードのみを解釈する限定実装です。
汎用JSON Schemaエンジンではありません。到達した未知のスキーマキーワードも拒否します。
外部参照・型強制変換・FreeCAD API呼出しはありません。

## 再現

リポジトリルートでPowerShellから実行します。

```powershell
& 'C:\Users\NGGmo\AppData\Local\Programs\FreeCAD 1.1\bin\python.exe' -B cad-harness/tests/generate_fixtures.py
& 'C:\Users\NGGmo\AppData\Local\Programs\FreeCAD 1.1\bin\python.exe' -B cad-harness/tests/run_tests.py
```

fixtureの期待受理/拒否と理由は `../fixtures/manifest.json` にあります。
生成スクリプトは既存fixtureと同じ内容を再生成します。
実行器はunittestのstdout/stderrを加工せず `../tests/evidence/` にバイト保存し、
実行コマンド・Python版・終了コードも記録します。失敗時は非ゼロ終了します。
unittestの件数はテストメソッド数です。各メソッド内のsubTestでfixture・全境界・
全状態対・未知キーを網羅します。CAD形状・保存・再読込・DSH試験はA2以降の未実装です。
