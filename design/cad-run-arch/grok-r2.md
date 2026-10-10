# Grok R2 — 2者の最終立場

claude は不参加。合意は grok と codex の2者で作る。以下が R3 草案に入れる立場である。

## 1. スクリプト契約

実行単位は evidence と同じトップレベルの `.py` とする。`build(doc)` には包まない。

evidence のファイル自体は実行しない。`run05-script.py` は出力先を evidence ディレクトリに固定し、`run05-native.FCStd`、`run05-cad.json`、`run05-owned-pid.json` を書き、`App.closeDocument` で文書を閉じる。そのまま起動すると既存 evidence を上書きする。これは grok R1 の「そのまま実行」の欠陥である。

良いスモークは `run05-script.py` のコピーである。変えてよいのは attempt 内を指す4つのパス定数だけで、形状操作、寸法、辺選択、既存の try/except は残す。原本とコピーの sha256 を result に残す。コピーは attempt ディレクトリに置き、evidence と既存の reports ファイルは変更しない。

Probe はコピーが保存した FCStd を、cad_run が別に起動した所有プロセスで開く。スクリプトが書いた `checks`、`script_ok`、`geometry_ok` は判定に使わない。開き直しが `freecadcmd.exe` でできるかは未確認である。できなければその attempt は終了コード 6 で止め、console には切り替えない。

`build(doc)` を採らない理由は、記録された成功がトップレベルスクリプトの実行だからである。`run02-launch.json` は `FreeCAD.exe --console` に `run02-build.py` を渡している。BRIEF のスモークも既知スクリプトである。関数へ移植したコピーは、その経路の再現ではなくなる。

## 2. 終了コード

終了コードは 0/2/3/4/5/6 を維持する。result には同じ意味の `failed_phase` を必ず書く。コードだけ、または JSON だけでは経路が落ちる。

| code | failed_phase | 意味 |
|---|---|---|
| 0 | null | プロセス終了 0、FCStd あり、スクリプトエラーなし、Probe 述語が全部 true、所有プロセスの回収済み |
| 2 | launch または cleanup | CLI、実行ファイルなし、レシピ不一致、既知の起動 Rule、cfg 非対応、所有不明、回収失敗 |
| 3 | exec | プロセス終了が 0 以外、またはスクリプトがエラーを記録した、または FCStd が無い |
| 4 | probe | モデルは読めたが述語が false |
| 5 | dialog | 所有 PID の題名が「ドキュメントの復旧」。終了要求も強制終了も無し |
| 6 | probe | Probe 自身の例外、または FCStd を読めない。`probe_pass` は null |

`run05-script.py` は `script_ok` を false で初期化し、例外を捕捉して JSON を書き、再送出しない。プロセス終了 0 でも exec 失敗があり得る。終了コード 3 はこの形を含む。codex の 0/1/2 では、ダイアログ（人手）、Probe 例外（人手）、述語不適合（後で Sol 向け）が同じ 1 になる。経路表と合わない。

## 3. 後片付け

ユーザー条件に合わせ、cad_run が起動したプロセスだけを片付ける。ユーザーのプロセスは強制終了しない。

強制終了してよいのは、親が起動してハンドルを持つ PID だけであり、かつ題名が復旧ダイアログではないときだけである。名前で FreeCAD を列挙して止めない。プロセスが自分で終了していれば `TerminateProcess` は使わず、`cleanup_status` は exited とする。

所有が一致しない、またはハンドルを確認できないときは殺さない。`cleanup_status=cleanup_pending`、終了コード 2 で人手に渡す。ここは codex の停止を採る。

復旧ダイアログを見ている所有 PID は、タイムアウトでも殺さない。終了コード 5。ダイアログの無い所有 PID が残ったときだけ、その PID を終了する。一切強制終了しない案は、自分で起動したプロセスを放置する。

`--timeout-s` は呼び出し側の引数とし、合意の定数にはしない。evidence にタイムアウト秒数は無い。

## 4. 出力先

出力先は `reports/cad-run/<attempt_id>/` だけにする。空の新規ディレクトリ以外は拒否する。`reports/runs`、`reports/outcomes`、evidence ディレクトリの配下は拒否する。既存 reports の既存ファイルは変更しない。

任意の `--out-dir` は採らない。evidence を直接指せるからである。

`measure_rollout.py` の `--task-dir` は配下の全 `.jsonl` を入力にする（`_discover_task_dir`）。`events.jsonl` を `reports/runs` に置くと rollout と誤って読まれ得る。セッション側の探索は `rollout-*.jsonl` であり、こちらとは別である。cad_run の schema は `cad-harness.cad_run.v0` のまま、計測スキーマでは始めない。

## 5. 壊したスクリプト

Probe 不適合を示すのは、フィレットを省き、ポケットまでを最終形状として保存するコピーである。Pad 長さの変更は採らない。`run05-script.py` は上面 z=20 にポケットを付け、Pad の ZMax 20 を見ている。長さを変えると保存前に例外になりやすく、exec 失敗と述語失敗が混ざる。

フィレットをただ削除しただけでも、同スクリプトは `fillet` を参照したまま例外になり、`saveAs` は try の中なのでモデルが残らない。壊したコピーは、フィレット生成とそれを名指しする検査を外し、ポケット形状の `saveAs` は残す。差分を記録する。

その形状が `run02-cad.json` の `pocket.shape` と同じなら、読取は体積 22500.0 mm³、面数 11 である。これはフィレット前の既存参照であり、合格基準ではない。合格は runbook §6 のまま、体積は 22500 mm³ 未満かつ evidence の最終体積 22239.9556819442 mm³ の ±1%、面数は 15、外周フィレットは半径 3 である。±1% の展開値は資料に無いので計算結果を新しい出典にはしない。

スクリプト例外の経路も示す。PHASE 3 の CAD 起動は BRIEF どおり 2 回のままにする。例外経路は PHASE 2 の CAD なしフィクスチャで示す。入力は、プロセス終了 0、エラー文字列あり、FCStd なし。期待は終了コード 3 で、Probe を呼ばない。根拠は `run05-script.py` が例外を飲み込んでもプロセスが続き得ることである。

## 6. ファイル構成

3 ファイル、合計約 700 行を目安にする［推定。行数は未計測］。

- `tools/cad_run.py` 約 300 行。CLI、起動、パス定数の付替、回収、終了コード、イベント、J1 スタブ。
- `tools/cad_probe_abox.py` 約 250 行。FreeCAD に渡す課題 A の Probe。
- `tools/cad_run_test.py` 約 150 行。CAD を起動しないテスト。

`tools/fixtures/` に作成処理の再実装は置かない。`tools/README.md` は追記しない。入口は `cad_run.py` の argparse とする。README は `measure_rollout.py` の説明のまま残す。

## 7. freecadcmd が使えないとき

一致している。既定レシピは `freecadcmd`。失敗した attempt から `console` へ自動で切り替えない。人が次の起動で `--recipe console` を付けたときだけ、evidence と同じ `FreeCAD.exe --console` を使う。フラグ名は `--recipe freecadcmd|console` とする。

`freecadcmd.exe` で PartDesign、Sketcher、フィレット、FCStd の開き直しができるかは未確認のままである。evidence が示しているのは `FreeCAD.exe --console` で、`run02-cad.json` の `runtime.run_mode` は `Cmd`、`gui_up` は 0、`checks.console_no_gui` は true、最終体積と面数は下記のとおり、ということである。

## 8. イベントログのフィールド

全行が同じキーを持つ。値が無いキーは null。入れ子の `detail` は置かない。

`ts`, `attempt_id`, `event_seq`, `stage`, `event`, `status`, `owned_pid`, `cad_exit_code`, `recipe`, `script_sha256`, `message_code`, `artifact_basename`, `stderr_bytes`, `stderr_sha256`

`ts` は親が書いた UTC の1時刻だけにする。`duration_ms` は置かない。区間を足して総時間にしない。`stage` は `launch`、`exec`、`probe`、`cleanup`、`j1`。`event` は `launch_started`、`launch_finished`、`exec_finished`、`probe_finished`、`cleanup_finished`、`dialog_detected`、`j1_skipped`、`run_finished`。`status` は `ok`、`failed`、`pending`、`skipped`。`message_code` は短いトークンに限り、本文とフルパスと stderr 全文は置かない。`artifact_basename` はファイル名だけである。

## 9. CONSENSUS の起草と実装

R3 の `CONSENSUS.md` は grok が起草する。署名欄の codex 行は未署名のまま残し、grok は自分の行以外を後から埋めない。codex は `proto/cad-run` の実装者のままとする。ローカル commit のみ、push はしない。diff のレビューは grok が1回行う。

## 出典の確認

codex R1 の次の値は evidence と一致した。

- 最終体積 22239.9556819442、表面積 5364.637121611783、面数 15。`run02-cad.json`、`run04-cad.json`、`run05-cad.json` の measurements。表面積を合格条件にしないのは runbook §6 と一致する。
- フィレット前は `run02-cad.json` の `pocket.shape` が体積 22500.0、面数 11。最終ソリッドの値ではない。
- `run04-cad.json` の `pocket_inner_edges` は 12 本、各 `sharp` は true。内訳は開口 4（長さ 20 と 15、z=20）、縦 4（長さ 5、端点 z=20 と z=15）、底 4（長さ 20 と 15、z=15）。辺名は Edge20 以降で、合格条件に辺名は使わない。
- `run05-cad.json` は `sharp_top_edge_count` 4 と `sharp_bottom_edge_count` 4 だけを記録する。縦辺 4 はこのファイルには無い。12 本の出典は run04 である。
- runbook §6 の面数は文書時点では未固定。15 は上記 evidence の実読取を、その「1回測って固定」に当てたものである。
- 幾何の `TOL=1e-6` は `run04-script.py` と `run05-script.py`。bbox の ±0.1 mm は runbook §6。Probe は後者を外形許容にし、二つの許容を一つの数値へ合成しない。

grok R1 の内側検査は開口 4 辺だけだった。Probe は runbook の「内側エッジにフィレットが無い」に合わせ、run04 の 12 本を幾何で見る。標準 Origin 一式は追加フィーチャに数えない。所属の記録は `run04-cad.json` の `standard_body_auxiliaries` と、`run05-cad.json` の `Origin001`（`App::Point`）にある。

570,385 ms と 94,261 ms は前回の参照量［推定］のまま置く。この試作の所要時間には転用しない。
