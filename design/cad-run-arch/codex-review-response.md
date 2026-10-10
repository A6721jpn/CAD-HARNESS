# codex: PHASE 2 レビュー対応

対象: grok-review.md（初回 commit 839d97d）。#1〜5、#7、#8に同意して修正。不同意の指摘はない。#6は行数の留保を継続し、#9は指定どおりPHASE 3後に判断する。

- **#1 — 修正。** 親の失敗記録とworkerで、最初の failed_phase / probe_status / next_actor を保持する。述語不適合は保存前に一次失敗として確定し、後続の保存・文書close・CAD終了・ログ回収の障害で上書きしない。保存失敗は save_error_type、close失敗は close_error_type / document_closed、プロセス回収は cleanup_status とイベントの cleanup_action に分離する。既存の失敗がある親へのworker結果の取込みもProbe状態を変更しない。CAD終了による追加の一次失敗は、取得値が整数かつ非0で、一次失敗がまだ無い場合だけ採用する。Noneは非0終了とせず、回収の事実として残す。
- **#2 — 修正。** 無関係な窓・消えた窓の所有者取得失敗は、そのPIDの検査失敗にしない。所有PIDに一致した窓の読取失敗だけを記録する。列挙全体が失敗した場合は所有PIDの検査完了を証明できないので scan_failed を維持する。待機中は scan_failed だけで打ち切らず、終了またはtimeoutまで待つ。cleanup時の再検査が失敗すれば終了APIを呼ばず cleanup_pending とする。復旧ダイアログの停止条件は維持した。
- **#3 — 修正。** Popen直後の launch_finished は pending。所有PIDの ready 通知、またはCAD終了コードの取得後に確定行を追加する。readyも終了コードも無いまま停止した起動はpendingのままとし、全体の失敗と分ける。プロセスを作れなかった起動はfailedで記録する。
- **#4 — 修正。** 起動失敗の例外とCAD出力を既知Ruleに照合する。PATH → rule_path、ExecutionPolicy / execution policy / 実行ポリシー → rule_execution_policy、CIM → rule_cim。一致時はmessage_codeに固定トークンを入れ、stubもj1_skippedも発生させない。missing_executableも既知扱いを継続。不一致のlaunch失敗だけ無効stubとj1_skippedへ進む。出力の匿名化前に照合して保持するのはRule名だけであり、CIM実行や自動修正は追加していない。
- **#5 — 修正。** exit 2を維持し、output_root / invalid_timeout / build_required / private_input / parent_path / output_existsをmessage_codeまで保持する。一般のI/O・構文例外は例外型だけを残し、パスを含み得る例外本文は出さない。入力拒否のprobe_statusはnot_run。
- **#6 — 留保を継続。** 約700行の目安を超えるが、今回の追加は指摘された失敗境界と回帰確認に限る。停止条件やProbeを削って行数を合わせず、一般化・新しいCAD経路・自動再実行は追加しない。
- **#7 — 修正。** READMEの2文に、全述語true・CAD終了0・強制終了とtimeout無し、および所有ハンドル・GuiUp・窓0・復旧題名等で終了しない条件を明記した。計測説明の既存部分は維持した。
- **#8 — 修正。** cleanup_statusは終了済みならexited、未回収ならcleanup_pendingに整理。強制終了の操作名はイベントのcleanup_actionに残す。cleanup_actionが強制終了を示す場合は、終了済みでもexit 0にしない。
- **#9 — 保留（指示どおり）。** Pad/Pocket TypeのLength / 0の許容を変更していない。PHASE 3の実読取後に判断する。Probeとfixtureの形状処理は今回変更していない。

確認: 指定Pythonで python -B -m unittest tools.test_cad_run を実行し、11テスト成功。一次不適合＋保存/close/非0終了、一次ダイアログ＋worker結果、窓確認失敗後の自然終了待ち、timeout時の終了禁止、起動pendingと終了確定、既知Rule/未一致、入力理由をCADなしで確認した。CAD/FreeCADは起動していない。measure_rollout.py、既存reports/docs、CONSENSUS.mdは変更していない。実CADでの確認はPHASE 3に残る。
