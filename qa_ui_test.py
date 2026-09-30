"""QA helper: drives the real app.py UI with Streamlit's AppTest (upload + chat)."""

import os

from streamlit.testing.v1 import AppTest

PDF = "data/helixnova_pharma_quality_policy_dataset.pdf"
TXT = "data/helixnova_pharma_quality_policy_dataset.txt"
FALLBACK = "I could not find enough information in the uploaded document."


def page_text(at):
    return "\n".join(m.value for m in at.markdown)


def check(name, ok):
    print(("PASS" if ok else "FAIL"), "-", name)


def upload(at, path, mime):
    with open(path, "rb") as f:
        at.file_uploader[0].set_value((os.path.basename(path), f.read(), mime)).run()


def ask(at, question):
    at.chat_input[0].set_value(question).run()


at = AppTest.from_file("app.py", default_timeout=300)
at.run()
check("title shown", at.title[0].value == "Enterprise Document RAG Assistant")
check("chat input hidden before upload", len(at.chat_input) == 0)

# PDF upload
upload(at, PDF, "application/pdf")
text = page_text(at)
check("PDF: character count shown", "Extracted characters" in text)
check("PDF: chunk count shown", "Chunks created" in text)
check("PDF: no errors", len(at.error) == 0)
print("   ", [m.value for m in at.markdown if "Extracted" in m.value or "Chunks" in m.value])

ask(at, "How quickly must a Critical deviation be reported?")
ask(at, "What is the capital of France?")
text = page_text(at)
chats = at.chat_message
check("PDF: 4 chat messages visible (2 Q + 2 A)", len(chats) == 4)
check("PDF: first answer mentions 30 minutes", "30 minutes" in text)
check("PDF: unsupported question returns exact fallback", FALLBACK in text)
check("PDF: 'Sources used:' shown", "**Sources used:**" in text)
check("PDF: sources show file name + chunk number",
      "- helixnova_pharma_quality_policy_dataset.pdf - Chunk " in text)
check("PDF: source chunk expanders present", len(at.expander) >= 2)
check("history: first question still visible after second",
      "How quickly must a Critical deviation be reported?" in text)

# TXT upload (new document clears old history)
upload(at, TXT, "text/plain")
text = page_text(at)
check("TXT: history cleared on new document", len(at.chat_message) == 0)
print("   ", [m.value for m in at.markdown if "Extracted" in m.value or "Chunks" in m.value])
ask(at, "How long must completed training records be retained?")
text = page_text(at)
check("TXT: answer mentions 7 years", "7 years" in text)
check("TXT: sources show .txt file name + chunk number",
      "- helixnova_pharma_quality_policy_dataset.txt - Chunk " in text)
check("TXT: no errors", len(at.error) == 0)

# Missing API key -> simple error
os.environ["ANTHROPIC_API_KEY"] = ""
at2 = AppTest.from_file("app.py", default_timeout=60)
at2.run()
check("missing key: simple error shown",
      len(at2.error) == 1 and "ANTHROPIC_API_KEY is not set" in at2.error[0].value)
