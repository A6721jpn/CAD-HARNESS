# Grok E1 — driver 方式は go with changes

判定は (1) を go with changes とする。(2)(3)(4) は no-go。複雑課題の R2 はこの評価では決めない。

条件 B は Sol が自分でシェルから cad_run を呼ぶ。2026-10-11 の N=5 は run2 で止まった。run1（`rollout-2026-10-11T15-25-43-01a129a3-7f92-78e0-aa3b-09e0409993a3`）は wall 284828 ms、session_delta total 730858、cad_run 1 回成功、script_ok true、geometry_ok true。BRIEF のとおり約 4 分は権限待ちである。run2（`rollout-2026-10-11T15-35-21-01a129ac-5291-7463-ba09-5c0bd3bbf60f`）は wall 276874 ms、session_delta total 393261、exec_command 3、cad_run 0 回、script_ok null、geometry_ok null。notes は sandbox setup marker の欠落から昇格エラー 1223 でシェル起動に失敗した、と書いている。同じ日に run1 が通過したあとでも run2 は落ちた。

2026-10-05 のベースライン（シェルあり、runs 2–5）は `reports/aggregate-A-box-pocket-fillet.json` の wall_ms_mean 489159.75、session_delta total 2470906（input 2416743、cached_input 2267648、output 54163）。BRIEF の平均 489.16 秒、LLM 応答 59、exec_command 8/12/12/11 はこれと同じ集計である。集計ファイルの top_tool_names も 8、12、12、11 である。

## 速度とトークン

(1) サンドボックス初期化の待ちを Sol の経路から外す。run2 の 276874 ms と 393261 トークンは CAD に届かずに使われている。ここが driver の直接の対象である。確認済みの `codex exec` はシェルを全部無効にし、空ディレクトリ、read-only で exit 0、7 秒、本文 `PING OK.` だった。これは CAD の所要時間ではない。課題 A の壁時計がベースラインの 489159.75 ms より短いかは未計測である。

トークンは呼び出しの分け方で定義が変わる。両 run の first.input は 20286 で、BRIEF の「最初のスナップショット約 2 万」と一致する。`measure_rollout.py` の session_delta は last−first であり、スナップショット 1 個なら 0 になる。ベースラインはこの定義で、最初の約 2 万を合計に含まない。driver が exec を attempt ごとに分けると、その欠落が attempt の数だけ増える。ベースラインの 2470906 と並べる数にはできない。

(2) 速度の見込みは、初期設定が本当に一度で済むときだけである。run2 はその前提を同じ日に外している。1223 の待ちはベースラインの 489159.75 ms には含まれていない。公平な短縮とは言えない。

(3) シェル起動の失敗は避けられる可能性がある。回避フラグの実時間とトークンは未確認であり、ベースラインはシェルありの通常経路である。フラグ付きの秒数を 489.16 秒と比べる条件はまだ無い。

(4) 読み取り調査を足すと、ツール往復がベースラインの exec_command 8/12/12/11 に近づく。ping の 7 秒は調査なしの起動である。調査ありのトークンは未計測である。

## 2026-10-05 との公平性

ベースラインはシェルがあり、Sol が CAD 操作のコマンドを自分で出している。条件 B は cad_run 経由で、runbook は fixtures と evidence を読ませず、cad_run は初回を含めて最大 3 回である。driver はさらに、誰が cad_run を起動するかを変える。三つの条件を一つの aggregate に混ぜない。`aggregate-A-box-pocket-fillet.json` は上書きしない。

cached_input 2267648 と input 2416743 はベースラインの内訳である。入力トークンが減ったことだけを費用の減少として比較表に書かない。

比較に使ってよいのは、同じトークン定義で取り直した N=5 のあとだけである。それまでは driver の表を別条件として置き、ベースラインの 2470906 と 489159.75 ms は引用に留める。

## Sol が失う能力と複雑課題

(1) で Sol が失うのは、シェル、ファイル調査、FreeCAD を自分で起動するデバッグである。課題 A では runbook がもともと fixtures と evidence を禁じ、CAD 起動を cad_run に限っている。失う調査は、A の測定手順がすでに使わせていない範囲である。

複雑課題では LinearPattern の長さの意味のように、仕様に書いていない API を Sol がその場で調べたくなる。その調査をシェルに戻すと、条件 B が止まった経路へ戻る。(1) では仕様文と、sol 向けの result 項目だけを渡す。仕様に無い API は、この評価の外で仕様側に書く。

`AGENTS.md` は exec でも読まれる、と BRIEF にある。空ディレクトリでも仕様書よりそちらを手順にする余地がある。プロンプトで課題仕様を優先すると書いておき、読み込みを止められるかは未確認である。code_mode_host を無効にすると「Code Mode is unavailable」が出る。CAD の失敗には数えない。

(4) の読み取り調査は、evidence と A の fixture を読める状態に戻しうる。runbook が禁じている参照であり、複雑課題の正答に近づく。測定条件としては (1) よりベースラインにも条件 B にも揃わない。

## 安全性

(1) は Sol にシェルも UAC もサンドボックス昇格も渡さない。確認済みの起動は read-only と空の作業ディレクトリである。スクリプトの書き込みと cad_run の起動は driver だけが行う。cad_run の出力先制限、終了 0/1/2、`next_actor` の分担はそのまま使う。

CONSENSUS では launch、Probe 自身の例外、復旧ダイアログ、cleanup 不明は human で、Sol に起動方法を書かせない。build の失敗と述語不適合だけが sol である。driver はこの分担をループの条件にする。

(2) は UAC 承認が残る。run1 のあと run2 が 1223 で落ちたので、一度の承認を測定の前提にできない。

(3) は承認とサンドボックスを外す。ベースラインのシェル経路とも、確認済みの read-only 起動とも違う権限である。測定ハーネスの常設手順にはしない。

(4) は読み取りでも、シェルツールがサンドボックスを再度要求するかは未確認である。ping はシェルを無効にしたので、サンドボックスログに新しいエントリが無かった。調査用のファイルツールが同じかたちは未確認である。

## 実装コスト

(1) は driver を一つ足す。`measure_rollout.py` と cad_run の合否は変えない。コストは小さい。必要な変更は次節である。

(2) はコードがほぼ要らない代わりに、毎回の昇格が測定手順に残る。run2 の再発をコードでは防げない。

(3) はフラグ一つで、実装は最小、安全性のコストが最大である。

(4) は driver に加えて、読ませる範囲の規則が要る。範囲を空ディレクトリだけにするなら (1) と同じである。

## go with changes で必要な変更

Sol の呼び方。確認済みの形を使う。モデル gpt-6.1-sol、reasoning effort xhigh、shell_tool、unified_exec、code_mode_host、multi_agent、apps、plugins、browser_use、computer_use、image_generation、view_image を無効、`-s read-only`、空の作業ディレクトリ、`--json`。CAD の起動は driver が `python tools/cad_run.py` で行い、レシピは freecadcmd、`--timeout-s 300`、失敗しても console に切り替えない。`codex exec resume` で 1 セッションに積めるかは未確認である。積めると分かるまで、attempt ごとに新規 exec を前提にし、トークンはベースラインの session_delta とは別系列だと結果に書く。

使用量。`--json` の turn.completed にある input_tokens、cached_input_tokens、cache_write_input_tokens、output_tokens、reasoning_output_tokens を、driver が生のまま attempt ごとに残す。それが累積スナップショットか差分かは未確認なので、driver は引き算しない。jsonl は今までどおり measure_rollout にかけ、壁時計だけを取る。スナップショット 1 個の session_delta 0 を使用量として採用しない。ベースラインと同じ last−first で比べるのは、1 セッションの中にスナップショットが複数あると確認できたあとだけにする。

プロンプトに渡すもの。課題仕様の本文、`build(doc)` だけを返す契約、新規文書と Probe と保存は cad_run が行うこと。修正回では、前回のスクリプト本文と、result の `failed_phase`、`probe_status`、`predicate_diff`、`measurements`、`message_code`、`next_actor` だけを渡す。stderr 全文、絶対パス、evidence、fixtures は渡さない。`script_ok` は cad_run が書かないので渡さない。

修正ループ。初回 1 回に修正 2 回まで、cad_run は最大 3 回。これは runbook の「初回を含め最大 3 回」と一致させる。次の attempt は新しい `--out-dir`（`<RUN>`、`<RUN>-a2`、`<RUN>-a3`）だけを使う。`next_actor` が sol のときだけ修正する。human、JSON が読めない、担当が無い、は止めて報告する。4 回目はしない。

比較の扱い。条件名をベースラインとも条件 B とも分け、新しい aggregate ファイルにだけ書く。10/05 の 489159.75 ms と 2470906、条件 B の run1 284828 ms と 730858、run2 の 276874 ms と cad_run 0 回は、それぞれの出典のまま併記する。driver の初回 N=5 が終わるまで、速度やトークンが改善したとは書かない。Sol 側の rollout で exec_command が 0 であることは、シェルを渡していないプロトコルの確認であり、ベースラインの 8/12/12/11 に対する時短の証拠ではない。

## 未確認（BRIEF に無い codex exec の挙動）

- `codex exec resume` が同一の thread_token_usage 系列を続けるか。
- turn.completed の usage が累積か、その turn の増分か。
- シェル無効のまま、空でないディレクトリのファイルを読むツールが残るか。残る場合にサンドボックス初期化が再び要るか。
- `AGENTS.md` の読み込みを exec のフラグで止められるか。
- `--dangerously-bypass-approvals-and-sandbox` が外す範囲と、昇格 1223 を実際に避けるか。
- サンドボックス初期設定のマーカーが、どの単位（アカウント、日、子プロセス）で再利用されるか。run2 の失敗は、run1 の直後の子には再利用されなかった、という記録までである。
