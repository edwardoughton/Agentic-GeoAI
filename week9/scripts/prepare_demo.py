"""Validate the bundled 50 train / 10 validation / 50 test dataset and rebase YAML."""
from pathlib import Path
import argparse
import hashlib
import json
import math


def find_root(start=None):
    start = Path(start or Path.cwd()).resolve()
    for candidate in (start, *start.parents):
        for root in (candidate, candidate / 'week9'):
            if (root / 'scripts/prepare_demo.py').is_file() and (root / 'data/demo100/manifest.json').is_file():
                return root
    raise FileNotFoundError('Cannot find week9. Launch from the repository, week9, or notebooks directory.')


def prepare(root=None, seed=662):
    root = find_root(root)
    destination = root / 'data/demo100'
    manifest = json.loads((destination / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['seed'] != seed:
        raise ValueError('Dataset seed differs from requested seed')
    records = manifest['records']
    parents = {}
    for split, count in [('train', 50), ('val', 10), ('test', 50)]:
        selected = [r for r in records if r['split'] == split]
        if len(selected) != count:
            raise ValueError(f'Expected {count} records for {split}')
        parents[split] = {r['parent_scene'] for r in selected}
        for kind, extension in [('images', '*.jpg'), ('labels', '*.txt')]:
            expected = {(destination / r[kind]).resolve() for r in selected}
            actual = {p.resolve() for p in (destination / kind / split).glob(extension)}
            if actual != expected:
                raise ValueError(f'{split} {kind} differ from manifest')
            for r in selected:
                path = (destination / r[kind]).resolve()
                if not path.is_relative_to(destination.resolve()):
                    raise ValueError('Manifest path leaves dataset directory')
                if hashlib.sha256(path.read_bytes()).hexdigest() != r[kind + '_sha256']:
                    raise ValueError(f'Checksum mismatch: {path}')
        for r in selected:
            for line in (destination / r['labels']).read_text().splitlines():
                values = list(map(float, line.split()))
                if len(values) != 5 or values[0] != 0 or not all(math.isfinite(v) for v in values):
                    raise ValueError(f'Invalid annotation: {r["labels"]}')
                _, x, y, w, h = values
                if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                    raise ValueError(f'Invalid box: {r["labels"]}')
    if len(records) != 110 or any(parents[a] & parents[b] for a, b in [('train','val'), ('train','test'), ('val','test')]):
        raise ValueError('Unexpected records or overlapping parent scenes')
    yaml = ('path: ' + json.dumps(destination.as_posix()) +
            '\ntrain: images/train\nval: images/val\ntest: images/test\nnames:\n  0: tower\n')
    (destination / 'data.yaml').write_text(yaml, encoding='utf-8')
    return destination


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(prepare(args.root))
