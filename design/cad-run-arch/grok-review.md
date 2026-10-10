# Grok review — proto/cad-run 839d97d

読んだのは `tools/cad_run.py`（363行）、`tools/cad_run_freecad.py`（255行）、`tools/fixtures/cad_run_a_build.py`（111行）、`tools/test_cad_run.py`（178行）、`tools/README.md` の cad_run 節（83–102行）。テスト実行、CAD 起動、ハッシュ再計算はしていない。

行数の合計は 4 本で 907 行。CONSENSUS §11 は約 700 行を目安とし、Probe と停止条件を削って行数に合わせることを禁じている。所有確認、匿名化、失敗経路のテストによる超過は、その条項の範囲である。

## 一致していること

- CIM、WMI、`Win32_Process`、ソケット、HTTP は 3 本の実装に無い。終了は `Popen.terminate`（Windows では起動ハンドル）だけで、名前による列挙は無い。
- `--out-dir` は `reports/cad-run/<id>` の未作成ディレクトリだけを受け、`reports/runs`、`reports/outcomes`、evidence、`..` を拒否する。計測 schema では始まらない。`measure_rollout` は呼ばない。
- 既定レシピは `freecadcmd`。欠落時に `console` へ切り替えない。
- 警告行 `'Midplane' property` は件数だけを増やし、終了 0 かつ述語 pass を失敗にしない。CAD の整数終了コードが 0 以外なら失敗のままである。
- `cleanup` は、ハンドルが無い、GuiUp が 0 以外、窓列挙が `no_windows` 以外、復旧ダイアログで `blocked`、のときは `terminate` を呼ばない。`WM_CLOSE` は無い。
- イベント行は §6 の 15 キーに固定され、`data` のキーは合意の 6 つに限られる。
- J1 は `enabled/invoked/decision/usage` が false/false/null/null の関数だけである。
- Probe は体積 22500 未満かつ 22239.9556819442 の ±1%、面数 15、単一 valid solid、外周 4 辺の幾何と半径 3、内側 12 本（開口 z=20、底 z=15、縦 4 隅）の sharp、Fillet を含むフィーチャ数を見る。±1% の展開値は保存していない。`geometry_ok` は null で、`script_ok` は無い。
- fixture に evidence へのパス、`saveAs`、`closeDocument`、JSON 書き込みは無い。形状操作は `run05-script.py` の Pad / Pocket / Fillet と同じ順序である。`build_without_fillet` は Tip を Pocket にする。

## must-fix

### 1. 一次失敗の next_actor が後段で人手に変わる

- 重大度: must-fix
- 場所: `tools/cad_run.py` 48–53行、316–321行。`tools/cad_run_freecad.py` 202–208行、220–223行
- 節: CONSENSUS §5「一次失敗をあとの段で消さない」、経路表の `predicate_fail → sol`、`probe exception → human`

`fail` は `failed_phase` が既にあるとき、後から渡された actor が human だと `next_actor` だけを human に置き換える。親は worker 結果をマージしたあとで、`cad_exit_code != 0` と cleanup 不完全と capture 不完全を、いずれも human の `fail` で足す。

`None != 0` も真である。プロセスがまだ回収されていないだけで、probe 不適合の `next_actor=sol` が human になる。`failed_phase` と `probe_status` は probe のまま残るので、JSON の3つが経路表と矛盾する。

worker 側も同じである。述語失敗を記録したあと `saveAs` が失敗すると、`except` が `failed_phase` を build に、`next_actor` を human に置き換える。`finally` は文書を閉じられないとき、既存の sol を human に置き換える。

修正: 最初の `failed_phase`、`probe_status`、`next_actor` を不変にする。後段は `cleanup_status` と `close_error_type` だけを足す。CAD 終了の追加失敗は、`cad_exit_code` が int でかつ 0 以外のときだけ、一次失敗がまだ無いときに入れる。未回収の None は cleanup の事実として残す。

## should-fix

### 2. 窓列挙の失敗が広すぎ、待ちを即座に打ち切る

- 重大度: should-fix
- 場所: `tools/cad_run.py` 141–159行、284–291行
- 節: §7 の「列挙に失敗したら終了しない」。失敗してよいのは所有 PID の検査に失敗したとき

`GetWindowThreadProcessId` がデスクトップ上の無関係な HWND で 0 を返すと、スキャン全体が `scan_failed` になる。待ちループは 50 ms 以内に `failed_phase=cleanup` で抜け、`blocked` になるため自分のプロセスを残したまま戻る。復旧ダイアログが無い headless の成功実行もここで止まれる。

修正: 失敗フラグは所有 PID の窓に限る。待ち中の `scan_failed` では break しない。timeout または終了時の cleanup で、その回の列挙に失敗していれば終了しない。

### 3. launch_finished を起動直後に ok で書く

- 重大度: should-fix
- 場所: `tools/cad_run.py` 253–263行
- 節: §6 の `launch_finished`

`Popen` の直後に `launch_finished/ok` を出している。実行ファイルがすぐ落ちても、イベント上は起動成功に見える。プロセスが worker の ready を出すか、終了コードが付くまで `pending` にし、結果が分かった行で `ok` か `failed` にする。

### 4. J1 の前に既知 Rule の照合が無い

- 重大度: should-fix
- 場所: `tools/cad_run.py` 35–36行、326–328行
- 節: §8。呼ぶ位置は、失敗を観測し、既知の起動 Rule と照合して一致しなかったとき

`judge_stub` の戻り値は捨てている。経路は変わらないので外部呼出しにはなっていない。ただし missing_executable 以外の launch 失敗は、Rule を持たないまま stub を呼ぶ。PATH、実行ポリシー、CIM という既知の3語に一致したら stub を呼ばず `message_code` をその Rule にし、一致しない launch 失敗だけ `j1_skipped` を出す、と §8 に合わせる。

### 5. preflight の理由が InputError に潰れる

- 重大度: should-fix
- 場所: `tools/cad_run.py` 227–228行、351–353行
- 節: §5 の exit 2。CAD は起動しない、という点は満たしている

`output_root` や `build_required` は `InputError` に置き換わり、stdout の `message_code` は `InputError` だけになる。exit 2 は維持し、`message_code` には元のトークン（`output_root`、`invalid_timeout`、`build_required`、`private_input`）を入れる。

## nit

### 6. 行数

- 重大度: nit
- 場所: 4 ファイル全体（363+255+111+178）
- 節: §11

目安の 700 行を超えている。§11 が、行数のために停止条件を削ることを禁じているため、この超過自体は差し戻し条件にしない。

### 7. README の成功条件の省略

- 重大度: nit
- 場所: `tools/README.md` 95–97行
- 節: §5、§7

終了 0 の説明が「実行・Probe・保存・自然終了」までで、述語が全部 true であることと、強制終了と timeout が無いことが文面に無い。97行の回収条件も、ハンドル、GuiUp、窓 0、復旧題名では終了しない、まで書いていない。実装の `cleanup` にはある。節の2文を §5 と §7 の条件に合わせる。

### 8. cleanup_status の語

- 重大度: nit
- 場所: `tools/cad_run.py` 182–184行
- 節: §7 は exited と cleanup_pending を使う

強制終了できたときの `cleanup_status` が `forced_own_headless_exit` である。操作名は `cleanup_action` に残し、状態は `cleanup_pending` 以外の終了済みであることが分かる語にすると、exit 0 の判定（316–319行が `exited` と `not_started` だけを成功側に見ている）と読み手が揃う。今の実装は、この語を exit 0 に含めていない。

### 9. Pad/Pocket の Type に "0" を許す

- 重大度: nit
- 場所: `tools/cad_run_freecad.py` 136–141行
- 節: §4。整数の Type や単位表示を一致条件にしない

`str(o.Type) in ("Length", "0")` は `run05-script.py` の `length_type` と同じである。fixture が `Type = 0` を置くのは原本どおりである。幾何（長さ 20 と 5、Pad の z 0..20）は別述語にある。列挙文字列 `Length` だけにすると、FreeCAD が 0 を返す実行で良いモデルを落とす。PHASE 3 で実際の `str(Type)` を見てから、`"0"` を残すか決めるのでよい。

## 確認済みで指摘にしないもの

- fixture の `SOURCE_SHA256` は、テストが原本バイトと照合する形になっている。このレビューではコマンドを動かしていないので、ダイジェストの一致は未計算である。
- `C:/dev/CAD/.tools/...` は BRIEF のツール配置であり、個人のホームパスではない。イベントと result には入れておらず、stderr の個人パスと `token=` 形式は行単位で落とす。
- 保存失敗の `next_actor` を human にする点は、worker が保存の所有者であるという §3 と、経路表が保存失敗を sol と書いている §5 の両方に触れる。一次失敗を消さない修正と一緒に、保存失敗は human（固定側の障害）、Body が返らない失敗は sol、と表を実装に合わせて読む。
