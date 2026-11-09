# Week 10: Tower Detective 🕵️🗼

**GGS 662 Agentic GeoAI.** Label 20 aerial images in a browser, compare your work with supplied human annotations, then develop an agent that can consult imagery, detector proposals, OSM tags, and FCC evidence.

Open **[notebooks/10_agentic_tower_verification.ipynb](notebooks/10_agentic_tower_verification.ipynb)**. The lesson follows the usual numbered introduction → worked example → baseline → coding-agent handoff → evaluation → research briefing structure. Suggested class time: 75 minutes, with longer agent runs prepared ahead of class.

## Setup

For the investigator + blind image-only reviewer workflow, start with
[TWO_AGENT_WORKFLOW.md](TWO_AGENT_WORKFLOW.md). It prepares independent assistant
packets, validates both outputs, and generates a human labeling page containing
only cases routed for review.

From a terminal in `week10`:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements-demo.txt
```

Select that environment as the notebook kernel. Package installation needs internet; the core data/evidence exercises run offline. No GPU, trained weights, or data-service keys are required. A local coding assistant is used separately for the interface and agent exercises; no model API is called automatically.

## Browser labelling

Double-click `review/manual20.html`. Keep it in the lesson directory. Draw rectangles, select positive/negative/uncertain, and save each decision. Click a box and choose **Delete selected** to remove it. Export JSON frequently; browser storage is only a convenience. Resume by loading an exported JSON file.

Save your download as `student_work/my_tower_labels.json` for notebook comparison. Do not overwrite supplied references. Students spend about 15 minutes on the manual subset and may continue even if unfinished. The 20 images are part of the supplied 60, not additional images.

The page is an original small teaching interface inspired by VIA; it exports VIA 2-style rectangle records. Upstream VIA itself is not bundled. The notebook supplies a prompt to customize the working page, so students need not build annotation infrastructure from scratch.

## Included material

- 60 uniquely named RGB images at original pixel dimensions, encoded as compact JPEGs (~22 MB including metadata).
- 30 human-reviewed positives, 20 negatives, and 10 uncertain references. The intended sampling groups are 20 likely easy positives, 20 challenging cases, and 20 negatives; confidence-based difficulty is provisional.
- A varied, unlabelled 20-image browser starter; complete supplied references in JSON, CSV, and VIA-style JSON.
- Compact cached detector, OSM, FCC, and imagery records. Missing channels are explicit. Historical proposal sources differ, and some images have no saved detector output.
- Classroom CSVs in `data/tables/`: `sites.csv`, `osm_candidates.csv`, and `fcc_matches.csv`. Students load and filter local tables rather than downloading records for each candidate.
- Two reproducible fixed baselines, a bounded evidence CLI, and an agent handoff. No fabricated agent results.

Read [data/README.md](data/README.md) for source limitations and credits. This is a retrospective classroom comparison with references intentionally in the repo and known historical model overlap. It is not a blind held-out test or national accuracy estimate. `AGENT_HANDOFF.md` excludes references from the agent task by instruction; unrestricted filesystem access cannot enforce that boundary.

## Instructor preparation

Run the notebook once, inspect the reference examples/box convention, test browser export/resume, and pre-run the full 60-image agent exercise if needed. The default notebook skips absent manual/agent exports and displays baseline results. In an existing Python environment:

```powershell
python -m unittest discover -s tests -v
node tests/review.test.cjs
python scripts/build_review.py
python scripts/build_evidence_tables.py
python scripts/build_notebook.py
```

`scripts/prepare_lesson.py --source PATH` is an instructor packaging utility for the original project, not a student dependency. It rebuilds the selected dataset and reference files from existing human reviews without fetching data or training a model. Rerunning against a changed source index can change selection; the committed manifests/hashes define this version. Rebuild the review page afterwards.

Keep student exports, tool logs, execution outputs, and new runs local. Commit notebook source, selected images, compact reference/evidence records, and code. No national archives, source GeoTIFFs, ZIP packs, credentials, or model weights are bundled.

### Preparing FCC and OSM before class

This preparation is already complete for the committed lesson files. FCC searches cover all 60 locations using a 1 km radius; 68 record rows match 39 locations, and 21 searches have no nearby record. OSM attributes are bundled for the candidates where available. The notebook loads `data/tables/sites.csv`, `osm_candidates.csv`, and `fcc_matches.csv` once and filters by site ID. Agent evidence tools read the same prepared local data.

To rebuild after changing the teaching selection, run `prepare_lesson.py`, then `prepare_fcc.py --archive PATH_TO_EXISTING_FCC_ZIP --source-manifest PATH_TO_SOURCE_MANIFEST`, then `build_evidence_tables.py`. The FCC utility verifies the existing archive's hash and source-table row counts; it never downloads data. Students do not run these preparation steps. See `data/README.md` for provenance and missing-data semantics.
