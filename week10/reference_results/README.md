# Reproducible fixed baselines

These files contain **computed fixed-rule decisions**, not agent-generated annotations or invented results. Reproduce them with `scripts.lesson.baseline` and `scripts.lesson.score`.

| Method | Automatic / 60 | Request review | Errors on resolved automatic decisions |
| --- | ---: | ---: | ---: |
| Detector only | 37 | 23 | 2 / 34 |
| Fixed evidence rules | 20 | 40 | 0 / 20 |

Three detector-only automatic decisions concern uncertain references and are reported separately rather than scored as known binary truth. Rules send all ten uncertain references for review. These results describe the packaged retrospective sample and historical caches; they do not establish calibrated confidence or generalization.

Agent results must come from an actual documented run. No example array is silently substituted for missing agent output. Save live results in ignored `runs/` directories and inspect evidence faithfulness as well as scores.
