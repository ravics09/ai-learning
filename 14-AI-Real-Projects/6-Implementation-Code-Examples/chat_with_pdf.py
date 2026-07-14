"""
chat_with_pdf.py — the ONLINE half of a Chat-with-your-PDF RAG app.

WHY this design:
    This is the query path an interviewer will grill you on. It shows the full
    RAG loop in ~150 readable lines: embed the question, retrieve the top-k
    chunks, build a grounded prompt WITH citations, and instruct the model to
    answer only from the retrieved context (and say "I don't know" otherwise).
    Those two habits — citing sources and refusing when context is missing —
    are what separate a trustworthy RAG app from a hallucination machine.

Two ways to run:
    1) CLI:   python chat_with_pdf.py "What is the refund policy?"
    2) UI:    streamlit run chat_with_pdf.py      (a reviewer can click around)

Prerequisite: run `python ingest.py your.pdf` first to build the index.
"""

from __future__ import annotations

import os
import sys
import time
import pickle

import numpy as np
import faiss
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"   # WHY: cheap + fast for a demo; swap per cost/quality needs
TOP_K = 4                    # how many chunks to retrieve; tune on an eval set
INDEX_PATH = "index.faiss"
META_PATH = "chunks.pkl"

client = OpenAI()

# The system prompt is where we ENFORCE grounding. WHY each rule:
#  - "only use the context" => reduces hallucination.
#  - "cite [source p.N]"     => makes every claim verifiable by the user.
#  - "say you don't know"    => a graceful failure beats a confident wrong answer.
SYSTEM_PROMPT = """You are a precise assistant that answers questions about the \
user's documents.
Rules:
1. Answer ONLY using the provided context. Do not use outside knowledge.
2. Cite the source of every claim inline as [source, p.PAGE].
3. If the context does not contain the answer, say you don't know and point to \
the closest relevant section. Never invent facts."""


def load_index() -> tuple[faiss.Index, list[dict]]:
    """Load the prebuilt index + chunk metadata. Fail loudly with guidance."""
    if not (os.path.exists(INDEX_PATH) and os.path.exists(META_PATH)):
        print("Index not found. Run:  python ingest.py your.pdf")
        sys.exit(1)
    index = faiss.read_index(INDEX_PATH)
    with open(META_PATH, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def embed_query(text: str) -> np.ndarray:
    """Embed the question with the SAME model + normalization as ingestion.
    WHY 'same': query and document vectors must live in the same space or
    similarity is meaningless — a classic RAG bug."""
    resp = client.embeddings.create(model=EMBED_MODEL, input=[text])
    vec = np.array([resp.data[0].embedding], dtype="float32")
    faiss.normalize_L2(vec)
    return vec


def retrieve(question: str, index, chunks, k: int = TOP_K) -> list[dict]:
    """Return the top-k most similar chunks, each with its similarity score.
    The score lets us implement an 'I don't know' guard when retrieval is weak."""
    qvec = embed_query(question)
    scores, ids = index.search(qvec, k)
    hits = []
    for score, idx in zip(scores[0], ids[0]):
        if idx == -1:
            continue
        hit = dict(chunks[idx])
        hit["score"] = float(score)
        hits.append(hit)
    return hits


def build_context(hits: list[dict]) -> str:
    """Concatenate retrieved chunks with labels the model is told to cite.
    WHY labels: they turn retrieval provenance into user-facing citations."""
    blocks = []
    for h in hits:
        label = f"[{h['source']}, p.{h['page']}]"
        blocks.append(f"{label}\n{h['text']}")
    return "\n\n---\n\n".join(blocks)


def answer(question: str) -> dict:
    """The full RAG query: retrieve -> ground -> generate. Returns answer +
    citations + timing so we can report latency (an eval/interview metric)."""
    index, chunks = load_index()
    t0 = time.time()

    hits = retrieve(question, index, chunks)

    # Retrieval-confidence guard. WHY: if the best match is weak, the honest
    # move is to not answer rather than force a grounded-sounding hallucination.
    best = hits[0]["score"] if hits else 0.0
    if not hits or best < 0.20:  # threshold is illustrative — tune on eval data
        return {
            "answer": "I couldn't find this in the document. Try rephrasing, "
                      "or it may not be covered.",
            "citations": [],
            "latency_ms": int((time.time() - t0) * 1000),
        }

    context = build_context(hits)
    resp = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0,  # WHY 0: factual Q&A wants determinism, not creativity.
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    return {
        "answer": resp.choices[0].message.content,
        "citations": [f"{h['source']} p.{h['page']}" for h in hits],
        "latency_ms": int((time.time() - t0) * 1000),
    }


# --- Streamlit UI (only runs under `streamlit run`) --------------------------
def _run_streamlit() -> None:
    import streamlit as st

    st.title("Chat with your PDF")
    st.caption("Grounded answers with citations. Run ingest.py first.")
    q = st.text_input("Ask a question about your document:")
    if q:
        with st.spinner("Retrieving + answering..."):
            result = answer(q)
        st.markdown(result["answer"])
        if result["citations"]:
            st.markdown("**Sources:** " + ", ".join(result["citations"]))
        st.caption(f"Latency: {result['latency_ms']} ms")


def _is_streamlit() -> bool:
    # WHY: one file, two entry points. Detect the Streamlit runtime so the same
    # module works as a CLI tool and as a clickable demo.
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        return get_script_run_ctx() is not None
    except Exception:
        return False


if __name__ == "__main__":
    if _is_streamlit():
        _run_streamlit()
    elif len(sys.argv) > 1:
        out = answer(" ".join(sys.argv[1:]))
        print("\n" + out["answer"])
        if out["citations"]:
            print("\nSources:", ", ".join(out["citations"]))
        print(f"({out['latency_ms']} ms)")
    else:
        print('Usage: python chat_with_pdf.py "your question"')
        print("   or: streamlit run chat_with_pdf.py")
