"""
llamaindex_rag.py
-----------------
Goal: a minimal end-to-end RAG pipeline with LlamaIndex — build an index from
documents and answer questions with cited sources.

WHY LLAMAINDEX FOR RAG?
  It's a data framework purpose-built for "answer over my documents": connectors ->
  documents -> nodes(+metadata) -> embeddings -> index -> retriever -> synthesizer.
  You get mature chunking/indexing/query primitives in a few lines instead of gluing
  a parser + splitter + vector store + prompt by hand. For pure document Q&A it's
  usually the fastest, cleanest path (compose it with LangGraph for orchestration).

Run:
  export OPENAI_API_KEY=sk-...
  python llamaindex_rag.py
"""

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter


# 1) Source documents. In real life these come from connectors (PDF, Notion, SQL, S3...).
#    Here we hardcode a tiny corpus so the example is self-contained.
raw_docs = [
    Document(
        text=(
            "Refund policy: Customers may request a full refund within 30 days of "
            "purchase. After 30 days, only store credit is available."
        ),
        metadata={"source": "policy.md", "section": "refunds"},
    ),
    Document(
        text=(
            "Shipping: Standard shipping takes 3-5 business days. Express shipping "
            "arrives next business day for an extra fee."
        ),
        metadata={"source": "policy.md", "section": "shipping"},
    ),
]

# 2) Chunking. WHY: retrieval quality depends on chunk size — too big dilutes the
#    match, too small loses context. SentenceSplitter respects sentence boundaries.
splitter = SentenceSplitter(chunk_size=128, chunk_overlap=20)

# 3) Build the index: chunk -> embed -> store. WHY: embeddings let us retrieve by
#    meaning (semantic search), not just keywords.
index = VectorStoreIndex.from_documents(raw_docs, transformations=[splitter])

# 4) Query engine = retriever + response synthesizer.
#    similarity_top_k=2 -> fetch the 2 most relevant chunks before answering.
#    WHY: fewer, tighter chunks = lower cost/latency and less distraction for the LLM.
query_engine = index.as_query_engine(similarity_top_k=2)


if __name__ == "__main__":
    question = "Can I get a refund after 40 days?"
    response = query_engine.query(question)

    print("Q:", question)
    print("A:", response)

    # WHY show sources: RAG's value is citable, grounded answers — always surface
    # which chunks the answer came from so users (and you) can verify.
    print("\nSources:")
    for node in response.source_nodes:
        meta = node.node.metadata
        print(f"  - {meta.get('source')} [{meta.get('section')}] score={node.score:.3f}")
