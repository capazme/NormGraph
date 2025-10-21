"""
Information extractor with confidence scores and full traceability.

Extracts entities and relationships from text while maintaining
provenance information for scientific rigor.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

from .models import (
    Node, Edge, Provenance, EntityType, RelationType,
    ValidationStatus, ExtractionMethod
)
from .text_reader import TextSegment


class ExtractionResult:
    """
    Result of an extraction operation.

    Contains extracted nodes, edges, and metadata about the extraction process.
    """

    def __init__(self):
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.extraction_stats: Dict[str, Any] = {
            "total_segments_processed": 0,
            "nodes_extracted": 0,
            "edges_extracted": 0,
            "average_confidence": 0.0,
            "extraction_time": 0.0,
        }

    def add_node(self, node: Node):
        """Add a node to the extraction result."""
        self.nodes.append(node)
        self.extraction_stats["nodes_extracted"] = len(self.nodes)

    def add_edge(self, edge: Edge):
        """Add an edge to the extraction result."""
        self.edges.append(edge)
        self.extraction_stats["edges_extracted"] = len(self.edges)

    def calculate_stats(self):
        """Calculate extraction statistics."""
        all_confidences = (
            [n.confidence for n in self.nodes] +
            [e.confidence for e in self.edges]
        )

        if all_confidences:
            self.extraction_stats["average_confidence"] = sum(all_confidences) / len(all_confidences)
        else:
            self.extraction_stats["average_confidence"] = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
            "extraction_stats": self.extraction_stats,
        }


class InformationExtractor:
    """
    Extracts legal entities and relationships from text segments.

    Supports both automatic extraction (using LLMs or NLP) and manual extraction.
    All extractions include provenance information for traceability.
    """

    def __init__(
        self,
        llm_model_func: Optional[callable] = None,
        embedding_func: Optional[callable] = None,
        extractor_version: str = "1.0.0"
    ):
        """
        Initialize InformationExtractor.

        Args:
            llm_model_func: Optional LLM function for automatic extraction
            embedding_func: Optional embedding function
            extractor_version: Version identifier
        """
        self.llm_model_func = llm_model_func
        self.embedding_func = embedding_func
        self.extractor_version = extractor_version

    def extract_from_segments(
        self,
        segments: List[TextSegment],
        extraction_method: ExtractionMethod = ExtractionMethod.AUTOMATIC,
        actor_id: str = "system"
    ) -> ExtractionResult:
        """
        Extract entities and relationships from text segments.

        Args:
            segments: List of text segments to process
            extraction_method: Method used for extraction
            actor_id: ID of the actor performing extraction

        Returns:
            ExtractionResult containing nodes and edges
        """
        result = ExtractionResult()
        start_time = datetime.now()

        for i, segment in enumerate(segments):
            # Extract entities from this segment
            nodes = self._extract_entities_from_segment(
                segment,
                extraction_method,
                actor_id
            )

            for node in nodes:
                result.add_node(node)

            # Extract relationships (if we have LLM support)
            if self.llm_model_func:
                edges = self._extract_relationships_from_segment(
                    segment,
                    nodes,
                    extraction_method,
                    actor_id
                )

                for edge in edges:
                    result.add_edge(edge)

        result.extraction_stats["total_segments_processed"] = len(segments)
        result.extraction_stats["extraction_time"] = (datetime.now() - start_time).total_seconds()
        result.calculate_stats()

        return result

    def _extract_entities_from_segment(
        self,
        segment: TextSegment,
        extraction_method: ExtractionMethod,
        actor_id: str
    ) -> List[Node]:
        """
        Extract entities from a single text segment.

        This is a rule-based implementation. Can be extended with LLM-based extraction.
        """
        nodes = []

        # Pattern for Italian legal articles: "Art. 123" or "Articolo 123"
        article_pattern = r"(?:Art\.|Articolo)\s+(\d+(?:-bis|-ter|-quater)?)"
        article_matches = re.finditer(article_pattern, segment.text, re.IGNORECASE)

        for match in article_matches:
            article_num = match.group(1)
            full_text = match.group(0)

            # Create a node for this legal article reference
            node = Node(
                label=f"Art. {article_num}",
                entity_type=EntityType.NORMA,
                description=f"Riferimento all'articolo {article_num}",
                article_number=article_num,
                provenance=self._create_provenance_for_match(
                    segment,
                    match,
                    extraction_method
                ),
                confidence=0.9,  # High confidence for regex-based extraction
                created_by=actor_id,
                modified_by=actor_id,
                validation_status=ValidationStatus.PENDING,
            )

            nodes.append(node)

        # Pattern for legal concepts in Italian
        # e.g., "diritto penale", "procedura penale", "responsabilità civile"
        concept_patterns = [
            r"(diritto\s+\w+)",
            r"(responsabilità\s+\w+)",
            r"(procedura\s+\w+)",
            r"(codice\s+\w+(?:\s+\w+)?)",
        ]

        for pattern in concept_patterns:
            concept_matches = re.finditer(pattern, segment.text, re.IGNORECASE)

            for match in concept_matches:
                concept_text = match.group(1)

                # Create a node for this legal concept
                node = Node(
                    label=concept_text.title(),
                    entity_type=EntityType.CONCETTO_GIURIDICO,
                    description=f"Concetto giuridico: {concept_text}",
                    provenance=self._create_provenance_for_match(
                        segment,
                        match,
                        extraction_method
                    ),
                    confidence=0.7,  # Medium confidence
                    created_by=actor_id,
                    modified_by=actor_id,
                    validation_status=ValidationStatus.PENDING,
                )

                nodes.append(node)

        # If LLM is available, use it for more sophisticated extraction
        if self.llm_model_func:
            llm_nodes = self._extract_entities_with_llm(
                segment,
                extraction_method,
                actor_id
            )
            nodes.extend(llm_nodes)

        return nodes

    def _extract_relationships_from_segment(
        self,
        segment: TextSegment,
        entities: List[Node],
        extraction_method: ExtractionMethod,
        actor_id: str
    ) -> List[Edge]:
        """
        Extract relationships between entities in a segment.

        Uses pattern matching and optionally LLM-based extraction.
        """
        edges = []

        # Pattern for legal references: "Art. 123 modifica l'Art. 456"
        reference_patterns = [
            (r"Art\.\s+(\d+)\s+(?:modifica|abroga|deroga)\s+(?:l')?Art\.\s+(\d+)", RelationType.MODIFICA),
            (r"Art\.\s+(\d+)\s+(?:richiama|riferisce)\s+(?:l')?Art\.\s+(\d+)", RelationType.RIFERISCE),
            (r"Art\.\s+(\d+)\s+(?:integra|completa)\s+(?:l')?Art\.\s+(\d+)", RelationType.INTEGRA),
        ]

        for pattern, relation_type in reference_patterns:
            matches = re.finditer(pattern, segment.text, re.IGNORECASE)

            for match in matches:
                source_article = match.group(1)
                target_article = match.group(2)

                # Find or create nodes for these articles
                source_node = self._find_or_create_article_node(
                    source_article,
                    entities,
                    segment,
                    extraction_method,
                    actor_id
                )
                target_node = self._find_or_create_article_node(
                    target_article,
                    entities,
                    segment,
                    extraction_method,
                    actor_id
                )

                # Create edge
                edge = Edge(
                    source_id=source_node.id,
                    target_id=target_node.id,
                    relation_type=relation_type,
                    description=f"{source_node.label} {relation_type.value} {target_node.label}",
                    provenance=self._create_provenance_for_match(
                        segment,
                        match,
                        extraction_method
                    ),
                    confidence=0.85,
                    created_by=actor_id,
                    modified_by=actor_id,
                    validation_status=ValidationStatus.PENDING,
                )

                edges.append(edge)

        # If LLM is available, extract more complex relationships
        if self.llm_model_func:
            llm_edges = self._extract_relationships_with_llm(
                segment,
                entities,
                extraction_method,
                actor_id
            )
            edges.extend(llm_edges)

        return edges

    def _extract_entities_with_llm(
        self,
        segment: TextSegment,
        extraction_method: ExtractionMethod,
        actor_id: str
    ) -> List[Node]:
        """
        Extract entities using LLM.

        This is a placeholder for LLM-based extraction.
        Should be implemented based on the specific LLM being used.
        """
        # TODO: Implement LLM-based entity extraction
        # For now, return empty list
        return []

    def _extract_relationships_with_llm(
        self,
        segment: TextSegment,
        entities: List[Node],
        extraction_method: ExtractionMethod,
        actor_id: str
    ) -> List[Edge]:
        """
        Extract relationships using LLM.

        This is a placeholder for LLM-based relationship extraction.
        Should be implemented based on the specific LLM being used.
        """
        # TODO: Implement LLM-based relationship extraction
        # For now, return empty list
        return []

    def _find_or_create_article_node(
        self,
        article_number: str,
        existing_nodes: List[Node],
        segment: TextSegment,
        extraction_method: ExtractionMethod,
        actor_id: str
    ) -> Node:
        """
        Find an existing node for an article or create a new one.
        """
        # Try to find existing node
        for node in existing_nodes:
            if (node.entity_type == EntityType.NORMA and
                node.article_number == article_number):
                return node

        # Create new node
        node = Node(
            label=f"Art. {article_number}",
            entity_type=EntityType.NORMA,
            description=f"Articolo {article_number}",
            article_number=article_number,
            provenance=Provenance(
                source_file=segment.provenance.source_file,
                source_url=segment.provenance.source_url,
                source_type=segment.provenance.source_type,
                extraction_method=extraction_method,
                extraction_timestamp=datetime.now(),
                extractor_version=self.extractor_version,
            ),
            confidence=0.8,
            created_by=actor_id,
            modified_by=actor_id,
            validation_status=ValidationStatus.PENDING,
        )

        existing_nodes.append(node)
        return node

    def _create_provenance_for_match(
        self,
        segment: TextSegment,
        match: re.Match,
        extraction_method: ExtractionMethod
    ) -> Provenance:
        """
        Create provenance information for a regex match.
        """
        # Get character positions in the segment
        char_start = match.start()
        char_end = match.end()

        # Get context around the match
        context_size = 100
        text_start = max(0, char_start - context_size)
        text_end = min(len(segment.text), char_end + context_size)

        return Provenance(
            source_file=segment.provenance.source_file,
            source_url=segment.provenance.source_url,
            source_type=segment.provenance.source_type,
            line_start=segment.provenance.line_start,
            line_end=segment.provenance.line_end,
            char_start=char_start,
            char_end=char_end,
            page=segment.provenance.page,
            section=segment.provenance.section,
            extraction_method=extraction_method,
            extraction_timestamp=datetime.now(),
            extractor_version=self.extractor_version,
            raw_text=match.group(0),
            context_before=segment.text[text_start:char_start],
            context_after=segment.text[char_end:text_end],
        )

    def create_manual_node(
        self,
        label: str,
        entity_type: EntityType,
        description: str = "",
        attributes: Optional[Dict[str, Any]] = None,
        article_number: Optional[str] = None,
        law_reference: Optional[str] = None,
        actor_id: str = "user",
        confidence: float = 1.0
    ) -> Node:
        """
        Manually create a node with provenance tracking.

        Args:
            label: Node label
            entity_type: Type of entity
            description: Description of the entity
            attributes: Additional attributes
            article_number: Article number (if applicable)
            law_reference: Legal reference
            actor_id: ID of the user creating the node
            confidence: Confidence score (default 1.0 for manual)

        Returns:
            Created Node object
        """
        provenance = Provenance(
            source_type="manual",
            extraction_method=ExtractionMethod.MANUAL,
            extraction_timestamp=datetime.now(),
            extractor_version=self.extractor_version,
        )

        node = Node(
            label=label,
            entity_type=entity_type,
            description=description,
            attributes=attributes or {},
            article_number=article_number,
            law_reference=law_reference,
            provenance=provenance,
            confidence=confidence,
            created_by=actor_id,
            modified_by=actor_id,
            validation_status=ValidationStatus.APPROVED if confidence == 1.0 else ValidationStatus.PENDING,
        )

        return node

    def create_manual_edge(
        self,
        source_node: Node,
        target_node: Node,
        relation_type: RelationType,
        description: str = "",
        attributes: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
        actor_id: str = "user",
        confidence: float = 1.0
    ) -> Edge:
        """
        Manually create an edge with provenance tracking.

        Args:
            source_node: Source node
            target_node: Target node
            relation_type: Type of relationship
            description: Description of the relationship
            attributes: Additional attributes
            weight: Relationship weight
            actor_id: ID of the user creating the edge
            confidence: Confidence score (default 1.0 for manual)

        Returns:
            Created Edge object
        """
        provenance = Provenance(
            source_type="manual",
            extraction_method=ExtractionMethod.MANUAL,
            extraction_timestamp=datetime.now(),
            extractor_version=self.extractor_version,
        )

        edge = Edge(
            source_id=source_node.id,
            target_id=target_node.id,
            relation_type=relation_type,
            description=description,
            attributes=attributes or {},
            weight=weight,
            provenance=provenance,
            confidence=confidence,
            created_by=actor_id,
            modified_by=actor_id,
            validation_status=ValidationStatus.APPROVED if confidence == 1.0 else ValidationStatus.PENDING,
        )

        return edge
