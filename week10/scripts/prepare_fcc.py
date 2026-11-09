"""Instructor-only: subset an already downloaded FCC ASR archive for the 60 sites.

Field positions follow the source project's ASR parser (RA/EN/CO tables).
No downloads, archive extraction, or changes to reference annotations.
"""
import argparse
from datetime import date, datetime
import hashlib
import io
import json
import math
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RADIUS_M = 1000


def prepare(archive, source_manifest):
    provenance = json.loads(source_manifest.read_text(encoding='utf-8'))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != provenance['archive_sha256']:
        raise ValueError('FCC archive does not match the recorded source hash')
    files = sorted((ROOT/'data/challenge/evidence').glob('*.json'))
    evidence = [json.loads(p.read_text(encoding='utf-8')) for p in files]
    for ev in evidence:
        if ev['imagery']['latitude'] is None or ev['imagery']['longitude'] is None:
            raise ValueError(f"Missing candidate coordinates: {ev['id']}")
    records, owners = {}, {}
    nearby = {ev['id']: [] for ev in evidence}
    with zipfile.ZipFile(archive) as z:
        def rows(name):
            with io.TextIOWrapper(z.open(name), encoding='utf-8', errors='replace') as f:
                for line in f:
                    yield line.rstrip('\r\n').split('|')
        for a in rows('RA.dat'):
            if a[0] != 'RA' or len(a) < 42:
                raise ValueError('Unexpected FCC registration schema')
            if a[1] == 'REG':
                records[a[4]] = dict(zip(
                    ['registration','unique_id','status_code','constructed_date','dismantled_date',
                     'action_date','city','state','county_fips','height_structure_m','overall_height_agl_m',
                     'structure_type_code','address'],
                    [a[i] for i in [3,4,8,12,13,14,24,25,26,28,30,32,23]]))
        for a in rows('EN.dat'):
            if len(a)>13 and a[1]=='REG' and a[5]=='O' and a[9] and not (a[10] or a[12]):
                owners[a[4]] = a[9]
        coordinate_rows = 0
        for a in rows('CO.dat'):
            if len(a)<15 or a[1]!='REG' or a[4] not in records:
                continue
            try:
                lat = (float(a[6])+float(a[7])/60+float(a[8])/3600)*(-1 if a[9]=='S' else 1)
                lon = (float(a[11])+float(a[12])/60+float(a[13])/3600)*(-1 if a[14]=='W' else 1)
            except ValueError:
                continue
            if not (-90<=lat<=90 and -180<=lon<=180):
                continue
            coordinate_rows += 1
            for ev in evidence:
                slat, slon = float(ev['imagery']['latitude']), float(ev['imagery']['longitude'])
                if abs(lat-slat) > .01:
                    continue
                dlat, dlon = math.radians(lat-slat), math.radians(lon-slon)
                hav = math.sin(dlat/2)**2 + math.cos(math.radians(lat))*math.cos(math.radians(slat))*math.sin(dlon/2)**2
                distance = 2*6371008.8*math.asin(min(1,math.sqrt(hav)))
                if distance > RADIUS_M:
                    continue
                match = {**records[a[4]], 'latitude':lat,'longitude':lon,
                         'coordinate_type_code':a[5], 'organization_owner':owners.get(a[4],''),
                         'fcc_url':'https://wireless2.fcc.gov/UlsApp/AsrSearch/asrRegistration.jsp?regKey='+a[4],
                         'distance_m':round(distance,1),
                         'spatial_relation':'within 100 m; possible site match' if distance<=100 else 'within 1 km; may be another structure',
                         'constructed_after_naip':None}
                try:
                    match['constructed_after_naip'] = datetime.strptime(match['constructed_date'],'%m/%d/%Y').date() > date.fromisoformat(ev['imagery']['date'][:10])
                except (ValueError,TypeError):
                    pass
                nearby[ev['id']].append(match)
    if len(records) != provenance['rows_registration'] or coordinate_rows != provenance['coordinate_rows']:
        raise ValueError('Parsed row counts differ from the recorded source manifest')
    for p, ev in zip(files,evidence):
        matches = sorted(nearby[ev['id']], key=lambda x:(x['distance_m'],x['unique_id'],x['coordinate_type_code']))
        ev['fcc'] = {'available':True,'matches':matches,'search_radius_m':RADIUS_M,
                     'source_manifest':'data/tables/fcc_source_manifest.json',
                     'caution':'Registration does not establish cellular use. No nearby registered structure does not establish absence. Dates/status are as filed.'}
        p.write_text(json.dumps(ev,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    out = ROOT/'data/tables/fcc_source_manifest.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({**provenance,'classroom_prepared_date':'2026-11-09',
                   'query':'All REG coordinate records within 1000 m of each candidate; approximate spherical distances, NAD83/WGS84 not transformed.',
                   'candidate_count':len(evidence),'match_rows':sum(map(len,nearby.values()))},indent=2)+'\n',encoding='utf-8')
    print(f'Prepared FCC searches for {len(evidence)} candidates from the existing verified archive.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',required=True,type=Path)
    parser.add_argument('--source-manifest',required=True,type=Path)
    args=parser.parse_args()
    prepare(args.archive,args.source_manifest)
