"""Instructor-only: package reviewed source images; no downloads or model training."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(source: Path):
    master = read(source / "master_dataset/master_annotations.json")
    evidence = {}
    for p in sorted(source.glob("evidence_review*/evidence.json")):
        evidence.update(read(p))
    predictions = {}
    for relative in ["assisted_annotation_v3/batch3_raw_predictions.json",
                     "assisted_annotation_v4/batch4_raw_predictions.json"]:
        for name, boxes in read(source / relative).items():
            predictions[name] = (boxes, relative)
    with (source / "experiment_review_index.csv").open(encoding="utf-8-sig") as f:
        metadata = {x["sample_id"]: x for x in csv.DictReader(f)}
    with (source / "assisted_annotation_v4/training_manifest.csv").open(encoding="utf-8-sig") as f:
        membership = {x["name"]: x["split"] for x in csv.DictReader(f)}
    eligible = [x for x in master["images"] if x.get("label_quality") == "user_reviewed"
                and x.get("review_status") in {"positive", "negative", "uncertain"}
                and Path(x.get("image_path", "")).is_file()]
    rng = random.Random(66210)
    rng.shuffle(eligible)
    selected, used = [], set()

    def take(pool, n, group):
        count = 0
        for x in pool:
            site = x.get("site_group") or x["name"].replace("_30cm", "").replace("_60cm", "")
            if site in used:
                continue
            used.add(site)
            selected.append((x, group))
            count += 1
            if count == n:
                return
        raise ValueError(f"Insufficient reviewed examples for {group}: {count}/{n}")

    positives = [x for x in eligible if x["review_status"] == "positive" and x["filename"] in evidence]
    def confidence(x):
        return max([float(b.get("region_attributes", {}).get("model_confidence", 0))
                    for b in evidence[x["filename"]].get("original_boxes", [])] or [0])
    take([x for x in positives if confidence(x) >= .7], 20, "likely_easy_positive")
    take([x for x in positives if confidence(x) < .7], 10, "challenging")
    take([x for x in eligible if x["review_status"] == "uncertain"], 10, "challenging")
    # Prefer cases with saved evidence, then fill from other human-reviewed negatives.
    negatives = [x for x in eligible if x["review_status"] == "negative"]
    negatives.sort(key=lambda x: x["filename"] not in evidence)
    take(negatives, 20, "verified_negative")
    rng.shuffle(selected)
    manifest, references, provenance, via = [], [], [], {}
    group_ids = {}
    for i, (x, group) in enumerate(selected, 1):
        sid = f"site_{i:03d}"
        group_ids.setdefault(group, []).append(sid)
        dest = ROOT / "data/challenge/images" / f"{sid}.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        original = Path(x["image_path"])
        with Image.open(original) as im:
            width, height = im.size
            im.convert("RGB").save(dest, quality=94, subsampling=0, optimize=True)
        regions = []
        for b in x.get("regions", []):
            a = b["shape_attributes"]
            if a.get("name") != "rect":
                raise ValueError(f"Unsupported reference shape: {x['name']}")
            left, top, bw, bh = [float(a[k]) for k in ("x", "y", "width", "height")]
            if min(left, top) < -.01 or min(bw, bh) <= 0 or left + bw > width + 1 or top + bh > height + 1:
                raise ValueError(f"Invalid reference box: {x['name']}")
            regions.append({"shape_attributes": {"name": "rect", "x": left, "y": top,
                            "width": min(bw, width-left), "height": min(bh, height-top)},
                            "region_attributes": {"class": "tower_ground_site"}})
        status = x["review_status"]
        assert status != "positive" or regions
        assert status != "negative" or not regions
        row = {"id": sid, "image": f"images/{sid}.jpg", "width": width, "height": height,
               "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
        manifest.append(row)
        references.append({"id": sid, "status": status, "sampling_group": group,
                           "source_review": x["source"], "regions": regions})
        via[sid] = {"filename": f"{sid}.jpg", "size": dest.stat().st_size, "regions": regions,
                    "file_attributes": {"id": sid, "status": status, "notes": "Supplied human review"}}
        ev = evidence.get(x["filename"], {})
        md = metadata.get(x["name"], {})
        chip_meta = source / "samples" / x.get("state", "") / "chips" / f"{x['name']}.json"
        cm = read(chip_meta) if chip_meta.is_file() else {}
        detections, detector_source = predictions.get(x["filename"], (None, None))
        if ev:
            detections = []
            for b in ev.get("original_boxes", []):
                a = b["shape_attributes"]
                detections.append({"xyxy": [a["x"], a["y"], a["x"]+a["width"], a["y"]+a["height"]],
                                   "confidence": float(b.get("region_attributes", {}).get("model_confidence", 0))})
            detector_source = "source evidence.json/original_boxes"
        channels = {
            "imagery": {"path": row["image"], "date": ev.get("imagery_date") or md.get("acquisition_datetime") or cm.get("acquisition_datetime"),
                        "resolution_m": ev.get("resolution_m") or md.get("resolution_m") or cm.get("resolution_m"),
                        "source_id": ev.get("imagery_source") or md.get("source_id") or cm.get("source_id"),
                        "latitude": ev.get("latitude") or md.get("latitude"), "longitude": ev.get("longitude") or md.get("longitude")},
            "osm": {"tags": ev.get("osm_tags") or x.get("tags", {}),
                    "snapshot": ev.get("osm_snapshot"), "url": ev.get("osm_url") or md.get("osm_url")},
            "detector": {"available": detections is not None, "detections": detections,
                         "source": detector_source, "mode": "cached historical proposals; not rerun on classroom JPEGs"},
            "fcc": {"available": bool(ev), "matches": ev.get("fcc_matches") if ev else None,
                    "search_radius_m": ev.get("fcc_search_radius_m") if ev else None,
                    "caution": "Missing cache is not an empty registry search. A match does not prove cellular use or presence on the imagery date."},
        }
        write(ROOT / "data/challenge/evidence" / f"{sid}.json", {"id": sid, **channels})
        provenance.append({"id": sid, "original_filename": x["filename"], "site_group": x.get("site_group"),
                           "reference_source": x["source"], "original_sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
                           "image_encoding": "JPEG quality 94, no resize; coordinates unchanged",
                           "master_split": x.get("split"), "v4_training_manifest_split": membership.get(x["name"]),
                           "detector_cache_source": detector_source})
    write(ROOT / "data/challenge/manifest.json", manifest)
    write(ROOT / "data/reference/labels.json", references)
    write(ROOT / "data/reference/labels_via.json", {"_via_img_metadata": via, "_via_attributes": {"region": {}, "file": {}}})
    with (ROOT / "data/reference/labels.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "status", "sampling_group", "source_review"])
        writer.writeheader()
        writer.writerows({k: x[k] for k in writer.fieldnames} for x in references)
    manual = group_ids["likely_easy_positive"][:7] + group_ids["challenging"][:6] + group_ids["verified_negative"][:7]
    rng.shuffle(manual)
    write(ROOT / "data/manual20/ids.json", manual)
    write(ROOT / "data/manual20/starter_via.json", {"_via_img_metadata": {
        sid: {"filename": f"{sid}.jpg", "regions": [], "file_attributes": {"id": sid, "status": "unreviewed", "notes": ""}}
        for sid in manual}})
    write(ROOT / "data/reference/provenance.json", {"selection_seed": 66210, "images": provenance,
          "limits": "Retrospective teaching sample; mixed historical proposal sources and known training/validation overlap. Easy means human-positive with high proposal score, not an independent difficulty adjudication. Reference uncertainty is preserved."})
    print("Packaged", len(manifest), "images; manual subset", len(manual))
    print("Reference statuses:", dict(Counter(x["status"] for x in references)))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    main(parser.parse_args().source)
