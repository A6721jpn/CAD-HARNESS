# A0 環境互換性の実測記録

`compatibility.json` は今回の実測と未確認項目を記録する。A0 全体の完了を意味しない。
再現コマンド（PowerShell）: `& 'C:\Users\NGGmo\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe' 'C:\cad-harness\work\.a0-probe\probe.py'`
終了コードは 0。証拠は JSON 内の `A0_PROBE_RESULT` 行と起動バナー。
FreeCAD 1.1.3、build `20260725 (Git shallow)`、同梱 Python 3.11.14 を確認した。
Part 読込、100×40×8 mm の箱、体積 32000 mm³、ソリッド 1、形状の有効性、STEP/FCStd 出力を確認した。
ツール版は `node --version`、`codex --version`、`git --version` で再確認できる。
DSH 版はインストール済み package.json、プロファイル名は `Get-ChildItem -LiteralPath 'C:\Users\NGGmo\.dsh\profiles' -Name` で確認した。headless/web は変更していない。
DSH 起動は認証未設定のため unknown。専用プロファイル、tool/signal API、画像返却、snapshot/worker、datum/joint 追従、GUI編集・再読込も unknown。
