# CAD-HARNESS MVP — STATUS

2026-10-12、Phase 7。寸法を明記した単純な機械部品の初稿を自然文から作り、
主要寸法を保持したFCStdと受け渡し用STEPを出すMVP。定義した最低合格線をホスト評価で達成した。

## 3層の役割

| 層 | 役割 |
| --- | --- |
| CLI | 入力・単位・仕様の検査、対応形状の決定的な建模、起動・予算管理、独立測定、失敗分類・診断整形、保存・再読込・集計 |
| skill | `skills/freecad-modeling/SKILL.md`。LLMの説明解釈と建模方針を導く一般規約。規約・schema・診断は別のdeveloper contextで渡す |
| prompt | ユーザーの今回のJA/EN説明文だけ。規約やgoldを追記しない |

自然文はSolが短い型付き仕様へ解釈し、CLIが建模する。明示typed入力はLLM不要。
対応範囲外はSolによるソース生成へfallbackできる。採点は人手で凍結したgoldとCLI測定で行い、LLM judgeは使わない。
設計の詳細は[DECISION-02](DECISION-02-architecture.md)・[DECISION-03](DECISION-03-layering.md)。

## 合格線と実測

[DECISION-01](DECISION-01-acceptance-bar.md)：固定5説明を各2 fresh runs、計10件。
P1,P2,P4,P5,P3の順で各2件を実行し、warm-up除外・失敗の差替えはしない。
合格線は8/10以上かつ全partが1/2以上。1 runはSol最大3 calls、CAD最大3 attempts、
説明受領から終了処理まで900秒以内。建模・再検証のfreecadcmdは各300秒を残り時間で短縮する。
幾何gold、単一Body・有効Sketch/native feature・主要寸法・正常再計算の薄い編集gate、
FCStdとSTEPの別process再読込、文書closeと正常終了をすべて満たすことが必要。
寸法±0.01 mm、軸1e-6、P2–P5体積相対1e-4。P1は既存GOAL_VOLUMEの相対1%帯かつV<22500を保持する。
成果物間の体積一致はP1も相対1e-4。goldや許容値は評価結果に合わせて緩めていない。

出典は[集計JSON](../../reports/aggregate-mvp-eval-v1-r2.json)・[CSV](../../reports/aggregate-mvp-eval-v1-r2.csv)のみ。
集計作成日時：2026-10-12 01:28:10.966 JST（JSONのUTC時刻を換算・丸め）。
`bar_met=true`、10/10、全part 2/2、`valid_suite / complete / versions_consistent=true`。
全runでgeometry・editability・reimportがtrue、failure_classはnull。各runはSol 1 call、CAD 1 attempt、19.594–32.281秒。

wallはr1/r2の秒数を小数3桁へ丸め、calls・attempts・token欄は各partの2 run合計。
tokenはprovider usageの各欄を個別合計した値で、推定値・料金ではない。欄を足して総tokenにはしない。

| Part | 合格 | wall秒 r1 / r2 | Sol calls | CAD attempts | input | cached input | cache write | output | reasoning output |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P1 | 2/2 | 23.015 / 25.625 | 2 | 2 | 69600 | 39936 | 0 | 1242 | 649 |
| P2 | 2/2 | 23.859 / 32.203 | 2 | 2 | 69967 | 45056 | 0 | 1459 | 740 |
| P3 | 2/2 | 30.360 / 25.156 | 2 | 2 | 69906 | 45568 | 0 | 1289 | 796 |
| P4 | 2/2 | 23.500 / 32.281 | 2 | 2 | 69867 | 39936 | 0 | 1413 | 792 |
| P5 | 2/2 | 27.281 / 19.594 | 2 | 2 | 69765 | 45568 | 0 | 1171 | 527 |

全10件のusage合計：input=349105、cached input=216064、cache write=0、output=6574、reasoning output=3504。
[再集計JSON](../../reports/aggregate-mvp-eval-v1-r2-reaggregate.json)はrun別データとsummaryが一致し、[再集計CSV](../../reports/aggregate-mvp-eval-v1-r2-reaggregate.csv)も一致する。追加試行ではない。
Supervisor確認：`host-live-probe-r2-mvp1`でdeveloper_instructions注入を確認、grok再checkはREADY。

## 実行方法

ホストの`C:\dev\CAD-HARNESS`で実行。FreeCADは
`C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe`のみ、headless。
以下のpreviewと評価はSolを呼ぶ。既存run ID・集計suffixは再利用せず、週次使用60%の停止条件をホストで確認する。

```powershell
# 自分のUTF-8説明文を仕様previewへ（gold不要、CADなし）
python -B tools\cad_agent.py --mode description --run my-preview-next-mvp1 --description-file my-part.txt
# 新しい固定10件の評価（r2の再実行例。新prefix・suffixを使用）
python -B tools\eval_mvp.py --prefix host-mvp-eval-next --suffix next
# 既存r2の再集計だけ（Sol/CADなし、新suffix）
python -B tools\eval_mvp.py --aggregate-only --prefix host-mvp-eval-r2 --suffix r2-status-check
# 確認済みtyped仕様を建模・採点（LLMなし。goldは人手で確認する）
python -B tools\cad_agent.py --mode typed --run my-build-next-mvp1 --spec confirmed-spec.json --gold confirmed-gold.json
```

`my-part.txt`、`confirmed-spec.json`、`confirmed-gold.json`はユーザーが用意する入力。
previewを確認してから仕様と採点条件を凍結する。FCStd/STEPは成功attemptの
`reports/cad-run/<run>/a<attempt>-mvp1/`に保存される。集計は既存JSON/CSVへの上書きを拒否する。

## 限界と次の候補

- 評価は対応schema内の単純5部品、寸法・加工対象が明示された固定日本語説明に限る。各part N=2で、任意のJA/EN依頼に同じ成功率を保証しない。
- 範囲外agent fallbackと修復経路はこの評価では実行されていない。複雑形状・曖昧な説明・多数試行の性能は未測定。
- GUI操作や寸法変更後の全履歴追従は検証していない。編集可能性は薄いgateまでで、製造適性・強度・別CADカーネルでの正しさは保証しない。
- 合意はgrok+codex。Claudeは組織のsubscription access無効で利用不可だった。
- 次の候補：より難しい／範囲外の別suite、曖昧な説明と確認応答、各partの試行数増加。既存bar・凍結goldとは別版で評価する。

Supervisor報告のローカル履歴：`proto/cad-run`、Phase 3 `183826f..7353beb`、round 2 `f5a0d78 / 63feae0 / 57c0037`、re-check `d881d26`。pushなし。
このPhase 7では集計と決定を読み、STATUS.mdだけを作成した。コード編集・Git・FreeCAD・Sol実行は行っていない。
