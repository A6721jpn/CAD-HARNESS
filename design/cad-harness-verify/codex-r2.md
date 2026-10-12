# CAD-HARNESS VERIFY — Codex R2 cross-critique

2026-10-12。grok-r1と自案を再読した収束提案。数時間の検証を優先し、自R1の全型N=5・注入15・回答付き曖昧さ20を撤回する。
CLI/skill/promptの境界、指定FreeCAD 1.1.4 headless、gpt-6.1-sol/xhigh、3 calls/3 CAD/900秒、gold不変は維持。

## (a) 範囲外suite

ACCEPT：5型×N=2、verify-v1 Probe、description→unsupported→sourceの実経路を確認。compilerのみの成功はfallback miss。
COUNTER：grok V1の単純溝ピンは3段shaft、V4の箱は底＋4壁のrect_stackで表せ、範囲外を強制できない。
修正版はcodex-r1 V1–V5：中空溝ローラー、四角loft、90°曲管sweep、箱＋三角rib、円形フランジの円周穴＋直線溝列。
その説明・式・断面/空隙/肩/壁厚/配置checksを採用し、Native/FCStd/STEP/closeを全成功runに要求する。
COUNTER：loft/sweepの正しい曲面を許すことには合意するが、余計な加工を一律record-onlyにはしない。要求した面・断面・開口をgoldで検査する。

## (b) 修復・fault injection

ACCEPT：自然な初回失敗は観測、注入は別集計。specのF1をN=3、sourceのF2をN=2、計5 episodesへ削減する。
F1は別寸法の対応内plateでpocket depth×2（底を貫かない）。F2は別寸法の中空溝ローラーで穴径＋1 mm、agent modeからsource修復を測る。
specは機械的変異、任意sourceへの文字列置換はCOUNTER：source側は凍結した誤native candidateを一度だけ差し替え、原出力/注入物SHAを保存する。
盲穴faultは今回は採らずV1系へ集約する。初回Sol callも計数し、実Probeのexpected/actualから実Solで修復、同じ総予算を共有する。
COUNTER：injectedフラグで強制failにせず実測で失敗させる。not_reachedを主分母から除外しない；成功/予定5、成立/5、成功/成立を併記する。
自然修復率は初回の修復可能CAD失敗を分母とし、0件ならN/A。parse修復は別。注入成績を自然文成功率へ混ぜない。

## (c) 曖昧さ

ACCEPT：grok Q2/Q3（厚さ欠落・穴位置欠落）各N=5、初回1 callだけ、CAD=0。固定follow-upと対話機能は今回撤回する。
必要不足fieldを尋ねるneeds_clarificationだけ1点。発明した値、unsupported、invalid output、call_limitは0点；field ID＋凍結rubricでCLI採点する。
grok Q1（原点省略）N=3も採用：XY中心/底Z=0の初回対応と最終幾何gateが必要、不要質問は後で成功しても0点。
停止flag/1-call上限はVERIFY opt-in。既存MVPのclarification retryを変更しない。回答後の建模性能は未検証と明記する。

## (d)(e) 複雑形状・N・CI

ACCEPT：全型N=5は費用に比して広げすぎた。複雑な対応内形状はcodex V6（2 pocket＋6穴＋面取り）N=3へ一本化し、grok C1/C2両方は採らない。
新寸法のsimple prism＋pocket＋RをS1、N=5で採用。自然文CADはV10＋C3＋S5、既定値Q1の3件を別群として記録する。
95%両側Wilson（z=1.96）を各完了batch/partに報告。N=2は経路確認のpilotであり、N=5のS1も未知形状の信頼性を示さない。
順・Nを先登録しfresh/逐次、warm-up除外・失敗差替え・結果を見た追加Nなし。未完了batchはCIと実用合格を主張しない。

## (f)(g)(h) 回帰・metrics・分離

ACCEPT：MVPの全runtime/rules/settings/SHAが完全一致するときだけ旧集計を回帰証拠にできる。ただし新profileでdriver/Probe変更を見込むので新eval-v1×10を予算へ入れる。
8/10＋各1/2・P1帯・goldは不変。legacy A/Bはunitとgood/broken計4 offline smokes、追加Solなし。
ACCEPT：provider usageのみ・欠測null、全失敗の分類。初回/最終gate、経路、修復率/分母、calls、CAD/repair attempts、全run wall中央値/p95/最大を別群で出す。
ACCEPT：dev/test別directory、devは各型の別寸法offline fixture＋最多4「実Sol calls」（4 runsではない）。同じtest candidateで注入実装を調整しない。
COUNTER：test前だけの凍結では遅い。dev/testの説明・gold・fault・rubric・順はどのSolより前に人手確認/SHA/local commit；code/skillはdev後に最終凍結。
testを見た修正は新版＋新未使用testへ。生成/初回contextにgoldを入れず、case名/SHA lookup禁止。新reportsのみ、supervisor local commits/no push。

## (i) bar・予算・停止・実装順

COUNTER：各Vの1成功・注入1成功・Q/C/Sの単なる報告だけでは実用判定が弱い。
提案bar：V群≥8/10かつ各≥1/2、C≥2/3、S≥4/5、既定値Q1≥2/3、Q2/Q3各≥4/5かつ重要寸法の黙った発明0。
注入は成立5/5・所定の初回fail5/5・修復≥4/5かつspec/source双方≥1成功。MVP/legacy回帰、全成功成果物gate、false passなしも必要。
このbarは「列挙した部品で、人が仕様を確認して編集可能な初稿を得る経路を小標本で確認」。汎用成功率・GUI・全履歴追従・製造適性を保証しない。
計画callsはV20＋C3＋S5＋Q1=3＋不足Q10＋F10＋dev4＋MVP10＝65。通常CAD群21×3＋不足Q10×1＋F5×3＋dev4＋MVP10×3＝最大122。
旧MVP再試行不要なら計画55、最大92。仮のinput50k/output5k per call予約は65–122でinput3.25–6.10M/output0.325–0.610M；source実績・週次割合の保証ではない。
ACCEPT 60% hard stop、追加で55% soft stop。各run/repair call前にホスト使用率確認、取得不能/鮮度不明も停止。token→使用率は換算しない。
ACCEPT 3h上限、COUNTER batch境界だけの確認：dev Sol/回帰/新suiteを含め共通deadline、各runをmin(900秒,全体残時間)へclipし回収も含める。
環境/Probe/保存/再読込/未回収PID、SHA不一致、false passは最初の確定harness障害で停止。quota/時間/未完了は未達、隠れた差替えや成功までの再開なし。
順：全入力/gold凍結→verify Probe/used native linksと手製fixture→opt-in停止/注入/集計の最小mock→dev4 callsと版凍結→回帰→固定test→限界付き集計。

R2ではこの提案だけ作成。コード・FreeCAD・Sol・Gitは実行しない。
R2 DONE
