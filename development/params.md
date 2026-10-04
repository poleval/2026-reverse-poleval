# Frozen Test A parameters

Binding from 13 October 2026 for the development period and for both
panels. Do not change these without republishing Test A.

| Parameter | Value | Used for |
| --- | --- | --- |
| *N* (Track 1 budget) | **50–200** | Format gate. The 50-item floor prevents a few panel-specific splits from determining the whole score |
| Max `input` characters | **2000** | Format gate |
| Max `gold` or alias characters | **80** | Format gate |
| Max inline aliases per item | **5** | Format gate |
| *K* (Track 2 hidden seeds) | **3** | Test B official ranking (mean; worst-seed also published) |
| *K*_dev (Track 2 feedback) | **1** | Unofficial development-panel runs only; not the rank |
| Max Jaccard overlap across Track 2 seeds | **0.5** | Seed-dependence gate (≥2 materialisations; no panel needed) |
| Track 2 per-seed wall-clock | **120 s** | Generator sandbox; exceeded run is Track 2 DQ |
| Pairwise saturation *t* | **5%** | Ranking |
| Pairwise harmonic floor *ε* | **0.01** | Ranking |
| Evaluator timeout | **5 s** per call | Sidecar sandbox |
| Case folding | **disabled** | Exact match and aliases on every official run |
| Qualification audit sample | **30** items | Rolling qualification |
| Decoding | **temperature 0**, `max_new_tokens=64` | All panel runs |
| Parameter-size cap | **40B** | Any model on either panel; the development list is smaller, the hidden Test B panel may use larger open-weight models up to this cap |
| Unofficial feedback | **1 batch run / team / ISO week** (Monday–Sunday, `Europe/Warsaw`) | Development period |

The six development-panel model IDs are listed in `models.txt` and
`../development-models.md`. Pin each ID to a commit hash before the first
public Test A announcement; until then the IDs are the intended
repositories, not frozen revisions.
