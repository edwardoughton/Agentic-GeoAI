"""Check blind handoffs and consequential routing failures without a model API."""
import json
from pathlib import Path
import sys
import shutil
import uuid
from contextlib import contextmanager
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import two_agent as flow
from scripts import lesson as lab


@contextmanager
def workspace_temp():
    root = (lab.ROOT / 'runs').resolve()
    path = root / ('test-' + uuid.uuid4().hex)
    path.mkdir()
    try:
        yield path
    finally:
        if path.resolve().parent != root:
            raise ValueError('Test cleanup must stay within runs')
        shutil.rmtree(path)


class TwoAgentChecks(unittest.TestCase):
    def setUp(self):
        (lab.ROOT / 'runs').mkdir(exist_ok=True)

    def test_blind_packet_and_routing(self):
        with workspace_temp() as tmp:
            run = flow.prepare(Path(tmp) / 'run', ['site_001', 'site_002'])
            packet = lab.load(run / 'reviewer/packet.json')
            self.assertEqual(set(packet[0]), {'id', 'width', 'height', 'sha256', 'image_path'})
            rows = [{'id': sid, 'action': 'confirm', 'confidence': .95,
                     'image_quality': 'adequate', 'evidence_ids': [sid+':imagery'],
                     'reason': 'Visible tower.'} for sid in ('site_001', 'site_002')]
            lab.save(run / 'investigator/decisions.json', rows)
            rows[1]['action'] = 'no_target'
            lab.save(run / 'reviewer/decisions.json', rows)
            result = flow.finalize(run)
            self.assertEqual([r['action'] for r in result], ['confirm', 'request_review'])
            self.assertEqual(lab.load(run / 'human_review.json')[0]['routing_reasons'], ['agent_disagreement'])
            self.assertTrue((run / 'human_review.html').exists())
            rows[1]['action'] = 'confirm'
            lab.save(run / 'reviewer/decisions.json', rows)
            flow.finalize(run)
            self.assertFalse((run / 'human_review.html').exists())

    def test_invalid_or_incomplete_decisions_fail_closed(self):
        row = {'id': 'site_001', 'action': 'confirm', 'confidence': .95,
               'image_quality': 'adequate', 'evidence_ids': ['site_001:imagery'], 'reason': 'Visible tower.'}
        with self.assertRaises(ValueError):
            flow.validate([row], ['site_001', 'site_002'])
        for value in (True, float('nan'), -1, 1.1):
            with self.assertRaises(ValueError):
                flow.validate([{**row, 'confidence': value}], ['site_001'])
        with self.assertRaises(ValueError):
            flow.validate([{**row, 'evidence_ids': ['site_001:imagery', 'site_001:osm']}], ['site_001'], True)

    def test_agreement_still_routes_uncertainty(self):
        for changes in ({'confidence': .5}, {'image_quality': 'poor'}, {'action': 'request_review'}):
            with self.subTest(changes=changes), workspace_temp() as tmp:
                run = flow.prepare(Path(tmp) / 'run', ['site_001'])
                row = {'id': 'site_001', 'action': 'no_target', 'confidence': .95,
                       'image_quality': 'adequate', 'evidence_ids': ['site_001:imagery'],
                       'reason': 'Observation.', **changes}
                for role in ('investigator', 'reviewer'):
                    lab.save(run / role / 'decisions.json', [row])
                self.assertEqual(flow.finalize(run)[0]['action'], 'request_review')


if __name__ == '__main__':
    unittest.main()
