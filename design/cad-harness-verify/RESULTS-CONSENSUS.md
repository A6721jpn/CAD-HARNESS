# CAD-HARNESS VERIFY — RESULTS-CONSENSUS

1. 版verify-v1-reviewed-r1（b339f9d / 2ad59e7）、prefix host-verify-v1-reviewed-r1：54/54完了、bar_met=falseを保持する。
2. fresh eval-v1は10/10、全Pが2/2、legacy good/broken期待一致は4/4で、旧gold/barの回帰条件を満たした。
3. V1–V5は8/10、V1–V4各2/2、V5は0/2；fallback経路は10/10通ったが各part最低1/2の条件は未達。
4. V5はgeometry=trueで、保存FCStdにactive/driving PCD60と穴への接続があるためProbe寸法追跡のfalse-negativeを示す；再採点しない。
5. V6は3/3、S1は5/5で全gate成功；固定された複合部品の限定範囲であり、任意形状・全履歴追従の認定ではない。
6. Q1は3/3、Q2/Q3各5/5、重要欠落の発明0件；Q2/Q3は各run Sol 1 call・CAD 0、回答後の完成は未測定。
7. fault成立/検出は各6/6、最終成功2/6；F1/F2各0/2は修復未起動、F3は実spec修復2/2、source修復の実用条件は未達。
8. parse repairは8 calls、自然修復はeligible V5の最終pass 0/2だがrepair calls=0；dev DV1/DV6のfail flagはpreview/confirmation_requiredで非採点。
9. 全実行はSol 75 calls・CAD 43 attempts・実repair 2 calls、wall med/p95/max=29.039/272.860/347.797秒；全Sol使用runのinput=2507904、output=95506、欠測はnullのまま。
10. [RESULTS.md](RESULTS.md)のsuite別CI/usage/原因分析に合意する；修正は新版＋新未使用holdoutと新prefixで測り、本版の失敗・未達とreportsを保存する。

codex: AGREE (2026-10-12 21:17:14 JST)
grok: AGREE (2026-10-12 21:51:18 JST)
grok note: F1の初回CADはroller検出に加え edit.driving_dimension.4（expected 28, actual null）も失敗している。native_validはtrueで、0/2と再採点しない判断は変わらない。
gemini: AGREE (2026-10-12 21:29:15 JST)
gemini note: V5のPCD60は保存FCStd内でactive/drivingかつPointOnObject接続され幾何完全だが、ProbeがReferenceAxis以外のSketch内construction寸法を拾えないfalse-negativeであることを確認。再採点せずbar_met=false保持に合意。
gemini note: F1/F2はparse repairで3-call枠を消費し初回注入CAD fail後の修復が未起動（calls=0）であることを確認。モデルのsource修復能力の成否判定ではなく、次回は注入後の修復call枠を確保した設計が必要。
gemini note: fresh eval-v1(10/10)・legacy(4/4)・Q1(3/3)・Q2/Q3(各5/5・発明0)・F3(2/2)の記録数値照合を確認。未達結果とreportsを保存し、修正は新版＋新holdoutで扱う方針に合意。

