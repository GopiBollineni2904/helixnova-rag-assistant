"""Enterprise Document RAG Assistant.

Upload a PDF or TXT policy document and ask questions about it.
Flow: Upload -> Extract -> Chunk -> Embed -> FAISS -> Ask -> Retrieve -> Claude -> Answer
"""

import io
import os

import anthropic
import faiss
import numpy as np
import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

# ---------------- Settings ----------------
CHUNK_SIZE = 800          # characters per chunk
CHUNK_OVERLAP = 100       # characters shared between neighbouring chunks
TOP_K = 4                 # number of chunks sent to Claude
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CLAUDE_MODEL = "claude-opus-5"
FALLBACK = "I could not find enough information in the uploaded document."

SYSTEM_PROMPT = f"""You are a policy assistant. Answer the user's question using ONLY the context chunks provided.
Rules:
- Use only facts stated in the context. Do not use outside knowledge and do not guess.
- If the context does not contain enough information to answer, reply with exactly this sentence and nothing else:
{FALLBACK}
- Keep the answer concise and factual."""

load_dotenv()  # reads ANTHROPIC_API_KEY from a local .env file, if present


# ---------------- Helpers ----------------
def get_api_key():
    """Streamlit Cloud secrets first, then the environment (.env locally)."""
    try:
        if "ANTHROPIC_API_KEY" in st.secrets:
            return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        pass  # no secrets.toml locally - that's fine
    return os.environ.get("ANTHROPIC_API_KEY")


@st.cache_resource
def load_embedding_model():
    return SentenceTransformer(EMBEDDING_MODEL)


def extract_text(uploaded_file):
    data = uploaded_file.getvalue()
    if uploaded_file.name.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return data.decode("utf-8", errors="replace")


def chunk_text(text, file_name):
    """Split text into overlapping chunks, remembering file name and chunk number."""
    chunks = []
    step = CHUNK_SIZE - CHUNK_OVERLAP
    for start in range(0, len(text), step):
        piece = text[start:start + CHUNK_SIZE].strip()
        if piece:
            chunks.append({
                "file_name": file_name,
                "chunk_number": len(chunks) + 1,
                "text": piece,
            })
        if start + CHUNK_SIZE >= len(text):
            break
    return chunks


def embed(texts):
    model = load_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype="float32")


def build_index(chunks):
    vectors = embed([c["text"] for c in chunks])
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(vectors)
    return index


def retrieve(question, index, chunks):
    query = embed([question])
    k = min(TOP_K, len(chunks))
    _, ids = index.search(query, k)
    return [chunks[i] for i in ids[0] if i != -1]


def ask_claude(question, context_chunks):
    context = "\n\n".join(
        f"[Source: {c['file_name']} - Chunk {c['chunk_number']}]\n{c['text']}"
        for c in context_chunks
    )
    client = anthropic.Anthropic(api_key=get_api_key())
    response = client.beta.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=16000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}",
        }],
    )
    if response.stop_reason == "refusal":
        return FALLBACK
    answer = "".join(b.text for b in response.content if b.type == "text").strip()
    # Keep the fallback wording exact if Claude adds extra words around it
    if FALLBACK.lower().rstrip(".") in answer.lower():
        return FALLBACK
    return answer or FALLBACK


# ---------------- UI ----------------
st.set_page_config(page_title="Enterprise Document RAG Assistant")
st.title("Enterprise Document RAG Assistant")

if not get_api_key():
    st.error("ANTHROPIC_API_KEY is not set. Add it to .env locally or to Streamlit secrets in the cloud.")
    st.stop()

# Section 1 - Upload Document
st.header("1. Upload Document")
uploaded = st.file_uploader("Upload a PDF or TXT policy document", type=["pdf", "txt"])

if uploaded is not None:
    file_id = (uploaded.name, uploaded.size)
    if st.session_state.get("file_id") != file_id:
        try:
            text = extract_text(uploaded)
        except Exception:
            st.error("Could not read this PDF. Please upload a valid PDF or TXT file.")
            st.stop()
        if not text.strip():
            st.error("No text could be extracted from this document.")
            st.stop()
        with st.spinner("Chunking and embedding the document..."):
            chunks = chunk_text(text, uploaded.name)
            st.session_state.index = build_index(chunks)
        st.session_state.chunks = chunks
        st.session_state.char_count = len(text)
        st.session_state.file_id = file_id
        st.session_state.messages = []  # old answers belong to the old document

    st.write(f"Extracted characters: **{st.session_state.char_count:,}**")
    st.write(f"Chunks created: **{len(st.session_state.chunks)}**")
    st.success("Document processed and stored in FAISS.")

# Section 2 - Ask Your Document
st.header("2. Ask Your Document")
if "index" not in st.session_state:
    st.info("Upload a document first.")
    st.stop()

def show_sources(sources):
    with st.expander("View retrieved source chunks"):
        for c in sources:
            st.markdown(f"**{c['file_name']} - Chunk {c['chunk_number']}**")
            st.text(c["text"])
            st.divider()
    st.markdown("**Sources used:**")
    for c in sources:
        st.markdown(f"- {c['file_name']} - Chunk {c['chunk_number']}")


# Chat history lives only in this browser session
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            show_sources(msg["sources"])

question = st.chat_input("Ask a question about the document")
if question and question.strip():
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        results = retrieve(question, st.session_state.index, st.session_state.chunks)
        with st.spinner("Asking Claude..."):
            try:
                answer = ask_claude(question, results)
            except anthropic.APIError as e:
                st.error(f"Claude API error: {getattr(e, 'message', e)}. Please try again.")
                st.stop()
        st.markdown(answer)
        show_sources(results)
    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": results}
    )
