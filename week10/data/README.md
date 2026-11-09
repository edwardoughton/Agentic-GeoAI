# Teaching dataset and evidence

This is a **retrospective, purpose-selected classroom sample**, not an independent model benchmark. It preserves source human reviews rather than generating new reference labels with an assistant.

## Contents

- `tables/sites.csv`: one row for each of the 60 candidates, with imagery metadata and explicit FCC availability/search status. A blank FCC match count means not retrieved, not zero matches.
- `tables/osm_candidates.csv`: one row per candidate with common OSM tags as columns; `tags_json` preserves the complete cached tag dictionary. Blank fields mean unavailable/unspecified, not verified absence.
- `tables/fcc_matches.csv`: one row per nearby FCC match, joined using `id`; candidates can have multiple rows or none. Always consult `sites.csv` before interpreting a missing row. Registration/unique IDs should be loaded as strings.

Students load these tables with `pandas.read_csv`; no FCC or OSM downloads are required during class. `scripts/build_evidence_tables.py` regenerates CSVs from the same bundled JSON read by the agent tools. This flattens existing caches; it does not claim new searches for sites with missing evidence. OpenCellID has not been added.

FCC preprocessing was completed for **all 60 locations** using the source project's already downloaded, hash-verified national ASR archive. There are **68 nearby-record rows across 39 locations**; the other **21 locations have a completed 1 km search with no matching record**. These are absence of nearby registry records, not verified absence of towers. `tables/fcc_source_manifest.json` records archive provenance, schema/row-count checks, query distance, and the approximate NAD83/WGS84 comparison.

The OSM table has one row for all 60 candidates; **54 have source tags and 6 have no associated cached tags**. Empty values are preserved rather than invented. Full tags remain in `tags_json`. Core student exercises require no live Overpass request.

- `challenge/manifest.json`: 60 neutral IDs, relative image paths, dimensions, and SHA256 checksums.
- `challenge/images/`: JPEG derivatives of original RGB chips, quality 94, no resize. Reference coordinates are unchanged; tiny source edge-rounding overruns are clipped to image boundaries.
- `challenge/evidence/`: one record per image, with separate imagery, OSM, detector, and FCC channels. No reference verdicts, sampling groups, human boxes, or review notes are copied into these records. Original candidate tags can still be predictive and are not independent confirmation.
- `manual20/ids.json` and `starter_via.json`: 20-image subset, initially unreviewed with no boxes.
- `reference/labels.json`, `labels.csv`, `labels_via.json`: supplied source human annotations; positives have boxes, negatives have none, uncertainty remains explicit. The VIA-style JSON references the JPEG basenames; use the challenge image folder when importing it into upstream VIA.
- `reference/provenance.json`: original filenames/hashes, review source, selection seed, historical model membership when available, and encoding details. No original-machine absolute paths are needed for student execution.

## Selection and limitations

Selection seed: 66210. Twenty human positives with saved detector score ≥0.70 form the likely-easy group. Ten positives below that threshold and ten source uncertain records form the challenging group. Twenty human negatives complete the sample, prioritizing examples with saved evidence. Sites are deduplicated across source IDs/resolutions, then assigned shuffled neutral IDs. The manual subset contains 7 likely-easy, 6 challenging, and 7 negative examples; student inputs do not reveal those groups.

High proposal confidence is not independent human adjudication of difficulty. Negatives are source-reviewed, not a newly classified taxonomy of look-alikes. The lesson does not assert that all 20 negatives are particular structure types. The source box convention should be discussed from examples rather than treated as an error-free standard. Historical labels and metadata are snapshots and can contain mistakes.

The source master index includes examples assigned to training and validation. Known membership in the v4 manifest and the later master snapshot is recorded; absent membership does not prove absence from every previous checkpoint. Cached detector proposals come from several historical source runs. They were generated on original source images, not rerun on these JPEG derivatives. Comparing policies over these caches does not isolate the effect of one model.

The label answers are supplied for teaching and are accessible in this repository. Students inspect some during development. Claims about blinded evaluation, independence, calibrated confidence, national representativeness, or verified causal improvement would be unsupported.

## Missing and temporal evidence

`available=false` means that evidence was not present in the selected cache. `matches=null` is different from a completed search with `matches=[]`. No registry miss establishes absence. Nearby FCC coordinates may describe another structure. Registration does not establish cellular use, and construction/dismantlement information must be compared with imagery dates. Some source dates or coordinates are unavailable; do not fill them with guesses.

## Attribution and provenance

Source project: instructor's `us_tower_expansion`, master index as inspected November 9, 2026, with latest recorded human import through evidence Batch 8. Source references are the instructor's existing reviewed annotations. No copyrighted street-level imagery is included.

- Aerial imagery: **USDA National Agriculture Imagery Program (NAIP)**. Credit USDA Farm Production and Conservation / geospatial imagery providers. [USDA dataset record and public-domain designation](https://catalog.data.gov/dataset/national-agriculture-imagery-program-naip-imagery). Individual acquisition/source IDs are retained where available.
- Candidate tags: **© OpenStreetMap contributors**, available under the [Open Database License](https://www.openstreetmap.org/copyright). Cached candidate attributes are a small extracted subset; retain attribution and comply with the source license when redistributing derivatives.
- Structure records: source project's cached **FCC Antenna Structure Registration** evidence. Relevant original record identifiers/URLs remain in the evidence records. This lesson does not imply FCC endorsement or assign new licensing terms to upstream data.
- Annotation workflow: inspired by [VGG Image Annotator](https://robots.ox.ac.uk/~vgg/software/via/index.html). The lesson HTML is original code; no upstream VIA JavaScript is copied.
