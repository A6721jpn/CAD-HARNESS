# CAD-HARNESS 三者協議フレームワーク (CONSULT-FRAMEWORK)

制定: 2026-10-12 (ユーザー指示 t116u: Claude Opus 5.5 を外し、Agy 経由 Gemini 3.8 Flash High を入れる)

## 参加者
| key | エージェント | モデル | Orca タブ (DPC-019) |
|---|---|---|---|
| grok | Grok Build | (既存設定) | debate-grok term_f028d01a |
| codex | Codex CLI | 最高エフォート設定 (既存) | verify-codex term_588425d4 (案件ごとに差し替え可) |
| gemini | Antigravity CLI (agy 1.3.3) | gemini-3.8-flash-high, --effort high | consult-gemini term_bb0ef25e |

Claude Opus 5.5 は参加者から外す (ユーザー判断 t113u/t116u)。
起動: `%LOCALAPPDATA%\agy\bin\agy.exe --model gemini-3.8-flash-high --effort high` (cwd C:\dev\CAD-HARNESS, --dangerously-skip-permissions は使わない)。
中継: `%TEMP%\orcarelay_verify\relay.py` (peek / read <k> N / send <k> file / gapprove)。

## 進め方 (協議ごとに design\<topic>\ を作る)
1. BRIEF.md: 監督が論点・制約・既決事項を書く。プロンプトには BRIEF のパスだけ渡す。
2. R1 提案: 3者が独立に `<key>-r1.md` を書く (他者の案は見ない)。
3. R2 相互批評: 他2者の R1 を読み `<key>-r2.md` に賛否・修正案を書く。
4. R3 合意: 起草者 1名 (既定 codex) が CONSENSUS.md を起草、残り2者が `AGREE` または `<key>-sign.md` に `COUNTER` (具体的修正点) を書く。COUNTER があれば起草者が反映し再署名。
5. 成立条件: 3者全員が CONSENSUS.md 末尾に `AGREE <key> <JST時刻>` を署名。監督がローカル commit (push しない)。

## 対立時のルール
- COUNTER の往復は最大 2 回。それでも割れたら 2対1 の多数決で決め、少数意見を CONSENSUS.md の「少数意見」節に原文で残す。
- 合格ライン・gold・既存集計の変更、課金・外部送信を伴う事項は多数決で決めず、ユーザー判断に回す。
- 数値は計測・出典があるものだけ書く。根拠のない試算は合意文書に入れない。

## 片方が使えない場合
- 1者ダウン (認証切れ、利用上限、無応答 30 分以上): 残り2者で進め、CONSENSUS.md に不在者と理由を明記。2者が割れたら決めずにユーザー判断。復帰後に不在者のレビューを任意で追加。
- 2者以上ダウン: 協議を止めてユーザーに報告。
- Codex は週間使用量 60% で停止 (55% で継続判断)。

## 権限
- gemini の承認プロンプトは relay の `gapprove` で、`design\` 配下への書き込みだけ1回ずつ承認。それ以外 (tools/ skills/ evals/ 削除、push 等) は承認しない。
- 協議参加者は設計文書のみ書く。実装は合意後に別タスクで行う。