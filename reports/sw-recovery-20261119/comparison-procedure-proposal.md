# H2 比較手順の提案（未承認・未実装）

## 1. 結論と適用境界

**次の独立 run では、事前に割り当てた A/B 全試行を残す intent-to-treat（ITT）型の記述集計を主報告にし、timeoutをcache欠測で隠さず元の公式不合格として残すことを提案する。** usage欠測だけで公式合格を不合格に変えず、公式結果がない試行は不明/未実行とする。cache一致の感度分析と現行採用判定を別欄にする。現行run・公式採点・採用分母は変更しない。

- 「主報告」と「採用判定の主解析」は別。全割当集計を採用判定にも使うなら、現行の「一致5組」と異なる規約になるため、**ユーザー判断と新しい独立事前登録が必須**。2件差を任意の全割当分母へ流用・比率換算しない。
- 現行の gain **2/5 以上**、critical invention 非増加、平均 active time・model calls 非悪化、fresh holdout **5/5** を緩和しない。試行ごとの公式 pass、採点、policy、カード、時間枠、較正・課題選択・呼出し上限も変更しない。
- 下記の集計規約・停止規約が未解決なら、**新たな課金 run の凍結・開始はしない**。本書だけで課金・再実行・設定変更を許可しない。

## 2. ソースで確認した現行挙動と証拠の限界

以下の全体経路はソース確認であり、旧runの再測定ではない。別途、未変更の`cache_match/compare`だけをASTから隔離して人工入力6ケースを実行し、**6/6 PASS**を`comparison-source-smoke.json`に保存した（usage欠測除外、1 percentage point境界、2件gain、時間非悪化、4組拒否）。CAD/COM/model呼出し0。将来の提案手順は未実装で、旧run個別成果物/private入力は開いていない。

| 確認事項 | 正確な根拠と意味 |
|---|---|
| cache 除外 | `tools/sw_h2.py:27-37`。initial の uncached/read/write の3値は、bool を除く非負整数、合計は正である必要がある。欠測・不正値は `unknown_or_invalid_initial_cache`。read / (uncached + read + write) の差が **1 percentage point を超える**と不一致。境界は整数交差積で判定する。 |
| 分母・選択 | `tools/sw_h2.py:199-219`。較正は各5回すべての公式 pass を数え、2または3件なら課題選択。比較は最大10組を実行し、最初の cache 一致5組まで収集。一致しない組は `pairs` に残るが `compare(matched)` の分母には入らない。payload hash 不明・不一致は cache 除外で済まず停止する（210-211行）。 |
| 採用ゲート | `tools/sw_h2.py:40-54,218-220`。ちょうど5一致組が必要。B−A の公式 pass 件数差 ≥2、critical invention 件数非増加、各5試行平均の `model_calls` と `active_s` は B≤A。時間・calls 欠測／非有限／負値は採用不可。その後の fresh holdout は全件公式 pass が必要。 |
| usage の出所 | `tools/sw_h2_runtime.py:445-455`。最初の `charged=True` の model 完了イベントから initial usage を採る。イベントがなければ usage・payload 等は不明。`tools/cad_verify_v4_live.py:471-481,492-500` では model timeout 等の transport failure は usage 不明として保存し、provider rejection の免除とは区別する。timeout だから cache=0／token=0 とはいえない。 |
| 実 wall と active | `tools/sw_h0.py:40-54` は実 monotonic の `wall_s` と transport clock の `active_s` を別測定する。`tools/cad_verify_v4_agent.py:105-115` の active clock は除外時間を差し引く。`tools/cad_verify_v4_live.py:356-370,471-478` は provider 待機と明示的 rejection 時間を active から除外する。採用比較の時間は wall でなく active。 |
| 全体／stage の期限 | `tools/cad_verify_v3_guard.py:45-63,90-112` は episode 900秒・initial stage 450秒、cleanup reserve 30秒等を定義。`tools/sw_h0_runtime.py:110-114,138` の共有 guard は `deadline=None`、残時間は無限大。H2 が渡す clock は active（`tools/sw_h0.py:42-44`）。よってこれは一律の「global wall 420秒」ではない。 |
| model timeout | `tools/cad_verify_v3_guard.py:98-103`、`tools/cad_verify_v3_agent.py:289-293,309-341` で stage 残時間等から呼出し期限を算出する。initial の約420秒は450秒−30秒 reserve に整合するが、実効値は経過時間に依存する。`tools/sw_h0_runtime.py:155-189` の期限切れは所有 OMP process の停止であり、SW 終了の証拠ではない。 |
| native／SDK timeout | `tools/sw_h0_cad.py:36-46,55-62,80,100-101`。SW client と neutral SDK worker は別の期限・停止コードを持つ。期限切れに止めるのは所有 Python client/SDK process だけで、共有 SW server は停止しない。`STOP_SW_nonresponse_no_restart` というコードだけで SW のクラッシュ原因が確定するわけでもない。 |
| closed neutral timeout | `tools/sw_h2_runtime.py:173-194,245-255` は neutral timeout のときだけ、COM 完了 PASS、stop/unknown=false、文書0、PID/revision・現在 identity 一致から証明を作る。`tools/sw_h2.py:166-181` は証明付きなら不合格のまま episode timeout を記録し停止扱いを解除するが、公開 `failure_class` は正規化される。これは SW 障害の包括的な回避規則ではない。 |
| 公式合否と保存 | `tools/cad_verify_v4_live.py:643-677` が公式 pass と episode timeout 不合格を決める。`tools/sw_h2.py:175-183,225-235` は試行・除外・集計を保存する。新しい記述フラグでこの公式 `passed` を上書きしない。 |

**レビューは参照、旧 run の再測定ではない。** `reports/review-fable-20261114.md:62-68` は E7 の約420秒打切り、P01B/P02B 等の usage 欠測と選択バイアスを指摘する。今回確認した実装はその除外経路を裏付けるが、「すべて CAD timeout」「全失敗の原因は応答速度」とは確定しない。時間の近似値・正規化済み `failure_class` だけから原因を割り当てず、model 例外、stage/episode 期限、native worker 記録、host/controller の終了証拠を区別する。外部 global-wall watchdog の存在・発火が未確認なら `unknown` とする。レビュー第4節（194-199行）のゲート見直し、複数題化、時間無制限再検証は本提案には採用しない。

## 3. 次の独立 run で事前登録する変更案

### 割当・metadata（将来の実装仕様）

1. **割当単位は A/B の trial label**（model の transport retry や CAD attempt ではない）。既存の比較順・最大10組／最初の5一致組まで、quota・budget・安全停止を維持する。unit の実行前チェックを通った後、A 実行前に A/B 両方を不可変の assignment 台帳に記録する。割当後の除外・補充・再採番は禁止。将来の予定だけで未割当の組は分母外とし、予定数・割当数・開始数・完了数を別記する。
2. assignment ごとに `study_id`, `protocol_sha256`, `experiment_manifest_sha256`, `assignment_id`, `pair_index`, `label`, `case_id`, `arm`, `phase`, `assigned_at_utc`, `assignment_order` を記録。新しい independent run と旧 run の参照関係を明示し、旧結果を新しい割当に流用しない。既存の課題・入力同一性チェックはそのまま通す。
3. outcome は `execution_state = not_started | started | result_saved | interrupted`、元の `official_passed`（未取得は null）、`completed`, `stopped`, `initial_usage` の3値と `usage_status = valid | missing | invalid`、元の `wall_s`, `active_s`, `model_calls`, `cache_match`, `excluded_reason` を保持。既存モデル／CADイベントへの参照を付け、欠測値には `missing_reason` を付ける。token/cache/calls/時間のゼロ補完や推定はしない。
4. 期限イベントは `timeout_origin = episode_or_stage_active | model_process | SW_client | neutral_sdk_worker | external_global_wall | unknown`、`clock_basis`, `stage`, `configured_limit_s`, `effective_timeout_s`, `elapsed_s`, `observed_error_type`, `stop_code`, `evidence_refs` を保存。不明な期限値は null。`external_global_wall` は明示的な watchdog 証拠がある場合のみ。`native_state = not_observed | certified_closed | unknown`、証明 hash、終了／COM の観測参照を別に持ち、**期限の発生箇所と根本原因を混同しない**。生の例外・private 内容は公開欄へ転記せず、公開は安全な分類と証拠 hash に限定する。

### 集計・decision の分離

- 主記述欄 `assigned_attempts`：比較phaseの全assignmentを残し、公式合格・公式不合格・結果不明・未開始を別々に数える。**official_passed=trueはusage欠測でも合格のまま**。既存判定でtimeout不合格となった試行はそのまま不合格。結果なし/割当後未開始の片側を実行済みの不合格へ書き換えない。cache/usageの欠測は別の観測品質欄で記録し、token=0等を補完しない。
- A/B別に割当n、開始n、公式合格/不合格/不明/未開始数、timeout出所別件数、usage欠測数、pair別outcomeを表示する。全割当nに対する確認済み合格数/nは**達成率の下限**と明記し、不明を含む完全な合格率とは呼ばない。分母と不明数を伴わない差や統計的確認を主張しない。time/calls/tokenは実測値と欠測nを併記し、既知値だけの参考平均で採用の非悪化を立証しない。
- `cache_matched_sensitivity`：現行 `cache_match`、同一 payload 条件、最初の5一致組という選択を保つ。採用と照合できるよう**元の公式 pass**を用い、採用された pair index、除外理由・arm 別 usage 欠測内訳と全割当からの脱落数を示す。5組未達は未成立。usage が有効な timeout は一致し得るので、「timeout は必ず除外」とは記述しない。これは主記述と定義が異なる選択集団であり、バイアスが消えた証明ではない。
- `official_adoption`：承認されるまでは既存5一致組の `compare` と fresh 5/5 のまま。主記述が良好でも採用を救済しない。全割当での採用判定へ切り替える場合は、別の事前登録として分母・必要組数・欠測 time/calls の扱い・停止規則をユーザーが決めるまで開始不可。勝手に2件差・時間・calls・fresh gate を置換しない。
- 較正と final は比較集計へ混ぜず、phase 別の全割当と元の公式 pass を併記する。較正選択も fresh 全合格も元の公式 pass を維持する。

## 4. 無益性と課金・旧結果の保全

無益性停止は**未実装の任意承認事項**とする。現行ゲートのまま証明できる例は、確定した最初の一致組 m 個（m≤5）における公式 pass 件数差を d とすると、残り各組の最大寄与は +1 なので、最終差の上限は `d + (5-m)`。これが **2未満**なら残りがすべて B 合格・A 不合格でも gain gate に届かない。例：m=4,d=0 なら上限1で不採用確定、m=3,d=0 なら上限2なのでこの理由では止められない。前提は確定一致組の差替え・再選択なし、公式 pass の再採点なし、既存5組ゲートの維持。**全割当の記述差でこの判定をしない。** 平均時間・calls の途中悪化や確率的予想だけを停止理由にしない。

この停止を導入しても採用基準は緩まないが、割当数・情報量が変わるため新しい事前登録と承認が要る。導入しない間は現行停止規則を維持する。止める場合は `futility_not_adopted`、m/d/上限・根拠 pair index、未割当数を記録し、未割当試行を観測済み失敗と呼ばない。

旧 E7 の保存済み14試行は、レビュー35-38行による歴史的参照であり、今回の測定や最終採用の証拠ではない。旧 manifest／result／ledger／呼出し負債は不変保存し、新手順への遡及適用、再採点、課金済み出力の replay、返金・call 枠の復活を行わない。cache 除外も消費を消さない（`tools/sw_h2.py:107-120,128-147,232`、`tools/sw_h2_runtime.py:321-362`）。現在残高・quota の新規測定は本書ではしておらず、過去の残高を新しい利用可能額として転記しない。

## 5. 承認後に用意する決定論的・隔離回帰シナリオ（提案のみ）

人工の公開 row/event、fake clock、注入した process/identity 応答、一時ディレクトリだけで実施する。CAD/COM/model 呼出し、実 quota/registry、private fixture、旧 ledger は使わない。**以下の将来手順シナリオは未実装・未実行**。上記6ケースは既存の純粋関数だけのsmokeであり、新しいassignment/reportingの動作証拠ではない。既存テストもソース参照に限る（`tools/test_sw_h2.py:24-61,153-186,237-264`）。

| 人工入力／操作 | 必須の期待結果 |
|---|---|
| A は公式 pass・usage 有効、B は model timeout・initial usage=null | 全割当 A/B 各1、主記述 B失敗、cache 感度から組を除外。B tokens/cache は null のまま、呼出し負債は保持。SW 障害とは分類しない。 |
| 公式 pass=true だが usage の1値欠測。別入力では bool・負値・全0・非整数 | 公式値と全割当欄の合格を保持、cache は unknown/invalid。観測品質欠測と形状不合格を混同せず、tokenをゼロ補完しない。 |
| usage=(900,100,0) 対 (890,110,0)、次に (889,111,0)。write bucket だけ変えた入力も使う | 差1 percentage point は一致、超過は不一致。read が uncached より大きくても有効、write を総入力に含める。巨大整数でも同じ決定。 |
| initial fake clock を450秒 stage・30秒 reserveから進め、model の `TimeoutExpired` を注入。別入力は明示的 stage/global-wall イベント | 実効期限と clock を別記し、model／active stage／外部 wall の出所を混同しない。OMP timeout から native failure を捏造しない。 |
| neutral SDK timeout＋closed 証明の全条件成立／文書1・identity違い・証明なし・SW client timeout | 成立時だけ certified closed、不合格維持。その他は安全停止・状態不明を保持し、closed 証明を他の失敗の bypass にしない。 |
| A/B 割当後 A 保存・B 開始前に controller 中断。別入力で明示的 provider rejection とその後の応答 | 片側も全割当分母に残り `not_started`。transport retry で assignment を増やさず、provider 免除は既存課金規約のまま。未割当の予定組は分母外。 |
| 5一致組で公式 gain=2、時間/calls等値。その後 B の時間又はcallsを微増／critical invention増加／時間欠測、fresh は4/5と5/5 | 等値は比較ゲートを通過し得るが他条件違反は不採用、fresh4/5は不採用。主記述が良くても各ゲートを上書きしない。4一致組を5組に見せない。 |
| m=4,d=0 と m=3,d=0 の確定一致 prefix | 無益性の算術上限はそれぞれ1と2。前者だけ gain 不可能の証明になり、後者は継続可能。承認前は停止動作を追加しない。 |
| 人工の旧 result/ledger に固定 hash・消費を置き、新しい記述 report を生成 | 旧 bytes/hash・消費は不変。除外・中断・無益性を理由に replay/refund/reset せず、新 report は新 study ID。 |

### ユーザー判断が必要な事項

1. **全割当の公式結果を主記述として併記し、採用は現行一致組のまま**という安全な案を採るか。全割当を採用の主解析にもするなら別規約・独立事前登録が必要で、本提案はその採用基準を決定していない。
2. A/B同時割当と、不明/未実行を失敗と偽らない達成率下限の記述を、新しい独立事前登録に含めるか。公式合否や既存停止horizonは変えない。
3. 上の論理的に証明できる gain 無益性停止を将来採用するか、既存停止だけに留めるか。

**安全な既定値：未承認の分析・停止変更を実装せず、旧結果と消費を保全し、論点が解決するまで新しい課金凍結を行わない。**
