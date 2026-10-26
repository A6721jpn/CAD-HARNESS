# SolidWorks版 Harness2 H0 結果

> **停止中：SW経路の状態不明。能力評価はまだ成立していない。** 001は18送信すべてCLI exit1、回答0、CAD試行0。以下の0/18は原採点の保存結果であり、AIが18題のCADを解けなかったという成績ではない。18予約は返却せず、残り22。起動設定の最小修正後、無課金smokeが300.094秒で`H0_CAD_backend_stopped`となったため、新規002の固定・生成には進んでいない。

## 結論

- 状態: **安全停止・未完了**。SWの応答・所有文書状態の確認をユーザーへ依頼する。SWを終了・再起動していない。
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

- H0スコープのモデル呼出し上限: 40回。
- 保守的計上（conservative_reserved_calls、予約を含む）: 18回 / 40回。
- 価格・費用: 不明。単価が不明のため金額を算出しない。
- 各行の呼出し数と wall_s / active_s は供給値。不明値を0に置換しない。
- 停止理由: `H0_CAD_backend_stopped`（無課金`h0-smoke-04`、300.094秒）。状態不明のため所有セッションlockと非公開証拠を保持。55%/60%条件は緩めていない。

## 修正・検証と残件

- 001のCLI既定は承認モデルのCodexを無効化していた。H0専用の一時overlayだけを承認モデル`openai-codex/gpt-6.1-sol`へ限定し、起動失敗を次の題へ流さず停止する修正を実装。グローバル設定・auth・元v4 source・policy・カード・採点・goldは変更していない。
- ホスト15テストとFreeCAD 1.1.4の既存実形状6テストは合格。修正後smokeはFAILであり、実SW経路の再検証完了・新規版固定済みとは主張しない。
- `h0-smoke-04`はmock応答1、最終的なCAD結果0、R1修復0。実モデル送信0、production40枠の追加消費0。公開証拠：`reports/sw-h0/h0-smoke-04/summary.json`。
- 残件はSW応答・所有文書状態の確認、無課金smoke成功、新規002固定、共有残り22以内の同じ選択18題の実行。SW確認前にlockを消したり、モデル生成を始めたりしない。途中で残枠が題の元上限未満なら未着手で止める。
- ユーザー確認事項：SWを終了・再起動せず応答可能であることと、ハーネス文書の状態を確認いただきたい。確認できるまで待機する。

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
