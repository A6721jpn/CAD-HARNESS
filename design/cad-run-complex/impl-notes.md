# 課題B 実装・受入記録（2026-10-11）

proto/cad-run上で、署名済みCONSENSUS.mdを実装。固定A/B registry、両CLIの--task、課題別プロンプト、
Bの幾何/履歴Probe、worker段時間と生成UTC、Chamfer省略だけの負例を追加した。

## Aと計測の不変確認

A Probeと補助関数のブロックは変更せずcad_run_probes.pyへ移設した。旧workerの入口も残した。
A fixtureのSHA256は3ad5c506d84739c4378ce80d9557800919e7c0dd6c8f46cb8ff1cbc3882393ddのまま。
原本run05のSHA256はfixtureのSOURCE_SHA256と既存テストで照合した。Aの初回プロンプトSHA256は
ea2008c9dfdb3d1c9ff732dd5c373fd431064d53744e01db9cad8921e32cc641で変更なし。
measure_rollout.pyは未変更（SHA256 9ee8cff2527ae86040bc4b663c1505e2510b2e8d6a8da7065c5e7a2cd698f90d）。
既定/明示A、一次失敗の不変性、警告・J1・cleanup条件は既存テストとAスモークで維持を確認した。
既存reportsは編集せず、新規スモークの出力と負例入力だけ作成した。

## 単体テスト

実行: python -B -m unittest tools.test_cad_run tools.test_cad_agent
結果: 24件成功（既存20件＋追加4件、0.773秒）。CAD/Sol/CLI実行は全てモック。
追加は合意の3群のみ：task/prompt/照合、B幾何と履歴の境界、段時間/未到達/UTC。
既存hostイベント試験にもworker時刻の転記を確認するアサートを加えた。

## freecadcmdスモーク

FreeCAD 1.1.4、timeout_s=300。A good→A broken→B good→B brokenの順。
goodはfixture原本、brokenは新規入力コピーのbuildでFalseを選び、AはFillet、BはChamferだけ省略。
全件でcad_exit_code=0、script_completed=true、document_closed=true、cleanup_status=exited。
強制終了なし、GUI/console切替なし、Sol/codex exec未実行。
表のtimings_msはbuild/recompute/probe/saveの順、小数3桁に丸めた実測。生値は各result.json。
0msは時計で差0を観測した到達済み区間であり、未到達のnullとは区別する。

| スモーク | cad_run exit | status | probe_status | failed_phase / next_actor | timings_ms |
| --- | --- | --- | --- | --- | --- |
| a-good | 0 | ok | pass | null / null | 203.000 / 0.000 / 32.000 / 0.000 |
| a-broken | 1 | failed | predicate_fail | probe / sol | 156.000 / 0.000 / 31.000 / 0.000 |
| b-good | 0 | ok | pass | null / null | 235.000 / 0.000 / 62.000 / 16.000 |
| b-broken | 1 | failed | predicate_fail | probe / sol | 188.000 / 0.000 / 46.000 / 0.000 |

失敗述語（実読取predicate_diff）：

- a-good: []。体積 22239.9556819442 mm³、15面。
- a-broken: ["volume","faces","feature_counts","feature_chain","outer_fillet"]。体積 22500 mm³、11面。
- b-good: []。体積 44613.103316864086 mm³、18面。
- b-broken: ["feature_counts","feature_chain","outer_chamfer","volume"]。体積 44751.769983530765 mm³、14面。

出力と実測UTC（eventsの最初→最後、JST=UTC+09:00）：

- a-good: [reports/cad-run/b-impl-20261011t113520-a-good/result.json](../../reports/cad-run/b-impl-20261011t113520-a-good/result.json)、2026-10-11T11:35:37.247587+00:00 → 2026-10-11T11:35:37.679730+00:00。
- a-broken: [reports/cad-run/b-impl-20261011t113520-a-broken/result.json](../../reports/cad-run/b-impl-20261011t113520-a-broken/result.json)、2026-10-11T11:35:46.842107+00:00 → 2026-10-11T11:35:47.215590+00:00。
- b-good: [reports/cad-run/b-impl-20261011t113520-b-good/result.json](../../reports/cad-run/b-impl-20261011t113520-b-good/result.json)、2026-10-11T11:35:56.068435+00:00 → 2026-10-11T11:35:56.559066+00:00。
- b-broken: [reports/cad-run/b-impl-20261011t113520-b-broken/result.json](../../reports/cad-run/b-impl-20261011t113520-b-broken/result.json)、2026-10-11T11:36:13.448277+00:00 → 2026-10-11T11:36:13.878092+00:00。

全ready/event行にworker生成UTCがあり、kind=eventのtsは公開data.worker_tsへ保持されることを照合。
親由来の行はworker_ts=null、公開トップレベル15キーと親tsを維持している。

## Bの導出値と実測の照合

理論値は仕様からの導出：45600−270π−416/3 = 44613.10331686409 mm³。
goodで実読取した体積は44613.103316864086 mm³。残差は−7.275957614183426e-12 mm³、
相対残差1.6309014780940062e-16で合意の1e-6以内。許容・理論式を変更せず受入した。
brokenの実読取は44751.769983530765 mm³、Chamferなしの導出45600−270πと一致する。
good/brokenの実読取面数は18/14、表面積は13030.163617567285/13195.84067435231 mm²。
面数・表面積は診断だけで、合否には使っていない。

LinearPattern.Lengthの実読取は40 mm、Occurrences=3、軸Role=X_Axis。
円筒面・円弧から抽出した穴中心は(-20,-20),(0,-20),(20,-20)、半径3、Z=0..10、上下開口。
Chamfer.Sizeの実読取は1 mmで、外周4方向の45°帯と上面78×58をProbeが検査して合格した。
ネイティブのPattern/Chamfer、配置と導出値は今回のgoodスモークで確認できた。生成/抽出の修正、
帯の拡張、理論式の観測への上書きは不要だった。B2 N=3は監督側の後続工程として未実行。

## 規模と配置

行数は末尾改行を含む通常の物理行数。Aの移設を純増へ二重計上しない。

| ファイル | 行数 |
| --- | ---: |
| tools/cad_run.py | 411 |
| tools/cad_run_freecad.py | 139 |
| tools/cad_run_probes.py | 399 |
| tools/cad_agent.py | 317 |
| tools/fixtures/cad_run_b_build.py | 106 |
| tools/test_cad_run.py | 409 |
| tools/test_cad_agent.py | 263 |
| tools/README.md | 125 |
| docs/runbook-B-plate-pocket-hole-pattern-chamfer-driver.md | 48 |

上記実装/テスト/説明の純増は569行。合意の約740行目安以内。
テスト純増は121行で約100行の目安を上回るが、3群を4メソッドと既存試験の拡張へまとめ、ネイティブ起動を増やすテストは追加していない。
