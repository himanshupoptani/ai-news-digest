from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class GraphNode(BaseModel):
    """Represents an entity node in the news intelligence graph."""
    id: str
    label: str
    group: str  # 'topic', 'event', 'source', or 'article'
    metadata: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    """Represents a directed or semantic relationship between two nodes."""
    source: str
    target: str
    relation: str  # 'CONTAINS_SUBTOPIC', 'CATEGORIZES', 'COVERS_EVENT', 'PUBLISHED_BY'
    label: Optional[str] = None

class GraphDataResponse(BaseModel):
    """Complete serialized graph payload ready for frontend visual rendering."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
