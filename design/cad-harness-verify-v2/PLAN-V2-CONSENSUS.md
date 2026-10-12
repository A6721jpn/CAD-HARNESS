# CAD-HARNESS VERIFY v2 — PLAN-V2-CONSENSUS

R2+R3 draft。3者署名＋supervisor local commit後、本書がv2 Phase 2/3のbinding仕様となりR1案を置換する。[BRIEF](BRIEF.md)、[v1 PLAN](../cad-harness-verify/PLAN-CONSENSUS.md)、[RESULTS](../cad-harness-verify/RESULTS.md)、[FROZEN](../cad-harness-verify/FROZEN.md)を根拠とする。
v1のV5は使用中PCD寸法のProbe false-negative、F1/F2はparseがrepair枠を消費した未起動。旧成績を再採点せず、fresh holdoutでverify-v2だけを測る。本稿は設計文書のみ。
DRAFT2変更：grokのpayload suffix COUNTERを原文どおり採用し、共通の寸法列注記を除外。W3/A1の配置例外・A/Cの不足情報・Kの同一bytesを保持し、gold/barは変更なし。

## R2 crit

- grok：W/S/A/C/K表・固定N・到達graph・共有parse 1＋予約repair 1を採用。式は全件再導出して一致。新testをdev pilotへ使う案と、残6秒だけでrepair機会を扱う案は採らない。
- gemini：active/drivingの使用関係、decoy拒否、初回質問確定後の完成をbar外にする点を採用。単一edge限定・専用repair 2回・call算術（clean23→28、F14→16）の誤り・未根拠の週次%/所要時間予測は採らない。
- codex：native使用経路の証拠、保存v1正例/反例、450＋450秒の予約、回答SHAを採用。Ppre/Ppost各1とcore補助Nは採らず、少ない共有parse枠と別C cohortで統一する。

## Probe・成果物gate

verify-v2専用opt-in/profileで実装し、mvp-v1/verify-v1既定挙動、eval_mvp.py、eval-v1 gold/barは変更しない。Body Tipから使用Profile/Sections/Spine/ReferenceAxis等を辿るnative gateを保持する。
使用Sketchの実際に選択された非construction profile/path幾何をseedとし、使用ReferenceAxisは既存の一意解決規則でseedに加える。全Sketch使用ならその実幾何全部、部分選択なら選択部分だけ。曖昧な参照を推測しない。
同Sketch内のactiveかつdrivingなCoincident/PointOnObject/Tangent/Symmetric/Equal/Distance/DistanceX/DistanceY/Angle/Perpendicular/Parallel/Horizontal/Verticalをtype別に解決する。
constraintのFirst/Second/Thirdの有効な幾何ID≥0同士を辺にし、seedから推移的に到達したconstructionだけを使用と扱う。原点/H/V軸・外部参照の負IDはseed/hubにせず、Radius/Diameterや単項constraintだけで辺を作らない。
到達幾何を対象とするactive/drivingのDistance(X/Y)/Radius/Diameterの再計算済mm値だけを採る。reference/inactive/未接続decoy/custom数値を除外し、feature→Sketch→constraint→geometry経路と値を記録する。
既存の寸法値/半値一致は維持し、新しい別名一致は足さない。使用参照の解決不能・Probe未対応を成功にしない。薄いnative編集gateであり、全履歴の寸法変更追従は認定しない。
幾何±0.01 mm、方向1e-6、体積相対1e-4、verifyのoptimal bbox、単一valid solid/Body/Tip/使用Sketch/主要駆動寸法/正常recomputeを保持。FCStd＋STEPを別freecadcmdで生成器なしに同gold検査し、全bbox/全体積一致・close/所有PID回収/正常exitを要求する。face/edge/feature個数は助言で、要求された面/断面/壁/空隙/加工のgateは省かない。
Sol前に保存済v1 V5 r1/r2の reports/cad-run/host-verify-v1-reviewed-r1-geometry-V5-r{1,2}-mvp1/a1-mvp1/model.FCStd を再読込し、PCD60が使用寸法として取れることをoffline確認する。旧文書/reports/goldは読み取り専用、再採点結果で旧成績を置換しない。
同値の有効寸法を他に置かない未接続construction円、constructionのみの閉路、ray経由の接続、reference/inactive寸法、原点経由のdecoyを最小反例で確認する。W5正例はPCD72を拾い、decoyだけの負例は落ちること。

## ParseとCAD repairの枠・時計

v2のP（JSON/schema/対応範囲/source構文訂正）はepisode全体で≤1、初期生成にもrepair応答にも使えるが両方には使えない。R（実CAD診断修復）は別枠で≤1、CAD attempts≤2（初期＋repair）。初回CADで初期生成枠を閉じ、Rは初期target（source/spec）を維持して追加fallbackしない。
source経路は解釈1＋fallback source1＋P1＋予約R1で最大4 calls。対応内descriptionはspec1＋P1＋予約R1で最大3。A2/A3初回質問は1 call/CAD0、P/Rなし。Cは質問1＋対応内最大3＝最大4。
settled repairable CAD fail＝既存repair_reasonがNoneかつharness_failureなし：next_actor=sol、build/probe失敗、Probe例外なし、closed/exited、cad_exitは整数、build失敗は測定またはpredicate_diffあり。K成立は更にscript完了・exit0・native正常・所定predicate_failを要求する。
settled fail後、guard許可なら必ずRを実際に1回呼ぶ。注入されたものを含む実失敗source/specと実測feedbackを渡す。parseがR枠を使う、正解source差込み、fault再注入、counter/deadline reset、2回目のCAD repairは禁止。
eligible数/実R数/成功数/repair_not_attempted_reasonを保存。quota/SHA/時間等のguard停止以外でeligibleなのにRが起動しない場合はharness障害として版を停止する。
1 episodeは900秒固定。初期工程（Cの質問/回答後生成も含む）≤450秒で打切り、修復工程へ450秒を予約する。成功時reimportも各工程内。初期timeoutでsettled failに達しなければnot_reached/timeoutを記録する。
修復工程の上限内訳はR Sol180秒＋未使用P60秒＋再build/export90秒＋独立reimport90秒＋cleanup30秒＝450秒。初期工程もcleanup30秒を先に確保し、各子processを工程残/900秒残/共有残へclip、FreeCADは常に≤300秒。
dev/legacy/MVP/core/C/保存/cleanup/集計すべてに単一monotonic 10800秒を適用。各episode開始には900秒＋集計60秒の共有残と当該最大call枠を確保する。Cの回答時に時計を再開しない。
v2専用Budget/manifest/Guard上限で実装する。共有MAX_ATTEMPTSやMVP既定の3 calls/3 CAD/900秒、needs_clarification retry、v1 Guard125を一括変更しない。

## Clarify→凍結回答→完成（bar外）

A2/A3各5の初回rubricは必要field IDのみのneeds_clarificationで1点、発明/別field/unsupported/invalidは0点。A1は初回の配置default・不要質問なし＋最終全gate。後続で初回失敗を救済しない。
C2/C3各3はAと異なる新入力の独立cohort。初回1 callのartifactとrubric点を保存・確定してから、正しい質問にだけ凍結answerを返す。誤質問/発明は完成miss・not_reachedとして予定分母3に残し、answerを渡さない。
session resumeは新設しない。完成callのuser payloadはdescription.txtのUTF-8 bytes＋LF1個＋answer.txtのbytes（双方BOM/末尾LFなし）だけ。初回質問は別artifactに保存し、field-IDヒント/期待gold/fixtureをpayloadへ加えない。
完成gold.descriptionはその連結payloadと完全一致させ、元description/answer/連結payloadのSHAをgold・manifest・reportへbindする。これは凍結回答を条件にした完成測定で、会話履歴を保つ一般対話の認定ではない。
同一900秒/初期450秒/共有P1/R1/CAD2で対応内生成→全幾何/native/独立reimport gateを測る。追加質問は完成fail。初回/回答後初回/最終gate、時間、call purpose、usage、未起動理由を分離する。
C各partの完成pass/予定3とWilson95%、正質問に限る条件付き完成率（分母0ならN/A）を別表にする。C得点/分母/CIはbar_metへ入れず、共通の版・guard・harness停止規則は適用する。

## Fresh holdout・解析gold（mm、体積mm³）

W1–W5/K1/K2はdescription→unsupported→source必須でschema拡張なし。W6/S2/A1/C完成/K3は対応内。下表の説明列の直後に「単位mm。他の加工なし。」だけを足したものを本文とする。W3とA1以外は、その前に「XY中心、下面Z=0。」を置く。「寸法列はX×Y（3つ目はZ）。」はpayloadに入れない。Kは対応Wの完成description bytesと同一で、注入指定を本文へ入れない。

| ID / N / v1 class | 説明本文（回答・rubricは入れない） | 解析gold / 凍結する別answer |
| --- | --- | --- |
| W1 / 2 / V1 | Z軸の中空ローラー。外径40、長さ48、貫通穴直径10。外周のZ=20..28に幅8、半径深さ3の全周溝。 | V=17112π、溝外径34、Z=10/24/38の環状断面・肩・両端開口/内腔。 |
| W2 / 2 / V2 | 中実の四角テーパー。Z=0は50×30、Z=40は30×18。中心一致、ねじれなし、寸法は高さに対して線形に比例縮小。 | V=39200、Z=20は40×24、端/中間断面・方向・斜面。 |
| W3 / 2 / V3 | XY平面で90度曲がる管。中心線R32、外径16、内径10。(0,0,0)から+X向きに出て(32,32,0)へ+Y向きで到着。両端開口、一定断面。 | V=624π²、bbox=[0,40,-8,32,-8,8]、始/45°/終の法線環状断面・内腔。 |
| W4 / 2 / V4 | 上面開口の箱。外形X=-36..36,Y=-24..24,Z=0..24、壁と底4。Y=-2..2の三角リブ、XZ頂点(-32,4),(32,4),(32,16)。 | V=33280、内腔64×40・壁/底4、rib厚4/三角断面/接続。 |
| W5 / 2 / V5 | 円形フランジ外径96、厚さ10、中央通し穴D24。PCD72にD6通し穴6個、+Xから60度刻み。上面の長手Xの10×3・深さ2の溝を中心(-18,-20),(18,-20)に。 | V=21060π−120、6穴中心(36cos(kπ/3),36sin(kπ/3)),k=0..5、溝床Z8、駆動PCD72。 |
| W6 / 3 / V6 | 96×64×14の板。上面に22×14深さ4のポケットを中心(-22,0),(22,0)に。D5通し穴をX=-30,0,30とY=-22,22の6点に。上面外周だけ脚1の面取り。 | V=83552−525π−(160−4/3)、床Z10・穴/鋭い内縁・外周C1。 |
| S2 / 5 / S1 | 70×50×18のブロック。上面中央に22×16深さ5のポケット。上面外周4辺だけR2.5、垂直辺は鋭く残す。 | stock scope=[-35,35]×[-25,25]×[0,13]のV=45500、全体積は記録/成果物一致のみ。局所R2.5は下記。 |
| A1 / 3 / Q1 | 90×50×12の板。中央にD10の通し穴。 | 初回XY中心/底Z0、V=54000−300π、不要質問なし＋全gate。 |
| A2 / 5 / Q2 | 70×36の板。四隅D5通し穴、穴中心は外形からX8 Y7。 | rubric: plate_thicknessのみ。幾何gold/answerなし。 |
| A3 / 5 / Q3 | 64×40×12の板。D8通し穴2個。 | rubric: hole_positionsのみ。幾何gold/answerなし。 |
| C2 / 3 / Q2完成 | 76×44の板。四隅D6通し穴、穴中心は外形からX9 Y8。 | 初回plate_thickness；answer「厚さは11。」、V=36784−396π、中心(±29,±14)。 |
| C3 / 3 / Q3完成 | 72×46×9の板。D7通し穴2個。 | 初回hole_positions；answer「穴中心は(18,0)と(-18,0)。」、V=29808−220.5π。 |
| K1 / 2 / F1 | W1と同一bytes。 | contract-valid source後に溝なしsourceを一度注入。完成gold=W1、誤候補V=18000π、所定roller fail。 |
| K2 / 2 / F2 | W5と同一bytes。 | contract-valid source後にPCDの(36,0)穴を欠くsourceを一度注入。完成gold=W5、誤候補V=21150π−120、所定holes fail。 |
| K3 / 2 / F3 | W6と同一bytes。 | schema-valid spec後に(-30,-22)穴だけD5→D8を一度注入。完成gold=W6、誤候補V=83552−661.5π−(160−4/3)、所定holes fail。 |

W1：π(20²−5²)48−π(20²−17²)8=(18000−888)π。W2：t=z/40、40∫₀¹(50−20t)(30−12t)dt=40(1500−600+80)=39200。
W3：断面π(8²−5²)×中心線長32π/2=624π²。P=((32+u)sinθ,32−(32+u)cosθ,v)、θ∈[0,π/2],25≤u²+v²≤64よりbbox=[0,40,-8,32,-8,8]。
W4：72×48×24−64×40×20＋64×12×4/2=82944−51200+1536=33280。ribは内腔内で底/壁と境界接続のみ、体積の二重加算なし。
W5：π(48²−12²−6×3²)10−2×10×3×2=21060π−120。溝最近半径√(13²+18.5²)>12、最遠√(23²+21.5²)<48、下側PCD穴とのY間隔18√3−21.5>3なので全切削は互いに非交差。
W6：96×64×14−2×22×14×4=83552、穴除去6π(2.5²)14=525π。chamferはa=1−s、∫₀¹[2(96+64)a−4a²]ds=160−4/3。穴/ポケットは外周加工帯と非交差。
S2：床Z=18−5=13、fillet帯Z=15.5..18なのでscope体積70×50×13=45500は不変。Y0のXZ局所円中心(±32.5,15.5)、X0のYZは(±22.5,15.5)、R2.5。その2局所断面でZ16.75の外境界は±(32.5+1.25√3)/±(22.5+1.25√3)、内腔は各|x|<11/|y|<8。隅patch全体積はgoldにしない。
A1：90×50×12−π5²×12=54000−300π。C2：76×44×11−4π3²×11=36784−396π、中心±(38−9)/±(22−8)。C3：72×46×9−2π3.5²×9=29808−220.5π。
bboxを(X半幅,Y半幅,Z0..H)で記すとW1=(20,20,48)、W2=(25,15,40)、W4=(36,24,24)、W5=(48,48,10)、W6=(48,32,14)、S2=(35,25,18)、A1=(45,25,12)、C2=(38,22,11)、C3=(36,23,9)。外形の残存端/下面から得られ、内部切削・上辺加工はこれを縮めない。
K1差分=+888π、K2差分=+π3²×10=+90π、K3差分=−π(4²−2.5²)14=−136.5π。完成goldは清浄Wのまま。全表式はdescriptionだけから再導出済み、FreeCAD測定へ合わせた値ではない。

## Bar不変・順序・call枠

W1–W5→V1–V5は≥8/10かつ各≥1/2＋所定fallback、W6→V6≥2/3、S2→S1≥4/5、A1→Q1≥2/3、A2/A3→Q2/Q3各≥4/5かつ重要欠落の発明0。Nを成功後に追加せず、分数を変更しない。
K1/K2/K3→F1/F2/F3は成立/所定検出6/6、最終全gate≥4/6かつ各≥1/2、source/spec双方の実R成功。生成失敗/not_reachedも予定6が分母、pass/成立と自然repair success/eligibleは別記する。Faultのreached/injectedは実置換が返った時だけtrue、target_missingはnot_reached理由を残す。
新prefixのfresh eval-v1 P1–P5各2は≥8/10＋各≥1/2、P1例外帯/gold不変。legacy A/B good/broken 4 offlineは4/4、追加legacy Solなし。core＋回帰51件の完了・全成功gate・版/時間/quota/false-pass条件だけでbar_metを決め、C/devの成績は混ぜない。
v1 V/S/Q/Fのtest一式・失敗source/保存FCStdはv2 dev資料に降格し採点外。旧凍結ファイルを移動/改変せずv2/devのコピーまたはSHA付き参照にする。MVP/legacyだけは固定回帰の例外。
順序：共有3h開始→v1 dev-live 3（V1/V6/Q2、計≤4 calls、率外）→legacy4→fresh eval-v1 P1,P1,P2,P2,P4,P4,P5,P5,P3,P3→clean W/S→A→C→K→独立aggregate。
cleanはr1/r2各W1..W6,S2、r3はW6,S2、r4/r5はS2。A1×3→(A2,A3)×5 rounds→(C2,C3)×3 rounds（各episode質問から完成まで）→(K1,K2,K3)×2 roundsをmanifestへ先登録する。
devは新testを使わずV1は解釈＋source≤2、V6はspec1、Q2は初回質問1、合計≤4のpreviewのみでP/R/CAD0。previewをCAD成功扱いしない。全60 episodes＝dev3＋legacy4＋MVP10＋clean18＋A13＋C6＋K6。
基準計画83 calls＝dev枠4＋MVP10＋W1–W5 20＋W6 3＋S2 5＋A1 3＋A2/A3 10＋C12＋K1/K2 12＋K3 4。parseなし、clean repairなし、Kだけ実Rを含む予約計算で、実績ではない。
最大163＝source14×4＋対応内13×3＋ask10×1＋C6×4＋MVP10×3＋dev4。source14=W1–W5/K1/K2、対応内13=W6/S2/A1/K3。v2 Guardだけ163を上限とし、slot/phase/episode capsも同時に守る。
run/aggregateのexpected IDs/N/class対応は凍結manifest由来、bar coreとC/devを別検証。初回/最終gate・route・P/R purpose/stage・CAD attempts・fault到達/成立/検出SHA・停止理由を保存する。
完了cohort/partだけ95%両側Wilson(z=1.96)、失敗込みwall median/p95/max、provider input/cached/cache-write/output/reasoningの各欄合計（欠測null維持）とfailure-class分布を報告。異種cohortをpoolして一般成功率にしない。

## 実装・freeze・停止

Phase 2はSolなし：v1資料/offline devで最小Probe/Budget/C計測を実装。mockはconstruction到達/decoy、parse消費後の実R保証/時計/guard、C初回固定・未到達分母・SHA契約に必要なものだけ。TEMPはtools/test_support.pyと同様にredirectする。
人手の新description/answer/rubric、生成器と独立の解析gold（表示式と数値）、全geometryの手製native正負、fault候補/対象、run-order/SHAを作り、全新offline native＋保存V5＋decoy＋4 legacy smokesと全unitを確認する。
grok＋geminiは実装/データを各1回review、必要な指摘修正・再確認後supervisorが選択ファイルをlocal commit（pushなし）してfreezeする。testを使うlive pilotをせず、devも含む全Solより前に凍結/commitを完了する。
code/skill/build schema/Probe/CLI/model設定/継承AGENTS/全dataをSHA化し、version・commit・manifest digestを記録する。旧SHAを上書きせず別版に保存。生成/初回contextへgoldなし、compilerのcase名/description-SHA lookup禁止。
FreeCADは C:\dev\CAD\.tools\freecad\FreeCAD_1.1.4-Windows-x86_64-py311\bin\freecadcmd.exe headlessのみ。Solは既存driver/gpt-6.1-sol/xhigh/tools無効/read-only。Phase 3はsupervisor host実行・snapshot提供、新prefix/aggregate、全予定IDを保存しno overwrite。
各real call前にsupervisor snapshotを検査：missing/invalid/未来時刻/age>300秒はstop。使用≥55%で新callを止め継続判断、≥60% hard stop。実%と日時/SHAを記録し、token→週次%や実行時間の根拠なし予測を行わない。
quota/共有3h/900秒/予約call不足は開始/新callを止め、未完了coreはbar未達・CIなし。cleanupを予約しdeadline後の成功は数えない。N・期限・上限の自動延長、途中調整、warm-start、手修正、成績を見た追加runは禁止。
gold不一致はdescriptionから先に再導出しexpected/actual/式を記録する。解析gold誤りならSTOP報告・自分で変更しない。goldを確認できたfixture/Probe実装欠陥はSol前のみ修正/記録して全offline batchを最初から再開し、tolerance/gateを落とさない。
最初のlaunch/save/export/reimport/Probe例外/cleanup/未回収PID・SHA不一致・誤形状false-pass・確認されたharness障害で版を停止する。モデルの構文/意味/修復失敗は成績として残し、環境/Probe障害をモデルへ修復させない。
freeze後のどのfixも旧失敗を保存し新version＋新未使用holdoutで別計画にする。途中でgold/bar/既存集計を書換えない。3者署名不一致のgold/bar/cost事項はCONSULT-FRAMEWORKどおりsupervisor判断へ戻す。
リスクはgraphの誤接続/取りこぼし、厳しい時間予約によるsource timeout、共有Pを先に使った後のrepair構文失敗、小Nの広いCI。83/163は枠の算術で時間/quota保証ではなく、この限定部品・1回修復と凍結回答の認定に留める。

gemini notes（counter修正前レビュー、2026-10-13 00:12:00 JST）：W1–W6/S2/A/C/Kの全解析gold体積式・bbox・故障差分を独立再導出して一致確認。core実用barの全条件・分数が不変であることを確認。 非construction幾何をseedとするSketch内active拘束の推移到達によるPCD等寸法取得と、負ID排除・未接続decoy拒否のProbe設計に合意。 P≤1＋R≤1の枠分離と450秒repair予約、C2/C3完成cohortをbar_met外の独立指標として分離する運用方針に合意。

codex: AGREE (2026-10-13 00:16:19 JST)
grok: AGREE (2026-10-13 00:21:58 JST)
grok note: payload suffixはCOUNTERどおり。gold/barは不変。
gemini: AGREE (2026-10-13 00:22:15 JST)
gemini note: payload末尾の共通寸法列注記除外（grok COUNTER採用）を確認。v1文面規則との整合、W3/A1配置例外、解析gold不変に合意。
