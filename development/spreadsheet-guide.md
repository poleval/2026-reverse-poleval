# Preparing a submission in a spreadsheet

Submit `items.jsonl`: one item per line with `input`, `gold` and optional
`aliases`. Upload the file to the PolEval evaluation platform with
a short explanation of the diagnostic phenomena, how the items were created, sources and confirmation of the
authorship and publication licence rules.

You can author items in Google Sheets or Excel. Use two columns: `input`
(task text) and `gold` (canonical answer). The first row may contain the
headers `input,gold`; the converter also recognises `pytanie,odpowiedź`.

Submit 50–200 items. Each input may contain up to 2,000 characters, and
each answer up to 80. Multiline text within one cell is allowed. Inputs
must be unique after official normalisation. Do not copy existing tests
or use LLM-generated item content.

Download the sheet as CSV or TSV. A team member with Python can use the
optional starter-kit converter:

```bash
python scripts/sheet_export_to_jsonl.py --in questions.csv --out items.jsonl
python scripts/validate_format.py --items items.jsonl
```

The converter removes recognised headers and preserves cell text,
including line breaks. Add equivalent answer forms to each item's JSON
object as `aliases`, for example `"aliases": ["first variant", "second variant"]`.
At most five aliases are allowed per item; each must mean the same thing
as the canonical answer. Do not submit a separate aliases file.

If your team needs help with conversion, contact the organiser. Upload one
complete JSONL file through the PolEval platform before the deadline.
