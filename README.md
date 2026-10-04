# StudyMate Answers Questions from Course Notes

I built StudyMate to help a postgraduate learner locate evidence in supplied notes. It retrieves passages, returns a short answer with candidate source labels, or returns `not found`. Hosted mode uses rented embeddings and an LLM; offline mode uses TF-IDF and extractive answers. The current scope is English, text-based notes and study support.

## Run on another machine

Python 3.10 or later is required. From the extracted project directory:

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell alternative: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python tests/test_smoke.py
python tests/test_hosted_paths.py
python tests/test_evaluation_integrity.py
python scripts/run_evaluation.py --label my_diagnostic
python scripts/run_evaluation.py --questions blind_questions.csv --label my_blind
python scripts/audit_evaluation.py
streamlit run app.py
```

Use a new result label each time; the evaluation now refuses to overwrite existing records unless you supply `--overwrite`. The PDF files are included; you do not need to rebuild them to run the app. `scripts/build_public_pdfs.py` additionally needs reportlab only if you regenerate PDFs from Markdown. No key is needed for offline tests.

For hosted use, copy `.env.example` to `.env` and set `OPENAI_API_KEY` or `OPENROUTER_API_KEY`. The model defaults are `gpt-4o-mini` and `text-embedding-3-small`, automatically prefixed with `openai/` for OpenRouter. Do not upload `.env`. Tick the hosted checkbox in the app. Questions and source text are sent to the configured provider; this is not an entirely local path.

## Data and evaluation

The project data comprises three notes, three one-page PDFs and recorded model outputs. The source inventory contains filenames, page counts, permission information and hashes. I wrote 20 diagnostic questions. A classmate who had not seen the index wrote 10 blind questions. See `evals/blind_provenance.md`.

Historical hosted RAG scores are 17/20 diagnostic and 8/10 blind; the keyword excerpt baseline scores 6/20 and 3/10. These are literal answer-anchor AND expected-source matches, not independently reviewed semantic accuracy. Both sets and both systems are reported separately. The 30 hosted questions have a calculated token cost of US$0.00274184. Pricing is historical/configured, not a current quotation or provider bill.

## Architecture and scope

```text
PDF notes -> page chunks -> TF-IDF or hosted embeddings -> evidence threshold
Question -> credential policy check ---------------------> retrieval
                                      low score -> not found
                                      otherwise -> extractive answer or hosted LLM
                                                -> answer + candidate sources + excerpts
```

Rules handle file loading, credential refusal, thresholds, logging and exact scoring. The LLM only generates an answer from retrieved excerpts. There is no agent, tool execution or model-based judge. Citations list retrieved candidates and do not prove claim-level support. The interface now exposes the full excerpts for inspection.

## Submission contents

- The final report is submitted separately through the course submission system.
- [Product documentation](docs/product_documentation.md): persona, inputs, outputs, architecture, targeted and reached metrics.
- [Design decisions](docs/design_decisions.md) and [evaluation critique](docs/evaluation_review.md).
- [Data explanation](data/README.md), source notes, PDFs, licence and source inventory in `data/`.
- [Evaluation explanation](evals/README.md), diagnostic questions, independently authored blind questions and developer safety checks in `evals/`.
- `results/`: original evaluation outputs, token cost logs, and analyses supporting the report.
- `app.py`, `src/`, `scripts/`, `tests/`, and `requirements.txt`: documented application code, evaluation tools and checks.

The actual face-and-screen demonstration video is not included. Record the planned six-minute demonstration and submit the video according to the course upload instructions. The instructor allows two to eight minutes. Written scripts are not a substitute for this video.

## Repository upload

Upload the contents of this folder so that `README.md`, `app.py`, `src/`, `data/` and `evals/` are at the repository root. Include `.gitignore` and `.env.example`. Do not include a local `.env`, credentials, or `.venv`.
