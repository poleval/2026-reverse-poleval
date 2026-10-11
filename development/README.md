# Reverse PolEval — development period

Binding participant rules: `../README.md`. Limits: `params.md`.
Development panel: `models.txt` and `../development-models.md`.

Send submissions and feedback requests to
[krzysztof.pawel.wrobel@uj.edu.pl](mailto:krzysztof.pawel.wrobel@uj.edu.pl).

Email one `items.jsonl` attachment with 50–200 items and a short explanation
of the diagnostic design, authorship, sources and publication licence.
`provenance-template.md` can guide the explanation; a separate document is
optional. Use one email thread per team. JSON objects contain `input`,
`gold` and optional `aliases`. Example: `../scripts/examples/sample_items.jsonl`
shows the format only, not a template to clone.

Before sending:

```bash
python scripts/validate_format.py --items items.jsonl
```

`format_ok\t1` checks structure, not linguistic quality or rank.
Spreadsheet authors may use `spreadsheet-guide.md` and the optional
`../scripts/sheet_export_to_jsonl.py` helper.

Organisers review Polish necessity, originality, gold validity and
diagnostic design, and format. A rejected set may be revised and resent.
Aliases are reviewed with the JSONL file. Custom evaluators are used only
after manual acceptance and cannot coexist with non-empty aliases.

To request unofficial development feedback, say so in the email. At most
one successful organiser panel run per team per ISO week (Monday–Sunday,
Europe/Warsaw). The report includes the published panel's diagnostic score,
per-item discrimination and pairwise rates. This is private unofficial
feedback; official ranking uses the hidden panel.

For final submission, send the complete attachment in an email marked
FINAL before the announced deadline. The last timely FINAL email counts.

## Track 2 (optional)

Email a ZIP with the generator, README, provenance, required data and
pinned dependencies, and code/data licences. A repository link is optional.
Document `python generate.py --seed N --out items.jsonl`. Output follows the
same schema and 50–200 item limits. Generation must be deterministic,
offline and finish within 120 seconds in the organiser sandbox.

Seed-dependence is checked with `scripts/check_generator_seeds.py`.
Track 2 ranks separately by the mean over three hidden seeds; unofficial
feedback uses one seed. All teams use the same hidden seeds.
