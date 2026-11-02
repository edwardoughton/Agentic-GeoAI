from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import torch
from matplotlib.patches import Rectangle
from PIL import Image
from ultralytics import YOLO

try:
    from scripts.prepare_demo import prepare, find_root
except ModuleNotFoundError:
    from prepare_demo import prepare, find_root


def main() -> None:
    root = find_root(Path(__file__).resolve().parents[1])
    data = prepare(root)
    experiments = root / "experiments"
    results_path = experiments / "results.csv"
    rows = list(csv.DictReader(results_path.open(newline="", encoding="utf-8")))

    valid = [r for r in rows if r["status"] == "ok"]
    ranked = sorted(valid, key=lambda r: float(r["mAP50_95"]), reverse=True)
    baseline = next(r for r in rows if r["run_id"].startswith("baseline_") and r["status"] == "ok")
    best = ranked[0]

    selected = {
        "checkpoint": str(Path(best["checkpoint"]).resolve()),
        "imgsz": int(float(best["imgsz"])),
        "adapter": "plain_yolo",
    }
    (experiments / "selected_model.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")

    device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO(best["checkpoint"])
    paths = sorted((data / "images/val").glob("*.jpg"))[:3]
    predictions = model.predict(
        source=[str(path) for path in paths],
        imgsz=int(float(best["imgsz"])),
        conf=0.25,
        device=device,
        verbose=False,
    )

    fig, axes = plt.subplots(len(paths), 2, figsize=(10, 5 * len(paths)))
    if len(paths) == 1:
        axes = [axes]
    for row, path, prediction in zip(axes, paths, predictions):
        image = Image.open(path).convert("RGB")
        width, height = image.size
        row[0].imshow(image)
        label_path = data / "labels" / "val" / f"{path.stem}.txt"
        for line in label_path.read_text().splitlines():
            _, x, y, bw, bh = map(float, line.split())
            row[0].add_patch(
                Rectangle(
                    ((x - bw / 2) * width, (y - bh / 2) * height),
                    bw * width,
                    bh * height,
                    fill=False,
                    edgecolor="red",
                    linewidth=2,
                )
            )
        row[0].set_title(f"Annotation: {path.name}")
        row[0].axis("off")
        row[1].imshow(prediction.plot()[..., ::-1])
        row[1].set_title("Prediction (conf>=0.25)")
        row[1].axis("off")
    plt.tight_layout()
    predictions_path = experiments / "representative_val_predictions.png"
    fig.savefig(predictions_path, dpi=150)
    plt.close(fig)

    additional = [r for r in rows if not r["run_id"].startswith("baseline_")]
    additional_seconds = sum(float(r["seconds"] or 0) for r in additional)

    lines = [
        "# Tower detector optimization report",
        "",
        "## Summary",
        f"- Baseline run: `{baseline['run_id']}`",
        f"- Baseline validation mAP50-95: {float(baseline['mAP50_95']):.6f}",
        f"- Selected run: `{best['run_id']}`",
        f"- Best validation mAP50-95: {float(best['mAP50_95']):.6f}",
        f"- Absolute gain: {float(best['mAP50_95']) - float(baseline['mAP50_95']):+.6f}",
        f"- Additional runs used: {len(additional)} / 6",
        f"- Additional training/eval runtime (seconds): {additional_seconds:.3f}",
        "",
        "## Trials",
        "| run_id | status | model | epochs | imgsz | mAP50 | mAP50-95 | seconds | notes |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        map50 = "" if row["mAP50"] == "" else f"{float(row['mAP50']):.6f}"
        map95 = "" if row["mAP50_95"] == "" else f"{float(row['mAP50_95']):.6f}"
        note = ""
        if row["status"] != "ok":
            note = (row["error"] or "").replace("|", "/").replace("\n", " ")[:120]
        lines.append(
            f"| {row['run_id']} | {row['status']} | {row['model']} | {row['epochs']} | {row['imgsz']} | {map50} | {map95} | {float(row['seconds']):.3f} | {note} |"
        )

    lines.extend(
        [
            "",
            "## Selected pipeline",
            f"- Checkpoint: `{Path(best['checkpoint']).resolve()}`",
            f"- Inference image size: {int(float(best['imgsz']))}",
            "- Adapter: `plain_yolo`",
            "",
            "## Representative validation predictions",
            "- File: `experiments/representative_val_predictions.png`",
            "",
            "## Limitations",
            "- Validation set has only 10 images; variance is high.",
            "- Failures, if any, are recorded in the trials table.",
            "- Test evaluation is reserved for the human-controlled notebook cell; check experiments/final_test_metrics.json for prior access.",
        ]
    )
    (experiments / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "baseline": baseline["run_id"],
                "best": best["run_id"],
                "best_map50_95": float(best["mAP50_95"]),
                "gain": float(best["mAP50_95"]) - float(baseline["mAP50_95"]),
                "report": str(experiments / "report.md"),
                "selected_model": str(experiments / "selected_model.json"),
                "predictions": str(predictions_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
