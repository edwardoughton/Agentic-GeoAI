# Tower Detective: evidence-using agent task

Work in `week10`. This is an exploratory classroom comparison with supplied reference answers, not a blind national test. The references are intentionally in the repo so students can compare their manual work. During this agent task do not read `data/reference/`, student annotation exports, reference results, or sampling-group information. This instruction is not a technical access barrier.

## Target and actions

The target is a freestanding cell-tower ground site. Water towers, electrical pylons, rooftop supports, and other supports are excluded even when they carry antennas. A chip can contain an excluded support and a separate true target. Inspect the whole image.

Choose `confirm`, `no_target`, or `request_review`. Missing tool results are not evidence of absence. An OSM cellular tag, detector score, height, or FCC match alone does not establish the target. Missing FCC registration does not disprove it. Compare imagery and structure dates; nearby registrations may describe a different structure. Model scores are not calibrated probabilities.

## Allowed tools

Read candidate IDs and neutral image dimensions from `data/challenge/manifest.json`. Retrieve evidence using the following CLI, changing `--tool` to `imagery`, `detector`, `osm`, or `fcc`:

```powershell
python scripts/lesson.py --id site_001 --tool imagery --run agent_v1
```

The imagery result gives an absolute path to the local image; actually view it using your image-viewing capability. If you cannot view images, report that limitation and request review rather than pretending you inspected them. All source evidence is cached and labelled as such. The wrapper logs outputs and UTC timestamps in `runs/agent_v1/tool_calls.jsonl` and enforces five calls per candidate within that run. Do not bypass the wrapper or reset its log to avoid the budget.

Gather basic image evidence first. Choose additional channels when they could resolve uncertainty. Do not use all tools mechanically on every image. Record observable evidence and short reasons, not private internal reasoning. No network requests, retraining, reference-label access, or source-data edits are needed.

## Budget and output

First try 5 IDs chosen by the student. Stop after those five, summarize disagreements in evidence, and let the student inspect tool use. When asked for the full run, process all 60 IDs once with the frozen policy, at most five evidence calls per image. Use the same run name for continued work. Preserve earlier runs; use a new name for a policy revision.

Write a JSON array to `runs/agent_v1/predictions.json`. Each candidate appears once:

```json
[
  {
    "id": "site_001",
    "action": "request_review",
    "evidence_ids": ["site_001:imagery", "site_001:detector"],
    "reason": "Replace this example with observed facts and the specific unresolved issue."
  }
]
```

Cite only evidence IDs actually returned by tools. Do not make up model usage or cost. Optional model confidence must be labelled as an uncalibrated self-report. If evidence is insufficient, `request_review` is an acceptable complete decision.

Validate with `scripts.lesson.validate_predictions`. The full-run scorer requires all 60 IDs; omitted cases must not silently become negatives. Record the policy, tool budget, model/assistant name if known, execution date, and limitations in `runs/agent_v1/run_notes.md`. Stop after saving decisions; the student runs reference scoring in the notebook.
