# codex R1 — 固定の実行器とA専用Probeだけを試作する

[BRIEF](BRIEF.md)の決定事項1〜10に対する提案。根拠は[挿入位置CONSENSUS](../judge-ai-insertion/CONSENSUS.md)、[CASES](../judge-ai-insertion/CASES.md)、[bottleneck報告](../../reports/bottleneck-A-box-pocket-fillet.md)、[runbook](../../docs/runbook-A-box-pocket-fillet.md)、[measurement-slice](../../docs/measurement-slice-v0.md)、[tools README](../../tools/README.md)、[measure_rollout.py](../../tools/measure_rollout.py)、指定evidenceのスクリプト・cad.json。今回は資料読取と本提案の保存だけで、コード・CAD実行・計測は行っていない。

**結論：標準PythonのCLIと、FreeCAD内で動く実行・Probeの二つを核にする。A専用、同期、単一attempt、J1無効。** プラグイン、常駐サービス、複数CAD対応、自動修復・再実行は作らない。以下のCLI識別値・配置・規模は設計案で、実装と性能は未計測。

## 1. CLI：本文はUTF-8ファイルで渡す

入口は `python tools/cad_run.py --script <file.py> --out-dir reports/cad-run/<id> --timeout-s <limit>`。Aのtask_idは固定。`--backend cmd|console`はcmdを既定とし、登録済みレシピ以外のexe・追加起動引数は受け付けない。本文をargvへ埋める方式は、Windowsの引用・長さ問題を避けるため初版では採らない。timeoutは正の値を明示指定し、具体的な運用値は未設定・未計測。

スクリプト契約は `build(doc)` が渡された新規文書へAのモデルを作り、Bodyを返す形。保存・Probe・文書終了は固定側が担当する。スクリプト自身のchecksやgeometry_okは判定入力にしない。これは信頼するローカルCADスクリプトの契約であり、任意Pythonのアクセスを閉じ込めるサンドボックスではない。

元のevidenceをそのまま実行しない。[run02-build.py](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run02-build.py)等は出力先を既存evidenceへ固定し、自身で文書も閉じる。PHASE 2でrun02の作成処理から試験用コピーを用意し、形状操作・寸法・辺選択を保持してbuild契約へ包む。変更点、原本ハッシュ、コピーのハッシュを記録し、元スクリプト・既存cad.json・FCStdを上書きしない。

出力先は新規専用ディレクトリだけ。配下にattempt別のinput.py、隔離cfg、model.FCStd、worker結果、result.json、events.jsonl、stdout/stderrログを置く。既存ディレクトリの再使用・過去モデルの採用を拒否し、初版では既存evidenceやreports/runsを出力先にしない。

stdoutは短い結果JSON一つ。CADのstdout/stderrは別ファイルへ送り、JSONへ混ぜない。JSONにはschema、task_id、cad_run_id、script_sha256、recipe/probe版、status、failed_phase、next_actor、cad_exit_code、script_completed、probe_status、述語差分、実読取値、cleanup_status、相対artifactパスを分離する。未取得値はnull。

終了コードの設計は、0＝CAD終了0・スクリプト完了・Probe pass・後片付け確認済み、1＝実行／Probe不適合／停止・未完了、2＝入力・CLI設定不備。生のcad_exit_codeを別に保存する。実行成功とProbe不適合はJSONで区別し、人手のscript_ok／geometry_okへ自動転記しない。

## 2. 段：launch → build → Probe → cleanup

**launch：** DPC-019、BRIEF指定のFreeCAD 1.1.4配置に固定。cmdは指定のbin/freecadcmd.exe、consoleは既存証拠のFreeCAD.exe --console。試行別user/system cfg、空stdin、専用cwdを使う。Pythonのsubprocessで実行ファイルと引数配列を直接渡し、shell経由・.ps1実行・Start-Processの環境辞書を使わず、親の環境をそのまま継承する。一般PATH探索や実行ポリシー変更はしない。これは旧direct &方式の意図を保つ**新しいレシピ実装案**であり、同じ検証済みレシピとは呼ばず、版を付けてPHASE 3で確認する。根拠：R2-S09、R3-S08、R5-S09。

**build：** FreeCAD内の固定workerが版、GuiUp、空の文書一覧、実PIDを確認して新規文書を作り、入力のbuildを呼ぶ。返ったBodyがその文書に属することを確認し、recompute後にProbeを実行する。GUI操作・ViewObject依存を要求しない。

**headlessの根拠と未確認：** [run02-launch.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run02-launch.json)はFreeCAD.exe --console、exit_code 0。run02-cad.jsonはRunMode=Cmd、gui_up=0、Pad/Pocket/Filletとconsole_no_guiの成功を記録している。したがって当該AをGUIなしで作れる実例はある。一方、bin/freecadcmd.exeそのものの起動・オプション受理・DLL読込・同じ結果は今回のevidenceから確認できない。cmdを優先するが、失敗時に別レシピやGUIへ自動切替しない。consoleは明示選択する既存方式の対照で、GUI版の実装はこの試作に含めない。run01のFreeCADGui／カメラ操作は移植しない。

**cleanup：** 正常経路はworkerが自分の文書だけを保存・閉じ、空stdinでプロセスが自然終了したことを親が確認する。所有根拠は親が得たプロセスハンドル・PIDとworkerの実PIDの一致。名前で全FreeCADを終了したり、ユーザーの既存文書・プロセスを操作したりしない。残存・timeout・所有不明はcleanup_pendingとして失敗を返し、人手へ渡す。初版は所有プロセスにも強制終了を実装しない。

## 3. 固定Probe：要求と、既存の実読取値を分ける

FreeCAD側で実際のBody/Shape・フィーチャ関係を読む。ホスト側でcad.jsonのtrueを信用してpassにする方式は採らない。

| 確認項目 | 固定する期待値・方法 | 出典 |
| --- | --- | --- |
| 単位・外形 | Quantityをmmへ変換。bbox 40×30×20 mm、bbox許容±0.1 mm。中心配置も実読取 | runbook §1/§6、run02/run04-cad.json |
| ポケット | 上面中央20×15 mm、深さ5 mm、非貫通。底面z=15、上面z=20、底面一つ・垂直壁四つを実形状で確認 | runbook §1/§6、run04-cad.jsonのfeature_measurements |
| 体積 | フィレット無し基準22500 mm³より小さく、既存の最終実読取22239.9556819442 mm³を参照に±1% | runbook §6、run02/run04/run05-cad.json |
| 面・単一ソリッド | 最終15面、単一Body・単一valid solid。表面積5364.637121611783 mm²は参照・補助記録で、独立の合格条件にしない | run02/run04/run05-cad.jsonのmeasurements。runbookの面数未固定という旧記述を新しいevidenceで具体化 |
| 外周フィレット | Radius 3 mm、Baseは実Pocket、上面外周の異なる四辺だけ。UseAllEdgesを許さない。参照元Pocketの各辺の端点・直線性・外周座標を検証 | runbook §1、run04-script.py／cad.json |
| 内側への非適用 | ポケット内縁が直線のまま、隣接する平面の法線が直交することを確認。run04の内縁12本（開口・底・縦辺）のsharp判定を採る | run04-script.py、run04-cad.jsonのpocket_inner_edges。run05は開口四辺・底四辺の追加参照 |
| 追加featureなし | Body、Sketch、Pad、Sketch、Pocket、Filletの型と所属・Profile/Base/Tip関係。標準Origin等は実体とOriginFeatures・親関係で除外 | run02/run04/run05のスクリプト・cad.json |

出典：[run02-cad.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run02-cad.json)、[run04-cad.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run04-cad.json)、[run04-script.py](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run04-script.py)、[run05-cad.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run05-cad.json)。期待値として保存する数値と、今回読めたmeasurementsは別欄にする。未読取を期待値で埋めない。幾何の一致・直交判定はrun04のTOL=1e-6を出典付きで使い、bboxの許容と混同しない。体積の新しい理論式・許容範囲の数値は作らない。

Edge4等の番号を固定の正解にはしない。選択されたBase辺を実形状へ解決して検証し、生成側のselectedフラグに依存しない。Radius・Lengthはnative Quantity、Type/SideTypeは列挙文字列で読み、int(Pad.Type)やUnit表示の文字列一致を避ける。App::Pointを名前Origin001だけで除外しない。これはR3-S09/R3-S12/R4-S09/R4-S14/R5-S12の確認不一致を固定側で解消する提案。

## 4. CIM不使用と失敗の行き先

Get-CimInstance／WMIを呼ばず、ホスト識別は環境のホスト名、所有は起動ハンドルとworkerの実PIDで確認する。Get-Processが要る場合も自PIDだけの補助確認に限る。CIM拒否を回避するための権限変更・CAD再実行はない（R1-S05/R2-S03/R3-S03/R4-S03/R5-S10）。

launch失敗は既知Rule一致・未一致とも停止・人手。生成コードのbuild例外とProbeの述語不適合は短い差分JSONを返してSol向けとするだけで、このCLIからSolを呼ばない。固定Probeの例外、段・コード所有者不明、cleanup未完了は停止・人手。コード修正も再実行も自動化しない。

## 5. 警告・終了コード

stderrに文字があるだけでは失敗にしない（R4-S08）。Midplane等の既知警告は記録するが、CAD非0終了・worker例外・結果欠落・Probe不適合を警告へ読み替えない。CAD終了0でも、結果が欠けたらharness_failure、述語不適合ならprobe_failed。過去のFCStdが読めるだけで成功にはしない。

run02のone_sideとrun04のSideTypeは既存コードの参照になるが、警告を消す目的で生成スクリプトのCAD APIを自動書換えしない。警告をログへ残し、同じ意味で形状が読めたかは実際のProbeで確認する。

## 6. 復旧ダイアログ：検出して操作を止める

R1-S13の「ドキュメントの復旧」を既知題名とする。Windows標準APIを標準ライブラリのctypesから使う小さな検出器で、起動ハンドルが生存する間、その所有PIDに属するウィンドウ／ダイアログの題名だけを見る。ユーザーの他PIDの画面は対象にしない。GUI操作、画像入力、外部サービスは不要。

題名一致ならgui_blocked・人手対応を記録し、以後の自動操作を止める。CloseMainWindow、WM_CLOSE、kill/TerminateProcess等は送らず、timeoutも強制終了へ進めない。主試作はheadlessなので復旧画面を予防するが、題名検出でQtの当該画面を捕捉できるかは未確認。検出不能を「復旧画面なし」と断定せず、timeout・状態不明も人手へ渡す。実GUIを起動して検出器を試す追加CAD試験は今回の計画に足さない。

## 7. イベントログ：一行に一イベント

schema、cad_run_id、attempt_id、event_seq、timestamp_utc、recorded_at_utc、phase、event、status、code_owner、recipe_id、script_sha256、owned_pid、cad_exit_code、duration_ms、message_code、diagnostic、artifact_refを別フィールドにする。時刻・状態・メッセージを結合した文字列一つにしない。

親がpublicなevents.jsonlの唯一のwriterになる。workerのbuild/Probe/文書終了は専用の内部JSONLで伝え、親が一イベントずつ記録する。CADの出力・tracebackはstdout/stderrログへ分離する。開始、起動結果、build結果、Probe結果、cleanup結果、run終了を固定イベントで残し、モデルに進捗文を生成させない。

総時間は親の単調時計で直接測り、worker内のbuild/Probe区間は別の計測欄にする。発生時刻と親が保存した時刻を分け、入れ子区間を総時間へ再加算しない。純recompute、LLM think、tokensはこの試作では取得せずnull。ログ・返却文に秘密や個人パス、本文全文を含めず、artifactは相対パスで参照する。原形状の巨大なcad.json全文を返さない。

## 8. J1とmeasure_rollout.pyとの境界

J1は固定関数の無効スタブ。`enabled=false / invoked=false / decision=null / usage=null`だけを返し、§4の固定経路を使う。Q1/Q2の版・六ラベルは前回合意を参照しておけばよく、候補0.90/0.90を実行判定に使わない。キー読込・HTTP・SDK・対のフィクスチャ実呼出し・activeスイッチを作らない。

measure_rollout.pyと既存のreports/runs・outcomesスキーマは変更しない。cad_runは別schemaのsidecarとしてreports/cad-run配下に置く。必要ならrolloutのstemを相関IDに保持し、人手のoutcome notesから相対パスを参照する。script_ok/geometry_okの手記録は継続する。

理由は同モジュールのanalyze、_discover_task_dir、_normalize_report、_apply_metadataにある。再帰探索は配下のJSONLを入力にし、保存済み計測JSONはschema確認、outcomesはホワイトリストだけをマージする。events.jsonlをreports/runsへ入れるとCADイベントをCodexセッションと誤集計し得るため、入力を物理的に分離し、既存CLIへsidecarを渡さない。将来も測定は本物のrolloutを明示指定する。route=apiという既存分類も変更せず、cad_runのbackendと混同しない。

## 9. 最小テスト：CADなしの境界確認と、許可済みの二回だけ

PHASE 2は標準unittestと偽プロセス／worker結果による小表に留める。必要な境界は、警告＋CAD終了0を失敗にしない、非0終了を成功にしない、結果欠落・Probe不適合を成功にしない、他PID／ダイアログ停止で終了APIやJ1を呼ばない、eventsを既存計測入力へ混ぜないこと。これらは実CADの形状検証済みという証明には使わない。

PHASE 3はBRIEFどおりDPC-019の二回：上記の既知モデル作成処理を保持したコピーで一回、意図的にFilletを省いてPocketを最終形状にするコピーで一回。後者は実行できても、フィレット・体積・面の述語で拒否されることを確かめる。フィレット無しの22500 mm³・11面はrun02-cad.jsonのpocket.shapeにある既存参照値で、試験結果には実際に読んだ値だけを書く。壊したコピーは試験用出力域に置く。

良いケースでnative Probeが通り、悪いケースでfalseが出て、双方で結果・ログ・所有確認が揃うことを試作の受入条件にする。cmdが動かなければ未確認の起動障害として報告し、追加のGUI・レシピ試行やN=5を自動で増やさない。二回の確認はProbe全体の網羅性や性能改善の証明ではない。既存計測コードを変更しないため、その全面再試験も予定しない。

## 10. 実装者・配置・ブランチ・規模

実装者は**codex一名**。合意後に `proto/cad-run` ブランチで実装し、ローカルcommitのみ、pushなし。grok/claudeはdiffを一回レビューし、合意した修正をcodexが行う。今はブランチ作成・実装・CAD実行へ進まない。

以下は未実装・行数未計測の規模目安［推定］。

| 新規ファイル | 責任 | 行数目安 |
| --- | --- | ---: |
| tools/cad_run.py | CLI、固定launch、所有確認、停止、ログ、結果、J1スタブ | 約250 |
| tools/cad_run_freecad.py | build契約、新規文書、A専用Probe、保存・閉じる処理 | 約250 |
| tools/fixtures/cad_run_a_build.py | evidenceから準備する良い作成処理 | 約120 |
| tools/test_cad_run.py | CADなしの少数の境界テスト | 約80 |

新規四ファイル・計約700行を目安とし、説明は既存tools/README.mdへ約20行追加する程度。実行時artifactはこのコード規模に含めない。超える場合もフレームワーク化せず、GUI対応・AI評価・汎用スクリプト互換を後に回す。

前回から維持するのは本番(b)なし、固定Probe、停止・人手とSol向け失敗の分離、CIM不使用、人手outcome、C−B未計測。今回決める差分はファイル入力のbuild契約、二つの薄い実行層、新版の直呼びレシピ、A専用の実測参照値、独立したイベントログである。570,385msや94,261ms等は過去の対策対象区間の参照量［推定］のまま。本試作の速度・tokens・費用の削減予測には転用しない。
