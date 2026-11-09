"""Offline two-agent handoffs and conservative human-review routing.

No model calls or reference labels: run each packet in a fresh assistant session.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from scripts import lesson as lab

TARGET = ('Label freestanding cell-tower ground sites. Exclude water towers, '
          'electrical pylons and rooftop supports, even with antennas. Inspect the whole chip.')


def prepare(run, ids=None):
    run = Path(run)
    if run.exists():
        raise ValueError('Use a new run directory; existing runs are preserved.')
    rows = lab.manifest()
    if ids is not None:
        if not ids or len(ids) != len(set(ids)):
            raise ValueError('Provide distinct candidate IDs.')
        for sid in ids:
            lab.check_id(sid)
        rows = [r for r in rows if r['id'] in ids]
    packets = {'investigator': [], 'reviewer': []}
    for row in rows:
        sid = row['id']
        neutral = {k: row[k] for k in ('id', 'width', 'height', 'sha256')}
        neutral['image_path'] = str((lab.ROOT / 'data/challenge' / row['image']).resolve())
        packets['reviewer'].append(neutral)
        packets['investigator'].append({**neutral, 'evidence': lab.evidence(sid)})
    for role, records in packets.items():
        lab.save(run / role / 'packet.json', records)
        instruction = ("Use imagery and cached detector, OSM and FCC evidence. Reconcile spatial/date "
                       "conflicts; missing records are not negative evidence. Cite inspected channels."
                       if role == 'investigator' else
                       "Classify directly from the image only. Do not request or output a reasoning "
                       "trace. Do not read investigator outputs, metadata evidence, or references. "
                       "Return a label, confidence and brief visible observation only. If your model "
                       "supports disabling reasoning, disable it in the host configuration.")
        (run / role / 'TASK.md').write_text(
            f'# {role.title()}\n\n{TARGET}\n\n{instruction}\n\n'
            'Use a fresh session. Only read this packet and its image files; actually view each image. '
            'Never read data/reference, reference_results, or student labels. '
            'If you cannot view an image, abstain and set image_quality to poor. '
            'Confidence is an uncalibrated self-report, not a probability.\n\n'
            'Save a JSON array as decisions.json in this directory, one row per packet ID:\n\n'
            '```json\n[{"id":"site_001","action":"request_review","confidence":0.0,'
            '"image_quality":"poor","evidence_ids":["site_001:imagery"],'
            '"reason":"Image could not be inspected."}]\n```\n\n'
            'Actions: confirm, no_target, request_review. image_quality: adequate or poor. '
            'For reviewer, reason means a short visible observation, not a rationale. '
            'Cite imagery and only channels you inspected. Reviewer may cite imagery only.\n',
            encoding='utf-8')
    lab.save(run / 'policy.json', {'ids': [r['id'] for r in rows], 'target': TARGET,
                                 'mode': 'independent offline assistant handoffs'})
    return run


def validate(rows, ids, reviewer=False):
    lab.validate_predictions(rows, require_all=False)
    if {r['id'] for r in rows} != set(ids):
        raise ValueError('Each agent must return exactly the packet IDs; omissions are not negatives.')
    for r in rows:
        c = r.get('confidence')
        if isinstance(c, bool) or not isinstance(c, (float, int)) or not math.isfinite(c) or not 0 <= c <= 1:
            raise ValueError('Confidence must be a finite number from zero to one.')
        if r.get('image_quality') not in {'adequate', 'poor'}:
            raise ValueError('image_quality must be adequate or poor.')
        if f"{r['id']}:imagery" not in r['evidence_ids']:
            raise ValueError('Both agents must inspect imagery.')
        if reviewer and r['evidence_ids'] != [f"{r['id']}:imagery"]:
            raise ValueError('Reviewer must use imagery only.')
    return {r['id']: r for r in rows}


def finalize(run, threshold=0.85):
    run = Path(run)
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('Threshold must be between zero and one.')
    policy = lab.load(run / 'policy.json')
    ids = policy['ids']
    agents = [validate(lab.load(run / role / 'decisions.json'), ids, role == 'reviewer')
              for role in ('investigator', 'reviewer')]
    predictions, queue = [], []
    for sid in ids:
        a, b = (agent[sid] for agent in agents)
        reasons = []
        if a['action'] != b['action']:
            reasons.append('agent_disagreement')
        if any(r['action'] == 'request_review' for r in (a, b)):
            reasons.append('agent_abstention')
        if min(a['confidence'], b['confidence']) < threshold:
            reasons.append('low_confidence')
        if any(r['image_quality'] == 'poor' for r in (a, b)):
            reasons.append('poor_imagery')
        action = 'request_review' if reasons else a['action']
        predictions.append({'id': sid, 'action': action,
                            'evidence_ids': sorted(set(a['evidence_ids'] + b['evidence_ids'])),
                            'reason': ', '.join(reasons) if reasons else 'Independent agents agree above the routing threshold.',
                            'investigator': a, 'reviewer': b})
        if reasons:
            queue.append({'id': sid, 'routing_reasons': reasons, 'investigator': a, 'reviewer': b})
    # All inputs validated before writing any outputs.
    lab.save(run / 'predictions.json', predictions)
    lab.save(run / 'human_review.json', queue)
    lab.save(run / 'summary.json', {'total': len(ids), 'provisionally_accepted': len(ids)-len(queue),
                                  'human_review': len(queue), 'threshold': threshold,
                                  'confidence_calibrated': False,
                                  'input_sha256': {role: hashlib.sha256((run / role / 'decisions.json').read_bytes()).hexdigest()
                                                   for role in ('investigator', 'reviewer')}})
    if queue:
        import os
        manifest = {r['id']: r for r in lab.manifest()}
        records = []
        for q in queue:
            m = manifest[q['id']]
            image = lab.ROOT / 'data/challenge' / m['image']
            records.append({**m, 'image': os.path.relpath(image, run).replace('\\', '/'),
                            'size': image.stat().st_size, 'boxes': [], 'status': 'unreviewed',
                            'notes': ', '.join(q['routing_reasons'])})
        data = {'key': 'two-agent-' + hashlib.sha256(json.dumps(predictions, sort_keys=True).encode()).hexdigest()[:16],
                'title': 'Uncertain cases: human review', 'filename': 'human_tower_labels.json', 'records': records}
        template = (lab.ROOT / 'review/template.html').read_text(encoding='utf-8')
        (run / 'human_review.html').write_text(template.replace('__LESSON_DATA__', json.dumps(data).replace('</', '<\\/')), encoding='utf-8')
    elif (run / 'human_review.html').exists():
        (run / 'human_review.html').unlink()
    return predictions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['prepare', 'finalize'])
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--ids', nargs='+')
    parser.add_argument('--threshold', type=float, default=.85)
    args = parser.parse_args()
    if args.stage == 'prepare':
        print(prepare(args.run, args.ids))
    else:
        finalize(args.run, args.threshold)
        print(json.dumps(lab.load(args.run / 'summary.json'), indent=2))


if __name__ == '__main__':
    main()
