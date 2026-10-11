# 課題B: PartDesign Pocket・穴パターン・Chamfer（B2 driver）
設計出典：design/cad-run-complex/CONSENSUS.md。単位mm、DPC-019、FreeCAD 1.1.4。
識別子：B-plate-pocket-hole-pattern-chamfer。A-box-pocket-filletは既定のまま。

## 仕様

1. 原点・回転なしの単一Body。XY中心矩形80×60を+Z片方向へPad長さ10。
2. 上面Z=10中央の30×20矩形をPocket深さ4、底Z=6、非貫通・垂直壁。
3. 上面中心(-20,-20,10)、半径3の円をPocket長さ10で下向き貫通。
4. 穴PocketだけをBody +XへLinearPattern。元を含め3個、中心(-20,-20),(0,-20),(20,-20)。
   ピッチ20、最初から最後の総距離40。スモークでLength=40の配置を確認済み。
5. 上面外周4直線辺だけ等脚1・45°Chamfer。内部縁・縦稜・下面は鋭いまま。Tip=Chamfer。

標準Origin族以外の個数：Body1、Sketch3、Pad1、Pocket2、LinearPattern1、Chamfer1、Fillet0。
Pad/Pocketは非Reversed・非対称。追加Part::Feature、Hole、座ぐり、ねじは作らない。

## Probeと受入

固定Probeが幾何と履歴を検査。単一valid solid、bbox80×60×10、中央Pocket、穴位置・半径・開口、
フィーチャ型/個数/順/所属/リンク、上面外周Chamfer、体積を検査する。
面数・表面積は診断値だけ。Bの線形/軸許容1e-6、体積相対許容1e-6。Aの許容は変えない。
good理論体積45600−270π−416/3 mm³は仕様からの導出値、実測値はresult.jsonに分離する。
導出と実測の照合はdesign/cad-run-complex/impl-notes.md。帯を実測に合わせて広げない。

## スモーク（CAD起動の承認がある場合だけ）

各out-dirはreports/cad-run配下の新規名。既存入力・出力・evidenceは上書きしない。
A good/brokenを先に照合し、崩れたらBへ進まない。B goodを実行：
```bat
python -B tools/cad_run.py --task B-plate-pocket-hole-pattern-chamfer --script tools/fixtures/cad_run_b_build.py --out-dir reports/cad-run/<FRESH>-good --timeout-s 300 --recipe freecadcmd
```
brokenはB fixtureの新規コピーでbuildをbuild_without_chamferへ切替。Chamfer以外は変更しない。
期待失敗はvolume/feature_counts/feature_chain/outer_chamferのみ。build例外は受入結果にしない。
双方で保存・文書close・cleanup_status=exited・CAD exit0、段別時間とworker生成UTCを確認する。

## 監督側のB2 N=3（スモーク合格後・別工程）

```bat
python -B tools/cad_agent.py --run <FRESH-B-RUN> --task B-plate-pocket-hole-pattern-chamfer
```
新規run-idで順次3回。run1=warm-up、run2/3=主報告。失敗/停止/未到達と全attemptも残す。
gpt-6.1-sol/xhigh、ツール10種無効・read-only・CODEX_HOME継承、resumeなし、毎attempt新規空の外部cwd。
初回＋最大2修正、CAD最大3回、freecadcmd/300秒のみ。fixture/API例/過去解答をSolへ渡さない。
Sol修正はbuild/probe担当・Probe例外なし・文書close済み・回収済み・整数CAD exitの条件でのみ行う。
診断不足/human/launch/dialog/不正JSON/回収未了は停止。driverの既存停止条件を緩めない。
driver wall_msが主時計。Sol/cad_run/workerは内訳、usageは生値を記録し合算しない。
計測は既存measure_rollout.py。geometry_okの出典をProbeとnotesに記載し、B専用の新規aggregateへ。
Aや10/05との差は課題・道具・母数が異なる参考比較。難易度差を速度改善率へ換算しない。
