# Specification - Enterprise Document RAG Assistant

Based on `requirements.md` and `CLAUDE.md`. This document defines *how* the app works; it contains no code.

## 1. Architecture overview

A single Streamlit app (`app.py`) runs the whole pipeline in memory. Nothing is written to disk and there is no database.

```
Document Upload -> Text Extraction -> Chunking -> Embeddings -> FAISS Vector Store
                                                                     |
User Question -> Question Embedding -> Similarity Search <-----------+
                                            |
                                  Relevant Context (top 4 chunks)
                                            |
                                         Claude
                                            |
                                  Answer + Sources used
```

## 2. Defaults

| Setting | Value |
|---------|-------|
| Supported file types | `.pdf`, `.txt` |
| Chunk size | ~800 characters |
| Chunk overlap | ~100 characters |
| Top-k chunks retrieved | 4 |
| Embedding model | `all-MiniLM-L6-v2` (sentence-transformers, 384 dimensions, runs on CPU) |
| Vector index | FAISS `IndexFlatL2` on normalized embeddings (exact search) |
| LLM | Anthropic Claude, model `claude-opus-5` |
| Fallback text | `I could not find enough information in the uploaded document.` |

## 3. Pipeline steps

### 3.1 Document Upload
- `st.file_uploader` accepts one file of type `pdf` or `txt`.
- The uploaded file is read from memory. No local file paths are used.

### 3.2 Text Extraction
- **PDF:** `pypdf.PdfReader` reads each page; page texts are joined with newlines.
- **TXT:** bytes are decoded as UTF-8 (undecodable bytes are replaced, not fatal).
- The app shows the extracted character count.
- If no text is extracted (e.g. a scanned PDF), the app shows a simple error and stops.

### 3.3 Chunking
- Fixed-size character windows: each chunk is up to 800 characters, and each new chunk starts 700 characters after the previous one (100 characters of overlap).
- Empty or whitespace-only chunks are skipped.
- Each chunk records: `file_name`, `chunk_number` (1-based), and `text`.
- The app shows the chunk count.

### 3.4 Embeddings
- The sentence-transformers model is loaded once and cached (`st.cache_resource`).
- All chunk texts are embedded in one batch as float32 vectors, normalized.

### 3.5 FAISS Vector Store
- A FAISS index is built from the chunk embeddings.
- The index and chunk list are stored in `st.session_state` so they survive Streamlit reruns.
- The index is rebuilt only when a different file is uploaded.

### 3.6 User Question
- The user types a question into `st.chat_input` (see section 5).

### 3.7 Similarity Search
- The question is embedded with the same model and normalized.
- FAISS returns the top 4 nearest chunks (fewer if the document has fewer than 4 chunks).

### 3.8 Relevant Context
- The retrieved chunks are formatted as labelled blocks, each tagged with its file name and chunk number.
- Only these chunks and the question are sent to Claude. The full document never is.

### 3.9 Claude
- **System prompt rules:**
  - Answer only from the provided context; do not use outside knowledge.
  - If the context does not contain the answer, reply with exactly the fallback text and nothing else.
  - Keep answers concise and factual.
- **User message:** the labelled context blocks followed by the question.
- One API call per question. Earlier chat turns are **not** sent to Claude, so every answer is grounded only in the chunks retrieved for that question.

### 3.10 Answer
- The answer text is displayed in the chat.
- Below it: **"Sources used:"** followed by one line per retrieved chunk, as `file name - Chunk N`.
- An expander ("View retrieved source chunks") shows the full text of each retrieved chunk.
- If Claude returns the fallback text, the sources list is still shown so the user can see what was searched.

## 4. API key handling
1. Try `st.secrets["ANTHROPIC_API_KEY"]` (Streamlit Community Cloud).
2. Otherwise read `os.environ["ANTHROPIC_API_KEY"]`, loaded from `.env` via python-dotenv when running locally.
3. If neither is set, show: "ANTHROPIC_API_KEY is not set. Add it to .env locally or to Streamlit secrets in the cloud." and stop.
- The key is never displayed, logged, or hardcoded.

## 5. UI layout
- **Title:** "Enterprise Document RAG Assistant"
- **Section 1 - Upload Document:** file uploader, extracted character count, chunk count, success message.
- **Section 2 - Ask Your Document:**
  - Previous turns are replayed with `st.chat_message("user")` / `st.chat_message("assistant")`, including each answer's sources.
  - `st.chat_input` for new questions. It appears only after a document has been processed.
- **Session state keys:** `chunks`, `index`, `file_id`, `messages` (list of `{role, content, sources}`).
- Chat history lasts for the current browser session only. Uploading a new document clears it, because old answers refer to the old document.

## 6. Error handling (simple messages)
| Situation | Message |
|-----------|---------|
| Missing API key | "ANTHROPIC_API_KEY is not set..." |
| Unreadable PDF | "Could not read this PDF. Please upload a valid PDF or TXT file." |
| No text extracted | "No text could be extracted from this document." |
| Claude API error | "Claude API error: <short reason>. Please try again." |

## 7. Files
| File | Purpose |
|------|---------|
| `app.py` | Entire application (entry point) |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Excludes secrets, virtual envs, caches |
| `requirements.md` | Requirements |
| `CLAUDE.md` | Development rules |
| `specification.md` | This document |
| `QA_RESULTS.md` | QA test results |
| `data/` | Sample policy document (PDF + TXT) |

## 8. Deployment (Streamlit Community Cloud)
- Entry point: `app.py`.
- Secrets: `ANTHROPIC_API_KEY` set in the app's Secrets settings (available as `st.secrets`).
- All direct imports are listed in `requirements.txt`; `faiss-cpu` provides FAISS.
