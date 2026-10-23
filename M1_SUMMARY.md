# SolidWorks版 Harness2 M1 結果

## 結論

**承認された「元60題のgold仕様の移植確認」を完了。CAD対象45題は全項目合格。作れない形状・未証明の追加確認は0件。課金・生成モデル呼び出し0回。**

元60行はすべて保持した。質問11行・オフライン対照4行はCAD作成の対象外であり、合格CADに数えない。これはLLM生成や障害復旧の本番採点ではなく、元のv4成績57/60を変更しない。

| 確認項目 | 結果 |
|---|---:|
| SW APIで作成、native保存・閉じる・再オープン、STEP出力、元の幾何判定 | 45/45合格 |
| 参照形状との形全体の双方向境界距離が0.005mm以内 | 45/45合格 |
| 実際に消費されるnative寸法1つの変更・再構築・形状変化・復元 | 45/45合格 |
| 意図的な誤仕様の拒否（形状種別ごとの対照） | 6/6拒否、誤合格0 |
| 元の質問／オフライン対照 | 11/4行を対象外として保持 |
| 回帰テスト | 11件合格（ホスト5、FreeCAD実体6） |

対象の形状種別はrect_prism 30、roller 5、flange 4、taper 2、elbow 2、ribbed_box 2。SWのスケッチ・押出・カット・ロフト・回転・仕上げによって作成した。FreeCADから作った形状をSWへ輸入して作成成功とする方法ではない。

## 判定の扱いと限界

- 元のFreeCAD 1.1.4幾何判定・gold・カード・許容値は変更していない。元カードの線形許容値は0.01mmであり、追加の形全体0.005mm確認とは分離した。
- 全体偏差は元M0の全境界オフセット包含証明を使用。ribbed_box等でオフセット証明が得られない場合は、変更していないv4の平面・全トリム領域の区間証明を全実面の一対一対応に適用した。点サンプル、最小距離、体積一致だけで合格にしていない。入力の保存公差の余裕も含める。
- 曲率G2が必要な接続部は元60題に含まれないため、本M1では非該当。元の形状名G2はテーパーであり、曲率G2の意味ではない。M0の専用G2対照とは別である。
- 編集確認はnativeの消費寸法1つについての証拠であり、全寸法の拘束完成や元のFreeCAD PartDesign履歴の認証ではない。元のFreeCAD履歴判定をSW STEPで通ったと読み替えない。
- completion/fault等も元の区分を保持してgold形状の移植だけを確認した。LLMによる質問応答・修復・故障回復・本番採点は実行していない。新しい未使用holdoutの成績ではない。
- OCCTのBRep・オフセット演算と保存公差を前提とする。任意形状、他のSW版・STEP設定、アセンブリや自由曲面一般まで保証するものではない。

## 時間と途中修正

| 実行段階 | 実測秒 |
|---|---:|
| 初回60行（45形状作成、質問・対照は対象外） | 844.085 |
| 保存済みCADから未完10行の追加確認 | 167.589 |
| 合計（丸め前の値で合算） | 1011.673 |

合計は約16分52秒。開発用対照・回帰テスト・実装時間はこの合計に含めない。下表は各行の初回処理と必要な追加確認の実測合計で、秒の小数第3位に丸めた。

初回から45形状すべてが元の幾何判定に合格した。追加確認だけに残った問題をM1アダプター内で修正した。

1. 旧goldの穴注記`through`は実行build-specのフィールドではない。明示された切断範囲zを維持して注記だけを変換し、厳密spec検証は維持した。
2. ポケット後の貫通穴の深さを増やしても、穴が貫通済みなら形は変化しない。有限ポケットの寸法、または仕上げ寸法を選んで編集を確認した。
3. 復元偏差の二分探索1回では上界を絞れなかった例を、元の距離関数の既定8回で確認した。閾値は不変。

保存済み50行の合格／対象外結果は保持し、未完10行だけを再確認した。うち矩形9行は既存nativeのコピーで編集・復元のみ実施、他の1行は保存STEPだけで再判定した。元の45形状を新規作成し直していない。公開の開発用8形状と、保存nativeコピーの編集専用経路も確認済みである。

## 全60行

序数は元ファイル順。PASSはその列のM1確認の合格、NAは元の質問・対照でCAD非該当。SW編集は上記の1消費寸法の変更・再構築・復元を指す。元区分・経路は変更していない。

| 序数 | 元区分/経路 | 形状種別 | 元幾何 | 全体0.005mm | SW編集 | 秒 |
|---:|---|---|---|---|---|---:|
| 1 | dev/source | roller | PASS | PASS | PASS | 29.622 |
| 2 | dev/spec | rect_prism | PASS | PASS | PASS | 16.647 |
| 3 | dev/ask | — | NA | NA | NA | 0.000 |
| 4 | legacy/offline | rect_prism | NA | NA | NA | 0.000 |
| 5 | legacy/offline | rect_prism | NA | NA | NA | 0.000 |
| 6 | legacy/offline | rect_prism | NA | NA | NA | 0.000 |
| 7 | legacy/offline | rect_prism | NA | NA | NA | 0.000 |
| 8 | mvp/mvp | rect_prism | PASS | PASS | PASS | 12.457 |
| 9 | mvp/mvp | rect_prism | PASS | PASS | PASS | 10.814 |
| 10 | mvp/mvp | rect_prism | PASS | PASS | PASS | 38.339 |
| 11 | mvp/mvp | rect_prism | PASS | PASS | PASS | 38.369 |
| 12 | mvp/mvp | rect_prism | PASS | PASS | PASS | 7.930 |
| 13 | mvp/mvp | rect_prism | PASS | PASS | PASS | 7.960 |
| 14 | mvp/mvp | rect_prism | PASS | PASS | PASS | 20.932 |
| 15 | mvp/mvp | rect_prism | PASS | PASS | PASS | 20.869 |
| 16 | mvp/mvp | rect_prism | PASS | PASS | PASS | 10.983 |
| 17 | mvp/mvp | rect_prism | PASS | PASS | PASS | 11.037 |
| 18 | geometry/source | roller | PASS | PASS | PASS | 25.729 |
| 19 | geometry/source | taper | PASS | PASS | PASS | 21.028 |
| 20 | geometry/source | elbow | PASS | PASS | PASS | 25.784 |
| 21 | geometry/source | ribbed_box | PASS | PASS | PASS | 22.468 |
| 22 | geometry/source | flange | PASS | PASS | PASS | 48.837 |
| 23 | geometry/spec | rect_prism | PASS | PASS | PASS | 36.018 |
| 24 | geometry/spec | rect_prism | PASS | PASS | PASS | 17.544 |
| 25 | geometry/source | roller | PASS | PASS | PASS | 54.329 |
| 26 | geometry/source | taper | PASS | PASS | PASS | 14.373 |
| 27 | geometry/source | elbow | PASS | PASS | PASS | 21.279 |
| 28 | geometry/source | ribbed_box | PASS | PASS | PASS | 13.548 |
| 29 | geometry/source | flange | PASS | PASS | PASS | 34.239 |
| 30 | geometry/spec | rect_prism | PASS | PASS | PASS | 35.941 |
| 31 | geometry/spec | rect_prism | PASS | PASS | PASS | 17.553 |
| 32 | geometry/spec | rect_prism | PASS | PASS | PASS | 35.822 |
| 33 | geometry/spec | rect_prism | PASS | PASS | PASS | 17.803 |
| 34 | geometry/spec | rect_prism | PASS | PASS | PASS | 17.609 |
| 35 | geometry/spec | rect_prism | PASS | PASS | PASS | 17.495 |
| 36 | q/spec | rect_prism | PASS | PASS | PASS | 10.859 |
| 37 | q/spec | rect_prism | PASS | PASS | PASS | 11.281 |
| 38 | q/spec | rect_prism | PASS | PASS | PASS | 11.014 |
| 39 | q/ask | — | NA | NA | NA | 0.000 |
| 40 | q/ask | — | NA | NA | NA | 0.000 |
| 41 | q/ask | — | NA | NA | NA | 0.000 |
| 42 | q/ask | — | NA | NA | NA | 0.000 |
| 43 | q/ask | — | NA | NA | NA | 0.000 |
| 44 | q/ask | — | NA | NA | NA | 0.000 |
| 45 | q/ask | — | NA | NA | NA | 0.000 |
| 46 | q/ask | — | NA | NA | NA | 0.000 |
| 47 | q/ask | — | NA | NA | NA | 0.000 |
| 48 | q/ask | — | NA | NA | NA | 0.000 |
| 49 | completion/completion | rect_prism | PASS | PASS | PASS | 14.002 |
| 50 | completion/completion | rect_prism | PASS | PASS | PASS | 13.944 |
| 51 | completion/completion | rect_prism | PASS | PASS | PASS | 13.972 |
| 52 | completion/completion | rect_prism | PASS | PASS | PASS | 14.096 |
| 53 | completion/completion | rect_prism | PASS | PASS | PASS | 14.313 |
| 54 | completion/completion | rect_prism | PASS | PASS | PASS | 14.275 |
| 55 | fault/source | roller | PASS | PASS | PASS | 24.802 |
| 56 | fault/source | flange | PASS | PASS | PASS | 34.677 |
| 57 | fault/spec | rect_prism | PASS | PASS | PASS | 35.908 |
| 58 | fault/source | roller | PASS | PASS | PASS | 24.548 |
| 59 | fault/source | flange | PASS | PASS | PASS | 34.658 |
| 60 | fault/spec | rect_prism | PASS | PASS | PASS | 35.754 |

## 安全性・保存先

- 54回の実COMワーカー記録でSW PIDはすべて41448。開始時・終了時の文書数0、状態不明なし。既存インスタンスへの接続のみで、SW終了・kill・再起動は行っていない。自分の文書だけを開閉するガードを使用した。
- 54個のnativeファイル、222個のSTEPファイル、20個の共用gold入力について記録ハッシュとの一致を読み取り専用で確認した。元native・goldの変更はない。
- 非公開goldは固定プログラムだけが機械参照。本文・寸法・gold・正解由来CAD・数値生ログはLLMとGitへ出さず、`reports/sw-m0/m1-private/`内の出力をGit除外した。公開するのはコードと状態・時間・ハッシュ等の要約だけ。
- 最終公開証拠：`reports/sw-m1/original60-02/{manifest,rows,summary,safety-audit-public}.json`。初回証拠：`reports/sw-m1/original60-01/`。private成果物はローカルに保持する。
- 実装・回帰：`tools/sw_m1*.py`、`tools/test_sw_m1*.py`。既存M0/v4判定コードは未変更。`herdr/v4`・`v4-freecad-final`・タグ・`C:/dev/CAD-HARNESS-h2`は変更しない。

## 未解決の質問

本M1の承認範囲ではなし。次の段階のモデル利用や本番生成を今回の成功で許可されたとは扱わず、M1結果をcommit・pushして待機する。
