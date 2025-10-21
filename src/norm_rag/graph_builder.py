"""
Graph builder with multiple construction strategies.

This module provides flexible graph construction with different strategies
optimized for legal knowledge representation.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict
import networkx as nx

from .models import (
    Node, Edge, GraphMetadata, EntityType, RelationType,
    ValidationStatus
)
from .extractor import ExtractionResult


class LegalKnowledgeGraph:
    """
    A knowledge graph for legal documents with rich metadata.

    Represents entities and relationships with full traceability.
    """

    def __init__(self, metadata: Optional[GraphMetadata] = None):
        """
        Initialize a legal knowledge graph.

        Args:
            metadata: Optional metadata for the graph
        """
        self.metadata = metadata or GraphMetadata()
        self.nodes: Dict[str, Node] = {}  # id -> Node
        self.edges: Dict[str, Edge] = {}  # id -> Edge

        # NetworkX graph for efficient operations
        self.nx_graph = nx.DiGraph()

        # Indexes for fast lookup
        self._entity_type_index: Dict[EntityType, Set[str]] = defaultdict(set)
        self._relation_type_index: Dict[RelationType, Set[str]] = defaultdict(set)
        self._article_index: Dict[str, str] = {}  # article_number -> node_id

    def add_node(self, node: Node) -> bool:
        """
        Add a node to the graph.

        Args:
            node: Node to add

        Returns:
            True if added, False if already exists
        """
        if node.id in self.nodes:
            return False

        self.nodes[node.id] = node
        self.nx_graph.add_node(node.id, **node.to_dict())

        # Update indexes
        self._entity_type_index[node.entity_type].add(node.id)

        if node.article_number:
            self._article_index[node.article_number] = node.id

        # Update metadata
        self.metadata.node_count = len(self.nodes)
        if node.is_validated():
            self.metadata.validated_node_count += 1

        self.metadata.modified_at = datetime.now()

        return True

    def add_edge(self, edge: Edge) -> bool:
        """
        Add an edge to the graph.

        Args:
            edge: Edge to add

        Returns:
            True if added, False if already exists or nodes don't exist
        """
        if edge.id in self.edges:
            return False

        # Check that source and target nodes exist
        if edge.source_id not in self.nodes or edge.target_id not in self.nodes:
            return False

        self.edges[edge.id] = edge
        self.nx_graph.add_edge(
            edge.source_id,
            edge.target_id,
            key=edge.id,
            **edge.to_dict()
        )

        # Update indexes
        self._relation_type_index[edge.relation_type].add(edge.id)

        # Update metadata
        self.metadata.edge_count = len(self.edges)
        if edge.is_validated():
            self.metadata.validated_edge_count += 1

        self.metadata.modified_at = datetime.now()

        return True

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[Edge]:
        """Get an edge by ID."""
        return self.edges.get(edge_id)

    def get_nodes_by_type(self, entity_type: EntityType) -> List[Node]:
        """Get all nodes of a specific type."""
        node_ids = self._entity_type_index.get(entity_type, set())
        return [self.nodes[nid] for nid in node_ids]

    def get_edges_by_type(self, relation_type: RelationType) -> List[Edge]:
        """Get all edges of a specific type."""
        edge_ids = self._relation_type_index.get(relation_type, set())
        return [self.edges[eid] for eid in edge_ids]

    def get_node_by_article(self, article_number: str) -> Optional[Node]:
        """Get a node by article number."""
        node_id = self._article_index.get(article_number)
        if node_id:
            return self.nodes[node_id]
        return None

    def get_neighbors(self, node_id: str, direction: str = "out") -> List[Node]:
        """
        Get neighboring nodes.

        Args:
            node_id: ID of the node
            direction: "out" (outgoing), "in" (incoming), or "both"

        Returns:
            List of neighboring nodes
        """
        if node_id not in self.nodes:
            return []

        neighbor_ids = set()

        if direction in ["out", "both"]:
            neighbor_ids.update(self.nx_graph.successors(node_id))

        if direction in ["in", "both"]:
            neighbor_ids.update(self.nx_graph.predecessors(node_id))

        return [self.nodes[nid] for nid in neighbor_ids]

    def get_edges_from_node(self, node_id: str) -> List[Edge]:
        """Get all edges originating from a node."""
        edges = []
        for edge_id, edge in self.edges.items():
            if edge.source_id == node_id:
                edges.append(edge)
        return edges

    def get_edges_to_node(self, node_id: str) -> List[Edge]:
        """Get all edges pointing to a node."""
        edges = []
        for edge_id, edge in self.edges.items():
            if edge.target_id == node_id:
                edges.append(edge)
        return edges

    def calculate_statistics(self):
        """Calculate and update graph statistics."""
        # Average confidence
        all_confidences = (
            [n.confidence for n in self.nodes.values()] +
            [e.confidence for e in self.edges.values()]
        )

        if all_confidences:
            self.metadata.average_confidence = sum(all_confidences) / len(all_confidences)

        # Validation counts
        self.metadata.validated_node_count = sum(
            1 for n in self.nodes.values() if n.is_validated()
        )
        self.metadata.validated_edge_count = sum(
            1 for e in self.edges.values() if e.is_validated()
        )

        # Completeness (placeholder - can be customized)
        # For now, measure % of validated elements
        total_elements = len(self.nodes) + len(self.edges)
        validated_elements = (
            self.metadata.validated_node_count +
            self.metadata.validated_edge_count
        )

        if total_elements > 0:
            self.metadata.completeness_score = validated_elements / total_elements
        else:
            self.metadata.completeness_score = 0.0

    def to_networkx(self) -> nx.DiGraph:
        """Convert to NetworkX DiGraph."""
        return self.nx_graph.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire graph to dictionary."""
        return {
            "metadata": self.metadata.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges.values()],
        }


class GraphBuildingStrategy(ABC):
    """
    Abstract base class for graph building strategies.

    Different strategies create different graph structures from the same data.
    """

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def build(
        self,
        extraction_result: ExtractionResult,
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """
        Build a graph from extraction results.

        Args:
            extraction_result: Extracted nodes and edges
            existing_graph: Optional existing graph to extend

        Returns:
            LegalKnowledgeGraph
        """
        pass


class EntityCentricStrategy(GraphBuildingStrategy):
    """
    Entity-centric graph building strategy.

    Focuses on legal entities (articles, concepts, etc.) as primary nodes.
    Creates dense connections between frequently co-occurring entities.
    """

    def __init__(self):
        super().__init__("entity_centric")

    def build(
        self,
        extraction_result: ExtractionResult,
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """Build entity-centric graph."""
        graph = existing_graph or LegalKnowledgeGraph()
        graph.metadata.construction_strategy = self.name

        # Add all nodes
        for node in extraction_result.nodes:
            graph.add_node(node)

        # Add all edges
        for edge in extraction_result.edges:
            graph.add_edge(edge)

        graph.calculate_statistics()
        return graph


class HierarchicalStrategy(GraphBuildingStrategy):
    """
    Hierarchical graph building strategy.

    Creates a tree-like structure: Constitution -> Laws -> Articles -> Clauses
    Emphasizes parent-child relationships and legal hierarchy.
    """

    def __init__(self):
        super().__init__("hierarchical")

    def build(
        self,
        extraction_result: ExtractionResult,
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """Build hierarchical graph."""
        graph = existing_graph or LegalKnowledgeGraph()
        graph.metadata.construction_strategy = self.name

        # First, add all nodes
        for node in extraction_result.nodes:
            graph.add_node(node)

        # Organize nodes by hierarchy level
        hierarchy_levels = self._organize_by_hierarchy(extraction_result.nodes)

        # Create hierarchical edges (PARTE_DI and CONTIENE)
        for level_idx in range(len(hierarchy_levels) - 1):
            current_level = hierarchy_levels[level_idx]
            next_level = hierarchy_levels[level_idx + 1]

            for parent_node in current_level:
                for child_node in next_level:
                    if self._should_connect_hierarchically(parent_node, child_node):
                        # Create CONTIENE edge from parent to child
                        edge = Edge(
                            source_id=parent_node.id,
                            target_id=child_node.id,
                            relation_type=RelationType.CONTIENE,
                            description=f"{parent_node.label} contiene {child_node.label}",
                            confidence=0.8,
                            created_by="hierarchical_strategy",
                            modified_by="hierarchical_strategy",
                        )
                        graph.add_edge(edge)

        # Add original edges
        for edge in extraction_result.edges:
            graph.add_edge(edge)

        graph.calculate_statistics()
        return graph

    def _organize_by_hierarchy(self, nodes: List[Node]) -> List[List[Node]]:
        """
        Organize nodes into hierarchy levels.

        Levels: [Codici/Leggi] -> [Articoli] -> [Concetti]
        """
        levels: List[List[Node]] = [[], [], []]

        for node in nodes:
            if node.entity_type in [EntityType.ATTO, EntityType.NORMA] and not node.article_number:
                # Top level: laws and codes
                levels[0].append(node)
            elif node.article_number:
                # Middle level: articles
                levels[1].append(node)
            else:
                # Bottom level: concepts, etc.
                levels[2].append(node)

        return [level for level in levels if level]  # Remove empty levels

    def _should_connect_hierarchically(self, parent: Node, child: Node) -> bool:
        """
        Determine if parent and child should be connected hierarchically.

        This is a simplified heuristic - can be customized.
        """
        # Connect if child's law_reference matches parent's label
        if child.law_reference and parent.label in child.law_reference:
            return True

        # Connect articles to their code
        if parent.entity_type == EntityType.ATTO and child.entity_type == EntityType.NORMA:
            return True

        return False


class TemporalStrategy(GraphBuildingStrategy):
    """
    Temporal graph building strategy.

    Orders nodes chronologically and creates temporal edges (PRECEDE/SEGUE).
    Useful for tracking legislative evolution over time.
    """

    def __init__(self):
        super().__init__("temporal")

    def build(
        self,
        extraction_result: ExtractionResult,
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """Build temporal graph."""
        graph = existing_graph or LegalKnowledgeGraph()
        graph.metadata.construction_strategy = self.name

        # Add all nodes
        for node in extraction_result.nodes:
            graph.add_node(node)

        # Sort nodes by effective date
        dated_nodes = [
            n for n in extraction_result.nodes
            if n.effective_date is not None
        ]
        dated_nodes.sort(key=lambda n: n.effective_date)

        # Create temporal edges
        for i in range(len(dated_nodes) - 1):
            current = dated_nodes[i]
            next_node = dated_nodes[i + 1]

            # Create PRECEDE edge
            edge = Edge(
                source_id=current.id,
                target_id=next_node.id,
                relation_type=RelationType.PRECEDE,
                description=f"{current.label} precede {next_node.label}",
                confidence=1.0,  # High confidence for temporal ordering
                created_by="temporal_strategy",
                modified_by="temporal_strategy",
            )
            graph.add_edge(edge)

        # Add original edges
        for edge in extraction_result.edges:
            graph.add_edge(edge)

        graph.calculate_statistics()
        return graph


class SemanticClusteringStrategy(GraphBuildingStrategy):
    """
    Semantic clustering strategy.

    Groups related legal concepts based on semantic similarity.
    Creates clusters of related articles and concepts.
    """

    def __init__(self, similarity_threshold: float = 0.7):
        super().__init__("semantic_clustering")
        self.similarity_threshold = similarity_threshold

    def build(
        self,
        extraction_result: ExtractionResult,
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """Build semantically clustered graph."""
        graph = existing_graph or LegalKnowledgeGraph()
        graph.metadata.construction_strategy = self.name

        # Add all nodes
        for node in extraction_result.nodes:
            graph.add_node(node)

        # Create clusters based on similarity
        # (This is a simplified version - can be enhanced with embeddings)
        clusters = self._create_semantic_clusters(extraction_result.nodes)

        # Create SIMILE_A edges within clusters
        for cluster in clusters:
            for i, node1 in enumerate(cluster):
                for node2 in cluster[i + 1:]:
                    similarity = self._calculate_similarity(node1, node2)

                    if similarity >= self.similarity_threshold:
                        edge = Edge(
                            source_id=node1.id,
                            target_id=node2.id,
                            relation_type=RelationType.SIMILE_A,
                            description=f"{node1.label} simile a {node2.label}",
                            weight=similarity,
                            confidence=similarity,
                            directed=False,
                            created_by="semantic_strategy",
                            modified_by="semantic_strategy",
                        )
                        graph.add_edge(edge)

        # Add original edges
        for edge in extraction_result.edges:
            graph.add_edge(edge)

        graph.calculate_statistics()
        return graph

    def _create_semantic_clusters(self, nodes: List[Node]) -> List[List[Node]]:
        """
        Create semantic clusters of nodes.

        Simple implementation based on entity type and keywords.
        Can be enhanced with embeddings and proper clustering algorithms.
        """
        clusters: Dict[str, List[Node]] = defaultdict(list)

        for node in nodes:
            # Cluster by entity type and keywords in description
            cluster_key = f"{node.entity_type.value}"

            # Add keywords from description
            keywords = set(node.description.lower().split())
            common_legal_terms = {"penale", "civile", "procedura", "responsabilità", "diritto"}

            for term in common_legal_terms:
                if term in keywords:
                    cluster_key += f"_{term}"

            clusters[cluster_key].append(node)

        return [cluster for cluster in clusters.values() if len(cluster) > 1]

    def _calculate_similarity(self, node1: Node, node2: Node) -> float:
        """
        Calculate semantic similarity between two nodes.

        Simple Jaccard similarity based on description words.
        Can be enhanced with embeddings.
        """
        words1 = set(node1.description.lower().split())
        words2 = set(node2.description.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union) if union else 0.0


class HybridStrategy(GraphBuildingStrategy):
    """
    Hybrid strategy combining multiple approaches.

    Uses entity-centric as base, adds hierarchical relationships,
    temporal ordering, and semantic clustering.
    """

    def __init__(self):
        super().__init__("hybrid")
        self.entity_strategy = EntityCentricStrategy()
        self.hierarchical_strategy = HierarchicalStrategy()
        self.temporal_strategy = TemporalStrategy()
        self.semantic_strategy = SemanticClusteringStrategy()

    def build(
        self,
        extraction_result: ExtractionResult,
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """Build hybrid graph."""
        # Start with entity-centric
        graph = self.entity_strategy.build(extraction_result, existing_graph)

        # Add hierarchical relationships
        graph = self.hierarchical_strategy.build(extraction_result, graph)

        # Add temporal relationships
        graph = self.temporal_strategy.build(extraction_result, graph)

        # Add semantic clustering
        graph = self.semantic_strategy.build(extraction_result, graph)

        graph.metadata.construction_strategy = self.name
        graph.calculate_statistics()

        return graph


class GraphBuilder:
    """
    Main graph builder class supporting multiple strategies.
    """

    STRATEGIES = {
        "entity_centric": EntityCentricStrategy,
        "hierarchical": HierarchicalStrategy,
        "temporal": TemporalStrategy,
        "semantic_clustering": SemanticClusteringStrategy,
        "hybrid": HybridStrategy,
    }

    def __init__(self, strategy: str = "entity_centric"):
        """
        Initialize GraphBuilder with a strategy.

        Args:
            strategy: Name of the strategy to use
        """
        if strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy}. "
                f"Available: {list(self.STRATEGIES.keys())}"
            )

        self.strategy: GraphBuildingStrategy = self.STRATEGIES[strategy]()

    def build_graph(
        self,
        extraction_result: ExtractionResult,
        graph_name: str = "Legal Knowledge Graph",
        graph_description: str = "",
        existing_graph: Optional[LegalKnowledgeGraph] = None
    ) -> LegalKnowledgeGraph:
        """
        Build a graph from extraction results.

        Args:
            extraction_result: Extracted nodes and edges
            graph_name: Name for the graph
            graph_description: Description of the graph
            existing_graph: Optional existing graph to extend

        Returns:
            LegalKnowledgeGraph
        """
        graph = self.strategy.build(extraction_result, existing_graph)

        # Update metadata
        graph.metadata.name = graph_name
        graph.metadata.description = graph_description
        graph.metadata.modified_at = datetime.now()

        return graph

    def set_strategy(self, strategy: str):
        """Change the building strategy."""
        if strategy not in self.STRATEGIES:
            raise ValueError(
                f"Unknown strategy: {strategy}. "
                f"Available: {list(self.STRATEGIES.keys())}"
            )

        self.strategy = self.STRATEGIES[strategy]()

    def get_available_strategies(self) -> List[str]:
        """Get list of available strategies."""
        return list(self.STRATEGIES.keys())
