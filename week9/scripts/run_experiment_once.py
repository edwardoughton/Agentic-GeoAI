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


def _coerce_value(value: str):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def parse_options(raw: str | None, pairs: list[str] | None) -> dict:
    parsed: dict = {}
    if raw:
        obj = json.loads(raw)
        if not isinstance(obj, dict):
            raise ValueError("--options must be a JSON object")
        parsed.update(obj)
    for pair in pairs or []:
        if "=" not in pair:
            raise ValueError(f"Invalid --set value '{pair}'; expected key=value")
        key, value = pair.split("=", 1)
        parsed[key] = _coerce_value(value)
    return parsed


def _assert_fixed_split_integrity(data: Path) -> dict[str, list[str]]:
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    split_records = {split: [r for r in manifest["records"] if r["split"] == split] for split in ("train", "val", "test")}

    expected_counts = {"train": 50, "val": 10, "test": 50}
    for split, expected in expected_counts.items():
        if len(split_records[split]) != expected:
            raise ValueError(f"Unexpected {split} record count: {len(split_records[split])} (expected {expected})")

    listed: dict[str, list[str]] = {}
    for split in ("train", "val", "test"):
        images = sorted([(data / r["images"]).resolve().as_posix() for r in split_records[split]])
        labels = sorted([(data / r["labels"]).resolve().as_posix() for r in split_records[split]])
        actual_images = sorted([p.resolve().as_posix() for p in (data / "images" / split).glob("*.jpg")])
        actual_labels = sorted([p.resolve().as_posix() for p in (data / "labels" / split).glob("*.txt")])
        if images != actual_images or labels != actual_labels:
            raise ValueError(f"{split} files differ from manifest")
        listed[split] = sorted([Path(path).name for path in images])

    if set(listed["train"]) & set(listed["test"]) or set(listed["val"]) & set(listed["test"]):
        raise ValueError("Split overlap detected between train/val and test")
    return listed


def _write_tuning_yaml(data: Path, run: Path) -> Path:
    """Create a split-sealed YAML for optimization runs (no test split reference)."""
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


def run_experiment(
    root: Path,
    data: Path,
    results: Path,
    name: str,
    model_name: str,
    epochs: int,
    imgsz: int,
    batch: int,
    training_options: dict,
) -> dict:
    device = 0 if torch.cuda.is_available() else "cpu"
    eval_options = dict(conf=0.001, iou=0.7, max_det=300, augment=False)
    manifest_hash = hashlib.sha256((data / "manifest.json").read_bytes()).hexdigest()
    forbidden = {"data", "seed", "project", "name", "exist_ok", "device", "workers", "split"}
    if forbidden & training_options.keys():
        raise ValueError("Keep dataset, seed, split and run bookkeeping fixed")

    run = root / "runs" / f"{name}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1000000}"
    run.mkdir(parents=True, exist_ok=False)

    split_listing = _assert_fixed_split_integrity(data)
    tuning_yaml = _write_tuning_yaml(data, run)
    access_log = {
        "policy": "optimization_runs_must_use_train_val_only",
        "train_images": split_listing["train"],
        "val_images": split_listing["val"],
        "test_images_blocked_count": len(split_listing["test"]),
    }
    (run / "access_log.json").write_text(json.dumps(access_log, indent=2), encoding="utf-8")

    environment = dict(
        python=platform.python_version(),
        torch=torch.__version__,
        ultralytics=ultralytics.__version__,
        device=str(device),
        seed=SEED,
    )
    options = dict(patience=5, plots=True, mosaic=0.0, cache=False)
    options.update(training_options)
    config = dict(
        model=model_name,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        seed=SEED,
        manifest_sha256=manifest_hash,
        evaluation=eval_options,
        options=options,
        tuning_data_yaml=str(tuning_yaml),
    )
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (run / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    started = time.perf_counter()
    try:
        detector = YOLO(model_name)
        detector.train(
            data=str(tuning_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            workers=0,
            device=device,
            seed=SEED,
            project=str(run),
            name="train",
            exist_ok=False,
            **options,
        )
        checkpoint = run / "train/weights/best.pt"
        fitted = YOLO(str(checkpoint))
        metrics = fitted.val(
            data=str(tuning_yaml),
            split="val",
            imgsz=imgsz,
            batch=batch,
            workers=0,
            device=device,
            project=str(run),
            name="validation",
            **eval_options,
        )
        row = dict(
            run_id=run.name,
            status="ok",
            model=model_name,
            epochs=epochs,
            imgsz=imgsz,
            seed=SEED,
            manifest_sha256=manifest_hash,
            precision=float(metrics.box.mp),
            recall=float(metrics.box.mr),
            mAP50=float(metrics.box.map50),
            mAP50_95=float(metrics.box.map),
            seconds=time.perf_counter() - started,
            checkpoint=str(checkpoint),
            config=str(run / "config.json"),
            error="",
        )
    except Exception as exc:
        row = dict(
            run_id=run.name,
            status="failed",
            model=model_name,
            epochs=epochs,
            imgsz=imgsz,
            seed=SEED,
            manifest_sha256=manifest_hash,
            precision="",
            recall="",
            mAP50="",
            mAP50_95="",
            seconds=time.perf_counter() - started,
            checkpoint="",
            config=str(run / "config.json"),
            error=str(exc),
        )
        raise
    finally:
        (run / "metrics.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
        write_header = not results.exists() or results.stat().st_size == 0
        with results.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row))
            if write_header:
                writer.writeheader()
            writer.writerow(row)

    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--imgsz", type=int, default=320)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--options", default="{}")
    parser.add_argument("--set", action="append", default=[])
    args = parser.parse_args()

    root = find_root(Path(__file__).resolve().parents[1])

    data = prepare(root)
    experiments = root / "experiments"
    experiments.mkdir(exist_ok=True)
    results = experiments / "results.csv"

    row = run_experiment(
        root=root,
        data=data,
        results=results,
        name=args.name,
        model_name=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        training_options=parse_options(args.options, args.set),
    )
    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
