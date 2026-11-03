# Tower detection optimization report

## Summary
- Baseline run: `baseline_20261102_155320_890400`
- Baseline validation mAP50-95: 0.000426
- Best run: `exp05_sgd_e45_img640_20261103_072626_839500`
- Best validation mAP50-95: 0.287415
- Absolute improvement: 0.286989
- Additional run budget used: 6/6 runs
- Additional training+validation runtime: 977.9 s (16.30 min)

## Trials and outcomes

| run_id | status | model | epochs | imgsz | mAP50-95 | seconds | notes |
|---|---:|---|---:|---:|---:|---:|---|
| `baseline_20261102_155320_890400` | ok | `yolov8n.pt` | 5 | 320 | 0.00042596022123156586 | 23.19 |  |
| `exp01_yolov8n_e30_img640_20261102_182909_609000` | failed | `yolov8n.pt` | 30 | 640 |  | 43.31 |   Download failure for https://github.com/ultralytics/assets/releases/download/v8.4.0/yolov8n.pt. Retry limit reached. H |
| `exp02_resume_e30_img640_20261102_183006_106300` | failed | `C:\Users\eoughton\Desktop\Github\Agentic-GeoAI\week9\runs\baseline_20261102_155320_890400\train\weights\best.pt` | 30 | 640 |  | 4.63 | [WinError 5] Access is denied |
| `exp03_resume_e30_img640_20261102_183030_162500` | ok | `C:\Users\eoughton\Desktop\Github\Agentic-GeoAI\week9\runs\baseline_20261102_155320_890400\train\weights\best.pt` | 30 | 640 | 0.28516285304365646 | 267.84 | First successful long 640 run from baseline checkpoint. |
| `exp04_adamw_lr003_e40_img640_20261102_183537_191100` | ok | `C:\Users\eoughton\Desktop\Github\Agentic-GeoAI\week9\runs\baseline_20261102_155320_890400\train\weights\best.pt` | 40 | 640 | 0.2621256457274855 | 302.54 | AdamW variant underperformed best SGD-like run. |
| `exp05_sgd_e45_img640_20261103_072626_839500` | ok | `C:\Users\eoughton\Desktop\Github\Agentic-GeoAI\week9\runs\baseline_20261102_155320_890400\train\weights\best.pt` | 45 | 640 | 0.2874147020113149 | 297.47 | Best measured validation mAP50-95. |
| `exp06_finetune_from_exp05_20261103_073614_770900` | ok | `C:\Users\eoughton\Desktop\Github\Agentic-GeoAI\week9\runs\exp05_sgd_e45_img640_20261103_072626_839500\train\weights\best.pt` | 20 | 640 | 0.26976350773278945 | 62.15 | Low-LR fine-tune from exp05 did not improve best. |

## Changes tried
- Increased image resolution from 320 to 640 and training duration from 5 epochs to 30-45 epochs.
- Switched model initialization to local baseline checkpoint to avoid external weight downloads.
- Compared optimizer/schedule settings (default optimizer vs AdamW, with tuned lr/lrf/weight_decay).
- Tried a follow-on low-learning-rate fine-tune from the best checkpoint.

## Representative validation predictions (best run)
- `runs/exp05_sgd_e45_img640_20261103_072626_839500/validation/val_batch0_pred.jpg`
- `runs/exp05_sgd_e45_img640_20261103_072626_839500/validation/val_batch1_pred.jpg`
- `runs/exp05_sgd_e45_img640_20261103_072626_839500/validation/val_batch2_pred.jpg`
## Limitations
- CPU-only training constrained search breadth and model size exploration.
- No external pretrained weight downloads were possible due proxy/network restrictions.
- Validation set has only 10 images, so ranking variance can be high; test set intentionally not used.
- A second baseline row (`baseline_20261102_182515_382900`) exists from a rerun and was preserved.

