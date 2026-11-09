"""Checks for consequential annotation/scoring edge cases, not model performance."""
import copy
import csv
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import lesson as lab


class LessonChecks(unittest.TestCase):
    def setUp(self):
        self.refs = {x['id']: x for x in lab.load(lab.ROOT/'data/reference/labels.json')}

    def test_bundle_integrity(self):
        self.assertEqual(lab.validate_bundle()['images'], 60)

    def test_csv_evidence_matches_agent_inputs(self):
        with (lab.ROOT/'data/tables/sites.csv').open(encoding='utf-8') as f:
            sites = list(csv.DictReader(f))
        with (lab.ROOT/'data/tables/fcc_matches.csv').open(encoding='utf-8') as f:
            matches = list(csv.DictReader(f))
        self.assertEqual({r['id'] for r in sites}, set(self.refs))
        for row in sites:
            ev = lab.evidence(row['id'])
            actual = [m for m in matches if m['id']==row['id']]
            self.assertEqual(row['fcc_available'], str(ev['fcc']['available']))
            self.assertEqual(len(actual), len(ev['fcc']['matches'] or []))
            self.assertEqual(int(row['fcc_match_count']), len(actual))
            for m in actual:
                self.assertLessEqual(float(m['distance_m']), 1000)

    def test_all_abstain_is_not_perfect_performance(self):
        rows = [{'id': sid, 'action': 'request_review', 'evidence_ids': [f'{sid}:imagery'], 'reason': 'Insufficient evidence.'} for sid in self.refs]
        result = lab.score(rows)
        self.assertEqual(result['coverage'], 0)
        self.assertIsNone(result['selective_error'])
        self.assertEqual(result['unresolved_routing'], {'request_review': 10})

    def test_uncertain_references_not_counted_as_binary_errors(self):
        rows = [{'id': sid, 'action': 'confirm', 'evidence_ids': [f'{sid}:imagery'], 'reason': 'Test decision.'} for sid in self.refs]
        result = lab.score(rows)
        self.assertEqual(result['resolved_automatic'], 50)
        self.assertEqual(result['false_confirms'], 20)
        self.assertEqual(result['selective_error'], .4)

    def test_missing_duplicate_and_unknown_citations_rejected(self):
        rows = lab.baseline()
        with self.assertRaises(ValueError):
            lab.score(rows[:-1])
        with self.assertRaises(ValueError):
            lab.score(rows[:-1]+[rows[0]])
        rows[0]['evidence_ids'] = ['invented-source']
        with self.assertRaises(ValueError):
            lab.score(rows)

    def test_unfinished_manual_export_and_invalid_negative_box(self):
        obj = lab.load(lab.ROOT/'data/manual20/starter_via.json')
        with patch.object(lab, 'load', side_effect=lambda p: obj if str(p)=='review.json' else json.loads(Path(p).read_text(encoding='utf-8'))):
            self.assertEqual(len(lab.import_manual('review.json')), 20)
            modified = copy.deepcopy(obj)
            row = next(iter(modified['_via_img_metadata'].values()))
            row['file_attributes']['status'] = 'negative'
            row['regions'] = [{'shape_attributes': {'name':'rect','x':1,'y':1,'width':10,'height':10}}]
        with patch.object(lab, 'load', side_effect=lambda p: modified if str(p)=='review.json' else json.loads(Path(p).read_text(encoding='utf-8'))):
            with self.assertRaises(ValueError):
                lab.import_manual('review.json')


if __name__ == '__main__':
    unittest.main()
