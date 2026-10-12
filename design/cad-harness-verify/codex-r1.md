# CAD-HARNESS VERIFY R1 — Codex independent proposal

2026-10-12。MVPは完了済み。これは検証計画の提案であり、下記の成功率・時間・予算は未実測。
基準はBRIEF、MVP STATUS、DECISION-01/02/03、現行driver/compiler/evaluator/skill。
CLI＝検査・実行・採点、skill＝解釈・建模判断、prompt＝今回のユーザー入力のみを維持する。
FreeCAD 1.1.4の指定freecadcmdのみ、headless。Solは既存driverのgpt-6.1-sol/xhigh、GUI/Fusion/SolidWorksなし。

## (a)(d) 新しい自然文suite：6部品、各N=5

下記は凍結候補の説明文。mm、中心XY/下面Z=0は既定値。ただし明示座標・曲管はその指定を優先する。
V1–V5は現build schemaでは表せない形状。schemaを拡張してfallback試験をcompiler試験へ変えない。
description入口からunsupported→build(doc)を確認し、agent入口への手動変更・要求の近似省略は失敗とする。

| ID / 型 | ユーザー説明文案 | goldの独立チェック |
| --- | --- | --- |
| V1 回転部品・全周溝 | 「Z軸の中空ローラー。外径32、長さ36、下端Z=0。中央に直径8の貫通穴。外周のZ=14..18に幅4、半径方向深さ2の全周溝。単位mm。他の加工なし。」 | 外径32/内径8、溝部外径28・Z範囲、肩面、穴の両端開口と軸上空隙。Z=9,16,30の環状断面、bbox、V=8400π。 |
| V2 loft | 「中実の四角テーパー。Z=0は40×24、Z=30は24×16の長方形。XY中心をそろえ、ねじれなしで寸法が高さに比例して縮む。単位mm。穴や丸みなし。」 | Z=0,15,30の断面40×24/32×20/24×16、中心・方向、4斜面・端面、bbox、寸法の積を高さで積分したV=19520。 |
| V3 sweep | 「XY平面で90度曲がる管。中心線半径25、外径12、内径8。中心線は(0,0,0)から+X向きに出て(25,25,0)へ+Y向きで到着。単位mm。両端開口、一定断面。」 | 中心線R25/90°、端面方向、始点・45°点・終点の法線断面D12/D8、連続した内腔の空隙、bbox、V=250π²。 |
| V4 shell＋三角rib | 「上面開口の箱。外形X=-30..30,Y=-20..20,Z=0..20、壁と底3。内側にY=-1.5..1.5の三角リブ。XZ断面の頂点は(-27,3),(27,3),(27,15)。単位mm。穴なし。」 | 壁/底3、開口・内腔54×34、リブ厚3・三角断面・端位置・一体接続、bbox、V=48000−54×34×17+54×12×3/2=17760。斜面により矩形stackでは代替不能。 |
| V5 複数pattern | 「円形フランジ外径84、厚さ8、中央に直径20の通し穴。PCD60に直径5の通し穴8個、+Xから45度刻み。上面に長手Xの12×4、深さ2の溝3本、中心(-16,-15),(0,-15),(16,-15)。単位mm。」 | 円筒外形/中央穴、8穴の径・中心・角間隔・開口、3矩形溝の位置/深さ/床、bbox、V=12912π−288。Patternクラスやfeature個数は固定しない。 |
| V6 多加工の対応内plate | 「110×76×12の板、XY中心、下面Z=0。上面から26×18、深さ5のポケットを中心(-26,0),(26,0)に2つ。直径4の通し穴をX=-36,0,36、Y=-27,27の6点に。上面外周だけ脚0.8の面取り。単位mm。」 | 2ポケットの位置/深さ/鋭い内縁、6穴の開口/空隙、指定外周C0.8、bbox、V=95640−288π−(186×0.8²−4×0.8³/3)。compiler経路を記録。 |

全件：valid solid=1、要求外加工なし、薄いnative編集gate、FCStd＋STEPを生成コードなしの別processで採点。
寸法±0.01 mm、方向成分1e-6、体積相対1e-4、正常close/exit。断面・壁厚・空隙等の欠測はfail。
新goldはverify-v1として人手で式・座標・幾何役割をレビューする。生成LLMや観測体積から期待値を作らない。
同じFreeCADでの独立測定であり、他カーネル・微小な余計形状の完全排除の証明ではない。

## (h) dev/test分離と凍結

Devは同6型を別寸法で各1件、計6件。例：D1外径28/長30/内径6/溝幅3深1.5、D2は50×30→28×18/H24、
D3はR32/D14/D10/60°、D4は70×48×24/壁4/別三角rib、D5はD90/H10/PCD68/D6、D6は120×80×14/別穴配置。
Dev全文・goldも完成させ、testのV1–V6、曖昧さrubric、固定回答、注入candidate、run順を先にsupervisorがlocal commit/SHA凍結する。
全setの凍結前はSol禁止。手製の参照fixtureと式の不一致は先に調査し、測定値へgoldを合わせない。
Devのみ1 episode/型・最大3 callsで調整可。Test開始前にcode/skill/schema/Probe/モデル/CLI/継承規約のSHAを固定する。
Testのgoldはgenerator・初回Solに渡さず、部品ID/description SHAで解答を選ばない。修復expectedだけはgold由来でよい。
Test開始後は調整禁止。修正するなら旧失敗を保存し、変更版と新しい未使用testセットを別評価にする。

## (b) 修復を必ず試す、自然な失敗と分ける

V1/V3/V4/V5は最初から未経験の難しい入力とし、自然発生の初回失敗→最終成功を別集計する。難しさだけで修復発生を保証しない。
自然修復率=修復可能な初回CAD失敗後の最終pass/該当run数、分母0はN/A。parse修復は別に数える。
注入は3種類×5 fresh episodes＝15件、初回候補を一度だけ凍結済みの誤候補に差し替えるCLI試験hookを用意する。
F1：V1の溝欠落、F2：V5の周辺穴1個欠落、F3：V6の穴1個をD6へ変更。すべて有効native solidの幾何不一致にする。
F1/F2はagent modeで初回source call後に誤sourceを注入、F3はdescription modeで初回spec call後に誤specを注入する。
原出力と注入物のSHA・fault IDを保存。実際のSol生成callも使用量へ数える。注入でcall数・時間をリセットしない。
実Probeのexpected/actual→通常repair経路→実Sol→CAD→export/reimportまで測る。正解sourceをrepairへ差し込まない。
上限は同じ3 calls/3 CAD/900秒。検出率=初回所定fail/15、注入修復成功率=最終全gate pass/15。
注入未成立・環境障害も固定15件から落とさず、成立件数と条件付き成功率も併記。自然文成功率へ混ぜない。
既存mockで環境/保存/Probe例外/cleanupのhuman停止も確認する。これらをSol修復の成功として扱わない。

## (c) 曖昧さ：4説明×N=5、CADなしの20 episodes

Q1「60×40×8の板、中央に貫通穴。単位mm。」→不足は穴径。固定回答「直径6です」。
Q2「80×50×10の板に直径4の通し穴4個。単位mm。」→不足は穴位置。固定回答「中心はXY=(±25,±15)、軸Zです」。
Q3「32×22×6の板、中央に直径4の通し穴。単位mm。」→origin未指定はXY中心/底Z=0でpreview、質問しない。
Q4 “Make a 48 by 32 by 6 plate, two D4 through holes at X=-12,+12 and Y=0. No other cuts.” →mm/既定原点でpreview、質問しない。
VERIFY専用契約でclarificationにfield ID（hole_diameter / hole_positions）を付け、CLIが必須不足fieldと照合する。
Q1/Q2は必要fieldの質問＋clarification_required、CAD=0、寸法/位置を推測しない。その後、固定ユーザー回答だけで再解釈する。
Q3/Q4は最初のpreviewで寸法・単位・既定座標をCLI比較。Q1/Q2も回答後previewを同様に比較し、JSON全文一致は求めない。
1点=期待した質問/既定値対応とpreview値をすべて満たす。不要質問、黙った仮定、unsupported逃避、call_limitは0点。
現driverのneeds_clarificationはinvalidとして再試行するため、この実験にはopt-inの待機結果が必要。MVPの挙動を黙って変更しない。
回答は新しいユーザー入力なのでSHAを別記録、修復のpayloadはその時点の同じ入力。episode全体の3 calls/900秒を共有し、CAD採点率へは混ぜない。

## (e)(f)(g) protocol、統計、回帰、記録

自然文testは6件を1回ずつ×5 rounds＝30 runs、順を事前登録。全件fresh・逐次、warm-up除外・成功まで追加・手修正なし。
各partの初回/最終pass率と95%両側Wilson区間（z=1.959964）を固定Nで計算。5/5でも区間は約56.6–100%、4/5は37.6–96.4%。
suite合計は参考集計とし、異なるpartの反復を未知の形状からの独立標本とは扱わない。CI幅は隠さず、追加Nを結果次第で選ばない。
eval-v1は別集計でP1–P5×2を再実行、gold/8-of-10＋各1-of-2/P1例外帯を不変にする。既存10/10を新版の回帰試験へ流用しない。
legacy A/Bは既存good＋brokenの4 headless smokes、A prompt SHA/旧判定のunit回帰。追加legacy Sol試行は不要。
記録：initial/final geometry/editability/reimport/pass、経路、unsupported、call種別、CAD attempts、repair回数、repair成功分母。
wallは失敗込み全件の中央値/p95/最大、callsとusageは全call。provider input/cached/cache-write/output/reasoningを個別集計し、欠測はnull。
失敗分布は解釈・建模・幾何・native編集・再読込・環境・timeout/budgetに固定分類。曖昧さscoreと注入成績は別表にする。
全planned ID・SHA・未完了件を残す。新reports/aggregatesだけ、上書き禁止。missing predicate/measurementをpassにしない。

## 予算と(i)停止規則

LLM対象はdev6＋新自然文30＋MVP回帰10＋注入15＋曖昧さ20＝81 episodes。
余分な修復なしの計画値は11＋55＋10＋30＋30＝136 calls、全episode最大3なら243 calls。失敗で増減するため予測と実績を分ける。
MVP集計の観測平均は1 call当たりinput=34910.5、output=657.4。長いagent sourceにはそのoutput平均を外挿しない。
仮の予約量をinput 50k/output 5k per callと置くと136–243 callsでinput 6.80–12.15M、output 0.680–1.215M。
これは予約用仮定で上限保証・料金・週次使用率への換算ではない。reasoning/cacheは実際のprovider欄を別記録する。
BRIEF時点の使用約6%から60%まで約54 percentage points。tokenから残call数は断定できず、dev実績で時間・使用増分を再見積もりする。
現CLIは週次quotaを取得しない。VERIFY pre-call guardへsupervisor確認済み使用率snapshotを渡し、鮮度未確認なら止める。
逐次実行、開始前と各call前にホスト使用率確認。55%で予備停止、60%以上で新規call禁止。取得不能/次blockの見積超過でも開始しない。
試験セッションは2–3時間を予約、3時間で新runを止める提案。複雑形状の所要時間は未測定、900秒×全件ならこの枠を超えるため完走保証はしない。
quota/時間停止は未完了・実用判定未達、fail差替え不可。待機後の継続は同じ版/SHAと全planned IDを保持し、sessionを分けて記録する。
起動/保存/再読込/Probe例外/未回収PID、gold/SHA変更、誤形状のfalse passを検出したらその時点で全suite停止、Solへ環境修正をさせない。

## (i) 検証後の「実用」と実装順

提案bar：自然文全30件完了、各part≥4/5（全体≥24/30）、V1–V5のfallback経路成立。CIは報告し、母集団80%保証とは言わない。
注入15/15で所定fail検出、修復≥12/15かつ各fault≥4/5。曖昧さ≥18/20かつ各説明≥4/5、重要不足の黙った推測は0件。
加えてMVP/legacy回帰合格、全成功成果物に薄い編集gate＋独立再読込、予算内完了、false passなしを要求する。
達成時の表現は「列挙した単一Bodyの部品で、確認を挟んで編集可能な初稿を作れる」。GUI、寸法変更後の全履歴追従、製造適性・強度・任意複雑部品の保証は含めない。
1. 人手gold・質問rubric・固定回答・fault・dev/test manifestを先に凍結し、supervisorがlocal commit。Claude unavailableなのでgrok＋codex合意。
2. verify-v1 gold/Probeを追加：溝・loft断面・曲管・rib・pattern、used-profile編集検査を拡張。現allowlistにないLoft/Pipe/Groove等はVERIFY側だけで扱う。
3. driverのopt-in clarification/注入hook/shared budget/quota guardと、新eval_verify CLIを実装。既存eval_mvpの5件固定/判定は保持し、必要な契約だけmock試験。
4. 手製fixtureのoffline採点→dev6→修正確定・版凍結→legacy4とMVP10回帰。既存コード/skillへtest専用寸法や解答を入れない。
5. 凍結版の自然文30・注入15・曖昧さ20を予定順に実行し、実測・Wilson・限界を集計。未達なら未達のまま報告する。

このR1では提案ファイルのみ作成。コード編集、FreeCAD/Sol実行、commitは行わない。
R1 DONE
