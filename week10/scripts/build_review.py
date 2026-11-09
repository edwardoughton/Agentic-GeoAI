"""Build a file://-compatible, offline labelling page with no reference answers."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    manifest = json.loads((ROOT / 'data/challenge/manifest.json').read_text())
    ids = json.loads((ROOT / 'data/manual20/ids.json').read_text())
    rows = []
    for sid in ids:
        m = next(x for x in manifest if x['id']==sid)
        rows.append({**m, 'image': '../data/challenge/'+m['image'],
                     'size': (ROOT/'data/challenge'/m['image']).stat().st_size,
                     'boxes': [], 'status': 'unreviewed', 'notes': ''})
    fingerprint = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()[:12]
    data = {'key': 'manual20-'+fingerprint, 'title': 'Your 20-image mission',
            'team': 'Team Agentic-GeoAI', 'filename': 'my_tower_labels.json', 'records': rows}
    template = (ROOT/'review/template.html').read_text(encoding='utf-8')
    output = ROOT/'review/manual20.html'
    output.write_text(template.replace('__LESSON_DATA__', json.dumps(data).replace('</','<\\/')),encoding='utf-8')
    return output


if __name__ == '__main__':
    print(build())
