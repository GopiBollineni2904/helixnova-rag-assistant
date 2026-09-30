# CLAUDE.md - Project Development Rules

These rules apply to all development work on the HelixNova Pharma RAG Assistant.

## Keep it simple
- Keep the RAG application beginner-friendly: clear names, short functions, plain comments.
- Keep most application logic inside `app.py`. Do not split it into a package.
- Do not add unnecessary frameworks or complexity (no LangChain, LlamaIndex, databases, or extra UI libraries).
- Keep error messages simple and readable for a non-technical user.

## Secrets
- Never hardcode API keys, tokens, or passwords anywhere in source.
- Always read `ANTHROPIC_API_KEY` from the environment (`.env` locally via python-dotenv) or from `st.secrets` on Streamlit Community Cloud.
- Never print or log the key's value.
- `.env` and `.streamlit/secrets.toml` must stay in `.gitignore` and must never be committed.

## RAG behaviour
- Support both PDF (via pypdf) and TXT uploads.
- Always chunk text before embedding.
- Embed with sentence-transformers and store vectors in FAISS.
- Always retrieve relevant chunks before calling Claude.
- Send Claude only the retrieved chunks and the question, never the whole document.
- Claude answers only from the retrieved context, never from general knowledge.
- If the answer is not found in the retrieved context, return exactly:
  `I could not find enough information in the uploaded document.`
- Every answer shows its sources as file name + chunk number.

## Session
- Chat history lives in `st.session_state` for the current session only. No database, no files.

## Workflow
- Read `requirements.md` and `specification.md` before changing behaviour.
- Fix only the affected code when something breaks; don't redesign.
- Keep `requirements.txt` in sync with every directly imported package.
- Use relative paths only. No absolute local file paths in source.
