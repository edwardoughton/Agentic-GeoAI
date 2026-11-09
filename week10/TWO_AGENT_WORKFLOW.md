# Independent tower labeling and review

The investigator views imagery and reconciles cached detector, OSM and FCC evidence. The reviewer independently classifies the original image, without the investigator's answer, reasoning, detector boxes or registry metadata. Run them in separate fresh assistant sessions. Their task files request observable facts rather than private reasoning traces.

The reviewer is a direct classification role. A prompt cannot guarantee that a model does no internal reasoning; select a non-reasoning model or disable reasoning in your host where supported. The repository prepares handoffs and adjudicates their outputs; it does not invoke a model service automatically.

From `week10`, prepare a small pilot:

```powershell
python -m scripts.two_agent prepare --run runs/two_agent_pilot --ids site_001 site_002 site_003 site_004 site_005
```

Give each assistant only its own `TASK.md`, `packet.json`, and the referenced image files. Ask it to complete that task and save `decisions.json` beside its packet. A host that can restrict file access should expose only those files. Packet separation prevents accidental answer exposure; it does not sandbox an assistant with unrestricted repository access. Neither role should read supplied reference labels. The investigator packet contains all cached evidence for inspection; this batch workflow does not use the separate five-call adaptive CLI budget.

After both outputs are saved:

```powershell
python -m scripts.two_agent finalize --run runs/two_agent_pilot --threshold 0.85
```

Only matching binary decisions with adequate imagery and both confidence scores at or above the threshold receive a provisional automatic label. All disagreements, abstentions, poor images and low scores enter `human_review.json`. Missing or malformed decisions stop finalization rather than becoming negatives. `predictions.json` retains both original decisions, citations and routing reasons; `summary.json` records counts, threshold and input hashes.

Open the generated `human_review.html` to label the uncertain subset and draw boxes. It uses the existing offline labeling interface and exports VIA-style JSON. If the queue is empty, no page is created. Keep exports as a separate human audit record; finalization never silently replaces model decisions with human labels. The existing `import_manual` helper is specific to manual20 and does not import this variable subset. This workflow assigns chip-level labels; automatic tower bounding boxes are not inferred.

For all 60 images, prepare a new run without `--ids`. Freeze the policy after the pilot. Score its predictions separately with `scripts.lesson.score` after agents finish, comparing coverage and selective error against the single-agent baseline. Uncertain references are excluded from binary error calculations. Confidence scores and the default 0.85 threshold are uncalibrated; agreement is not proof, especially when both roles use the same model. Audit a sample of accepted positives and negatives before relying on saved human effort. Do not claim speed or accuracy gains until measured.

No paid API calls, online lookups, fabricated decisions, or reference scoring occur during preparation/finalization. Record model names/settings and elapsed human labeling time alongside each run for a reproducible comparison.
