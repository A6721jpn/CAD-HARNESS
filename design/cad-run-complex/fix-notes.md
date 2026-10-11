# 課題B レビュー修正（2026-10-11）

対象: a5b35bf / grok-review.md（20:59）/ 署名済みCONSENSUS.md。must-fixはなし。
should-fix 1–2とnit 3–4はすべて採用した。不同意項目はない。

## 指摘ごとの対応

- should-fix 1: BのスケッチGeometryCount一致を撤廃した。構築ジオメトリを理由に不合格にしない。
  Profileの所属・リンク・順序、輪郭bbox、穴Profileの円中心/半径/軸/上面Zは保持。
  穴3個・Patternの元・方向・非Reversedはfeature_chainへ移し、holes_patternは抽出された
  円筒面/円弧から中心・半径・軸・Z=0..10・上下開口・軸が中実でないことだけを判定する。
- should-fix 2: b_probeへ偽の面・円筒面・円弧を渡すCADなし試験を1メソッド追加した。
  合格例に構築ジオメトリを含め、円筒面/円弧の分割をまとめる抽出も通す。
  穴中心ずれはholes_pattern、底面Zの不一致はcentral_pocket、面取り帯1面欠落はouter_chamferだけが落ちる。
  他の形状値・履歴を保持した抽出の負例であり、CAD成立の確認は別の実機4スモークで行った。
  既存のChamfer/深さ/個数/位置の4故障試験も残した。
- nit 3: Origin X_Axisのオブジェクト同一性を合否に使わず、正規化方向が+X・非Reversedかを判定する。
  ベクトル、参照直線Edge、標準軸の向きを抽出。生のLengthは引き続き記録だけ。
  +Xの複数表現は合格、負X・ゼロ方向・Reversedはfeature_chainだけ不合格になる単体試験を追加した。
- nit 4: BプロンプトにDPC-019だけでCADを実行し、LPC-017では実行しない制約を明記した。
  Bプロンプト試験にもこの文を追加した。Aプロンプトと既存のSHA256固定試験は変更していない。

## 単体テスト・A不変確認

実行: python -B -m unittest tools.test_cad_run tools.test_cad_agent
結果: 25件、全件成功（0.653秒）。既存24件＋抽出1件。CAD/Sol/codex execはモックのみ。
A Probe・補助関数・初回プロンプトは変更前の文字列と一致することを確認。
A PROMPT SHA256: ea2008c9dfdb3d1c9ff732dd5c373fd431064d53744e01db9cad8921e32cc641。
A fixture、cad_run.py、cad_run_freecad.py、measure_rollout.pyはハッシュ一致で未変更を確認。
A fixture SHA256: 3ad5c506d84739c4378ce80d9557800919e7c0dd6c8f46cb8ff1cbc3882393dd。
measure_rollout.py SHA256: 9ee8cff2527ae86040bc4b663c1505e2510b2e8d6a8da7065c5e7a2cd698f90d。

## freecadcmd実機スモーク

固定実行先はC:/dev/CAD/.tools/freecad/FreeCAD_1.1.4-Windows-x86_64-py311/bin/freecadcmd.exe。
FreeCAD 1.1.4、freecadcmd、timeout_s=300、全readyでGuiUp=0。GUI/console/Sol/外部APIは実行していない。
A good→A broken→B good→B broken。全件でCAD終了0、保存完了、document_closed=true、cleanup_status=exited。
各出力先は新規-fix1のみ。負例の入力コピーはreports外の一時領域に作り、完了後に回収した。
新規出力フォルダー以外のreportsは変更していない。B brokenはChamfer省略1点だけ。
timings_msはbuild/recompute/probe/saveの実読取、生値を以下に記録する。総時間へ合算しない。

| スモーク | cad_run exit | status | probe_status | failed_phase / next_actor | 体積mm³ |
| --- | ---: | --- | --- | --- | ---: |
| a-good | 0 | ok | pass | null / null | 22239.9556819442 |
| a-broken | 1 | failed | predicate_fail | probe / sol | 22500 |
| b-good | 0 | ok | pass | null / null | 44613.103316864086 |
| b-broken | 1 | failed | predicate_fail | probe / sol | 44751.769983530765 |

出力と失敗述語・段時間（UTC。JST=UTC+09:00）：

- a-good: [reports/cad-run/b-review-20261011t121025-a-good-fix1/result.json](../../reports/cad-run/b-review-20261011t121025-a-good-fix1/result.json)
  predicate_diff=[]。
  timings_ms={"build":204.00000002700835,"recompute":0,"probe":15.000000013969839,"save":0}。
  2026-10-11T12:10:49.290551+00:00 → 2026-10-11T12:10:49.720670+00:00。
- a-broken: [reports/cad-run/b-review-20261011t121025-a-broken-fix1/result.json](../../reports/cad-run/b-review-20261011t121025-a-broken-fix1/result.json)
  predicate_diff=["volume","faces","feature_counts","feature_chain","outer_fillet"]。
  timings_ms={"build":171.99999996228144,"recompute":0,"probe":16.00000000325963,"save":15.000000013969839}。
  2026-10-11T12:10:52.911333+00:00 → 2026-10-11T12:10:53.284976+00:00。
- b-good: [reports/cad-run/b-review-20261011t121025-b-good-fix1/result.json](../../reports/cad-run/b-review-20261011t121025-b-good-fix1/result.json)
  predicate_diff=[]。
  timings_ms={"build":218.99999998277053,"recompute":0,"probe":62.000000034458935,"save":0}。
  2026-10-11T12:11:09.119582+00:00 → 2026-10-11T12:11:09.604137+00:00。
- b-broken: [reports/cad-run/b-review-20261011t121025-b-broken-fix1/result.json](../../reports/cad-run/b-review-20261011t121025-b-broken-fix1/result.json)
  predicate_diff=["feature_counts","feature_chain","outer_chamfer","volume"]。
  timings_ms={"build":188.00000002374873,"recompute":0,"probe":46.999999962281436,"save":15.000000013969839}。
  2026-10-11T12:11:12.612081+00:00 → 2026-10-11T12:11:13.041701+00:00。

Aはgood 15面/体積22239.9556819442、broken 11面/22500で従来どおり。
B goodは全述語pass、brokenはfeature_counts/feature_chain/outer_chamfer/volumeだけ失敗。
Bの許容・体積式は変更せず、good実測と導出値の差は−7.275957614183426e-12 mm³。
worker生成UTCのdata.worker_ts転記と、親だけの行のnullも4件すべてで照合した。
