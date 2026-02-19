import json
import os
import chromadb
from schema.state import TriageState
from schema.ticket import DedupResult

SIMILARITY_THRESHOLD = 0.82  # Tuned via scripts/tune_threshold.py

_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Lazy-initialized embedding function (avoids model download at import time)
_embedding_fn = None


def _get_embedding_fn():
    """Lazily load the sentence-transformer embedding function."""
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
    return _embedding_fn


def init_vector_store(persist_dir: str = None) -> chromadb.Collection:
    """Initialize or load ChromaDB collection."""
    if persist_dir is None:
        persist_dir = os.path.join(_DATA_DIR, "chroma_db")
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name="tickets",
        embedding_function=_get_embedding_fn(),
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def seed_vector_store(
    collection: chromadb.Collection,
    seed_file: str = None,
):
    """Load seed tickets into ChromaDB. Run once."""
    if seed_file is None:
        seed_file = os.path.join(_DATA_DIR, "seed_tickets.json")

    with open(seed_file) as f:
        tickets = json.load(f)

    # Skip if already seeded
    if collection.count() >= len(tickets):
        return

    documents = [f"{t['title']}. {t['description']}" for t in tickets]
    ids = [t["id"] for t in tickets]
    metadatas = [
        {
            "title": t["title"],
            "component": t.get("component", ""),
            "severity": t.get("severity", ""),
            "team": t.get("team", ""),
        }
        for t in tickets
    ]

    collection.add(documents=documents, ids=ids, metadatas=metadatas)


def dedup_agent(state: TriageState) -> dict:
    """Check if a similar ticket exists in the vector store."""
    parsed = state.get("parsed_ticket")
    if not parsed or not parsed.is_valid:
        return {
            "dedup_result": DedupResult(is_duplicate=False),
            "trace": state.get("trace", []) + ["DEDUP: Skipped (invalid ticket)"],
        }

    collection = init_vector_store()

    query_text = f"{parsed.title}. {parsed.description}"

    results = collection.query(
        query_texts=[query_text],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    decision = None

    if results["distances"] and results["distances"][0]:
        top_distance = results["distances"][0][0]
        top_similarity = 1 - top_distance
        top_id = results["ids"][0][0]
        top_title = results["metadatas"][0][0].get("title", "Unknown")

        is_dup = top_similarity >= SIMILARITY_THRESHOLD

        dedup_result = DedupResult(
            is_duplicate=is_dup,
            similar_ticket_id=top_id if is_dup else None,
            similar_ticket_title=top_title if is_dup else None,
            similarity_score=round(top_similarity, 4),
        )

        if is_dup:
            decision = "duplicate"
            trace_msg = f"DEDUP: Duplicate of {top_id} (similarity: {top_similarity:.3f})"
        else:
            trace_msg = f"DEDUP: No duplicate found (closest: {top_similarity:.3f} to {top_id})"
    else:
        dedup_result = DedupResult(is_duplicate=False)
        trace_msg = "DEDUP: No similar tickets found"

    return {
        "dedup_result": dedup_result,
        "decision": decision,
        "trace": state.get("trace", []) + [trace_msg],
    }
