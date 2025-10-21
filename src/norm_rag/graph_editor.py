"""
Graph editor for manual manipulation of knowledge graphs.

Provides comprehensive CRUD operations on nodes and edges with full audit trail.
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from copy import deepcopy

from .models import (
    Node, Edge, EntityType, RelationType, Provenance,
    ExtractionMethod, ValidationStatus, AuditLogEntry
)
from .graph_builder import LegalKnowledgeGraph


class GraphEditorException(Exception):
    """Exception raised by GraphEditor operations."""
    pass


class GraphEditor:
    """
    Editor for manual manipulation of legal knowledge graphs.

    Supports:
    - Adding/removing/modifying nodes and edges
    - Merging and splitting nodes
    - Batch transformations
    - Full audit trail
    """

    def __init__(self, graph: LegalKnowledgeGraph, actor_id: str = "user"):
        """
        Initialize GraphEditor.

        Args:
            graph: The graph to edit
            actor_id: ID of the actor performing edits
        """
        self.graph = graph
        self.actor_id = actor_id
        self.audit_log: List[AuditLogEntry] = []

    # ===== NODE OPERATIONS =====

    def add_node(
        self,
        label: str,
        entity_type: EntityType,
        description: str = "",
        attributes: Optional[Dict[str, Any]] = None,
        article_number: Optional[str] = None,
        law_reference: Optional[str] = None,
        confidence: float = 1.0,
        tags: Optional[Set[str]] = None
    ) -> Node:
        """
        Add a new node to the graph.

        Args:
            label: Node label
            entity_type: Type of entity
            description: Description
            attributes: Additional attributes
            article_number: Article number (if applicable)
            law_reference: Legal reference
            confidence: Confidence score
            tags: Tags for categorization

        Returns:
            The created Node

        Raises:
            GraphEditorException: If operation fails
        """
        # Create provenance for manual creation
        provenance = Provenance(
            source_type="manual",
            extraction_method=ExtractionMethod.MANUAL,
            extraction_timestamp=datetime.now(),
            extractor_version="graph_editor_1.0",
        )

        # Create node
        node = Node(
            label=label,
            entity_type=entity_type,
            description=description,
            attributes=attributes or {},
            article_number=article_number,
            law_reference=law_reference,
            provenance=provenance,
            confidence=confidence,
            created_by=self.actor_id,
            modified_by=self.actor_id,
            validation_status=ValidationStatus.APPROVED if confidence == 1.0 else ValidationStatus.PENDING,
            tags=tags or set(),
        )

        # Add to graph
        success = self.graph.add_node(node)

        if not success:
            raise GraphEditorException(f"Failed to add node: {label}")

        # Log the operation
        self._log_operation(
            operation="add_node",
            entity_type="node",
            entity_id=node.id,
            new_value=node.to_dict(),
            comments=f"Added node: {label}"
        )

        return node

    def remove_node(
        self,
        node_id: str,
        remove_connected_edges: bool = True
    ) -> bool:
        """
        Remove a node from the graph.

        Args:
            node_id: ID of node to remove
            remove_connected_edges: Whether to remove connected edges

        Returns:
            True if successful

        Raises:
            GraphEditorException: If node doesn't exist
        """
        node = self.graph.get_node(node_id)

        if not node:
            raise GraphEditorException(f"Node not found: {node_id}")

        # Store old value for audit log
        old_value = node.to_dict()

        # Remove connected edges if requested
        if remove_connected_edges:
            edges_to_remove = (
                self.graph.get_edges_from_node(node_id) +
                self.graph.get_edges_to_node(node_id)
            )

            for edge in edges_to_remove:
                self.remove_edge(edge.id)

        # Remove from graph
        del self.graph.nodes[node_id]
        self.graph.nx_graph.remove_node(node_id)

        # Update indexes
        self.graph._entity_type_index[node.entity_type].discard(node_id)

        if node.article_number and node.article_number in self.graph._article_index:
            del self.graph._article_index[node.article_number]

        # Update metadata
        self.graph.metadata.node_count = len(self.graph.nodes)
        self.graph.metadata.modified_at = datetime.now()

        # Log operation
        self._log_operation(
            operation="remove_node",
            entity_type="node",
            entity_id=node_id,
            old_value=old_value,
            comments=f"Removed node: {node.label}"
        )

        return True

    def modify_node(
        self,
        node_id: str,
        label: Optional[str] = None,
        description: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        tags: Optional[Set[str]] = None,
        **kwargs
    ) -> Node:
        """
        Modify an existing node.

        Args:
            node_id: ID of node to modify
            label: New label (optional)
            description: New description (optional)
            attributes: New attributes (optional, merged with existing)
            confidence: New confidence score (optional)
            tags: New tags (optional, merged with existing)
            **kwargs: Additional node fields to update

        Returns:
            The modified Node

        Raises:
            GraphEditorException: If node doesn't exist
        """
        node = self.graph.get_node(node_id)

        if not node:
            raise GraphEditorException(f"Node not found: {node_id}")

        # Store old value for audit log
        old_value = node.to_dict()

        # Apply modifications
        if label is not None:
            node.label = label

        if description is not None:
            node.description = description

        if attributes is not None:
            node.attributes.update(attributes)

        if confidence is not None:
            node.confidence = confidence

        if tags is not None:
            node.tags.update(tags)

        # Apply additional kwargs
        for key, value in kwargs.items():
            if hasattr(node, key):
                setattr(node, key, value)

        # Update metadata
        node.modified_at = datetime.now()
        node.modified_by = self.actor_id
        node.version += 1

        # Update graph
        self.graph.metadata.modified_at = datetime.now()

        # Log operation
        self._log_operation(
            operation="modify_node",
            entity_type="node",
            entity_id=node_id,
            old_value=old_value,
            new_value=node.to_dict(),
            comments=f"Modified node: {node.label}"
        )

        return node

    def merge_nodes(
        self,
        node_ids: List[str],
        merged_label: str,
        merged_description: str = "",
        keep_all_attributes: bool = True
    ) -> Node:
        """
        Merge multiple nodes into one.

        Args:
            node_ids: IDs of nodes to merge
            merged_label: Label for merged node
            merged_description: Description for merged node
            keep_all_attributes: Whether to merge all attributes

        Returns:
            The merged Node

        Raises:
            GraphEditorException: If nodes don't exist or merge fails
        """
        if len(node_ids) < 2:
            raise GraphEditorException("Need at least 2 nodes to merge")

        # Get all nodes
        nodes = [self.graph.get_node(nid) for nid in node_ids]

        if None in nodes:
            raise GraphEditorException("One or more nodes not found")

        # Create merged node with combined attributes
        merged_attributes = {}
        merged_tags = set()
        merged_confidence = sum(n.confidence for n in nodes) / len(nodes)

        if keep_all_attributes:
            for node in nodes:
                merged_attributes.update(node.attributes)
                merged_tags.update(node.tags)

        # Use entity type of first node
        entity_type = nodes[0].entity_type

        # Create new merged node
        merged_node = self.add_node(
            label=merged_label,
            entity_type=entity_type,
            description=merged_description or f"Merged from: {', '.join(n.label for n in nodes)}",
            attributes=merged_attributes,
            confidence=merged_confidence,
            tags=merged_tags
        )

        # Redirect all edges from old nodes to merged node
        for old_node in nodes:
            # Outgoing edges
            for edge in self.graph.get_edges_from_node(old_node.id):
                if edge.target_id not in node_ids:  # Don't create self-loops
                    self.add_edge(
                        source_id=merged_node.id,
                        target_id=edge.target_id,
                        relation_type=edge.relation_type,
                        description=edge.description,
                        weight=edge.weight,
                        confidence=edge.confidence
                    )

            # Incoming edges
            for edge in self.graph.get_edges_to_node(old_node.id):
                if edge.source_id not in node_ids:  # Don't create self-loops
                    self.add_edge(
                        source_id=edge.source_id,
                        target_id=merged_node.id,
                        relation_type=edge.relation_type,
                        description=edge.description,
                        weight=edge.weight,
                        confidence=edge.confidence
                    )

        # Remove old nodes
        for old_node in nodes:
            self.remove_node(old_node.id, remove_connected_edges=True)

        # Log operation
        self._log_operation(
            operation="merge_nodes",
            entity_type="node",
            entity_id=merged_node.id,
            new_value=merged_node.to_dict(),
            operation_context={"merged_from": node_ids},
            comments=f"Merged {len(nodes)} nodes into: {merged_label}"
        )

        return merged_node

    def split_node(
        self,
        node_id: str,
        split_configs: List[Dict[str, Any]]
    ) -> List[Node]:
        """
        Split a node into multiple nodes.

        Args:
            node_id: ID of node to split
            split_configs: List of configs for new nodes, each with keys:
                - label: str
                - description: str
                - attributes: Dict (optional)
                - tags: Set (optional)

        Returns:
            List of newly created Nodes

        Raises:
            GraphEditorException: If node doesn't exist or split fails
        """
        original_node = self.graph.get_node(node_id)

        if not original_node:
            raise GraphEditorException(f"Node not found: {node_id}")

        if len(split_configs) < 2:
            raise GraphEditorException("Need at least 2 split configs")

        # Create new nodes
        new_nodes = []

        for config in split_configs:
            new_node = self.add_node(
                label=config["label"],
                entity_type=original_node.entity_type,
                description=config.get("description", ""),
                attributes=config.get("attributes", {}),
                confidence=original_node.confidence,
                tags=config.get("tags", set())
            )
            new_nodes.append(new_node)

        # Distribute edges to new nodes
        # Simple strategy: duplicate all edges to all new nodes
        # Can be customized with more sophisticated logic

        outgoing_edges = self.graph.get_edges_from_node(node_id)
        incoming_edges = self.graph.get_edges_to_node(node_id)

        for new_node in new_nodes:
            # Duplicate outgoing edges
            for edge in outgoing_edges:
                self.add_edge(
                    source_id=new_node.id,
                    target_id=edge.target_id,
                    relation_type=edge.relation_type,
                    description=edge.description,
                    weight=edge.weight,
                    confidence=edge.confidence
                )

            # Duplicate incoming edges
            for edge in incoming_edges:
                self.add_edge(
                    source_id=edge.source_id,
                    target_id=new_node.id,
                    relation_type=edge.relation_type,
                    description=edge.description,
                    weight=edge.weight,
                    confidence=edge.confidence
                )

        # Remove original node
        self.remove_node(node_id, remove_connected_edges=True)

        # Log operation
        self._log_operation(
            operation="split_node",
            entity_type="node",
            entity_id=node_id,
            new_value=[n.to_dict() for n in new_nodes],
            operation_context={"split_into": [n.id for n in new_nodes]},
            comments=f"Split node {original_node.label} into {len(new_nodes)} nodes"
        )

        return new_nodes

    # ===== EDGE OPERATIONS =====

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        description: str = "",
        attributes: Optional[Dict[str, Any]] = None,
        weight: float = 1.0,
        directed: bool = True,
        confidence: float = 1.0,
        tags: Optional[Set[str]] = None
    ) -> Edge:
        """
        Add a new edge to the graph.

        Args:
            source_id: Source node ID
            target_id: Target node ID
            relation_type: Type of relationship
            description: Description
            attributes: Additional attributes
            weight: Edge weight
            directed: Whether edge is directed
            confidence: Confidence score
            tags: Tags for categorization

        Returns:
            The created Edge

        Raises:
            GraphEditorException: If nodes don't exist or operation fails
        """
        # Verify nodes exist
        if not self.graph.get_node(source_id):
            raise GraphEditorException(f"Source node not found: {source_id}")

        if not self.graph.get_node(target_id):
            raise GraphEditorException(f"Target node not found: {target_id}")

        # Create provenance
        provenance = Provenance(
            source_type="manual",
            extraction_method=ExtractionMethod.MANUAL,
            extraction_timestamp=datetime.now(),
            extractor_version="graph_editor_1.0",
        )

        # Create edge
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description,
            attributes=attributes or {},
            weight=weight,
            directed=directed,
            provenance=provenance,
            confidence=confidence,
            created_by=self.actor_id,
            modified_by=self.actor_id,
            validation_status=ValidationStatus.APPROVED if confidence == 1.0 else ValidationStatus.PENDING,
            tags=tags or set(),
        )

        # Add to graph
        success = self.graph.add_edge(edge)

        if not success:
            raise GraphEditorException(f"Failed to add edge: {source_id} -> {target_id}")

        # Log operation
        self._log_operation(
            operation="add_edge",
            entity_type="edge",
            entity_id=edge.id,
            new_value=edge.to_dict(),
            comments=f"Added edge: {source_id} -> {target_id}"
        )

        return edge

    def remove_edge(self, edge_id: str) -> bool:
        """
        Remove an edge from the graph.

        Args:
            edge_id: ID of edge to remove

        Returns:
            True if successful

        Raises:
            GraphEditorException: If edge doesn't exist
        """
        edge = self.graph.get_edge(edge_id)

        if not edge:
            raise GraphEditorException(f"Edge not found: {edge_id}")

        # Store old value for audit log
        old_value = edge.to_dict()

        # Remove from graph
        del self.graph.edges[edge_id]
        self.graph.nx_graph.remove_edge(edge.source_id, edge.target_id, key=edge_id)

        # Update indexes
        self.graph._relation_type_index[edge.relation_type].discard(edge_id)

        # Update metadata
        self.graph.metadata.edge_count = len(self.graph.edges)
        self.graph.metadata.modified_at = datetime.now()

        # Log operation
        self._log_operation(
            operation="remove_edge",
            entity_type="edge",
            entity_id=edge_id,
            old_value=old_value,
            comments=f"Removed edge: {edge.source_id} -> {edge.target_id}"
        )

        return True

    def modify_edge(
        self,
        edge_id: str,
        relation_type: Optional[RelationType] = None,
        description: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        weight: Optional[float] = None,
        confidence: Optional[float] = None,
        tags: Optional[Set[str]] = None,
        **kwargs
    ) -> Edge:
        """
        Modify an existing edge.

        Args:
            edge_id: ID of edge to modify
            relation_type: New relation type (optional)
            description: New description (optional)
            attributes: New attributes (optional, merged)
            weight: New weight (optional)
            confidence: New confidence (optional)
            tags: New tags (optional, merged)
            **kwargs: Additional fields to update

        Returns:
            The modified Edge

        Raises:
            GraphEditorException: If edge doesn't exist
        """
        edge = self.graph.get_edge(edge_id)

        if not edge:
            raise GraphEditorException(f"Edge not found: {edge_id}")

        # Store old value
        old_value = edge.to_dict()

        # Apply modifications
        if relation_type is not None:
            edge.relation_type = relation_type

        if description is not None:
            edge.description = description

        if attributes is not None:
            edge.attributes.update(attributes)

        if weight is not None:
            edge.weight = weight

        if confidence is not None:
            edge.confidence = confidence

        if tags is not None:
            edge.tags.update(tags)

        # Apply additional kwargs
        for key, value in kwargs.items():
            if hasattr(edge, key):
                setattr(edge, key, value)

        # Update metadata
        edge.modified_at = datetime.now()
        edge.modified_by = self.actor_id
        edge.version += 1

        # Update graph
        self.graph.metadata.modified_at = datetime.now()

        # Log operation
        self._log_operation(
            operation="modify_edge",
            entity_type="edge",
            entity_id=edge_id,
            old_value=old_value,
            new_value=edge.to_dict(),
            comments=f"Modified edge: {edge.source_id} -> {edge.target_id}"
        )

        return edge

    # ===== BATCH OPERATIONS =====

    def batch_transform(
        self,
        filter_func: callable,
        transform_func: callable,
        entity_type: str = "node"  # "node" or "edge"
    ) -> int:
        """
        Apply a transformation to multiple nodes or edges.

        Args:
            filter_func: Function to filter entities (returns bool)
            transform_func: Function to transform entity (modifies in place)
            entity_type: "node" or "edge"

        Returns:
            Number of entities transformed

        Example:
            # Add a tag to all NORMA nodes
            editor.batch_transform(
                filter_func=lambda n: n.entity_type == EntityType.NORMA,
                transform_func=lambda n: n.tags.add("codice_penale"),
                entity_type="node"
            )
        """
        count = 0

        if entity_type == "node":
            entities = list(self.graph.nodes.values())
        elif entity_type == "edge":
            entities = list(self.graph.edges.values())
        else:
            raise ValueError("entity_type must be 'node' or 'edge'")

        for entity in entities:
            if filter_func(entity):
                old_value = entity.to_dict()
                transform_func(entity)
                entity.modified_at = datetime.now()
                entity.modified_by = self.actor_id
                entity.version += 1

                # Log operation
                self._log_operation(
                    operation="batch_transform",
                    entity_type=entity_type,
                    entity_id=entity.id,
                    old_value=old_value,
                    new_value=entity.to_dict(),
                    comments="Batch transformation applied"
                )

                count += 1

        self.graph.metadata.modified_at = datetime.now()

        return count

    # ===== AUDIT TRAIL =====

    def _log_operation(
        self,
        operation: str,
        entity_type: str,
        entity_id: str,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        operation_context: Optional[Dict[str, Any]] = None,
        comments: str = ""
    ):
        """Log an operation to the audit trail."""
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=self.actor_id,
            actor_type="user",
            old_value=old_value,
            new_value=new_value,
            operation_context=operation_context or {},
            comments=comments,
        )

        self.audit_log.append(entry)

    def get_audit_log(
        self,
        entity_id: Optional[str] = None,
        operation: Optional[str] = None
    ) -> List[AuditLogEntry]:
        """
        Get audit log entries.

        Args:
            entity_id: Filter by entity ID (optional)
            operation: Filter by operation type (optional)

        Returns:
            List of audit log entries
        """
        entries = self.audit_log

        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]

        if operation:
            entries = [e for e in entries if e.operation == operation]

        return entries

    def export_audit_log(self) -> List[Dict[str, Any]]:
        """Export audit log to dictionary format."""
        return [entry.to_dict() for entry in self.audit_log]
