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

## Handoff — 002ライブ実行中、固定物を変更しない

- 回復と独立予算のcheckpointは`3da5d9d`、`origin/h2/sw`へpush済み（`87ec4ef..3da5d9d`）。23件の回帰と標準M0/smoke05の実動作証拠、失敗とrename lock、H2事前計画を含む。元gold/private raw/`__pycache__`は含めていない。
- 002の新規prepareが成功。schema v2、manifest SHA256 **`db2209467f2abbc299a01e9bb49b2423f9737fe185e2ffdea11c5f9bce6914f6`**。Codex `gpt-6.1-sol` xhigh、omp/18.11.2、exe SHA `97f5c9d5…`。共有development40の既存18予約を保持し、開始時残22。当初の同じ18題・元順序を固定。新しい独立poolはまだ使っていない。
- `.../python.exe -B tools/sw_h0.py run --run h0-20261027-002`を **bg_53** として開始済み（deadlineなし、内部の元時間枠/予算/quota監視は有効）。現在の生成成立・件数・成績は未確認。**重複run/prepare・ソース編集・H0_PLAN/skill/policy変更・別のCodex worker起動をしない。** 親と単一生成childで最大2を守る。
- 完了通知を待ち、`reports/sw-h0/h0-20261027-002/{summary,rows}.json`だけを読む。private inputs/gold/model応答/raw stdout/stderrは親から開かない。必要な基盤診断は固定プログラムが既知のコード・サイズ・hashだけを出力する。H0_PROGRESSは固定対象外なので追記可。
- 次：①bg_53自動結果②公開の有効回答/実CAD/合否と全pool会計を集計③基盤失敗なら保存後に原因修正し別claim、残枠不足なら未完了の元順序分だけ新独立40枠（承認50以下）で続行④H0結果commit/push⑤H0後、H2_SKILL_PLANに従い新データ・スキル記述のみ交互各5回の段階へ。55%は委任の例外としてASK、60%停止。SW無応答なら稼働中を終了/再起動せず停止する。

## 002完了：初回選択18題すべて合格

- `bg_53`は正常完了。選択/実行/完了18、合格18、不合格0、非選択not_run42。元60全体の合格率とは表示しない。内訳はspec11題で各1回の実CADが幾何・native編集復元・独立再読込すべて合格、ask7題も元rubricで合格。すべて1生成、parse修復0、ライブCAD修復0。controller wall414.797秒。
- 新規モデル送信18。旧001の失敗18予約も維持し、共有poolの保守計上36/40、pending0、残4、検証済みoverload拒否0。原163枠を使っていない。今回の入力66,574（cached10,368）、出力4,488は18件すべてusage既知。reasoningは18件すべて不明、料金不明。旧18失敗のトークンが不明なので全36件の総トークンをこの既知subtotalで置き換えない。overload robustnessはUNVERIFIEDのまま。
- source/skill/policy/カード/採点を固定実行中に変更していない。gold・原要求・モデル生出力は親から開かず、公開summary/rowsと完了stdoutの許可済みprojectionだけを読んだ。実モデル起動のCodex限定overlayも今回の有効応答で成立した。追加のH0継続batchは不要で、独立40poolの新規課金使用はまだ0。
- 公開証拠`reports/sw-h0/h0-20261027-002/{manifest-public,rows,summary}.json`。H0_SUMMARYはこの002から自動生成された部分H0集計。001は削除せず別の起動障害セグメントとして残す。最初に記録した18題のH0を完了し、指示どおり新規独立データのHarness²段階へ進む。残り42題を合格扱いせず、original60を改善に使わない。
- 次はH0結果とこのメモをh2/swへcommit/push。その後H2_SKILL_PLANの固定条件で、スキル本文だけを変える外側ランナー・独立fixture author・cache整合/ペア/予算の検証を実装。新しい封印ホールドアウトを比較前に作る。各版5回交互、50以下の新batchを使い、旧H0の残4を流用しない。起動中SWの終了/再起動禁止・55%ASK/60%停止・同時Codex2は維持する。

## Harness²開始：新データの由来を偽装しない

- H0公開結果は`41aec01`としてh2/swへcommit/push済み。初回選択18題のライブH0完了を区切りとし、残42はnot_runのまま明示して次段階へ。動作中の生成jobなし。
- 元のGold schemaは`authority=fixture, confirmed=false`を正式に持つが、production run_driverは非previewでhuman確認を要求する。新しい合成課題をhuman提供/確認済みと偽装して通さない。委員会で認められた「本番custodyなしの外側開発ランナー」として、新しい封印fixture専用のadmissionを用意する。
- 採る方法は元driverを変更せず独立ロードし、**production human由来確認の1箇所だけ**を、fixture由来・request/Golddigest・封印pack・正負native controlの確認へ置き換える開発用adapter。元schema読取・全数値判定・slot/時間/repair状態機械・採点を変えない。差分とadapter hashを事前manifestへ記録し、両armで同一に固定する。人間確認済みという虚偽metadataや元60の流用を拒否する。これはskillの改善対象ではなく、新しい独立fixtureを評価するための共通custody層として実験前に固定する。
- 最初の独立ラダーは同じ対応済みrect_prismの位置/単位/角度解釈を段階化した5課題、最終封印5課題。寸法・seed・goldは固定プログラムが新しく生成しprivateへ保存、親にはID/commitment/制御合否だけ出す。公称値は合成課題として設計したものと明示し、実測やユーザー提供値を装わない。
- H2用の新しい40枠を別scopeで使い、旧H0残4は使わない。説明文差分はmodelingの1段落だけとし、CLI/判定/policy/カードの数値条件は両arm同一。新holdout封印を先に作り、元版5回の較正で2/5か3/5の最初のラダー課題を選ぶ。全て天井/床なら利得を捏造せず、比較ゲート未成立と報告する。

## 独立fixture初回制御の停止・データ隔離

- `skill-20261028-01`を新seedで封印（dev5/holdout5、元60不使用、モデル0）。`bg_54`の無課金native制御はdev最初の3件の正負が合格し、次の正例が不合格で停止した。機械診断ではnative編集は成功、元のvolume/holesと全境界判定が不合格。正例にモデル出力を使っていないため、これはスキル成績ではなく入力どおりのnative作成を確認する前提条件の問題。
- 診断でsub-check IDを項目名とみなして表示したが、一部の項目名にGold由来の数値が埋め込まれていた。生Gold/原60/holdout本文を開いてはいないものの、この部分的露出を隠さず記録する。数値はここに引用しない。**dataset01全体をlive較正・比較・最終確認から隔離**し、public `quarantine.json`へ記録。課金0のため比較結果への混入はない。private資料は削除・書換えしない。
- 以後の診断は固定されたpredicateカテゴリと真偽/statusだけを出し、動的sub-check名を出さない。候補説明文は診断前のまま変更していない。backend修正後、同じ事前ラダー生成規則・新seedでdataset02を作り直す。簡単な形に変更したり、観測したGold値へ合わせたりしない。
- SolidWorks公式CreateCircleByRadius資料は、AddToDBがUIのinferencing/自動関係/grid snappingを避けると明記する。`sw_m1_build.Builder.begin/end`で自作SketchManagerのAddToDBをTrue/Falseに戻す共通処理を追加し、numeric座標の非対話作成を切り分ける。設定の読戻しとCOM異常時隔離を行い、他文書やアプリ設定は変更しない。参照：https://help.solidworks.com/2026/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.ISketchManager~CreateCircleByRadius.html
- これは比較開始前のnative精度の前提修正であって、skill改善の利得とは扱わない。両armには同じ修正済みbackendを固定し、旧H0成績と新backend成績を混ぜない。まず隔離datasetの問題となった制御を機械だけで再確認し、その後fresh dataset02全体の正負native制御と公開開発smokeを通す。H2のモデル呼出しはまだ0。

- 切分け再開の前に、失敗したnative制御のlock所有者PID45196不在と排他open成功、SW53084/34.4.0/文書0を確認した。lockを`session.lock.stale-20261028-h2-controls01`へrename保存し、隔離済みdataset01の機械専用再現制御だけを別出力へ実行する。live/calibration/holdout評価には使わず、診断出力は真偽と固定statusだけに限定する。

## AddToDB切分け成功・fresh制御へ

- `bg_55`は53.07秒、モデル0で終了。隔離済み制御の正例はgeometry/editability/verificationの全てTrue、誤仕様はgeometry/verification False・editability Trueとなった。座標の非対話作成でこの再現は解消した。ただし内部の自動補正機構のどれが働いたかまでは断定しない。
- 元の生成規則・候補文を保った新seed `skill-20261028-02`を生成・封印し、全10件×正負のnative制御を`bg_56`で開始。dataset01の隔離は解除しない。並行して外側H2ランナーを実装中で、H2のモデル呼出しは0。
- 生成前の事前条件を明文化：cache比較は初回受理生成だけ、最大10ペア内の整合5組、追加を無限に続けない。同一request/runtime_data hashと共通cwdを照合する。条件未成立時は元版維持であり、形状の合格線を動かさない。

## Handoff：H2比較実装・無課金検証中

- H0は`41aec01`までpush済み、初回選択18/18合格。旧pool36/40のまま。H2のlive/model課金呼出しは0。
- fresh `skill-20261028-02`のdev5＋holdout5について、正負20制御が全てPASS（`bg_56`、420.81秒）。seal SHAは`de7b26e3f4363136317d9e3a36b10cc87775818ee36fc289867528853c2c8adc`、公開証拠は`reports/sw-h2/skill-20261028-02/native-controls-public.json`。private Gold/seed/CADは開示・Git追加しない。
- AddToDB共通修正後の既存H0 smoke06はPASS。mock2、real CAD2、誤仕様拒否、R1=1、完全capture8、live0、episode60.516秒（tool wall62.65秒）。元H0/v3のファイル・policy・採点は変えていない。
- 追加中のファイル：`tools/sw_h2_fixtures.py`、`sw_h2_runtime.py`、`sw_h2.py`、`test_sw_h2.py`、`skills/cad-harness-v4/modeling-h2-r1.md`。既存の変更は共通native `tools/sw_m1_build.py`と計画/このメモだけ。dataset01は公開quarantineを付けて保持し、live対象へ戻さない。
- 外側ランナーは正直なfixture入場（元run_driverのhuman入場Ifだけを隔離ASTへ置換）、共通source/skill A+B/入力/native結果hash、SW PID/revision/実体hash、共通cwd、独立40枠、5回較正、A/B交互、初回cache整合5ペア、最大10ペア、新holdout5全通過を扱う。A完了/B未完了の再開でAを再生成しない。生エラー/Gold由来項目名はpublicへ出さない。
- 進行中：固定FreeCAD 1.1.4で全`test_sw*.py`を実行するSDK子PID68992（Evalの`h2UnitSDKResult`）、H2自身のmock-model＋real SW/FreeCAD smokeは`bg_58`。どちらもモデル0。結果確認前にgreen/成功としない。
- 次の一手：Evalで`print(await h2UnitSDKResult)`をbarrierとして受領し、`bg_58`の自動結果を受領する。問題があれば最小修正と該当検証。両方成立後、sourceをcommit/pushし、`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py freeze --experiment skill-20261028-02`、続けて同じCLIの`run`を実行。source凍結後の編集はしない。quota55でASK、60で停止、SW無応答時は終了/再起動しない。

## H2無課金通し確認・凍結前結果

- 固定FreeCAD 1.1.4 SDKで`test_sw*.py`全40テストがPASS（既存23＋追加17、3.025秒、skipなし）。判定境界、旧予算/隔離/再import、fixture入場拒否、pending課金保持、片側再開、40枠跨ぎ、cache不明/不整合の除外と全費用保持を検証した。unitの架空25予約はテスト内の模擬poolであり、実モデル呼出しではない。
- `bg_58`のH2自身のmock＋real CAD通しもPASS。`fixture/confirmed=false`を保持したまま入場し、改善文B bundle・共通cwd・実SW/FreeCAD・誤仕様拒否・元R1=1・完全capture8を確認。mock2、real CAD2、live0、episode36.390秒（tool37.96秒）。根拠は`reports/sw-h2/skill-20261028-02/preflight-smoke.json`。
- 生成前のquota公開値は13%（snapshot `omp-usage-1793126906348-7d=13`、2026-10-27T18:48:26.348Z）。各生成の直前と実行中にも既存guardが再確認する。55%/60%は緩めない。
- 次はこの実装と公開の無課金証拠だけをh2/swへcommit/pushし、live用manifestを一度作成して較正を開始する。課題・正解・raw・CADはprivate、元60は再利用しない。以降、共通sourceを変えず、gate不成立なら元版維持として記録する。

## Handoff：H2版固定後のlive較正を開始

- source＋無課金公開証拠18ファイルを`306e573`としてh2/swへcommit/push済み。__pycache__、Gold、seed、raw、CADは追加していない。
- live共通manifestは2026-10-27T18:54:52.744446Z作成、SHA `eab33e5514006133dbe5e20797d1609a39cd184511366d96c048263077e8e590`。A skill `df6a2ff9df096e7be5815957318f00684810fd79422d203d6fcdf42c9de25109`、B skill `3c96a45fbe5639f71eecdd057757a1318462a463316db3dbcea3a908555d2616`。生成器Sol/xhigh・omp18.11.2。SW53084/revision34.4.0/実体hashも固定した。source/skill/計画は以後編集しない。
- **進行中の実生成jobは`bg_59`だけ**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py run --experiment skill-20261028-02`。同時に別runを起動しない。親＋逐次generatorでCodex最大2。runnerが各生成前/実行中のquotaと各pool40上限を守り、較正→条件成立時の交互比較→採用条件成立時の新holdoutを進める。
- 凍結後に追加したのは公開`regression-tests.json`（実40/40・模擬呼出しのみ）と、このメモ、privateの`publish-accounting.py`だけ。後者はGoldを読まず、controller終了後に各40枠とtrial ledgerの予約数を突合して公開会計を出す固定プログラム。まだ実行しない。
- 残手順：`bg_59`の自動完了/停止結果を受領（pollしない）→次のコマンドで会計→public結果だけを集計→採用/元版維持と制約を記録→h2/swへ結果をcommit/pushして区切る。正解/private生成物は親へ表示しない。55%の停止ならASKして待ち、60%も停止。SW無応答なら終了/再起動をせず報告する。
- **job終了後の正確な次コマンド**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261028-02/publish-accounting.py`。既存CLAIM・結果を消さず、完了済みの生成をやり直さない。

## H2 dataset02：較正25/25、難度ゲート未成立

- `bg_59`は正常終了（controller1570.28秒、episode合計1557.689秒）。H2D1〜H2D5はいずれも元版Aが5/5、全25試行が初回生成・初回CADでPASS。2/5または3/5の候補がなく、比較・最終holdoutは**not_run**。候補Bの改善効果も採用も主張せず、元版を維持する。結果は公開`skill-20261028-02/result.json`。
- live会計は1つの独立calibration poolで25/40、pending0、物理モデル25、CAD25、overload免除0、最大観測quota14%。mock smokeの同prefix ledgerを除外する`evidence_mode=live`条件を会計用固定スクリプトへ追加して突合した。source/採点/生成物は変えていない。公開`accounting-public.json`の原カウンタはinput83,647、cache-read27,648、cache-write0、output40,845、reasoning別計測null、料金不明。
- 次の比較前にcache測定の単位を修正する必要がある。公開rowにはnative input991/cache-read3456があり、OMPの`input`は総入力ではなくuncachedの区分。元native parserはそのまま`input_tokens`へ写すため、旧H2の「cache-read<=input」条件は正しいcached応答まで拒否する。upstream maintainerの説明もinputがprompt-minus-cachedであることを確認する：https://github.com/can1357/oh-my-pi/issues/4469 。今回は比較0組なので、この問題は25件の合否と難度ゲートの結果に影響しない。旧結果・旧manifestは書き換えない。
- 次epochではuncached/read/writeの3区分を明示し、cache率をread/(uncached+read+write)で定義する。初回受理呼出しだけ・整合幅1 percentage point・最大10ペア・採用条件はそのまま。先に回帰検証し、新しい共通manifestを作る。
- 01:30の全設計委任と「開発を進める」を適用し、元版維持の記録を確定したうえで、**別の独立難度ラダー**へ進む。変更は公開生成規則の穴数/角度の設計値だけ（8/9/11/13/17穴、いずれも既存schema上限64以内）。familyは既存rect_prism、箱/非貫通pocket/through holes、元許容差・policy・カード形式・判定・時間枠・call枠は変えない。候補B文は変更しない。新seed・新holdoutを先に封印し、正負20制御が全通過するまで課金を始めない。

## Handoff：Epoch03の無課金制御待ち

- dataset02の25/25とlive25/40の会計・全公開rowを`913f416`でh2/swへcommit/push済み。比較/holdoutはnot_run、元版維持。旧sourceはこのcommitで再現し、旧ファイルを書き換えない。
- v1 cache条件は実native counterの991 uncached/3456 readを有効な同率ペアとして扱えなかった（無課金再現False）。H2だけを明示的uncached/read/write DTOと総入力分母へ修正し、freeze schemaをv2へ。保存済みledgerの機械だけの再読で、修正後は同率ペアTrue・生成packet SHA不変、モデル0を確認した。原ledger・v4 parser/判定・25件の採点は変更していない。
- 修正後の固定SDK全`test_sw*.py`は**42/42 PASS、skip0、1.884秒**（既存23＋H2 19）。native cache-read>uncached、uncached0の有効cache、cache-writeの分母参加、不明/負値/bool/浮動値の拒否を含む。Eval変数`h2R2UnitSDKObserved`に証拠がある。新ラダー最小間隔の非重複条件も機械計算でTrue。
- `bg_60`で`skill-20261028-03`の新seed/新dev5/新holdout5を封印し、正負20制御を実行中。**epoch03の実モデル呼出しは0**。Bの説明文は未変更。変更中のsourceは`sw_h2_fixtures.py`（公開LEVELSだけ）、`sw_h2_runtime.py`（counter DTO/v2）、`sw_h2.py`（cache率）、`test_sw_h2.py`、計画/メモ。元policy/schema/カード/判定/Native API/時間枠/呼出し枠は変更していない。
- 次は`bg_60`の自動結果を受領（pollしない）。全制御成立後の正確な次コマンド：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py smoke --experiment skill-20261028-03`。42テストreceiptと無課金証拠を保存し、sourceをcommit/push→同CLI `freeze`→`run`。失敗時はモデルを呼ばず原因を切り分け、SW無応答は終了/再起動せず停止報告する。

- `bg_60`完了：epoch03の正負20制御は全PASS、866.47秒、モデル0。新seal SHA `ab9c7d41b718063d8a0f3ab54fd780d223e90d0e1b368eb40c649e69c7b9ae28`、factory SHA `fc05e68b5b49cdd718e1612cca11f3878a8f0f52b1815cfa271fbe400a5597b1`。公開native証拠と42テストreceiptを保存済み。
- 次のv2 smokeは`bg_61`で実行中（mockモデル＋real SW/FreeCAD、実モデル0）。完了後にこのepochのsource/公開証拠をcommit/pushし、`tools/sw_h2.py freeze --experiment skill-20261028-03`→`run`へ進む。source/候補文の途中改変はしない。

- `bg_61`のv2 mock/real CAD smokeもPASS（episode64.953秒、tool66.92秒）。mock2、実CAD2、誤仕様拒否、元R1=1、完全capture8、実モデル0。counter修正のbefore=False/after=Trueとpacket不変を公開`cache-counter-smoke.json`へ保存した。
- 生成前quotaは15%（2026-10-27T19:49:55.822Z）。epoch03はまだ課金0。sourceと上記無課金証拠をcommit/pushし、v2共通manifestを一度作成して新較正へ進む。

- H2停止 {"status": "STOPPED", "at": "2026-10-27T19:58:07.670803+00:00", "reason": "STOP_SW_state_unknown_no_restart", "manual_SW_recovery_required": true}

## Handoff：実prompt盲検化修正、epoch04の無課金制御中

- epoch03 source/無課金証拠は`624cd8f`としてh2/swへpush済みだった。v2 manifest SHAは`1f8f96287a1f68a20d04e23c7c2807a0533c98e3ae50d112b9ec60eaf9a07c39`。その後、保存済みnative user eventの機械再読でtrial ID/`payload.json` headerの露出を確認した（本文/Gold値は表示せず、モデル0）。A/Bに入る前に本計画へ欠陥を記録し、凍結guardのsource変更検知で`bg_62`を停止した。
- 停止は396.76秒。モデル予約6/40・pending0・CAD6・最大quota15%を`accounting-public.json`で突合。公開rowは5件合格と1件のguard中断失敗のまま保持するが、**6件の能力スコアには使わない**。比較/holdoutはnot_run。epoch03全体を`quarantine.json`で比較対象外とし、課題/結果を次epochへ持ち込まない。
- 印字は保守的に`STOP_SW_state_unknown_no_restart`だったが、保存reasonの機械確認は`H0_frozen_file_changed=True`、RPC/nonresponse=False。SWは同じ53084/34.4.0で応答・文書0を確認。controller49424不在と排他open成功後、lockを`session.lock.stale-20261028-h2-epoch03-guard`へrename保存。**SWの終了/再起動もnative worker killもしていない**。
- 実装済み未commit：`sw_h2_runtime.py`でH0 runtimeを独立ロードし、そのprivate native `_invoke`の`@file`式1箇所だけをliteral JSON argvへ変更（元v4/H0ファイル・numeric state/slots/timersは未変更）。前後AST/hashをfreeze v3へ固定。全user eventがarchive request/runtime_dataと一致することを応答直後に機械検査し、不明/不一致では次モデルへ進めない。実model入力確認flagも公開rowへ出す。stdinはDEVNULL。
- `sw_h2.py`のmockもliteral JSONを受け、実parser形のuser eventを出す。既存＋盲検化回帰のSDK全`test_sw*.py`は**44/44 PASS、skip0、1.785秒**。Evalの`h2R3UnitSDKObserved`に証拠。source変更はruntime/CLI/testと計画/このメモのみ。候補B・gold schema・policy・カード・判定・Native API・許容差は変更なし。
- **現在のjobは`bg_63`のみ**。`skill-20261028-04`を同じLEVELS・別seed・新dev5/holdout5で封印し、正負20制御を実行中。epoch04の実モデル呼出しは0。親にGold/seed/raw/CADを表示しない。Codex generatorもまだ起動していない。
- 次の一手：`bg_63`の自動結果を受領し、全制御PASS後に`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py smoke --experiment skill-20261028-04`。44テストreceiptと無課金証拠→source/epoch03会計/停止記録をcommit/push→v3 freeze→run。最初の実native user packetも自動検査し、通らなければ1件で止める。55%ASK/60%停止、SW無応答時の停止、max2、Gold machine-onlyは不変。

- epoch04の`bg_63`は正負20件全PASS、812.56秒、モデル0。seal SHA `cbf19d770a914523fe0f950f905aee249942fe58d4a63130006a22bca01fb846`、factoryは同じ`fc05e68b5b49cdd718e1612cca11f3878a8f0f52b1815cfa271fbe400a5597b1`。新しいblind inputのmock＋real CAD smokeは`bg_64`で実行中。
- 44テストreceiptと、旧native eventにheaderが存在したことの真偽だけの証拠をepoch04のpublicへ保存済み。次は`bg_64`の結果→source/停止会計/証拠commit・push→v3 freeze・run。実native streamの初回packet確認が通るまでは盲検化の実証済みとしない。

- `bg_64`のliteral argv＋実SW/FreeCAD smokeはPASS（episode65.922秒、tool67.42秒）。mock2、CAD2、誤仕様拒否、元R1=1、完全capture8、モデル0。mockが実際に受けたliteral JSON user packetをnative parser形式へ渡し、metadata/header拒否の検査も通した。実CLIについては最初の実生成streamで同じ検査を行う。
- source/停止記録/公開証拠をh2/swへcommit・pushした後、v3の`skill-20261028-04`をfreeze・runする。以後、code/skill/計画を変えず、実input未確認では比較を続けない。

## Handoff：v3 blind inputの実較正を実行中

- source・44テスト/20制御/smoke証拠・epoch03の6予約と停止/隔離記録は`31b45a3`でh2/swへcommit/push済み。元v4/H0ファイル・Native API・policy・カード・採点・許容差は未変更。__pycache__/Gold/seed/raw/CADは追加していない。
- epoch04 freeze v3は2026-10-27T20:22:26.304603Z作成、manifest SHA `aa6b99a106f6c48547af54de19e5badb2be16924117dcba09bcfb7198c47c17e`。native argv ASTの置換1箇所、literal JSON引数、stdin DEVNULLを固定。A/B skill SHAは従来と同じ`df6a2ff9df096e7be5815957318f00684810fd79422d203d6fcdf42c9de25109`/`3c96a45fbe5639f71eecdd057757a1318462a463316db3dbcea3a908555d2616`。
- **現在の実生成jobは`bg_65`のみ**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py run --experiment skill-20261028-04`。別run/別generatorを起動しない。source/skill/計画は編集しない。実stdoutの各user packetはJSON本文の同一性を自動検査し、不明/不一致で次生成へ進めない。packet確認flag・cache/calls/timeだけをpublicへ出し、本文はprivateのまま。
- 生成前の公開quotaは16%（2026-10-27T20:21:42.443Z）。各call直前/実行中にもguardが確認する。55%ASK/60%停止、各pool40、max2、SW終了/稼働中再起動禁止、Gold machine-onlyは不変。
- **job終了後の正確な次コマンド**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261028-04/publish-accounting.py`。この固定publisherはGoldを読まず、controller終了後だけlive pool/ledgerを突合し、初回実inputの確認件数も出す。未実行。凍結後の追加はこのprivate artifactと本メモだけ。
- 次は`bg_65`の自動結果を受領（pollしない）→会計→public結果の判定/採用または元版維持を記録→結果をcommit/push。比較ゲート/盲検化/採用が成立したと推測しない。旧epoch02のceiling、epoch03の中断は利得に算入しない。

## Epoch04実結果：盲検化25/25、較正は再びceiling

- `bg_65`は正常終了（controller4179.08秒、episode合計4166.002秒）。初回の**実native user packet確認25/25、未確認0**。filename/arm headerを含まないJSON本文がrequest/runtime_dataと一致することを実streamで確認できた。これでv3の盲検化はmockだけの主張ではなくなった。
- H2D1〜H2D5は全て元版Aが5/5、合計25/25。H2D2の1回だけ元R1を使い、実モデル/CAD各26、parse修復なし。1つの独立poolで26/40、pending0、overload免除0、最大観測quota17%。公開`result.json`と`accounting-public.json`を突合済み。B/比較/最終holdoutはnot_run、元版維持であり、改善効果は測れていない。
- 次に進む理由は同じDIFFICULTY_LADDER_GATED条件（2/5または3/5）がまだ成立しないため。Bは変更せず、source上限64穴以内の独立ラダーで穴数を19/21/23/25/29へ進める。穴の重なりでanalytic Goldを壊さないよう、公開の合成設計半径範囲だけを30–40へ広げる（実測値ではない）。新しいfeature/family/API、許容差、採点、モデル、時間枠/call枠は追加・変更しない。新seed/新holdoutを封印し、正負native制御20件を先に通す。

## Handoff：Epoch05の無課金制御を実行中

- epoch04の実input確認25/25・較正25/25・26予約と全公開rowは`73595db`でh2/swへcommit/push済み。B/比較/最終holdoutはnot_run、元版維持。これまでのH2実予約はepoch02=25、隔離03=6、epoch04=26。旧H0の36/40とは別scope。
- 未commitの変更は`tools/sw_h2_fixtures.py`の公開難度設定（19/21/23/25/29穴、半径30–40の合成設計値）と`H2_SKILL_PLAN.md`・本メモだけ。v3 runtime、候補B、policy/schema/カード/判定/Native API/許容差/slots/time/call枠は変えていない。元64穴上限内、最小半径/最大直径で全穴が非重複であることを機械計算してTrueを確認。
- 固定SDKの全`test_sw*.py`は今回も**44/44 PASS、skip0、1.749秒**。Evalの`h2R4UnitSDKObserved`に証拠がある。新stress設計の境界計算は`h2StressDesign`。模擬poolの25予約はテスト内だけで実モデル0。
- **現在のjobは`bg_66`のみ**：`tools/sw_h2_fixtures.py create --experiment skill-20261028-05`→`controls`。新seed/dev5/holdout5を封印し、正負20native制御を実行中。epoch05の実モデルは0。Gold/seed/CADを親へ表示せず、途中でsourceを変えない。
- 正確な次コマンド（全制御PASS後）：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py smoke --experiment skill-20261028-05`。44テストreceipt/境界設計proof/無課金証拠→sourceをcommit/push→同CLIの`freeze`→`run`。native制御が元の条件を通らなければモデル不正解と混ぜず、barを緩めず原因を切り分ける。
- 55%ASK/60%停止、各独立pool40、max2、SW稼働中の終了/再起動禁止、Gold machine-onlyは不変。直近公開quotaは17%。実input検査を通ってもdifficulty gate成立を推測しない。次も満点なら結果を記録し、Bの利得を作らない。

- `bg_66`のepoch05正負20native制御は全PASS、1773.77秒、実モデル0。seal SHA `63871ef830fb0aa43daa51acc48beb9b802f5f90505fd78924d10170a5628c73`、factory SHA `bee593cc2188aff65a1c0facd17c822ce44ea04fbcd6c8ff4a6402c0d131930c`。29穴まで元条件でnative controlを通った。公開証拠・44テストreceipt・非重複境界proofを保存。
- `bg_67`でepoch05のmock/real CAD smokeを実行中。元repair CAD枠内で誤仕様拒否→R1復旧も確認してからsourceをcommit/push・freeze・runする。比較生成はまだ開始していない。

- `bg_67`の元repair枠smokeはPASS。mock2/実CAD2、誤仕様拒否、元R1=1、完全capture8、実モデル0、episode123.781秒（tool126.39秒）。Sourceとpublic証拠をcommit/pushし、同じv3 runtimeと候補文でepoch05をfreeze・runする。直前quotaは18%（2026-10-27T22:08:14.623Z）。
