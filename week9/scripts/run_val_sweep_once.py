from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from pathlib import Path

import torch
import ultralytics
import yaml
from ultralytics import YOLO

try:
    from scripts.prepare_demo import prepare, find_root
except ModuleNotFoundError:
    from prepare_demo import prepare, find_root

SEED = 662


def _write_tuning_yaml(data: Path, run: Path) -> Path:
    source_yaml = yaml.safe_load((data / "data.yaml").read_text(encoding="utf-8"))
    tuning_yaml = {
        "path": str(data.resolve().as_posix()),
        "train": source_yaml["train"],
        "val": source_yaml["val"],
        "names": source_yaml["names"],
    }
    destination = run / "data_tuning.yaml"
    destination.write_text(yaml.safe_dump(tuning_yaml, sort_keys=False), encoding="utf-8")
    return destination


def append_results_row(results_path: Path, row: dict) -> None:
    write_header = not results_path.exists() or results_path.stat().st_size == 0
    with results_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--confs", default="0.001,0.005,0.01,0.02")
    parser.add_argument("--ious", default="0.6,0.7,0.8")
    args = parser.parse_args()

    root = find_root(Path(__file__).resolve().parents[1])
    data = prepare(root)
    experiments = root / "experiments"
    experiments.mkdir(exist_ok=True)
    results = experiments / "results.csv"

    run = root / "runs" / f"{args.name}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1000000}"
    run.mkdir(parents=True, exist_ok=False)

    manifest_hash = hashlib.sha256((data / "manifest.json").read_bytes()).hexdigest()
    tuning_yaml = _write_tuning_yaml(data, run)

    confs = [float(x.strip()) for x in args.confs.split(",") if x.strip()]
    ious = [float(x.strip()) for x in args.ious.split(",") if x.strip()]

    config = {
        "method": "val_sweep",
        "checkpoint": args.checkpoint,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "confs": confs,
        "ious": ious,
        "tuning_data_yaml": str(tuning_yaml),
    }
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    environment = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "ultralytics": ultralytics.__version__,
        "seed": SEED,
        "device": "cpu",
    }
    (run / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    started = time.perf_counter()
    model = YOLO(args.checkpoint)

    sweep = []
    best = None
    for conf in confs:
        for iou in ious:
            metrics = model.val(
                data=str(tuning_yaml),
                split="val",
                imgsz=args.imgsz,
                batch=args.batch,
                workers=0,
                device="cpu",
                augment=False,
                conf=conf,
                iou=iou,
                max_det=300,
                project=str(run),
                name=f"val_conf{str(conf).replace('.', 'p')}_iou{str(iou).replace('.', 'p')}",
            )
            rec = {
                "conf": conf,
                "iou": iou,
                "precision": float(metrics.box.mp),
                "recall": float(metrics.box.mr),
                "mAP50": float(metrics.box.map50),
                "mAP50_95": float(metrics.box.map),
            }
            sweep.append(rec)
            if best is None or rec["mAP50_95"] > best["mAP50_95"]:
                best = rec

    seconds = time.perf_counter() - started
    (run / "sweep_metrics.json").write_text(json.dumps(sweep, indent=2), encoding="utf-8")

    row = dict(
        run_id=run.name,
        status="ok",
        model=f"val_sweep:{args.checkpoint}",
        epochs=0,
        imgsz=args.imgsz,
        seed=SEED,
        manifest_sha256=manifest_hash,
        precision=best["precision"],
        recall=best["recall"],
        mAP50=best["mAP50"],
        mAP50_95=best["mAP50_95"],
        seconds=seconds,
        checkpoint=args.checkpoint,
        config=str(run / "config.json"),
        error="",
    )
    (run / "metrics.json").write_text(json.dumps({"best": best, "row": row}, indent=2), encoding="utf-8")
    append_results_row(results, row)
    print(json.dumps({"best": best, "run_id": run.name, "seconds": seconds}, indent=2))


if __name__ == "__main__":
    main()
