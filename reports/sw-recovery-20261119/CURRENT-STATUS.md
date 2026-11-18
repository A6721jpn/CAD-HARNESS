# 復旧の現在地（11/19、最終観測18:01:59 UTC）

- **BLOCK：管理者による監視設定と、ユーザーのSolidWorksログイン・手動確認が必要。課金再開不可。**
- quotaは1%（observed18:01:41Z）。追加CAD生成モデル/課金呼び出し0。55%確認・60%停止は不変。
- host/SW crash/GPU/display/sessionのread-only証拠を採取。10/31の未追跡公開M0証拠25ファイルは`0ea81c1`で保全・push済み。
- 新規SPE監視は管理者不足で拒否、registry/ACL/driver/表示設定の変更0。既存vendor WERは維持。[管理者設定と復元手順](USER-RECOVERY.md#1-管理者による監視の設定solidworks不在時)。
- 公式shortcut起動はSW不在時の1回だけ。現在CATSTART28160とSWXDesktopLauncher47604が応答あり、SW/Viewerは0。ログイン画面を残している。再起動/kill/再起動連打/認証代行はしていない。
- HF5.11更新の提示があった。agentのskip操作は失敗して効果未証明。インストール済みSW exeは34.4.0.0078、SHA256は10/31記録と一致。runtime版は未取得。
- 独立・保存済みM0 STEPの**FreeCAD側だけ**の正負確認はPASS（1.1.4/OCCT7.8.1、2.048秒）。SWの現在の作成能力・G2・安定条件を合格にした証拠ではない。
- 比較関数の人工入力smokeは6/6 PASS。[比較手順提案](comparison-procedure-proposal.md)は未実装。公式合否/採用条件/カード/policy/封印/旧比較結果は不変。
- 次はユーザーが[復旧手順書](USER-RECOVERY.md)に沿って管理者設定、PC再起動、ログイン、検証専用部品の手動確認を行い、SW文書0で知らせる。agentはPC再起動やユーザー文書の開閉をしない。
- その後のgate：同じ条件でM0連続5回→smoke2回→30分idle後M0を1回→正負20制御。**今回はすべて未実施**。完了前のlive/newfreeze禁止。
