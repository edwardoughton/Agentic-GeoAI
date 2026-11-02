# Quick tower detection dataset

50 original training images, 10 original validation images, and 50 original test images, each with a matching YOLO label file (class 0: tower). The demo100 name is retained from the initial 50 train / 50 test bundle; validation images were added for the notebook's agent search. No saved augmentation variants are included.

The deterministic selection uses seed 662 and cycles across parent scenes. Original source split membership is preserved. The source NY exclusion list was applied to train/test selection. Parent-scene names are disjoint across splits; spatial proximity has not been independently audited. All selected images have tower annotations, so background false-positive performance is not represented.

Run scripts/prepare_demo.py from week9, or run the notebook setup cell, before training. It checks files and hashes against manifest.json and writes an absolute local dataset root to data.yaml. The external tower_detector folder is not required. Use validation for tuning and reserve test for one final evaluation.

The manifest records original paths for provenance and SHA-256 checksums for images and labels. Source imagery/annotation rights are unchanged; no new license is assigned.
