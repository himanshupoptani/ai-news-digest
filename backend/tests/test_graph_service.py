import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
from backend.app.models.topic import Topic
from backend.app.schemas.news import RawArticle
from backend.app.schemas.graph import GraphDataResponse
from backend.app.services.graph_service import GraphService

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()

    # Seed root topic and subtopics
    root_tech = Topic(name="Technology", slug="technology", description="Tech news")
    session.add(root_tech)
    session.commit()

    sub1 = Topic(name="Artificial Intelligence", slug="ai", description="AI news", parent_id=root_tech.id)
    sub2 = Topic(name="Semiconductors", slug="chips", description="Hardware news", parent_id=root_tech.id)
    session.add_all([sub1, sub2])
    session.commit()

    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_build_topic_taxonomy_graph(db):
    graph = GraphService.build_topic_taxonomy_graph(db)

    assert isinstance(graph, GraphDataResponse)
    assert graph.total_nodes == 3
    assert graph.total_edges == 2
    # Verify edge relations
    subtopic_edges = [e for e in graph.edges if e.relation == "CONTAINS_SUBTOPIC"]
    assert len(subtopic_edges) == 2

def test_build_article_intelligence_graph():
    art1 = RawArticle(
        title="OpenAI signs safety testing pact",
        url="https://reuters.com/ai-pact",
        source_name="Reuters",
        content="Testing pact content."
    )
    art2 = RawArticle(
        title="US safety institute begins model evaluations",
        url="https://bloomberg.com/ai-eval",
        source_name="Bloomberg",
        content="Evaluation details."
    )

    graph = GraphService.build_article_intelligence_graph([art1, art2], query_topic="AI Safety")

    assert isinstance(graph, GraphDataResponse)
    # Nodes: 1 central topic + 2 sources + 2 articles = 5 nodes
    assert graph.total_nodes == 5
    # Edges: 2 topic->source + 2 source->article = 4 edges
    assert graph.total_edges == 4

    # Verify node groups
    groups = {n.group for n in graph.nodes}
    assert groups == {"topic", "source", "article"}
