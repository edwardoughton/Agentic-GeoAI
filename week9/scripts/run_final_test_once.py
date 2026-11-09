from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
from ultralytics import YOLO

try:
    from scripts.prepare_demo import prepare, find_root
except ModuleNotFoundError:
    from prepare_demo import prepare, find_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Run final test evaluation exactly once per explicit request.")
    parser.add_argument("--confirm", action="store_true", help="Required safety flag to evaluate on split=test")
    args = parser.parse_args()

    if not args.confirm:
        raise SystemExit("Refusing to run test evaluation without --confirm")

    root = find_root(Path(__file__).resolve().parents[1])
    data = prepare(root)
    experiments = root / "experiments"

    selected = json.loads((experiments / "selected_model.json").read_text(encoding="utf-8"))
    checkpoint = selected["checkpoint"]
    imgsz = int(selected.get("imgsz", 640))

    device = 0 if torch.cuda.is_available() else "cpu"
    eval_options = dict(conf=0.001, iou=0.7, max_det=300, augment=False)

    model = YOLO(checkpoint)
    metrics = model.val(
        data=str(data / "data.yaml"),
        split="test",
        imgsz=imgsz,
        batch=4,
        workers=0,
        device=device,
        **eval_options,
    )

    out = {
        "checkpoint": checkpoint,
        "imgsz": imgsz,
        "split": "test",
        "precision": float(metrics.box.mp),
        "recall": float(metrics.box.mr),
        "mAP50": float(metrics.box.map50),
        "mAP50_95": float(metrics.box.map),
        "evaluation": eval_options,
    }

    (experiments / "final_test_metrics.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
