"""Flatten bundled evidence into classroom CSVs; no downloads or source lookups."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def write_csv(path, rows, fields):
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build():
    out = ROOT / 'data/tables'
    out.mkdir(parents=True, exist_ok=True)
    sites, osm, matches = [], [], []
    for path in sorted((ROOT / 'data/challenge/evidence').glob('*.json')):
        ev = json.loads(path.read_text(encoding='utf-8'))
        sid, im, fcc = ev['id'], ev['imagery'], ev['fcc']
        tags = ev['osm']['tags']
        sites.append({'id': sid, 'latitude': im['latitude'], 'longitude': im['longitude'],
                      'imagery_date': im['date'], 'resolution_m': im['resolution_m'],
                      'fcc_available': fcc['available'],
                      'fcc_match_count': len(fcc['matches'] or []) if fcc['available'] else None,
                      'fcc_search_radius_m': fcc['search_radius_m'],
                      'fcc_status': 'matches_found' if fcc['matches'] else 'no_matches_in_cached_search' if fcc['available'] else 'not_retrieved',
                      'osm_tags_available': bool(tags)})
        osm.append({'id': sid, 'snapshot': ev['osm']['snapshot'], 'osm_url': ev['osm']['url'],
                    'man_made': tags.get('man_made'), 'tower_type': tags.get('tower:type'),
                    'mobile_phone': tags.get('communication:mobile_phone'), 'power': tags.get('power'),
                    'operator': tags.get('operator'), 'tags_json': json.dumps(tags, sort_keys=True)})
        for match in fcc['matches'] or []:
            matches.append({'id': sid, **match})
    write_csv(out/'sites.csv', sites, list(sites[0]))
    write_csv(out/'osm_candidates.csv', osm, list(osm[0]))
    fields = ['id'] + sorted(set().union(*(x.keys() for x in matches)) - {'id'})
    write_csv(out/'fcc_matches.csv', matches, fields)
    return {'sites': len(sites), 'osm_rows': len(osm), 'fcc_match_rows': len(matches),
            'fcc_cached_sites': sum(s['fcc_available'] for s in sites),
            'fcc_not_retrieved_sites': sum(not s['fcc_available'] for s in sites)}


if __name__ == '__main__':
    print(build())
