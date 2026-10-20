# h2-mvp 仕様（リード h2lead、2026-10-21 00:10 JST）

設計入力: docs/h2-consultation-20261020/conclusion.md（10/20 三者協議）。実現性・整合・リスクの 3 基準で
全員一致の第一候補は **LIBRARY_ONLY**。したがって MVP は「実行ハーネスは毎回ベースから始め、経験はドメイン別
ライブラリにだけ残す」。ベースハーネスへの自動の永続化（DP 系）は MVP に入れない。
DP_GATED_ABLATION（期待効果・測りやすさで首位）は将来拡張とし、そのために記録の形だけを揃えておく。

v4（tools/cad_verify_v4_*、skills/cad-harness-v4）とは別の設計。v4 のコードは import も変更もしない。
再利用してよい既存部品は次の 2 つだけで、どちらも変更しない。
- `tools/cad_run.py`（FreeCAD 1.1.4 freecadcmd の同期ランナー。結果 JSON を stdout に出す）
- `tools/cad_run_probes.py`（タスク A の AI 不使用形状プローブ。cad_run が呼ぶ）

## 1. 合格条件（ユーザー指定）
1. 規定タスク A-box-pocket-fillet で「実行 → 改善案を複数出す → 同じタスクで試す → 比べて合成 → 教訓を保存」
   が 1 周（k=1）、1 コマンドで自動に回る。
2. 合否は AI 不使用の形状チェック（cad_run の probe_status == "pass"）で出る。
3. LLM 呼び出しごとのトークン数と、各段階・全体の時間が記録される。

## 2. 置き場所
- `h2/` 新規ディレクトリ（コード）。`h2/base/harness.json`（ベースハーネス、ループが書き換えない）、
  `h2/tasks/A-box-pocket-fillet.json`（依頼文。runbook-A §1 の形状仕様だけを写す。CLI 手順は書かない）、
  `h2/library/cad-freecad.jsonl`（ドメインライブラリ、追記のみ）。
- 実行出力: `reports/cad-run/h2/<cycle_id>/...`（cad_run の out-dir 制約により reports/cad-run 配下）。
  サイクルの要約は `reports/h2/<cycle_id>/cycle.json`。
- テスト: `h2/tests/`（LLM と FreeCAD を呼ばない単体テスト。stub executor で 1 周を通す）。

## 3. ハーネスの表現（編集可能な面）
ハーネスは JSON 1 つ。例:
```json
{"id":"base-v0","executor":{"model":null,"reasoning_effort":"low"},
 "rules":["..."], "snippets":["..."], "max_attempts":3,
 "feedback_fields":["status","failed_phase","probe_status","predicate_diff","message_code"]}
```
改善案（edit）は構造化した操作のリストに限る: `add_rule`、`add_snippet`、`set_max_attempts`（1〜4）、
`set_feedback_fields`、`set_reasoning_effort`（low/medium）。任意コードの差し込みは不可。
これで編集同士の合成と衝突検出が機械的にできる。

## 4. 実行（execute）
- 実行エージェントは `codex exec --json --sandbox read-only --skip-git-repo-check`（-C は空の作業 dir）。
  ファイルは書かせない。最終メッセージに `build(doc)` を定義した Python を 1 ブロックで返させ、
  オーケストレータが `reports/cad-run/h2/<cycle>/<variant>/inputs/a<n>-build.py` に保存し、
  `python tools/cad_run.py --script ... --out-dir reports/cad-run/h2/<cycle>/<variant>/a<n> --timeout-s 300 --recipe freecadcmd`
  を実行する。
- 失敗時は harness.feedback_fields で選んだ結果 JSON の項目と前回コードを渡して再依頼（新しい exec 呼び出し）。
  max_attempts で打ち切る。cad_run の next_actor が human なら打ち切り。
- 実行エージェントには tools/fixtures、既存 reports、v4 を読まないよう依頼文で指示する。
- トークン: `--json` のイベント（turn.completed の usage）から input / cached_input / output / reasoning / total を
  呼び出しごとに取得。取れなければ null（推定値で埋めない）。時間: 呼び出しごと・cad_run ごとの wall_ms。

## 5. 1 周（k=1）の流れ — `python -m h2.cycle --task A-box-pocket-fillet --candidates 3`
1. **Run0**: base ハーネスで実行（ライブラリは使わない。ベースは毎回同じ）。
2. **Propose**: 提案エージェント（codex exec、medium）に Run0 の痕跡要約（各 attempt の結果項目、
   attempts 数、トークン、時間、最終コードの要旨）と、ライブラリの**この run より前の**エントリを渡し、
   互いに異なる edit を `--candidates` 個（既定 3）JSON で出させる。スキーマ検証し、不正なら 1 回だけ再依頼。
3. **Probe**: 各候補 = base + edit_i を同じタスク・同じ条件で 1 回ずつ実行（順番に。FreeCAD は同時 1 つ）。
4. **Compose**（決定的、AI 不使用）: 各候補を Run0 と対比。
   順位は (形状 pass) > (attempts 少) > (total tokens 少) > (wall 短)。
   「支持あり」= pass で、かつ Run0 より 1 つ以上の指標で厳密に良く、他の指標で悪化していない
   （トークン・時間は ±10% を同等とみなす）。支持ありの edit だけを合成。衝突（同じスカラー設定の別値）は
   上位を採る。合成ハーネスで確認 run を 1 回行い、pass でなければ単独最上位の edit だけに戻す。
   支持ありが 0 件なら合成なし（base を採用）。
5. **Library**: 各 edit について 1 エントリを追記:
   `{entry_id, domain:"cad-freecad", task_id, cycle_id, created_at, edit, verdict: supported|unsupported|confounded,
     contrast:{run0:{...}, probe:{...}}, lesson: "いつ・なぜ効いた/効かなかったか（1〜2 文）", adopted_in_composed: bool}`。
   lesson は提案時の rationale と測定差から作る（LLM を追加で呼ばないなら定型文でよい）。
   合成ハーネスそのものはベースに書き戻さない。
6. `reports/h2/<cycle_id>/cycle.json` に全段の結果、各 run の geometry pass、LLM 呼び出しごとのトークン、
   段階ごとの wall_ms、合計を書く。標準出力に 1 行要約。

## 6. 予算と安全
- 1 周の LLM 呼び出し上限を設ける（既定 20）。超えたら止めて cycle.json に記録。
- ネットワーク・権限の拡大はしない。CAD は FreeCAD 1.1.4（cad_run 経由）だけ。
- 実行エージェント・提案エージェントのプロンプト本文はログに残してよいが reports/h2 配下だけ。

## 7. 完了の定義（h2sol の報告に含める）
- 単体テスト（stub、FreeCAD なし）が通る。
- 実 LLM・実 FreeCAD で 1 周が完走し、cycle.json と library 追記がある。合否・トークン・時間が埋まっている。
