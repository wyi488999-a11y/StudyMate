# Data statement

I use the supplied real project data: three source notes with their PDF versions and recorded evaluation outputs. `sample_notes/` contains the Markdown sources. `public_pdfs/` contains three one-page text PDFs indexed as three chunks. `source_inventory.csv` lists their filenames, page counts, SHA-256 hashes and the permission recorded in the included CC0 licence.

The collection covers retrieval augmented generation, evaluation and responsible use. It supports note-grounded question answering, not measurement of student learning gains or broad course coverage. No student identities are included. Any additional source requires a recorded permission decision before redistribution.

The loader supports `.md`, `.txt` and text-based `.pdf` files; PDF loading requires `pypdf`. It splits PDFs by page and does not perform OCR. English tokenisation limits the offline path's suitability for Chinese notes.

I wrote 20 diagnostic questions. A classmate who had not seen the index wrote the separate 10-question blind set. See `evals/blind_provenance.md` for the provenance record.
