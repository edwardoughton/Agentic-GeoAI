# Second-stage agent assignment: training augmentation

Run only when the human explicitly delegates this extension after the initial search. No experiments are launched by adding this file. New budget: at most three additional training attempts (failures included) or 30 minutes of training, whichever comes first. Preserve the original experiment record and incumbent selection.

## Audit first

Read the notebook, original AGENT_HANDOFF.md, experiments/results.csv, and each successful run's config.json and train/args.yaml. Summarize actual transforms. The existing opt06_adamw640 run requested horizontal flips, degrees=5, mosaic=0.25 and mixup=0.1. Do not claim augmentation was absent. The external source archive contains pre-augmented data, but this bundle uses originals. A no-additional-augmentation control cannot undo transforms in source images or earlier checkpoint training.

## Three matched trials

Use scripts/run_experiment_once.py and names prefixed aug_. Choose one existing local initial checkpoint and use that identical file for every trial, preferably the baseline checkpoint. Do not initialize each trial from the previous trial's result. Record its path and hash. Keep model, resolution (suggested 640), epochs (suggested 30), optimizer, learning rate, batch size, seed and stopping policy identical. Choose limits that fit the remaining budget; a common fixed schedule with patience greater than epochs avoids differing early-stop exposure. Record actual epochs and wall time. Prior checkpoint training is shared by all trials and must be acknowledged.

Explicitly set the following training arguments, rather than inheriting checkpoint settings:

- Control: fliplr=0, flipud=0, degrees=0, translate=0, scale=0, shear=0, perspective=0, hsv_h=0, hsv_s=0, hsv_v=0, mosaic=0, mixup=0, copy_paste=0, close_mosaic=0. Also disable cutmix and bgr if supported by the installed version. Audit any automatic Albumentations transforms; either disable consistently through a supported mechanism or report their presence and call this a controlled built-in-transform comparison rather than a wholly augmentation-free control.
- Flips: same explicit control settings, except fliplr=0.5 and flipud=0.5.
- Flips plus rotation: same as flips, except degrees=15 (random angles within +/-15 degrees). Rotation strength can be chosen before running, but must be documented.

Use detection-aware online transforms so bounding boxes are transformed with images. Do not enlarge or modify data/demo100 or change its manifest: online augmentation provides more varied views while retaining 50 training tiles. Preview training batch visualizations for correctness and clipping; do not infer quantitative benefit from appearance alone. Offline augmentation is a later capability, not necessary for this task. It requires derived-data bookkeeping, box verification and compute-matched comparisons.

## Fixed evaluation and deliverables

Keep validation/test files and labels unchanged; no test access. Retain the same validation evaluator and conf=0.001, iou=0.7, max_det=300, augment=False. Maximize validation mAP50-95. Append every run to experiments/results.csv with the existing schema and preserve per-run settings. Do not run scripts/finalize_report.py blindly if it would overwrite the first-stage report. Write experiments/augmentation_report.md containing the audit, three measured scores, deltas versus matched control and incumbent, actual settings, source counts, runtime and limitations. Attribution of augmentation benefit comes from the matched trials, not from comparing different epoch schedules.

Keep experiments/selected_model.json unchanged unless a candidate strictly improves the incumbent validation mAP50-95 under the same protocol. If improved, preserve the previous selection in experiments/selected_model_before_augmentation.json before updating and document the change. If the test has already been viewed, say so and do not present a repeat test as an untouched final evaluation. No formal hypothesis writing is required. Do not upload data or use paid cloud compute.
