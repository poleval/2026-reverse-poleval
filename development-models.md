# Reverse PolEval — development panel

The Test A development panel contains the following six open-weight instruct
models. Their Hugging Face commit hashes and the inference image digest are
frozen and published with Test A, before the development period begins.

| Model ID | Role in panel | Parameters |
| --- | --- | ---: |
| `speakleash/Bielik-11B-v3.0-Instruct` | Polish-focused | 11B |
| `CYFRAGOVPL/PLLuM-12B-instruct-2512` | Polish-focused | 12B |
| `meta-llama/Llama-3.1-8B-Instruct` | multilingual baseline | 8B |
| `Qwen/Qwen2.5-7B-Instruct` | multilingual baseline | 7B |
| `mistralai/Mistral-Nemo-Instruct-2407` | multilingual baseline | 12B |
| `google/gemma-3-12b-it` | multilingual baseline | 12B |

All runs use each model's released chat template, the fixed official system
message and unmodified `input` as the user message, as specified in `README.md`, greedy decoding
(`temperature=0`), `max_new_tokens=64`, and the same inference engine
configuration. Organisers must pin each repository to an immutable commit
hash before publishing Test A; a moving branch such as `main` is not an
official model identifier.

This is the development panel only. The Test B panel is hidden, consists of
different models, and may be larger, up to the 40B parameter-size cap
(`development/params.md`).
