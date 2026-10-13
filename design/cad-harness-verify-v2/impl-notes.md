# VERIFY v2 Phase 2 implementation notes

Binding: [PLAN-V2-CONSENSUS.md](PLAN-V2-CONSENSUS.md)、3-party AGREE。Grok/Gemini implementation reviewは双方READY受領済み。2026-10-13のsupervisor指定レビュー後fix（grok SHOULD 1/2、NIT 3）と全offline再確認を完了、uncommitted。Sol実呼出0、Git操作0。選択commit、旧SHA保存、reviewed re-freeze、Phase 3実行はsupervisorが担当する。

## 実装と保全

- `tools/cad_verify_v2_probe.py`: used native Tipの実際のProfile/Sections/Spine選択とReferenceAxisからseedを得る。active/drivingの指定constraintだけでSketch内を推移的に辿り、負IDの原点・軸・外部参照をhubにせず、到達したdriving寸法だけを採る。証跡はfeature/link/sketch/constraint/geometry経路付き。寸法の絶対値/半値一致、geometry・stock scope・optimal bbox・独立FCStd/STEP再読込gateは既存verifyと同じ。
- `tools/cad_verify_v2_guard.py` / `cad_verify_v2_agent.py`: opt-in v2専用。P全体1、R別枠1、CAD最大2。source最大4、spec最大3、ask1、C最大4。初期CAD後に生成枠を閉じ、実際の失敗source/specと実測feedbackをRへ渡す。R後のPにもそのfeedbackを保持し、fault再注入はしない。
- 900 s/episode、初期450 s、repair450 s（R180/P60/build-export90/reimport90/cleanup30）。source/parse/repairの実起動とstage、CAD timeout・stage時刻を保存。共有10800 s内で各episode開始に960 s以上とcall枠を予約し、回答時に時計を再開始しない。guard以外の理由でeligible Rが未起動ならharness STOP。
- settledなin-schema editability missも既存repair_reason/harness_failureの判定に従ってR対象にする。`repair_time_reservation_lost` はそのepisodeの時間停止として別欄に記録し、未完了/miss・failure_class=timeoutとする。共有clock/call枠が残れば後続episodeへ進み、harness/Probe障害なら従来どおり版を止める。partial wallは集計へ残し、未完了partのCIを出さない。
- C2/C3は初回1 callを確定保存し、正質問にだけ `description bytes + LF + frozen answer bytes` を渡す新callを起動する。BOM・末尾LFなし、3 SHAをbind。追加質問はmiss、誤質問/発明/invalidはanswerなしのmiss。完了cohort各3のWilsonと正質問条件付き率を独立計算し、C/devをbarへ混ぜない。
- `tools/eval_verify_v2.py` の `run / aggregate / freeze` を追加。新prefix・`aggregate-verify-v2-*.json/csv`、上書き拒否、全60 ID保存、独立再集計。run logsのinput/answer/first-response/call-purpose/quota/source/spec/fault/成果物SHA・閉鎖/PID/exit/routeを照合。未完了cohortにはCIなし。providerの5 fieldは個別合計し、欠測はnullを維持する。
- manifestはcode、skill、schema、Probe、全test/devとv1参照、inherited AGENTS、model設定をbindする。reviewed freezeはCLI実体SHAと `--version` もbindし、before-callで変更を止める。Phase 2 manifestはCLI/commit未確定のためlive起動を拒否する。
- testは86 files（15 items、13 analytic geometry gold、31 standalone native sources、rubric、fault、answer/binding）。descriptionはbinding表＋指定suffixそのまま、Kは対応Wと同一bytes。生成器と独立した手製native sourcesで確認した。v1 testと保存済みV5 FCStdはdevのSHA付き参照で、原本を移動・変更・再採点していない。
- run-order: dev3 → legacy4 → fresh eval-v1 10 → clean W/S18 → A13 → C6 → K6。合計60、scored core/regression51。planned83/max163 calls、v1 class対応と全bar閾値はbindingどおり。
- 開始時SHAとの照合: 既存tools44のうち変更はopt-in起動を追加した `cad_run.py / cad_run_freecad.py / cad_verify_freecad.py` の3つ。既存design213、skill1、reports5131は全てbyte一致。`cad_agent.py`、v1 Probe/Guard/evaluator、`eval_mvp.py`、eval-v1 gold/barはbyte一致、MVP clarification retryも既定のまま。

## Fix log（全てSol前）

1. Native Probe preflight r1 (`.tmp/verify-v2-api/native-first.txt`): geometric relationに `getDriving(i)` を呼ぶと `ValueError: Invalid constraint id`。`Curve.isSame` は `(geometry, linear_tol, angular_tol)` を要求した。v2 Probeだけを修正し、relationの `Constraint.Driving` と正しいAPI引数を使用。native testsを最初から再実行、3/3成功 (`native-r2.txt`)。保存v1 V5 r1/r2でPCD60の到達証跡とgeometry/editability真を確認。gold/tolerance/gate変更なし。
2. 初期gold serialization: rect_prismの未使用 `regions` をschemaが要求する空配列へ修正。最初の測定前のserialization修正で、description、寸法、式、volume targetは変更していない。
3. Native batch r1: A1 positiveは全gate成功、期待/実測V=53057.522203923065。negativeはgeometryを落としたが、未使用の片側extrusion `Length2` 既定値5/10 mmが不足するdriving寸法を供給したためcontrol不一致で停止。fixture sourceのType=0 extrusionで未使用 `Length2=0` を明示。意図したgeometry/gold/gate/tolerance変更なし。r1出力を保持し、全batchをr2から最初から再開、41/41成功。UTF8 bytes保存と実注入source SHA確認を強化後、r3でも全batchを最初から再実行して41/41成功。
4. Evaluator mock integration: manifestの `first_response` はstopモードflagでありCのrubricロードとは別、rowの実応答とも別。Cはrouteでrubricをロードし、frozen entryを `manifest_entry` として保存・照合するよう修正。60 episodeのmock runと独立aggregateが成功。
5. 最終C guard照合: 正質問後、quota等で回答callを未起動でも到達真とする記録を修正。実際にanswer込みのinterpretation callを起動した時だけ `completion_reached=True`。正質問のscore、未到達理由、partial usageは残し、guard停止episodeは未完了としてCIを出さない。quota55%でquestion1/CAD0/answer未起動をmock確認。CLI実体SHA・versionのreviewed freeze検証も追加した。
6. レビュー後fix（supervisor指定、2026-10-13、Sol前）:
   - grok SHOULD 1: agentのspec/editability missを `compiler_native_failure` へ置換する分岐と、evaluatorの同じrepair eligibility除外を削除。settled repairable条件をsource/specで共通にした。W6/S2/A1/C2/C3/K3で実R1（R応答の構文失敗後は共有P1）、独立recordのeligible真、モデル修復失敗はcompleted missでありharness停止しないことをunitで確認。Probe例外時のharness停止も既存unitで維持。
   - grok SHOULD 2: `repair_time_reservation_lost` のharness分類を除去。`episode_stop_reason` と `repair_not_attempted_reason` に理由を保存し、その回はtimeout/未完了、実R0とする。runは同一共有clock/countersで次の回へ進み、aggregateはpartial wallを保持する。別prefixの60-episode mockで、settled W6 r1後の遅延により450 s予約が失われる条件を再現。W6 r1のみ未完了、次回以降完了、run/aggregateの版stop_reasonなし、W6はsuccess2/予定3・completed2・CIなし、bar未達を確認。900 s/3 h・quota/call不足・実harness停止を緩和していない。
   - grok NIT 3: v2 Guardをv1の125上限で初期化してから書き戻す処理を廃止し、共有状態をv2の1..163で直接初期化。163回のadmission成功、164回目拒否、要求上限164拒否、v1 Guardの126拒否をunit確認。v1 Guard原本は変更していない。
   - その他のNITは適用していない。変更はv2 agent/guard/evaluator/unitと本notesのみ。Probe、native fixture source、gold、description、rubric、answer、fault候補、run-order、dev refs、SHA manifest、レビュー原文は変更しなかった。

正例とgoldの測定値不一致は発生していない。解析gold式はbinding表から独立再計算しunit確認済み。レビュー後full batchでもS2はscope V=45500（期待45500）、full V=60924.08914058348はrecord/成果物一致専用でありgoldとの不一致ではない。

## 最終結果と再現commands

FreeCADは指定 `C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe` のみ、headless実行。sandbox内で成功した。

| 確認 | 結果 | 証跡 |
| --- | --- | --- |
| 全unit（TEMPはtest_supportでredirect） | 91 tests、85 PASS/6 native skip、37.556 s | `python -B -m unittest discover -s tools -p "test_*.py"` |
| native v2 unit | 3/3 PASS、2.400 s | `.tmp/verify-v2-review-fix-native/test_verify_v2_native/native.log`、08:49:07 JST |
| 既存DV3 native unit | 3/3 PASS、0.868 s、documents_closed真 | `.tmp/verify-v2-review-fix-native/test_verify_dv3_native/native.log`、08:49:09 JST |
| 全新native/rubric smokes（最初から再実行） | 41/41 PASS、STOPなし | `reports/cad-run/20261013-verify-v2-review-fix-native-r1-mvp1/smoke-summary.json`、2026-10-13 08:49:31 JST |
| legacy 4 smokes | 4/4 PASS、全closed/exited/native exit0 | `reports/cad-run/20261013-verify-v2-review-fix-legacy-r1-mvp1/smoke-summary.json`、2026-10-13 08:49:08 JST |
| 60-episode mock run/aggregate | 基準batch PASS（mock calls82/dev4/P1/R6、C2完了1/3でもbar真）。別prefixの時間停止batchも後続継続・独立aggregate検証PASS | `tools/test_verify_v2.py`、provider/CAD完全mock、aggregateはprocess起動0 |
| frozen/preflight | 旧phase2 manifest原本保持。レビュー後code4 files分はstale、supervisorがarchiveしてre-freezeする | `SHA256.json`、version=`verify-v2-phase2-uncommitted`、commit pending/CLI null、live拒否を維持 |

41 controls = geometry手製13 positives/13 negatives + W5 decoy/reference/inactive3 + K actual injected faults3 + K3 compiler-positive1 + A2/A3/C2/C3 rubric正負8。全14 CAD positivesでnative/editability/geometry・独立FCStd/STEP・PID別・closed/exited/exit0を満たし、全19 CAD negativesを想定どおり拒否した。K1/K2/K3はnative valid/settledで指定predicateを検出。Native unitは保存済みv1 V5両方のPCD60、chain/isolated loop/origin/reference/inactive decoys、partial selectionも確認した。

手製K1/K2とK3の実native失敗feedbackで修復argvをoffline構成して、UTF16長17113/18291/13995（上限30000以内）を確認。Rへ実source/specを渡し、巨大なconstraint証跡はCAD reportに残す。

保存した旧Phase 2 manifest SHA256: `71812acc039f940cc19e61a1a7eedf4a1c1ff03c450023e969115eca5dc57e37`（今回変更していない。最新codeの凍結証明として使わない）。binding plan SHA256: `ac4455b972c6e2a3b086e0bf21addd4d512f8b2b08256dfdffba85ddd54faa7d`。本notesとreview文書、可変quota snapshot、生成reportはmanifestのdata範囲外。

最終保全照合（2026-10-13 08:53:22 JST）: 開始時のsource/design/skills hashesとの差分は上記v2 code/unitの4 filesと本notesのみ、追加filesなし。旧manifest全187 entriesを再計算し、変更した4 code entries以外の183 entriesは一致。gold/data/test-item、binding plan、レビュー原文、v1/MVPは不変で、旧SHA256.json原本のdigestも一致した。

以下はsupervisor hostでの再確認。QA prefixは実行ごとに新しくする。nativeはexit codeだけでなくsuccess markerとunittest結果も確認する。

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
python -B -m unittest discover -s tools -p "test_*.py"
if ($LASTEXITCODE -ne 0) { throw 'unit failed' }
$qaTag = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfff')
$nativeCfg = "C:\dev\CAD-HARNESS\.tmp\verify-v2-host-native-$qaTag"
New-Item -ItemType Directory -Path $nativeCfg -ErrorAction Stop | Out-Null
& 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe' --user-cfg "$nativeCfg\v2-user.cfg" --system-cfg "$nativeCfg\v2-system.cfg" C:\dev\CAD-HARNESS\tools\test_verify_v2_native.py 2>&1 | Tee-Object -FilePath "$nativeCfg\v2.log"
if (-not (Select-String -LiteralPath "$nativeCfg\v2.log" -SimpleMatch 'VERIFY_V2_NATIVE_OK=True')) { throw 'native v2 failed' }
& 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe' --user-cfg "$nativeCfg\dv3-user.cfg" --system-cfg "$nativeCfg\dv3-system.cfg" C:\dev\CAD-HARNESS\tools\test_verify_dv3_native.py 2>&1 | Tee-Object -FilePath "$nativeCfg\dv3.log"
if (-not (Select-String -LiteralPath "$nativeCfg\dv3.log" -SimpleMatch '"passed": true')) { throw 'native DV3 failed' }
python -B tools\smoke_verify_v2.py --run "host-verify-v2-offline-$qaTag-mvp1"
if ($LASTEXITCODE -ne 0) { throw 'native smoke STOP; derive analytically before any fix' }
python -B tools\smoke_cad_mvp.py --run "host-verify-v2-legacy-$qaTag-mvp1" --group legacy
if ($LASTEXITCODE -ne 0) { throw 'legacy smoke failed' }
```

## COMMIT PLAN（supervisorのみ、pushなし）

1. Message: `feat(cad): add verify-v2 probe and guarantee settled spec repair`。Paths: `tools/cad_run.py`, `tools/cad_run_freecad.py`, `tools/cad_verify_freecad.py`, `tools/cad_verify_v2_probe.py`, `tools/cad_verify_v2_guard.py`, `tools/cad_verify_v2_agent.py`（レビュー後修正済み、v2 cap163直接初期化・settled spec編集性missもR対象）。
2. Message: `test(cad): author analytic verify-v2 holdout and native controls`。Paths: `design/cad-harness-verify-v2/test/`, `design/cad-harness-verify-v2/dev/`, `design/cad-harness-verify-v2/run-order.json`, `tools/fixtures/verify_v2_native.py`。
3. Message: `feat(eval): isolate verify-v2 episode time stops and aggregate independently`。Paths: `tools/eval_verify_v2.py`, `tools/smoke_verify_v2.py`, `tools/test_verify_v2.py`, `tools/test_verify_v2_native.py`, `design/cad-harness-verify-v2/impl-notes.md`（SHOULD 1/2/NIT 3回帰unitを含む）。旧SHA原本は保存資料であり、最新codeをfreeze済みとは扱わない。
4. Message: `docs(cad): freeze reviewed verify-v2-r1 before host measurement`。Paths: reviewed `design/cad-harness-verify-v2/SHA256.json`、保存した旧phase2 SHA manifest、`grok-impl-review.md / gemini-impl-review.md` とsupervisorのfreeze記録。implementation commitは1–3の最終修正が全て含まれるcommitのSHA、plan commitは3-party署名済みbindingのSHAをmetadataに記録する。

`.tmp/`、generated native/smoke reports、dashboardは上記source commitsへ含めない。v1 files/manifestを更新しない。Grok/Gemini READYとsupervisor指定修正の再検証を受領・完了済み。こちらから他モデルの代理レビューはしていない。

## 正確なhost freeze commands

前記レビュー・選択commit完了後、旧SHAを保存してからfreezeする。上書き禁止。変更後は旧measurementsを保持して新version/fresh holdoutへ進める。

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
$verifyBase = 'C:\dev\CAD-HARNESS\design\cad-harness-verify-v2'
$phase2Manifest = Join-Path $verifyBase 'SHA256.json'
$archiveManifest = Join-Path $verifyBase ("SHA256.phase2-" + [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfff') + '.json')
if (-not [IO.Path]::GetFullPath($archiveManifest).StartsWith($verifyBase + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'archive path outside workspace' }
if (Test-Path -LiteralPath $archiveManifest) { throw 'archive exists' }
Move-Item -LiteralPath $phase2Manifest -Destination $archiveManifest -ErrorAction Stop
$implementationCommit = Read-Host 'Committed implementation SHA (commits 1-3 included)'
$planCommit = Read-Host 'Committed three-party binding plan SHA'
python -B tools\eval_verify_v2.py freeze --version verify-v2-reviewed-r1 --implementation-commit $implementationCommit --plan-commit $planCommit --codex codex.exe
if ($LASTEXITCODE -ne 0) { throw 'freeze failed; no live calls' }
Get-FileHash -LiteralPath "$verifyBase\SHA256.json" -Algorithm SHA256
```

新manifest・archive・レビュー記録をcommit 4へ選択commitし、version/commit/CLI/manifest digestをfreeze記録に保存する。Phase 2のpending/CLI-null manifestではdevを含む全live呼出が拒否される。

## Phase 3 host run / aggregate

snapshotはsupervisorの**実測**使用率を入力して、開始前と稼働中5分以内ごとに別host terminalから更新する。percentageをtoken推計や固定仮値で作らない。missing/invalid/future/stale>300 sはSTOP、55%以上soft STOP、60%以上hard STOP。下記writerはUTF8 BOMなし・一時fileから置換する。

```powershell
$quotaPath = 'C:\dev\CAD-HARNESS\.tmp\verify-v2-supervisor-quota.json'
$quotaStage = 'C:\dev\CAD-HARNESS\.tmp\verify-v2-supervisor-quota.stage.json'
$measuredPercent = [double](Read-Host 'Actual supervisor quota used_percent')
$quotaRecord = @{ snapshot_id = [guid]::NewGuid().ToString(); observed_at = [DateTimeOffset]::UtcNow.ToString('o'); used_percent = $measuredPercent }
[IO.File]::WriteAllText($quotaStage, ($quotaRecord | ConvertTo-Json -Compress), [Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $quotaStage -Destination $quotaPath -Force -ErrorAction Stop
```

reviewed freeze commit完了後のみ、以下を同一bootで連続実行する。共通3hはrun開始からindependent aggregate終了まで。STOP後にdeadline/counterをresetして続行しない。suffix/prefixが既存なら上書きせずsupervisor判断へ戻す。

```powershell
Set-Location -LiteralPath C:\dev\CAD-HARNESS
python -B tools\eval_verify_v2.py run --prefix host-verify-v2-reviewed-r1 --quota-snapshot C:\dev\CAD-HARNESS\.tmp\verify-v2-supervisor-quota.json --call-budget 163 --codex codex.exe
$verifyRunExit = $LASTEXITCODE
python -B tools\eval_verify_v2.py aggregate --prefix host-verify-v2-reviewed-r1 --suffix host-reviewed-r1
$verifyAggregateExit = $LASTEXITCODE
Write-Output "run_exit=$verifyRunExit aggregate_exit=$verifyAggregateExit"
```

Outputs: `reports/cad-run/host-verify-v2-reviewed-r1-verify-v2-suite-mvp1/{plan.json,progress.jsonl,suite-run.json}`、各episodeの新run directory、`reports/aggregate-verify-v2-host-reviewed-r1.json/csv`。終了コードaggregate 1はbar未達、2はinput/freeze/guard等の停止。全予定IDと失敗理由を保持する。

最初のharness/Probe/export/save/reimport/cleanup/PID/SHA/false-passで版を止める。positive mismatchはdescriptionから先に再導出し、expected/actual/式を記録する。gold算術誤りならSTOP報告し自己編集しない。fixture/Probe欠陥はSol前だけ修正記録して全native batchを新prefixで最初から再実行する。freeze後のfixは旧結果を保存し、新版をfresh holdoutで別測定する。

Dashboard: `.dashboard/public/index.html` を更新済み。Tailscale Serve状態照会は保護pipeへのAccess deniedで未検証、設定変更・公開URLの推測はしていない。
