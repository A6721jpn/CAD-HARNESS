"""Whitelist-only public projections and partial-H0 summaries; no input-file reads."""

from __future__ import annotations

from collections.abc import Mapping
import math
from pathlib import Path
import re


_GROUPS = frozenset(('dev', 'legacy', 'mvp', 'geometry', 'q', 'completion', 'fault'))
_ROUTES = frozenset(('source', 'spec', 'ask', 'completion', 'offline', 'mvp'))
_CODE = re.compile(r'[A-Za-z][A-Za-z0-9_]{0,95}')
_SHA256 = re.compile(r'[A-Fa-f0-9]{64}')
_PRIVATE = 'PRIVATE_DETAIL_RETAINED'
_SCOPE_CAP = 40
_ORIGINAL_ROWS = 60


def _mapping(value):
    if not isinstance(value, Mapping):
        raise ValueError('invalid_public_mapping')
    return value


def _metadata(value, ordinal_key):
    value = _mapping(value)
    sequence = value.get(ordinal_key)
    group, route = value.get('group'), value.get('route')
    if type(sequence) is not int or not 1 <= sequence <= _ORIGINAL_ROWS:
        raise ValueError('invalid_public_sequence')
    if type(group) is not str or group not in _GROUPS:
        raise ValueError('invalid_public_group')
    if type(route) is not str or route not in _ROUTES:
        raise ValueError('invalid_public_route')
    return dict(sequence=sequence, group=group, route=route)


def _count(value):
    if type(value) is not int or value < 0:
        raise ValueError('invalid_public_count')
    return value


def _boolean(value):
    if type(value) is not bool:
        raise ValueError('invalid_public_boolean')
    return value


def _gate(value):
    return value if type(value) is bool else None


def _number(value, *, nonnegative=False):
    if type(value) not in (int, float):
        return None
    if type(value) is float and not math.isfinite(value):
        return None
    if nonnegative and value < 0:
        return None
    return value


def safe_code(value):
    if value is None:
        return None
    if type(value) is str and _CODE.fullmatch(value) is not None:
        return value
    return _PRIVATE


def _selected_row(value):
    value = _mapping(value)
    result = _metadata(value, 'sequence')
    if value.get('selected') is not True:
        raise ValueError('invalid_selected_row')
    result.update(
        selected=True,
        completed=_boolean(value.get('completed', False)),
        passed=_boolean(value.get('passed', False)) and value.get('completed') is True,
        geometry=_gate(value.get('geometry')),
        editability=_gate(value.get('editability')),
        reimport=_gate(value.get('reimport')),
        q_score=_number(value.get('q_score')),
        critical_invention=_boolean(value.get('critical_invention', False)),
        model_calls=_count(value.get('model_calls')),
        cad_attempts=_count(value.get('cad_attempts')),
        parse_repairs=_count(value.get('parse_repairs')),
        repair_calls=_count(value.get('repair_calls')),
        wall_s=_number(value.get('wall_s'), nonnegative=True),
        active_s=_number(value.get('active_s'), nonnegative=True),
        failure_class=safe_code(value.get('failure_class')),
    )
    return result


def row(entry, report, scored, *, wall_s, active_s, model_calls):
    """Project one selected episode without copying producer payloads or IDs.

    Counters must be supplied as nonnegative integers. Unknown scores, gates and
    times remain null; a selected but unfinished episode stays incomplete.
    """
    metadata = _metadata(entry, 'sequence')
    report, scored = _mapping(report), _mapping(scored)
    final = scored.get('final')
    if not isinstance(final, Mapping):
        final = {}
    return _selected_row(dict(
        **metadata,
        selected=True,
        completed=scored.get('completed', False),
        passed=scored.get('passed', False),
        geometry=final.get('geometry'),
        editability=final.get('editability'),
        reimport=final.get('reimport'),
        q_score=scored.get('q_score'),
        critical_invention=scored.get('critical_invention', False),
        model_calls=model_calls,
        cad_attempts=report.get('cad_attempts'),
        parse_repairs=report.get('parse_repairs'),
        repair_calls=report.get('repair_calls'),
        wall_s=wall_s,
        active_s=active_s,
        failure_class=scored.get('failure_class'),
    ))


def complete_rows(entries, selected_rows):
    """Return all 60 ordinals, retaining planned selection on unstarted rows."""
    metadata, planned = {}, {}
    for entry in entries:
        public = _metadata(entry, 'sequence')
        sequence = public['sequence']
        if sequence in metadata:
            raise ValueError('duplicate_public_sequence')
        metadata[sequence] = public
        planned[sequence] = _boolean(entry.get('selected', False))
    if len(metadata) != _ORIGINAL_ROWS:
        raise ValueError('incomplete_original_order')

    selected = {}
    for value in selected_rows:
        public = _selected_row(value)
        sequence = public['sequence']
        if sequence in selected:
            raise ValueError('duplicate_selected_sequence')
        original = metadata[sequence]
        if public['group'] != original['group'] or public['route'] != original['route']:
            raise ValueError('selected_metadata_mismatch')
        selected[sequence] = public

    return [
        selected[sequence] if sequence in selected else dict(
            **metadata[sequence], selected=planned[sequence], completed=False,
            passed=None, status='not_run',
        )
        for sequence in range(1, _ORIGINAL_ROWS + 1)
    ]


def _summary_rows(rows):
    entries, selected = [], []
    for value in rows:
        public = _metadata(value, 'sequence')
        planned = _boolean(value.get('selected'))
        entries.append(dict(
            sequence=public['sequence'], group=public['group'],
            route=public['route'], selected=planned,
        ))
        if value.get('status') == 'not_run':
            if value.get('completed') is not False or value.get('passed') is not None:
                raise ValueError('invalid_not_run_row')
        elif planned:
            selected.append(value)
        else:
            raise ValueError('invalid_not_run_row')
    return complete_rows(entries, selected)


def _cell(value):
    if value is None:
        return '不明'
    if type(value) is bool:
        return 'PASS' if value else 'FAIL'
    return str(value)


def write_summary(path, rows, accounting, *, manifest_sha256, stopped_reason=None):
    """Write the exact caller-supplied output path, using only public fields.

    Pass complete_rows(...) even after a stopped run. Accounting is read only at
    conservative_reserved_calls; unrelated producer data is never serialized.
    """
    public = _summary_rows(rows)
    accounting = _mapping(accounting)
    reserved = accounting.get('conservative_reserved_calls')
    if reserved is not None:
        reserved = _count(reserved)
    if type(manifest_sha256) is not str or _SHA256.fullmatch(manifest_sha256) is None:
        raise ValueError('invalid_manifest_sha256')

    selected = [value for value in public if value['selected']]
    completed = [value for value in selected if value['completed']]
    passed = sum(value['passed'] for value in completed)
    failures = len(completed) - passed
    unstarted = sum(value.get('status') == 'not_run' for value in selected)
    state = '部分実行・停止' if stopped_reason is not None else '部分H0の公開集計'
    lines = [
        '# SolidWorks版 Harness2 H0 結果', '',
        '## 結論', '',
        f'- 状態: {state}。',
        f'- 選択 {len(selected)}/60行、完了 {len(completed)}/{len(selected)}選択行、'
        f'未完了 {len(selected) - len(completed)}行（うち未着手 {unstarted}行）、'
        f'非選択 {60 - len(selected)}行。',
        f'- 合格 {passed}/{len(completed)}完了行、不合格 {failures}/{len(completed)}完了行。',
        '- 未実行・未完了行は成功にも失敗にも加算しない。',
        '', '## 判定の扱いと限界', '',
        '- これは部分H0の集計であり、元60題のスコアでも全60題の合格確認でもない。',
        '- 供給された公開判定のみを集計する。実CAD・実モデルのライブ実行成立は、'
        'この要約だけでは主張しない（停止・模擬実行を成功実行と扱わない）。',
    ]
    for key, label in (('geometry', '幾何'), ('editability', '編集性'), ('reimport', '再読込')):
        true_count = sum(value[key] is True for value in completed)
        false_count = sum(value[key] is False for value in completed)
        unknown_count = len(completed) - true_count - false_count
        lines.append(f'- {label}（完了行のみ）: PASS {true_count}、FAIL {false_count}、不明 {unknown_count}。')
    inventions = sum(value['critical_invention'] for value in completed)
    lines.extend([
        f'- 重大な発明判定あり（完了行のみ）: {inventions}行。',
        f'- マニフェスト SHA-256: `{manifest_sha256.lower()}`',
        '', '## 時間と呼出し会計', '',
        '- H0スコープのモデル呼出し上限: 40回。',
        f'- 保守的計上（conservative_reserved_calls、予約を含む）: {_cell(reserved)}回 / {_SCOPE_CAP}回。',
        '- 価格・費用: 不明。単価が不明のため金額を算出しない。',
        '- 各行の呼出し数と wall_s / active_s は供給値。不明値を0に置換しない。',
        '- 停止理由: ' + ('なし（停止理由の指定なし）' if stopped_reason is None else safe_code(stopped_reason)),
        '', '## 全60行', '',
        '序数は元順序。not_run は未着手（選択予定行を含む）、incomplete は着手済み未完了。'
        'passed / failed は完了した選択行だけの判定。', '',
        '| 序数 | 区分 | 経路 | 選択 | 状態 | モデル | CAD | parse修復 | repair | wall_s | active_s | 幾何 | 編集性 | 再読込 | Q | 重大発明 | 失敗分類 |',
        '|---:|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|---|---|',
    ])
    columns = ('model_calls', 'cad_attempts', 'parse_repairs', 'repair_calls',
               'wall_s', 'active_s', 'geometry', 'editability', 'reimport',
               'q_score', 'critical_invention', 'failure_class')
    for value in public:
        if value.get('status') == 'not_run':
            status = 'not_run'
        elif not value['completed']:
            status = 'incomplete'
        else:
            status = 'passed' if value['passed'] else 'failed'
        cells = [str(value['sequence']), value['group'], value['route'],
                 'yes' if value['selected'] else 'no', status]
        cells.extend(_cell(value.get(key)) for key in columns)
        lines.append('| ' + ' | '.join(cells) + ' |')
    lines.extend([
        '', '## 安全性・保存先', '',
        '- このファイルには公開メタデータ・判定・呼出し数・時間だけを投影する。'
        '原要求、生成応答、gold、寸法、任意のエラー詳細は転記しない。',
        '',
    ])
    Path(path).write_text('\n'.join(lines), encoding='utf-8')
