# Reverse PolEval: Diagnostic Benchmark Design for Polish LLMs

PolEval 2026 shared task. Participants design the benchmark. Organisers run
a fixed panel of local open-weight models and score how diagnostic the
submitted set is.

A useful item is not merely hard. An item on which every model fails, or
every model succeeds, does not compare systems. The target is an
automatically checkable Polish example on which some models are correct and
others are not, for a reason that depends on Polish.

Organiser: Krzysztof Wróbel, Jagiellonian University.

This file is the public task description. Frozen numbers:
[`development/params.md`](development/params.md). Qualification examples:
[`development/qualification-rubric.md`](development/qualification-rubric.md).
Spreadsheet path (no coding):
[`development/spreadsheet-guide.md`](development/spreadsheet-guide.md).

Submit solutions through the PolEval evaluation platform. For Track 1, upload
`items.jsonl`; for Track 2, provide a repository URL pointing to a specific
commit hash or tag. See the [submission procedure](development/README.md).

## What you submit

There is no organiser gold test for you to solve, and no training set.
You submit the items. You do not upload model predictions.

| Track | What | Where | Rank |
| --- | --- | --- | --- |
| **1 — Benchmark set** (official) | 50–200 pairs `(input, gold)` | `items.jsonl` uploaded to PolEval | Hidden Test B panel |
| **2 — Generator** (secondary) | Repository implementing `generate(seed)` | Repository URL with commit hash or tag, submitted on PolEval | Mean over 3 hidden seeds |

Tracks are ranked separately. Track 1 is the official task.

## Schedule

Aligned with the [PolEval 2026 calendar](https://poleval.pl/dates/).

| Date | Milestone |
| --- | --- |
| 13 October 2026 | Test A: schema, prompts, development models, format check, this kit |
| 13 October – 30 November 2026 | Development. Rolling qualification. At most one unofficial panel run per team per ISO week |
| 13 November 2026 | Second call for participation |
| 1 December 2026 | Test B deadline. Organisers run the hidden panel offline |
| 8 December 2026 | Official results |
| 15 December 2026 | Participant paper deadline |
| 5 January 2027 | Paper acceptance |
| 19 January 2027 | Camera-ready |
| March 2027 | Presentation; proceedings in the ACL Anthology |

## Official chat messages

You do not supply a system prompt, a chat template, or decoding parameters.
Every item is sent as:

**System**

> Jesteś modelem rozwiązującym krótkie, automatycznie oceniane zadania dotyczące języka polskiego. Odpowiedz wyłącznie poprawną odpowiedzią na zadanie z wiadomości użytkownika. Nie dodawaj wyjaśnień, etykiet, cytatów ani dodatkowego tekstu.

**User**

```text
<input>
```

The system message is fixed for every submission and both panels. The user
message content is exactly the submitted `input`, including its whitespace
and line breaks. The `input` field holds the task and its linguistic material. It must not contain
instructions about role, instruction priority, ignoring earlier
instructions, or the conversation itself. Such an item is rejected at
qualification.

Decoding is greedy and deterministic: temperature 0, `max_new_tokens=64`,
each model’s released chat template, the same inference configuration on
every run.

## Scope

In scope: phenomena for which Polish is necessary to decide the gold
answer — inflection and agreement, case, gender, reference, negation and
particles, lexical or constructional ambiguity, and inference from a Polish
passage when the answer is uniquely determined.

Out of scope: arithmetic, ciphers, long-context symbol puzzles, and any
task whose decision rule and gold survive literal translation into another
language. Polish must not be only a wrapper around a language-independent
puzzle.

Example (passes the Polish-necessity gate):

```json
{"input": "Który wyraz w zdaniu „Posłanka, która wczoraj wystąpiła, złożyła wniosek” odnosi się do posłanki?", "gold": "która"}
```

`scripts/examples/sample_items.jsonl` shows the file shape only. It is not a
template to clone.

## Originality and human authorship

Items (Track 1) and generators (Track 2) must be original. They must not
be built from existing public evaluation sets. In particular, do not copy,
subset, shuffle, lightly edit, or translate items from public benchmarks
or leaderboards, including Open PL LLM Leaderboard suites, KLEJ, PolQA,
Polish exam dumps, MMLU and its translations, MT-Bench-style prompts, and
previous PolEval test sets. Do not scrape items whose gold answers are
already published as evaluation data.

Generative language models must not create or propose item text, questions,
gold answers, diagnostic contrasts, or a Track 2 generator's rules,
templates, or linguistic data. The diagnostic design and all submitted
linguistic content must be created by the team. Generative tools may only be
used for clerical transformations that do not create or alter linguistic or
program logic, and their use must be declared.

Allowed: newly written items; newly designed generators; public
*unlabelled* text (a corpus sentence, for example) as raw material, when
the question, the gold, and the diagnostic target are yours and are not
recoverable from a public evaluation key.

Declare provenance with
[`development/provenance-template.md`](development/provenance-template.md).
Organisers may request working materials or a short explanation of the design
process. A false declaration or a derivative of a known public test set is
rejected, including after the scoring run if found later.

## Track 1 — file format

One UTF-8 JSONL file, `items.jsonl`, with one object per line. Each item
has required string fields `input` and `gold`, and an optional array of
strings `aliases` (empty when omitted). No other fields are accepted.

Schema-only example, not a valid linguistic task:

```jsonl
{"input": "First line\nSecond line", "gold": "answer", "aliases": ["answer."]}
```

Submit 50–200 items. Inputs must be non-empty, unique after official
normalisation, and at most 2,000 characters. Gold and each alias must be
non-empty after normalisation and at most 80 characters. At most five
aliases per item are allowed. Duplicate aliases and aliases equivalent to
the canonical gold after normalisation are rejected. Multiline inputs are
allowed through JSON escaping (`\n`). Blank lines are rejected.
Items are numbered automatically in reports; no IDs are required.

Fewer than 200 items is allowed with no item-count penalty. Deterministic,
human-designed generation followed by editing is allowed under the
originality and authorship rules.

```bash
python scripts/validate_format.py --items items.jsonl
```

`format_ok\t1` means the file may enter qualification; it is not the task
score. Official ranks are computed offline at Test B. Spreadsheet authors
can use the optional helper described in
[`development/spreadsheet-guide.md`](development/spreadsheet-guide.md).

## How answers are marked

Default: **exact match** after official normalisation (Unicode NFKC, strip,
collapse whitespace). Matching is case-sensitive; case folding is disabled
for every official run.

**Aliases** (preferred when several surface forms are valid): put extra
accepted strings in the item's `aliases` array. Gold is always accepted.
An alias must be genuinely equivalent to gold for that item, rather than a
model-specific answer pattern. Organisers review aliases with the items;
changes require requalification. No separate alias file is submitted.
Implementation: `scripts/aliases_evaluator.py`. Example:
`scripts/examples/sample_items.jsonl`.

**Custom `evaluator.py`** only when aliases cannot express the
equivalence:

```python
def accept(prediction: str, gold: str) -> bool:
    ...
```

Deterministic, no network, returns a plain `bool`, finishes within 5
seconds per call, and accepts the submitted gold. Official scoring uses
it only after organisers have read the code, checked that it implements an
inspectable string equivalence (not a list of known model outputs), and
confirmed it can be sandboxed. A declined or broken checker is replaced by
exact match. Do not submit both a
custom evaluator and non-empty inline aliases.

## Qualification

Pass/fail, rolling through the development period, on a random sample of
30 items. A submission is admitted only if all four gates hold. Any audited
gold-validity or diagnostic-design failure rejects the pack; three audited
Polish-necessity or originality failures reject it. A rejected set may be
resubmitted.

1. **Polish necessity.** Organisers translate `input` literally. If the
   same decision rule and the same gold still work, the item fails. The
   fixed system message is not part of the item. Polish is a
   gate, not a term in the score.
2. **Originality.** As above.
3. **Gold validity and diagnostic design.** One non-empty canonical string.
   Each submitted set must include, in its provenance declaration, a concise
   phenomenon description and a Polish contrast or controlled perturbation
   for each item cluster. A contrast changes the relevant Polish feature and
   predictably changes (or preserves, for a control) the gold. Reviewers use
   this only for qualification, not ranking, to reject format/tokenizer
   artefacts and linguistically unsupported golds. Extra equally good
   short forms belong in the item's `aliases` array. An accepted custom
   evaluator must accept the gold and must not key on particular models.
4. **Format.** The checks in `scripts/validate_format.py`.

Worked pass/fail rows:
[`development/qualification-rubric.md`](development/qualification-rubric.md).

## Ranking

Official ranks use the **hidden** Test B panel only. The development panel
is for your own checks and for optional unofficial feedback. Fitting the
published models is explicitly allowed: Test B measures whether this design
generalises to an unknown, family-disjoint panel. Fitting the development
panel is not the same as winning Test B.

Let $`n`$ be the number of items and $`m`$ the number of panel models.
Each item yields a bitvector of correct/incorrect outcomes. The official
score is the product of three components, each in $`[0, 1]`$:

$$
\mathrm{score} = \mathrm{discrimination} \times \mathrm{diversity} \times \mathrm{pairwise\ separation}
$$

**Discrimination.** For item $`i`$, let $`p_i`$ be the fraction of the
panel that is correct. Per-item discrimination is $`4 p_i (1-p_i)`$: 1
when the panel splits evenly, 0 when every model is right or every model
is wrong. The submission’s discrimination is the mean over items. There
is no separate difficulty term.

**Behavioural diversity.** Let $`c_v`$ be the number of items with
correctness bitvector $`v`$. Raw diversity is Simpson diversity,
$`1-\sum_v(c_v/n)^2`$. It is divided by its attainable maximum when the
$`\min(n,2^m)`$ possible observed bitvectors are used as evenly as possible.
Thus reported diversity lies in $`[0,1]`$. Repeating one outcome cut lowers
the score even if every model is correct on half the items; distinct cuts
with balanced frequencies score highest. Diversity is computed only from
correctness outcomes. Declared tags are not used.

**Harmonic pairwise separation.** For every pair of models, $`r_{kl}`$ is
the fraction of items on which they disagree. With saturation $`t = 5\%`$,
credit is $`s_{kl} = \min(r_{kl}/t, 1)`$, floored at $`\varepsilon = 0.01`$
so one unseparated pair does not zero the term. Separation is the
harmonic mean of these credits. Weakly separated pairs pull it down more
than an arithmetic mean would. This term, not an $`n/200`$ factor, is what
makes a short set harder.

Reference implementation: `scripts/compute_metric.py`.

## Models

Only open-weight models, run locally by the organisers. No API and no
closed models. Parameter-size cap: **40B**.

Development panel (published; commit hashes are pinned at the Test A
release):

| Model ID | Role | Parameters |
| --- | --- | ---: |
| `speakleash/Bielik-11B-v3.0-Instruct` | Polish-focused | 11B |
| `CYFRAGOVPL/PLLuM-12B-instruct-2512` | Polish-focused | 12B |
| `meta-llama/Llama-3.1-8B-Instruct` | multilingual baseline | 8B |
| `Qwen/Qwen2.5-7B-Instruct` | multilingual baseline | 7B |
| `mistralai/Mistral-Nemo-Instruct-2407` | multilingual baseline | 12B |
| `google/gemma-3-12b-it` | multilingual baseline | 12B |

The Test B panel is hidden, uses different models, and may be larger, up
to the 40B cap.

### Unofficial feedback

13 October – 30 November 2026: at most **one** organiser batch run of the
development panel per team per ISO week (Monday–Sunday, `Europe/Warsaw`). Manual, not
an API. Request template:
[`development/feedback-request-template.md`](development/feedback-request-template.md).
The report is an unofficial score on the published panel. It is not the
leaderboard.

## Track 2 — generator repository

Submit a repository URL pointing to a specific commit hash or tag through
the PolEval platform. The referenced revision must be accessible to organisers
and contain the complete submission. For a private repository, grant the user
`djstrong` read access. Organisers resolve a tag to a commit when accepting
the submission. The tree must implement `generate(seed) → n` items, $`50 \le n \le 200`$, same
`input`/`gold` schema, documented as:

```bash
python generate.py --seed N --out items.jsonl
```

The run is deterministic given `seed`, **offline**, and must finish within
**120 seconds**. Randomness may depend only on `seed`. Organisers execute
generators only in a hermetic sandbox: no network, read-only submission
tree, an isolated writable output directory, and CPU, memory, process, and
wall-clock limits.

Any lexicon or other database the generator needs — morphological forms,
for example — must be **inside the repository at that commit** (SQLite, TSV, or similar),
with a content hash in the README. Generation samples that snapshot. It
does not download data or call a network service. Python dependencies are
pinned and installable from the checked-out repository before the network is cut. If the
data licence forbids shipping a snapshot, Track 2 is unavailable: submit a
frozen Track 1 JSONL instead.

```text
generate.py
data/                 # vendored snapshot
vendor/               # optional wheels
requirements.txt
README.md
LICENSE               # OSI-approved, so organisers can rerun the code
data/LICENSE          # redistributable with the repository
```

Generated items follow the same publication licence as Track 1.

At Test B, organisers draw $`K = 3`$ hidden seeds, materialise three sets,
score each with the Track 1 metric, and rank by the mean. The worst-seed
score is also published. Unofficial development feedback, if offered, uses
one seed only and is not the rank.

The seed must change the benchmark. If any two materialised `input` sets
have Jaccard overlap above **0.5**, the generator is treated as a static
Track 1 list and is disqualified from Track 2. That does not affect a
team’s Track 1 standing. A non-deterministic run, a timeout, or a network
call is the same Track 2 disqualification.

```bash
python scripts/check_generator_seeds.py \
  --sets seed0.jsonl seed1.jsonl seed2.jsonl
```

Worked (invalid) example: `example-submission/track-2/`. It multiplies
integers, so it fails Polish necessity on purpose.

## Licence

Items must be redistributable (proposed: CC BY 4.0). Submissions that
cannot be published will not be ranked. The campaign artefact is the union
of qualified submissions, for later evaluation of Polish and multilingual
open-weight models.

## Repository map

All public files are linked below. Arithmetic examples are pipeline smoke
tests and do not qualify as linguistic submissions.

### Participant guides

- [development/README.md](development/README.md) — Submission and feedback procedure.
- [development/params.md](development/params.md) — Official limits.
- [development/qualification-rubric.md](development/qualification-rubric.md) — Qualification rules and examples.
- [development/provenance-template.md](development/provenance-template.md) — Provenance template.
- [development/feedback-request-template.md](development/feedback-request-template.md) — Feedback request template.
- [development/spreadsheet-guide.md](development/spreadsheet-guide.md) — Spreadsheet submission guide.
- [development-models.md](development-models.md) — Development panel description.
- [development/models.txt](development/models.txt) — Development model IDs.

### Evaluation scripts

- [scripts/validate_format.py](scripts/validate_format.py) — Validate items.jsonl.
- [scripts/query_models.py](scripts/query_models.py) — Query models.
- [scripts/evaluate_responses.py](scripts/evaluate_responses.py) — Mark model responses.
- [scripts/compute_metric.py](scripts/compute_metric.py) — Compute the score.
- [scripts/check_generator_seeds.py](scripts/check_generator_seeds.py) — Check generator seed variation.
- [scripts/sheet_export_to_jsonl.py](scripts/sheet_export_to_jsonl.py) — Convert spreadsheet exports to JSONL.
- [scripts/aliases_evaluator.py](scripts/aliases_evaluator.py) — Official aliases checker.
- [scripts/example_evaluator.py](scripts/example_evaluator.py) — Custom evaluator example.
- [scripts/common.py](scripts/common.py) — Shared loading, prompts and normalisation.
- [scripts/task_params.py](scripts/task_params.py) — Script parameters.
- [scripts/requirements.txt](scripts/requirements.txt) — Python dependencies.
- [scripts/tests/test_json_pipeline.py](scripts/tests/test_json_pipeline.py) — Pipeline regression tests.

### Sample items and responses

- [scripts/examples/sample_items.jsonl](scripts/examples/sample_items.jsonl) — Sample items with aliases.
- [scripts/examples/responses/model-a.jsonl](scripts/examples/responses/model-a.jsonl) — Synthetic model A responses.
- [scripts/examples/responses/model-b.jsonl](scripts/examples/responses/model-b.jsonl) — Synthetic model B responses.
- [scripts/examples/responses/model-c.jsonl](scripts/examples/responses/model-c.jsonl) — Synthetic model C responses.
- [scripts/examples/multiply_generator.py](scripts/examples/multiply_generator.py) — Example generator wrapper.

### Example submission

- [example-submission/README.md](example-submission/README.md) — Example submission instructions.
- [example-submission/provenance.md](example-submission/provenance.md) — Example provenance.
- [example-submission/track-1/items.jsonl](example-submission/track-1/items.jsonl) — Track 1 item set.
- [example-submission/track-2/README.md](example-submission/track-2/README.md) — Track 2 instructions.
- [example-submission/track-2/generate.py](example-submission/track-2/generate.py) — Track 2 generator.
- [example-submission/track-2/LICENSE](example-submission/track-2/LICENSE) — Generator licence.

### Local configuration

- [.env.example](.env.example) — Endpoint configuration template.
- [.gitignore](.gitignore) — Credentials and generated-file exclusions.

## Local scoring scripts

Python 3.10+ and `requests` (`scripts/requirements.txt`). Credentials for
your own endpoint go in `.env` (`EVAL_BASE_URL`, `EVAL_API_KEY`); see
`.env.example`. The scripts apply the official prompts and greedy decoding.
They are for local development. Test B is computed by the organisers on
the hidden panel.

```bash
python scripts/query_models.py \
  --items items.jsonl \
  --models-file development/models.txt \
  --output-dir responses

python scripts/evaluate_responses.py \
  --items items.jsonl \
  --responses-dir responses \
  --output correctness_matrix.json

python scripts/compute_metric.py \
  --matrix correctness_matrix.json \
  --per-item --per-pair
```

Omit `aliases` from each item for exact match. `--evaluator path/to/evaluator.py`
is the custom-code path; organisers still have to accept that file before
Test B.

Bundled synthetic responses (three placeholder models, not the development
panel):

```bash
python scripts/evaluate_responses.py \
  --items scripts/examples/sample_items.jsonl \
  --responses-dir scripts/examples/responses \
  --output /tmp/reverse-poleval-example.json

python scripts/compute_metric.py \
  --matrix /tmp/reverse-poleval-example.json \
  --per-item --per-pair
```
