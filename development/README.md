# Reverse PolEval — development period

Binding participant rules: `../README.md`. Limits: `params.md`.
Development panel: `models.txt` and `../development-models.md`.

Upload one `items.jsonl` file with 50–200 items through the PolEval
evaluation platform. Include a short explanation of the diagnostic design,
authorship, sources and publication licence with the submission.
`provenance-template.md` can guide the explanation; a separate document is
optional. JSON objects contain `input`, `gold` and optional `aliases`.
`../scripts/examples/sample_items.jsonl` shows the format only, not a
template to clone.

Before uploading:

```bash
python scripts/validate_format.py --items items.jsonl
```

`format_ok\t1` checks structure, not linguistic quality or rank.
Spreadsheet authors may use `spreadsheet-guide.md` and the optional
`../scripts/sheet_export_to_jsonl.py` helper.

Organisers review Polish necessity, originality, gold validity and
diagnostic design, and format. A rejected set may be revised and
resubmitted on the platform.
Aliases are reviewed with the JSONL file. Custom evaluators are used only
after manual acceptance and cannot coexist with non-empty aliases.

Request unofficial development feedback for the platform submission. At most
one successful organiser panel run per team per ISO week (Monday–Sunday,
Europe/Warsaw). The report includes the published panel's diagnostic score,
per-item discrimination and pairwise rates. This is private unofficial
feedback; official ranking uses the hidden panel.

For final submission, upload the complete version through the platform
before the announced deadline. The latest valid submission recorded by
the platform before the deadline counts.

## Track 2 (optional)

Submit a repository URL pointing to a specific commit hash or tag through
the PolEval platform. The referenced revision must contain the
generator, README, provenance, required data, pinned dependencies, and
code/data licences, and be accessible to organisers. Organisers resolve
a tag to a commit when accepting the submission. For a private
repository, grant the user `djstrong` read access.
Document `python generate.py --seed N --out items.jsonl`. Output follows the
same schema and 50–200 item limits. Generation must be deterministic,
offline and finish within 120 seconds in the organiser sandbox.

Seed-dependence is checked with `scripts/check_generator_seeds.py`.
Track 2 ranks separately by the mean over three hidden seeds; unofficial
feedback uses one seed. All teams use the same hidden seeds.
