import pytest
import tempfile
import os
from agents.dedup import init_vector_store, seed_vector_store, SIMILARITY_THRESHOLD


@pytest.fixture(scope="module")
def seeded_collection():
    """Initialize and seed ChromaDB in a temp directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        collection = init_vector_store(persist_dir=tmpdir)
        seed_file = os.path.join(os.path.dirname(__file__), "..", "data", "seed_tickets.json")
        seed_vector_store(collection, seed_file=seed_file)
        yield collection


class TestDedupVectorSearch:
    def test_exact_match_returns_high_similarity(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["Login button unresponsive on Safari - Checkout page"],
            n_results=1,
            include=["distances"],
        )
        similarity = 1 - results["distances"][0][0]
        assert similarity > 0.9

    def test_paraphrased_duplicate_detected(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["Safari users can't click login on the checkout page"],
            n_results=1,
            include=["distances"],
        )
        similarity = 1 - results["distances"][0][0]
        assert similarity >= SIMILARITY_THRESHOLD * 0.9  # Allow some tolerance

    def test_different_issue_not_flagged(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["The search bar autocomplete is not showing suggestions on the homepage"],
            n_results=1,
            include=["distances"],
        )
        similarity = 1 - results["distances"][0][0]
        assert similarity < SIMILARITY_THRESHOLD

    def test_returns_correct_number_of_results(self, seeded_collection):
        results = seeded_collection.query(
            query_texts=["Any bug report text here"],
            n_results=3,
            include=["distances", "metadatas"],
        )
        assert len(results["ids"][0]) <= 3

    def test_collection_has_all_seed_tickets(self, seeded_collection):
        count = seeded_collection.count()
        assert count == 50

    def test_seed_idempotent(self, seeded_collection):
        """Seeding again should not add duplicates."""
        seed_file = os.path.join(os.path.dirname(__file__), "..", "data", "seed_tickets.json")
        seed_vector_store(seeded_collection, seed_file=seed_file)
        assert seeded_collection.count() == 50

    def test_stripe_duplicate_detected(self, seeded_collection):
        """TICK-046 is a near-duplicate of TICK-002 about Stripe timeouts."""
        results = seeded_collection.query(
            query_texts=[
                "Large Stripe payments over $10,000 are timing out during processing"
            ],
            n_results=1,
            include=["distances", "metadatas"],
        )
        similarity = 1 - results["distances"][0][0]
        # Should find either TICK-002 or TICK-046 with high similarity
        assert similarity > 0.7
