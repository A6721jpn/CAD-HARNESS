# EVAL-CONSENSUS: Sol にシェルを持たせない driver（2026-10-11）

課題 A の試作だけを決める。数値は BRIEF と既存 reports の引用である。改善幅は未計測。

## 1. 判定

- 案1 driver: go with changes。Sol は `build(doc)` のソースだけを返し、cad_run は driver が起動する。シェルと UAC を Sol から外す。変更は §2。
- 案2 一度だけのサンドボックス初期設定: 今回は no-go。run1 の翌日ではない同じ日に、run2 が marker 欠落から昇格 1223 で落ち、cad_run は 0 回だった。持続は未確認で、恒久否決ではない。
- 案3 bypass: no-go。承認と隔離を外す。フラグの範囲と 1223 を避けるかは未確認。
- 案4 読取調査: 今回は no-go。A の試作に仲介を付けない。Sol のシェルは戻さない。複雑課題の別条件として再評価できる。

## 2. 変更点リスト

両者の E2 の和である。

- 実装するのは案1の課題 A だけとする。
- 案2は、新しい子で初期設定が残った記録ができるまで実装しない。
- 案4は保留する。許可ファイルの抜粋も今回は作らない。
- exec は attempt ごとに独立する。resume は使わない。run 間で文脈を渡さない。
- usage は turn.completed の生の項目だけを残す。合計、引き算、cached や reasoning を足した料金、rollout との二重加算はしない。未取得は null。session_delta の 0 を使用量なしとしない。
- 記録に CLI 版、model、effort、設定、AGENTS の識別、prompt と source のハッシュ、セッション ID、開始終了、終了状態、最終 out-dir を含める。
- 初回に渡すのは runbook の形状仕様、build 契約、ホストと FreeCAD 1.1.4、許すモジュール、ハーネスが文書・Probe・保存・close を持つこと。API のコード例は足さない。fixture、evidence、他 run の解答、個人パスは渡さない。
- 修正時は直前ソース、実際の exit、取得済みの `failed_phase`、`probe_status`、`predicate_diff`、`next_actor`、`measurements`、`message_code`、`error_type`。無い例外文や実測は補わない。stderr 全文は渡さない。
- cad_run は初回を含め最大 3 回。直すのは `next_actor=sol` かつ文書が閉じ、所有プロセスが終了したときだけ。`cleanup_pending`、human、JSON 不正、未知の担当、launch、dialog、Probe 自身の例外は停止する。
- 診断が `error_type` だけで、述語差も measurements も無い build 失敗は人手で止める。
- 採る: 主時計は driver の開始から最終結果までとする。exec の時間と cad_run の時間は内訳であり、主時計に再び足さない。Sol の rollout 壁時計は主時計ではない。
- 採る: 複雑課題の前に、サニタイズした例外文と発生行を返す変更を別件で評価する。今回 cad_run の判定は変えない。
- 集計は新ファイル。10/05 と条件 B は参考比較。warm-up、停止 run、CAD 未到達を隠さない。

## 3. 実装仕様

新規は `tools/cad_agent.py` のみ。cad_run と `measure_rollout.py` は変えない。

呼出しは BRIEF の確認済み設定を attempt ごとに新規実行する。モデル gpt-6.1-sol、effort xhigh、shell_tool、unified_exec、code_mode_host、multi_agent、apps、plugins、browser_use、computer_use、image_generation、view_image を無効、`-s read-only`、空の作業ディレクトリ、`--json`、最終文をファイルへ出す。driver 自体は監督側の通常プロセスから起動し、Sol のシェルからは起動しない。

返答からソースを取る規則。最終文が `build(doc)` を定義する UTF-8 の Python であること。前後が一つのフェンスだけのときは中身をソースにする。Markdown の説明、コマンド、JSON イベント、警告行はソースにしない。空、構文エラー、`build` が無いものは呼出し失敗とし、cad_run を起動しない。

入力検査のあと、ソースをその run のディレクトリへ保存する。cad_run は次だけを使う。

```text
python tools/cad_run.py --script <そのrunの入力.py> --out-dir reports/cad-run/<run>/aN
  --timeout-s 300 --recipe freecadcmd --task A-box-pocket-fillet
```

`aN` は a1、a2、a3。既存ディレクトリは使わない。失敗しても console に切り替えない。

ループ。exit 0 かつ probe が pass なら終了する。上の修正条件を満たし、まだ 3 回未満なら再送する。それ以外は停止する。隠れた 4 回目はしない。

記録は `reports/cad-run/<run>/driver-run.json` と `events.jsonl` だけに足す。schema は `cad-harness.cad_agent.v0` と `cad-harness.cad_agent.event.v0` とし、`cad-harness.measure_rollout` では始めない。JSON には条件 B2、課題 A、主時計の開始と終了、内訳の exec 時間と cad_run 時間、attempt ごとの §2 の識別と生 usage、最終 exit、`failed_phase`、`probe_status` を入れる。`geometry_ok` は driver が決めず null のままにする。`script_ok` は書かない。events は 1 行 1 件で、`exec_started`、`exec_finished`、`cad_run_finished`、`repair_decided`、`run_finished` に限る。

出力は `reports/cad-run/<run>/` の配下だけである。`reports/runs`、`reports/outcomes`、既存 aggregate には書かない。計測 CLI に sidecar を渡さない。

テストは CAD なし。フェンスの除去、`build` 欠落、sol でも `cleanup_pending` なら停止、上限 3、usage を足さない、run 配下以外の出力を拒否、を見る。

行数は未計測の目安で、`cad_agent.py` 約 350 行、`tools/test_cad_agent.py` 約 150 行。

## 4. 比較の扱い

この試作の条件名は B2 とする。

参考比較に留めるもの。10/05 ベースラインは `reports/aggregate-A-box-pocket-fillet.json` の wall_ms_mean 489159.75 と session_delta total 2470906。条件 B の run1 は wall 284828 ms、session_delta 730858、cad_run 1 回成功。BRIEF の約 4 分の権限待ちを引いた値は作らない。run2 の wall 276874 ms、session_delta 393261、cad_run 0 回は成功集計から除かない。

B2 の N=5 が終わるまで、速度やトークンが減ったとは書かない。ping の 7 秒と、Sol 側で exec_command が無いことは、時短の証拠ではない。既存 aggregate は上書きしない。

## 5. 未確認

- resume が同一の使用量系列と無効化設定を保つか。
- turn.completed の usage が累積か、その turn の増分か。
- 無効化フラグだけで全ツールが止まり、長い生成でもサンドボックス準備が起きないか。
- `AGENTS.md` の読込を止められるか。
- bypass の実際の権限範囲。
- 初期設定マーカーがどの単位で再利用されるか。run1 の通過は run2 には効いていなかった。
- 最終文の受渡しと、CLI 異常時のログの形。

## 6. 署名

- grok: AGREE
- codex: AGREE
- claude: 不参加（組織設定で Claude Code 利用不可。opencode は資格情報 0、omp の opus 指定は Cloud Code Assist 404 で、他経路も不可）
