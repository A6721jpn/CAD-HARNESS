# CAD-HARNESS VERIFY v2 — grok R1

実用barの分数・回数はPLAN-CONSENSUSのまま（W1–W5で8/10かつ各1/2、W6は2/3、S2は4/5、A1は2/3、A2/A3は各4/5かつ発明0、Kは成立/検出6/6・最終4/6・各1/2・specとsourceの両方）。eval-v1とlegacyも不変。採点Nを増やすと8/10や4/6の意味が変わるので、安い追加はbar外のCだけ。1 runは900 s、CADはmin(300, run残)。3 hはphase全体の単調時計10800 sのままで、1件3 hにはしない。

## 1. Probeの駆動寸法

`cad_verify_probe.py:511-521` はconstruction上のDistance/DistanceX/DistanceY/Radius/Diameterを、Revolution/GrooveのReferenceAxisが指した軸だけ数える。v1 V5のPCDはThroughHoleProfile内のconstruction円、Diameter=60（First=1, Type=18, IsDriving）、実穴からのPointOnObjectが8件。goldの`key_dimensions_mm[7]=60`が`edit.driving_dimension.7`でactual null。幾何は通っていた。

修正は使用スケッチ内の到達性だけ。種は非construction幾何。外部原点・軸（負index）は種にしない。Coincident / PointOnObject / Tangent / Symmetric / Equal / Distance / DistanceX / DistanceY / Angle / Perpendicular / Parallel / Horizontal / Vertical で、両端が幾何index≥0かつ片方が既到達ならconstructionへ進む。Radius/Diameter自体は辺を作らない。到達した幾何のdrivingかつactiveな寸法だけ値に入れる。ReferenceAxis規則と半値一致は維持。未使用constructionは到達しない。全construction無条件加算はしない。gold・許容差・幾何gateは変えない。mvp-v1 probeは変えない。

Sol前offline：v1 V5 r1/r2の保存FCStdで60が取れること、同じ60を実穴と結ばないdecoy円だけでは60が取れないこと、新規W5のpositive nativeが通りnegativeが落ちること。不一致は停止し、goldを観測に合わせない。

## 2. parse枠とrepair枠

MVPの共有3 callは不変。verify-v2だけ分ける。parseは1 runに1回までで、生成にもrepair応答にも使えるが両方には使えない。repair枠は1回で、settledな修復可能CAD失敗の後だけ使う。条件はscript完了、document closed、cleanup exited、cad exit 0、probe_status=predicate_fail、harnessのlaunch/save/export/close/例外ではないこと。parseはこの枠を消費できない。repair後のCADは1回。CAD attempts上限は2（初期+repair）。3回目の修復はしない。上限リセットも正解sourceの差替えもしない。

fallback（W1–W5、K1、K2）の非予約枠は3（初回、parse、source）、予約repairで合計4。in-schema（W6、S2、A1、K3）は非予約2+repairで合計3。A2/A3は合計1、parseもCADもrepairもない。予約callはquota不許可、run残≤6 s、suite deadlineでは出さず、その行はmiss。900 sは延ばさない。

保証は「枠がparseで消えない」ことであり、deadlineを超えてSolを撃つことではない。生成でparseを使うと、repair応答の再parseはない。その場合もrepair call自体は1回出る。

## 3. 回答後の完成（bar外）

A2/A3の初回採点はv1と同じ（正fieldだけ、発明0、Sol 1、CAD 0）。C2/C3は別cohortでbar_metに入れず、幾何率にも足さない。初回がrubricと一致した時だけ、凍結answerを続ける。現行driverはthread resumeがないので、2回目のuser bytesは`description.txt`のbytes、LF 1個、`answer.txt`のbytes。説明文に答えを書かない。field IDヒントも足さない。goldは完成幾何。不一致の初回はCを起動せずnot_reachedとして分母に残す。完成側はin-schema枠（spec、parse 1、repair 1、CAD 2、900 s）。WilsonはCだけで出す。

## 4. 新規holdoutとN

採点IDはv1と別。人手の日本語、UTF-8、BOMなし、説明SHAをgoldへ。体積は解析式。FreeCAD測定で式を合わせない。S2は全体積を合否にしない。v1のtest一式はdevへ移し、evaluation外、率に入れない。positive/negative native、fault candidate、rubric、run-order、SHAをSol前にsupervisorがlocal commit。新prefixと新aggregate。v1 reportsは上書きしない。schemaは広げず、W1–W5はunsupported→sourceのまま。

| ID | N | 凍結する説明の寸法（payloadはこの文） | 解析gold |
| --- | --- | --- | --- |
| W1 | 2 | 外径40、長さ48、下端Z=0、貫通穴直径10、溝Z=20..28、幅8、半径深さ3 | 17112π |
| W2 | 2 | Z=0は50×30、Z=40は30×18、中心一致、比例縮小、穴なし | 39200。Z=20は40×24 |
| W3 | 2 | 経路R32、外径16、内径10、(0,0,0)+Xから(32,32,0)+Y | 624π²。bbox [0,40,-8,32,-8,8] |
| W4 | 2 | X=-36..36,Y=-24..24,Z=0..24、壁と底4、rib Y=-2..2、頂点(-32,4),(32,4),(32,16) | 33280 |
| W5 | 2 | 外径96、厚さ10、中央穴24、PCD72に直径6が6個、+Xから60度。溝10×3深さ2を(-18,-20),(18,-20) | 21060π−120。駆動寸法に72 |
| W6 | 3 | 96×64×14、ポケット22×14深さ4を(±22,0)、穴D5をX=-30,0,30とY=-22,22、外周C1 | 83552−525π−(160−4/3) |
| S2 | 5 | 70×50×18、ポケット22×16深さ5、上面外周R2.5、垂直辺は鋭い | stock 70×50×13=45500。scope z=0..13。全体積は記録のみ |
| A1 | 3 | 90×50×12、中央穴D10。既定の中心と底Z=0 | 54000−300π |
| A2 | 5 | 70×36、底Z=0、四隅D5、中心は外形からX8 Y7。厚さなし | fieldはplate_thickness |
| A3 | 5 | 64×40×12、底Z=0、通し穴D8が2個。位置なし | fieldはhole_positions |
| C2 | 3 | 76×44、底Z=0、四隅D6、中心は外形からX9 Y8。厚さなし | answer「厚さは11。」V=36784−396π。中心(±29,±14) |
| C3 | 3 | 72×46×9、底Z=0、通し穴D7が2個。位置なし | answer「穴中心は(18,0)と(-18,0)。」V=29808−220.5π |
| K1 | 2 | W1のsource注入。溝なし | predicate roller |
| K2 | 2 | W5のsource注入。PCD穴1個なし | predicate holes |
| K3 | 2 | W6のspec注入。1穴をD5→D8 | predicate holes |

順：時計開始→dev-live最大4（v1形状と新規各1の経路確認、率外）→legacy 4→eval-v1のP1,P1,P2,P2,P4,P4,P5,P5,P3,P3→r1/r2でW1..W6,S2、r3でW6,S2、r4/r5でS2→A1×3→(A2,A3)×5→(C2,C3)×3→(K1,K2,K3)×2→新aggregate。

計画Sol（parseなし。cleanなW/S/Aはrepairなし。Cは質問+完成specの2でrepairを含まない。Kだけ注入後repairを含む）：dev4+eval10+W1–W5の20+W6の3+S2の5+A1の3+A2/A3の10+C12+K1/K2の12+K3の4=83。上限はfallback 4、in-schema 3、ask 1、Cは4、MVPは従来3で、全枠を使い切ると163。v1実績は75 callでinput 2507904、output 95506。この比率をv2の保証にしない。55/60と5分snapshot、欠測nullは維持。

リスク：到達規則が広すぎるとdecoyが通り、狭すぎるとray経由のPCDを落とす。両方を保存FCStdとdecoyで止める。半値一致は30と60を取り違え得るので、新しい別名一致は足さない。devをevaluation=falseのpreviewのままCAD成功と採点しない。pilotを見てtest goldやNを変えない。最初のharness失敗、SHA不一致、false passで版を止める。
