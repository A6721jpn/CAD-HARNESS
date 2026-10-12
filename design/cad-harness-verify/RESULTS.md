# CAD-HARNESS VERIFY — RESULTS

**判定：verify-v1-reviewed-r1 の実用barは未達（`bar_met=false`）。** 予定54件は54件とも完了した。fresh eval-v1とlegacy回帰、不足情報を尋ねる経路、V6/S1は合格した。一方、V5は0/2、F1/F2も各0/2で、各partの最低条件とfault修復条件を満たさない。旧MVPの合格線を変えず、本版を実用認定しない。

V5には、保存済みFCStdに実在する駆動PCD寸法をProbeが取りこぼす証拠がある。F1/F2と自然修復の未達は、実際の修復応答が失敗したのではなく、parse repairでcall枠を使い切って修復を起動できなかった。この原因分析は保存された採点を変更しない。

## 出典・版・読み方

- 成績の一次資料：[aggregate JSON](../../reports/aggregate-verify-v1-host-reviewed-r1.json)・[CSV](../../reports/aggregate-verify-v1-host-reviewed-r1.csv)。本書の合否・利用量・時間はこのJSONの各rowと既存run reportsから取り出した。JSON/CSVの全54 ID、合否、wall、Sol/CAD件数を照合した。
- prefix：`host-verify-v1-reviewed-r1`。版：`verify-v1-reviewed-r1`。supervisor指定のcommits：`b339f9d`・`2ad59e7`。版の説明は[FROZEN.md](FROZEN.md)、合格条件は[PLAN-CONSENSUS.md](PLAN-CONSENSUS.md)、検証項目(a)–(i)は[BRIEF.md](BRIEF.md)。
- [suite-run.json](../../reports/cad-run/host-verify-v1-reviewed-r1-verify-suite-mvp1/suite-run.json)・[実行plan.json](../../reports/cad-run/host-verify-v1-reviewed-r1-verify-suite-mvp1/plan.json)。開始は2026-10-12 19:44:41.878 JST、suite-run作成は20:48:48.978 JST、独立集計作成は20:54:31.916 JST。devから最後のfaultまでの記録wallは3847.140秒。集計を含む共通deadlineは`deadline_ok=true`。
- manifest SHA-256：`d03406333a4a01fdae336c8582f71cb2f3d6edd9a9a7c01b78d92366a2069edc`。aggregateは`valid_suite / complete / versions_consistent / deadline_ok=true`、`stop_reason=null`。既存manifestの133ファイルは本解析時も一致した。これは計測実装の完全性を保証するフラグではない。
- 表のpassはaggregateの`passed`をそのまま使う。通常部品は経路、幾何、薄い編集gate、FCStd/STEP再読込、close/exitまでの全条件。Q2/Q3は初回rubricの点数、legacyはgood/brokenの期待結果一致。これらを一般の自然文成功率として合算しない。
- Wilsonは両側95%、z=1.96。part値はaggregateの`summary.per_part`、固定suite小計は同じ式でそのrowから算出した。全対象が完了したため表示できる。各CIは当該固定batch/partの記述値であり、任意のJA/EN要求への母集団保証ではない。
- wallは失敗も含むaggregateの`wall_s`、中央値・p95・最大を小数3桁に丸めた。p95は昇順の`ceil(0.95*N)`番目で、補間しない。小標本ではp95と最大が同じになる。
- `CAD全 / 後続`は全CAD attemptsと各runの`max(CAD attempts−1,0)`の合計。本batchの後続CADはF3の修復のみ。`repair calls`はSolのpurpose=repair、`parse repair calls`は別のpurposeで、CAD修復と混ぜない。未記録値は`null`のまま。
- 今回は既存JSON/CSV、source、diagnostics、FCStd ZIP内XMLを読み、この2文書だけを作成した。FreeCAD/Sol、unit tests、新run、再aggregate、コード編集、gold編集、Git操作は行っていない。

## suite別の成績・資源・失敗分類

| Suite / part | pass/N | Wilson 95% | wall 秒 med / p95 / max | Sol calls | CAD全 / 後続 | repair calls | parse repair calls | failure_class 分布 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| eval-v1 | 10/10  | 72.25–100.00% | 23.367 / 34.641 / 34.641 | 10 | 10 / 0 | 0 | 0 | `null`=10 |
| legacy | 4/4  | 51.01–100.00% | 0.492 / 0.562 / 0.562 | 0 | 4 / 0 | null | null | `null`=4 |
| V1–V5 | 8/10  | 49.02–94.33% | 142.664 / 347.797 / 347.797 | 24 | 10 / 0 | 0 | 4 | `null`=8; `budget`=2 |
| V6 | 3/3  | 43.85–100.00% | 32.593 / 36.750 / 36.750 | 3 | 3 / 0 | 0 | 0 | `null`=3 |
| S1 | 5/5  | 56.55–100.00% | 28.797 / 33.578 / 33.578 | 5 | 5 / 0 | 0 | 0 | `null`=5 |
| Q1 | 3/3  | 43.85–100.00% | 22.734 / 23.125 / 23.125 | 3 | 3 / 0 | 0 | 0 | `null`=3 |
| Q2 | 5/5  | 56.55–100.00% | 23.610 / 27.750 / 27.750 | 5 | 0 / 0 | 0 | 0 | `null`=5 |
| Q3 | 5/5  | 56.55–100.00% | 24.906 / 28.594 / 28.594 | 5 | 0 / 0 | 0 | 0 | `null`=5 |
| F1 | 0/2  | 0.00–65.76% | 201.235 / 209.485 / 209.485 | 6 | 2 / 0 | 0 | 2 | `budget`=2 |
| F2 | 0/2  | 0.00–65.76% | 274.960 / 298.968 / 298.968 | 6 | 2 / 0 | 0 | 2 | `budget`=2 |
| F3 | 2/2  | 34.24–100.00% | 68.758 / 75.343 / 75.343 | 4 | 4 / 2 | 2 | 0 | `null`=2 |

`null`というfailure_classは「失敗分類なし」。V1–V5は先登録したfallback batchの小計である。V6/S1、Q、fault、回帰をそのCIへ加えない。

### fresh eval-v1

| Suite / part | pass/N | Wilson 95% | wall 秒 med / p95 / max | Sol calls | CAD全 / 後続 | repair calls | parse repair calls | failure_class 分布 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| P1 | 2/2  | 34.24–100.00% | 26.789 / 30.937 / 30.937 | 2 | 2 / 0 | 0 | 0 | `null`=2 |
| P2 | 2/2  | 34.24–100.00% | 26.554 / 29.672 / 29.672 | 2 | 2 / 0 | 0 | 0 | `null`=2 |
| P4 | 2/2  | 34.24–100.00% | 21.586 / 23.297 / 23.297 | 2 | 2 / 0 | 0 | 0 | `null`=2 |
| P5 | 2/2  | 34.24–100.00% | 28.297 / 34.641 / 34.641 | 2 | 2 / 0 | 0 | 0 | `null`=2 |
| P3 | 2/2  | 34.24–100.00% | 25.125 / 29.281 / 29.281 | 2 | 2 / 0 | 0 | 0 | `null`=2 |

全partが2/2。旧barの「8/10以上かつ各part 1/2以上」を満たす。旧STATUSの過去10/10を流用した結果ではなく、今回prefixのfresh 10件。各runは初回からgeometry/editability/reimportの全gateを通り、parse/CAD修復はない。

### legacy A/B

| Suite / part | pass/N | Wilson 95% | wall 秒 med / p95 / max | Sol calls | CAD全 / 後続 | repair calls | parse repair calls | failure_class 分布 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| A-good | 1/1  | 20.65–100.00% | 0.500 / 0.500 / 0.500 | 0 | 1 / 0 | null | null | `null`=1 |
| A-broken | 1/1  | 20.65–100.00% | 0.422 / 0.422 / 0.422 | 0 | 1 / 0 | null | null | `null`=1 |
| B-good | 1/1  | 20.65–100.00% | 0.562 / 0.562 / 0.562 | 0 | 1 / 0 | null | null | `null`=1 |
| B-broken | 1/1  | 20.65–100.00% | 0.485 / 0.485 / 0.485 | 0 | 1 / 0 | null | null | `null`=1 |

A/BのgoodはProbe pass、brokenはProbe failとなり、close/正常exitまで含めて期待結果に一致したため4/4。brokenを正常部品の成功として数えた値ではない。legacy rowのgeometry/editability/reimportは`null`なので、通常生成物と同じ全gate検証済みと読み替えない。Sol callsは記録上0、provider usageは`null`。

### V1–V5：description→unsupported→source

| Suite / part | pass/N | Wilson 95% | wall 秒 med / p95 / max | Sol calls | CAD全 / 後続 | repair calls | parse repair calls | failure_class 分布 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| V1 | 2/2  | 34.24–100.00% | 157.070 / 184.203 / 184.203 | 6 | 2 / 0 | 0 | 2 | `null`=2 |
| V2 | 2/2  | 34.24–100.00% | 122.383 / 140.000 / 140.000 | 4 | 2 / 0 | 0 | 0 | `null`=2 |
| V3 | 2/2  | 34.24–100.00% | 127.172 / 163.359 / 163.359 | 4 | 2 / 0 | 0 | 0 | `null`=2 |
| V4 | 2/2  | 34.24–100.00% | 140.906 / 145.328 / 145.328 | 4 | 2 / 0 | 0 | 0 | `null`=2 |
| V5 | 0/2  | 0.00–65.76% | 310.329 / 347.797 / 347.797 | 6 | 2 / 0 | 0 | 2 | `budget`=2 |

10/10で`route_ok=true`、unsupported→sourceの経路を実際に通った。V1–V4は各2/2で全gateに合格し、V5は両runのgeometry=trueだがeditability=false。従ってfallback経路の実行は確認できたが、先登録barの各part最低1/2を満たさない。source修復の成功とは別の結果である。

### V6・S1

V6は3/3、S1は5/5。いずれもsource fallbackを経ないcompiler経路で、初回から全gateに合格した。V6の複数ポケット・穴・外周面取りと、S1のポケット・外周Rは、この固定入力では確認できた。S1の採点は凍結された下部stock体積と局所R断面で、全体積を新しいtargetへ置き換えていない。全体積は成果物間の一致に使われている。

### Q1–Q3

Q1は3/3で初回specのXY中心/底Z=0を採用し、不要質問なしで全幾何gateに合格。Q2は5/5で`plate_thickness`、Q3は5/5で`hole_positions`だけを尋ねた。Q2/Q3の各runはSol 1 call、CAD 0、初回で終了し、`critical_inventions=0`。回答後の対話や完成までの能力は測っていない。

### F1–F3：故障成立・検出・最終修復

| Suite / part | pass/N | Wilson 95% | wall 秒 med / p95 / max | Sol calls | CAD全 / 後続 | repair calls | parse repair calls | failure_class 分布 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| F1 | 0/2  | 0.00–65.76% | 201.235 / 209.485 / 209.485 | 6 | 2 / 0 | 0 | 2 | `budget`=2 |
| F2 | 0/2  | 0.00–65.76% | 274.960 / 298.968 / 298.968 | 6 | 2 / 0 | 0 | 2 | `budget`=2 |
| F3 | 2/2  | 34.24–100.00% | 68.758 / 75.343 / 75.343 | 4 | 4 / 2 | 2 | 0 | `null`=2 |
| F全episode | 2/6  | 9.68–70.00% | 201.235 / 298.968 / 298.968 | 16 | 8 / 2 | 2 | 4 | `budget`=4; `null`=2 |

| 固定fault cohortの指標 | 値 | Wilson 95% |
| --- | ---: | --- |
| reached | 6/6 | 60.97–100.00% |
| established（settled geometry fail） | 6/6 | 60.97–100.00% |
| prescribed predicate detected | 6/6 | 60.97–100.00% |
| 最終全gate pass / planned | 2/6（33.33%） | 9.68–70.00% |
| 最終pass / established | 2/6（33.33%） | 9.68–70.00% |
| 自然修復：eligible runの最終pass | 0/2 | 0.00–65.76%（完了eligible cohortからの派生値） |

成立・検出は全件成功し、not_reachedはない。F3だけが実際のrepair callと後続CADを各runに1回ずつ持ち、2/2で全gate成功した。F1/F2はrepair calls=0、後続CAD=0。この0/2を「source修復応答を2回試して2回とも失敗した」と解釈しない。起動されたsource修復の成功率は分母0でN/A。

自然修復の分母2はV5の2件だけで、aggregateの定義は「初回CADが修復可能な全gate failだったrun」。両方とも修復を開始できず最終pass=0なので、保存された指標は0/2。実際に起動された自然CAD修復も0件で、その成功率はN/A。parse repairはここへ算入しない。

## provider token fields

各欄を当該rowのprovider usageから個別に合計した。全callには費やしたparse repairと失敗分も含む。input/cache/output/reasoningは重なる内訳を持つため、欄を足して「総token」にはしない。欠測を0で補完せず、推定料金やtoken→使用率換算は行わない。小計と内訳は重複するので、表の全行を足さない。

| Scope | input | cached input | cache write input | output | reasoning output |
| --- | ---: | ---: | ---: | ---: | ---: |
| eval-v1 | 348763 | 182272 | 0 | 5425 | 2502 |
| legacy | null | null | null | null | null |
| V1–V5 | 761545 | 350080 | 0 | 44166 | 31322 |
| V6 | 105182 | 51840 | 0 | 2552 | 1114 |
| S1 | 175593 | 115840 | 0 | 3264 | 1862 |
| Q1 | 104928 | 76928 | 0 | 1545 | 839 |
| Q2 | 157679 | 123648 | 0 | 2153 | 1677 |
| Q3 | 175285 | 125952 | 0 | 2345 | 1700 |
| F1 | 205960 | 111360 | 0 | 10153 | 7623 |
| F2 | 188592 | 112000 | 0 | 14656 | 10248 |
| F3 | 146556 | 97664 | 0 | 3533 | 1577 |
| V1 | 169398 | 70144 | 0 | 7712 | 5661 |
| V2 | 134102 | 65792 | 0 | 6155 | 4391 |
| V3 | 134308 | 50304 | 0 | 6382 | 4952 |
| V4 | 134091 | 61056 | 0 | 7422 | 4755 |
| V5 | 189646 | 102784 | 0 | 16495 | 11563 |
| P1 | 69759 | 45056 | 0 | 1314 | 755 |
| P2 | 69693 | 34304 | 0 | 1184 | 437 |
| P4 | 69750 | 34304 | 0 | 748 | 220 |
| P5 | 69799 | 34304 | 0 | 1207 | 530 |
| P3 | 69762 | 34304 | 0 | 972 | 560 |
| dev 合計（非採点） | 137821 | 51712 | 0 | 5714 | 4274 |
| DV1 | 67545 | 17280 | 0 | 4321 | 3531 |
| DV6 | 35211 | 17280 | 0 | 946 | 423 |
| DQ2 | 35065 | 17152 | 0 | 447 | 320 |
| 全Sol使用run（legacy除外） | 2507904 | 1399296 | 0 | 95506 | 64738 |
| 全54 records（legacy nullを含む） | null | null | null | null | null |

geometry群の検算小計はinput=1042320、cached input=517760、cache write=0、output=49982、reasoning output=34298。Q群は437892 / 326528 / 0 / 6043 / 4216、fault群は541108 / 321024 / 0 / 28342 / 19448で、aggregateの`provider_tokens`と一致する。

「全Sol使用run」はlegacyだけを除き、devを含めた実usageのあるscope。全54 recordsを欠測伝播で合計するとlegacyの`null`が残る。legacyの0 Sol callsと欠測usageを同一視しない。

全54件のwall中央値/p95/最大は29.039 / 272.860 / 347.797秒。全実行のSol callsは75、CAD attemptsは43、実repair callsと後続CADはいずれも2、parse repair callsは8。failure_classの全記録分布は`null=46 / budget=6 / interpretation=2`で、`interpretation`2件は次の非採点dev。全suiteを混ぜたpass率/CIは作らない。

## dev：非採点・別報告

devは別寸法pilotで最大4 callsの枠を実際に4 calls使用した。実用barやtest率に含めない。以下のpass/NとCIはaggregateに保存されたflagの参考表示で、devの合否認定ではない。

| Suite / part | pass/N | Wilson 95% | wall 秒 med / p95 / max | Sol calls | CAD全 / 後続 | repair calls | parse repair calls | failure_class 分布 |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| DV1 | 0/1 （raw・非採点） | 0.00–79.35%（参考） | 178.141 / 178.141 / 178.141 | 2 | 0 / 0 | 0 | 0 | `interpretation`=1 |
| DV6 | 0/1 （raw・非採点） | 0.00–79.35%（参考） | 35.218 / 35.218 / 35.218 | 1 | 0 / 0 | 0 | 0 | `interpretation`=1 |
| DQ2 | 1/1 （raw・非採点） | 20.65–100.00%（参考） | 21.688 / 21.688 / 21.688 | 1 | 0 / 0 | 0 | 0 | `null`=1 |

dev合計のwall中央値/p95/最大は35.218 / 178.141 / 178.141秒、Sol 4、CAD 0、repair/parse callsとも0。geometryとclarificationを混ぜたdev全体の成功率/CIは提示しない。

[DV1 driver](../../reports/cad-run/host-verify-v1-reviewed-r1-dev-DV1-r1-mvp1/driver-run.json)と[DV6 driver](../../reports/cad-run/host-verify-v1-reviewed-r1-dev-DV6-r1-mvp1/driver-run.json)は、いずれも`status=preview / message_code=confirmation_required`。DV1はunsupportedを正しく返した後に`preview-source.py`を作り、DV6は有効なspecを返してpreviewへ進んだ。CADは起動されず、initial/final gatesも`null`。DQ2は不足寸法を正しく尋ねて終了した。

原因は[runner](../../tools/eval_verify.py)がdevを`evaluation=false`で呼び、[driver](../../tools/cad_agent.py)がdescription previewで止めるのに、集計は通常のCAD完了gateでdevのflagを判定すること。したがってDV1/DV6の`failure_class=interpretation`は、モデルの解釈失敗・FreeCAD建模失敗・Probe測定失敗を示す証拠ではない。pilotの記録/採点設計の不整合で、動的CAD能力はこの2件では未測定。保存された0/1のflagを再採点しない。

## 失敗の原因分析

### V5 0/2：形状は一致、PCD60の駆動寸法追跡に欠陥

[r1の診断](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r1-mvp1/a1-mvp1/result.json)・[r2の診断](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r2-mvp1/a1-mvp1/result.json)は共に`geometry_ok=true`、`native_valid=true`、正常close/exitで、唯一の不一致は`edit.driving_dimension.7: expected=60, actual=null`。bboxは[-42,42,-42,42,0,8]、体積はr1=40276.24434315141、r2=40276.24434315142 mm³、診断のgold target=40276.24434315141 mm³。穴径・中心・溝を含む幾何checksは通っている。editability=falseのためSTEP/独立reimportは起動されておらず、再読込失敗とは分類しない。

[r1 source](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r1-mvp1/input-a1.py)・[r2 source](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r2-mvp1/input-a1.py)は、使用されるThroughHoleProfile内にconstruction pitch circleを作り、Diameter=60のconstraintと、実穴中心からそのcircleへのPointOnObject接続を定義している。さらに保存済み[r1 FCStd](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r1-mvp1/a1-mvp1/model.FCStd)・[r2 FCStd](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r2-mvp1/a1-mvp1/model.FCStd)のZIP内`Document.xml`を、FreeCADを起動せずに読んで確認した：

| 既存FCStdに保存された証拠 | r1 | r2 |
| --- | --- | --- |
| ThroughHoles.Profile | ThroughHoleProfile | ThroughHoleProfile |
| pitch geometry | construction circle、Radius=30 | construction circle、Radius=30 |
| PCD constraint | Value=60、First=1、Type=18（sourceでDiameter） | 同左 |
| constraint状態 | IsDriving=1、IsActive=1 | 同左 |
| pitchへのPointOnObject接続 | 8件 | 8件（ray経由の接続を含む） |
| Probeの採点 | PCD60が見つからない | PCD60が見つからない |

現版[Probeのeditability](../../tools/cad_verify_probe.py)は、construction geometryの寸法をReferenceAxisで使用されたconstructionだけから採る。Sketch内部のPointOnObject等による実geometryへの依存を追わないため、実際に使用中のPCD circleまで除外する。**これはモデルがPCDを作らなかった失敗ではなく、Probeのused-dimension追跡によるfalse-negativeを示す証拠である。** 数値goldの算術誤りを示す証拠はない。動的な寸法変更試験やSTEP再読込を新規に行ったわけではないため、全履歴追従の証明はしない。

r1/r2は共に`interpretation→parse_repair→source`でSol 3 callsを消費し、driverは`call_limit`で終了した。集計failure_classはそのまま`budget`2件、成績は0/2、bar_met=falseを保持する。静的に原因が判明しても旧版のgateを外したり合格に置き換えたりしない。

### F1/F2 0/2ずつ：検出成功、修復callを残せなかった

[F1 r1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F1-r1-mvp1/driver-run.json)・[F1 r2](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F1-r2-mvp1/driver-run.json)、[F2 r1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F2-r1-mvp1/driver-run.json)・[F2 r2](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F2-r2-mvp1/driver-run.json)の4件は全て同じ順：call 1のspecが未対応操作を表そうとし、call 2のparse repairでunsupportedへ訂正、call 3でsourceを生成。その直後に凍結faultを差し替えて初回CADを実行した。`actual_call=3`、CAD attempts=1、`reached / established / detected=true`。次のrepairへ入る前に固定上限で`call_limit`となり、repair callもrepair sourceも後続CADも存在しない。

| 既存の注入CAD診断 | r1/r2の値 | 所定fail |
| --- | ---: | --- |
| F1体積 | 27143.36052701581 mm³（target 26389.37829015426） | 溝断面・肩・roller、native_valid=true |
| F2体積 | 40433.3239758309 mm³（target 40276.24434315141） | holes count=8、expected=9（中央穴を含む）、所定PCD穴欠落 |
| F1/F2初回CAD exit/close | exit=0、closed、cleanup=exited | settled、Probe例外なし |

個別診断：[F1 r1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F1-r1-mvp1/a1-mvp1/result.json)・[F1 r2](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F1-r2-mvp1/a1-mvp1/result.json)・[F2 r1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F2-r1-mvp1/a1-mvp1/result.json)・[F2 r2](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F2-r2-mvp1/a1-mvp1/result.json)。凍結した欠陥は測定どおりに検出されており、この初回failをgold/Probe誤りとする証拠はない。

モデル側の問題は初回にunsupportedを選べず無効なbuild-specを出したこと。実験/driver側の制約はparse correction、fallback、CAD repairが同じ3-call枠を共有し、注入後のsource修復機会を残せなかったこと。この4件から「sourceを修復するモデル能力が低い」とは判定できない。ただしplanned episodeの最終成功0/2ずつは有効な未達で、版の途中でcall上限や分母を変えない。

対して[F3 r1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F3-r1-mvp1/driver-run.json)・[F3 r2](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F3-r2-mvp1/driver-run.json)はcall 1でspecを注入し、実repairをcall 2で行った。初回の穴半径actual=3、expected=2が検出され、後続CADの体積は94616.86398243284 mm³、全gateがtrueになった。spec修復2/2は確認済みで、source修復の代用にはならない。

### 8 parse repair calls：JSON構文ではなく対応範囲の誤選択

| cohort | 対象run | parse repair calls | 最終pass | CAD repair calls |
| --- | --- | ---: | ---: | ---: |
| clean V1 | r1/r2 | 2 | 2/2 | 0 |
| clean V5 | r1/r2 | 2 | 0/2 | 0 |
| fault F1 | r1/r2 | 2 | 0/2 | 0 |
| fault F2 | r1/r2 | 2 | 0/2 | 0 |
| 合計（parse cohortの確認） | 上記8 run | 8 | cohort間の率を合算しない | 0 |

全8件の`last-c1.txt`は読み取れるJSONで、stepped_shaftにholes、V5/F2ではpocketsも指定している。意味/対応範囲の契約違反であり、壊れたJSON構文ではない。現compilerはその組合せを`unsupported_shaft_operation`で拒否する。各`last-c2.txt`はunsupportedに訂正され、続くsource生成まで進む。8回のparse correctionはその目的では機能したが、V5/F1/F2の6件では後続CAD修復用のcall枠を使い切った。

一次応答例：[V1 r1 call1](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V1-r1-mvp1/last-c1.txt)・[訂正call2](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V1-r1-mvp1/last-c2.txt)、[V5 r1 call1](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r1-mvp1/last-c1.txt)・[訂正call2](../../reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r1-mvp1/last-c2.txt)、[F1 r1 call1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F1-r1-mvp1/last-c1.txt)、[F2 r1 call1](../../reports/cad-run/host-verify-v1-reviewed-r1-fault-F2-r1-mvp1/last-c1.txt)。8件という名称/件数はaggregateの`parse_repair_calls`を変更せず、CAD repairと分けて解釈した。

## 実用bar：条件ごとの判定

| 凍結threshold | 記録された結果 | 判定 |
| --- | --- | --- |
| 全planned IDs完了、版整合、deadline/stop条件 | 54/54、valid/complete/versions/deadline=true、stop=null | MET（記録上） |
| fresh eval-v1 ≥8/10、各P ≥1/2 | 10/10、各2/2 | MET |
| legacy good/broken全一致 | 4/4 | MET |
| V1–V5 ≥8/10 | 8/10 | MET |
| V1–V5 各≥1/2、所定fallback経路 | routeは10/10、V5のみ0/2 | **UNMET** |
| V6 ≥2/3 | 3/3 | MET |
| S1 ≥4/5 | 5/5 | MET |
| Q1 ≥2/3 | 3/3 | MET |
| Q2/Q3 各≥4/5 | 各5/5 | MET |
| 重要欠落の黙った発明0件 | 0件 | MET |
| fault成立/所定初回検出とも6/6 | 各6/6 | MET |
| fault最終全gate ≥4/6 | 2/6 | **UNMET** |
| 各fault ≥1/2 | F1=0/2、F2=0/2、F3=2/2 | **UNMET** |
| spec/source双方の実修復成功 | spec=2件、source=0件（未起動） | **UNMET** |
| guard：dev≤4 calls、全call枠≤125、fresh snapshot、55% soft/60% hard | dev=4、全75、75 snapshotがallow、記録使用8–9%、最大age=171.776秒 | MET（記録上） |
| 成功物の全gate、false pass / harness停止条件 | aggregateは停止なし。V5に計測のfalse-negativeを後から確認 | 成功物gateは記録上MET、Probe検証課題は未解決 |
| 総合 `bar_met` | false | **UNMET** |

guardの数字はsuite-runのsnapshot記録であり、provider usageから使用率を推定した値ではない。閾値違反の実場面を本live batchで試した結果でもない。

## STATUSの未検証課題とplan(a)–(i)の判定

| 課題 / plan項目 | 今回の結論 | 残る範囲 |
| --- | --- | --- |
| (a) out-of-schema fallback | 経路10/10、V1–V4の全gate各2/2。**部分確認** | V5の正式合格は0/2で、construction寸法追跡のProbe欠陥を解決する必要 |
| (b) repair loop | 注入/検出6/6、spec実修復2/2。**source/自然修復は未確認、実用bar未達** | F1/F2と自然eligible V5はrepair callなし。単なる修復能力不良とは言えない |
| (c) ambiguity / defaults | Q1=3/3、Q2/Q3各5/5、重要発明0。**初回の限定範囲は確認** | 回答後の対話・建模、他の不足情報や言語への一般化は未測定 |
| (d) complex multi-feature parts | V6=3/3、S1=5/5、taper/pipe/ribも通過。**固定形状では部分確認** | V5のProbe課題。任意形状、製造適性、強度、別kernelは対象外 |
| (e) repeats / statistics | 先登録N=2/3/5の全件を報告し、完了partにWilson。**計画範囲MET、一般性能推定は未達** | 2/2の下限は34.24%、5/5も56.55%。全partでN≥5を測ったわけではない |
| (f) regression | 新eval-v1 10/10＋legacy 4/4。**MET** | GUIと寸法変更後の全履歴追従は今回の回帰に含まれない |
| (g) metrics | 初回/最終gate、時間、calls、usage、attempts、失敗分類を記録。**MET、分類解釈に留意** | `budget`は原因を隠す場合がある。devの`interpretation`はpreview停止を拾ったもの |
| (h) holdout / freeze | frozen SHAと版整合、dev/test別報告、途中調整/差替えなしの記録。**記録上MET** | 新修正のacceptanceは新holdout。本版の旧失敗を差替えない |
| (i) stopping / practical | 全件完了、記録guard条件を守った。**practical UNMET** | V5とsource修復条件が未達。probe false-negativeは本版を再採点せず新版で検証 |

[STATUS.md](../cad-harness-mvp/STATUS.md)で未測定だったfallback、修復、曖昧さ、複雑形状、小標本の課題は、上記の範囲まで証拠が増えた。GUI操作、回答後の完成、寸法変更後の全履歴追従、別CAD kernel、任意JA/EN要求への一般成功率は依然未確認。MVP回帰の合格をVERIFY全体の実用認定へ拡張しない。

## 次の作業（提案のみ：新版＋未使用holdout）

1. **Probeを先に検証する。** V5の保存済みsource/FCStdは不具合再現用dev資料として使い、Sketch内部のconstraint依存から使用中のconstruction寸法を追えるか調べる。未使用の寸法decoyは引き続き拒否し、全constructionを無条件に数えて合格にしない。gold/許容差/gateを観測値に合わせて変更しない。
2. **実source修復を測れる計画にする。** 初回のunsupported判断と一般的な対応範囲説明を改善する候補をdevで検討し、source fault成立後に少なくとも実修復を起動できるよう、call配分と停止条件を次版の計画で先登録する。旧版の上限を後から延ばしたり、8回のparse repairをCAD repair成功と数えたりしない。
3. **devの観測を分ける。** preview成功/確認待ちをCAD成功・解釈失敗から区別し、pilotが資源/経路を見るだけか、実CADまで確認するかを明示する。本版のDV1/DV6を再採点する提案ではない。
4. **修正は別版として測る。** 例えば`verify-v2-proposed`という新計画で、コード/skill/Probe/入力・人手gold/rubric/faults/N/順/予算を先に凍結し、新prefixで新しい未使用testを実行する。現版のreportsとbar_met=falseを保存する。現V5/F1/F2の成功再試行を新holdoutの代用にしない。
5. **一般化は別課題にする。** 新版の計測・repair経路が成立してから、より多い先登録N、別寸法/構成、必要なら別言語・対話後完成へ対象を広げる。今回のCIやprovider実績を範囲外の成功率・費用保証に使わない。

これらの修正・試行は本Phase 4では実施していない。結果への署名状況は[RESULTS-CONSENSUS.md](RESULTS-CONSENSUS.md)。

## データ照合

aggregate JSON SHA-256：`832ec5d6ea30125f35c17666a7155645462db35f9bb500ad96a2926afd1288ce`。CSV SHA-256：`1410997f2876596f46b9afacb9ade11dda787b8459aa653034875ea60a88508d`。表は既存rowの合否を保持し、suite内で統計/usageを算出した。診断による原因説明を追加しても、元aggregate、run reports、frozen manifest、code、goldは変更していない。

