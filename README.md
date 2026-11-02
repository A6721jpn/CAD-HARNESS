# Harness2 CAD Harness — SolidWorks版

**現在はnative CAD経路がBLOCKです。SolidWorksを使う確認・本番runは、環境復旧まで実行しないでください。** 詳細は[現在のBLOCK](#現在のblockab93268)を参照してください。

## 1. 目的

LLMに作図の依頼を解かせ、SolidWorksで組み立てた形を、既存のFreeCAD版と同じ基準で評価するCADハーネスです。作図の再現性と、スキル説明文の改善効果を分けて確認します。

LLMが返すのは作図仕様の **build-spec JSON** です。LLMに任意のPython・マクロ・COM操作・ファイル読み取りを直接実行させる仕組みではありません。

## 2. 構成

CAD作成を伴う課題の経路です。質問だけの課題は、元の質問用の採点を使います。

```mermaid
flowchart LR
    R[作図の依頼] --> L[LLM: build-spec JSON]
    L --> P[固定Python: 仕様を検査]
    P --> S[COM経由でSolidWorksを操作]
    S --> F[native保存・再オープン・STEP出力]
    F --> J[FreeCAD 1.1.4: v4判定]
```

| 判定 | 変更していない基準 |
|---|---|
| 元カードの寸法判定 | 0.01 mm |
| 参照形状との形全体のずれ | 0.005 mm。全境界を双方向で確認し、最小距離や体積一致だけでは代用しない |

形状の妥当性、再読み込み、native寸法の変更・再構築・復元も確認します。SolidWorksの質量特性は補助的な照合であり、FreeCADの主判定を置き換えません。

## 3. 主要なフォルダ・ファイル

| 場所 | 役割 |
|---|---|
| [H0_PLAN.md](H0_PLAN.md) / [H0_SUMMARY.md](H0_SUMMARY.md) | 元60題から事前選択した部分H0の計画・結果 |
| [H0_PROGRESS.md](H0_PROGRESS.md) | H0からH2までの進捗、停止点、復旧記録。末尾のHandoffが最新 |
| [H2_SKILL_PLAN.md](H2_SKILL_PLAN.md) | 元スキルAと改善候補Bの比較計画・採用条件 |
| [M0_SUMMARY.md](M0_SUMMARY.md) / [M1_SUMMARY.md](M1_SUMMARY.md) | モデルなしの基本動作確認・元仕様の移植確認の記録 |
| [skills/cad-harness-v4/](skills/cad-harness-v4/) | `SKILL.md`、`contracts.md`、元の`modeling.md`、比較候補`modeling-h2-r1.md` / `modeling-h2-r2.md` |
| [tools/cad_spec.py](tools/cad_spec.py) / [build-schema.json](design/cad-harness-mvp/build-schema.json) | build-specの読み取り・仕様の契約 |
| [tools/sw_m0.py](tools/sw_m0.py) | 指定した既存SWへの接続、所有文書ガード、公開M0対照 |
| [tools/sw_m1_build.py](tools/sw_m1_build.py) | 固定のSolidWorks特徴作成プログラム |
| [tools/sw_m1_judge.py](tools/sw_m1_judge.py) / [tools/sw_m1_distance.py](tools/sw_m1_distance.py) | 既存判定との照合、形全体のずれの確認 |
| [tools/sw_h0.py](tools/sw_h0.py) / [tools/sw_h0_runtime.py](tools/sw_h0_runtime.py) | H0の準備・実行・無課金smoke、入力と実行環境の固定 |
| [tools/sw_h0_worker.py](tools/sw_h0_worker.py) / [tools/sw_h0_cad.py](tools/sw_h0_cad.py) / [tools/sw_h0_verify.py](tools/sw_h0_verify.py) | 検証済み仕様からのnative作成、STEP経路、独立検証 |
| [tools/sw_h0_budget.py](tools/sw_h0_budget.py) | 送信前予約、永続的な呼出し会計、上限管理 |
| [tools/sw_h2.py](tools/sw_h2.py) / [tools/sw_h2_runtime.py](tools/sw_h2_runtime.py) / [tools/sw_h2_fixtures.py](tools/sw_h2_fixtures.py) | H2の較正・交互比較・版固定、独立課題の作成と正負対照 |
| [design/cad-harness-verify-v4/policy.json](design/cad-harness-verify-v4/policy.json) | 変更しないv4 policy |
| [reports/sw-h0/](reports/sw-h0/) / [reports/sw-h2/](reports/sw-h2/) | 公開可能な結果・会計・停止証拠 |
| [tools/](tools/)の`test_sw_*.py` | SW版の安全境界・会計・判定の回帰テスト |

封印した正解仕様（gold）とseedは、Git除外の `reports/sw-m0/m1-private/` 以下で固定プログラムだけが扱い、LLMやGitへ出しません。生成器へ渡すのは規定の依頼文と`runtime_data`だけです。元要求・生成応答・候補CAD・rawログの非公開原本も同領域へ保存し、Gitには含めません。Git cloneだけでは、封印入力や過去の台帳が必要な本番runを再現できません。

## 4. 動かし方

### 前提

- 検証ホストは **Windows / DPC-019**。記録上のSWは2026 SP4.0、API revision `34.4.0`。
- SW COM用venvと、固定したFreeCAD 1.1.4 SDKが必要です。承認モデルは `openai-codex/gpt-6.1-sol` / `xhigh`、実績のCLIは `omp/18.11.2`。本番には承認済みのCLI環境・封印入力・台帳が必要です。
- 実行対象SWの実PIDを `CAD_HARNESS_SW_PID` に明示します。過去のPIDを再利用せず、別インスタンスへ自動で切り替えません。SWは文書0件から始め、ハーネスが作った文書だけを開閉します。
- **起動中のSWを終了・再起動しません。** 不在時だけ許可された公式3DEXPERIENCE起動経路を使います。SW無応答・COM状態不明なら停止します。ViewServer71496も操作しない指示を維持します。
- 課金前に `C:/dev/v4-ops/quota.json` の新しく有効な値が必要です。使用量55%で停止・確認、60%で停止。不明・古い値でも停止します。Codexは親＋逐次生成器の最大2台です。

PowerShellで作業ディレクトリとPythonを指定します。以下の `<...>` は、実際の未使用名や確認済みPIDに置き換える必要があります。

```powershell
Set-Location C:\dev\CAD-HARNESS-sw
$Root = (Get-Location).Path
$SWPY = 'C:\dev\solidworks\.venv-solidworks-automation\Scripts\python.exe'
$FCBIN = 'C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin'
$FCPY = Join-Path $FCBIN 'python.exe'
```

### テスト：生成モデル・SolidWorks起動なし

FreeCAD内の独立形状を使う判定テストを含みます。SWの実動作確認とは別です。

```powershell
$env:CAD_SW_M0_NATIVE = '1'
$TestBootstrap = "import sys,unittest; sys.path[:0]=[r'$Root',r'$FCBIN']; suite=unittest.defaultTestLoader.discover('tools',pattern='test_sw_*.py'); result=unittest.TextTestRunner(verbosity=2).run(suite); raise SystemExit(not result.wasSuccessful())"
& $FCPY -I -B -c $TestBootstrap
```

`ab93268`時点の[保存済み回帰結果](reports/sw-h2/skill-20261030-07r1/recovery-20261031-regressions.json)は **64/64 PASS、skip 0**。これをSW障害の解消やnative合格の証拠としては扱いません。

### 課金0の確認：環境復旧後のみ

CLIの `--help` はSW・モデルを使いません。一方、次のM0とsmokeは **モデル呼出し0でも実際のSW/FreeCADを使います**。現在のBLOCK中は実行しません。

```powershell
$env:CAD_HARNESS_SW_PID = '<confirmed-current-SW-PID>'
& $SWPY -B tools/sw_m0.py --out "$Root\reports\sw-m0\<new-m0-check>"
& $SWPY -B tools/sw_h0.py smoke --run '<new-h0-smoke>'
```

1行ずつ結果と `$LASTEXITCODE` を確認し、FAIL・STOPPED・非0終了なら以降を実行しません。正例の成功だけでなく、誤仕様の拒否、保存再読込、修復経路、文書閉鎖まで確認します。状態不明のlockを削除して強行せず、所有者不在を確認できた場合だけ記録付きでrename保全します。

### 本番run：承認と無課金確認の成功後のみ

**このREADMEは課金や再開の許可ではありません。現在は下記runを実行不可です。** `prepare` / `freeze` でコード・スキル・policy・入力・モデル・ホスト・実行環境のhashを固定し、その固定物だけで実行します。固定後に条件を変更しません。

H0の新しい独立バッチの入口です。対象は[事前選択済みの18題](H0_PLAN.md)で、`--new-batch` は過去の会計をresetする指定ではありません。

```powershell
$H0 = '<new-h0-run>'
& $SWPY -B tools/sw_h0.py prepare --run $H0 --new-batch
# prepare成功と固定内容を確認してから、別途実行する
& $SWPY -B tools/sw_h0.py run --run $H0
```

H2 epoch07復旧では、旧runを上書きせず、同条件の新しい独立課題・実行名を使う入口が実装されています。現在のv6手順では親runの指定が必要です。次の各行も成功を確認してから進めます。

```powershell
$EXP = '<fresh-experiment-name>'
& $SWPY -B tools/sw_h2_fixtures.py create --experiment $EXP
& $SWPY -B tools/sw_h2_fixtures.py controls --experiment $EXP
& $SWPY -B tools/sw_h2.py smoke --experiment $EXP --recovery-from 'skill-20261029-07'
& $SWPY -B tools/sw_h2.py freeze --experiment $EXP --recovery-from 'skill-20261029-07'
# freeze成功・新しい固定物を確認してから、別途実行する
& $SWPY -B tools/sw_h2.py run --experiment $EXP
```

`create` / `controls` / `smoke` / `prepare` / `freeze` はモデル呼出し0です。`controls` は独立dev5＋holdout5の正負20件を実SWで確認します。`--recovery-from` は `smoke` / `freeze` 専用で、`run` には付けません。同じSWインスタンス・同じsourceで対照からrunまで揃える必要があります。

- 呼出しは送信前に予約し、失敗・中断も保守的に計上します。pendingを新poolで迂回しません。
- 各poolは40回上限、承認された1バッチ50回以下の範囲で扱います。元v4本番163回枠から借りません。
- H0の旧pool **36/40** と、epoch06/07共有poolの **32/40・残8** は別会計です。復旧時は既消費と残高を継承し、新40枠は次の完全な実行単位が既存枠へ収まらない場合だけ使用します。
- 元60題や旧holdoutをH2の改善・最終確認へ使い回しません。封印、合格ライン、policy、カード、採点、時間制限を緩めて通しません。

## 5. H0・H2の現状

### H0と移植確認

- **M0/M1は過去の無課金確認が完了**。M1は元60行を保持し、CAD対象45題を移植確認、質問11行・オフライン対照4行はCAD対象外です。LLMによる60題全問正解という意味ではありません。
- **H0は選択18題が18/18合格**（作図11、質問7）。残42題は `not_run`。001の起動失敗18予約を消さず、成功した002の18回と合わせて36/40を保持しています。
- 根拠：[H0_SUMMARY.md](H0_SUMMARY.md)、[H0_PROGRESS.md](H0_PROGRESS.md)、[M1_SUMMARY.md](M1_SUMMARY.md)。過去の合格は、現在のSW環境の稼働保証ではありません。

### H2 epoch01〜07

Aは元スキル、Bは改善候補です。同じ課題をA/B交互に実行し、入力キャッシュ条件が揃った最初の5組で比較します。採用には、Bの合格がAより2件以上多いこと、重大な発明・平均呼出し数・平均active時間が悪化しないこと、最後の新しい封印5題が全合格することが必要です。形状そのものの合格基準とは別の採用条件です。

| Epoch | 記録された結果 | 結論・根拠 |
|---|---|---|
| 01 | 無課金native対照で停止。診断labelへの正解由来情報の露出を記録 | dataset全体を[隔離](reports/sw-h2/skill-20261028-01/quarantine.json)。live比較なし |
| 02 | 元Aの較正25/25。5候補すべて5/5 | 難度条件未成立、B比較なし・元版維持。[結果](reports/sw-h2/skill-20261028-02/result.json) |
| 03 | 6予約を保持。実user入力へtrial ID/filenameが露出 | 盲検化の欠陥で[隔離](reports/sw-h2/skill-20261028-03/quarantine.json)。能力成績に使わない |
| 04 | 盲検化修正後、元Aの較正25/25 | 再び難度条件未成立、B比較なし・元版維持。[結果](reports/sw-h2/skill-20261028-04/result.json) |
| 05 | 一致5組でA 4/5、B 5/5 | 利得+1で採用条件未達、元版維持。[結果](reports/sw-h2/skill-20261028-05/result.json) |
| 06 | 較正A 2/5、一致5組でA 2/5、B 2/5 | 利得0、元版維持。[結果](reports/sw-h2/skill-20261029-06/result.json) |
| 07 | 較正A 5/5→2/5、比較2組を保存後P03Aで中断。保存結果14件、保守計上15回 | 比較未完了・採用判断なし。[保存会計](reports/sw-h2/skill-20261029-07/accounting-public.json) |

epoch05・06の候補は不採用、epoch07は未完了です。最終封印holdoutの合格や、スキル改善の統計的な確証は主張していません。比較条件の詳細は[H2_SKILL_PLAN.md](H2_SKILL_PLAN.md)を参照してください。

### 現在のBLOCK：ab93268

**2026-10-31の復旧記録では、InsertSketch付近でSW本体が落ち、RPC接続が切れます。** 基本線描画・押出しでも終了を再現しました。4回の新しいSWによる無課金対照はいずれも完走せず、judge未到達です。根本原因は未確定で、ViewerやGPUを原因と断定していません。

`ab93268` は、RPC失敗後に追加COM操作をしない安全停止の修正と、BLOCKの記録です。SW障害そのものの解決ではありません。失敗した形状・描画の診断変更は戻し、既存結果・封印・基準・採点・時間制限を保っています。

- 復旧中の追加モデル呼出し **0**、共有poolは **使用32・残8**。新しい固定・epoch07再開は未実施です。
- 起動中SWをこちらから終了・再起動していません。**ViewServer71496には触れていません。**
- native環境復旧の指示を待ち、復旧後のM0/H0/独立正負対照が通るまで、本番へ進みません。
- 証拠：[BLOCK記録](reports/sw-h2/skill-20261030-07r1/recovery-20261031-BLOCK.json)、[RPC安全停止smoke](reports/sw-h2/skill-20261030-07r1/recovery-20261031-rpc-safety.json)、[最新Handoff](H0_PROGRESS.md)。証拠保管先の`07r1`は隔離済みbankであり、比較への再利用を意味しません。
