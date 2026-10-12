# CAD-HARNESS VERIFY v2 — Codex R1 独立案

根拠：[BRIEF](BRIEF.md)、v1 [RESULTS](../cad-harness-verify/RESULTS.md)・[PLAN](../cad-harness-verify/PLAN-CONSENSUS.md)・[FROZEN](../cad-harness-verify/FROZEN.md)、指定4コードと協議frameworkを読んだ。他者R1は未読。提案のみ、実装・試行なし。
v1のV5は使用中PCDのconstruction寸法をProbeが除外し、F1/F2はparse correction後に修復callが残らなかった。旧成績・gold・MVP挙動は保存し、verify-v2 opt-inだけを変更する。

## 1. Probe：使用関係を証明して駆動寸法を拾う
Body TipからProfile/Sections/Spine/ReferenceAxis等を辿る現行のnative検査を維持し、選択された実profile/path geometryと使用axisをseedにする。
使用Sketch内でactiveかつdrivingの幾何関係constraintsをwhitelist化し、First/Second/Thirdの実geometry ID間を結ぶ。PointOnObject/Coincident/Equal/Tangent等の到達経路を記録する。
origin/H_Axis/V_Axis等の負IDは共有hubにしない。seedから到達するconstructionだけが対象で、単に同じSketchにある全constructionを採らない。
到達geometryのactive/driving Distance(X/Y)/Radius/Diameterをmmで採り、式で駆動される場合も再計算後の値＋依存経路を保存する。reference/inactive/未使用decoy/custom数値は除外する。
証拠はfeature→Sketch→constraint→geometryのpathと値。construction PCD→実穴中心の連鎖も認め、従来のReferenceAxisだけという制限を外す。
最小offline確認はv1 V5のPCD正例、同値の未接続decoy、reference/inactive負例。全新profileの手製正負fixtureも確認し、欠測・解決不能の参照は成功にしない。
bboxのoptimal API、±0.01 mm/軸1e-6/体積1e-4、薄いnative gate、独立FCStd/STEP・close/exitを保持する。goldを測定へ合わせない。

## 2. Budget：parseとCAD repairを分け、修復slotを予約
v2専用BudgetでG（初期生成）、Ppre（初回CAD前のparse修正）、R（CAD修復）、Ppost（修復応答のparse修正）を別counterにする。Ppre=1、R=1、Ppost=1、CAD≤2。
Gはsource経路なら解釈1＋fallback source1=2、対応内なら1。Q2/Q3は質問C=1を追加。最大Solはsource5、対応内4、質問回答episode5；初回質問にはparse retryなし。
parseはJSON/schema/未対応操作の訂正で、CAD repairとは別目的。初期candidateが成立しない場合はnot_reachedとして分母に残す。初回CADでG/Ppreを閉じ、未使用slotもRへ転用しない。
修復可能なsettled CAD fail後はRを必ず1回起動する（guard許可時）。故障source/specを実測diagnostics付きで渡し、正解source差込み・counter/deadline reset・2回目のCAD修復なし。
900秒を初期450秒＋修復450秒に分割。初期生成・parse・初回CAD/成功時reimportは前半内にclip；初期timeoutでCAD fail未成立ならその旨を記録する。
修復bankはSol180＋Ppost60＋再建模/export90＋独立reimport90＋cleanup30秒。全child timeoutをphase/run残秒へclipし、FreeCAD各processは300秒を超えない。
900秒＋集計用60秒の全体残とcall予約を確保できる評価episodeだけ開始する。quota/SHA/環境/全体deadline停止が優先し、保証対象外はrepair_not_attempted_reasonで区別する。
現Budget.call/MAX_ATTEMPTS、max_calls≤3、Guard≤125を一括緩和せず、v2設定でstage枠・batch上限を渡す。eval-v1/MVPは従来3 calls/3 CAD/900秒のまま。

## 3. 質問→凍結回答→完成（barとは別指標）
Q2/Q3各5 episodeで初回1 callのfield-ID/rubric点を先に確定し、barはその初回値だけを使用する。発明・誤質問は初回0点、完成も0、回答で救済しない。
正しい質問にだけ事前凍結したuser回答を1回返し、同じ900秒・stage counterでspec→CAD→必要ならR→全gateまで進める。対話部分だけ時計を再開しない。
初文・CLI質問・回答を別turnのtranscriptに保存し、description SHA＋answer SHAへ完全goldをbindする。現description==gold.descriptionの単一入力照合をv2の二入力契約へ置換する。
モデルが見る追加情報は実user回答だけ。gold/期待値/fixtureをcontextへ入れず、前回答を流用して別episodeをwarm-startしない。
completionは全planned 5を主分母にし、正しい質問をしたepisodeに限る条件付き完成率も併記。初回/回答後初回/最終gates、実修復、時間/usage、未起動理由を別集計する。

## 4. Fresh holdout候補・N（mm；幾何行はXY中心/底Z=0、Q1は配置を省略）
| class | core N / 補助N | 新しい形状・寸法・文面の設計候補 |
| --- | --- | --- |
| V1 | 2 / 0 | 中空カラーD38/D12、L46、Z10..16に深さ3の全周溝；中心から外した溝位置 |
| V2 | 2 / 0 | 無ねじれ四角テーパー44×30→26×18、H34、同心、線形縮小 |
| V3 | 2 / 0 | XYの90°管、中心線R29、D16/D10、始点(0,0,0)接線+X→(29,29,0)接線+Y |
| V4 | 2 / 0 | 箱68×46×25、壁/底4；Y=±2のrib、XZ頂点(-30,4),(30,4),(30,17) |
| V5 | 2 / 0 | フランジD96×10、中央D24、PCD68にD6×6穴（+Xから60°）；上面14×5深さ3の溝、中心(±18,-14) |
| V6 | 3 / 2 | 板118×88×14；28×16深さ6のpocket中心(±28,0)；D5穴X=-40,0,40/Y=±32；上面外周C1.2 |
| S1 | 5 / 0 | 64×48×18、中央20×16深さ5 pocket、外周R2.5、垂直辺sharp；stock goldはZ0..13＋局所断面 |
| Q1 | 3 / 2 | 72×46×11板、中央D10のみ。XY配置/底高さは書かずbinding defaultを測る |
| Q2/C2 | 5 / 0 | 88×54板、四隅D6、縁からX12/Y9、板厚省略；回答「板厚9 mm」 |
| Q3/C3 | 5 / 0 | 78×50×12板、D8通し穴2個、位置省略；回答「中心(-22,0),(22,0) mm」 |
| F1/F2/F3 | 各2 / 0 | 上記V1の溝欠落source／V5のPCD穴1個欠落source／V6の(-40,-32)穴D5→D7 spec；一度だけ注入 |
V6/Q1は安価な補助2件で計5へ増やす。core round1..3と補助round4..5を実行前に固定し、bar分母は変えず、全5件の率/CIも別記する。
coreのthresholdはV1–V5≥8/10＋各≥1/2、V6≥2/3、S1≥4/5、Q1≥2/3、Q2/Q3各≥4/5＋発明0、fault成立/検出6/6・最終≥4/6＋各≥1/2＋spec/source実修復、旧回帰のまま。

## 5. Authoring・凍結・順序
人手で上記候補をverbatim説明へ仕上げ、生成器と独立に解析式/数値goldを導く。全geometryのnative正負、constraint decoy、所定faultのsettled failをSol前に確認する。
v1のV/S/Q/F、失敗source/FCStdはdev資料だけで、v2合格へ使わない。MVP eval-v1とlegacy A/Bは例外的に旧条件の固定回帰としてfresh実行する。
保存済みv1資料とoffline devだけで実装を確定し、新test本文/回答/rubric/gold/fault/counter/順、全code・skill・schema・CLI/model設定・継承AGENTSをSHA化。grok＋gemini各1回reviewとsupervisor local commitを済ませ、live pilotを含む全Solの前に凍結する。
実行順：共有3h開始→v1 dev pilot（3 episode、計≤4 calls、非採点previewはpreviewと記録）→legacy4→fresh eval-v1 P1/P2/P4/P5/P3各2→clean V/S→Q1→Q2/Q3→F1/F2/F3→独立集計。
cleanはv1同様のround配列でcoreを先に固定し、V6の補助r4/r5はclean末尾、Q1はcore3→補助2。Q2/Q3は交互5 rounds・各episode内で回答まで、Fは交互2 rounds；計58 episode。
eval_verifyの固定expected Counterはversion manifest由来にし、core/supplement/completion/devを混ぜない。初期/最終gate、実R起動数・成功/eligible、parse stage、全wall、provider各欄（null維持）・failure分布、完了cohortだけWilson95%を記録する。

## 6. Call見積・停止・リスク
通常経路の計画枠は85 calls＝source clean20＋V6/S1/Q1 core11＋fault16＋Q2/Q3質問/回答20＋補助4＋MVP10＋dev枠4（parse追加なし、fault実Rを含む）。実績ではない。
絶対上限222＝source14 episode×5＋対応内17×4＋質問回答10×5＋MVP10×3＋dev4；legacy0。新guardだけこの上限を持ち、残callは後続予定とR用に予約する。
55%以上は新callを止めsupervisorへ継続相談、60%以上はhard stop。5分以内の実snapshot必須；共通3h・900秒を延長せず、未完了はbar未達、成功まで追加Nしない。
リスク：拘束graphの誤接続によるdecoy false-pass、外部/選択geometryの未対応、修復bankで長いsourceがtimeout、補助とcoreの混同。Probeで参照を解決できなければharness stop、必要な反例だけで確認する。
call上限は時間/週次quotaの保証ではない。N=2のsource/faultは広いCIの限定認定；回答後完成率も一般対話能力ではない。修正後も未達なら旧結果を保持し、次版＋新未使用holdoutへ進む。
