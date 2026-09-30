# QA Results - Enterprise Document RAG Assistant

**Date:** 30 September 2026
**Build tested:** `app.py` (model `claude-opus-5`, `all-MiniLM-L6-v2` embeddings, FAISS `IndexFlatL2`, chunk 800 / overlap 100, top-k 4)
**Test data:** `data/helixnova_pharma_quality_policy_dataset.pdf` and `.txt`

## How it was tested

| Script | What it does |
|--------|--------------|
| `qa_ui_test.py` | Drives the real `app.py` UI with Streamlit's `AppTest`: uploads the PDF and TXT through `st.file_uploader`, asks questions through `st.chat_input`, and checks the rendered page. |
| `qa_check.py` | Runs the pipeline functions from `app.py` (extract -> chunk -> embed -> FAISS -> retrieve -> Claude) for all 10 suggested questions plus 2 off-topic questions, on both files. |

Run with: `python qa_ui_test.py` and `python qa_check.py data/<file>`.

## 1. Functional checks

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | PDF upload works | **PASS** | PDF uploaded via `st.file_uploader`, no errors |
| 2 | TXT upload works | **PASS** | TXT uploaded via `st.file_uploader`, no errors |
| 3 | Text extraction works | **PASS** | PDF: 15,311 characters; TXT: 15,460 characters (difference is PDF layout whitespace) |
| 4 | Chunking works | **PASS** | 22 chunks for each file, numbered 1-22 |
| 5 | Embeddings are created | **PASS** | 22 vectors x 384 dimensions |
| 6 | FAISS retrieval works | **PASS** | `index.ntotal = 22`; top 4 chunks returned per question, and the relevant section is in them for all 10 questions |
| 7 | Relevant chunks are sent to Claude | **PASS** | Prompt contains only the 4 retrieved chunks, labelled `[Source: <file> - Chunk N]` |
| 8 | Claude answers from document context | **PASS** | All 10 policy answers match the policy text (see section 2) |
| 9 | Unsupported questions return the fallback | **PASS** | "What is the CEO's salary?" and "What is the capital of France?" both returned exactly: *I could not find enough information in the uploaded document.* |
| 10 | API keys are not hardcoded | **PASS** | Key read from `st.secrets` or `os.environ` (via `.env`); no key string in any source file |

Extra UI checks (all **PASS**): the title "Enterprise Document RAG Assistant" is shown; the chat input is hidden until a document is processed; "Sources used:" shows file name + chunk number; source-chunk expanders render; earlier questions and answers stay visible after a new question; history resets when a different document is uploaded; a missing API key shows a simple error.

## 2. Suggested test questions (PDF)

| # | Question | Assistant answer (summary of actual output) | Sources used | Correct? |
|---|----------|---------------------------------------------|--------------|----------|
| 1 | How quickly must a Critical deviation be reported? | "Critical deviations must be reported to the Site Quality Head within **30 minutes of discovery**." | pdf - Chunks 3, 21, 10, 20 | Yes (s2.2) |
| 2 | What is the target timeline for completing a deviation investigation? | Normally within 15 calendar days; an extension needs a documented reason and QA approval; no deviation may stay open beyond 30 calendar days without written approval from the Site Quality Head. | pdf - Chunks 3, 4, 5, 21 | Yes (s2.3) |
| 3 | Who can approve final batch release? | Only an authorized QA release approver. Manufacturing, QC, Supply Chain, or Commercial may recommend release readiness but cannot independently release. | pdf - Chunks 6, 7, 5, 1 | Yes (s4.1) |
| 4 | What happens if a vaccine shipment is outside the approved temperature range? | It is a temperature excursion (standard refrigerated range 2-8 C unless the label or stability protocol says otherwise); not automatic destruction; quality hold until an authorized assessment; notify Site QA within 1 hour (commercial batch) and Global Quality Operations within 2 hours (distributed product); disposition uses stability data, duration, etc.; only QA may approve return to inventory. | pdf - Chunks 7, 8, 9, 6 | Yes (s5) - see note A |
| 5 | How quickly must a potential product recall be escalated? | To the Global Recall Committee within 1 hour of confirmation of a credible distributed-product risk; don't delay escalation while waiting for complete information if serious patient-safety risk can't be excluded. | pdf - Chunks 11, 20, 12, 22 | Yes (s8.2) |
| 6 | What is the difference between a correction and a CAPA? | A correction fixes the immediate observed problem; a Corrective Action addresses the root cause to prevent recurrence; a Preventive Action addresses a potential cause before it occurs. Also noted CAPA timings (owner in 2 business days, 60-day target, effectiveness check). | pdf - Chunks 4, 5, 2, 6 | Yes (s3.1, s3.3) |
| 7 | When is formal change control required? | Before changes that may affect: validated processes, specifications, analytical methods, critical equipment, GxP computerized systems, critical-material suppliers, labeling, packaging, storage conditions, regulatory commitments. Also noted the emergency-change exception (formal entry within 1 business day). | pdf - Chunks 9, 8, 17, 22 | Yes (s6.1, s6.2) |
| 8 | What are the data-integrity expectations for electronic records? | No shared accounts; records preserve identity + date/time of action; audit trails enabled and not disabled; data must be attributable, legible, contemporaneous, original, accurate, complete, consistent, enduring, available; corrections traceable (what/who/when/why); no deleting/overwriting to hide errors. | pdf - Chunks 14, 13, 19, 16 | Yes (s10) |
| 9 | How long must completed training records be retained? | "At least 7 years after completion, unless a longer legal or product-specific requirement applies." | pdf - Chunks 19, 15, 20, 22 | Yes (s11.3, s16) |
| 10 | What should the assistant say if the policy does not contain the answer? | It should state that it could not find enough information in the document rather than inventing an answer (s15.3); the employee remains responsible for verifying decisions (s15.4). | pdf - Chunks 18, 19, 22, 17 | Yes (s15.3) |

**TXT path:** the same 10 questions were run against the `.txt` file. All answers matched the PDF results in content, with sources labelled `helixnova_pharma_quality_policy_dataset.txt - Chunk N`, and both off-topic questions returned the exact fallback.

## 3. Notes (not defects)

- **A. Q4 "vaccine":** the policy never mentions vaccines; it covers "products labeled for refrigerated storage". The assistant applied those rules and hedged with "unless the product-specific label or stability protocol states otherwise". That is grounded, not invented.
- **B. PDF bullets:** pypdf extracts the PDF's bullet glyphs as a control character (`\x7f`), which shows up in the "View retrieved source chunks" expander for the PDF. It has no effect on retrieval or answers. Left as is (cosmetic).

## 4. Defects found and fixed

None. No code changes were needed during QA.

## 5. Acceptance criteria

| Criterion | Result |
|-----------|--------|
| PDF and TXT both work | PASS |
| At least one policy question answered correctly with source chunks | PASS (10/10) |
| Unsupported questions return the agreed fallback | PASS |
| No API key is hardcoded | PASS |
| Sources show file name + chunk number | PASS |
| Previous questions/answers remain visible during the session | PASS |
| Can be prepared for Streamlit Community Cloud without changing business functionality | PASS (see deployment check) |
