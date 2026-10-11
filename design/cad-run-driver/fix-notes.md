# cad_agent レビュー修正

対象: grok-review.md（08adc78 のレビュー）。proto/cad-run 上で対応。

- #1 must-fix: run・attempt ごとにリポジトリ外の新規 TemporaryDirectory を使用。TEMP がリポジトリ内なら実行せず停止。-C と cwd は同じ空ディレクトリとし、正常終了・例外の両方で回収する。絶対パスはメモリだけに保持し、記録・プロンプトには渡さない。パスを含む返答も CAD へ渡さず停止する。
- #2 should-fix: 回収済み・文書 close 済み・担当 sol の build/probe は cad_exit_code が整数なら非0でも修正対象にする。null・文字列・小数・bool は停止。成功判定では引き続き整数0を要求する。診断不足の build は人手停止。
- #3 should-fix: モックで freecadcmd、timeout 300、課題 A、console 不使用、-C/cwd がリポジトリ外であることを検証。wall_ms と exec_wall_ms/cad_run_wall_ms は別々に記録し、合計フィールドを追加していないことを検証。
- #4 nit: 値がすべて null の measurements は診断不足として停止。値0は取得済みとして扱う。
- #5 nit: 版の照会は変更なし。版の識別用で、失敗時は null。今回も呼出しはモックのみ。
- #6 nit: -o の生の最終文は外部一時領域で受ける。run 配下へは除去処理後の文だけ保存し、生の文が永続成果物へ先に書かれる手順を除いた。
- #7 nit: recompute の一文は build 契約の範囲なので変更なし。
- #8 nit: README は変更していない。指定するのは BRIEF の確認済み10フラグであり、全ツールの停止は未確認という合意の留保を維持する。実際の smoke は監督側で行う。

検証: python -B -m unittest tools.test_cad_run tools.test_cad_agent — 20件、全成功。CAD、Sol、codex exec は実行していない。cad_run.py、cad_run_freecad.py、measure_rollout.py は変更なし。テストは安全な再試行と作業先・ログの隔離を確認するために既存7件へ2件を追加した（driver 325行、テスト236行）。
