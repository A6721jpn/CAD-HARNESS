# DECISION-03 — CAD-HARNESS MVP layering

2026-10-11 draft。22:44 JSTのユーザー原則を全構成へ適用する。Codexは合意、grok署名待ち。
決定可能な処理はCLI、解釈・建模の判断はskillを読むSol、promptはユーザーの今回の入力だけ。
本書・DECISION-02・必要なDECISION-01の文言だけを更新する。実装、FreeCAD/Sol実行は行わない。

## 自然文とtyped inputの境界

採用は(b)：自然文→Solによる短いbuild_spec→CLI検証・compiler→CAD→独立Probe。型付き入力なら解釈を省略する。
build_specは寸法・配置・加工対象を表す宣言的JSONであり、FreeCADソースや解答のfeature graphではない。
CLIが対応形状と固定recipeを選ぶ。自然文の意味を読めることと、JSONを検証できることは別である。

| 案 | 決定 | 理由 |
| --- | --- | --- |
| (a) typed inputだけcompile、自然文はSol build(doc) | typed入口はACCEPT、自然文の主経路はCOUNTER | 自然文でも毎回長いソースを書かせず、対応範囲の建模をCLIへ移せる |
| (b) Sol解釈→CLI compile、範囲外はSol build(doc) | ACCEPT | 自然文を入口に保ち、通常は1 callの短い仕様出力で済む |
| (c) JA/ENをすべてCLI抽出 | COUNTER（MVPには追加しない） | 任意文の意味・曖昧さは決定的に扱えない。明示typed JSON/formの読取・換算・配置展開はCLIにする |

対応範囲は5部品に必要な矩形押出/矩形領域の一体化、同軸段付き円柱、矩形pocket、円形通し穴、指定上面外周のR/C。
recipeは寸法を変えて使える型別実装。P1–P5、説明SHA、goldへのlookupで解答を選ばない。
unknown/unsupported条件を黙って落とさない。自然文で範囲外なら元説明からagent生成へfallbackし、同じ予算を消費する。
compilerの例外・native構成不良はharness不具合として停止する。Solによるcompiler修正や、失敗を隠すfallbackは行わない。

## 最終境界表

「skill / Sol」は判断をskillの一般規約で導く層。「新規」は合意後の予定ファイルであり、本draftで作らない。

| component | layer | why | owner file |
| --- | --- | --- | --- |
| ユーザーの自然文/typed入力 | prompt | 今回の入力だけ。規約・schema・診断を追記しない | tools/cad_agent.py |
| 入力受付、SHA、mode選択 | CLI | description/typedの明示入口を区別し、再現可能に記録 | tools/cad_agent.py |
| typed JSON/form読取、単位換算、穴配置展開 | CLI | 型・既定座標・数値計算は固定処理 | tools/cad_spec.py（新規） |
| 自然文から寸法/配置/加工対象の解釈 | skill / Sol | JA/ENの意味と曖昧さには判断が必要 | skills/freecad-modeling/SKILL.md（新規）; tools/cad_agent.py |
| schema、有限値、範囲、対応加工、接続/干渉の既知条件 | CLI | 検査できる条件を全件検査し、未知条件はunsupported | tools/cad_spec.py; design/cad-harness-mvp/build-schema.json（新規） |
| 規約/contextの組立、出力契約、JSON/source検査 | CLI | 固定契約を別developer contextへ渡す | tools/cad_agent.py |
| 対応型のrecipe選択とnative build(doc)生成 | CLI | 同じspecとcompiler版なら同じ構築手順。planner不要 | tools/cad_spec.py |
| 建模作法・範囲外の構築戦略/ソース生成 | skill / Sol | featureの選択・依存関係の設計は判断 | skills/freecad-modeling/SKILL.md; tools/cad_agent.py |
| attempt、call数、900秒deadline、300秒clip | CLI | 全mode/fallback共通の上限 | tools/cad_agent.py; tools/cad_run.py |
| launch、exec、文書close、所有PID回収 | CLI | OS/CADの操作と終了確認は固定処理 | tools/cad_run.py; tools/cad_run_freecad.py |
| 人手goldの凍結・読込・版照合 | CLI（値の承認は人） | 生成側に期待値を作らせない | design/cad-harness-mvp/eval-v1/P1.json〜P5.json（新規）; tools/cad_spec_probe.py（新規） |
| 幾何測定・gold比較 | CLI | 保存BRepのbbox/体積/穴/pocket/段/R/Cを検査 | tools/cad_spec_probe.py |
| 薄い編集可能性とskill警告 | CLI | 必須gateと助言を機械的に分ける | tools/cad_spec_probe.py |
| rule-based失敗分類・修復許可 | CLI | 既知状態から停止/修復を決め、根本原因を推測しない | tools/cad_agent.py repair_reason(); tools/cad_run.py |
| expected/actualのfeedback整形 | CLI | Probeと同じ比較値をpredicate_detailsへ変換 | tools/cad_spec_probe.py; tools/cad_run_probes.py; tools/cad_agent.py |
| 未確認build_spec/sourceの修復判断 | skill / Sol | 診断を読んで寸法解釈/構築を改める | tools/cad_agent.py; skills/freecad-modeling/SKILL.md |
| FCStd/STEP保存と別process再読込 | CLI | 結果ファイルを生成コードなしで再検査 | tools/cad_run_freecad.py; tools/cad_verify_freecad.py（新規） |
| usage、時間、SHA、全試行集計、A/B回帰 | CLI | 実測記録と固定条件の比較 | tools/cad_agent.py; tools/cad_run.py; tools/test_cad_agent.py; tools/test_cad_run.py |

数値の既定値、許容、許可型、出力形式はCLI/schemaが所有する。skillは選択理由・建模の作法を担い、判定器や起動手順を所有しない。
skill・schema契約・修復データはper-call -c developer_instructionsへ渡す。user payloadは初回も修復も同じ元入力。
codex execの専用system-messageフラグはない。0.159.2のhelpと公式設定資料で確認済みの渡し方をDECISION-02へ保持する。実注入は未検証。

## 1 runの最小/最大LLM calls

| 経路 | 最小 | 上限/条件 |
| --- | --- | --- |
| 明示typed input→CLI compile | 0 | コンパイル/Probe不一致は停止。AI修復を自動追加しない |
| 自然文→build_spec→CLI compile（DECISION-01の主経路） | 1 | 解釈修復を含めSol合計最大3 |
| 自然文の範囲外判定→Sol build(doc) | 2 | 解釈1+ソース1。修復は残り予算内、合計最大3 |
| 明示agent modeで自然文→Sol build(doc) | 1 | 最大3。suiteの主経路を黙ってこのmodeへ変更しない |

全経路でcad_run建模最大3 attempts、end-to-end 900秒、各freecadcmdは300秒を残り時間で短縮する。
不正JSON/sourceもcall数を消費する。fallbackでカウンタをリセットせず、別processの再読込も900秒へ含める。
compiled形状のgold不一致はspecかcompilerか未確定。description経路の未確認specには失敗幾何の診断を返せるが、compilerを書き換えさせない。
同一specの再出力は再CADせず停止する。確認済みtyped spec、起動/保存/再読込/Probe例外/cleanup不良は人へ戻す。
実運用では同じ解釈出力を仕様プレビューに使い、ユーザー確認後に凍結する。通常compileのための別ソースcallは不要。

## DECISION-01が測る経路と削減するcalls

5件の正確な自然文から上記description経路を各2回測る。goldをcompiler入力に渡す0-call試験は、この10件の代替にならない。
解釈出力とgoldのJSON一致をpass gateにしない。保存した幾何・薄い編集可能性・両成果物・終了/時間条件を、凍結人手goldで採点する。
DECISION-01のprotocolをこの経路へ改訂する。5件/10 runs、8/10かつ各1/2、寸法/体積帯、最大3 attempts、900秒は変更しない。

- 対応型のSolソース生成callをCLI compilerへ置換。typed inputなら自然文解釈callも不要。
- 独立planner call、解釈後の同内容のpreview call、抽出対gold一致を判定するcallは設けない。
- compilerの修正call、保存/再読込/環境のAI修正callは設けない。
- LLM judge、失敗classifier、feedback作文、FCStd/STEPレビューのcallsはCLI検査・整形へ置換する。
現在のdriverに存在しないcallも含む「不要にする呼出し」の一覧であり、削減量の実測ではない。
自然文の初回call数は現行の直接source生成と同じ1で、出力を短い仕様へ替える。grok-layeringの「six-part barも0 call」は採用しない。barは5部品の自然文経路である。
compiler/JSON解釈の新経路は未実装・未測定。少ない出力tokenと固定建模を狙うが、速度・成功率の改善はまだ主張しない。

codex: AGREE
grok: AGREE
grok note: six-part・0-callを合格線にする案は取り下げた。DECISION-01は自然文5部品の経路（最小Sol 1 call）。0 callは明示typed inputだけ。
grok note: recipeは型で選ぶ。過学習の確認はDECISION-02の系ごとのheld-out spec。
grok note: LLM judgeは足さない。既存judge_stubは無効のまま。
claude: unavailable (org disabled subscription access, retried 22:25)
