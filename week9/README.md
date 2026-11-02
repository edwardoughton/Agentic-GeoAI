# Week 9: Using AI reasoning for scientific discovery

GGS 662 Agentic GeoAI: electricity tower detection from aerial imagery.

## Setup in this repository

Open the Agentic-GeoAI repository in VS Code. From a PowerShell terminal at the repository root:

```powershell
cd week9
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-demo.txt
.\.venv\Scripts\python scripts/prepare_demo.py
```

Open `notebooks/09_tower_detection_agentic_demo.ipynb` and select the `week9/.venv/Scripts/python.exe` kernel. The notebook locates the lesson from the repository root, week9, or week9/notebooks. Scripts locate it relative to their own files. Dataset setup validates bundled files and rebases data.yaml; it does not require the external source archive.

Complete the baseline before sending the Section 7 prompt to your coding agent. For agent work, use week9 as the working folder and the same Python environment. Fresh results go to week9/experiments and checkpoints to week9/runs. Rerun Section 8 after optimization. Leave the final-test switch disabled until model selection is complete. The augmentation assignment is a separate optional follow-on task.

Installation and the initial yolov8n.pt download require internet. CPU works; CUDA is used when available. Baseline training needs no agent API. The optional Claude launcher requires a separate SDK installation, API key and paid API access. No agent starts automatically.

## Included data

`data/demo100` contains **50 training / 10 validation / 50 test** original JPEGs and 110 matching YOLO labels. The name demo100 is retained from the initial 50/50 bundle; ten validation images were added so tuning can leave test untouched. Total imagery is about 16 MiB. Selection seed is 662. Original source train/validation/test membership is retained, with sampling spread across parent scenes. Parent-scene names are disjoint across splits; geographic proximity has not been independently audited.

Class 0 is tower. Label rows are normalized class/x-center/y-center/width/height. All selected images contain annotations: this small positive-only sample cannot establish performance on tower-free imagery. Missing labels are never assumed to mean verified negatives. Online augmentation adds varied views without saving extra JPEGs.

The manifest records source paths and image/label checksums. Source paths are provenance and need not exist locally. SHA256SUMS.json verifies portable bundled files; data.yaml is excluded because setup rewrites its local path. Historical scores in reference_results were measured on the earlier 35/10/5 demo50 dataset and are not comparable with this selection. No trained checkpoints, source archive, keys or live experiment results are bundled.

Source and annotation provenance and redistribution terms remain to be documented; this bundle assigns no new imagery license. Report results as a small classroom demonstration.
