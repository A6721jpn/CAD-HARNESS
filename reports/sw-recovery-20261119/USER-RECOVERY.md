# SolidWorks復旧：ユーザー作業と再開条件

## 現在

- 課金再開は不可。監視の管理者設定と、ユーザーの再起動・手動確認が未完了。
- 11/19採取時はSolidWorksとViewServerとも稼働0。PCの最終起動記録は10/7で、10/29の障害をPC再起動のせいとは確定できない。
- 通常の画面は仮想ディスプレイが主画面。NVIDIAの出力はAPI上すべて非アクティブ。CIMの1024×768表示だけでは実際の出力状態を判断できなかった。変更はしていない。
- 旧データや判定は変えない。以下はユーザー作業。agentはPCを再起動しない。
- その後、許可された無課金切り分けとして公式shortcutを1回起動したが、SW本体は現れず、launcherはログイン画面で待機中。更新提示はHF5.9→5.11だったが、agentのskip操作は`app_not_found`で効果未証明。exeの現在値は34.4.0.0078で10/31とhash一致。認証や更新を完了したとは扱わない。**今のlauncherに対してユーザーが対応し、別の起動を重ねない。**
- 保存済みの独立M0 STEPを使うFreeCAD側だけの確認はPASS（2.048秒）。これは現在のSW作図・手動確認・安定gateの代用ではない。現在地の短い記録は[`CURRENT-STATUS.md`](CURRENT-STATUS.md)。

## 1. 管理者による監視の設定（SolidWorks不在時）

`monitoring-before.json`に変更前の9値を保存した。既存のSolidWorks独自LocalDumpsはmini/保持5/`%localappdata%\SolidWorks\CXPD`。今回のApplyは管理者権限なしで拒否され、変更0。ユーザーは**同じWindowsアカウントの管理者PowerShell**で以下を行う。別アカウントでは保存先が変わるため、scriptは拒否する。

```powershell
Set-Location C:\dev\CAD-HARNESS-sw
powershell -NoProfile -File reports/sw-recovery-20261119/monitor-sldworks.ps1 -Mode Apply -State C:/dev/CAD-HARNESS-sw/reports/sw-recovery-20261119/monitoring-before.json -Receipt C:/dev/CAD-HARNESS-sw/reports/sw-recovery-20261119/monitoring-apply-admin.json
```

成功はexit0と`APPLIED_readback_verified`の両方。失敗・設定競合なら進めずreceiptを渡す。実行前後の現在値もreceiptへ残す。既存値を強制削除したり、全アプリ共通設定に広げたりしない。既存snapshotと違えば新しいInspectを別ファイルへ保存し、差を確認してから再適用する。

設定は`sldworks.exe`だけ：WER mini、保持2、専用非公開folder、既存IFEO flagを保持して`0x200`追加、SilentProcessExitのlocal dump/自己終了も検知。miniでもメモリに設計・個人情報が入ることがある。**dump、journal、CXPA archiveはGit/LLMへ渡さない。** SilentProcessExitは他processによる終了時に終了主体のdumpも作る場合がある。専用folderは`%LOCALAPPDATA%\CADHarnessRecovery\sw-20261119\dumps`。

元に戻すとき（適用成功後、SW不在時だけ）：

```powershell
powershell -NoProfile -File reports/sw-recovery-20261119/monitor-sldworks.ps1 -Mode Restore -State C:/dev/CAD-HARNESS-sw/reports/sw-recovery-20261119/monitoring-before.json -Receipt C:/dev/CAD-HARNESS-sw/reports/sw-recovery-20261119/monitoring-restore-admin.json
```

元の値・型・値の不存在を戻し、作った空の対象exe keyだけを削除する。後から他人が変えた値は上書きしない。dumpは証拠なので自動削除しない。Apply/Restoreの管理者成功経路と実際のdump生成は**まだ未検証**。Inspectと管理者不足時の無変更停止だけ実行確認済み。

参考：[Microsoft LocalDumps](https://learn.microsoft.com/en-us/windows/win32/wer/collecting-user-mode-dumps)、[SilentProcessExit](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/registry-entries-for-silent-process-exit)、[flag 0x200](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/enable-silent-process-exit-monitoring)、[MINIDUMP_TYPE](https://learn.microsoft.com/en-us/windows/win32/api/minidumpapiset/ne-minidumpapiset-minidump_type)。WERはアプリ独自crash処理等で収集できないこともあり、設定成功だけで原因捕捉を保証しない。

## 2. PC再起動・手動確認（ユーザーのみ）

1. 他の作業を保存し、agentやCAD等に影響がない時間を選ぶ。起動中のSWにユーザー文書があればユーザーが保存する。agentに終了を任せない。
2. ユーザーがPCを再起動。ログイン方法、主画面、解像度、リモート接続の有無と時刻を記録する。agentは再起動・ログオフ・表示切替をしない。
3. ユーザーが公式の「SOLIDWORKS Design」ショートカットで初回起動。更新/認証/復旧画面はユーザーが処理する。自動更新をagentが無断で無効化しない。
4. 起動後5分置き、ユーザーが新しい検証専用部品で矩形→押し出し→保存を試す。課題/正解データを使わない。終了時刻・成功/異常と版を記録する。
5. 自分のテスト文書はユーザーが保存して閉じ、**SW自体は起動したまま**、文書0の状態を知らせる。agentはユーザーが作った部品を開閉しない。
6. 固まった場合は追加COM、kill、再起動をさせず停止点を記録。SWが消失した場合も、監視証拠を保全して原因を確認する。

## 3. 課金0の自動確認・描画方式比較

- 自動確認は元の`tools/sw_m0.py`、公開の独立M0 fixture、既存7入力のhashを固定して行う。実PIDを明示し、保存先は毎回未使用名。自分の作成文書だけ扱う。
- 既存の文書、古いlock、無応答instanceがあれば止める。古いlockは所有process不在と排他取得を確認してからrename保存し、削除しない。
- Software OpenGL比較は文書0・応答ありの状態で、一度に1条件だけ変更し、元設定/有効性/版/renderer/PIDを記録。同じM0と判定を使い、効果未確認の状態を「復旧」としない。
- 切替に健康なSWの再起動が必要なら**ユーザーが行う**。agentは終了・再起動しない。API/版で設定できない場合も別設定を推測して変更しない。表示/driver更新・SW修復は後回しで、勝手に行わない。
- ユーザー作業前に行う無課金診断があっても、手動確認や以下の安定gateの代わりにはしない。

## 4. 課金再開のgate

同一の記録した描画/表示条件で、M0連続5回→H0 smoke2回→30分idle後M0を1回→正負20制御を全件完走。途中のcrash/無応答で未達とする。誤仕様は形状判定で落ちる必要があり、COM障害を正しいnegativeと数えない。各段階のreceipt/hash/時間を記録する。

すべて成立しても、比較手順提案の採否・独立runの事前登録/新freeze・正規会計・新quotaを確認するまで課金しない。旧runは再採点/replay/refundしない。55%で確認、60%停止、Codex親を含め2台以内。cardの0.01mm、全体偏差0.005mm、既存G2その他の判定/時間制限/採用gate/policy/封印は不変。
