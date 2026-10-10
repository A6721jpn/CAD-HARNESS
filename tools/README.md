# measure_rollout

Codex の `rollout-*.jsonl` または保存済み計測 JSON から、壁時計時間、トークン、API/CU 経路を集計する標準ライブラリのみの CLI。プロンプト本文はレポートに出力しない。

規定タスク A（`A-box-pocket-fillet`）の CAD は 2026-10-03 約 18:29 JST のユーザー決定で DPC-019 の FreeCAD 1.1.4 である。実行ファイルは `C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\FreeCAD.exe`。LPC-017 は CAD ホストではない。手順は `docs/runbook-A-box-pocket-fillet.md` と `docs/measurement-slice-v0.md`。SolidWorks と Fusion 360 の経路は retired。この README は計測 CLI の説明であり、CAD GUI は起動しない。後述の `mcp__*fusion*` / `adsk` は分類コードが現在見ている文字列であり、コード自体はここでは変えない。


## 最小実行

```bat
cd C:\dev\CAD-HARNESS
python tools\measure_rollout.py --with-computer-use --out reports\latest.json
python tools\measure_rollout.py --latest --out reports\latest.json
python tools\measure_rollout.py --file %USERPROFILE%\.codex\sessions\...\rollout-....jsonl --out reports\one.json
```

探索先は `--sessions-dir` の明示指定を優先し、未指定なら `%CODEX_HOME%\sessions`、`CODEX_HOME` が未設定または空なら `%USERPROFILE%\.codex\sessions`（Windows 以外では `$HOME/.codex/sessions`）を使う。Orca のアカウント別ログも現在の `CODEX_HOME` から選ぶ。`--latest` は mtime が最新の rollout を選ぶ。`--with-computer-use` は任意の本文文字列ではなく、CU の tool call がある最新 rollout を選ぶ。

## 入力と集計

`--file PATH`、`--glob PATTERN` は複数指定できる。`--task-dir DIR` は配下を再帰的に探索し、rollout JSONL または保存済み個別計測 JSON を入力にする。複数入力時は集計し、単一入力でも `--aggregate` で集計モードを明示できる。

```bat
python tools\measure_rollout.py --glob "reports\runs\*.jsonl" --glob "reports\runs\*.json" --aggregate --out reports\aggregate.json --csv reports\aggregate.csv
python tools\measure_rollout.py --task-dir reports\runs --aggregate --out reports\aggregate.json
```

`--out` は JSON、`--csv` は CSV の保存先。集計時に `--csv` を省略すると、`--out` の隣に同名 `.csv` を出力する。集計 JSON は `runs` と `summary` を持ち、CSV には `wall_ms`、`tokens.session_delta.input/output/cached_input/cache_write/reasoning/total`、`route`、`script_ok`、`geometry_ok` と run を識別する項目を含める。

同じ source の rollout と保存済み JSON を重複指定しても 1 run として集計する。CSV の未取得値は空欄。保存済み JSON は計測時の token mode を維持し、`--token-mode` は JSONL の計測時に適用する。`session_delta` を持たない旧レポートは元の rollout から再計測する。

実際の流れは、rollout を `reports\runs` に計測保存し、同じ source stem の outcomes を手入力してから集計する。この README の更新ではその計測を実行しない。

```bat
python tools\measure_rollout.py --file %USERPROFILE%\.codex\sessions\...\rollout-a.jsonl --out reports\runs\rollout-a.json
```

`reports\outcomes\rollout-a.json`（`run_id=rollout-a`）:

```json
{"task_id":"A-box-pocket-fillet","script_ok":null,"geometry_ok":null,"notes":"手動記入"}
```

```bat
python tools\measure_rollout.py --file reports\runs\rollout-a.json --file reports\runs\rollout-b.json --aggregate --out reports\aggregate.json --csv reports\aggregate.csv
```

## 手動結果とオプション

```bat
python tools\measure_rollout.py --file PATH --task-id A-box-pocket-fillet --script-ok true --geometry-ok null --notes "フィレット確認待ち" --outcomes-dir reports\outcomes --out reports\one.json
```

利用できる主なオプションは次のとおり。

| オプション | 内容 |
| --- | --- |
| `--file PATH` | 入力ファイル。複数指定可 |
| `--glob PATTERN` | 入力 glob。複数指定可 |
| `--task-dir DIR` | rollout JSONL/個別計測 JSON を再帰探索 |
| `--aggregate` | 集計モードを強制 |
| `--out JSON` / `--csv CSV` | JSON/CSV 出力先 |
| `--sessions-dir DIR` / `--latest` / `--with-computer-use` | sessions 探索の指定 |
| `--task-id ID` | タスク識別子（例: `A-box-pocket-fillet`） |
| `--script-ok true\|false\|null` | スクリプト結果。`null` も明示値 |
| `--geometry-ok true\|false\|null` | geometry 結果。`null` も明示値 |
| `--notes TEXT` | 手動メモ。既存 notes に追加 |
| `--outcomes-dir DIR` | outcomes の場所。既定 `reports\outcomes` |
| `--token-mode auto\|cumulative_snapshot\|delta_sum\|single` | トークン集計方式 |

各 run の `run_id` は入力 source の stem。`reports/outcomes/<run_id>.json` を手入力すると、許可されたメタデータだけが計測結果にマージされる。CLI の明示値は outcomes より優先し、明示した `null` も上書き値として扱う。notes は追加される。

## レポートの読み方

`tokens.first`、`tokens.last`、`tokens.session_delta` はそれぞれ `input`、`output`、`cached_input`、`cache_write`、`reasoning`、`total` を持つ。互換用のフラットな token 値は `last` の値である。`tokens.mode` は `cumulative_snapshot`、`delta_sum`、`single` の実際の方式を示し、`auto` はヒューリスティックに選択する。`total_max_across_records` は選択した同一 token stream の各レコードにある `total` の最大値であり、異なる名前の stream や別カウンタを混ぜた最大値ではない。セッション増分でもない。

実トークン欄は `thread_token_usage` を優先し、per-call の `usage` は補助的に扱う。名前の異なる token stream は混在させず、取得できた範囲だけの部分的なカバレッジになり得る。文字数÷4 や画素数から推定しない。

`route` は `api`、`cu`、`cu_hybrid`。CU だけなら `cu`、CU と他のツールがあれば `cu_hybrid`、CU がなければ `api`。ツール名・プラグイン名を優先して分類し、Fusion/CAD API に類する `mcp__*fusion*`、`adsk` などは `cad_api` として記録する。これは分類実装の現状で、規定タスクの CAD ホスト（DPC-019 の FreeCAD 1.1.4）とは別である。コードはこの README 更新では変えていない。

壁時計はセッション全体の timestamp 差で、アイドル時間を含む。`cad_regen`、LLM think、tool RTT、screenshot encode は rollout から取得できないため `null`。最初に観測した累積 token 区間は `session_delta` に含まれない。`script_ok` と `geometry_ok`、CAD geometry、実コストは手動または別工程で扱う。

## cad_run 試作（課題Aのみ）

標準ライブラリの同期CLI。入力は信頼するUTF-8ファイルの `build(doc)` 契約。
FreeCAD 1.1.4の固定レシピで新規文書を作り、同じプロセスでProbe・保存・終了する。
既定は `freecadcmd`。不可でもconsoleやGUIへ自動切替しない。実CAD確認はPHASE 3。
```bat
python tools\cad_run.py --script tools\fixtures\cad_run_a_build.py --out-dir reports\cad-run\good-smoke --timeout-s N --recipe freecadcmd
```
`N` は実行者が指定する正の整数秒。合意済みの既定秒数はない。
`--out-dir` はreports/cad-run配下の未作成ディレクトリのみ。既存reportsは上書きしない。
結果はstdoutのJSON一つとresult.json。CAD出力は匿名化したstdout/stderrログへ分離する。
events.jsonlは一イベント一行。所有PID、段、状態、メッセージを別フィールドで記録する。
終了0＝実行・Probe・保存・自然終了が成功、1＝実行失敗／不適合／停止、2＝入力不備。
失敗の詳細はfailed_phase、probe_status、code_owner、next_actor、cleanup_statusに残す。
自分で起動したPIDだけを回収する。復旧画面・状態不明では操作せず人手へ返す。
良いfixtureはrun05由来。原本ハッシュ・除いた処理はfixture、入力コピーのハッシュはresultに記録。
悪いスモークはfixtureの新規コピーの末尾に `build = build_without_fillet` を付加して渡す。
CADなしのテスト：`python -B -m unittest tools.test_cad_run`。
J1は無効。Sol呼出し、自動修正、N=5、Fusion/SolidWorks対応は含めない。
結果をmeasure_rollout入力やoutcomesへ自動転記しない。設計はdesign/cad-run-arch/CONSENSUS.md。
