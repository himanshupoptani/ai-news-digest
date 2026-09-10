import pytest
from backend.app.schemas.news import RawArticle
from backend.app.services.vector_store import InMemoryVectorStore, SearchResult

@pytest.fixture
def store():
    vs = InMemoryVectorStore()
    yield vs
    vs.clear()

def test_chunking_with_overlap(store):
    # Create 100-word text
    words = [f"word_{i}" for i in range(100)]
    text = " ".join(words)

    # Chunk size 40, overlap 10
    chunks = store.chunk_text(text, chunk_size=40, overlap=10)
    assert len(chunks) > 1
    # Check that adjacent chunks share overlapping words
    chunk0_words = chunks[0].split()
    chunk1_words = chunks[1].split()
    # The last words of chunk 0 should equal the first words of chunk 1
    assert chunk0_words[-10:] == chunk1_words[:10]

def test_vector_search_semantic_matching(store):
    art1 = RawArticle(
        title="NASA Artemis Moon Mission Completes Liquid Fuel Tests",
        url="https://apnews.com/artemis",
        source_name="Associated Press",
        content="NASA completed a full cryogenic wet dress rehearsal for the Space Launch System rocket at Kennedy Space Center with liquid hydrogen fuel."
    )
    art2 = RawArticle(
        title="Federal Reserve Holds Interest Rates Steady",
        url="https://reuters.com/fed",
        source_name="Reuters",
        content="The Federal Reserve maintained benchmark interest rates at 5.5 percent citing labor market conditions and inflation targets."
    )
    art3 = RawArticle(
        title="Nvidia Blackwell Chip Production Ramps Up",
        url="https://bloomberg.com/nvidia",
        source_name="Bloomberg",
        content="Nvidia CEO confirmed production of next generation Blackwell GPUs is scaling to meet continuous data center demand."
    )

    count = store.add_articles([art1, art2, art3])
    assert count == 3

    # Query 1: Space launch fuel query
    results_space = store.similarity_search("rocket cryogenic fuel launch", top_k=2)
    assert len(results_space) > 0
    top_space = results_space[0]
    assert isinstance(top_space, SearchResult)
    assert top_space.chunk.source_name == "Associated Press"
    assert "NASA" in top_space.chunk.article_title
    assert top_space.similarity_score > 0.20

    # Query 2: Chip hardware query
    results_gpu = store.similarity_search("Blackwell GPU semiconductors", top_k=2)
    assert len(results_gpu) > 0
    top_gpu = results_gpu[0]
    assert top_gpu.chunk.source_name == "Bloomberg"
    assert "Nvidia" in top_gpu.chunk.article_title

def test_vector_search_threshold_filtering(store):
    art = RawArticle(
        title="Nvidia Revenue Surges",
        url="https://reuters.com/nvda",
        source_name="Reuters",
        content="Nvidia recorded quarterly revenue of 30 billion dollars."
    )
    store.add_articles([art])

    # Totally unrelated query should return empty list due to min_score threshold
    results_unrelated = store.similarity_search("ancient Egyptian pyramids pharaohs", min_score=0.20)
    assert len(results_unrelated) == 0
