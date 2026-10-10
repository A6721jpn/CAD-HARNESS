# Grok R1 — cad_run は3ファイルの試作

合意済みの `cad_run` を、標準ライブラリだけの小さな CLI にする。フレームワーク、Sol、J1 のネットワーク、N=5 は入れない。数値は runbook と evidence の引用だけを使い、無いものは未計測とする。

配置の目安は 3 ファイル、合計 1,100 行以内。

- `tools/cad_run.py` … 500 行以内。起動、ラップ、後片付け、終了コード、イベント。
- `tools/cad_probe_abox.py` … 350 行以内。課題 A の Probe だけ。
- `tools/cad_run_test.py` … 250 行以内。CAD を起動しない unittest。

`tools/measure_rollout.py` と `tools/README.md` は触らない。

## 1. CLI

スクリプト本文は引数に載せない。`--script PATH` で既存の `.py` を渡す。試作はファイルを attempt ディレクトリへコピーするだけで、中身は書き換えない。空の stdin は FreeCAD プロセスに渡す。Sol への本文受け渡しは、この試作の範囲外である。

```
python tools/cad_run.py --script PATH --out-dir PATH
    [--recipe freecadcmd|console] [--task A-box-pocket-fillet]
```

`--task` の既定かつ唯一の値は `A-box-pocket-fillet`。`--recipe` の既定は `freecadcmd`。失敗しても、もう一方へ自動で切り替えない。切替は人がフラグを変えた次の起動だけである。

各 attempt の出力は `--out-dir` だけに書く。

- `events.jsonl`
- `result.json`（schema `cad-harness.cad_run.v0`）
- `stderr.txt` / `stdout.txt`
- `owned-pid.json`
- スクリプトが保存した FCStd（コピー先の名前は attempt 内に固定）
- attempt 用の `user.cfg` と `system.cfg`

`result.json` は `probe_pass` と、プロセスが落ちずに FCStd を書いたかという `script_ran` を分ける。`geometry_ok` は常に null。`script_ok` は書かない。人手の outcomes 用の語と混ぜない。

終了コード:

| code | 意味 |
|---|---|
| 0 | FreeCAD の exit が 0 かつ Probe の述語が全部 true |
| 2 | launch / harness の失敗（レシピ不一致、実行ファイルが無い、Rule 上の既知の起動失敗） |
| 3 | FreeCAD の exit が 0 以外 |
| 4 | プロセスは完了したが Probe の述語が false |
| 5 | 復旧ダイアログを検出し、プロセスを止めずに戻った |
| 6 | Probe 自身の例外 |

標準出力は `result.json` の同じオブジェクトを 1 つだけ出す。進捗の文章は出さない。

## 2. 段

順は launch、実行、Probe、後片付け。GUI は試作の既定経路にしない。

launch は登録済みの 1 本だけを組む。`Start-Process` に環境辞書を渡さない。`.ps1` を実行しない。実行ポリシーは変えない。

- `freecadcmd`（既定）: BRIEF が優先すると書いた `bin/freecadcmd.exe`。引数に隔離 cfg を付けられるかは未確認。付けられないと分かった時点で exit 2 にし、別レシピへは進まない。
- `console`: evidence の `run02-launch.json` および `run05-launch.ps1` にある形。実行ファイルは `FreeCAD.exe`、引数は `--console`、`--user-cfg`、`--system-cfg`、スクリプトパス。stdin は空。`run02-launch.json` の `exit_code` は 0。

evidence でフィレットまで記録できているのは、後者である。`run02-cad.json` の `runtime.run_mode` は `Cmd`、`gui_up` は 0 だが、`executable` は `FreeCAD.exe` である。`freecadcmd.exe` で PartDesign、Sketcher、フィレットが同じ結果になるかは未確認。PHASE 3 の最初の 1 回でそれを見る。自動のフォールバックは作らない。

実行後、ハーネス所有のドライバがユーザースクリプトのあとで Probe を呼ぶ。evidence の `run02-build.py` や `run05-script.py` は測定まで自分で書いている。試作はそれを改変しない。スモークでは、そのスクリプトが書いた FCStd を Probe が開き直す。開き直せなければ `probe_pass` は null、終了コードは 6 ではなく 4 にもせず、result に `probe_error` を残して 6 とする（Probe が読めないのは述語の false と分ける）。

後片付けは、起動時に記録した PID だけを対象にする。その PID が残っていて、復旧ダイアログでなければ、その PID だけを終了する。他の FreeCAD は見ない。

## 3. CIM

`Get-CimInstance`、`Win32_Process`、CIM のクラス名をソースに置かない。プロセス確認は `Get-Process -Id` に所有 PID を渡すだけである。テストがソース文字列を見て CIM が無いことを確認する。

## 4. 警告と終了コード

ラッパは stderr を exit 1 に変えない。`'Midplane' property` の非推奨行は、`run03-attempt02-console.log` に出ている。その行は件数だけを `removed_warning_lines` に数え、成否を変えない。FreeCAD の exit が 0 以外なら、警告文があっても終了コード 3 のままである。成果物が読めることだけで成功にしない。

## 5. 復旧ダイアログ

所有 PID の窓題名に「ドキュメントの復旧」があるときだけ検出する。検出したら GUI を操作せず、通常の終了要求も送らず、強制終了もしない。`events.jsonl` に残し、終了コード 5 で戻る。コンソール経路では窓が無いことが evidence の `gui_up: 0` から想定されるが、freecadcmd で同じとは未確認。検出できなければ何もしない。他プロセスの題名は見ない。

## 6. イベントログ

`events.jsonl` は 1 イベント 1 行の JSON。フィールドは固定する。

`ts`, `attempt_id`, `stage`, `event`, `pid`, `exit_code`, `recipe`, `basename`, `detail`

`stage` は `launch`、`exec`、`probe`、`cleanup`、`j1`。本文、フルパス、stderr 全文、スクリプトは入れない。stderr はバイト数と sha256 だけを `exec_done` の `detail` に置く。

## 7. J1

`cad_run.py` 内の関数が `{"enabled": false, "called": false}` を返すだけにする。ソケットも HTTP も開かない。呼び出す箇所は、Rule に一致しない launch/build の直前で、戻り値は見ない。経路はコードの表だけに従う。launch の不一致は exit 2 で止まり、Sol も J1 も起動方法を書かない。

## 8. measure_rollout.py

変更しない。`cad_run` は `reports/runs` と `reports/outcomes` に書かない。schema は `cad-harness.cad_run.v0` とし、`cad-harness.measure_rollout` で始まらない。既存 CLI が読む rollout と outcomes の形はそのままである。試作の結果を計測 JSON にマージしない。人手の `geometry_ok` は、これまでどおり outcomes に書く。

## 9. テスト

PHASE 2 の自動テストは FreeCAD を起動しない。

- 終了コードの表が、exit 0 / 非 0、述語 true / false、Probe 例外、ダイアログ検出に対応する。
- 既知の Midplane 行だけでは exit 0 を失敗にしない。exit が非 0 のフィクスチャは 3 のまま。
- ダイアログ検出は終了 API を呼ばない。
- ソースに CIM の語が無い。
- J1 スタブが disabled を返し、ネットワーク名前がソースに無い。
- Probe の純関数に、evidence の数値をそのまま渡す。

PHASE 3 は DPC-019 で 2 回だけ。良いスクリプトは `reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/run05-script.py`。壊したスクリプトは、そのコピーの Pad 長さだけを変えたもの。N=5 も Sol も Fusion も SolidWorks もしない。`freecadcmd` がフィレットまで到達したかは、この 2 回の `result.json` で初めて記録する。到達しなければ exit 2 の記録で止め、自動では `--recipe console` にしない。

## 10. 実装

実装者は codex。ブランチは `proto/cad-run`。ローカル commit までで、push はしない。レビューは grok と claude が diff を 1 回ずつ見る。

## Probe が読む値

runbook §6 のチェックリスト（要求）:

- bbox は 40×30×20 mm、許容 ±0.1 mm
- 上面中央ポケットは 20×15 mm、深さ 5 mm、非貫通、垂直壁
- フィレット R=3 mm は上面外周 4 辺のみ
- ポケット内側エッジにフィレットは無い
- 追加フィーチャ無し、最終も単一ボディ
- 体積は 22500 mm³ より小さく、ゴールの ±1% 以内
- 面数はゴールを 1 回測って固定する、と runbook は書き、その文書の時点では未固定

ゴールとして使う記録は evidence の `run02-cad.json`、`run03-cad.json`、`run04-cad.json`、`run05-cad.json`。4 本とも次が同じである。

- `volume_mm3`: 22239.9556819442
- `face_count`: 15
- `solid_count`: 1
- `is_valid`: true
- bbox の `x_length` / `y_length` / `z_length`: 40.00000000000017 / 30.000000000000174 / 20.0
- フィレット半径 3.0。選択エッジの長さは 40 と 30 が各 2、頂点の z は 20
- ポケット底は z=15、20×15。垂直壁は 4。内側の鋭い上辺の長さは 20 と 15 が各 2

標準の Origin、軸、平面、`Origin001`（`App::Point`）は追加フィーチャに数えない。所属は `run04-cad.json` の `standard_body_auxiliaries` にある。

Probe の述語は、bbox を runbook の ±0.1 mm、体積を「22500 未満かつ evidence の体積の ±1%」、面数を evidence の 15、フィレットを半径 3 と外周 4 辺の幾何、内側を鋭い 4 辺、ソリッド数を 1、とする。±1% の展開値は資料に無いので、試作が計算し、result には evidence の体積と runbook の規則名だけを書く。新しいゴール数値は作らない。

`freecadcmd.exe` でこの Probe が同じ 15 面と体積を読むかは未確認。evidence が示しているのは、`FreeCAD.exe --console` で `run02-build.py` から `run05-script.py` までが上記の値を書いたことである。
