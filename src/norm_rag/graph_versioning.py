"""
Graph versioning system for tracking changes and managing multiple versions.

Supports:
- Creating snapshots of graph states
- Comparing versions (diff)
- Rolling back to previous versions
- Branching for parallel development
- Merging different versions
"""

from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
from copy import deepcopy
import json
from pathlib import Path

from .models import Node, Edge
from .graph_builder import LegalKnowledgeGraph


class GraphSnapshot:
    """
    A snapshot of a graph at a specific point in time.
    """

    def __init__(
        self,
        graph: LegalKnowledgeGraph,
        version_id: str,
        description: str = "",
        parent_version: Optional[str] = None
    ):
        """
        Create a snapshot of a graph.

        Args:
            graph: The graph to snapshot
            version_id: Version identifier
            description: Description of this version
            parent_version: ID of parent version (if any)
        """
        self.version_id = version_id
        self.description = description
        self.parent_version = parent_version
        self.timestamp = datetime.now()

        # Deep copy of the graph data
        self.graph_data = graph.to_dict()

        # Statistics
        self.node_count = len(graph.nodes)
        self.edge_count = len(graph.edges)

    def to_dict(self) -> Dict[str, Any]:
        """Convert snapshot to dictionary."""
        return {
            "version_id": self.version_id,
            "description": self.description,
            "parent_version": self.parent_version,
            "timestamp": self.timestamp.isoformat(),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "graph_data": self.graph_data,
        }

    def save_to_file(self, file_path: Path):
        """Save snapshot to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load_from_file(cls, file_path: Path) -> "GraphSnapshot":
        """Load snapshot from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        snapshot = cls.__new__(cls)
        snapshot.version_id = data["version_id"]
        snapshot.description = data["description"]
        snapshot.parent_version = data.get("parent_version")
        snapshot.timestamp = datetime.fromisoformat(data["timestamp"])
        snapshot.node_count = data["node_count"]
        snapshot.edge_count = data["edge_count"]
        snapshot.graph_data = data["graph_data"]

        return snapshot


class GraphDiff:
    """
    Represents the difference between two graph versions.
    """

    def __init__(
        self,
        from_version: str,
        to_version: str
    ):
        """
        Initialize graph diff.

        Args:
            from_version: Source version ID
            to_version: Target version ID
        """
        self.from_version = from_version
        self.to_version = to_version

        # Changes
        self.nodes_added: List[Dict[str, Any]] = []
        self.nodes_removed: List[Dict[str, Any]] = []
        self.nodes_modified: List[Dict[str, Any]] = []

        self.edges_added: List[Dict[str, Any]] = []
        self.edges_removed: List[Dict[str, Any]] = []
        self.edges_modified: List[Dict[str, Any]] = []

    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return bool(
            self.nodes_added or self.nodes_removed or self.nodes_modified or
            self.edges_added or self.edges_removed or self.edges_modified
        )

    def get_summary(self) -> str:
        """Get a human-readable summary of changes."""
        lines = [
            f"Diff: {self.from_version} → {self.to_version}",
            f"Nodes: +{len(self.nodes_added)} -{len(self.nodes_removed)} ~{len(self.nodes_modified)}",
            f"Edges: +{len(self.edges_added)} -{len(self.edges_removed)} ~{len(self.edges_modified)}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convert diff to dictionary."""
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "nodes_added": self.nodes_added,
            "nodes_removed": self.nodes_removed,
            "nodes_modified": self.nodes_modified,
            "edges_added": self.edges_added,
            "edges_removed": self.edges_removed,
            "edges_modified": self.edges_modified,
        }


class MergeConflict:
    """
    Represents a conflict when merging two graph versions.
    """

    def __init__(
        self,
        entity_type: str,  # "node" or "edge"
        entity_id: str,
        conflict_type: str,  # "modified_in_both", "deleted_in_one"
        version_a_value: Any,
        version_b_value: Any
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.conflict_type = conflict_type
        self.version_a_value = version_a_value
        self.version_b_value = version_b_value

    def __repr__(self) -> str:
        return (
            f"MergeConflict({self.entity_type} {self.entity_id}: "
            f"{self.conflict_type})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert conflict to dictionary."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "conflict_type": self.conflict_type,
            "version_a_value": self.version_a_value,
            "version_b_value": self.version_b_value,
        }


class GraphVersionManager:
    """
    Manages multiple versions of a legal knowledge graph.

    Supports branching, diffing, merging, and rollback operations.
    """

    def __init__(self, base_graph: LegalKnowledgeGraph):
        """
        Initialize version manager.

        Args:
            base_graph: The initial graph
        """
        self.snapshots: Dict[str, GraphSnapshot] = {}
        self.current_version: str = "v1.0"

        # Create initial snapshot
        self.create_snapshot(
            graph=base_graph,
            version_id=self.current_version,
            description="Initial version"
        )

    def create_snapshot(
        self,
        graph: LegalKnowledgeGraph,
        version_id: str,
        description: str = "",
        parent_version: Optional[str] = None
    ) -> GraphSnapshot:
        """
        Create a snapshot of the current graph state.

        Args:
            graph: The graph to snapshot
            version_id: Version identifier (e.g., "v1.0", "v1.1-branch")
            description: Description of this version
            parent_version: ID of parent version

        Returns:
            The created GraphSnapshot
        """
        if version_id in self.snapshots:
            raise ValueError(f"Version {version_id} already exists")

        # Use current version as parent if not specified
        if parent_version is None and self.current_version != version_id:
            parent_version = self.current_version

        snapshot = GraphSnapshot(
            graph=graph,
            version_id=version_id,
            description=description,
            parent_version=parent_version
        )

        self.snapshots[version_id] = snapshot
        self.current_version = version_id

        return snapshot

    def get_snapshot(self, version_id: str) -> Optional[GraphSnapshot]:
        """Get a specific snapshot."""
        return self.snapshots.get(version_id)

    def list_versions(self) -> List[str]:
        """List all available versions."""
        return sorted(self.snapshots.keys())

    def restore_snapshot(self, version_id: str) -> LegalKnowledgeGraph:
        """
        Restore a graph from a snapshot.

        Args:
            version_id: ID of the version to restore

        Returns:
            Restored LegalKnowledgeGraph

        Raises:
            ValueError: If version doesn't exist
        """
        snapshot = self.snapshots.get(version_id)

        if not snapshot:
            raise ValueError(f"Version not found: {version_id}")

        # Reconstruct graph from snapshot data
        graph = self._reconstruct_graph_from_data(snapshot.graph_data)

        return graph

    def compare_versions(
        self,
        from_version: str,
        to_version: str
    ) -> GraphDiff:
        """
        Compare two versions and generate a diff.

        Args:
            from_version: Source version ID
            to_version: Target version ID

        Returns:
            GraphDiff object

        Raises:
            ValueError: If versions don't exist
        """
        snapshot_from = self.snapshots.get(from_version)
        snapshot_to = self.snapshots.get(to_version)

        if not snapshot_from:
            raise ValueError(f"Version not found: {from_version}")

        if not snapshot_to:
            raise ValueError(f"Version not found: {to_version}")

        diff = GraphDiff(from_version, to_version)

        # Compare nodes
        nodes_from = {n["id"]: n for n in snapshot_from.graph_data["nodes"]}
        nodes_to = {n["id"]: n for n in snapshot_to.graph_data["nodes"]}

        # Added nodes
        for node_id in nodes_to.keys() - nodes_from.keys():
            diff.nodes_added.append(nodes_to[node_id])

        # Removed nodes
        for node_id in nodes_from.keys() - nodes_to.keys():
            diff.nodes_removed.append(nodes_from[node_id])

        # Modified nodes
        for node_id in nodes_from.keys() & nodes_to.keys():
            if nodes_from[node_id] != nodes_to[node_id]:
                diff.nodes_modified.append({
                    "id": node_id,
                    "from": nodes_from[node_id],
                    "to": nodes_to[node_id],
                })

        # Compare edges
        edges_from = {e["id"]: e for e in snapshot_from.graph_data["edges"]}
        edges_to = {e["id"]: e for e in snapshot_to.graph_data["edges"]}

        # Added edges
        for edge_id in edges_to.keys() - edges_from.keys():
            diff.edges_added.append(edges_to[edge_id])

        # Removed edges
        for edge_id in edges_from.keys() - edges_to.keys():
            diff.edges_removed.append(edges_from[edge_id])

        # Modified edges
        for edge_id in edges_from.keys() & edges_to.keys():
            if edges_from[edge_id] != edges_to[edge_id]:
                diff.edges_modified.append({
                    "id": edge_id,
                    "from": edges_from[edge_id],
                    "to": edges_to[edge_id],
                })

        return diff

    def branch(
        self,
        from_version: str,
        new_version_id: str,
        description: str = ""
    ) -> GraphSnapshot:
        """
        Create a new branch from an existing version.

        Args:
            from_version: Version to branch from
            new_version_id: ID for the new branch
            description: Description of the branch

        Returns:
            GraphSnapshot for the new branch

        Raises:
            ValueError: If source version doesn't exist
        """
        source_snapshot = self.snapshots.get(from_version)

        if not source_snapshot:
            raise ValueError(f"Version not found: {from_version}")

        # Restore the graph from source version
        graph = self.restore_snapshot(from_version)

        # Create new snapshot with source as parent
        branch_snapshot = self.create_snapshot(
            graph=graph,
            version_id=new_version_id,
            description=description or f"Branch from {from_version}",
            parent_version=from_version
        )

        return branch_snapshot

    def merge(
        self,
        version_a: str,
        version_b: str,
        merged_version_id: str,
        conflict_resolution: str = "take_b",  # "take_a", "take_b", "manual"
        manual_resolutions: Optional[Dict[str, Any]] = None
    ) -> Tuple[LegalKnowledgeGraph, List[MergeConflict]]:
        """
        Merge two graph versions.

        Args:
            version_a: First version ID
            version_b: Second version ID
            merged_version_id: ID for the merged version
            conflict_resolution: Strategy for resolving conflicts
            manual_resolutions: Manual conflict resolutions

        Returns:
            Tuple of (merged graph, list of conflicts)

        Raises:
            ValueError: If versions don't exist or conflict resolution fails
        """
        snapshot_a = self.snapshots.get(version_a)
        snapshot_b = self.snapshots.get(version_b)

        if not snapshot_a or not snapshot_b:
            raise ValueError("One or both versions not found")

        # Start with version A as base
        merged_graph = self.restore_snapshot(version_a)
        conflicts: List[MergeConflict] = []

        # Get differences
        diff_a_to_b = self.compare_versions(version_a, version_b)

        # Apply non-conflicting changes from B
        # Add new nodes from B
        for node_data in diff_a_to_b.nodes_added:
            node = self._dict_to_node(node_data)
            merged_graph.add_node(node)

        # Add new edges from B
        for edge_data in diff_a_to_b.edges_added:
            edge = self._dict_to_edge(edge_data)
            merged_graph.add_edge(edge)

        # Handle modifications (potential conflicts)
        for mod in diff_a_to_b.nodes_modified:
            node_id = mod["id"]

            # Check if this was also modified in A (conflict)
            # For now, apply conflict resolution strategy
            if conflict_resolution == "take_b":
                # Replace with B's version
                node = self._dict_to_node(mod["to"])
                merged_graph.nodes[node_id] = node
            elif conflict_resolution == "take_a":
                # Keep A's version (do nothing)
                pass
            elif conflict_resolution == "manual":
                # Record conflict for manual resolution
                conflict = MergeConflict(
                    entity_type="node",
                    entity_id=node_id,
                    conflict_type="modified_in_both",
                    version_a_value=mod["from"],
                    version_b_value=mod["to"]
                )
                conflicts.append(conflict)

        # Handle edge modifications similarly
        for mod in diff_a_to_b.edges_modified:
            edge_id = mod["id"]

            if conflict_resolution == "take_b":
                edge = self._dict_to_edge(mod["to"])
                merged_graph.edges[edge_id] = edge
            elif conflict_resolution == "take_a":
                pass
            elif conflict_resolution == "manual":
                conflict = MergeConflict(
                    entity_type="edge",
                    entity_id=edge_id,
                    conflict_type="modified_in_both",
                    version_a_value=mod["from"],
                    version_b_value=mod["to"]
                )
                conflicts.append(conflict)

        # Create snapshot of merged graph
        self.create_snapshot(
            graph=merged_graph,
            version_id=merged_version_id,
            description=f"Merge of {version_a} and {version_b}",
            parent_version=version_a
        )

        return merged_graph, conflicts

    def rollback(self, version_id: str) -> LegalKnowledgeGraph:
        """
        Rollback to a previous version.

        Args:
            version_id: Version to rollback to

        Returns:
            Restored graph

        Raises:
            ValueError: If version doesn't exist
        """
        graph = self.restore_snapshot(version_id)
        self.current_version = version_id

        return graph

    def save_version_to_file(self, version_id: str, file_path: Path):
        """
        Save a specific version to a file.

        Args:
            version_id: Version to save
            file_path: Path to save to

        Raises:
            ValueError: If version doesn't exist
        """
        snapshot = self.snapshots.get(version_id)

        if not snapshot:
            raise ValueError(f"Version not found: {version_id}")

        snapshot.save_to_file(file_path)

    def load_version_from_file(self, file_path: Path) -> GraphSnapshot:
        """
        Load a version from a file.

        Args:
            file_path: Path to load from

        Returns:
            Loaded GraphSnapshot
        """
        snapshot = GraphSnapshot.load_from_file(file_path)
        self.snapshots[snapshot.version_id] = snapshot

        return snapshot

    # ===== Helper Methods =====

    def _reconstruct_graph_from_data(self, graph_data: Dict[str, Any]) -> LegalKnowledgeGraph:
        """Reconstruct a LegalKnowledgeGraph from serialized data."""
        from .models import GraphMetadata

        # Create new graph
        metadata_dict = graph_data["metadata"]
        metadata = GraphMetadata(
            graph_id=metadata_dict["graph_id"],
            name=metadata_dict["name"],
            description=metadata_dict["description"],
            version=metadata_dict["version"],
        )

        graph = LegalKnowledgeGraph(metadata=metadata)

        # Add nodes
        for node_data in graph_data["nodes"]:
            node = self._dict_to_node(node_data)
            graph.add_node(node)

        # Add edges
        for edge_data in graph_data["edges"]:
            edge = self._dict_to_edge(edge_data)
            graph.add_edge(edge)

        return graph

    def _dict_to_node(self, node_data: Dict[str, Any]) -> Node:
        """Convert dictionary to Node object."""
        from .models import EntityType, ValidationStatus, Provenance

        # Reconstruct provenance
        provenance_data = node_data.get("provenance")
        provenance = None

        if provenance_data:
            from .models import ExtractionMethod

            provenance = Provenance(
                source_file=provenance_data.get("source_file"),
                source_url=provenance_data.get("source_url"),
                source_type=provenance_data.get("source_type", "unknown"),
                extraction_method=ExtractionMethod(provenance_data.get("extraction_method", "automatic")),
            )

        node = Node(
            id=node_data["id"],
            label=node_data["label"],
            entity_type=EntityType(node_data["entity_type"]),
            description=node_data.get("description", ""),
            attributes=node_data.get("attributes", {}),
            article_number=node_data.get("article_number"),
            law_reference=node_data.get("law_reference"),
            provenance=provenance,
            confidence=node_data.get("confidence", 1.0),
            validation_status=ValidationStatus(node_data.get("validation_status", "pending")),
            tags=set(node_data.get("tags", [])),
        )

        return node

    def _dict_to_edge(self, edge_data: Dict[str, Any]) -> Edge:
        """Convert dictionary to Edge object."""
        from .models import RelationType, ValidationStatus, Provenance, ExtractionMethod

        # Reconstruct provenance
        provenance_data = edge_data.get("provenance")
        provenance = None

        if provenance_data:
            provenance = Provenance(
                source_file=provenance_data.get("source_file"),
                source_url=provenance_data.get("source_url"),
                source_type=provenance_data.get("source_type", "unknown"),
                extraction_method=ExtractionMethod(provenance_data.get("extraction_method", "automatic")),
            )

        edge = Edge(
            id=edge_data["id"],
            source_id=edge_data["source_id"],
            target_id=edge_data["target_id"],
            relation_type=RelationType(edge_data["relation_type"]),
            description=edge_data.get("description", ""),
            attributes=edge_data.get("attributes", {}),
            weight=edge_data.get("weight", 1.0),
            directed=edge_data.get("directed", True),
            provenance=provenance,
            confidence=edge_data.get("confidence", 1.0),
            validation_status=ValidationStatus(edge_data.get("validation_status", "pending")),
            tags=set(edge_data.get("tags", [])),
        )

        return edge

    def get_version_history(self, version_id: str) -> List[str]:
        """
        Get the history of a version by following parent relationships.

        Args:
            version_id: Version to trace history for

        Returns:
            List of version IDs from root to specified version
        """
        history = []
        current = version_id

        while current:
            snapshot = self.snapshots.get(current)

            if not snapshot:
                break

            history.insert(0, current)
            current = snapshot.parent_version

        return history
