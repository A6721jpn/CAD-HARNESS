# CAD-HARNESS v5 — 実装計画

DeepSeek Harness＋FreeCADで、二つ穴の板から100部品以下のアセンブリへ段階的に拡張する実装計画です。
2026年10月17日、Grok 4.7 high・Agy Gemini 4 Argon High・Claude Opus 5.5 xhighとの討議を反映しました。

- **[実装計画HTML](docs/deepseek-freecad-plate-mvp-plan-ja.html)** — 構成図、M0〜M9、最初の実装タスク、検証条件。
- [3モデルの討議記録](docs/freecad-mvp-model-discussion-ja.html) — 8回答と採用・不採用の理由。
- [LLM向けCADアーキテクチャ](docs/llm-native-cad-architecture-ja.html)
- [既存手法の調査](docs/cad-harness-architecture-research-ja.html)
- [討議前の計画](docs/freecad-mvp-before-review.html)

## HTMLの閲覧

GitHub上ではHTMLがソース表示になるため、このブランチをダウンロードまたはcloneし、
`docs/deepseek-freecad-plate-mvp-plan-ja.html` をブラウザで開いてください。
HTMLの図は埋め込み済みです。関連資料のリンクを保つため、`docs/` 一式を同じ配置で保管してください。

## 状態

このブランチは文書のみです。CAD実装、FreeCADでの動作検証、100部品の性能測定はまだ実施していません。
公開用レビュー記録にはモデル設定と回答を含め、ローカル実行パス・プロセスIDは省いています。

v5の旧ファイル一式は、この文書配置コミットで削除しています。旧内容はGitの親コミットから参照・復元できます。
