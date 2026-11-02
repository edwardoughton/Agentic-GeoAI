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
    )
    (run / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (run / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    started = time.perf_counter()
    try:
        detector = YOLO(model_name)
        detector.train(
            data=str(data / "data.yaml"),
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
            data=str(data / "data.yaml"),
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
