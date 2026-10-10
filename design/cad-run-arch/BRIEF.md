# BRIEF: cad_run プロトタイプのアーキテクチャ（2026-10-10）

## ユーザー依頼
「まずその CAD ハーネスを試作してみて。アーキテクチャはまた三者で相談してね」。design/judge-ai-insertion/CONSENSUS.md で合意した `cad_run` を、**小さな試作**（フレームワークではない）として作る。

## 進め方
- PHASE 1（本フォルダ、最大4ラウンド）: R1 提案 `<agent>-r1.md` → R2 批評 `<agent>-r2.md` → R3 claude が CONSENSUS.md 草案、他は `<agent>-r3.md` → R4 `<agent>-final.md` で AGREE/DISAGREE、CONSENSUS.md §署名欄。
- PHASE 2: 実装者 1 名（既定は codex。合意で変更可）が新ブランチ（例 `proto/cad-run`）で実装しローカル commit（push 禁止）。他 2 名が diff を 1 回レビューし、合意した指摘を実装者が直す。
- PHASE 3: DPC-019 で FreeCAD 1.1.4（`C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe` を優先）を使い、2026-10-05 の既知の良いスクリプト（`reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/` の run0x-script.py 等）で 1 回、わざと壊したスクリプトで 1 回、スモークテスト。N=5 や Sol の CAD ロールアウトはしない。

## 入力（読み取りのみ）
- design/judge-ai-insertion/CONSENSUS.md、CASES.md
- reports/bottleneck-A-box-pocket-fillet.md
- docs/runbook-A-box-pocket-fillet.md、docs/measurement-slice-v0.md、tools/README.md、tools/measure_rollout.py
- reports/evidence/A-box-pocket-fillet-FreeCAD-20261005/（スクリプトと cad.json の実例）

## 決めること（全部）
1. CLI インタフェース（スクリプト本文を引数/ファイルで受けるか、出力先、終了コード、JSON 出力）
2. 段: launch 固定手順 → FreeCAD 実行（headless の FreeCADCmd で足りるなら優先、GUI は不可避な箇所だけ）→ 固定 Probe（A-box-pocket-fillet の寸法・体積・面・外周エッジだけのフィレット）→ 自分が起動したプロセスだけの後片付け
3. CIM（Get-CimInstance 等）を呼ばない
4. 警告と終了コードの方針（stderr 警告で失敗にしない、exit≠0 は失敗のまま）
5. 復旧ダイアログの検出と停止（ユーザーのプロセスを強制終了しない）
6. イベントログ: 1 イベント 1 行、フィールドを分ける
7. J1 判断スロットは無効化したスタブ（外部 API なし）
8. measure_rollout.py を壊さない統合方法
9. 最小のテスト計画
10. 実装者の指名、ファイル配置、ブランチ名

## 制約
- 本フェーズで書いてよいのは本フォルダ内の自分のファイルだけ（CONSENSUS.md は claude、署名行は各自の final を根拠に claude が記入）。
- コード編集禁止（PHASE 2 まで）、FreeCAD/CAD 起動禁止（PHASE 3 まで）、外部 API 禁止、Fusion/SolidWorks は絶対に起動しない、sldworks_fs に触れない、語数カウント等の追加コマンド禁止、秘密/鍵/個人の絶対パスを書かない。
- 数値は資料にあるものか、未計測と明記したものだけ。