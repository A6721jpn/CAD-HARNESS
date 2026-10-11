# BRIEF: Sol にシェルを持たせない driver 方式の評価（2026-10-11）

経緯: 条件B（Sol 子エージェントが自分で cad_run を呼ぶ）の N=5 は run2 で停止。Codex の Windows サンドボックスが毎回「sandbox setup required: sandbox setup marker missing or incompatible」を出し、子のシェル起動が昇格エラー 1223 で失敗した（run1 も約4分この壁で待ったのち通過、run2 は CAD 未到達で終了）。記録: reports/runs と reports/outcomes の rollout-2026-10-11T15-25-43-01a129a3... と rollout-2026-10-11T15-35-21-01a129ac...。

ユーザー案（15:54 JST）: driver（例 tools/cad_agent.py）が課題仕様を Sol に送り、Sol は build(doc) スクリプト本文だけを返す。driver が cad_run を実行し、非0なら result JSON を Sol に返して修正させる（修正は最大2回）。Sol はシェル・サンドボックス・UAC を使わない。

ユーザー追加（15:56 JST）: 実装前に三者評価。比較対象:
 (1) driver 方式（Sol は本文のみ）
 (2) Sol にシェルを持たせ、サンドボックス初期設定を一度だけ行う（UAC 承認が要る）
 (3) Sol にシェル、--dangerously-bypass-approvals-and-sandbox で回避
 (4) ハイブリッド: Sol に読み取り専用の調査を許す
評価基準: 速度・トークン、2026-10-05 ベースライン（シェルあり）との計測の公平性、Sol が失う能力（ファイル調査、FreeCAD 自体のデバッグ等）とそれが複雑課題で効くか、安全性、実装コスト。判定は go / go with changes / no-go。

監督が確認済みの事実（10/11 15:55 JST、DPC-019、codex-cli 0.159.2、Orca の Codex アカウント CODEX_HOME）:
- `codex exec -m gpt-6.1-sol -c model_reasoning_effort="xhigh" --disable shell_tool --disable unified_exec --disable code_mode_host --disable multi_agent --disable apps --disable plugins --disable browser_use --disable computer_use --disable image_generation --disable view_image -s read-only --skip-git-repo-check -C <空ディレクトリ> --json -o <last.txt> "<prompt>"` が exit 0、7秒、本文 "PING OK."。サンドボックスログに新しいエントリなし（シェル未使用）。
- セッション rollout は通常どおり CODEX_HOME\sessions に保存され、turn_context は model=gpt-6.1-sol effort=xhigh sandbox=read-only。
- `--json` の turn.completed に usage（input_tokens, cached_input_tokens, cache_write_input_tokens, output_tokens, reasoning_output_tokens）が出る。
- measure_rollout.py はこの rollout を読めるが、スナップショット1個だと session_delta（last-first）は 0。ベースラインは session_delta を集計していた（最初のスナップショット約2万トークン分を含まない）。driver 方式で呼び出しを分けるか `codex exec resume` で1セッションに続けるか、使用量を driver が自分で記録するかを決める必要がある。
- AGENTS.md（CODEX_HOME とユーザーの .codex）は exec でも読み込まれる。code_mode_host を無効にすると「Code Mode is unavailable」警告が出る。
- ベースライン（runs 2-5）: 平均 489.16 秒、session_delta 合計 2,470,906（input 2,416,743 / cached 2,267,648 / output 54,163）、LLM 応答 59、exec_command 8/12/12/11。条件B run1（warm-up）: 284.8 秒、730,858、応答 27、cad_run 1 回成功、うち約4分は権限待ち。
- Claude Code は 10/11 15:44 と 15:57 JST の再試行でも「organization has disabled Claude subscription access for Claude Code」。他経路（opencode は資格情報 0、omp の opus 指定は Cloud Code Assist 404）も不可。
