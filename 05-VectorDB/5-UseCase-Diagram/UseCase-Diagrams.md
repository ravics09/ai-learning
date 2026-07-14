# Vector Databases — Use Case Diagrams

Visual mental models for the concepts that come up most in interviews. Each diagram has a
short "how to read it" note.

---

## 1. HNSW Graph Search (layered traversal)

Start at a sparse top layer with long hops, greedily move toward the query, then descend to
denser layers for precision.

```mermaid
graph TD
    subgraph L2[Layer 2 - sparse]
      E((entry point)) --- N2((node))
    end
    subgraph L1[Layer 1]
      A1((n)) --- B1((n)) --- C1((n))
    end
    subgraph L0[Layer 0 - all nodes]
      A0((n)) --- B0((n)) --- C0((n)) --- D0((n)) --- T0((nearest))
    end
    E -.descend.-> A1
    C1 -.descend.-> C0
    C0 --> T0
    Q{{query}} -.guides walk.-> E
```
*Read it:* higher layers are express lanes; each descent narrows the search near the query.
`ef_search` controls how many candidates you keep while walking (recall vs latency).

---

## 2. Hybrid Search + Reciprocal Rank Fusion

Run dense and sparse retrieval in parallel, fuse by rank, then optionally rerank.

```mermaid
flowchart LR
    Q[Query] --> DE[Embed] --> DV[Dense / vector search]
    Q --> BM[BM25 / keyword search]
    DV --> LA[Ranked list A]
    BM --> LB[Ranked list B]
    LA --> RRF["RRF fuse: 1/(k+rank)"]
    LB --> RRF
    RRF --> CE[Cross-encoder rerank<br/>top ~50]
    CE --> OUT[Final top-k]
```
*Read it:* RRF merges by rank so incompatible score scales don't matter; the reranker adds
precision on a small candidate set.

---

## 3. Sharded + Replicated Cluster (scatter-gather)

Data split across shards for size; each shard replicated for QPS/HA; coordinator merges.

```mermaid
flowchart TB
    Q[Query] --> C[Coordinator / router]
    C --> S1[Shard 1]
    C --> S2[Shard 2]
    C --> S3[Shard 3]
    subgraph R1[Shard 1 replicas]
      S1 --- S1a[replica a] --- S1b[replica b]
    end
    S1 --> M[Merge local top-k → global top-k]
    S2 --> M
    S3 --> M
    M --> OUT[Results]
```
*Read it:* latency is bounded by the slowest shard; replicas absorb read QPS and survive
node failure.

---

## 4. Multi-Tenant Filtering (server-side isolation)

A trusted gateway injects `tenant_id`; each tenant only ever sees its own vectors.

```mermaid
flowchart TB
    TA[Tenant A] --> GW[Auth + tenant-scoping gateway]
    TB[Tenant B] --> GW
    GW -->|force tenant_id=A| VDB[(Vector DB<br/>shared collection)]
    GW -->|force tenant_id=B| VDB
    VDB --> RA[A's matches only]
    VDB --> RB[B's matches only]
```
*Read it:* the client never sets its own tenant id; the filter is enforced in a trusted
layer to prevent cross-tenant leakage.

---

## 5. Quantization Tiers (memory vs fidelity)

One vector, many representations; compress for the candidate stage, keep full precision for
re-ranking.

```mermaid
flowchart LR
    F[float32 1024d<br/>~4KB] -->|int8| S[int8 1024d<br/>~1KB, 4x]
    F -->|MRL truncate| T[float32 256d<br/>~1KB]
    S -->|PQ| P[PQ code<br/>~64B, up to 100x]
    F -->|binary| B[1 bit/dim<br/>~128B, 32x]
    P --> RR[Re-rank top-N<br/>with float32]
    B --> RR
    RR --> OUT[Final top-k]
```
*Read it:* each arrow trades fidelity for size; the re-rank step buys back most of the lost
recall cheaply.

---

## 6. Index Selection Flowchart

A pragmatic decision path from workload to index.

```mermaid
flowchart TD
    A{Dataset size?} -->|<100k or need exact| FLAT[Flat]
    A -->|100k – ~100M| B{Memory plentiful?}
    B -->|Yes, want top recall/latency| HNSW[HNSW]
    B -->|Memory limited| IVF[IVF or HNSW-PQ]
    A -->|billions| C{RAM budget?}
    C -->|Very tight| DISK[DiskANN - SSD]
    C -->|Moderate| IVFPQ[IVF-PQ + re-rank]
```
*Read it:* size sets the branch; memory budget picks between graph, cluster+compress, or
SSD-resident.

---

## 7. RAG Retrieval Pipeline (end to end)

Where the vector DB sits in a Retrieval-Augmented Generation flow.

```mermaid
flowchart LR
    D[Documents] --> CH[Chunk] --> EM[Embed] --> IDX[(Vector DB)]
    U[User question] --> EQ[Embed query] --> IDX
    IDX --> K[Top-k chunks]
    K --> RANK[Rerank]
    RANK --> PR[Prompt + context]
    PR --> LLM[LLM] --> ANS[Grounded answer + citations]
```
*Read it:* retrieval quality (chunking + embedding + index) upstream determines answer
quality downstream.

---

## 8. Write Path & Freshness (LSM-style segments)

How upserts become searchable and how compaction keeps recall healthy.

```mermaid
flowchart TB
    W[Upsert / delete] --> MEM[Mutable in-memory segment]
    MEM -->|refresh| SEARCH[Searchable]
    MEM -->|flush| SEG[Immutable on-disk segment]
    SEG --> COMP[Background compaction / merge]
    TOMB[Tombstones] --> COMP
    COMP --> CLEAN[Purged + rebuilt index]
```
*Read it:* fresh writes are visible after a refresh (visibility lag); deletes are tombstoned
and physically removed during compaction.

---

## 9. Two-Stage Retrieval at Billion Scale

Cheap coarse recall over compressed vectors, then exact re-rank.

```mermaid
flowchart LR
    Q[Query] --> COARSE[IVF-PQ coarse search<br/>compressed vectors]
    COARSE --> CAND[~200 candidates]
    CAND --> FETCH[Fetch full-precision vectors]
    FETCH --> EXACT[Exact re-score]
    EXACT --> CE[Optional cross-encoder]
    CE --> OUT[Top-k]
```
*Read it:* the first stage is cheap and slightly lossy; the small second stage restores
precision without paying full-precision cost across the whole corpus.

> Content synthesized from general domain knowledge and current (2025-2026) interview trends; rephrased for compliance with licensing restrictions.
