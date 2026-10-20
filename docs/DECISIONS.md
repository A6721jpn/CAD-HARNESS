# h2/mvp 設計判断（h2lead）

- D1 (10/21 00:05) MVP は LIBRARY_ONLY（10/20 協議の実現性・整合・リスクで全員一致の第一候補）。ベースは毎回固定、経験はライブラリだけに追記。DP 系の自動永続化は入れない。
- D2 (00:05) 合否は cad_run.py + cad_run_probes.py の probe_status=="pass"（AI 不使用、既存部品を変更せず呼ぶだけ）。fixture で status=ok/probe=pass を確認済み。
- D3 (00:05) 詳細仕様は design/h2-mvp/SPEC.md。ハーネス編集は構造化 op に限定し、合成は決定的ルール（pass > attempts > tokens > wall、±10% は同等）。
- D4 (00:08) 運用変更（ユーザー指示 00:07）: h2lead はコードを読まず書かない。実装・テスト・commit・push は h2sol。h2lead は docs/H2-SUMMARY.md と短い回答だけを読む。
- D5 (00:08) Codex の同時実行は 2 台まで（h2sol + codex exec 1）。サイクル内の codex exec 呼び出しは必ず逐次。
- D6 (00:14) h2sol の sandbox は git 管理領域（本体 .git/worktrees 配下）への書き込みもネットワークも不可。権限拡大は禁止なので、git commit/push と実 LLM を使うサイクルの起動だけは h2lead のシェルで機械的に行う（diff やコードは見ない）。h2sol はコード・テスト・要約・commit メッセージ案を担当する。
- D7 (00:14) トークンが取れずに比較できない場合は「判断不可（undeterminable）」として扱い、支持ありに数えない（h2sol の既定を承認）。
