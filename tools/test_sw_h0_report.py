"""Synthetic-only regression coverage for the public H0 projection boundary."""

import json
from pathlib import Path
import tempfile
import unittest

from tools.sw_h0_report import complete_rows, row, write_summary


class H0PublicReportTests(unittest.TestCase):
    def entries(self):
        # Synthetic metadata only; no requests, private fixtures or input reads.
        return [dict(sequence=i, group='q', route='spec', selected=i <= 2)
                for i in range(1, 61)]

    def selected_row(self, *, completed=True, passed=False):
        secret = 'SYNTHETIC_PRIVATE_PAYLOAD_<not-public>'
        entry = dict(self.entries()[0], id=secret, source=secret,
                     gold={'expected_dimensions': [987654.125]})
        report = dict(cad_attempts=2, parse_repairs=1, repair_calls=0,
                      first_response=secret, gold=secret,
                      expected_dimensions=[987654.125], error={'detail': secret})
        scored = dict(
            completed=completed, passed=passed, q_score=0.5,
            critical_invention=False,
            final=dict(geometry=True, editability=None, reimport=False,
                       measurements={'expected': 987654.125}, gold=secret),
            failure_class={'error': {'detail': secret, 'expected': 987654.125}},
            first_response=secret,
        )
        return row(entry, report, scored, wall_s=2.25, active_s=None, model_calls=1)

    def test_raw_payloads_are_not_projected_or_written(self):
        public = self.selected_row()
        self.assertEqual(set(public), {
            'sequence', 'group', 'route', 'selected', 'completed', 'passed',
            'geometry', 'editability', 'reimport', 'q_score',
            'critical_invention', 'model_calls', 'cad_attempts', 'parse_repairs',
            'repair_calls', 'wall_s', 'active_s', 'failure_class',
        })
        self.assertEqual(public['failure_class'], 'PRIVATE_DETAIL_RETAINED')
        self.assertIsNone(public['editability'])
        self.assertIsNone(public['active_s'])
        # Even accidental extra producer fields at subsequent boundaries vanish.
        public['gold'] = {'expected_dimensions': [987654.125]}
        public['first_response'] = 'SYNTHETIC_PRIVATE_PAYLOAD_<not-public>'
        rows = complete_rows(self.entries(), [public])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.md'
            write_summary(
                path, rows,
                {'conservative_reserved_calls': 3,
                 'error': {'detail': 'SYNTHETIC_PRIVATE_PAYLOAD_<not-public>'}},
                manifest_sha256='a' * 64,
                stopped_reason={'error': 'SYNTHETIC_PRIVATE_PAYLOAD_<not-public>'},
            )
            markdown = path.read_text(encoding='utf-8')
        serialized = json.dumps(rows) + markdown
        for private in ('SYNTHETIC_PRIVATE_PAYLOAD', '987654.125',
                        'expected_dimensions', 'first_response'):
            self.assertNotIn(private, serialized)

    def test_unstarted_selection_survives_without_fabricated_counts(self):
        public = self.selected_row(completed=False, passed=True)
        self.assertFalse(public['passed'])
        rows = complete_rows(reversed(self.entries()), [public])
        self.assertEqual([value['sequence'] for value in rows], list(range(1, 61)))
        self.assertEqual(rows[0], public)
        self.assertEqual(rows[1], dict(sequence=2, group='q', route='spec',
                                      selected=True, completed=False,
                                      passed=None, status='not_run'))
        self.assertEqual(rows[2], dict(sequence=3, group='q', route='spec',
                                      selected=False, completed=False,
                                      passed=None, status='not_run'))

    def test_invalid_metadata_is_rejected_without_echoing_values(self):
        report = dict(cad_attempts=0, parse_repairs=0, repair_calls=0)
        for key, value in (('sequence', True), ('sequence', 61),
                           ('group', {'private': 'SYNTHETIC_SECRET'}),
                           ('group', 'independent_dev'), ('route', 'SYNTHETIC_SECRET')):
            entry = dict(self.entries()[0])
            entry[key] = value
            with self.subTest(key=key, value=value):
                with self.assertRaisesRegex(ValueError, '^invalid_public_') as caught:
                    row(entry, report, {}, wall_s=None, active_s=None, model_calls=0)
                self.assertNotIn('SYNTHETIC_SECRET', str(caught.exception))

    def test_failure_codes_and_unknown_numbers_are_sanitized(self):
        report = dict(cad_attempts=0, parse_repairs=0, repair_calls=0)
        for code in ({'nested': 'SYNTHETIC_SECRET'}, 'bad detail', '1CODE',
                     'A' * 97, 'VALID\n'):
            public = row(self.entries()[0], report,
                         {'failure_class': code, 'q_score': float('nan'),
                          'final': {'geometry': {'private': 'SYNTHETIC_SECRET'}}},
                         wall_s=float('inf'), active_s=-1, model_calls=0)
            self.assertEqual(public['failure_class'], 'PRIVATE_DETAIL_RETAINED')
            for key in ('q_score', 'geometry', 'wall_s', 'active_s'):
                self.assertIsNone(public[key])
        public = row(self.entries()[0], report, {'failure_class': 'SW_Error9'},
                     wall_s=None, active_s=None, model_calls=0)
        self.assertEqual(public['failure_class'], 'SW_Error9')
        public = row(self.entries()[0], report, {'failure_class': None},
                     wall_s=None, active_s=None, model_calls=0)
        self.assertIsNone(public['failure_class'])


if __name__ == '__main__':
    unittest.main()
