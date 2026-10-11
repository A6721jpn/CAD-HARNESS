# CONSENSUS案: cad_run 複雑課題B（2026-10-11）

codex署名済み、grok署名待ち。grok-r2.mdとcodex-r2.mdを読んだ上で、ユーザー20:00の「Aより本当に難しく、例：穴パターン＋面取り＋ポケット」を優先する。新課題は1件、単一Bodyに中央ポケット・貫通穴パターン・外周Chamferを組み合わせる。穴数は3個に抑え、マルチボディ、課題C、新レシピは追加しない。

AのB2 N=5成功（reports/aggregate-A-box-pocket-fillet-driver.json、4593d43）はAでの実績であり、Bの動作・速度の保証ではない。BのLinearPatternとChamferの生成、Probe抽出、許容の適合は未確認。導出期待値を実測として扱わず、good fixtureスモークを受入ゲートにする。Claudeは組織設定で不参加。今回の議論ではCAD・Solを実行しない。

## 1. 課題の最終仕様

識別子は **B-plate-pocket-hole-pattern-chamfer**。単位mm、新規文書、原点・回転なしのPartDesign::Bodyが1個、最終valid solidが1個。寸法は以下の新課題仕様であり、実測ではない。

| 順 | PartDesignフィーチャ | 仕様 |
|---|---|---|
| 1 | 矩形Sketch → Pad | XYの中心矩形80×60。+Zへ片方向10。範囲X=-40..40、Y=-30..30、Z=0..10 |
| 2 | 上面矩形Sketch → 中央Pocket | Z=10の中央30×20、深さ4の非貫通。開口X=-15..15、Y=-10..10、底Z=6、垂直壁。Through allではない |
| 3 | 上面円Sketch → 穴Pocket | 円中心(-20,-20,10)、半径3。下向き長さ10で貫通し、Z=0/10で開く |
| 4 | LinearPattern | 元は穴Pocketだけ。Bodyの+Xに元を含め3個。中心XY=(-20,-20),(0,-20),(20,-20)、間隔20、最初から最後の距離40 |
| 5 | Chamfer | 上面外周4直線辺だけ、等脚1、45°。中央Pocketの縁、穴の縁、縦稜、下面には付けない。最終TipはChamfer |

Pad/Pocketは非対称・非Reversed。標準Origin族を除く型と個数はBody 1、Sketch 3、Pad 1、Pocket 2、LinearPattern 1、Chamfer 1、Fillet 0。追加Part::Feature、PartDesign::Hole、座ぐり、ねじは使わない。フィーチャの所属・リンク・順を確認し、名前やEdge/Face番号は固定しない。

穴は中央Pocketと交差せず、外周面取りとも交差しない。80×60の板と中央Pocketはcodex R1の仕様、穴3個と間隔20・Chamfer各脚1はgrok案を用い、穴列をY=-20へ離す。Pad→中央Pocket→穴Pocket→Pattern→Chamferの依存を一つの課題で評価する。

FreeCAD 1.1.4でのLinearPattern.Lengthの総長/間隔の意味は未確認。仕様上の総距離40と中心配置は固定するが、属性設定方法はgood fixtureで確認する。合否は個数・中心・方向・半径で取り、Lengthの生値を推測で固定しない。

## 2. Probe述語と期待値

信頼する課題別Probeが、同じFreeCADプロセスでBody・最終Shape・Sketch・各フィーチャ属性を読む。入力スクリプトの自己判定や自己申告値は使わない。幾何と履歴の両方が一致することを要求する。

| 述語 | 期待・検査 |
|---|---|
| solid_valid | 単一Body、単一valid solid |
| bbox | X=-40..40、Y=-30..30、Z=0..10、寸法80×60×10 |
| central_pocket | 上面中央30×20、底Z=6、深さ4、垂直壁4方向、非貫通。矩形Sketch・Pocketの属性と最終形状を確認 |
| holes_pattern | 半径3の貫通穴3個、上記3中心、軸はZ、Z=0..10、上下で開口、盲穴の底なし。分割円筒面・円弧は同軸同半径でまとめる |
| feature_counts / feature_chain | §1の型・個数・順・所属、両PocketのProfile、Patternの元が穴Pocketのみ、個数3・+X、最終TipがChamfer |
| outer_chamfer | 上面外周だけに等脚1の4方向の面取り平面帯。内部のPocket/穴の縁は鋭いまま。上面外側境界78×58、面取り帯Z=9..10、法線Z成分の絶対値√2/2は導出・未実測。分割面は同一平面でまとめる |
| volume | **導出・未実測：45600−270π−416/3 mm³** |
| raw面数・表面積 | 実読取を記録するだけ。今回の合否条件・期待数値にはしない |

Bの線形寸法・座標・bbox比較は絶対差1e-6 mm、軸/法線の成分比較は1e-6、体積はabs(Vobs−Vexpected)/abs(Vexpected)≤1e-6を初期許容とする。grok R2の厳しい許容に合わせ、codex R2のbbox±0.1 mm・仮の絶対体積差1 mm³はBへ採らない。これらはBで未較正の設計値で、good fixtureスモークで抽出と残差を確認して確定する。Aの許容は変えない。

期待体積の導出（すべて **導出・未実測**）：

- 板80×60×10=48000 mm³。中央Pocketは30×20×4=2400 mm³。
- 穴3個は3π×3²×10=270π mm³。中央Pocket・面取りと重ならない。
- 外周面取りの除去量は、上端1 mmの断面で内側への移動量t=0..1を使い、∫₀¹[80×60−(80−2t)(60−2t)]dt=140−4/3=416/3 mm³。
- 完成体積は48000−2400−270π−416/3=45600−270π−416/3 mm³。板のY寸法が60なので、80×40案の356/3は流用しない。

expectedには式・単位・導出の出典、measurementsには実読取だけを保存する。未取得はnull。goodで残差が許容を超えたら、生成・脚の解釈・導出・抽出を調べる。観測に合わせた帯の拡大や理論式の自動上書きは行わない。

## 3. Probe/specと課題選択

新規 **tools/cad_run_probes.py** 一つにA/Bのspec・形状プロンプト・Probeを固定登録する。登録表の参照は標準Pythonだけで可能とし、CAD importはProbe実行時に限る。任意プラグイン探索、任意--spec、入力スクリプトによるProbe選択は設けない。

- cad_runとcad_agentの両方に--task。選択肢はA-box-pocket-filletと本B、既定はA。未知taskはexit 2で、出力作成・Sol/CAD起動より前に拒否する。旧B草案の識別子は別課題として登録しない。
- cad_agentは選択taskの形状仕様＋共通build契約を送る。Aの初回PROMPTは現行のバイト列を保持する。Bは§1の仕様、DPC-019/FreeCAD 1.1.4、許可モジュールFreeCAD/Part/Sketcher/math、build(doc)が渡された文書に作成してBodyを返すこと、文書・Probe・保存・close・CAD実行はハーネス担当、と伝える。API例、fixture、evidence、他runの解答、理論体積のヒントは渡さない。
- report.task_id、cad_runのpreflight引数・実行argv、結果JSONのtask照合をすべて選択taskにそろえる。request/worker-resultにもtask_idを載せ、親はtask・attempt・ハッシュ・所有PIDを照合する。旧request/workerのtask欠落を互換で扱う場合はAだけに限定し、Bでは受け入れない。
- worker.probe / numeric_predicates / inner_predicate等の旧Aの入口、executeの既定呼出しを維持する。新しいタイマーの段名をfailed_phaseへ追加せず、従来の失敗段・担当を保つ。

## 4. CAD内部時間とworker時刻

workerの単調時計で **timings_ms** を作り、次の4キーだけを持つ。

| キー | 測る区間 |
|---|---|
| build | 現行builder(doc)呼出し全体。ハッシュ検査、ソース読込・トップレベル実行、build(doc)、入力内recomputeを含む |
| recompute | buildが返った後のworkerの最終doc.recomputeだけ |
| probe | 計測と述語評価 |
| save | saveAsと保存ファイル確認 |

区間は重ねず、例外時もfinallyで経過を記録し、未到達はnull。入力内recomputeを別に推定・差引しない。文書作成・close・launch・cleanupは含めない。worker-resultから親resultへ値をコピーし、4段の和を総時間と呼ばず、driverのwall_msやcad_run_wall_msへ加算しない。driverから読める最終out-dirのresult.jsonを内部時間の出典とする。

workerのready/event各行には生成時UTC **ts** を付ける。公開eventsのトップレベル15キーとts=親の記録時刻・event_seqを維持し、workerのkind=eventを転記した行は **data.worker_ts** に元tsをコピーする。親が作るpreflight/launch/cleanup/stderr/j1/run_finishedはnull。readyの元tsはworker-events.jsonlに保持し、親のlaunch_finishedの時刻と混同しない。DATA_KEYSにworker_tsを許可する。

イベント名は増やさず、stderr記録のbuild_finished改名は別件のまま。段時間はtimings_msから読み、build_finishedの件数・親の時刻差から推定しない。measure_rollout.py、既存の計測入力・集計形式、driverの5種のイベントは変えない。

## 5. Aの不変保証と最小テスト

Aのfixture・原本ハッシュは変更しない。Probeの比較式・許容・述語名と補助関数を意味を変えず移す。既定/明示A、Aの初回PROMPT、CLI設定、freecadcmd、終了0/1/2、一次失敗のfailed_phase/probe_status/next_actor不変、警告処理、所有プロセスだけのcleanup、J1無効、CIM不使用、consoleへ切り替えないことを維持する。geometry_okはdriver/cad_runではnull、script_okを追加しない。時間・時刻の追加までJSON全体のバイト一致は要求しない。

CADなしの既存tools.test_cad_run / tools.test_cad_agent（4593d43で計20件）を維持する。追加は以下の3群に絞る。

1. 既定A/明示B/未知taskの無起動、課題別プロンプトとargv、workerの課題照合。Aの既存プロンプトが変わらず、BへAの形状を送らないこと。
2. Bの独立した合成計測で正しい形状・履歴は合格、Chamfer欠落・Pocket深さ不一致・穴数/中心ずれは拒否。全てをbroken fixtureへ混ぜず、各述語の境界を確認する。
3. 偽時計/偽Appで4段、例外時の経過、未到達null、worker元時刻の保持、親だけの行はworker_ts=null、後段失敗が一次判定を変えないこと。

モックでnative Pattern/Chamferの動作済みとは判定しない。監督側でA good→A broken→B good→B brokenの4スモークを新しい出力先で実行する。A goodはphase3-smoke.mdのexit 0/pass・体積22239.9556819442・15面、A brokenはexit 1/predicate_fail・体積22500.0・11面・next_actor=solと照合する。時間の一致は要求せず、Aが崩れたらBへ進まない。

## 6. good/broken fixtureとBの受入

新規tools/fixtures/cad_run_b_build.pyに§1どおりのgoodとbuild_without_chamferを置く。**brokenはChamferを省く1点だけ**で、TipをLinearPatternにする。板・中央Pocket・穴Pocket・Patternの個数/配置/Length設定はgoodと同じ。新規入力コピーでbrokenを選び、good原本・A原本は上書きしない。

broken体積は **導出・未実測：45600−270π mm³**、goodとの差は **導出・未実測：416/3 mm³**。volume / feature_counts / feature_chain / outer_chamferで拒否し、bboxやvalid solidだけで通さない。個数3→2などの第二の破損は入れない。

DPC-019、FreeCAD 1.1.4、recipe freecadcmd、timeout 300でgoodの全述語と実読取、brokenのexit 1・probe_status=predicate_fail・failed_phase=probe・next_actor=solを確認する。両方で保存、文書close、所有プロセスの終了・回収状態、timings_msとworker時刻を記録する。build例外なら所期のProbe不適合を示したと扱わず、fixtureを見直す。Bの導出値と観測残差を確認して許容を確定した後に、B2試行へ進む。

## 7. ファイルと行数

全て **［推定・未計測］**。新規3本（Python2本＋runbook1本）、既存6本の変更を目安とし、Aの移設を純増へ二重計上しない。

| ファイル | 内容・目安 |
|---|---|
| tools/cad_run_probes.py（新規） | A約150行を移設＋B/spec/プロンプト、計約450行 |
| tools/fixtures/cad_run_b_build.py（新規） | good/broken共通化、約160行 |
| docs/runbook-B-plate-pocket-hole-pattern-chamfer-driver.md（新規） | 仕様・スモーク・B2 N=3、約40行 |
| tools/cad_run.py | task照合・内部時間・時刻の転記、純増約40行 |
| tools/cad_run_freecad.py | 約150行移出、段計測等約60行追加、純減約90行 |
| tools/cad_agent.py | --task・プロンプト選択、移設差引後の純増約30行 |
| tools/test_cad_run.py / tools/test_cad_agent.py | 必要な境界テスト、合計純増約100行 |
| tools/README.md | Bと時間欄の説明、純増約10行 |

純増約740行［推定］。新フレームワーク、外部パッケージ、GUI、読取仲介、新測定CLI、一般的なプラグイン探索は作らない。後続実装はproto/cad-run上で行い、既存reportsとmeasure_rollout.pyを変更しない。

## 8. B2 N=3の試行条件

上のテスト・4スモーク合格後、監督側が新しいrun-idでBを順次3回実行する。run1をwarm-upとして残し、run2/3を主報告とする。停止run・CAD未到達・全attemptを隠さない。Aの集計へ混ぜず、B専用の新規aggregateにする。

- cad_agentがcodex execをsubprocessで呼ぶ。gpt-6.1-sol/xhigh、BRIEFの確認済み10無効化フラグ、read-only、CODEX_HOME継承、resumeなし、attemptごと新規、リポジトリ外の新規空cwd。作業先は回収し、個人パスを成果物に残さない。全ツールが止まるかという既存の未確認事項を新たな保証にしない。
- SolはUTF-8のbuild(doc)ソースだけを返す。driverが選択Bでcad_runを起動し、出力はreports/cad-run/<run>/a1〜a3の新規ディレクトリ。レシピfreecadcmd、timeout 300、初回を含めCAD最大3回、consoleへ切り替えない。fixture・evidence・既存runの解答・API例はSolへ渡さない。
- 修正はnext_actor=sol、build/probe、Probe例外でなく、文書close済み・cleanup_status=exited・cad_exit_codeが整数のときだけ。非0整数は修正を妨げず、成功は従来どおりraw exit 0・Probe pass等の整合を要求する。型だけのbuild診断、全値nullのmeasurementsで述語差なし、human、launch/dialog、未知担当、不正JSON、未回収では止める。修正入力は直前ソース・実exit・取得済みの7診断項目のみで、例外文や実測値を補わない。
- 主時計はdriver wall_ms、Sol/cad_run/worker時間は内訳。usageは呼出しごとのturn.completedの生の項目と出典を保持し、cached/reasoningを足さず、累積か増分か未確認の値をdriver内で合算しない。geometry_okの監督判定はProbe由来とnotesに明記する。
- A B2や10/05との比較は課題・道具・サンプル数の違いを明記した参考比較とし、難易度差を速度改善率にしない。詳細例外文/発生行の返却は別件のまま、今回の停止条件を緩めない。

出典：grok-r2.md、codex-r2.md、両R1、ユーザー20:00/20:05の更新、tools/cad_agent.py（4593d43）、design/cad-run-driver/EVAL-CONSENSUS.md、design/cad-run-arch/phase3-smoke.md、reports/aggregate-A-box-pocket-fillet-driver.json。仕様値は提案、導出値は未実測、行数は推定である。

## 署名

- codex: AGREE
- grok: AGREE
