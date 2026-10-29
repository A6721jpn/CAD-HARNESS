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

## Handoff：Epoch05実較正を実行中

- sourceと新bankの20正負制御・44テスト・R1 smokeの公開証拠は`ec6394c`でh2/swへcommit/push済み。runtime/候補文/元判定は前epochのまま。旧epoch04結果の保存commitは`73595db`。
- epoch05 freeze v3は2026-10-27T22:09:34.292918Z作成、manifest SHA `0938ca64b11e56b57cf459226cb7caab83e16e1da89f707ddc1236afc8a33d65`。新fixture sealは`63871ef830fb0aa43daa51acc48beb9b802f5f90505fd78924d10170a5628c73`。A/B skill SHAは従来どおりで変更なし。
- **現在の実生成jobは`bg_68`のみ**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py run --experiment skill-20261028-05`。別generator/runは起動しない。code/skill/計画は編集しない。実user packet照合とquota/call guardを各callに適用し、較正が2/5か3/5になった最初の課題でのみA/Bへ進む。
- 最後の公開quotaは18%。55%ASK/60%停止、各pool40、max2、稼働SWの終了/再起動禁止、Gold machine-onlyは不変。source frozen後の追加はprivate会計publisherとこのメモだけ。
- **job終了後の正確な次コマンド**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261028-05/publish-accounting.py`。未実行。controller終了後だけlive pool/ledger/初回packet確認件数を突合し、Goldを読まない。
- 次は自動結果を受領（pollしない）→会計→public結果/採用gateを確認→h2/swへ結果commit/push。B/比較/holdoutの成立を推測しない。timeout/機械停止やcache除外の費用も消さない。quota/実SW無応答の安全停止は優先する。

- H2停止 {"status": "STOPPED", "at": "2026-10-28T00:01:57.232460+00:00", "reason": "STOP_SW_state_unknown_no_restart", "manual_SW_recovery_required": true}

## Handoff：Epoch05 closed-SW neutral timeout継続の検証中

- `bg_68`は20較正後に停止（6738.57秒）。保存合否はH2D1=5/5、D2=5/5、D3=4/5、D4=3/5。最後のD4R5は不合格のまま。model20/40・pending0・CAD18・初回実input確認20/20・最大quota18%を公開会計へ保存した。B/比較/holdoutはまだnot_run。
- 原因の機械確認：最後の`driver-run.json`は`H0_neutral_worker_timeout`。SW completionはPASS/stop=false/COM unknown=false/文書0、fresh再importのstage artifactあり。実SWも同じ53084/34.4.0で応答/文書0を確認した。したがってSWを終了/再起動せず、controller60948不在＋lock排他open成功後、`session.lock.stale-20261028-h2-epoch05-neutral-timeout`へrename保存した。bar/time枠を緩めて判定し直さない。
- 未commit実装：H2 runtime v4は、正確なneutral SDK timeout＋正常SW閉鎖＋同一SW/文書0を確認したときだけ、失敗scoreを保持してepisode timeoutとして次へ進む。SW非応答/COM unknown/source変更/quota/他checker errorは回復対象外。元v4/H0/Native API/判定/時間/call枠は編集していない。
- `freeze-continuation`/`run-continuation`を追加。旧manifest・20結果・各input/ledger/full stream/native completionをhash固定し、連続した完全5回ブロックと最後だけの認証済みtimeout失敗を要求。再生成/再採点/旧結果上書きなし。critical code/model/skill/policy/schema/host/binary等が変わっていれば拒否。元A/B順へD4から進み、比較は独立40枠を使う。
- SDK全`test_sw*.py`は**49/49 PASS、skip0、3.184秒**。SDK timeoutとSW unknownの区別、policy/judge変更拒否、保持failed scoreの改竄拒否を追加。Eval `h2RecoveryUnitSDKObserved`。実保存prefixの機械replayでも20件・5/5,5/5,4/5,3/5・最後Falseの保持とSW closed証明を確認（モデル0、公開`continuation-prefix-smoke.json`）。Source変更はH2 runtime/CLI/test＋計画/メモだけ。
- **現在のjobは`bg_69`のみ**。private `neutral-timeout-smoke.py`が正例を実SWで正常保存/閉鎖してから、テスト専用fresh SDK timeout=.001秒だけを注入する。稼働SWをkillせず、実SDK timeout例外が維持され失敗のままSW非応答と区別されることを確認する。productionの時間値は変更しない。モデル0。結果前に成功としない。
- 次の一手：`bg_69`の自動結果を受領→source/20部分結果/停止会計/新proofをh2/swへcommit/push→`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py freeze-continuation --experiment skill-20261028-05`→同CLI `run-continuation`。20生成物は呼び直さない。prefix certificateが通らなければ迂回しない。55%ASK/60%停止、max2、Gold machine-onlyは不変。

- `bg_69`完了：**実SW＋実FreeCADの注入timeout smoke PASS、58.47秒、モデル0回**。正常SW保存/閉鎖・同一SW/文書0を確認し、fresh SDKだけのtimeout例外を維持して`H2_closed_SW_neutral_timeout`へ分類。失敗をPASSにせずproduction時間値も変更なし。公開`neutral-timeout-recovery-smoke.json`。scratch専用lockは正常終了時に解放した。現在jobなし。
- 次コマンドは上記source/20部分結果/evidenceの明示path commit/push。その後`freeze-continuation --experiment skill-20261028-05`を実行し、証明が通った新manifestだけで`run-continuation`を起動する。新規生成は比較分だけ、元20件は読取継承する。

## Handoff：Epoch05比較を新継続ロックで実行中

- 回復source＋20件の保存結果/部分会計/49テスト/実timeout smokeは**`b25f134`**でh2/swへcommit/push済み。
- `freeze-continuation`成功（モデル0回、2026-10-28T00:24:19Z）。新v4 manifest SHA **`6481edfccc77cc64758c8e20badf6132a339fce1deac48c514042eb63d278de7`**、旧v3 SHA **`0938ca64b11e56b57cf459226cb7caab83e16e1da89f707ddc1236afc8a33d65`**。20件のprefix labelと最後のCH2D4R5 failed certificateを固定。policy/model/skills/host/binaries/判定/時間の不変比較も通過した。
- **現在`bg_70`**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py run-continuation --experiment skill-20261028-05`。元20件は再生成しない。初eligibleはH2D4（3/5）、A1B1から交互比較、最初のcache差<=1ppの5組を使用、最大10組。候補段落は初めの封印から同一。元60題は使わない。
- 残り：自動job結果受領→private `h2-skill-20261028-05/publish-final-accounting.py`（controller停止後だけ、公開`accounting-final-public.json`へ新規出力）→比較/採用/fresh holdoutの固定gate結果を記録→public結果＋メモをcommit/push。既存`accounting-public.json`や旧trial/stream/ledgerは上書きしない。Source/候補/計画は以後変更せず、stdout進捗をpollしない。55%ASK/60%停止・実SW無応答時停止を優先。

## H2完了：Epoch05、候補不採用・元skill維持

- `bg_70`正常完了（controller 7324.24秒）。元20較正は保存物だけで継承し再生成/再採点なし。最後のCH2D4R5はFalseを保持。A/BはA1B1…A10B10を全20回実行し、事前cache条件を満たす最初の5組が成立。除外組は1/5/6/7/8、費用も結果も削除しない。
- 一致5組の合格は**A=4/5、B=5/5**。平均model callはA/Bとも1.0、平均active秒はA=347.5032、B=329.5968。採用に必要な「+2件」には届かず、`pass_gain_below_two`で**不採用**。元skillを維持。fresh sealed holdoutは規定の事前gate不成立により**not_run（0件、0 call）**。N=5の統計的確認とは主張しない。
- 公開`result.json`はcomplete/adopted=false。episode active合計14044.456秒は元20＋比較20の合計で、controllerの経過時間とは区別する。model=`openai-codex/gpt-6.1-sol`/xhigh、判定/policy/cards/時間/技能候補は凍結値のまま。
- 最終会計`accounting-final-public.json`：本epoch **40 model attempts/40保守計上/36 CAD attempts**、較正20/40＋比較20/40の独立pool、pending/unknown=0、exact overload=0、最大quota18%。実初回user packet確認40/40、不一致/未確認0。tokenは36/40だけ既知で総計null、価格も根拠未提供のためnullとし推計しない。旧部分会計/全ledger/full stream/生成物は上書きなし。
- 完了後のread-only COM確認：**SW PID53084、34.4.0、ready=true、文書0**。実行中SWの終了/再起動なし。`final-sw-readiness.json`に記録。非応答jobやcontrollerの残件なし。回復実装は49テストPASS＋実SW/実SDKの0モデルtimeout smoke PASSで確認済み。
- H0の18/18完了後、独立dev/封印holdout・skill段落だけの交互比較・固定採用gateまで終了。元60題/Goldを改善に再利用せず、封印値/seed/raw/STEPはmachine-only・Git外のまま。今回の候補の利得不足は不採用の結果として保持し、新候補や追加実験を事後に開始しない。
- 最後の操作：新しい公開manifest/20比較row/cache判定/最終result/会計/SW確認と本メモをh2/swへ明示path commit/pushし、短く報告して待機する。未解決の実行blockerなし。今後の候補改訂は別の事前登録とfresh sealed cohortが必要。

## Handoff：Epoch06準備（10/29 02:45 JST承認）

- 前epochは`4816bd1`でh2/swへcommit/push済み。今回もこのworktree/branchだけを使用し、元skill維持の既存判定は変更しない。
- **PID10800をsolは起動していない**（前回終了以降はアプリ起動操作なし）。起動元は未確認。両SWを終了/再起動せず、10800へbind/文書操作/設定変更しない。ROTの登録名だけを列挙して`SolidWorks_PID_53084`の存在を確認した。新しい共通attachはこのmonikerだけをbindし、最初にPID一致を確認する。既定ProgIDへはfallbackしない。
- `H2_SKILL_PLAN.md`にepoch06を事前登録。穴27/29/31/33/35の別seed dev5/holdout5、同じ候補段落B、既存の全採用/cache/判定/時間条件。公開設計値は新しい合成fixtureの難度で、実測値やユーザー実物の寸法ではない。元Aの3–7割合格を狙うが保証せず、最初の2/5・3/5を選ぶ条件を維持。
- **今回の40回は較正＋比較＋最終の合計**。1つのdurable poolを全phaseで共有する実装に切替え、rolloverは廃止。次の完全な較正5回/比較pair/最終5回が元max3 callずつで収まらなければinconclusiveで元版維持。途中片側だけ開始/旧枠流用/unknown回避はしない。CLI/native判定・カード0.01/全体0.005・policy/採点は変更なし。
- 新dataset `skill-20261029-06`のseal SHA **`8c05668996f945c45222e0b7d7bc23eee3c10de0282d200165fae39d0fc12a2d`**、factory **`e285cc3f80ef5234c4af57a5f9bdf77b6f2f585615ca453f942105a402044a97`**を公開hashで確認。Gold/seed/spec/STEPはmachine-onlyのprivate保存。原60は再利用しない。
- **現在`bg_71`**：PID専用のread-only identity確認→新dataset封印→20正負native controlsを実行中。SW workerは自作文書だけ、実モデル呼出し0。controls中のnative source/factoryは以後変更しない。
- SDK全`test_sw*.py`は**54/54 PASS、skip0、3.735秒**。PID10800をbindしない/53084不在でfallbackしない/PID不一致で文書を照会しない、phase合算38回時に次pairを開始しない、最終5件予算の不足で部分開始しないことを確認した。既存のquota55/60・unknown保持・41回目拒否・privacy・numeric testsも通過。公開`regression-tests.json`。
- quota実測：**6%**、snapshot `omp-usage-1793209975076-7d=6`、observed 2026-10-28T17:52:55.076Z、guard decision allow。後の各modelでも新しいsnapshotを検証する。Codexは親＋逐次generatorの最大2。
- dashboard-builderは今回も専用storeから「指定されたモデル・effortではありません。」で読取/保存不能。モデル変更や代替公開はせず、dashboard未変更。このメモに事実を記録して本作業を継続する。
- 次の一手：`bg_71`の自動結果を受領→`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py smoke --experiment skill-20261029-06`（モデル0・実SW/FreeCAD R1）→source/evidenceを明示path commit/push→同CLI `freeze --experiment skill-20261029-06`→`run --experiment skill-20261029-06`。control/smoke成功前にliveへ進まない。結果/会計は新epochの公開ファイルへ保存し、旧epoch結果は触らない。

- 事前登録/source/seal/54テストは**`8041a81`**でh2/swへcommit/push済み（live0）。`bg_71`は**20/20正負native controls PASS、2015.79秒、実モデル0**で正常終了した。実測identityはSW53084/34.4.0/文書0・実体SHA従来一致。各controlもこのPIDのworkerで作成し、別SWへのfallbackなし。
- **現在`bg_72`**：`tools/sw_h2.py smoke --experiment skill-20261029-06`。mock応答だけで実SW/FreeCADへ誤仕様→元R1復旧を通し、captureと元のslot/time/privacyを確認中。成功前にliveは起動しない。
- 終了後の会計コマンドも準備済み：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261029-06/publish-accounting.py`。controller停止後だけ単一epoch poolと全live ledgerを突合し、較正/比較/最終合計<=40とpendingを公開する。新しい公開`accounting-public.json`へ保存し、sealed値/生応答は表示しない。

- `bg_72`の強制R1 smokeは**FAILのまま保存**（156.50秒、model0）。誤仕様は拒否され、2回目のSW作成/保存/閉鎖もPASS/COM unknown=false/文書0/同PID53084だったが、元のR1 CAD90秒枠のSDK判定で`H0_neutral_worker_timeout`。元v3のrepair CAD90秒/reimport90秒を確認した。SW非応答・source変更ではない。driverの完成CAD recordは1、ledger上の実CAD開始/終了は2であることも別診断へ保存した。上限延長や失敗の成功化をしない。
- **現在`bg_73`**：同じ封印dev1の正仕様だけをH2 blind経路のMVPで検証し、続けて既存の独立public開発fixture G6で誤仕様→R1成功を検証する（どちらもmock、実モデル0）。原60やsealed holdoutを使わない。難しい形が固定90秒R1で落ちることと、通常生成/修復機構自体の不具合を分ける。失敗したhard R1 proofは上書きしない。以後のliveでも同じtimeoutなら不合格としてそのまま採点する。

- `bg_73`正常完了（160.11秒）。**H2 blind MVP PASS、114.953秒、mock1/実CAD1/capture4**。独立G6の誤仕様拒否→**元R1復旧もPASS、44.093秒、mock2/実CAD2/capture8**。両方とも実モデル0、元時間枠/採点を維持。G6は独立public fixtureであり、較正/比較/holdoutへ混ぜない。
- 強制hard R1のFAIL・SDK timeout診断と、今回のMVP/独立R1の成功をそれぞれ別receiptへ保存した。`H2_SKILL_PLAN.md`へ最初のlive前の検証補足を追記し、hard R1が通ったと偽らず凍結する。コードは54テスト時から変更せず、補足は文書/証拠だけ。
- **現在jobなし。** 次はpublic証拠＋補足メモをcommit/push→`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py freeze --experiment skill-20261029-06`→同CLI `run --experiment skill-20261029-06`。single epoch poolの合計40上限、55%停止報告、PID53084のみを維持。全失敗/費用も保存し、実行中はsource/候補/計画を編集しない。

## Handoff：Epoch06凍結live実行中

- 全成功/失敗preflight証拠と最初のlive前の補足は**`cc77e49`**でh2/swへcommit/push済み。強制hard R1のFAILも含め保存した。54テスト時からコード変更なし。
- freeze完了：2026-10-28T18:35:34.539282Z、manifest SHA **`f9059adee6be459ed159a1c548d0450f7855ecd20b5fcb4ef06e20a410e040a3`**。PID53084/34.4.0/文書0、同じSW実体・omp18.11.2・Sol/xhigh・A/B skill SHAを固定。protocolに`epoch_call_cap=40`を明記し、全phaseが単一poolを使用する。
- **現在jobは`bg_74`のみ**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py run --experiment skill-20261029-06`。source/候補/計画は以後編集しない。初めの2/5・3/5候補だけを採り、同じA/B交互/一致5組/最大10組/採用条件を使う。採用gateと予算が両方通ればfresh5確認へ自動で続く。次の完全単位が40枠へ入らなければ不成立で元skill維持。新poolを増やさない。
- 53084以外のSWへbindしない。10800を含め稼働SWを終了/再起動しない。Codexは親＋逐次generatorの最大2、55%で停止報告（60%も停止）、欠損/古いquotaも停止。進捗logのpollやGold/seed/raw/CADの親への展開はしない。
- **job終了後の次コマンド**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261029-06/publish-accounting.py`。その後、公開結果/会計とread-onlyの53084文書0確認を保存→元skill維持/採用判定を記録→public結果/メモを明示path commit/push。既存epoch会計・結果は変更しない。dashboardは専用tool不一致のため今回3回とも未更新、代替モデルや公開設定変更はしていない。

## Epoch06完了：難度gate成立・文章候補は不採用

- `bg_74`正常完了、controller **6847.03秒**。事前順の最初H2D1で元Aが**2/5（40%）**となり、30–70%の目標と固定gateを満たした。残りdev4件へ都合よく入れ替えない。元60や旧epoch課題は再使用していない。
- A1B1…A6B6の12比較を実行し、cache差<=1ppを満たす最初の5組が成立。除外pairは3だけ。固定5組では**A2/5、B2/5**、平均callは各1.0、平均active秒はA407.9342/B406.0778。利得0で必要+2未達、`pass_gain_below_two`により**不採用・元skill維持**。最終封印holdoutは規定どおりnot_run、0件/0 call。N5の統計的確証とは主張しない。
- 最終会計：**model17/40（較正5＋比較12）・実CAD17・pending/unknown0・overload免除0・残23**。最大観測quota **6%**。単一epoch poolの予約と全live ledgerの合算が一致し、実初回user packetも17/17確認・不一致/未確認0。入力70539/cache-read4224/出力214623 tokenは記録値、reasoning内訳と価格は未提供のためnullを維持。未使用23枠を新claimへ移さない。
- `failure-summary.json`は公開rowだけを機械集計：全17件のうちPASS7/FAIL10、FAIL10件は全てclosed-SW neutral SDK timeout、他のfailure0。SW作成/閉鎖を確認できても時間内に形状の最終証明が終わらなかったものは、形状正解と断定せず**従来どおりFAIL**。判定・時間枠を変えず、再生成/再採点はしていない。
- 完了後read-only確認：**PID53084、34.4.0、文書0、同実体SHA**。`final-sw-readiness.json`へ保存。10800へbind/操作せず、両SWの終了/再起動なし。現在job/controllerなし、55%停止条件に到達していない。
- 成果は`reports/sw-h2/skill-20261029-06/`のfrozen manifest/result/accounting/全17row/failure summary/検証receipt。本epochのepisode active合計6839.17秒とcontroller経過時間は区別する。封印値・seed・raw・CADはGit外で維持。
- 次の事前登録済み手順は「比較が採用gateを満たす場合のfresh5確認」だけで、今回は条件不成立。新候補/追加pair/別epochは本登録にないため、残23回を使った事後比較は行わない。合格ライン・policy・カード0.01 mm・全体0.005 mm・採点・比較/採用条件は不変。結果をh2/swへcommit/pushして本epochを終了する。

## Handoff：Epoch07準備・課金0のtimeout原因調査と高速化

- 次段階の夜間委任を受領。まず旧epoch06の保存timing/構造だけを機械集計し、旧合否は再生成/再採点/上書きしていない。失敗10件のmodel合計3300.467秒（平均330.047）、SW合計126.171秒（平均12.617）。timeoutはprimary5件/fresh再import5件。候補のfeature数/種類は10件とも元の宣言と一致し、余分な加工を増やした証拠なし。ただしtimeout形状の正解は断定しない。
- `timeout-timing-diagnosis.json`/`timeout-complexity-diagnosis.json`は旧epoch06公開結果へ追記した新しい診断のみ。元17row/result/accountingと封印値は変更なし。SW待ちではなく、長いAI応答後に残時間で中立検証を完了できないことが原因と判明した。
- 課金0/SW操作0のコピーprofile：primary68.758＋fresh26.649秒、境界距離証明92.641秒/OCCT cut85.943秒が大半。`sw_m0_distance.boundary_distance`に`decision_only`を追加し、M1だけ使用。既存の双方向全境界包含・native guard・FAIL witnessを保ち、外向き丸めでも閾値内となる有効PASS証明後の追加細分化だけを止める。既定M0は従来の細かい数値上限を維持する。M1の上限値はより粗くても保守的な証明であり、0.005/原0.01/timer/採点は変更なし。
- 最適化profileはprimary45.470＋fresh18.363秒、同じ全判定/編集/再import成功。これは1ケースの実測で全題速度保証ではない。独立dev正負10件も旧保存判定と新geometry/whole-boundary判定が全一致（119.84秒）。初回等価性scriptのSDK import初期化漏れは課金/判定前に修正し、失敗captureはprivate保存。Gold/spec/STEP/model本文は親へ表示していない。
- SDK全`test_sw*.py`は**59/59 PASS、skip0、4.963秒**。near-boundary0.0049/0.0051とsmall-shift/void/guard、carry優先・prefix改竄停止・別pool pending迂回拒否・fallback中断再開でA再生成なし等を確認した。LSP reference lookupはserverなしだったため、既存callerを限定読取して更新。format/lint等の余計な処理なし。
- 未commitの恒久source：`tools/sw_m0_distance.py`、`sw_m1_distance.py`、`sw_h2_fixtures.py`（control sourceへ距離依存を追加）、`sw_h2.py`、`sw_h2_runtime.py`、`test_sw_m0_remaining_native.py`、`test_sw_h2.py`、新`skills/cad-harness-v4/modeling-h2-r2.md`。文書は本メモと`H2_SKILL_PLAN.md`。public診断/profile/等価性/59test receiptあり。ACL/ownership/registry/描画設定の変更なし。
- r2は1案のみ。共通datum/単位/初点と円周step回転の再利用、精度維持、compact数値JSONで計算時間の短縮を狙う。元A・その他skill/contract/policy/cards/schema/採点・cache/採用条件・モデル・時間/修復枠は固定。高速化をA/B共通backendとして扱い、epoch06との差を文章効果にしない。
- 予算実装：epoch06 poolの既消費17のprefix bytes/SHAをfreezeし、**残23を先に使う**。次の完全単位が入らない時だけ新40へ進む。最大作業量は従来手順どおり75較正＋60比較＋15最終＝150 logical calls（計画上限）。必要時だけ最大4個の新40枠を使え、余り/未使用枠を消費目標にしない。全既存poolのpending/unknown・prefix変更を毎unit確認し、unitのpool indexを保存して途中Aを再生成しない。各pool40上限と追加合算150を機械的に守る。
- 新dataset **`skill-20261029-07`**を事前登録後にdev5/holdout5へ新seed封印。seal **`cb53561f18ae8dc6768d9c349854f73f9e7ef40d413befd109da648b369e26f7`**、factory **`d852f00024156f0effb471a67ae1e121b913234475b6547064bff12e21fda645`**。27/29/31/33/35穴の既存ラダー、原60/旧課題を新model試験へ再利用しない。
- **現在jobは`bg_79`のみ**：funding残23/旧17の確認→新dataset作成→新backendで20正負native controlsを実行中。Native source/factoryは以後変更しない。SW53084だけ、10800を含む稼働SWの終了/再起動なし。まだepoch07の実モデル0。Codexは最大2。dashboard-builderは専用storeのmodel/effort不一致で未更新、代替モデルなし。
- **次の正確なコマンド**：`bg_79`の自動完了結果を受領→`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py smoke --experiment skill-20261029-07`→source/診断/prereg/全証拠を明示path commit/push→同CLI `freeze --experiment skill-20261029-07`→`run --experiment skill-20261029-07`。新manifestはv5でsource/予算順も固定。55%停止報告/60%停止を維持し、native無応答時は止めて報告。
- live終了後の会計scriptも準備済み：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261029-07/publish-accounting.py`。旧17を再計上せず各poolの追加分と新live ledgerだけを突合する。旧epoch06会計を上書きしない。

- 以上の診断/判定同等高速化/59テスト/単一r2候補/予算保全/新封印/事前登録は**`d9f048d`**でh2/swへcommit/push済み（epoch07 live0）。上の「未commit」はこの保存で解消した。`bg_79`のcontrol結果とその後のR1 smokeはまだ受領前で、成功とは記録しない。次は自動結果→同じ`smoke --experiment skill-20261029-07`。sourceを途中変更しない。

- `bg_79`完了：新backendの**20/20正負native controls PASS、1437.06秒、実モデル0**。開始時の旧17/残23も確認した。native source/factoryは`d9f048d`のまま。**現在`bg_80`**でepoch07 blind mock→誤仕様拒否→元R1復旧を実SW/FreeCADで実行中。成功前に課金へ進まない。次は自動結果→public controls/smokeとメモをcommit/push→`freeze`→`run`、experimentは全て`skill-20261029-07`。

- `bg_80`完了：**hard dev1のblind R1 smoke PASS、126.484秒（tool128.60秒）、mock2/実CAD2/capture8、実モデル0**。誤仕様拒否→元R1=1で復旧、parse修復0。原90秒CAD/90秒再import枠・判定・closed-stdin/盲検inputを維持した。epoch06のhard R1失敗を上書きせず、新しい独立課題で成功を確認した。これでepoch07の課金前検証は完了。
- 現在jobなし。次はpublic controls/preflightと本メモを明示path commit/push→`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py freeze --experiment skill-20261029-07`→同CLI `run --experiment skill-20261029-07`。初回のcarryは旧scope17予約を保った残23、必要時だけ新40。freeze以後はsource/候補/計画を変更しない。

## Handoff：Epoch07凍結live実行中

- source/prereg/診断は`d9f048d`、新control20件とhard R1成功を含むpreflight証拠は**`ac4f2c7`**でh2/swへcommit/push済み。
- quota直前実測 **7%**、snapshot `omp-usage-1793227053437-7d=7`、observed 2026-10-28T22:37:33.437Z、checked 22:38:17Z、decision allow。
- freeze v5は2026-10-28T22:38:18.542105Z、manifest SHA **`89691ce640bd18ebe7f8803bbc9b31d5e2f4338ac6c4686f17b0b37668656d2f`**。元A SHAは従来どおり、r2 B SHA **`b9c7d7fdebc07b21b964d5b10969c90b9441268b7f70bd97d231df57e480f3ed`**。旧17のprefix6817bytes/SHAと残23→条件付き新40の順序も固定。価格/usageは実record以外を補わない。
- **現在jobは`bg_81`のみ**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B tools/sw_h2.py run --experiment skill-20261029-07`。source/候補/計画を編集しない。最初の2/5・3/5ラダー候補、交互A/Bの最初のcache一致5組/最大10pair、固定採用gate、条件成立時だけfresh5確認まで同じrunnerが実行する。新backend共通なのでepoch06との単純差を文章の効果としない。
- 55%使用量で止めて報告、60%/snapshot異常も停止。SW53084のみ、10800へbindせず、両SWの終了/再起動なし。Codexは親＋逐次generatorの最大2。進捗poll・Gold/seed/raw/CADの親への展開はしない。dashboardは今回も専用store不一致で未更新、代替モデルなし。
- **結果受領後の正確な次コマンド**：`C:/dev/solidworks/.venv-solidworks-automation/Scripts/python.exe -B reports/sw-m0/m1-private/h0/h2-skill-20261029-07/publish-accounting.py`。旧17を引いた追加予約と新ledgerを突合→公開result/会計/失敗分類を確認→PID53084のread-only文書0確認→採用/維持/停止点を記録→明示public/メモのみcommit/push。既存epoch06会計/合否は変更しない。

## Handoff：10/30夜間復旧・課金0、運用経路の制約で停止

- 10/30 02:45 JSTの監督指示で再開調査。旧controller **PID44296は不在**、旧epochに一致する残存workerも0。controller/session/poolの3 lockは排他read可能と確認し、削除せずそれぞれ`.stale-20261030-recovery`へrename保存した。ACL/ownershipの変更なし。
- frozen manifest **`89691ce640bd18ebe7f8803bbc9b31d5e2f4338ac6c4686f17b0b37668656d2f`**とsidecar一致。source/計画/候補A+B/全sealed inputs/実行binary/OMP実体hashは全て変更なし。Gold/spec/model/STEP本文は親へ表示していない。
- 保存済み試行は**14件**。較正H2D1=5/5、H2D2=2/5、比較P01/P02の4試行が保存済み。全保存14件ではPASS9/FAIL5だが、比較は未完了で採用判断をしない。中断は**P03A**：model開始1/終了0・CAD開始0。最後の保存eventは`quota_checked` **2026-10-29T00:12:12.176637Z（09:12:12 JST）**。終了理由は外部omp終了までしか確認できず、SWがいつ/なぜ終了したかは未確定とする。
- 既存poolは予約32（旧epoch06の17＋epoch07の15）、うちpending1だった。監督の安全側計上指示により、既存の`Pool.settle`でその1回を**保守的に使用済み**へ確定した。予約総数32は前後不変、pending0、**残8**。providerの応答完了や請求額を確認したとは主張せず価格nullを維持。中断ledgerはbyte hash不変、架空のprovider応答/採点結果は作らず、呼び直し0。旧17のprefix hashも維持。
- `accounting-public.json`はepoch07追加**15 model attempts/11 CAD attempts・保存結果14件・pending0・残8**として新規保存し、既存ledgerと突合済み。旧epoch06会計は上書きしていない。旧live中の最大quota7%、復旧時の新snapshotは**9%**（observed 2026-10-29T17:47:00.733Z、decision allow）。55%停止には未到達。
- SW起動時に稼働0を確認し、公式`SOLIDWORKS Design.lnk`を**1回だけ**起動（launcher9944、2026-10-29T17:51:25.2656585Z）。既存SW/他processを停止していない。read-only COM確認で新SW **PID70316 / Revision34.4.0 / 文書0**。新SWは起動したまま維持し、終了/再起動しない。
- **凍結ソースを変えない既存経路は再開不能と実測確認**。`sw_m0.py`の接続先は旧PID53084に固定され、既存`solidworks_identity`は新PIDを`STOP_authorized_SW_PID_not_registered`で拒否。既存`funding_plan`は新しい独立実行名を`H2_epoch07_authorization_required`、元名の新freezeを消費済み残高のため`H2_carry_pool_balance_changed`で拒否した。P03Aの未完了directoryも残っており、通常のtrial作成は既存directoryへ上書きしない設計。凍結元の全controlも旧PIDへ固定されている。
- したがって、監督が許可した「通常resume」だけでなく「同条件の新独立run」も、現コードの正規入口には接続先/新run/現在残高の登録方法がない。PIDの偽装、実行時の未記録patch、残高reset、旧結果の作り替えで回避しない。**追加model0、追加CAD生成0**。候補/計画/判定/時間制限/封印は未変更。
- 成果は`recovery-20261030-{assessment,conservative-charge,startup,compatibility}.json`、新会計、保存14row、freeze-publicと本メモ。操作scriptとraw/lockのprivate側archiveはGit外。dashboardは専用storeのmodel/effort不一致で今回も保存不可、代替モデルなし。
- **必要な例外判断**：再開に必要な運用部分だけ（新SWの接続先、新しい独立run名、使用済みを保った現残高の登録）を最小修正し、0課金対照確認後に新しく固定し直してよいか。採用条件/候補文/課題family/判定/policy/cards/時間枠は変えない。許可までは起動済みSW70316を維持し、残8を使わず停止する。
- 次の操作：回復証拠・保存14row・本メモを**h2/swへcommit/push**し、上記の制約と必要な例外を`ASK:`で報告。凍結source/skill/planはcommit対象にも変更対象にも含めない。
