"""QA helper: runs the helper functions from app.py (everything above the UI section)
against the sample dataset, without starting the Streamlit UI."""

import sys
import warnings

warnings.filterwarnings("ignore")

src = open("app.py", encoding="utf-8").read().split("# ---------------- UI")[0]
ns = {}
exec(src, ns)


class Upload:
    def __init__(self, path):
        self.name = path.split("/")[-1]
        self._data = open(path, "rb").read()

    def getvalue(self):
        return self._data


QUESTIONS = [
    "How quickly must a Critical deviation be reported?",
    "What is the target timeline for completing a deviation investigation?",
    "Who can approve final batch release?",
    "What happens if a vaccine shipment is outside the approved temperature range?",
    "How quickly must a potential product recall be escalated?",
    "What is the difference between a correction and a CAPA?",
    "When is formal change control required?",
    "What are the data-integrity expectations for electronic records?",
    "How long must completed training records be retained?",
    "What should the assistant say if the policy does not contain the answer?",
]
UNSUPPORTED = [
    "What is the CEO's salary?",
    "What is the capital of France?",
]

if __name__ == "__main__":
    path = sys.argv[1]
    questions = QUESTIONS + UNSUPPORTED if len(sys.argv) < 3 else sys.argv[2:]
    up = Upload(path)
    text = ns["extract_text"](up)
    chunks = ns["chunk_text"](text, up.name)
    index = ns["build_index"](chunks)
    print(f"FILE {up.name} | chars={len(text)} | chunks={len(chunks)} | index.ntotal={index.ntotal}")
    for q in questions:
        results = ns["retrieve"](q, index, chunks)
        answer = ns["ask_claude"](q, results)
        print("=" * 80)
        print("Q:", q)
        print("A:", answer)
        print("SOURCES:", ", ".join(f"{r['file_name']} - Chunk {r['chunk_number']}" for r in results))
