# SolidWorks H0 進捗・再開メモ

## 固定された承認・計画

- ユーザー承認2026-10-26 23:15 JST：H0は開発用40課金呼出し上限、v4本番163枠とは別。23:20 JSTの50回以下バッチの包括承認は記録済みだが、本H0は40のまま。
- `H0_PLAN.md`に、元序数23,24,30..38のspec11題（各最大3）と39..45のask7題（各最大1）、合計18題・最大40呼出しを結果を見る前に記録。残り42行はnot_run、途中入替・余剰枠での追加・別モデル・retakeなし。
- 原本、policy、カード、スキル、合格ライン、元の採点関数は変更しない。親LLMとGitへ封印gold・課題本文・正解CAD・生の判定を出さない。生成器にはその原依頼文、固定スキル、実候補と許可済み観測だけ。候補をgoldから組み立てるM1経路は禁止。

## 完了した準備

- `tools/sw_h0_budget.py`：開発40枠の独立・永続・送信前予約。未完了も枠に残し、構造化・出力なし混雑拒否以外は返却しない。40件未完了で再起動しても41件目を拒否する実テストを含む安全3テストが合格（0.040秒）。本番163枠やそのclaimは使わない。
- `tools/sw_h0_worker.py`：検証済みAI build-specだけを受け取る固定SWワーカー。gold/card等の混入はCOM開始前に拒否。既存M1のSW特徴ビルダー・所有文書ガードを使用。終了・再起動・SWのkillなし。
- attachのみの事前確認に合格。SW PID41448、確認ワーカーPID60772、開始・終了文書数0。モデル呼出し・CAD作成は行わない確認だった。
- `tools/sw_h0_cad.py`：JSONから固定・ハッシュ束縛のSWワーカーラッパーをコンパイルする。モデルのPythonは実行しない。実行したラッパーのハッシュ、worker/独立判定PIDを記録し、元のpassゲートへ事実として対応付ける。
- `tools/sw_h0_verify.py`：新規のFreeCAD 1.1.4プロセスが実STEPを再読込し、元gold幾何判定とM1と同じ全境界0.005mmを再確認する。
- `tools/sw_h0_runtime.py`：原本・カードの既存機械照合、コード/入力/モデル/ホストの固定、5分以内の使用量確認、生成中の55/60%監視、元の600秒同一再送、gold期待値を渡さないrepair観測。
- `tools/sw_h0.py`：元v4/v3の状態機械と採点を再利用するprepare/run/smoke。既存コードは変更せず、独立ロードした状態機械の固定compiler依存だけをSWへ切り替える。公開結果は`tools/sw_h0_report.py`が明示的な状態・時間だけに絞る。
- 公開要約の統合で、入力の序数フィールドを元データの`sequence`へ統一し、未完了を合格扱いしないこと、failure=nullは不正情報に作り替えないことを確認中。null境界の単独回帰は合格。旧文言・書式への固定テストは除いた。

## 現在の実行と次の一手

- 実課金の生成呼出しはまだ0。productionの40枠カウンターも未使用。
- `h0-smoke-01`は、公開G6の旧goldのregionsが空であるため開発用spec構成時に拒否された。モデル・SW作成の前。公開parametersのbboxから開発用矩形regionを定義するよう直し、原本や判定は未変更。
- **`bg_36`で`h0-smoke-02`を実行中。重複起動しない。** 公開の開発用対照だけを使い、誤ったspec→元のR1修復→正しいspecのmock2応答と、実SW/実SDKの往復を確認する。ライブモデル呼出し0、専用mock-poolを使用し、本番の40枠を消費しない。
- 次は自動完了通知を受け、公開`reports/sw-h0/h0-smoke-02/summary.json`だけを確認する。非公開フォルダやrawログ、inputs-private、gold、実課題本文は親LLMから開かない。失敗時は固定診断のクラス・ソース行等の公開可能な情報だけで原因を特定する。
- smokeが通った後に既存回帰と新規7テストを一括確認し、コード/計画/公開証拠をローカルcommit。その後だけ新規の本番用prepare（manifest/SHA256固定）とrunへ進む。prepareはまだ行っていない。runでは送信前に使用量とSW文書0を再確認する。
- 55%で止まってASK、60%で停止。古い/不正/欠損snapshotやホスト・キャプチャ異常でも停止。SWが無反応ならPythonクライアントだけを止め、SWは再起動しない。状態不明なら所有セッションロックを残す。

## 進捗ダッシュボードの制限

- 規則に従って専用dashboard-builderへ作成を依頼したが、専用dashboard_storeが「指定されたモデル・effortではありません。」と拒否し、既存HTMLを読めず保存もできなかった。別モデルや別手段へ黙って切り替えていない。Serve・公開設定・外部ファイルを変更していない。
- 進捗原本はこのメモ。ダッシュボードの利用不能はCAD本体の許可・安全ゲートを緩める理由にしない。H0準備を継続する。

## 課金前の実動作確認完了

- `h0-smoke-02`はPASS。公開対照だけでmock応答2回、実SW/CAD2試行、誤仕様拒否、元のR1修復1回、正しい候補のnative保存再オープン・編集復元・新規SDKでの再読込を確認。84.281秒、実モデル0回。
- 複数課題で同じattempt IDが集計上衝突しないよう、共有journalからrun内で一意のIDを採る。専用回帰で2課題の呼出しが両方原ledgerの集計へ残ることを確認した。CADの論理stdout/stderrと実サブプロセスの全raw captureもハッシュ付きで束縛する。
- 最終`h0-smoke-03`もPASS。mock応答2、実CAD2、誤仕様拒否、R1修復1、欠損なしのtransport capture8本、79.109秒。productionの40枠は未使用で、実モデル0回。公開証拠は`reports/sw-h0/h0-smoke-03/summary.json`。
- 既存SW安全・M1機密性等を含むホスト15テストが合格（0.211秒）。既存FreeCAD 1.1.4実体の偏差・穴・旧gold変換6テストも合格（2.370秒）、計21件。新規回帰は55%/60%停止、入力改変の停止、gold期待値をrepair payloadへ渡さないことを含む。
- 実使用量の再確認：observed `2026-10-26T15:17:42.410Z`、checked `2026-10-26T15:18:35.294896Z`、1%、age52.885秒、allow。各送信前と長い生成中にも再確認するため、この履歴値で後の呼出しを許可しない。
- 次の一手：新規H0コード・計画・このメモ・公開mock証拠だけをローカルcommit。その後 `python -B tools/sw_h0.py prepare --run h0-20261027-001` で新規版を固定し、固定成功後のみ `python -B tools/sw_h0.py run --run h0-20261027-001`。どちらもSW専用venvから、worktree `C:/dev/CAD-HARNESS-sw`で実行する。実課題の生成はまだ開始していない。

## 本番用固定が完了・次は1回だけrun

- 実装checkpointはローカルcommit `3934862`。prepare `h0-20261027-001`が成功。まだ実課題のモデル呼出しは行っていない。
- manifest SHA256は`72a617445e72d09adcc43fcb0fbb583bc0acdfd695a5bf7d1d432aeae548f8c4`。モデルは`openai-codex/gpt-6.1-sol`、xhigh、CLI `omp/18.11.2`、固定した18題、別枠上限40。公開manifestは`reports/sw-h0/h0-20261027-001/manifest-public.json`。
- 正確な次のコマンド：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h0.py run --run h0-20261027-001`（cwd=`C:/dev/CAD-HARNESS-sw`）。runは新規claim・送信前使用量・SW文書0の確認を通過してから生成する。重複起動・再prepare・ソース修正・再実行をしない。

## H0本番バッチ実行中：重複起動禁止

- 上記runコマンドを **`bg_41`** として開始済み。自動完了通知を待つ。開始前の実モデル呼出しは0で、実行中の件数はまだ集計していない。40上限は送信前の永続予約と各カードの元上限で機械的に守る。
- 固定ソース・policy・カード・スキル・H0_PLAN・入力packetを実行中に変更しない。途中成績による再選択・再実行・修正・新規課題追加をしない。親LLMは非公開出力を開かない。
- 公開結果の予定先：`reports/sw-h0/h0-20261027-001/{row-NNN,rows,summary}.json`。完了通知後にこれらの公開状態だけを読み、`H0_SUMMARY.md`とこのメモを更新し、h2/swだけへcommit・pushする。
- 停止時は理由、実行済み序数、40枠の予約数、未着手行を保存して報告する。55%ならASK、60%なら停止。SW状態不明ならセッションロックを維持してユーザーへ報告し、終了・再起動・勝手な復旧はしない。成功・停止のどちらでも次段階を始めず待機する。

## 001終了・起動設定の最小修正

- `bg_41`は終了済み。18題ともCLI exit1、stdout0バイト、stderr117バイト（全件同一SHA256 `d8d7daf7010833a83f7d4a6015683a1589b5ef1b6a7c141a1456ca9039dec457`）。モデル最終回答0、CAD試行0。33.656秒。公開の元採点0/18は保持するが、モデル能力評価として成立していない起動失敗であり、CAD不正解18件とは呼ばない。
- 40枠の永続予約は18件を消費扱いのまま保持し、残り22。実請求・トークンは不明。出力なしでも構造化混雑拒否ではないため、1件も返却しない。001のclaim・行・ledgerは再実行や書換えをしない。
- 読み取り専用のCLI設定確認で、既定のCodex providerがdisabled、enabled provider/modelがopencode-go/DeepSeekになっていた。local catalogには承認されたCodexモデルが存在する。raw stderrや原問題・goldは親LLMから開いていない。固定診断は既知の`provider`/`disabled`分類とサイズ・ハッシュだけを公開した。
- 修正はH0の一時overlayだけを承認済みCodexモデルに限定し、起動失敗で次の題へ進まないこと。既定設定・auth・権限・元v4ファイルは変更しない。設定確認用`omp config get ... --config ...`はそのsubcommandで未対応として拒否された。生成はしていない。
- `H0_PLAN.md`に002の送信前計画を追加済み。同じ18題・同じ順序で、共有枠の残り22以内だけを使う。新しいソース固定の前にテストと無課金smokeを行う。まだ002はprepare/runしていない。

## 002前の検証

- H0一時overlayを独立ロードのtransportへだけ固定し、公開manifestにprovider/modelの限定と設定ハッシュを追加した。CLI exit非0または最終応答なしはバッチ停止理由`H0_model_launch_or_response_failure`とする。既存v4 sourceやグローバル設定は変更していない。
- 成功2送信の後に起動拒否1送信を起こす回帰で、3件すべてが同じ会計に残り、拒否がfatalとして呼出し元へ伝わり、6本のstdout/stderrを保存することを確認。既存も含むホスト15テストPASS（0.220秒）、SDKの既存実形状6テストPASS（0.648秒）。
- `bg_42`で`h0-smoke-04`を実行中。公開開発対照のmock応答と実SW/SDKのみ。実モデル送信は増やしていない。自動完了後に公開結果を確認してからソースをcommitし、新規002をprepareする。

## Handoff — 安全停止、SW確認待ち

- `bg_42`は終了済み。`h0-smoke-04`はFAIL、300.094秒、`H0_CAD_backend_stopped`。mock応答1、最終CAD結果0、R1修復0、保存transport stream2。新しい実モデル送信は0。SW経路の状態不明として、以後COM確認・文書操作・生成を行っていない。SW終了・再起動・SLDWORKS.exe killは禁止を維持した。
- 所有セッションlockを意図的に保持。タイムアウト処理は所有Pythonクライアントだけを停止する実装で、共有SWは停止しない。最後に確認済みのSW PIDは41448（現在の応答状態は未確認）。非公開証拠は`reports/sw-m0/m1-private/h0/h0-smoke-04/`、公開停止証拠は`reports/sw-h0/h0-smoke-04/summary.json`。
- 実装済み：H0固定spec→SW→旧判定の経路、40枠永続予約、quota55/60監視、oracleを漏らさないrepair、公開projection。修正済みだが実SW再検証未完：Codex専用一時overlay、CLI起動失敗fail-fast、設定ハッシュのmanifest記録。旧v4コード・policy・カード・採点・gold・グローバルprovider設定・auth・権限は変更していない。
- 最新の検証はホスト15 PASS（0.220秒）、SDK実形状6 PASS（0.648秒）、修正後SW smoke FAIL。以前のsmoke02/03のPASSを今回の成功に代用しない。002はprepareもrunも未実施。001の18予約を保持し、上限40に対して残り22、請求実績は不明。
- 今回の追加/変更ファイル：`H0_PLAN.md`、`H0_PROGRESS.md`、`H0_SUMMARY.md`、`tools/sw_h0_runtime.py`、`tools/test_sw_h0.py`、`tools/sw_h0_diagnose.py`、公開001結果とsmoke04結果。元M0/M1/v4実装や保護refは変更していない。保護refの確認値はherdr/v4とv4-freecad-final=`5f96e2f…`、tag v4-freecad-57of60=`0f545110…`、h2/mvp=`3ac25c8…`、作業branch=h2/sw。
- 残件順序：①ユーザーがSWの応答とハーネス文書状態を確認（終了・再起動で回避しない）②確認後に所有lockの安全性を判断し、無課金smokeを再検証③成功後だけ新規002を固定④同じ18題・順序を共有残り22以内で実施⑤公開集計・commit/push。
- **次のコマンドはまだ実行禁止**。ユーザー確認と所有lockの安全確認後の候補は、cwd=`C:/dev/CAD-HARNESS-sw`で `C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h0.py smoke --run h0-smoke-05`。今は停止を記録してh2/swへcommit・pushするだけで、その後待機する。
