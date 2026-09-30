# Requirements - HelixNova Pharma Quality & Regulatory RAG Assistant

## 1. Background

HelixNova Pharma (fictional) is a global pharmaceutical manufacturer. Employees in manufacturing, quality, supply chain, pharmacovigilance, and regulatory teams need to interpret internal SOPs covering deviations, CAPA, batch release, cold-chain excursions, change control, complaints, recalls, audit trails, data integrity, training, supplier quality, and escalation timelines.

Today they search long policy documents by hand. This project delivers a simple, grounded RAG (Retrieval-Augmented Generation) assistant: a user uploads a policy document and asks questions in plain English.

## 2. Users

- Employees who need quick, sourced answers from an approved policy document.
- Trainers and reviewers who check that answers are grounded in the document.

## 3. Functional requirements

| ID | Requirement |
|----|-------------|
| FR-1 | The user can upload a policy document in **PDF** or **TXT** format. |
| FR-2 | The app extracts the text from the uploaded document. |
| FR-3 | The app splits the extracted text into chunks. |
| FR-4 | The app creates an embedding for each chunk with **sentence-transformers**. |
| FR-5 | The app stores the chunk embeddings in a **FAISS** vector index. |
| FR-6 | The user can ask a natural-language question about the document. |
| FR-7 | The app retrieves the top relevant chunks for the question from FAISS. |
| FR-8 | The app sends **only** the retrieved chunks (plus the question) to Claude. |
| FR-9 | Claude returns an answer grounded in the retrieved chunks only. |
| FR-10 | Each answer shows its evidence: **file name and chunk number** for every source chunk used. |
| FR-11 | If the answer is not in the retrieved context, the app returns this exact fallback: **"I could not find enough information in the uploaded document."** |
| FR-12 | Previous questions and answers stay visible for the current Streamlit session only (no database, no persistence across sessions). |

## 4. Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | **Tech stack:** Python, Streamlit, Anthropic Claude API, sentence-transformers, FAISS, pypdf. |
| NFR-2 | **Security:** no API key is hardcoded. `ANTHROPIC_API_KEY` is read from the environment locally (`.env`) and from `st.secrets` on Streamlit Community Cloud. |
| NFR-3 | **Simplicity:** beginner-friendly code; most logic lives in a single `app.py`; no unnecessary frameworks. |
| NFR-4 | **Error handling:** simple, readable error messages (e.g. missing API key, unreadable file, empty document). |
| NFR-5 | **Deployability:** the project runs on Streamlit Community Cloud without changing business functionality. `app.py` is the entry point and all direct dependencies are in `requirements.txt`. |
| NFR-6 | **Source control:** the project is GitHub-ready; secrets (`.env`, `.streamlit/secrets.toml`) are never committed. |

## 5. Core RAG flow

Upload -> Extract -> Chunk -> Embed -> FAISS -> Ask -> Retrieve -> Claude -> Answer + Sources

## 6. Acceptance criteria

1. PDF and TXT uploads both work.
2. At least one policy question is answered correctly with source chunks.
3. Unsupported questions return the agreed fallback.
4. No API key is hardcoded.
5. Sources show file name + chunk number.
6. Previous questions/answers remain visible during the current session.
7. The app can be prepared for Streamlit Community Cloud without changing business functionality.

## 7. Test questions (QA)

Run against `data/helixnova_pharma_quality_policy_dataset.pdf` (and confirm the `.txt` path separately):

1. How quickly must a Critical deviation be reported?
2. What is the target timeline for completing a deviation investigation?
3. Who can approve final batch release?
4. What happens if a vaccine shipment is outside the approved temperature range?
5. How quickly must a potential product recall be escalated?
6. What is the difference between a correction and a CAPA?
7. When is formal change control required?
8. What are the data-integrity expectations for electronic records?
9. How long must completed training records be retained?
10. What should the assistant say if the policy does not contain the answer?

## 8. Deliverables

`requirements.md`, `CLAUDE.md`, `specification.md`, `app.py`, `requirements.txt`, `.gitignore`, QA results, a GitHub-ready project, and a Streamlit Community Cloud-ready project.

## 9. Out of scope (optional extensions, only if time allows)

Multi-document retrieval, similarity score display, document-level filters, evaluation dataset with expected answers, RAG quality dashboard.

## 10. Data note

All company names, thresholds, and procedures in `data/` are synthetic training content. They are treated as real input for the pipeline but are not fact-checked against real regulations.
