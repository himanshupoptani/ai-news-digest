import re
from typing import List, Dict, Set, Tuple
from sqlalchemy.orm import Session

from backend.app.models.source import Source
from backend.app.models.topic import Topic
from backend.app.models.article import Article, Event
from backend.app.schemas.news import RawArticle
from backend.app.schemas.graph import GraphNode, GraphEdge, GraphDataResponse

class GraphService:
    """
    Topic & Source Relationship Knowledge Graph Service.
    Transforms relational models and retrieved news into connected graph structures:
    - Topic Hierarchies: (Technology -> Artificial Intelligence -> LLMs)
    - Source Connections: (Reuters -> Article -> Event)
    - Cross-Source Event Clusters: (Event covered by multiple publishers)
    """

    @staticmethod
    def build_topic_taxonomy_graph(db: Session) -> GraphDataResponse:
        """Constructs a hierarchical graph of topics and subtopics from the database."""
        topics = db.query(Topic).all()
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        for topic in topics:
            nodes.append(
                GraphNode(
                    id=f"topic_{topic.id}",
                    label=topic.name,
                    group="topic",
                    metadata={"slug": topic.slug, "description": topic.description}
                )
            )
            if topic.parent_id:
                edges.append(
                    GraphEdge(
                        source=f"topic_{topic.parent_id}",
                        target=f"topic_{topic.id}",
                        relation="CONTAINS_SUBTOPIC",
                        label="subtopic"
                    )
                )

        return GraphDataResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges)
        )

    @classmethod
    def build_article_intelligence_graph(
        cls, 
        articles: List[RawArticle], 
        query_topic: str = "General News"
    ) -> GraphDataResponse:
        """
        Builds a multi-layer Knowledge Graph for a batch of retrieved articles:
        Layer 1: Central Query / Topic Node
        Layer 2: Publisher / Source Nodes (Reuters, Bloomberg, etc.)
        Layer 3: Article Headline Nodes
        """
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        seen_nodes: Set[str] = set()

        # 1. Central Topic Node
        topic_node_id = f"topic_{re.sub(r'[^a-zA-Z0-9_]', '_', query_topic.lower())}"
        nodes.append(
            GraphNode(
                id=topic_node_id,
                label=query_topic.title(),
                group="topic",
                metadata={"type": "query_focus"}
            )
        )
        seen_nodes.add(topic_node_id)

        # 2. Iterate articles to create Source and Article nodes
        for idx, art in enumerate(articles):
            # Source Node
            source_name = art.source_name or "Unknown Publisher"
            source_node_id = f"source_{re.sub(r'[^a-zA-Z0-9_]', '_', source_name.lower())}"

            if source_node_id not in seen_nodes:
                nodes.append(
                    GraphNode(
                        id=source_node_id,
                        label=source_name,
                        group="source",
                        metadata={"publisher": source_name}
                    )
                )
                seen_nodes.add(source_node_id)
                # Link Topic -> Source
                edges.append(
                    GraphEdge(
                        source=topic_node_id,
                        target=source_node_id,
                        relation="COVERED_BY",
                        label="reported by"
                    )
                )

            # Article Node
            art_node_id = f"article_{idx}"
            short_title = art.title[:45] + "..." if len(art.title) > 45 else art.title
            nodes.append(
                GraphNode(
                    id=art_node_id,
                    label=short_title,
                    group="article",
                    metadata={
                        "full_title": art.title,
                        "url": art.url,
                        "published_at": art.published_at,
                        "category": art.category
                    }
                )
            )
            seen_nodes.add(art_node_id)

            # Link Source -> Article
            edges.append(
                GraphEdge(
                    source=source_node_id,
                    target=art_node_id,
                    relation="PUBLISHED",
                    label="publishes"
                )
            )

        return GraphDataResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges)
        )

# Singleton instance
graph_service = GraphService()

