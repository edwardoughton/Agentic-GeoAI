# Tower detection optimization report

## Summary
- Baseline run: `baseline_20261102_155320_890400`
- Baseline validation mAP50-95: `0.000426`
- Current best run: `exp20_ensemble_exp10_exp17_20261104_083001_817900`
- Current best validation mAP50-95: `0.337500`
- Absolute improvement vs baseline: `0.337074`
- Final-test cell/script not executed; model selection remains validation-only.

## Anti-test-leak safeguards active
- `scripts/run_experiment_once.py` enforces split integrity checks against manifest and writes train/val-only `data_tuning.yaml`.
- `scripts/run_experiment_once.py` writes per-run `access_log.json` with blocked test split metadata.
- `scripts/run_final_test_once.py` isolates final test behind explicit `--confirm`.
- `scripts/run_alt_method.py` and `scripts/run_val_sweep_once.py` evaluate only on validation split under the fixed protocol.

## New experiments (`exp22`-`exp26`)

| run_id | status | model | mAP50-95 | seconds | notes |
|---|---:|---|---:|---:|---|
| `exp22_hardneg_from_exp10_20261104_085955` | failed | `exp22_hardneg_from_exp10` | - | 0 | Could not launch YOLO run because `ultralytics` is unavailable in this execution environment. |
| `exp23_tiled_exp10_20261104_085922_240400` | failed | `tiled` | - | 0 | Tiled YOLO adapter invocation blocked by missing `ultralytics`. |
| `exp24_frcnn_pretrained_e2_20261104_085913_993300` | failed | `fasterrcnn` | - | 0 | Faster R-CNN adapter blocked by missing `torchvision`. |
| `exp25_wbf_exp10_exp17_20261104_085931_482400` | failed | `ensemble-wbf` | - | 0 | WBF YOLO ensemble invocation blocked by missing `ultralytics`. |
| `exp26_loc_tune_from_exp10_20261104_085955` | failed | `exp26_loc_tune_from_exp10` | - | 0 | Could not launch YOLO run because `ultralytics` is unavailable in this execution environment. |

## Current best remains unchanged
- Selection run: `exp20_ensemble_exp10_exp17_20261104_083001_817900`
- Checkpoints:
  - `runs/exp10_lowlr_noaug_from_exp07_20261103_124759_288000/train/weights/best.pt`
  - `runs/exp17_cosine_from_exp10_20261103_175752_260100/train/weights/best.pt`
- Inference settings: `conf=0.001`, `iou=0.7`, `max_det=300`, `augment=false`.

## Limitations
- This session is blocked from running planned experiments because required local dependencies (`ultralytics`, `torchvision`) are unavailable and package installation is not succeeding in the current sandboxed runtime.
- Validation split has only 10 images, so rankings can shift with small metric differences.
- Test split was intentionally not used for tuning or selection.
