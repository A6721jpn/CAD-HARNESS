# CAD-HARNESS VERIFY v1 — PLAN-CONSENSUS

2026-10-12 R3。Phase 2/3の単一実行仕様。R1/R2の選択肢は本書で置換する。Codex合意、grok署名は末尾の状態による。
R3b変更：S1の隅接合に依存する全体積goldを正確な下部stock体積＋局所R2断面へ置換し、V6面取りの角補正を断面積分で再確認した。MVP gold/barは不変。
目的はMVPの未検証経路を数時間で確認すること。新たな成功率・agent時間・使用量はまだ実測していない。
CLI＝実行/検査/採点/診断整形、skill＝解釈・建模判断、prompt＝ユーザーの今回の説明だけ。LLM judgeは追加しない。
FreeCADはC:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exeのみ、headless。
Solは既存driverのgpt-6.1-sol/xhigh・tools無効・read-only。GUI/Fusion/SolidWorksなし。Claudeはorg access無効で利用不可。

## 固定test：形状とgold

V1–V6はcodex-r1の形状・寸法を採用する。下表の説明本文をUTF-8で凍結し、引用符・表記用注記をpayloadへ加えない。
V1–V5はdescription→unsupported→sourceを要求。schemaを拡張して対応内へ移さず、agent modeへ入口変更もしない。
V6/S1は対応内。幾何成功と経路を別記録し、fallbackの省略や形状の近似を成功と扱わない。

| ID / N | 凍結するユーザー説明 | goldチェックと導出体積mm³ |
| --- | --- | --- |
| V1 / 2 | Z軸の中空ローラー。外径32、長さ36、下端Z=0。中央に直径8の貫通穴。外周のZ=14..18に幅4、半径方向深さ2の全周溝。単位mm。他の加工なし。 | 外径32/内径8、溝外径28・区間/肩、Z=9,16,30の環状断面、穴の両端開口/空隙、bbox、V=8400π。 |
| V2 / 2 | 中実の四角テーパー。Z=0は40×24、Z=30は24×16の長方形。XY中心をそろえ、ねじれなしで寸法が高さに比例して縮む。単位mm。穴や丸みなし。 | Z=0,15,30の断面40×24/32×20/24×16、中心/方向/斜面/端面、bbox、V=19520。 |
| V3 / 2 | XY平面で90度曲がる管。中心線半径25、外径12、内径8。中心線は(0,0,0)から+X向きに出て(25,25,0)へ+Y向きで到着。単位mm。両端開口、一定断面。 | R25/90°、端面、始点/45°点/終点の法線断面D12/D8、内腔空隙、bbox、V=250π²。 |
| V4 / 2 | 上面開口の箱。外形X=-30..30,Y=-20..20,Z=0..20、壁と底3。内側にY=-1.5..1.5の三角リブ。XZ断面の頂点は(-27,3),(27,3),(27,15)。単位mm。穴なし。 | 壁/底3、開口/内腔54×34、rib厚3/三角断面/接続、bbox、V=48000−54×34×17+54×12×3/2=17760。 |
| V5 / 2 | 円形フランジ外径84、厚さ8、中央に直径20の通し穴。PCD60に直径5の通し穴8個、+Xから45度刻み。上面に長手Xの12×4、深さ2の溝3本、中心(-16,-15),(0,-15),(16,-15)。単位mm。 | 外形/中央穴、8穴の径/中心/角間隔/開口、3溝の位置/床/深さ、bbox、V=12912π−288。 |
| V6 / 3 | 110×76×12の板、XY中心、下面Z=0。上面から26×18、深さ5のポケットを中心(-26,0),(26,0)に2つ。直径4の通し穴をX=-36,0,36、Y=-27,27の6点に。上面外周だけ脚0.8の面取り。単位mm。 | 2ポケット/6穴の位置/深さ/鋭い縁/開口/空隙、外周C0.8、bbox、V=95640−288π−(186×0.8²−4×0.8³/3)。 |
| S1 / 5 | 58×42×16のブロック。XY中心、下面Z=0。上面中央に18×14、深さ4のポケット。上面の外周4辺だけR2。垂直辺は鋭く残す。単位mm。穴や面取りはなし。 | 外形/ポケット/外周R2/鋭い内縁/垂直辺。全体積targetなし、solidをZ=0..12で切ったstock体積=58×42×12=29232。局所R2断面は下記で固定。 |

### S1/V6の体積根拠（FreeCAD未実行）

S1を二つの円筒面の交線で接合する場合、上面からの深さs∈[0,r]に対し片側の除去幅a(s)=r−√(2rs−s²)。外側断面は(W−2a)(D−2a)。
従って除去体積=∫[2(W+D)a−4a²]ds=(2−π/2)(W+D)r²−(20/3−2π)r³。旧式の正の角項はこのモデルの重複除去の補正である。
球octant式は別の隅形状の仮定。上面4辺だけという条件からFreeCADのvertex patchがどちらと一致するかを未実行で保証しないため、双方を全体積goldに採らない。
これは[OCCT APIの一般説明](https://occt3d.com/dev/doc/refman/html/class_b_rep_fillet_a_p_i___make_fillet.html)を当該FreeCAD配布の隅形状の証明として扱わない判断である。
S1のpocket床はZ=16−4=12、R2の辺断面加工帯はZ=14..16。床以下のstockは加工されない58×42×12の直方体で、その体積29232は隅接合に依存しない。
Gold volume_scopeはworldの[-29,29]×[-21,21]×[0,12]とし、実BRepとの共通部分の体積を相対1e-4で検査する。全体積は必ず測定・記録し、FCStd/STEP間の全体積相対1e-4比較も保持する。
局所R2は隅を避けたY=0のXZ断面で中心(±27,14)、X=0のYZ断面で中心(±19,14)の四分円と接線を検査。Z=15では外側境界x=±(27+√3)、y=±(19+√3)、内側空隙はそれぞれ|x|<9、|y|<7。
隅のpatch体積そのものはS1で採点しない。bbox/ポケット床・壁・開口/鋭い内縁/垂直辺/全4辺R2/正常solidの検査は省かず、どの必須fixture不一致もSol前停止のままとする。
V6は平面chamferで曖昧さがない。上面からs∈[0,c]でa=c−s、断面の除去面積=WD−(W−2a)(D−2a)=2(W+D)a−4a²。
積分すると除去体積=(W+D)c²−4c³/3。W=110,D=76,c=0.8、pocket/穴はこの帯と交差しないため、表のV6式をそのまま保持する。球面角項を使わない。

通常の1 run合格は実gold幾何、valid solid=1、単一Body/native Tip/使用Sketch links/主要駆動寸法/正常recomputeの薄い編集gateをすべて満たすこと。
FCStd＋STEPを保存し、生成source/compilerなしの別freecadcmdで同じgoldを採点する。両文書close、所有PID回収、正常exitも必要。
verify-v1 Probeを新設：寸法±0.01 mm、方向1e-6、gold体積相対1e-4（S1は指定stock範囲、他は全体）、成果物間は全bbox±0.01 mm/全体積相対1e-4。欠測・未対応predicateはfail。
要求した面/断面/壁/空隙を検査し、正しい曲面を許す。feature/face/edge個数は記録・助言のみ。要求外加工を一律record-onlyにはしない。
V2中間断面を含む全gateはSol前に独立した手製native fixtureで確認する。不一致なら停止し、goldを観測値へ合わせたりgateを落としたりしない。

## 曖昧さの選択：初回だけ、follow-upなし

| ID / N | ユーザー説明 | 期待と採点 |
| --- | --- | --- |
| Q1 / 3 | 70×40×10の板。中央に直径8の通し穴。単位mm。他の加工なし。 | 初回specでXY中心/底Z=0、不要質問なし＋最終全幾何gate。bbox=(-35..35;-20..20;0..10)、D8、V=28000−160π。 |
| Q2 / 5 | 80×40の板。XY中心、下面Z=0。四隅に直径4の通し穴、穴中心は外形からX方向10、Y方向8。単位mm。他の加工なし。 | 欠落plate_thicknessを尋ねる。幾何goldはなくrubricだけ。 |
| Q3 / 5 | 60×40×10の板。XY中心、下面Z=0。直径6の通し穴2個。単位mm。他の加工なし。 | 欠落hole_positionsを尋ねる。幾何goldはなくrubricだけ。 |

Q2/Q3は1 real callで必ず終了、CAD=0。必要field IDだけのneeds_clarificationを1点、発明値/unsupported/invalid/別field質問を0点。
field ID契約とCLI定型質問はdeveloper context側、期待不足fieldはgold/rubric側。ユーザー説明に採点ヒントを加えない。
Q1は初回の既定値対応と最終gateを満たして1点、後から修復しても初回不要質問は0点。Qのscoreは自然文幾何成功率へ混ぜない。
VERIFY opt-inのfirst-response/clarification停止を追加し、MVPのneeds_clarification retryは不変。回答後の対話・建模は本版の対象外。

## faultの選択：description modeで3種類×N=2＝6 episodes

F1=V1の全周溝欠落source、F2=V5のPCD穴1個欠落source、F3=V6の穴1個をD4→D6とするspec。
初回のcontract-valid source/schema-valid specの後、候補を一度だけ変更し、実CAD/Probeのsettled geometry failから通常の実Sol repairへ進む。
source側は凍結した誤native candidateの差替えを採用し、任意sourceへの脆い文字列置換をしない。spec側は凍結した数値変異を行う。
原出力/注入物SHA・fault ID・実際のcallを保存。注入物はofflineで正常native構成かつ所定幾何failを確認。injectedフラグでfailを強制しない。
F1/F2は解釈→source→repairの通常3 calls、F3はspec→repairの通常2 calls。生成失敗やnot_reachedも予定6件の主分母に残す。
検出/6、成立/6、最終全gate pass/6、pass/成立を併記。自然修復は初回の修復可能CAD failを分母、0ならN/A。parse修復は別集計。
上限をリセットせず、正解sourceを修復に差し込まない。モデル由来のrun失敗は集計、確認されたharness障害は版全体を停止する。

## 分離・凍結・統計・回帰

dev/は各型の別寸法offline fixturesと別文面のpilotだけ、test/は上記V/S/Q/F。testでinjectorや生成規約を調整しない。
test/dev全文・人手gold数値/表示式・rubric・fault candidates/対象・run順・SHA manifestをどのSolより先にsupervisorがlocal commitする。
dev-liveは最大4 real Sol callsで資源見積/経路を確認、test率に含めない。本版はPhase 2のcode/skill凍結後に行い、pilotを見た途中調整もしない。
code/skill/build schema/Probe/CLI/model設定/継承AGENTSの版を固定。生成・初回contextにgoldなし、compilerのcase名/description SHA lookup禁止。
test後の修正は旧失敗を保存し、新版＋新未使用testで別計画。旧版の未達を成功runで差し替えない。
全件fresh・逐次、先登録したN/順、warm-up除外・手修正・成績を見た追加Nなし。95%両側Wilson(z=1.96)は完了batch/partだけ。
異なる形状や注入/曖昧さをpoolして一般JA/ENの信頼区間にしない。未完了batchはCIなし、planned/completedを明記する。
新eval-v1 P1–P5×2を新prefixで必ず再実行。gold/P1例外帯/8-of-10かつ各1-of-2は不変、旧10/10を代替にしない。
legacy A/Bのgood/broken計4 offline smokes＋必要な既存unit回帰、追加legacy Solなし。judge_stubは無効のまま。
各runに初回/最終geometry/editability/reimport/pass、unsupported→source経路、call種別、CAD/repair attempts、failure class、Q score、injected/reachedを記録する。
wallは失敗込み中央値/p95/最大。provider input/cached/cache-write/output/reasoningを個別記録、欠測null。推定tokenや推定料金は実績にしない。
新prefix/aggregateだけ、既存reports/fixtures/goldへ上書き禁止。通常幾何・Q・F・MVP・devは別表、全planned IDsと停止理由を保存する。

## quota・時間・予定calls

余分な修復なしの計画calls：V20＋V6 3＋S5＋Q1 3＋Q2/Q3 10＋F16＋dev4＋MVP10＝71。
最大calls：通常CAD群21×3＋Q2/Q3 10×1＋F6×3＋dev4＋MVP10×3＝125。first-response runsにも隠れたretryを行わない。
予約用仮定input50k/output5k per callならinput3.55–6.25M/output0.355–0.625M。これは未実測のagent予算枠で上限保証ではない。
MVP短JSONの観測平均input34910.5/output657.4をsourceへ外挿しない。token→週次%換算は不明、devの実績で残予算を確認する。
各real call前にsupervisor snapshot(使用%、確認日時)をCLIで検査。鮮度は5分以内、欠落/古い/未来日時/不正値はstop；snapshot識別も記録する。
55%以上でsoft stop、60%以上でhard stop、新call禁止。残budgetが不足しても開始しない。CLIがquotaを自動取得できるとは仮定しない。
Phase 3のdev/回帰/test/保存/close/回収/集計全体に共通3hの単調deadline。各runはmin(900秒,全体残秒)、各CAD/再読込はmin(300秒,run残秒)へclipする。
cleanupの余裕を工程開始前に確保し、deadline以後の成功は数えない。quota/時間停止は未完了・実用判定未達、Nや予算を自動延長しない。
最初のlaunch/save/export/reimport/Probe例外/cleanup/未回収PID、SHA不一致、false passで版を停止。環境修正をSolへ投げず、残plannedは未達にする。

## 小標本での実用barとPhase 2/3

選択：V1–V5≥8/10かつ各≥1/2、V6≥2/3、S1≥4/5、Q1≥2/3、Q2/Q3各≥4/5かつ重要欠落の黙った発明0件。
Fは成立/所定初回failとも6/6、最終修復≥4/6かつ各fault≥1/2。少なくともspec/source双方の実修復成功を要求する。
全planned testと回帰が完了し、MVP/legacyが旧barを満たし、全成功成果物gate・時間/quota・版整合・false passなしを満たした場合だけbar_met。
これは列挙した寸法明確な単一Body部品で生成/fallback/限定修復と不足情報を止める経路を確認する小標本bar。母集団成功率の保証ではない。
GUI、対話後の完成、寸法変更後の全履歴追従、製造適性/強度/別kernel/任意複雑形状は実用認定に含めない。有限checksで微小な余計形状をすべて排除した証明でもない。
Phase 2：Codexが全文/gold/fixtures→verify-v1 Probe/used native links→opt-in Q/F/quota/deadline→新eval_verify/集計を最小実装する。
同Phaseで必要なmock契約と手製positive/negative offline smokes、旧unitを確認。全profileの誤形状false pass・所定fault検出も確認する。Solなし。
grokが実装＋凍結予定dataを一度レビュー、Codexが指摘を直し必要分だけ再確認、supervisorが選択ファイルをlocal commit/SHA凍結。pushなし。
Phase 3順：3h時計開始→dev最大4 calls→legacy A/B 4 smokes→新eval-v1固定10→V/Sのclean群→Q→F→独立集計。
clean群はround1/2でV1..V6,S1、round3でV6,S1、round4/5でS1。次にQ1×3→(Q2,Q3)×5 rounds→(F1,F2,F3)×2 rounds、この順をmanifestに先登録する。
Phase 3はsupervisorがホスト実行・snapshot提供、全既定runの成績を公開する。途中調整・追加review round・成功までの再試行をしない。

codex: AGREE (2026-10-12 16:25:17 JST)
grok: AGREE (2026-10-12 16:38:27 JST)
grok note: S1の全体積は合否に使わない。円筒交線の角項も、COUNTERの球octant式もgoldにしない。
grok note: Z=15の外側境界と内側空隙は、Y=0のXZ断面とX=0のYZ断面上の値である。水平全周をその矩形にしない。
