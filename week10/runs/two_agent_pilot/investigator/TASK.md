# Investigator

Label freestanding cell tower ground sites. Exclude water towers, electrical pylons and rooftop supports, even with antennas. Inspect the whole chip.

Use imagery and cached detector, OSM and FCC evidence. Reconcile spatial/date conflicts; missing records are not negative evidence. Cite inspected channels.

Use a fresh session. Only read this packet and its image files; actually view each image. Never read data/reference, reference_results, or student labels. If you cannot view an image, abstain and set image_quality to poor. Confidence is an uncalibrated self-report, not a probability.

Save a JSON array as decisions.json in this directory, one row per packet ID:

```json
[{"id":"site_001","action":"request_review","confidence":0.0,"image_quality":"poor","evidence_ids":["site_001:imagery"],"reason":"Image could not be inspected."}]
```

Actions: confirm, no_target, request_review. image_quality: adequate or poor. For reviewer, reason means a short visible observation, not a rationale. Cite imagery and only channels you inspected. Reviewer may cite imagery only.
