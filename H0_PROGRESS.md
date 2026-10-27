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

## 公開保存完了・待機

- WIP/未ロックの停止checkpoint `17ada38`を`origin/h2/sw`へpush成功（remote `7d049b2..17ada38`）。非公開gold・raw出力・`__pycache__`は含めていない。この停止記録の追記も同branchへ保存する。
- 最終状態：**STOPPED、SW応答とハーネス文書状態のユーザー確認待ち**。002未固定・未実行、40枠の保守計上18・残22、55%ASK/60%停止は不変。公開コード修正の単体回帰21件は合格したが、無課金SW smokeは300.094秒で停止しており、再開許可や成功証明の代わりにはしない。稼働中jobなし。SW終了・再起動・保護branch/tag変更なし。新しい手順・生成は始めず待機する。

## 2026-10-28 再開許可・更新後SWの再確認

- 監督01:25 JSTの指示で再開。監督報告では10/27 00:42 JSTのGPU TDR後に旧SWが無応答となり、ユーザー操作で10/28 00:21 JSTに強制終了、仮想画面を導入、SW更新後01:20 JSTに起動された。親エージェントはSWを終了・再起動していない。監督の読み取り確認はPID28800、Responding=True、Revision34.4.0（旧34.3.0）、文書0。TDRと旧timeoutの因果は未確定。
- 保存lockの内容は`H0-unit-mock-smoke`で、前回smoke04由来。監督が旧所有者不在と新SWの空セッションを確認し、明示的にrenameを指示したため、`reports/sw-m0/session.lock.stale-20261027`へ削除せず退避する。その後は既存のattach-only/文書0ゲートを再度通して無課金M0確認を行う。
- 新規許可：課金バッチの起動失敗はCodexサブスク内・各50回以下で原因修正と再試行可。dev40終了後も新しい50回以下の別枠へ続行可。まず002は既存共有残22以内。55%ASK/60%停止、SW無応答停止・終了再起動禁止、gold機械参照のみ、元カード0.01mmと追加0.005mm判定・policy・採点は不変。同時稼働Codexは2以下に抑える。
- 次の順序は無課金M0→無課金smoke05→両方成功後だけ新規002固定・実行。失敗は保存し、SW無応答以外なら自分で調査・修正・再確認する。まだ追加のモデル生成なし。
- ダッシュボード専用agentへ更新を依頼したが、専用toolが再び「指定されたモデル・effortではありません。」と拒否した。別モデルへの変更や代替公開は行わず、このメモを原本として継続する。AGENTS共通inventoryは検出0・走査エラー0。

## 再開M0の障害調査・01:31の追加許可

- `m0-resume-20261028-01`は29.150秒でFAIL。SW34.4.0/PID28800へattachし、正例の作成・保存・再オープン・寸法変更復元までは記録されたが、負例の新規スケッチで`CreateCornerRectangle`が4.216秒かかった直後、`InsertSketch`でRPC unavailable（HRESULT -2147023174）。COM状態不明を記録し、所有lockを残して終了した。M0全体合格ではない。以降の読取確認でSLDWORKSプロセス数0。親がSWを終了するAPIやkillを使った事実はない。
- 保存済み正例STEPだけをオフラインの既存FreeCAD1.1.4判定へ渡した結果、保存前・再読込・復元の3形状は元0.01mmと追加0.005mmで合格、再読込/復元の差分体積0。これは部分確認のみで、未作成の負例やH0 smokeを代替しない。証拠`m0-resume-20261028-01/partial-neutral-result.json`。
- Windows ApplicationログはViewServerV6.exe18.0.0.749自身でアクセス違反0xc0000005、offset0x20380、01:26:42 JST、report ID `e5ed3340-5e45-42e8-bcc8-5e964dffaff4`を記録。SLDWORKS本体の一致する1000/1001記録は未発見。監督報告では新規TDRなし。GPU・仮想画面・新SP4.0・ViewServerのどれが根本原因かは、この時間相関だけでは確定しない。判定コードの変更や許容差緩和で回避しない。
- 01:30の委任に従い、安全な選択を自分で決める。現時点の選択は元のハーネスのまま再検証し、同じ障害が再現した場合だけ原因を切り分ける。H0終了後はスキル記述だけの改善を元版と交互に各5回比較する準備へ進む。封印goldから改善内容を作らない。
- 01:31の新規許可：SWがクラッシュ等で**存在しない時だけ**自分で起動可。稼働中SWの終了・再起動は引き続き禁止。上記調査を先に保存したので、プロセス不在を起動コマンド内でも確認してから、登録済みSLDWORKS.exeを通常起動する。PID14540（今回lock所有者）は既に存在しない。新lockの排他アクセスを確認してから`session.lock.stale-20261028-012610`へrenameする。追加ライブ生成0、既存40枠は18計上/22残のまま。

## 許可後の起動結果・安全な継続先

- 新lockはPID14540不在に加え、FileShare.Noneの排他open成功を確認後、`session.lock.stale-20261028-012610`へrenameした。旧`session.lock.stale-20261027`も保持。どちらも削除していない。
- 起動直前にもSLDWORKS不在を確認する条件付きコマンドで、COM登録のLocalServer32にあるSLDWORKS.exeを起動。新PID8536。90秒の読取専用COM準備確認はcom_errorで未成立。OSはResponding=Trueだが、Orcaの実画面は「レジストリのロード中…」のsplashのみで、操作可能な本体や別ダイアログは見つかっていない。起動完了とは扱わず、M0再投入・smoke05・002生成はまだ行わない。
- インストール済み公式ショートカットは直のexeではなくCATSTART→SWXDesktopLauncher（3DEXPERIENCE環境）だった。直接起動との環境差が今回の起動待ちに関係する可能性があるが未確定。新PIDが既に存在するため、終了・kill・二重起動・再起動で回避しない。次に起動可能な不在状態では公式ショートカット経路を選ぶ。
- 現在は新たな課金なし。基準を変えない既存判定で正例の保存STEP部分を確認できたが、M0全体・H0実動作成立の条件は満たしていない。SWを不要とする予算管理と、H0後のスキル記述のみ交互各5回比較の準備を先に進める。COM投入は起動完了を確認できるまで行わない。

## 無課金で進めた実装と検証

- 追加バッチは委任の範囲内でも既存と同じ40上限に決定（50以下）。`sw_h0_budget.Pool`に独立scopeを追加し、元development40はそのまま保持。新scopeで40予約後の41件目拒否、別scopeで再openした場合の拒否と正常なlock解放、旧poolの残高不変を確認した。
- `sw_h0_runtime.freeze`/`sw_h0.py`はmanifest v2にpool名・scope・元順序の選択を束縛。通常prepareは従来dev40、`--new-batch`は新しい40枠。`--sequences`は当初18題内の元順序だけ。CLIの重複指定23,23は原本読取前に拒否（exit2）。manifestの新batchを既存dev40へ付け替えてSHAを再作成しても拒否する回帰を追加した。コードは新claim前の変更であり、実行中の固定版を変更していない。
- 最新ホスト17テストPASS（0.351秒）、SDK実形状6テストPASS（4.156秒）、計23。新しいテスト中の合成manifestを書き換えるfixture helperでexclusive-createエラーが1回あり、fixtureの明示的なtamper操作へ直して17件すべて合格。実判定・閾値の変更はない。
- 実動作の予算smokeは実モデル0。元poolを前後に読み取り、18計上/22残が不変であることを確認。別の一時poolで合成40予約・41拒否。証拠`reports/sw-h0/budget-resume-20261028.json`。一時poolは削除済みで、本当の課金予約ではない。元private資料のGit除外も確認した。
- H0後の計画を`H2_SKILL_PLAN.md`に保存。元方針の新課題・30–70%難易度・交互各5回・新しい封印ホールドアウトを維持し、original60を改善に使わない。説明文以外は同一に固定する。採用差・cache整合幅・新規最終題数は、委任に基づく事前の安全側の設計値として区別し、実測と表示しない。比較生成・新課題作成は未実施。

## Handoff — 10/28、SW起動待ち以外の到達可能作業を保存

- SW PID8536は最後の実画面確認でもsplashのみ、読取専用COMはMK_E_UNAVAILABLE（-2147221021）。稼働中を終了・kill・再起動しない規則のため、公式ランチャーへ強制切替していない。ハーネスPython/課金生成の実行jobなし。Orcaは画面読取用に起動しただけで、他のCAD・文書を操作していない。
- 001は保持。002未固定・未実行、smoke05未実行、H0有効成績は未成立。今回ライブ生成0、元pool18計上/22残。利用率55%ASK/60%停止・古いsnapshot停止は変更なし。源gold・原要求・raw生成は開いておらず、Gitへも含めない。
- 変更ファイル：`tools/sw_h0_budget.py`、`tools/sw_h0_runtime.py`、`tools/sw_h0.py`、`tools/test_sw_h0.py`、`H0_PLAN.md`、`H0_PROGRESS.md`、`H0_SUMMARY.md`、`H2_SKILL_PLAN.md`、公開resume/budget証拠、公開独立M0の`m0-resume-20261028-01/`、rename保存lock2本。元M0/M1/v4実装・カード・policy・skill本文・共用SDK/ACL/registry設定は変更なし。
- 残件順序：①起動中SWを終了せず、起動完了が得られるか確認。現在の起動待ちを安全に解消できない場合は稼働中SWの終了禁止が阻害条件。プロセスが自然に不在になった場合だけ、公式`SOLIDWORKS Design.lnk`経路から起動可。②COM準備・文書0確認後、M0を新規出力で再実行③成功後smoke05④成功後002固定・実行（旧残22）⑤必要な残題だけ新規独立40枠で継続⑥H0集計⑦新しい独立データで説明文のみ各5回比較。
- 正確な次のCADコマンド（**COM準備後だけ**）：cwd=`C:/dev/CAD-HARNESS-sw`で `C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_m0.py --out reports/sw-m0/m0-resume-20261028-02`。その後 `.../python.exe -B tools/sw_h0.py smoke --run h0-smoke-05`。両方成功後だけ `.../python.exe -B tools/sw_h0.py prepare --run h0-20261027-002` → `.../python.exe -B tools/sw_h0.py run --run h0-20261027-002`。生成中にsourceやplanを直さない。
- 保護refの保存前ゲートは不変：herdr/v4・v4-freecad-final=`5f96e2f…`、tag=`0f545110…`、h2/mvp=`3ac25c8…`。現在branch=h2/sw。ここまでをWIP/未ロックcheckpointとしてcommit・pushする。停止理由と先へ進む条件は公開resume JSONと要約にも記録済み。

## 起動状態変化：M0再実行中

- 保存直前の安全ゲートでCOM取得の状態が変化。readiness用の一時コードがCOM method/propertyの違いでTypeErrorになったため、既存Session.callと同様にcallableを区別して読み直したところ、**PID25504、Revision34.4.0、文書0、COM ready**を確認した。PID8536の準備成功とは扱わず、新しい取得先を記録する。親は最初の8536以降にSWの起動・終了・再起動コマンドを実行していない。
- OSの読取ではPID25504にSP4.0の主画面、別PID53084に空タイトルがあった。別PIDの出現経路は親から未確認で、これを終了したり文書を操作したりしていない。ハーネスは取得済みのappと自作文書だけに限定する。
- COM文書0を確認後、無変更のM0を新しい出力`m0-resume-20261028-02`で**bg_47**として開始済み。重複起動せず完了通知を待つ。モデル呼出し0。成功後だけsmoke05へ進む。前節のPID8536起動待ちによる停止予定はこの状態変化により保留し、作業を継続する。

## 同じAPI境界での再発・描画経路の切分け

- `bg_47`のM0-02もFAIL、14.677秒。PID25504/34.4.0へ文書0でattachし、今回は最初の箱の`CreateCornerRectangle`が7.018秒の後、直後の`InsertSketch`がRPC unavailableとなった。負例や寸法復元だけが原因ではない。同じbulk rectangle APIの境界で再発したため、呼出し直後の描画・marshalling・SP4.0連携を区別する必要がある。新たなSW/ViewServer一致Application eventはこの回の検索では得られておらず、原因確定はしない。
- 主画面PID25504は消失し、残っていたPID53084は後の正しいFlagAsMethodでの読取でCOM ready、34.4.0、文書0を確認した。親はこのPIDの起動・終了を行っていない。既存の稼働プロセスをそのまま使い、再起動しない。
- 切分けの次の一条件は**自作モデルのIModelView.EnableGraphicsUpdateだけFalse**。元のfixture・CreateCornerRectangle・native編集復元・負例・中立判定をそのまま実行する独立診断`tools/sw_m0_render_probe.py`を追加した。公式APIのview-refresh制御であり、registry・アプリ全体・ドライバ設定は変更しない。各自作文書のviewだけを変更し、viewが閉じられるまでの範囲。設定値の読戻しを必須とし、未知状態なら所有lockを保持する。参照：https://help.solidworks.com/2020/english/api/sldworksapi/solidworks.interop.sldworks~solidworks.interop.sldworks.imodelview~enablegraphicsupdate.html
- M0-02のlock所有者PID29476は不在、排他open成功を確認した。先にこの理由を保存し、`session.lock.stale-20261028-020029`へrenameした後、COM文書0確認済みの既存appで無課金描画分離M0を実行する。これが通っても元の判定を緩めたものとはしない。さらにAPIや描画条件を同時に変えない。

## 描画分離M0成功・共通処理へ最小反映

- `bg_49`はPASS（ツール壁時計14.51秒）。PID53084/34.4.0、文書0→0、COM状態既知。元の全M0 native保存再読込・寸法変更復元・誤仕様対照と、無変更のFreeCAD1.1.4/OCCT7.8.1判定が全合格。元カード0.01mmと追加0.005mmもそのまま。実モデル0。
- これは自作viewの描画停止を有効な回避候補として実証したもので、GPUドライバ・仮想画面・SP4.0・ViewServerのうち1つを根本原因と確定したものではない。以前の2失敗と今回の成功はSW PIDが異なることも残す。
- 共通の`sw_m0.Session.adopt`へ同じowned-view設定と読戻しを最小反映した。M1/H0もこの採用処理を使うため、別の回避経路やspec特例は作らない。view設定中のCOM例外は状態不明として隔離し、追加呼出しをしない。geometry・fixture・gold・中立判定は未変更。
- 診断専用toolsの重複実装は切替後に除去し、成功時の正確なソースbytesを`reports/sw-m0/m0-render-off-20261028-01/render-probe-source.py`へ証拠として移動保存した（元tools位置・旧base hashで実行した歴史資料であり、現位置から直接再実行するCLIではない）。
- 共通処理へ反映した標準M0を`m0-resume-20261028-03`で **bg_50** として実行中。重複起動しない。成功後は同じ共通処理を使うsmoke05を実行し、native/API回避の有無を同じ合格条件で確認する。002固定・課金生成はまだ行っていない。最新観測quotaは10%（observed `2026-10-27T17:09:04.360Z`）、許可には送信前の新しいguard確認が必要。

## 002直前：両方PASS・次は固定と実行

- `bg_50`の標準M0はPASS、program total9.6757598秒。`bg_51`のH0 smoke05もPASS、63.609秒。mock2応答・実CAD2試行、誤仕様拒否、既存R1修復1、完全capture8。旧300秒切れはこの通し実行では再発していない。いずれも実モデル0。各文書を閉じ、SW PID53084/34.4.0を終了・再起動せず保持した。
- 共通view修正後のホスト17テストも全PASS（0.368秒）。既存SDK6 PASS（4.156秒）と合わせ23件。これらと無課金予算smokeを根拠に、002を固定して実行する条件を満たした。追加live生成はまだ0、18計上/22残。
- M0_SUMMARYとH0_SUMMARYを最新成功状態へ更新し、public resume JSONをprelive snapshotへ変更。H0_PLANに更新後34.4.0/owned-view制御・両確認の証拠を記載した。source bindingがtools全Pythonを含むことを確認し、`sw_m0.py`の変更も次のmanifestへ含まれる。
- dashboard-builderへmajor milestone更新を依頼したが、専用toolのmodel/effort不一致で再び保存不能。モデル変更・代替公開はしていない。ダッシュボード不調は課金や安全ゲートを変える理由にしない。
- **現在動作中jobなし。次の実コマンド**はcheckpoint commit後、`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h0.py prepare --run h0-20261027-002`、成功後同じvenvの`... run --run h0-20261027-002`（cwd SW worktree）。freeze後はH0_PLAN・tools・skill・policyを変更せず、H0_PROGRESSなど非凍結の進捗だけを追記する。55%ASK/60%停止・gold非公開・単一生成childを守る。
