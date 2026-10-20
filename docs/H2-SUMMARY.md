# h2 MVP 状況

実装#1aは76d13d3、実走#1の保存は22a1a31で反映済み。commit/pushと実LLMサイクル起動は運用D6に従いh2leadが行う。

実走#1（20261020T151238Z-e7120eed）は一周完走し、最終probe_statusはpass。

| 実行 | 改善要旨 | 合否 | 試行数 | tokens | 秒 |
| --- | --- | --- | ---: | ---: | ---: |
| Run0 | 固定の基準 | 不合格 | 3 | 79,802 | 104.553 |
| 候補1 | 作成履歴の接続規則 | 合格 | 2 | 51,504 | 64.132 |
| 候補2 | 再試行への情報追加 | 合格 | 2 | 51,503 | 58.410 |
| 候補3 | 思考量medium＋点検指示 | 作成失敗・未検査 | 3 | 78,685 | 104.914 |
| 合成 | 候補2＋1、衝突なし | 合格 | 2 | 53,410 | 60.899 |

全体はLLM 13回、342,290 tokens、411.493秒。経験3件はsupported=2、unsupported=1。
各案一回の比較とキャッシュ条件の違いはMVPの既知の限界。反復実験は追加しない。

依頼#3でreasoning_output_tokensの読み取りに対応し、実走#1を生ログから補完した。
reasoningは合計1,427、総tokensは342,290のままで二重加算なし。
cycle.jsonの元の値は保持し、accounting_supplementsの末尾に補完値・根拠ログのハッシュを保存。
ライブラリも元の3件を保持し、measurement_supplementとして比較記録の補完3件を追記した。新しい実験はない。
補完CLIは `python -m h2.supplement --cycle-id 20261020T151238Z-e7120eed`。再実行しても重複しない。
補完後、合格条件①自動一周・②AIを使わない形状判定・③tokensと時間の記録は充足。

今後はモデル名を実行ログの報告値から記録する。未取得ならnullと理由を保存する。
実走#1の全13回はログにモデル名がなく、理由はmodel_not_reported_in_runtime_events。実値を推測しない。

単体テスト14件成功、今回の出力は [tests-library-merge.log](../reports/h2/tests-library-merge.log)。
二周連続のスタブテストで、2周目の提案に前周までのライブラリだけが渡り、当周の追記は含まれず、基準設定が固定のままであることを確認した。
提案入力では補完を元の経験に統合し、元の教訓・識別子を保持して不足する計測値だけを埋める。
実際の2周目では提案ログのprior_libraryを確認する。現時点の保存レコード6件は教訓3件に統合される。
cycle.jsonのprior_library_record_countは保存件数、prior_library_countは統合後の教訓数を表す。保存ファイル自体は変更しない。

根拠: [cycle.json](../reports/h2/20261020T151238Z-e7120eed/cycle.json)、[実走ログ](../reports/h2/live1.log)、[ライブラリ](../h2/library/cad-freecad.jsonl)。
今回、実LLM・実FreeCADの追加実行はない。コミット対象にtools/__pycache__を含めない。
