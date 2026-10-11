# ランブック: A-box-pocket-fillet（条件B: cad_run経由）

ユーザー承認: 2026-10-11 15:15 JST。形状・仕様の出典は runbook-A-box-pocket-fillet.md §1。
本書はN=5の準備。作業場所はCAD-HARNESS、CADホストはDPC-019。cad_runのコードは固定する。

## 1. Sol用プロンプト全文

`<RUN>`は各runの識別子（例 `n5-1011-run1`）。貼付前に置換する。
```text
モデル / effort: gpt-6.1-sol / xhigh。
ホスト: DPC-019。CADはFreeCAD 1.1.4のみ。SolidWorksとFusionは起動しない。LPC-017ではCADを実行しない。
単位mm、新規ドキュメント、単一ソリッドボディで次を作る。
1) 直方体。幅40 mm（X）×奥行30 mm（Y）×高さ20 mm（Z）。PartDesignのBody上で、XYスケッチの中心矩形をPad長さ20 mmとする（片方向。貫通や対称の二重化はしない）。
2) 上面中央に20×15 mm、深さ5 mmの非貫通矩形ポケット。上面スケッチの中心矩形をPocket長さ5 mmとする。Through allではない。壁はスケッチ法線方向（垂直）。
3) 一定半径R=3 mmのフィレットを上面外周の4辺だけに適用する。ポケット内側のエッジには絶対にフィレットしない。
4) 追加フィーチャなし。最終も単一ソリッドボディ。
寸法・体積・表面積・面数はFreeCAD上で実際に読めた値だけ記録する。読めなければnull。理論値を実測として書かない。実在しないマクロは作ったことにしない。
FreeCADを直接起動しない。CADの実行は以下のcad_run経由だけとし、入力.pyを直接実行しない。
build(doc)を定義したUTF-8 .pyを reports\cad-run\_inputs\<RUN>-build.py に新規作成する。
build(doc)は渡された文書に形状を作り、PartDesignのBodyを返す。新規文書作成・Probe・保存・close・プロセス回収はcad_runに任せる。
python tools\cad_run.py --script reports\cad-run\_inputs\<RUN>-build.py --out-dir reports\cad-run\<RUN> --timeout-s 300 --recipe freecadcmd
exit 0なら終了。非0ならstdoutの結果JSONのfailed_phase、probe_status、predicate_diff、next_actorを読む。
next_actorがsolなら自分の入力スクリプトを直し、新しい--out-dir（reports\cad-run\<RUN>-a2、次はreports\cad-run\<RUN>-a3）で同じコマンドを再実行する。
next_actorがhumanなら止めて報告する。結果JSONを読めない場合や担当先が不明の場合も止めて報告する。
cad_run実行は初回を含め最大3回。3回目も非0なら止めて報告する。consoleやGUIへ切り替えない。
tools\fixturesや実験前からあるreports、evidenceは読まない・コピーしない。このrunで自分が作った入力・結果だけを参照する。
cad_runやその他toolsのコードを変更しない。既存ファイル・他runの入力や出力を上書きしない。
最後に、実際に最後に使ったout-dirとexit codeを1行で報告する（out-dir=... exit=...）。
```

## 2. N=5手順（順次実行）

1. 実験開始時のcommitとキャッシュ方針（coldのみ又はwarmのみ）を記録し、全5runで固定する。既存の入力・出力・計測・outcomesは上書きしない。
2. 各runは新規サブエージェントを model=gpt-6.1-sol、reasoning_effort=xhigh、fork_turns=none で作り、固有の<RUN>を入れた§1だけを依頼本文として渡す。モデル・設定を代替しない。
3. run1をwarm-upとして完了させ、次にrun2→run3→run4→run5を順次実行する。前runの完了後に次の新規エージェントを作り、解答・コード・結果を引き継がない。
4. 各runの全attemptを同じ子のrolloutに含め、rolloutの保存先、最終out-dir、exit、attempt数を親が控える。run1は参考のみ、主報告はrun2〜5（失敗runも除外しない）。

## 3. 計測とoutcomes

`<ROLLOUT_JSONL>`は当該子のrollout、`<STEM>`はそのsource stem。全プレースホルダを実値へ置換する。親が各run完了後に新規計測を保存する。
```bat
python tools\measure_rollout.py --file "<ROLLOUT_JSONL>" --task-id A-box-pocket-fillet --out reports\runs\<STEM>.json
```
`reports\outcomes\<STEM>.json`を新規作成し、task_id=A-box-pocket-fillet、script_ok、geometry_ok、notesを記入する。
script_okは最終cad_runのexit/resultを根拠とし、exit=0かつresult.status=okならtrue、取得済みの非0/失敗はfalse、根拠未取得はnull。
geometry_okは最終resultのprobe_status=passならtrue、それ以外はfalse、結果/Probe状態が未取得ならnull。not_runやexceptionも元の状態をnotesに残し、形状の実測不適合と混同しない。
notesにはcondition=B、<RUN>、warm-upか主報告か、attempt数、最終out-dir/result.jsonという出典、最終exitとprobe_statusを記す。
outcomesを揃えてから、run2〜5の個別計測だけを明示して主集計する。run1や他条件を混ぜない。
```bat
python tools\measure_rollout.py --file reports\runs\<RUN2-STEM>.json --file reports\runs\<RUN3-STEM>.json --file reports\runs\<RUN4-STEM>.json --file reports\runs\<RUN5-STEM>.json --aggregate --out reports\aggregate-A-box-pocket-fillet-cadrun.json --csv reports\aggregate-A-box-pocket-fillet-cadrun.csv
```
集計先は条件B専用の新規JSON/CSV。既存なら上書きしない。ベースライン aggregate-A-box-pocket-fillet.json/.csv は保持する。
cad_runのevents.jsonl/result.jsonをmeasure_rolloutの入力に混ぜず、reports全体への--task-dirやglobも使わない。計測CLIと既存コードは変更しない。
