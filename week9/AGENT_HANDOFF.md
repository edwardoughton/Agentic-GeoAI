# Agent assignment: maximize tower-detection mAP

Read README.md and notebooks/09_tower_detection_agentic_demo.ipynb. This is an optimization task for GMU GGS 662 Agentic GeoAI. Do not start a search until the human delegates it and the baseline has completed.

## Objective

Maximize measured validation mAP50-95 within six additional training runs or 60 minutes of training, whichever comes first. No formal hypothesis development is required. Choose preprocessing, feature representations, hyperparameters and detection models/methods using reasoning and measured validation feedback. Multiple changes per candidate are allowed. State briefly what changed and record exact settings. Use run_experiment where compatible; preserve baseline outputs and all trials, including failures.

## Fixed evaluation

Keep data/demo100/manifest.json, its 110 images, raw imagery, labels, class mapping, seed 662 and 50/10/50 assignments fixed. Never view test images or use test results during optimization. Fit learned preprocessing on training only. Transform boxes correctly for geometric operations. Merge tiled detections into original-image coordinates and score each original image once. Never treat missing labels as verified negative examples. RGB data cannot support genuine NDVI without an NIR band.

Primary score: validation mAP50-95 averaged across IoU 0.50:0.05:0.95. Retain the same AP evaluator, class mapping, conf=0.001, NMS iou=0.7, max_det=300 and augment=False at evaluation. Precision, recall, mAP50 and runtime are diagnostics. Input resolution can vary as a recorded pipeline choice. A non-YOLO model needs an adapter to the same evaluator; its own differently defined AP is not comparable. Do not tune the metric definition to increase scores.

## Execution and records

Use experiments/results.csv and per-run config/environment/metrics files. Preserve field names used by the notebook. Log failures and all training attempts; failed runs count toward the six-run budget. Set epoch or time limits to keep cumulative training within 60 minutes. Stop before launching a run that cannot fit the remaining budget. Local experiments and edits are authorized when this task is delegated; do not upload imagery, publish, or spend on cloud compute.

Candidate options include 320 versus 640 resolution, longer training, contrast preprocessing, learning rate/optimizer, augmentation, freeze depth, alternate learned features and different detectors. Choose the next candidate from the results rather than requiring a formal hypothesis or a full grid search. The goal is the highest observed score, not a claim to have found a global optimum.

If multiple agents are explicitly requested, share one total budget. A coordinator owns the results CSV and final selection; workers write separate run files and do not overwrite each other. No agent may inspect test data.

## Deliverables

Write experiments/report.md with baseline versus best validation mAP50-95, absolute gain, all trials, settings, runtime and limitations. Show representative validation predictions. Write experiments/selected_model.json with checkpoint (absolute path), imgsz and adapter (plain_yolo only for a plain YOLO pipeline). Include any preprocessing/inference adapter required to reproduce the chosen pipeline. Choose by maximum validation mAP50-95; break exact ties by lower runtime. Do not execute the final test: the human enables that once after selection. If blocked, report the actual blocker without fabricated metrics.
