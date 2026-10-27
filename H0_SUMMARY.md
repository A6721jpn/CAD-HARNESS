# SolidWorks版 Harness2 H0 結果

> **更新後の無課金確認は合格、002の固定・実行準備中。** 自作viewの描画更新だけを停止し、標準M0は9.676秒、H0 smoke05は63.609秒で合格。合格基準・policy・カード・採点は未変更。追加ライブ生成0、元18予約と残22を維持。以下の001の0/18は起動失敗の保存値で、AIの能力評価ではない。

## 結論

- 状態: **無課金の経路検証完了、ライブH0は未完了**。稼働中SWの終了・再起動はしていない。消失後の新規起動1回は01:31 JSTの明示許可に従ったもの。
- 下表は001の保存集計：選択18/60行、CLI終了18/18選択行、非選択42行。
- 原採点の保存値は合格0/18。ただしモデル回答・実CADの成立が0で、AIの能力スコアには使わない。
- 未実行・未完了行は成功にも失敗にも加算しない。

## 判定の扱いと限界

- これは部分H0の集計であり、元60題のスコアでも全60題の合格確認でもない。
- 供給された公開判定のみを集計する。実CAD・実モデルのライブ実行成立は、この要約だけでは主張しない（停止・模擬実行を成功実行と扱わない）。
- 幾何（完了行のみ）: PASS 0、FAIL 0、不明 18。
- 編集性（完了行のみ）: PASS 0、FAIL 0、不明 18。
- 再読込（完了行のみ）: PASS 0、FAIL 0、不明 18。
- 重大な発明判定あり（完了行のみ）: 0行。
- マニフェスト SHA-256: `72a617445e72d09adcc43fcb0fbb583bc0acdfd695a5bf7d1d432aeae548f8c4`

## 時間と呼出し会計

- 最初の共有開発poolは40上限。追加許可は各バッチ50以下で、今後の別poolも安全側に40上限を採用。元poolの残高はリセットしない。
- 保守的計上（conservative_reserved_calls、予約を含む）: 18回 / 40回。
- 価格・費用: 不明。単価が不明のため金額を算出しない。
- 各行の呼出し数と wall_s / active_s は供給値。不明値を0に置換しない。
- 旧停止理由はRPC接続切断・SW消失と起動待ち。更新後34.4.0の自作view描画停止で標準M0とsmoke05が合格したため、凍結前の回避修正として採用。GPU等の根本原因は未確定。55%/60%条件は不変。

## 修正・検証と残件

- 001のCLI既定は承認モデルのCodexを無効化していた。H0専用の一時overlayだけを承認モデル`openai-codex/gpt-6.1-sol`へ限定し、起動失敗を次の題へ流さず停止する修正を実装。グローバル設定・auth・元v4 source・policy・カード・採点・goldは変更していない。
- 最新ホスト17テストPASS（0.368秒）、FreeCAD1.1.4実形状6テストPASS（4.156秒）。別pool分離・40超拒否・共有poolへのmanifest付替拒否を含む。これに加え修正後の実SW M0とsmoke05が合格した。まだ002のライブ成績はない。
- `h0-smoke-04`はmock応答1、最終的なCAD結果0、R1修復0。実モデル送信0、production40枠の追加消費0。公開証拠：`reports/sw-h0/h0-smoke-04/summary.json`。
- 再開M0の保存済み正例3STEPは、既存の元0.01mmと追加0.005mmの判定に合格。再読込/復元差分体積0。ただし負例は未作成でM0全体FAIL（29.150秒）。ViewServerV6.exeのアクセス違反0xc0000005も記録されたが、根本原因は未確定。証拠：`reports/sw-m0/m0-resume-20261028-01/`。
- 先行lockは所有者不在・排他アクセス等を確認してrename保存。稼働中SWを終了して回避していない。現在の実SW確認はPID53084/34.4.0で合格し、開始/終了文書0。今後も不在時の起動だけが許可され、公式ランチャーを使う。
- 新しい独立40枠と、元18題内の未完了分を固定するprepare機能を実装・無課金検証した。002は従来の残22のみを使用する。新バッチも新claim・新manifestが必要で、正当な不合格を消したり課金予約を返却したりしない。
- 残件：固定前checkpoint保存→002固定/実行→必要な独立小バッチ→H0集計。H0後の説明文だけの交互各5回比較は`H2_SKILL_PLAN.md`に事前計画を保存。元60を改善データへ再利用せず、比較生成はまだ0。
- 成功証拠：`reports/sw-m0/m0-resume-20261028-03/result.json`、`reports/sw-h0/h0-smoke-05/summary.json`。smoke05はmock2・実CAD2・誤仕様拒否・既存R1修復1・完全なcapture8本。旧smoke04の300秒切れは再発せず、終了まで63.609秒だった。

## 全60行

序数は元順序。not_run は未着手（選択予定行を含む）、incomplete は着手済み未完了。passed / failed は完了した選択行だけの判定。

| 序数 | 区分 | 経路 | 選択 | 状態 | モデル | CAD | parse修復 | repair | wall_s | active_s | 幾何 | 編集性 | 再読込 | Q | 重大発明 | 失敗分類 |
|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---|---|
| 1 | dev | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 2 | dev | spec | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 3 | dev | ask | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 4 | legacy | offline | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 5 | legacy | offline | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 6 | legacy | offline | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 7 | legacy | offline | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 8 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 9 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 10 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 11 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 12 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 13 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 14 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 15 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 16 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 17 | mvp | mvp | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 18 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 19 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 20 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 21 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 22 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 23 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.4370000001508743 | 1.4370000001508743 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 24 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.297000000020489 | 1.297000000020489 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 25 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 26 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 27 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 28 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 29 | geometry | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 30 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.296000000089407 | 1.296000000089407 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 31 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.3119999999180436 | 1.3119999999180436 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 32 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.3440000000409782 | 1.3440000000409782 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 33 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.3600000001024455 | 1.3600000001024455 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 34 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.297000000020489 | 1.297000000020489 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 35 | geometry | spec | yes | failed | 1 | 0 | 0 | 0 | 1.327999999979511 | 1.327999999979511 | 不明 | 不明 | 不明 | 不明 | FAIL | exec_nonzero_or_missing_final |
| 36 | q | spec | yes | failed | 1 | 0 | 0 | 0 | 1.3130000000819564 | 1.3130000000819564 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 37 | q | spec | yes | failed | 1 | 0 | 0 | 0 | 1.3120000001508743 | 1.3120000001508743 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 38 | q | spec | yes | failed | 1 | 0 | 0 | 0 | 1.327999999979511 | 1.327999999979511 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 39 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.327999999979511 | 1.327999999979511 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 40 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.343000000109896 | 1.343000000109896 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 41 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.3130000000819564 | 1.3130000000819564 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 42 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.3600000001024455 | 1.3600000001024455 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 43 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.297000000020489 | 1.297000000020489 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 44 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.297000000020489 | 1.297000000020489 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 45 | q | ask | yes | failed | 1 | 0 | 0 | 0 | 1.3440000000409782 | 1.3440000000409782 | 不明 | 不明 | 不明 | 0 | FAIL | exec_nonzero_or_missing_final |
| 46 | q | ask | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 47 | q | ask | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 48 | q | ask | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 49 | completion | completion | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 50 | completion | completion | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 51 | completion | completion | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 52 | completion | completion | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 53 | completion | completion | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 54 | completion | completion | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 55 | fault | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 56 | fault | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 57 | fault | spec | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 58 | fault | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 59 | fault | source | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |
| 60 | fault | spec | no | not_run | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 | 不明 |

## 安全性・保存先

- このファイルには公開メタデータ・判定・呼出し数・時間だけを投影する。原要求、生成応答、gold、寸法、任意のエラー詳細は転記しない。
