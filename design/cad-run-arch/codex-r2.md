# codex R2 — grokとの二者合意に向けた最終立場

[grok R1](grok-r1.md)、[codex R1](codex-r1.md)、[BRIEF](BRIEF.md)と指定evidenceを照合した。以下は設計の確定案であり、実装・CAD起動・計測は未実施。claudeは今回参加できないため、合意・レビューをgrokとcodexの二者で進める。

ファイル入力、固定launch、A専用native Probe、CIM不使用、J1無効、既存計測との分離では一致する。スクリプトは試験用のbuild契約へ包み、終了コードは簡潔に保つ。後片付けは今回のユーザー条件に従ってR1の立場を改訂する。

## 1. スクリプト契約：run05由来のbuild(doc)コピー

**build(doc)を採る。原本の種はgrok案のrun05へ合わせる。** [run05-script.py](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run05-script.py)のモデル作成部分を試験用コピーへ移し、寸法・CAD操作・辺選択を保つ。buildは渡された新規文書へ作成してBodyを返し、固定workerがrecompute、Probe、保存、文書終了を担当する。原本とコピーのハッシュ、契約化で変更した箇所を記録する。原本の自己判定はProbeの合否入力にしない。

「原本をコピーするだけで、出力はattempt内」は成立しない。原本はROOTを既存evidenceに固定し、NATIVE、RESULT、PID_PATHへ書く。コピー先やcwdを変えてもrun05-native.FCStd、run05-cad.json、run05-owned-pid.jsonを上書きする。実行後のFCStdコピーでは防げない。また、原本はExceptionを捕捉してerrorへ記録し、再送出しない。ソース例外とCADの終了コードを同一視できず、前回のFCStdを開き直す方式では残存成果物を採用する危険がある。

Probeは今回の新規文書・返されたBodyの実形状を同じ所有プロセス内で読み、今回のモデルだけを新規出力先へ保存する。保存不成功も実行失敗にする。開き直しの追加CAD経路は初版へ足さない。これは信頼するローカルPythonの契約であり、任意スクリプトのファイルアクセスを制限するサンドボックスではない。

## 2. 終了コード：0 / 1 / 2、詳細はJSON

**codex案を維持する。** 0はCAD終了0・build完了・Probe pass・保存とcleanup完了をすべて満たす場合。1は起動／実行の失敗、Probe不適合・例外、復旧停止、cleanup未完了。2はCLI入力・設定検証の不備とする。実行時のexe／オプション／ライブラリ障害はlaunch失敗として1で止める。

JSONのstatus、failed_phase、code_owner、next_actor、生のcad_exit_code、script_completed、probe_status、cleanup_statusで原因を分ける。Probe不適合とProbe自身の例外も別statusにする。build例外・述語不適合はSol向け情報を返すだけでSolを呼ばず、固定側の障害・launch未一致・状態不明は人手へ返す。一次失敗をcleanupの結果で消さない。

grokの細分は情報として残すが、終了コードへ全分類を載せる必要はない。stderrの存在や既知警告だけでは失敗にせず、CAD非0、worker例外、結果欠落を成功へ読み替えない。stdoutはresult.jsonと同内容のJSON一つにする。

## 3. 後片付け：確認済みの自分のheadlessプロセスだけ終了可能

**R1の「所有プロセスにも一切強制終了しない」は撤回する。** ユーザーが今回明示した条件は、自分が起動したプロセスだけを片付け、ユーザーのプロセスを強制終了しないこと。正常時はworkerが自分の文書を閉じ、親が自然終了を確認する。

残存時は、保持した起動ハンドル、worker実PIDとの一致、登録レシピ、GuiUp=0と所有PIDの窓検査によりheadless・復旧画面なしを確認できた場合に限り、その生存ハンドルだけを終了できる。待機上限は正の設定値を明示し、未計測の秒数を既定にしない。名前による一括終了、プロセスツリー終了、記録ファイルのPIDだけを根拠とする終了、CIM探索を行わない。

復旧画面を検出した場合、GUI状態・所有・検出結果が不明な場合は操作せずcleanup_pendingで人手へ返す。「題名一致がなかった」だけを強制終了の根拠にしない。復旧画面には通常の終了要求も送らない。Windowsのterminateは強制終了としてログに明記し、対象・要求・確認結果を分離する。強制終了やtimeoutが生じたrunを成功にしない。他のユーザーPIDは調査・終了対象にしない。

## 4. 出力先：reports/cad-run配下の新規ディレクトリに限定

**固定の出力ルートを採る。** --out-dirはreports/cad-run配下の新規runディレクトリだけを受け付け、attempt別にinput.py、隔離cfg、今回のmodel.FCStd、worker結果、result.json、events.jsonl、stdout/stderrログを置く。既存ディレクトリの再使用・上書きを拒否する。解決後のパスを確認し、親への遡及やリンク経由のルート外への書込みも拒否する。

任意出力先の汎用性より、既存reportsの保護と計測入力の分離を優先する。reports/runs、reports/outcomes、evidenceの既存ファイルは変更しない。measure_rollout.pyはJSONLを再帰探索するため、schemaの違いだけでは混入を防げない。cad_runのsidecarを既存計測CLIの入力に渡さず、人手outcomeへ自動転記しない。

## 5. 壊したスクリプト：Fillet省略、例外はCADなしで確認

**CADスモークの失敗例にはFillet省略を採る。** Pocketまで作り、Body.TipをPocketにしたコピーで、buildが完了しても固定Probeが拒否する経路を示す。[run02-cad.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run02-cad.json)のfeatures.pocket.shapeは22500 mm³・11面・validな単一solidで、最終参照の22239.9556819442 mm³・15面と異なる。新しい試験結果には実読取値だけを書く。

grokのPad長さだけの変更は、run05の上面探索がz=20固定で、見つからなければ「Pad top face was not unique」を送出する。外周辺選択もz=20固定である。したがって許容差を超える変更ではProbe到達前のbuild失敗になり得る［推定：ソース読取に基づく］。Probe不適合を分離する例としてはFillet省略が適する。

**スクリプト例外経路も示す。** 実際の固定workerの例外境界に対し、例外を送出するbuildと偽のApp／文書／Probeを使う最小テストで、build_failed、script_completed=false、Probe未実行、自文書の後片付け、CLI終了1を確認する。worker結果JSONを偽造するだけのテストにはしない。実CADはBRIEFの良いモデル・Probe不適合モデルの二回に留め、例外用の三回目は追加しない。CAD固有の例外挙動まで検証済みとは扱わない。

## 6. ファイル構成：四本、約700行を目安

**codexの四本構成を採る。** tools/cad_run.pyは親CLI・起動・所有確認・イベント・J1スタブ、tools/cad_run_freecad.pyは固定workerとA専用Probe、tools/fixtures/cad_run_a_build.pyはrun05由来のbuildコピー、tools/test_cad_run.pyはCADなしの必要な境界テストを担当する。

新規約700行、README追記約20行はR1からの規模目安［推定・未実装／未計測］。grokの三本・1100行という目安に算術誤りはないが、試験用コピーを独立ファイルとして可視化する方が原本保持と契約をレビューしやすい。行数を守るために必要なProbeや停止条件を省かない。余分なフレームワーク・GUI対応・互換変換は足さない。

PHASE 2ではtools/README.mdへcad_run専用の短い節を追記し、入力契約、出力制約、終了コードを説明する。既存measurementの説明・CLI・schemaは変えず、measure_rollout.pyは編集しない。今回はREADMEを含むコード・文書編集へ進まない。

## 7. freecadcmd不可時：停止、consoleへ自動切替しない

**一致している。** CLI名はgrok案の--recipe freecadcmd|consoleへ統一し、codex R1の--backend別名は作らない。--scriptによるUTF-8ファイル入力、Aだけの--task、明示の--timeout-sを使う。既定はBRIEF指定のfreecadcmd。不可なら失敗記録で停止し、GUI起動・起動方法生成・自動再実行をしない。

[run02-launch.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run02-launch.json)が証明するのはFreeCAD.exe --consoleとexit_code=0であり、run02-cad.jsonのruntimeがRunMode=Cmd、gui_up=0を補強する。freecadcmd.exe自体のオプション受理・DLL読込・同じフィレット結果は未確認。consoleは人が明示選択する別attemptで、許可済みCAD試験を自動で増やさない。新しいPython直呼びレシピは版を付け、既存PowerShell方式と同一の検証済み実装とは呼ばない。

## 8. イベントログ：一つの固定フィールド集合

**次の集合へ統一する。** schemaはcad-harness.cad_run.event.v0、結果はcad-harness.cad_run.v0とする。これは新設する設計識別子で、既存スキーマへの追加ではない。

`schema, cad_run_id, attempt_id, event_seq, timestamp_utc, recorded_at_utc, phase, event, status, code_owner, recipe_id, script_sha256, owned_pid, cad_exit_code, duration_ms, message_code, diagnostic, artifact_ref, data`

phaseはpreflight／launch／build／probe／cleanup／run。dataはイベント別の小さな構造化オブジェクトで、stderrのバイト数・ハッシュ・既知警告件数、Probeの述語差分、cleanup操作等を別キーで保持する。時刻・状態・長い文章をdetail一個へ連結しない。未知値はnull。artifact_refは相対パスだけとし、秘密・個人パス・本文全文・巨大なcad.jsonを入れない。

親だけが公開events.jsonlを書き、workerの内部通知をイベント単位で取り込む。CAD出力は別ログへ分離し、保存・返却前に秘密と個人パスを除去する。timestamp_utcは発生時刻、recorded_at_utcは親の保存時刻。総時間は親の単調時計から直接測り、build／Probeの入れ子区間を合算しない。LLM時間・tokensは未取得のままにする。

J1はenabled=false、invoked=false、decision=null、usage=nullの無効スタブだけ。位置は「失敗観測→既知Rule照合→未一致なら無効スタブ→固定の停止／返却」とし、実行前の判断にしない。judge_skippedをイベントとして残せるが、段の制御は変えない。ネットワーク、キー読込、activeスイッチは実装しない。

## 9. 合意草案と実装担当

**grokがCONSENSUS.mdを起草し、codexが実装する案に同意する。** 二者の最終署名後、codexがproto/cad-runで実装し、ローカルcommitまで、pushなし。grokがdiffを一回レビューし、合意した指摘をcodexが直す。claudeの署名・レビュー待ちは設けず、代替モデルにも委任しない。今回はcodex-r2.md以外を作成・変更しない。

## evidence照合で確定した修正点

- grokの最終体積22239.9556819442 mm³、15面、単一valid solid、bbox値はrun02〜run05の各measurementsと一致する。これらに数値誤りは見つからない。runbookのbbox許容±0.1 mm、体積±1%を維持し、未確認のfreecadcmd成功や改善量を主張しない。
- grokの「run02-cad.jsonのexecutable」は出典箇所が違う。executableはrun02-launch.json、run_modeとgui_upはrun02-cad.jsonのruntime。標準補助物の正確な場所はrun04-cad.jsonのfeature_measurements.standard_body_auxiliariesである。
- 「内側は鋭い上辺四本」だけでは、ポケット内側全体への非適用確認が不足する。run05は上辺四本と底辺四本を確認し、[run04-script.py](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run04-script.py)と[run04-cad.json](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run04-cad.json)は開口・底・縦辺の計12本を確認する。固定ProbeはR1の12本と、外周四辺だけのBase・半径・実形状の検証を維持する。辺番号やOrigin001という名前だけを正解にしない。
- [run03-attempt02-console.log](../../reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run03-attempt02-console.log)にはMidplane警告が実在するが、同じattemptにはAssertionErrorとscript_ok=false／geometry_ok=falseもある。「警告だけの成功例」には使えない。このログはUTF-16LEであり、資料照合ではそのエンコーディングで読んだ。警告単独の扱いはCADなしのテストで分離して確認する。

参照値は既存evidence、規模とPad変更時の挙動は明記した推定に限る。FreeCADCmdでの実行可能性、Probeの実測結果、処理時間・tokens・費用の改善は本ラウンドでは未確認である。
