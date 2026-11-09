"""Notebook helpers and bounded evidence tools. Core runs need no network or weights."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIONS = {"confirm", "no_target", "request_review"}
CHANNELS = {"imagery", "osm", "detector", "fcc"}


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def manifest():
    return load(ROOT / "data/challenge/manifest.json")


def check_id(sid):
    if sid not in {x["id"] for x in manifest()}:
        raise ValueError(f"Unknown candidate ID: {sid}")


def evidence(sid):
    check_id(sid)
    return load(ROOT / "data/challenge/evidence" / f"{sid}.json")


def validate_bundle():
    from PIL import Image
    records = manifest()
    assert len(records) == 60 and len({x['id'] for x in records}) == 60
    references = load(ROOT / "data/reference/labels.json")
    assert {x['id'] for x in references} == {x['id'] for x in records}
    ids = load(ROOT / "data/manual20/ids.json")
    assert len(ids) == len(set(ids)) == 20 and set(ids) <= {x['id'] for x in records}
    for row in records:
        p = ROOT / "data/challenge" / row['image']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256'], p
        with Image.open(p) as im:
            assert im.size == (row['width'], row['height'])
        ev = evidence(row['id'])
        assert all(c in ev for c in CHANNELS)
    return {"images": len(records), "manual_images": len(ids), "image_checksums": "passed",
            "mode": "offline classroom comparison; references supplied"}


def show_images(ids, reference=False, proposals=False, columns=3):
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    from PIL import Image
    rows = {x['id']: x for x in manifest()}
    refs = {x['id']: x for x in load(ROOT / "data/reference/labels.json")} if reference else {}
    fig, axes = plt.subplots(math.ceil(len(ids)/columns), columns,
                             figsize=(5*columns, 5*math.ceil(len(ids)/columns)), squeeze=False)
    for ax in axes.flat:
        ax.axis('off')
    for ax, sid in zip(axes.flat, ids):
        check_id(sid)
        with Image.open(ROOT / "data/challenge" / rows[sid]['image']) as im:
            ax.imshow(im)
        title = sid
        if reference:
            title += ' | ' + refs[sid]['status']
            for r in refs[sid]['regions']:
                b = r['shape_attributes']
                ax.add_patch(Rectangle((b['x'], b['y']), b['width'], b['height'], fill=False, edgecolor='lime', linewidth=2))
        if proposals:
            for r in evidence(sid)['detector']['detections'] or []:
                x, y, right, bottom = r['xyxy']
                ax.add_patch(Rectangle((x,y), right-x, bottom-y, fill=False, edgecolor='orange', linewidth=2))
                ax.text(x, y, f"{r['confidence']:.2f}", color='orange', backgroundcolor='black')
        ax.set_title(title)
    fig.tight_layout()
    return fig


def baseline(mode='detector'):
    """Illustrative fixed thresholds, not tuned or calibrated on these references."""
    if mode not in {'detector', 'evidence_rules'}:
        raise ValueError(mode)
    result = []
    for row in manifest():
        sid = row['id']
        ev = evidence(sid)
        det = ev['detector']
        conf = max([b['confidence'] for b in det['detections'] or []] or [0])
        action, reason = 'request_review', 'Weak, missing, or conflicting evidence.'
        if mode == 'detector':
            if det['available']:
                action = 'confirm' if conf >= .7 else 'no_target' if conf < .25 else 'request_review'
                reason = f'Cached detector maximum score {conf:.3f}; fixed 0.25/0.70 thresholds.'
            channels = ['detector']
        else:
            # OSM candidate tags are not independent proof. Excluded supports are conflicts.
            tags = ev['osm']['tags']
            excluded = tags.get('power') == 'tower' or tags.get('man_made') in {'water_tower', 'water_tank'} or tags.get('tower:type') == 'water'
            dated_match = any(m.get('distance_m', 1e9) <= 100
                              and m.get('constructed_date') and m.get('constructed_after_naip') is False
                              and not m.get('dismantled_date') for m in ev['fcc']['matches'] or [])
            if conf >= .7 and dated_match and not excluded:
                action, reason = 'confirm', 'High detector score and nearby temporally compatible FCC record; no excluded support tag.'
            channels = ['detector', 'osm', 'fcc']
        result.append({'id': sid, 'action': action, 'evidence_ids': [f'{sid}:{c}' for c in channels],
                       'reason': reason, 'method': mode})
    return result


def validate_predictions(records, require_all=True):
    known = {x['id'] for x in manifest()}
    seen = set()
    for row in records:
        sid = row.get('id')
        if sid not in known or sid in seen:
            raise ValueError(f'Unknown or duplicate prediction ID: {sid}')
        seen.add(sid)
        if row.get('action') not in ACTIONS or not isinstance(row.get('reason'), str) or not row['reason'].strip():
            raise ValueError(f'Invalid action/reason: {sid}')
        cites = row.get('evidence_ids')
        if not isinstance(cites, list) or not cites or any(c not in {f'{sid}:{k}' for k in CHANNELS} for c in cites):
            raise ValueError(f'Invalid evidence citations: {sid}')
    if require_all and seen != known:
        raise ValueError(f'Expected all 60 IDs; received {len(seen)}. Missing IDs are not negatives.')
    return records


def score(records, require_all=True):
    validate_predictions(records, require_all)
    refs = {x['id']: x for x in load(ROOT / 'data/reference/labels.json')}
    auto = [r for r in records if r['action'] != 'request_review']
    resolved_auto = [r for r in auto if refs[r['id']]['status'] != 'uncertain']
    wrong = [r for r in resolved_auto if (r['action'] == 'confirm') != (refs[r['id']]['status'] == 'positive')]
    return {'evaluated': len(records), 'automatic': len(auto), 'request_review': len(records)-len(auto),
            'coverage': len(auto)/len(records) if records else None,
            'resolved_automatic': len(resolved_auto), 'wrong_automatic': len(wrong),
            'false_confirms': sum(r['action']=='confirm' for r in wrong),
            'false_rejections': sum(r['action']=='no_target' for r in wrong),
            'selective_error': len(wrong)/len(resolved_auto) if resolved_auto else None,
            'unresolved_routing': dict(Counter(r['action'] for r in records if refs[r['id']]['status']=='uncertain'))}


def breakdown(records):
    import pandas as pd
    validate_predictions(records, require_all=False)
    refs = {x['id']: x for x in load(ROOT / 'data/reference/labels.json')}
    rows = [{**r, 'reference': refs[r['id']]['status'], 'sampling_group': refs[r['id']]['sampling_group']} for r in records]
    df = pd.DataFrame(rows)
    return pd.crosstab(df['reference'], df['action']).reindex(
        index=['positive','negative','uncertain'], columns=['confirm','no_target','request_review'], fill_value=0)


def import_manual(path):
    """Validate the page's VIA-compatible export; unfinished records stay unreviewed."""
    obj = load(path)
    valid = set(load(ROOT / 'data/manual20/ids.json'))
    out = []
    seen = set()
    dims = {x['id']: (x['width'], x['height']) for x in manifest()}
    for item in obj['_via_img_metadata'].values():
        attrs = item['file_attributes']
        sid, status = attrs.get('id'), attrs.get('status')
        if sid not in valid or sid in seen or status not in {'positive','negative','uncertain','unreviewed'}:
            raise ValueError('Invalid manual ID or status')
        seen.add(sid)
        regions = item.get('regions', [])
        if status == 'positive' and not regions or status == 'negative' and regions:
            raise ValueError(f'Boxes conflict with status: {sid}')
        for region in regions:
            b = region['shape_attributes']
            w, h = dims[sid]
            vals = [b[k] for k in ['x','y','width','height']]
            if b.get('name') != 'rect' or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vals):
                raise ValueError(f'Invalid box: {sid}')
            if min(b['x'],b['y']) < 0 or min(b['width'],b['height']) <= 0 or b['x']+b['width'] > w+.01 or b['y']+b['height'] > h+.01:
                raise ValueError(f'Box outside image: {sid}')
        out.append({'id': sid, 'status': status, 'boxes': len(regions), 'notes': attrs.get('notes','')})
    return out


def compare_manual(rows):
    import pandas as pd
    refs = {x['id']: x['status'] for x in load(ROOT / 'data/reference/labels.json')}
    return pd.DataFrame([{**r, 'supplied_reference': refs[r['id']],
                          'agrees': r['status']==refs[r['id']] if r['status'] != 'unreviewed' else None} for r in rows])


def main():
    parser = argparse.ArgumentParser(description='Read one cached evidence channel, logging observable tool use.')
    parser.add_argument('--id', required=True)
    parser.add_argument('--tool', choices=sorted(CHANNELS), required=True)
    parser.add_argument('--run', default='student_agent')
    args = parser.parse_args()
    if not args.run.replace('_','').replace('-','').isalnum():
        raise ValueError('Use a run name containing only letters, numbers, underscores or hyphens')
    ev = evidence(args.id)
    result = {'id': args.id, 'evidence_id': f'{args.id}:{args.tool}', 'cached': True, 'result': ev[args.tool]}
    if args.tool == 'imagery':
        result['result'] = {**result['result'], 'absolute_image_path': str(ROOT / 'data/challenge' / ev['imagery']['path'])}
    log = ROOT / 'runs' / args.run / 'tool_calls.jsonl'
    log.parent.mkdir(parents=True, exist_ok=True)
    calls = [json.loads(line) for line in log.read_text(encoding='utf-8').splitlines()] if log.exists() else []
    if sum(c['id']==args.id for c in calls) >= 5:
        raise SystemExit('Five-call budget exhausted for this image; request human review.')
    with log.open('a', encoding='utf-8') as f:
        f.write(json.dumps({**result, 'utc': datetime.now(timezone.utc).isoformat()})+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
