# DECISION-02 — CAD-HARNESS MVP architecture

2026-10-11 layering改訂：22:44 JSTのユーザー原則とDECISION-03(b)を反映。自然文→短いspec→CLI compilerを主経路にする。
DECISION-01の5部品と合格barは保持。Codexは合意、grok署名待ち。コード・skill・gold・設定は変更せず、FreeCAD/Solも実行しない。

## 入力・実行mode・別context

- description mode: user payloadは元JA/EN説明だけ。Solは短いbuild_specを返し、CLIが検証・建模する。範囲外は元説明からSol build(doc)へfallbackする。
- typed mode: ユーザーのtyped JSON/formをCLIだけで読む。自然文解釈は不要。agent modeは明示選択した範囲外のソース生成入口とする。
- 全LLM callsのuser payloadは初回も修復も同じ元入力とSHA。skill、schema、出力契約、直前spec/source、predicate_detailsは別contextへ渡す。
- driverがskills/freecad-modeling/SKILL.mdを読む。外部新規cwd・tools/plugins無効なので自動発見に依存しない。
- ローカルcodex-cli 0.159.2のexec --helpで専用system-messageフラグがないこと、-c key=valueがTOML、[PROMPT]が引数/stdinであることを確認済み。
- per-callの-c developer_instructions=<正しくTOMLエンコードした文字列>を採用。追加developer contextという意味は[OpenAI Docs Configuration Reference](https://learn.chatgpt.com/docs/config-file/config-reference)で確認した。
- argv配列・shell=False・stdin=DEVNULLで元説明を渡す。JSON文字列をshell escapingに流用しない。引用符/改行/バックスラッシュ/日本語をTOML round-tripで検証する。
- gpt-6.1-sol/xhigh、既存10個の--disable、read-only、skip-git-repo-check、外部新規cwd、--json/-oを維持。CODEX_HOME・共通AGENTS・config.tomlは変えない。
- 修復contextはCLIがskill/出力契約とデータを分けて組む。生成物や診断を規約へ昇格させず、説明・gold・許容を変えない。
- description/skill/context/schema/compiler/Probe/goldの版とSHA、CLI版、モデル設定、継承AGENTSの識別を記録する。
- model_instructions_fileはbuilt-in instructionsを置換するので使わない。argv長/未対応設定はharness停止。promptへ規約を混ぜる迂回は行わない。
- 実注入は未検証。実装時の契約確認までは対応済みと主張しない。

## skillとCLIの所有範囲

skills/freecad-modeling/SKILL.mdは次の一般的判断の指針を持つ。task専用寸法・gold・fixture・解答ソースは入れない。

1. Scopeと入力解釈: 径/半径、穴間隔/総長、座標/加工対象、未指定/曖昧さを区別し、要求を追加・省略しない。
2. native編集の作法: BodyとSketch/featureを有効に結び、主要寸法が編集に使える構成を選ぶ。
3. agentの構築戦略: Pad/Pocket/Revolution、穴列Pattern、指定辺Fillet/Chamferを目的に応じて選ぶ。Partは幾何補助として使う。
4. 依存関係の作法: Profile/支持先/BaseFeature/所属/Tipを整合させる。FlatFace、単純押出の設定、仕上げを後段に置くことを推奨する。
5. 加工対象の選び方: 固定Edge/Face番号に頼らず位置・方向で選び、追加加工/UseAllEdgesを避ける。
6. 修復の判断: 失敗したexpected/actualから未確認specまたはsourceを直す。harness環境やcompilerの変更は引き受けない。
CLI/schemaはmm・既定XY中心/底Z=0、許可型・数値条件、JSON/source出力契約、attempt/時間、export/Probeを所有する。
出力契約はskill本文に埋めずCLIの別contextへ入れる。解釈はJSONだけ、agentはbuild(doc)を定義しBodyを返すsourceだけ。
agent契約の許可モジュールはFreeCAD/Part/Sketcher/math。文書作成・起動・保存・close・ファイル/ネット操作はharness側に限定する。
建模作法のうち薄い編集可能性だけがpass gate。幾何/成果物/時間等のgateも維持する。FlatFace・厳密なfeature順序/個数/連鎖はCLIのskill_warningsとし、修復を起動しない。

## build_spec・compiler・人手gold

- 新tools/cad_spec.pyはJSON/form読取、schema検証、換算・座標展開、固定recipe選択、build(doc)生成を担当する。
- build-schema.jsonは版/units/frameと、矩形押出領域、同軸段の径/区間、矩形pocket、円形通し穴、指定上面外周のR/Cを持つ。
- 自由コード/式、feature graph、期待体積/pass宣言は入力にしない。有限値・正寸法・一意ID・enum・既知の接続/干渉条件を検査する。未知field/重複keyも黙って捨てない。
- compilerは対応型ごとのSketch拘束・native featureを作る。矩形領域のPad、同軸円ProfileのPad、切除Pocket、対象辺仕上げを固定手順で組む。
- 部品名/説明SHAでrecipeを選ばない。P1–P5の解答表にせず、同じ型の寸法変更にも使える範囲をschemaで明示する。未対応条件はunsupported。
- evalのbuild_specはSol出力。goldとは別に保存・SHA記録する。goldの値をcompiler/初回Solへ渡さず、spec対goldの一致gateも作らない。
- typed modeの不正specはCLI拒否。descriptionの不正JSON/specはcallを消費して修復可。compiler例外/native構成不良は人へ返す。
- 自然文のunsupportedはSol sourceへfallback可。最初の解釈callも残り予算に含む。同じspecを再出力した修復は再CADせず停止する。
- 人手goldはDECISION-01の正確な入力・寸法・式と照合してレビュー/凍結する。生成側が期待値を更新しない。

| gold schema v1の項目 | 内容 |
| --- | --- |
| schema/case_id/description | 版、P1–P5、正確な文字列とUTF-8 SHA |
| units/frame/tolerances | mm、absolute/P1相対枠、linear=0.01 mm、axis=1e−6、volume_relative=1e−4、P1例外帯 |
| bbox/volume/provenance | 境界、凍結target/帯/上限、表示用導出式、人手確認、P1引用実測、版/SHA |
| regions/sections/steps | 底板/壁/矩形断面、段の径/区間/肩面 |
| holes/pockets/fillets/chamfers | 中心/軸/径/区間/開口、矩形/底/深さ/鋭い縁、対象の幾何役割とR/等脚C |
| editability | native、有効Profile/Tip、主要寸法の役割。固定ラベルやfeature個数は要求しない |

goldは生成用schemaと別用途/別ファイル。導出式は表示用でevalせず、数値targetを凍結する。gold読取も型/有限値/版/SHAを検査する。

## generic Probeと独立した採点

- 新tools/cad_spec_probe.pyがmvp-v1を担当。probe_profile/gold SHAをtask/attempt/source SHA/PIDへ結び、未対応predicateは黙って省略しない。
- P1/P2のcase名分岐ではなく幾何型別に、実BRepのvalid solid=1、bbox/配置/体積、矩形断面、同軸段の径/区間/肩を測る。
- 穴は同軸の分割円筒面を集約して個数/径/中心/軸/区間を測り、両端開口と孔内空隙も検査する。面数だけで穴数を決めない。
- pocketは開口・壁・底・深さ・鋭い内縁、仕上げは実際のR/等脚C・45度・対象位置を検査する。sourceの数値/feature名だけで合格にしない。
- 編集gateは単一Body、実在Sketch、検査solidを持つnative Tip、有効Profileリンク、使われる主要寸法の拘束/feature props、clean recompute。
- geometry/editability/artifact/運用条件とskill_warningsを別出力にする。参照solid/対称差は追加しない。必須測定nullは不合格。
- 採点器はLLMやcompilerの自己評価を使わない。suiteの期待は人手gold、実測は保存成果物、合否は固定predicateとする。

## CLI分類とpredicate_details

- feedback-change.mdの診断構造だけ再利用する。旧B v2のuser promptへの構築要件追加は再開しない。
- 既存7診断項目にversion=1/task_id/checks/truncated/omittedを追加。各失敗はpredicate/sub_check_id/expected/actual/許容/欠落理由を持つ。
- 同じ比較値をProbe→worker→cad_run→driver→別contextへ伝える。失敗下位条件だけ、未取得null、役割/型/順序ID、個人パス/ラベル/自由文traceなし。
- JSON全体8192 UTF-8 bytes、最大32件、expected/actual各256 bytes。失敗predicateごと最低1件を優先し、超過はレコード単位で省略する。
- legacy厳密履歴の診断を増やしても旧合否式は不変。mvp-v1のwarningだけでattemptを消費させない。
- CLIのrepair_reasonが、parse/spec不良、settledなagent build/probe不良を修復対象とし、compiler/起動/保存/再読込/Probe例外/cleanup不良を人へ戻す。
- compiled形状のgold不一致だけではspec/recipeの根本原因は確定しない。descriptionの未確認specなら幾何診断から解釈を修復できる。確認済みtyped specは自動変更しない。
- 全mode/fallback共通でSol最大3 calls、cad_run最大3建模attempts。parse失敗もcallを消費し、最大900秒は解釈から回収までの単調時計で計測する。

## FCStd・STEPと別process再検証

- workerで候補を検査し、harnessがmodel.FCStdをnative履歴付き、model.stepを同じ最終Tipのsolidだけとして新attempt出力先へ保存する。
- build workerをclose/回収してから、新freecadcmdのtools/cad_verify_freecad.pyで両成果物を読む。build/source/compilerを読み込まず実行しない。
- FCStdはrecompute後の幾何+編集gate、STEPは別文書へimportして単一valid solid+同じgold幾何を検査する。
- 両成果物world bbox±0.01 mm・体積相対差1e−4も比較する。P1の位置自由/体積例外帯は保存変化を許す例外にしない。
- artifact/gold/source/spec SHA、task/attempt/worker PIDを親が照合し、reimport合格・document_closed・所有PID終了後だけrun成功。
- 建模/検証freecadcmdは各300秒を残り時間でclip。LLM/compile/export/reimport/回収を同じ900秒へ含める。
- legacy timings_ms/worker_tsと第一失敗を保持し、新export/verificationの実測を追加項目に分ける。失敗成果物を成功納品にしない。

## 評価と実運用

DECISION-01はdescription modeの固定5説明×2 fresh runsを測る。主経路はSol解釈→CLI compile、unsupported時のagent fallbackも総予算内。
typed/goldを直接compileした0-call runはこの評価に含めない。JSON一致gate・独立planner・preview/LLM judge callsは設けない。
実運用では解釈出力のCLI整形要約をユーザーが確認してspecを凍結する。同じ解釈を再利用し、previewのための別Sol callは要らない。
確認待ちは評価suiteに入れず、productionではpreview/待ち/build時間を区別して記録する。同じモデルの別callを意味解釈の独立性とは扱わない。

## A/B回帰と最小の実装順・試験

legacy A/Bのprompt/Probe/許容/fixture/集計、終了コード・第一失敗・stop規約、measure_rollout.pyを保持する。
A初回SHAはea2008c9dfdb3d1c9ff732dd5c373fd431064d53744e01db9cad8921e32cc641。MVPを旧A/BやB v2=N3の集計へ混ぜない。

1. context/mode/call budget/deadline。既存mockで入力不変、TOML、fallback合計3、900秒/300秒clip、legacy SHAを確認する。
2. build schema/compiler。5件に必要な型だけ実装し、typed modeでSolなしのfixtureを作る。寸法変更の代表1件でcase lookupでないことを確認する。
3. 凍結5 goldとgeneric Probe/薄い編集gate。誤径/盲穴/加工対象違い/編集不可/skill warningの代表例でhard failとwarningを確認する。
4. predicate_details伝播とrule-based分類。既存比較の合否不変、null、UTF-8上限/省略、compiler停止/解釈修復を必要な契約試験で確認する。
5. exportと独立reimport。新出力でlegacy A/B good+broken計4件、MVP typedの5件でgold/native/成果物をsmoke確認。旧fixturesは変更しない。
6. 凍結版で自然文P1/P2/P4/P5/P3を各2回。typed smokeをwarm-up/代替にせず、追加A Sol回帰も行わない。全10件で8/10+各1/2を判定する。
修正後は新版の全10件を別集計する。weekly使用60%で停止し、未完了は未達。計画外の機能/広範な試験は増やさない。

## 合意後に触るファイル

| file | 最小の責務 |
| --- | --- |
| skills/freecad-modeling/SKILL.md（新規） | 解釈・建模判断の一般規約 |
| tools/cad_agent.py | mode、別context、interpret/source/repair、共通budget、MVP新集計。legacy入口を保持 |
| tools/cad_spec.py（新規） | typed検証/数値展開/型別compiler。gold期待値を入力にしない |
| tools/cad_run.py / tools/cad_run_freecad.py | profile/版照合、launch/cleanup、Probe選択、export/検証起動 |
| tools/cad_spec_probe.py / tools/cad_verify_freecad.py（新規） | 人手gold比較、薄い編集gate、buildなし再読込 |
| tools/cad_run_probes.py | legacy診断の分解だけ。旧合否/値/許容は不変 |
| design/cad-harness-mvp/build-schema.json（新規） | 生成用の型/既定値/対応範囲。task別goldなし |
| design/cad-harness-mvp/eval-v1/schema.json、P1.json〜P5.json（新規） | 人手goldと正確な説明、出典/許容/凍結版 |
| tools/fixtures/cad_mvp_build.py（新規） | compilerのtyped smokeと必要な誤形状。旧fixtureと分離 |
| tools/test_cad_agent.py / tools/test_cad_run.py | 上記の必要な契約・失敗経路のみ |
| reports/cad-run/新run / reports/新MVP集計 | 実行後の全件実測。既存reportsを上書きしない |

本draftでは実装ファイルは未変更。compilerの成功・速度・新しい合格率は未測定である。

codex: AGREE
grok: AGREE
grok note: 過学習防止はrecipe系ごとに、P1–P5のgoldに無い寸法のtyped specを1件ずつ通す。compiler試験はeval-v1と説明SHAを読まない。5形状だけ合格では汎用性の証拠にしない。
grok note: step 5のlegacy A/Bとtyped smokeが通るまでstep 6のSol 10件を始めない。
grok note: 修復診断のexpectedはgold由来であり得る。compiler入力と初回Solのcontextにgoldを入れない、は維持する。
claude: unavailable (org disabled subscription access, retried 22:25)
