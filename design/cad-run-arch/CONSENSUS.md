# CONSENSUS: cad_run 試作（grok 草案、2026-10-10）

二者は grok と codex。claude は組織設定で Claude Code を利用できないため不参加。数値は runbook と evidence の引用だけを使い、無いものは未確認とする。この文書は設計であり、実装も CAD 起動もまだ行っていない。

## 1. 結論

小さな同期 CLI を一つ作る。課題は `A-box-pocket-fillet` だけ。Sol、J1 の通信、自動再実行、N=5、GUI 操作は入れない。

残っていた4点は次の1案に決める。

(a) スクリプト契約は `build(doc)` とし、Probe は同じ所有プロセスで、今作った Body を読む。トップレベルのパス定数差し替えと、保存済み FCStd の開き直しは採らない。

評価: 未改変の `run05-script.py` は出力先を evidence に固定している。cwd だけを変えても `run05-native.FCStd`、`run05-cad.json`、`run05-owned-pid.json` を上書きする。4定数の差し替えはその上書き自体は避けられる。差し替え後も欠陥が残る。原本は `Exception` を捕捉して `error` に記録し、再送出しない。`script_ok` は false で始まる。プロセス終了 0 とソース例外は一致しない。開き直しは、今回の `build` が保存しなかったファイルを前回成果物として採用し得る。Probe がスクリプトの JSON を信じない方針とも衝突する。例外を JSON から推測すると、信じないと決めた出力を再び読むことになる。

`build(doc)` は渡された新規文書へ作成して Body を返す。文書の作成、recompute、Probe、保存、close は固定 worker が行う。原本の try/except、`saveAs`、`closeDocument`、evidence への JSON 書き込みはコピーに残さない。この差分は契約の変更としてハッシュと一緒に記録する。形状操作、寸法、辺選択は `run05-script.py` から持ってくる。これはサンドボックスではない。信頼するローカルの作成処理を、ファイルアクセスまで閉じ込めない。

記録された成功例は `FreeCAD.exe --console` にトップレベルスクリプトを渡した実行である（`run02-launch.json` の `exit_code` 0）。今回の fixture はその再実行そのものではない。

(b) 終了コードは 0 / 1 / 2。経路の細分は result の `failed_phase`、`probe_status`、`next_actor` に置く。0/2/3/4/5/6 は CLI の終了コードにしない。

(c) 新規ファイルは 4 本、合計約 700 行［推定。未計測］。`tools/README.md` には cad_run の節を約 20 行足す［推定］。既存の計測手順、計測 CLI、計測 schema の記述は変えない。

(d) イベントは §6 の1集合だけを使う。

## 2. CLI

```
python tools/cad_run.py --script PATH --out-dir reports/cad-run/<id>
    --timeout-s N --recipe freecadcmd|console --task A-box-pocket-fillet
```

- `--script` は UTF-8 のファイルパス。本文は argv に載せない。中身は `build(doc)` を持つ fixture であり、任意の `.py` を実行するランナーではない。
- `--task` の既定かつ唯一の値は `A-box-pocket-fillet`。
- `--recipe` の既定は `freecadcmd`。失敗しても `console` へ自動で切り替えない。人が次の起動で明示したときだけ別レシピになる。別名 `--backend` は作らない。
- `--timeout-s` は正の整数を毎回指定する。合意の既定秒数は置かない。evidence にタイムアウト秒数は無い。
- `--out-dir` は `reports/cad-run/` 配下の、まだ存在しない新規ディレクトリだけを受け付ける。既存ディレクトリ、中身のあるディレクトリ、`reports/runs`、`reports/outcomes`、evidence ディレクトリ、リンクや `..` でルートの外へ出るパスは拒否する。CAD は起動しない。
- 標準出力は `result.json` と同じ JSON を1つだけ出す。進捗の文章は出さない。CAD の stdout / stderr は別ファイルへ置く。

`result.json` の schema は `cad-harness.cad_run.v0`。フィールドは `schema`、`task_id`、`cad_run_id`、`attempt_id`、`recipe`、`script_sha256`、`source_sha256`、`status`、`failed_phase`、`code_owner`、`next_actor`、`cad_exit_code`、`script_completed`、`probe_pass`、`probe_status`、`geometry_ok`、`cleanup_status`、`removed_warning_lines`、`measurements`、`predicate_diff`、`timeout_s`、attempt 内相対パス。未取得は null。`geometry_ok` は常に null。`script_ok` は書かない。

## 3. 段とデータフロー

順は preflight、launch、build、Probe、保存、cleanup。GUI は試作の経路に入れない。

preflight が拒否したときはプロセスを作らない。

launch は登録済みレシピを1本だけ組む。Python の subprocess で実行ファイルと引数配列を渡す。shell、`.ps1`、`Start-Process` の環境辞書、実行ポリシーの変更、PATH の探索はしない。親の環境は継承する。試行別の `user.cfg` と `system.cfg`、空の stdin、専用の cwd を使う。この直呼びは新しいレシピであり、既存の PowerShell 起動と同一の検証済み実装とは呼ばない。

- `freecadcmd`: BRIEF が優先する `bin/freecadcmd.exe`。隔離 cfg を受け付けるかは未確認。受け付けないと分かった attempt は launch 失敗で止める。
- `console`: evidence の引数の形。実行ファイルは `FreeCAD.exe`、引数は `--console`、`--user-cfg`、`--system-cfg`、worker。`run02-launch.json` の `exit_code` は 0。`run02-cad.json` の `runtime.run_mode` は `Cmd`、`gui_up` は 0、`checks.console_no_gui` は true。`executable` の出典は `run02-launch.json` である。

`freecadcmd.exe` で PartDesign、Sketcher、フィレットが同じ結果になるかは未確認。PHASE 3 の最初の1回で記録する。届かなければ失敗として止め、自動では `--recipe console` にしない。

worker（`tools/cad_run_freecad.py`）は親が起動したプロセスの中で動く。

1. 空の文書一覧を確認し、新規文書を作る。
2. `build(doc)` を呼ぶ。返った Body がその文書に属することを確認する。
3. recompute のあと、同じプロセスで Probe をその Body に対して実行する。
4. 今回の文書だけを attempt 内の `model.FCStd` へ保存し、その文書を閉じる。
5. 例外は飲み込まれない。build が例外を出したら Probe は呼ばず、保存もしない。evidence や前回 attempt の FCStd は開かない。出力ディレクトリは開始時に空なので、残存ファイルを探す処理は持たない。

親だけが公開 `events.jsonl` と `result.json` を書く。worker の通知は親が1イベントずつ取り込む。一次失敗は、その後の cleanup の結果で成功に書き換えない。

CIM は使わない。`Get-CimInstance`、`Win32_Process`、WMI、CIM のクラス名をソースに置かない。プロセスの確認は、親が保持する起動ハンドルと、その PID に限る。名前で FreeCAD を列挙しない。

## 4. Probe の述語

FreeCAD 上の Body / Shape を読む。ホストが既存 cad.json の true を写して pass にはしない。辺の名前と `Origin001` という名前だけでは判定しない。`int(Pad.Type)` や単位表示の文字列一致は使わない。Radius と Length は Quantity として読む。

bbox の許容は runbook §6 の ±0.1 mm。スクリプトの `TOL=1e-6`（`run04-script.py`、`run05-script.py`）は直交と長さの近さにだけ使い、±0.1 mm と一つの帯に合成しない。体積の ±1% を展開した新しい数値は作らない。result には evidence の体積と規則名、および今回読んだ値を書く。

| 述語 | 期待 | 出典 |
|---|---|---|
| 外形 | 40×30×20 mm、許容 ±0.1 mm | runbook §6。実読取の長さは `run02-cad.json` ほか最終 measurements の 40.00000000000017 / 30.000000000000174 / 20.0 |
| ポケット | 上面中央 20×15 mm、深さ 5 mm、非貫通、底 z=15、垂直壁 4 | runbook §6。底と壁の実読取は `run04-cad.json` と `run05-cad.json` の pocket measurements |
| 体積 | 22500 mm³ 未満、かつ最終実読取 22239.9556819442 mm³ の ±1% | runbook §6。体積の出典は `run02-cad.json`、`run04-cad.json`、`run05-cad.json` |
| 面とソリッド | 面数 15、単一 Body、単一の valid solid | 同じ3ファイルの measurements（`face_count` 15、`solid_count` 1、`is_valid` true）。runbook §6 は面数を文書時点では未固定とし、ゴールを1回測って固定すると書いている。15 はその実読取 |
| 表面積 | 合格条件にしない。読めたときだけ記録する | runbook §6。記録値 5364.637121611783 mm² は同じ measurements |
| 外周フィレット | 半径 3 mm、対象は上面外周の異なる4辺だけ。ポケットを Base とし、`UseAllEdges` は許さない。辺の端点、直線、外周座標で見る | runbook §6。`run04-cad.json` の選択辺は長さ 40 と 30 が各2、z=20。辺名は固定しない |
| 内側にフィレットが無い | 開口4（長さ 20 と 15、z=20）、縦4（長さ 5、端点 z=20 と z=15）、底4（長さ 20 と 15、z=15）。12本とも sharp、隣接平面の法線は直交 | runbook §6 の「内側エッジにフィレットが無い」。12本の実読取は `run04-cad.json` の `pocket_inner_edges`。`run05-cad.json` は開口4と底4だけ（`sharp_top_edge_count` 4、`sharp_bottom_edge_count` 4）で、縦4の出典にはしない |
| 余分なフィーチャが無い | 要求した Sketch、Pad、Sketch、Pocket、Fillet の型と所属だけ。標準の Origin、軸、平面、`App::Point` は実体と親関係で除外する | `run04-cad.json` の `standard_body_auxiliaries`。`run05-cad.json` にも `Origin001` が `App::Point` としてある |

フィレットを省いた失敗例が、ポケットまでの形状として `run02-cad.json` の `pocket.shape` と一致するなら、その既存参照は体積 22500.0 mm³、面数 11、単一の valid solid である。これは合格値ではない。PHASE 3 の結果には、その回に読んだ値だけを書く。

警告: stderr に文字があるだけでは失敗にしない。`'Midplane' property` の既知行は `removed_warning_lines` に数え、成否を変えない。`run03-attempt02-console.log` にはその警告があるが、同じ attempt に失敗した検査もある。警告だけの成功例としては使わない。警告だけの扱いは CAD なしのテストで見る。CAD の終了が 0 以外のとき、成果物が読めることでは成功にしない。警告を消すために生成スクリプトの API を書き換えない。

## 5. 終了コードと経路

| exit | いつ | failed_phase | probe_status | next_actor |
|---|---|---|---|---|
| 0 | CAD 終了 0、build 完了、保存完了、述語が全部 true、cleanup が exited または reaped 以外の成功確認済み。強制終了も timeout も無い | null | pass | null |
| 2 | 引数、レシピ名、出力パス、`timeout-s` の不備。CAD は未起動 | preflight | not_run | human |
| 1 | 次行以降 | 下表 | 下表 | 下表 |

exit 1 の内訳は JSON で分ける。一次失敗をあとの段で消さない。

| 状況 | failed_phase | probe_status | next_actor | cleanup |
|---|---|---|---|---|
| 実行ファイルが無い、cfg 非対応、起動 Rule の一致または未一致、DLL や起動直後の失敗 | launch | not_run | human | 起動していれば §7。Sol に起動方法を書かせない |
| build の例外、Body が返らない、保存失敗 | build | not_run | sol | 自プロセスだけ §7。この CLI から Sol は呼ばない |
| モデルは読め、述語が false | probe | predicate_fail | sol | 同上 |
| Probe 自身の例外 | probe | exception | human | 同上。`probe_pass` は null |
| 所有 PID に「ドキュメントの復旧」 | dialog | not_run または中断時点 | human | 終了要求も強制終了もしない |
| 所有不明、窓検査の失敗、回収できない | cleanup | それまでの値 | human | `cleanup_pending`。成功にはしない |

`script_completed` は、`build` が Body を返し、worker が今回の文書を保存できたときだけ true。既知の Midplane 行だけでは 0 を 1 にしない。

stdout の JSON と `result.json` は同じオブジェクトである。

## 6. イベントログ

公開ファイルは attempt 内の `events.jsonl`。1行に1イベント。書き手は親だけ。schema は `cad-harness.cad_run.event.v0`。

全行が同じキーを持つ。未知の値は null。

`schema`, `cad_run_id`, `attempt_id`, `event_seq`, `ts`, `phase`, `event`, `status`, `recipe`, `script_sha256`, `owned_pid`, `cad_exit_code`, `message_code`, `artifact_rel`, `data`

- `ts` は親が書いた UTC の1時刻。発生時刻との対や `duration_ms` は置かない。build と Probe の区間を足して総時間にしない。
- `phase` は `preflight`、`launch`、`build`、`probe`、`cleanup`、`j1`、`run`。
- `event` は `preflight_finished`、`launch_started`、`launch_finished`、`build_finished`、`probe_finished`、`cleanup_finished`、`dialog_detected`、`j1_skipped`、`run_finished`。
- `status` は `ok`、`failed`、`pending`、`skipped`。
- `message_code` は短いトークン。文章、スクリプト本文、stderr 全文、絶対パスは入れない。
- `artifact_rel` は attempt ディレクトリからの相対パス、または null。
- `data` はイベント種別ごとのオブジェクト。キーは `stderr_bytes`、`stderr_sha256`、`removed_warning_lines`、`predicate`、`cleanup_action`、`window_scan` に限る。文字列一つへ連結しない。

CAD の出力は stdout / stderr ファイルへ分離する。秘密と個人のパスは残さない。トークンと LLM 時間は取得せず null のままにする。

## 7. cleanup

ユーザーのプロセスは調査も終了もしない。名前による一括終了、プロセスツリーの一括終了、CIM、ファイルに書かれた PID だけを根拠にした終了はしない。

自然に終了した所有プロセスは `cleanup_status=exited` とし、`TerminateProcess` は使わない。

強制終了してよいのは、次をすべて満たすときだけである。

1. 親が、自分で起動したプロセスのハンドルをまだ持っている。
2. 終了対象がそのハンドルの PID である。
3. worker が GuiUp を報告している場合、その値は 0 である。報告が無いときは、この項だけでは終了しない代わりに、次項の窓検査で判断する。
4. その PID の窓の列挙に成功し、窓が一つも無く、「ドキュメントの復旧」も無い。

題名が復旧ダイアログである、列挙に失敗した、別の窓がある、ハンドルが無い、GuiUp の報告が 0 以外である、のいずれでも終了しない。`cleanup_status=cleanup_pending` で人手に渡す。通常の終了要求（CloseMainWindow、WM_CLOSE）も送らない。

timeout は指定された `--timeout-s` で同じ規則に入る。強制終了または timeout があった run は exit 0 にしない。強制終了したときは、対象 PID、操作、窓検査の結果を別フィールドで残す。

## 8. J1

`cad_run.py` 内の関数が `enabled=false`、`invoked=false`、`decision=null`、`usage=null` を返すだけにする。ソケット、HTTP、SDK、鍵の読込、active の切替は作らない。

呼ぶ位置は、失敗を観測し、既知の起動 Rule と照合したあと、一致しなかったときである。戻り値は経路を変えない。起動の不一致は人手で止める。候補の 0.90 / 0.90 は使わない。Q1 / Q2 の文面は前回の合意を参照するだけで、この試作は送らない。

## 9. measure_rollout.py との境界

`tools/measure_rollout.py` は変更しない。`reports/runs` と `reports/outcomes` には書かない。schema `cad-harness.cad_run.v0` と `cad-harness.cad_run.event.v0` は `cad-harness.measure_rollout` で始まらない。

`--task-dir` は配下の全 `.jsonl` を入力にする（`_discover_task_dir`）。schema が違うだけでは、`events.jsonl` を計測入力へ渡したときの混入を防げない。sidecar を計測 CLI に渡さない。人手の `geometry_ok` は、これまでどおり outcomes に書く。cad_run の結果を計測 JSON へマージしない。`route=api` という既存分類は変えない。

## 10. テスト

PHASE 2 は CAD を起動しない。

- preflight の拒否は exit 2 で、プロセスを作らない。
- 例外を送出する `build` と、偽の App、文書、Probe で worker の境界を通す。終了は 1、`failed_phase=build`、`script_completed=false`、Probe 未実行。worker 結果 JSON を親に渡すだけのテストでは、この境界を通過したことにしない。
- 述語関数へ evidence の数値をそのまま渡す。最終体積 22239.9556819442、面数 15、12本の sharp は pass 側。22500.0 と面数 11 は pass にしない。
- Midplane の警告行だけでは、CAD 終了 0 かつ述語 pass のフィクスチャを失敗にしない。終了が 0 以外のフィクスチャは成功にしない。
- 復旧ダイアログ、所有不明、窓検査の失敗では終了 API を呼ばない。
- ソースに CIM の語とネットワークの名前が無い。J1 スタブは disabled を返す。
- `events.jsonl` を計測用ディレクトリの入力に混ぜない。

PHASE 3 は DPC-019 で FreeCAD 1.1.4 を2回だけ使う。

1. `run05-script.py` 由来の良い `build`。
2. 同じ作成処理から Fillet を省き、Tip を Pocket にした `build`。build は完了し、Probe が体積、面数、フィレットの述語で拒否する。

Pad 長さの変更は、上面の探索が z=20 固定であるため、Probe の前に build が失敗し得る。Probe 不適合の例には使わない。スクリプト例外の3回目の CAD 起動はしない。Fusion と SolidWorks は起動しない。N=5 と Sol のロールアウトはしない。

受入は、良い回が exit 0 かつ `probe_status=pass`、悪い回が exit 1 かつ `probe_status=predicate_fail`、両方で result、events、所有の確認が揃うこと。これは Probe の網羅や所要時間の証明ではない。`freecadcmd` がフィレットまで到達しなければ、その失敗を記録して止める。

前回合意の 570,385 ms と 94,261 ms は参照量［推定］のままである。この試作の時間、トークン、費用の予測には使わない。

## 11. ファイルと行数

実装者は codex。ブランチは `proto/cad-run`。ローカル commit までとし、push はしない。grok が diff を1回レビューし、合意した指摘を codex が直す。claude のレビュー待ちは設けない。PHASE 1 のこの草案では、ブランチ作成と実装に進まない。

| ファイル | 責任 | 行数［推定・未計測］ |
|---|---|---|
| `tools/cad_run.py` | CLI、preflight、launch、所有、終了コード、イベント、J1 スタブ | 約 250 |
| `tools/cad_run_freecad.py` | 新規文書、`build` 呼び出し、A の Probe、保存と close | 約 250 |
| `tools/fixtures/cad_run_a_build.py` | `run05-script.py` 由来の良い `build` と、Fillet を省いた `build` | 約 160 |
| `tools/test_cad_run.py` | CAD なしの境界テスト | 約 80 |

合計約 700 行を目安にする［推定］。超えてもフレームワーク、GUI 対応、任意スクリプト互換は足さない。行数を守るために Probe や停止条件を削らない。

`tools/README.md` には、入力契約、出力が `reports/cad-run/` に限られること、終了コード 0/1/2 を説明する節を約 20 行追加する［推定］。計測の説明は編集しない。`tools/measure_rollout.py` は編集しない。

fixture には原本 `run05-script.py` の sha256、コピーの sha256、契約化で除いたもの（例外の飲み込み、evidence への保存と JSON、文書の close）を残す。

## 12. 未解決

設計の分岐 (a)〜(d) は本文で1案に決めた。次は分岐ではなく、PHASE 3 まで未確認の事実である。

- `bin/freecadcmd.exe` が隔離 cfg を受け付けるか、PartDesign のフィレットまで到達するか、同じ体積と15面を読むか。
- headless の所有 PID で復旧ダイアログの題名を実際に観測できるか。主経路は headless であり、検出器を試す追加の GUI 起動はこの計画に含めない。
- `--timeout-s` の運用秒数。呼び出しごとに指定し、この合意は数値を持たない。
- Midplane の代替プロパティ名。Probe は警告行を失敗にしない範囲で扱い、名前の置換はしない。

## 13. 署名

- grok: AGREE（grok-r3.md 相当の理由は本文）
- codex: AGREE（codex-final.md）
- claude: 不参加（組織設定で Claude Code 利用不可）
