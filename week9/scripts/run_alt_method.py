from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from PIL import Image
try:
    from torchvision.models.detection import FasterRCNN_ResNet50_FPN_Weights, fasterrcnn_resnet50_fpn
    from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
    from torchvision.ops import box_iou, nms
    from torchvision.transforms import functional as F
except ModuleNotFoundError:
    FasterRCNN_ResNet50_FPN_Weights = None
    fasterrcnn_resnet50_fpn = None
    FastRCNNPredictor = None
    box_iou = None
    nms = None
    F = None

try:
    from ultralytics import YOLO
except ModuleNotFoundError:
    YOLO = None

try:
    from scripts.prepare_demo import prepare, find_root
except ModuleNotFoundError:
    from prepare_demo import prepare, find_root


SEED = 662


def compute_ap(recall: np.ndarray, precision: np.ndarray) -> float:
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([1.0], precision, [0.0]))
    mpre = np.flip(np.maximum.accumulate(np.flip(mpre)))
    indices = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[indices + 1] - mrec[indices]) * mpre[indices + 1]))


def yolo_label_to_xyxy(x: float, y: float, w: float, h: float, width: int, height: int) -> list[float]:
    x1 = (x - w / 2) * width
    y1 = (y - h / 2) * height
    x2 = (x + w / 2) * width
    y2 = (y + h / 2) * height
    return [x1, y1, x2, y2]


def load_ground_truth(val_images_dir: Path, val_labels_dir: Path) -> tuple[dict[str, torch.Tensor], list[Path]]:
    images = sorted(val_images_dir.glob("*.jpg"))
    gt: dict[str, torch.Tensor] = {}
    for image_path in images:
        width, height = Image.open(image_path).size
        label_path = val_labels_dir / f"{image_path.stem}.txt"
        boxes: list[list[float]] = []
        if label_path.exists():
            for line in label_path.read_text(encoding="utf-8").splitlines():
                parts = line.strip().split()
                if len(parts) != 5:
                    continue
                cls, xc, yc, bw, bh = map(float, parts)
                if int(cls) != 0:
                    continue
                boxes.append(yolo_label_to_xyxy(xc, yc, bw, bh, width, height))
        gt[image_path.name] = torch.tensor(boxes, dtype=torch.float32) if boxes else torch.zeros((0, 4), dtype=torch.float32)
    return gt, images


def evaluate_predictions(
    predictions: dict[str, tuple[torch.Tensor, torch.Tensor]],
    ground_truth: dict[str, torch.Tensor],
    conf_threshold: float = 0.001,
    nms_iou: float = 0.7,
    max_det: int = 300,
) -> dict[str, float]:
    iou_thresholds = np.arange(0.5, 0.96, 0.05)

    tp_all: list[np.ndarray] = []
    conf_all: list[np.ndarray] = []
    total_gt = 0

    for image_name, gt_boxes in ground_truth.items():
        pred_boxes, pred_scores = predictions.get(
            image_name,
            (torch.zeros((0, 4), dtype=torch.float32), torch.zeros((0,), dtype=torch.float32)),
        )

        mask = pred_scores >= conf_threshold
        pred_boxes = pred_boxes[mask]
        pred_scores = pred_scores[mask]

        if pred_boxes.numel() > 0:
            keep = nms(pred_boxes, pred_scores, nms_iou)
            keep = keep[:max_det]
            pred_boxes = pred_boxes[keep]
            pred_scores = pred_scores[keep]

        gt_boxes = gt_boxes.float()
        total_gt += gt_boxes.shape[0]

        num_preds = pred_boxes.shape[0]
        tp = np.zeros((num_preds, len(iou_thresholds)), dtype=np.float32)

        if num_preds > 0 and gt_boxes.shape[0] > 0:
            ious = box_iou(pred_boxes, gt_boxes).cpu().numpy()
            for t_idx, threshold in enumerate(iou_thresholds):
                matched = np.zeros(gt_boxes.shape[0], dtype=bool)
                for p_idx in range(num_preds):
                    order = np.argsort(-ious[p_idx])
                    for g_idx in order:
                        if matched[g_idx]:
                            continue
                        if ious[p_idx, g_idx] >= threshold:
                            tp[p_idx, t_idx] = 1.0
                            matched[g_idx] = True
                            break

        if num_preds > 0:
            tp_all.append(tp)
            conf_all.append(pred_scores.cpu().numpy())

    if total_gt == 0:
        return dict(precision=0.0, recall=0.0, mAP50=0.0, mAP50_95=0.0)

    if not conf_all:
        return dict(precision=0.0, recall=0.0, mAP50=0.0, mAP50_95=0.0)

    conf = np.concatenate(conf_all, axis=0)
    tp = np.concatenate(tp_all, axis=0)
    order = np.argsort(-conf)
    tp = tp[order]

    fp = 1.0 - tp
    ap_values: list[float] = []
    p50 = 0.0
    r50 = 0.0

    for t_idx in range(len(iou_thresholds)):
        tpc = np.cumsum(tp[:, t_idx])
        fpc = np.cumsum(fp[:, t_idx])
        recall_curve = tpc / (total_gt + 1e-9)
        precision_curve = tpc / (tpc + fpc + 1e-9)
        ap = compute_ap(recall_curve, precision_curve)
        ap_values.append(ap)

        if t_idx == 0 and precision_curve.size:
            p50 = float(precision_curve[-1])
            r50 = float(recall_curve[-1])

    return {
        "precision": p50,
        "recall": r50,
        "mAP50": float(ap_values[0]),
        "mAP50_95": float(np.mean(ap_values)),
    }


def append_results_row(results_path: Path, row: dict) -> None:
    write_header = not results_path.exists() or results_path.stat().st_size == 0
    with results_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        if write_header:
            writer.writeheader()
        writer.writerow(row)


@dataclass
class RunContext:
    root: Path
    data: Path
    results: Path
    run_dir: Path
    run_id: str
    manifest_hash: str


def create_run_context(root: Path, data: Path, name: str) -> RunContext:
    run_dir = root / "runs" / f"{name}_{time.strftime('%Y%m%d_%H%M%S')}_{time.time_ns() % 1000000}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return RunContext(
        root=root,
        data=data,
        results=root / "experiments" / "results.csv",
        run_dir=run_dir,
        run_id=run_dir.name,
        manifest_hash=hashlib.sha256((data / "manifest.json").read_bytes()).hexdigest(),
    )


def run_ensemble(ctx: RunContext, ckpt_a: str, ckpt_b: str, imgsz: int) -> dict:
    if YOLO is None:
        raise ModuleNotFoundError("ultralytics is required for YOLO-based adapters")

    device = 0 if torch.cuda.is_available() else "cpu"
    eval_conf = dict(conf=0.001, iou=0.7, max_det=300, augment=False)
    config = {
        "method": "yolo_ensemble_nms",
        "checkpoints": [ckpt_a, ckpt_b],
        "imgsz": imgsz,
        "evaluation": eval_conf,
    }
    (ctx.run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    environment = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": str(device),
        "seed": SEED,
    }
    (ctx.run_dir / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    gt, images = load_ground_truth(ctx.data / "images" / "val", ctx.data / "labels" / "val")
    model_a = YOLO(ckpt_a)
    model_b = YOLO(ckpt_b)

    started = time.perf_counter()
    preds: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    for image in images:
        out_a = model_a.predict(source=str(image), imgsz=imgsz, conf=0.001, iou=0.99, max_det=300, augment=False, device=device, verbose=False)[0]
        out_b = model_b.predict(source=str(image), imgsz=imgsz, conf=0.001, iou=0.99, max_det=300, augment=False, device=device, verbose=False)[0]

        boxes = torch.cat([out_a.boxes.xyxy.cpu(), out_b.boxes.xyxy.cpu()], dim=0)
        scores = torch.cat([out_a.boxes.conf.cpu(), out_b.boxes.conf.cpu()], dim=0)

        if boxes.numel() > 0:
            keep = nms(boxes, scores, eval_conf["iou"])[: eval_conf["max_det"]]
            boxes = boxes[keep]
            scores = scores[keep]
        preds[image.name] = (boxes, scores)

    metrics = evaluate_predictions(preds, gt, conf_threshold=eval_conf["conf"], nms_iou=eval_conf["iou"], max_det=eval_conf["max_det"])
    seconds = time.perf_counter() - started

    row = dict(
        run_id=ctx.run_id,
        status="ok",
        model=f"ensemble:{ckpt_a}|{ckpt_b}",
        epochs=0,
        imgsz=imgsz,
        seed=SEED,
        manifest_sha256=ctx.manifest_hash,
        precision=metrics["precision"],
        recall=metrics["recall"],
        mAP50=metrics["mAP50"],
        mAP50_95=metrics["mAP50_95"],
        seconds=seconds,
        checkpoint="",
        config=str(ctx.run_dir / "config.json"),
        error="",
    )
    (ctx.run_dir / "metrics.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    append_results_row(ctx.results, row)
    return row



def _weighted_box_fusion_single(
    boxes: torch.Tensor,
    scores: torch.Tensor,
    iou_threshold: float,
    max_det: int,
) -> tuple[torch.Tensor, torch.Tensor]:
    if boxes.numel() == 0:
        return torch.zeros((0, 4), dtype=torch.float32), torch.zeros((0,), dtype=torch.float32)

    boxes = boxes.float().cpu()
    scores = scores.float().cpu()
    order = torch.argsort(scores, descending=True)
    boxes = boxes[order]
    scores = scores[order]

    fused_boxes: list[torch.Tensor] = []
    fused_scores: list[torch.Tensor] = []
    remaining = torch.arange(boxes.shape[0])

    while remaining.numel() > 0 and len(fused_boxes) < max_det:
        anchor = remaining[0]
        anchor_box = boxes[anchor].unsqueeze(0)
        candidate_boxes = boxes[remaining]
        ious = box_iou(anchor_box, candidate_boxes).squeeze(0)
        cluster_mask = ious >= iou_threshold
        cluster_ids = remaining[cluster_mask]

        cluster_boxes = boxes[cluster_ids]
        cluster_scores = scores[cluster_ids]
        weights = cluster_scores.unsqueeze(1)
        fused_box = (cluster_boxes * weights).sum(dim=0) / (weights.sum(dim=0) + 1e-9)
        fused_score = cluster_scores.max()

        fused_boxes.append(fused_box)
        fused_scores.append(fused_score)
        remaining = remaining[~cluster_mask]

    return torch.stack(fused_boxes, dim=0), torch.stack(fused_scores, dim=0)


def run_ensemble_wbf(ctx: RunContext, ckpt_a: str, ckpt_b: str, imgsz: int, fusion_iou: float) -> dict:
    if YOLO is None:
        raise ModuleNotFoundError("ultralytics is required for YOLO-based adapters")

    device = 0 if torch.cuda.is_available() else "cpu"
    eval_conf = dict(conf=0.001, iou=0.7, max_det=300, augment=False)
    config = {
        "method": "yolo_ensemble_wbf",
        "checkpoints": [ckpt_a, ckpt_b],
        "imgsz": imgsz,
        "fusion_iou": fusion_iou,
        "evaluation": eval_conf,
    }
    (ctx.run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    environment = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": str(device),
        "seed": SEED,
    }
    (ctx.run_dir / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    gt, images = load_ground_truth(ctx.data / "images" / "val", ctx.data / "labels" / "val")
    model_a = YOLO(ckpt_a)
    model_b = YOLO(ckpt_b)

    started = time.perf_counter()
    preds: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    for image in images:
        out_a = model_a.predict(source=str(image), imgsz=imgsz, conf=0.001, iou=0.99, max_det=300, augment=False, device=device, verbose=False)[0]
        out_b = model_b.predict(source=str(image), imgsz=imgsz, conf=0.001, iou=0.99, max_det=300, augment=False, device=device, verbose=False)[0]

        boxes = torch.cat([out_a.boxes.xyxy.cpu(), out_b.boxes.xyxy.cpu()], dim=0)
        scores = torch.cat([out_a.boxes.conf.cpu(), out_b.boxes.conf.cpu()], dim=0)

        boxes, scores = _weighted_box_fusion_single(
            boxes,
            scores,
            iou_threshold=fusion_iou,
            max_det=eval_conf["max_det"],
        )
        preds[image.name] = (boxes, scores)

    metrics = evaluate_predictions(preds, gt, conf_threshold=eval_conf["conf"], nms_iou=eval_conf["iou"], max_det=eval_conf["max_det"])
    seconds = time.perf_counter() - started

    row = dict(
        run_id=ctx.run_id,
        status="ok",
        model=f"ensemble_wbf:{ckpt_a}|{ckpt_b}",
        epochs=0,
        imgsz=imgsz,
        seed=SEED,
        manifest_sha256=ctx.manifest_hash,
        precision=metrics["precision"],
        recall=metrics["recall"],
        mAP50=metrics["mAP50"],
        mAP50_95=metrics["mAP50_95"],
        seconds=seconds,
        checkpoint="",
        config=str(ctx.run_dir / "config.json"),
        error="",
    )
    (ctx.run_dir / "metrics.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    append_results_row(ctx.results, row)
    return row


def _tile_starts(full_size: int, tile_size: int, overlap: float) -> list[int]:
    if full_size <= tile_size:
        return [0]
    step = max(1, int(tile_size * (1.0 - overlap)))
    starts = list(range(0, max(1, full_size - tile_size + 1), step))
    tail = full_size - tile_size
    if starts[-1] != tail:
        starts.append(tail)
    return starts


def run_tiled_yolo(ctx: RunContext, ckpt: str, imgsz: int, tile_size: int, overlap: float) -> dict:
    if YOLO is None:
        raise ModuleNotFoundError("ultralytics is required for YOLO-based adapters")

    device = 0 if torch.cuda.is_available() else "cpu"
    eval_conf = dict(conf=0.001, iou=0.7, max_det=300, augment=False)
    config = {
        "method": "yolo_tiled_inference",
        "checkpoint": ckpt,
        "imgsz": imgsz,
        "tile_size": tile_size,
        "tile_overlap": overlap,
        "evaluation": eval_conf,
    }
    (ctx.run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    environment = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": str(device),
        "seed": SEED,
    }
    (ctx.run_dir / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    gt, images = load_ground_truth(ctx.data / "images" / "val", ctx.data / "labels" / "val")
    model = YOLO(ckpt)

    started = time.perf_counter()
    preds: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
    for image_path in images:
        image = Image.open(image_path).convert("RGB")
        width, height = image.size
        x_starts = _tile_starts(width, tile_size, overlap)
        y_starts = _tile_starts(height, tile_size, overlap)

        tile_boxes: list[torch.Tensor] = []
        tile_scores: list[torch.Tensor] = []
        for y0 in y_starts:
            for x0 in x_starts:
                tile = image.crop((x0, y0, min(x0 + tile_size, width), min(y0 + tile_size, height)))
                out = model.predict(
                    source=np.asarray(tile),
                    imgsz=imgsz,
                    conf=0.001,
                    iou=0.99,
                    max_det=300,
                    augment=False,
                    device=device,
                    verbose=False,
                )[0]
                if out.boxes is None or out.boxes.xyxy.numel() == 0:
                    continue
                boxes = out.boxes.xyxy.cpu().clone()
                scores = out.boxes.conf.cpu().clone()
                boxes[:, [0, 2]] += float(x0)
                boxes[:, [1, 3]] += float(y0)
                boxes[:, [0, 2]] = boxes[:, [0, 2]].clamp(0, float(width))
                boxes[:, [1, 3]] = boxes[:, [1, 3]].clamp(0, float(height))
                tile_boxes.append(boxes)
                tile_scores.append(scores)

        if tile_boxes:
            boxes = torch.cat(tile_boxes, dim=0)
            scores = torch.cat(tile_scores, dim=0)
            keep = nms(boxes, scores, eval_conf["iou"])[: eval_conf["max_det"]]
            boxes = boxes[keep]
            scores = scores[keep]
        else:
            boxes = torch.zeros((0, 4), dtype=torch.float32)
            scores = torch.zeros((0,), dtype=torch.float32)
        preds[image_path.name] = (boxes, scores)

    metrics = evaluate_predictions(preds, gt, conf_threshold=eval_conf["conf"], nms_iou=eval_conf["iou"], max_det=eval_conf["max_det"])
    seconds = time.perf_counter() - started

    row = dict(
        run_id=ctx.run_id,
        status="ok",
        model=f"tiled:{ckpt}",
        epochs=0,
        imgsz=imgsz,
        seed=SEED,
        manifest_sha256=ctx.manifest_hash,
        precision=metrics["precision"],
        recall=metrics["recall"],
        mAP50=metrics["mAP50"],
        mAP50_95=metrics["mAP50_95"],
        seconds=seconds,
        checkpoint=ckpt,
        config=str(ctx.run_dir / "config.json"),
        error="",
    )
    (ctx.run_dir / "metrics.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    append_results_row(ctx.results, row)
    return row


class TowerDataset(torch.utils.data.Dataset):
    def __init__(self, images_dir: Path, labels_dir: Path):
        self.images = sorted(images_dir.glob("*.jpg"))
        self.labels_dir = labels_dir

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, idx: int):
        image_path = self.images[idx]
        image = Image.open(image_path).convert("RGB")
        width, height = image.size
        label_path = self.labels_dir / f"{image_path.stem}.txt"

        boxes = []
        labels = []
        for line in label_path.read_text(encoding="utf-8").splitlines():
            cls, xc, yc, bw, bh = map(float, line.split())
            if int(cls) != 0:
                continue
            boxes.append(yolo_label_to_xyxy(xc, yc, bw, bh, width, height))
            labels.append(1)

        target = {
            "boxes": torch.tensor(boxes, dtype=torch.float32),
            "labels": torch.tensor(labels, dtype=torch.int64),
            "image_id": torch.tensor([idx], dtype=torch.int64),
        }
        return F.to_tensor(image), target, image_path.name


def collate_fn(batch):
    images, targets, names = zip(*batch)
    return list(images), list(targets), list(names)


def run_fasterrcnn(ctx: RunContext, epochs: int, batch: int, lr: float, pretrained: bool) -> dict:
    if fasterrcnn_resnet50_fpn is None or FastRCNNPredictor is None or F is None:
        raise ModuleNotFoundError("torchvision is required for Faster R-CNN adapter")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    eval_conf = dict(conf=0.001, iou=0.7, max_det=300, augment=False)

    config = {
        "method": "fasterrcnn_resnet50_fpn",
        "epochs": epochs,
        "batch": batch,
        "lr": lr,
        "pretrained_coco": pretrained,
        "evaluation": eval_conf,
    }
    (ctx.run_dir / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    environment = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "device": str(device),
        "seed": SEED,
    }
    (ctx.run_dir / "environment.json").write_text(json.dumps(environment, indent=2), encoding="utf-8")

    train_ds = TowerDataset(ctx.data / "images" / "train", ctx.data / "labels" / "train")
    val_ds = TowerDataset(ctx.data / "images" / "val", ctx.data / "labels" / "val")

    g = torch.Generator().manual_seed(SEED)
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch, shuffle=True, collate_fn=collate_fn, generator=g)
    val_loader = torch.utils.data.DataLoader(val_ds, batch_size=1, shuffle=False, collate_fn=collate_fn)

    torch.manual_seed(SEED)
    if pretrained:
        model = fasterrcnn_resnet50_fpn(weights=FasterRCNN_ResNet50_FPN_Weights.DEFAULT)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, 2)
    else:
        model = fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None, num_classes=2)
    model.to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=0.0005)

    started = time.perf_counter()
    model.train()
    for _epoch in range(epochs):
        for images, targets, _names in train_loader:
            images = [img.to(device) for img in images]
            targets = [{k: v.to(device) for k, v in t.items()} for t in targets]
            loss_dict = model(images, targets)
            loss = sum(loss_dict.values())
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()

    checkpoint_path = ctx.run_dir / "train" / "weights" / "best.pt"
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), checkpoint_path)

    model.eval()
    gt, _images = load_ground_truth(ctx.data / "images" / "val", ctx.data / "labels" / "val")
    preds: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}

    with torch.no_grad():
        for images, _targets, names in val_loader:
            image = images[0].to(device)
            output = model([image])[0]
            labels = output["labels"].detach().cpu()
            keep = labels == 1
            boxes = output["boxes"].detach().cpu()[keep]
            scores = output["scores"].detach().cpu()[keep]
            preds[names[0]] = (boxes, scores)

    metrics = evaluate_predictions(preds, gt, conf_threshold=eval_conf["conf"], nms_iou=eval_conf["iou"], max_det=eval_conf["max_det"])
    seconds = time.perf_counter() - started

    row = dict(
        run_id=ctx.run_id,
        status="ok",
        model="fasterrcnn_resnet50_fpn_pretrained" if pretrained else "fasterrcnn_resnet50_fpn_scratch",
        epochs=epochs,
        imgsz=0,
        seed=SEED,
        manifest_sha256=ctx.manifest_hash,
        precision=metrics["precision"],
        recall=metrics["recall"],
        mAP50=metrics["mAP50"],
        mAP50_95=metrics["mAP50_95"],
        seconds=seconds,
        checkpoint=str(checkpoint_path),
        config=str(ctx.run_dir / "config.json"),
        error="",
    )
    (ctx.run_dir / "metrics.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
    append_results_row(ctx.results, row)
    return row


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="method", required=True)

    ens = sub.add_parser("ensemble")
    ens.add_argument("--name", required=True)
    ens.add_argument("--ckpt-a", required=True)
    ens.add_argument("--ckpt-b", required=True)
    ens.add_argument("--imgsz", type=int, default=640)

    wbf = sub.add_parser("ensemble-wbf")
    wbf.add_argument("--name", required=True)
    wbf.add_argument("--ckpt-a", required=True)
    wbf.add_argument("--ckpt-b", required=True)
    wbf.add_argument("--imgsz", type=int, default=640)
    wbf.add_argument("--fusion-iou", type=float, default=0.55)

    tiled = sub.add_parser("tiled")
    tiled.add_argument("--name", required=True)
    tiled.add_argument("--ckpt", required=True)
    tiled.add_argument("--imgsz", type=int, default=640)
    tiled.add_argument("--tile-size", type=int, default=640)
    tiled.add_argument("--overlap", type=float, default=0.25)

    fr = sub.add_parser("fasterrcnn")
    fr.add_argument("--name", required=True)
    fr.add_argument("--epochs", type=int, default=3)
    fr.add_argument("--batch", type=int, default=2)
    fr.add_argument("--lr", type=float, default=0.005)
    fr.add_argument("--pretrained", action="store_true")

    args = parser.parse_args()

    root = find_root(Path(__file__).resolve().parents[1])
    data = prepare(root)

    ctx = create_run_context(root, data, args.name)
    try:
        if args.method == "ensemble":
            row = run_ensemble(ctx, ckpt_a=args.ckpt_a, ckpt_b=args.ckpt_b, imgsz=args.imgsz)
        elif args.method == "ensemble-wbf":
            row = run_ensemble_wbf(ctx, ckpt_a=args.ckpt_a, ckpt_b=args.ckpt_b, imgsz=args.imgsz, fusion_iou=args.fusion_iou)
        elif args.method == "tiled":
            row = run_tiled_yolo(ctx, ckpt=args.ckpt, imgsz=args.imgsz, tile_size=args.tile_size, overlap=args.overlap)
        else:
            row = run_fasterrcnn(ctx, epochs=args.epochs, batch=args.batch, lr=args.lr, pretrained=args.pretrained)
    except Exception as exc:
        row = dict(
            run_id=ctx.run_id,
            status="failed",
            model=args.method,
            epochs=getattr(args, "epochs", 0),
            imgsz=getattr(args, "imgsz", 0),
            seed=SEED,
            manifest_sha256=ctx.manifest_hash,
            precision="",
            recall="",
            mAP50="",
            mAP50_95="",
            seconds=0,
            checkpoint="",
            config=str(ctx.run_dir / "config.json"),
            error=str(exc),
        )
        (ctx.run_dir / "metrics.json").write_text(json.dumps(row, indent=2), encoding="utf-8")
        append_results_row(ctx.results, row)
        raise

    print(json.dumps(row, indent=2))


if __name__ == "__main__":
    main()
