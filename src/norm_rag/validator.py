"""
Domain validator for expert review and validation of legal knowledge graphs.

Provides tools for legal experts to:
- Review extracted entities and relationships
- Approve, reject, or modify extractions
- Add annotations and comments
- Track validation history
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import (
    Node, Edge, Validation, ValidationStatus
)
from .graph_builder import LegalKnowledgeGraph
from .graph_editor import GraphEditor


class ValidationTask:
    """
    A validation task assigned to a domain expert.
    """

    def __init__(
        self,
        task_id: str,
        entity_type: str,  # "node" or "edge"
        entity_id: str,
        entity_data: Dict[str, Any],
        priority: str = "normal",  # "low", "normal", "high", "urgent"
        assigned_to: Optional[str] = None
    ):
        self.task_id = task_id
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.entity_data = entity_data
        self.priority = priority
        self.assigned_to = assigned_to
        self.created_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.status = ValidationStatus.PENDING

    def complete(self, validation: Validation):
        """Mark task as completed with validation result."""
        self.completed_at = datetime.now()
        self.status = validation.status

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "entity_data": self.entity_data,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status.value,
        }


class DomainValidator:
    """
    Interface for domain experts to validate and improve knowledge graphs.

    Provides structured workflows for reviewing, annotating, and correcting
    automatically extracted legal knowledge.
    """

    def __init__(
        self,
        graph: LegalKnowledgeGraph,
        validator_id: str,
        validator_name: str = "",
        expertise_areas: Optional[List[str]] = None
    ):
        """
        Initialize domain validator.

        Args:
            graph: The graph to validate
            validator_id: Unique identifier for the validator
            validator_name: Human-readable name
            expertise_areas: List of legal expertise areas
        """
        self.graph = graph
        self.validator_id = validator_id
        self.validator_name = validator_name or validator_id
        self.expertise_areas = expertise_areas or []

        # Use GraphEditor for modifications
        self.editor = GraphEditor(graph, actor_id=validator_id)

        # Validation tasks
        self.tasks: Dict[str, ValidationTask] = {}

    # ===== VALIDATION WORKFLOW =====

    def get_pending_validations(
        self,
        entity_type: Optional[str] = None,
        priority: Optional[str] = None
    ) -> List[ValidationTask]:
        """
        Get list of pending validation tasks.

        Args:
            entity_type: Filter by "node" or "edge" (optional)
            priority: Filter by priority (optional)

        Returns:
            List of pending ValidationTask objects
        """
        tasks = [
            task for task in self.tasks.values()
            if task.status == ValidationStatus.PENDING
        ]

        if entity_type:
            tasks = [t for t in tasks if t.entity_type == entity_type]

        if priority:
            tasks = [t for t in tasks if t.priority == priority]

        # Sort by priority and creation time
        priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
        tasks.sort(key=lambda t: (priority_order.get(t.priority, 2), t.created_at))

        return tasks

    def create_validation_tasks(
        self,
        confidence_threshold: float = 0.8,
        filter_entity_type: Optional[str] = None
    ) -> List[ValidationTask]:
        """
        Automatically create validation tasks for low-confidence entities.

        Args:
            confidence_threshold: Entities below this confidence need validation
            filter_entity_type: Only create tasks for specific entity type

        Returns:
            List of created ValidationTask objects
        """
        tasks_created = []
        task_counter = len(self.tasks)

        # Create tasks for low-confidence nodes
        for node in self.graph.nodes.values():
            if node.confidence < confidence_threshold:
                if filter_entity_type and filter_entity_type != "node":
                    continue

                task_id = f"task_{task_counter:04d}"
                task = ValidationTask(
                    task_id=task_id,
                    entity_type="node",
                    entity_id=node.id,
                    entity_data=node.to_dict(),
                    priority="high" if node.confidence < 0.5 else "normal",
                    assigned_to=self.validator_id
                )

                self.tasks[task_id] = task
                tasks_created.append(task)
                task_counter += 1

        # Create tasks for low-confidence edges
        for edge in self.graph.edges.values():
            if edge.confidence < confidence_threshold:
                if filter_entity_type and filter_entity_type != "edge":
                    continue

                task_id = f"task_{task_counter:04d}"
                task = ValidationTask(
                    task_id=task_id,
                    entity_type="edge",
                    entity_id=edge.id,
                    entity_data=edge.to_dict(),
                    priority="high" if edge.confidence < 0.5 else "normal",
                    assigned_to=self.validator_id
                )

                self.tasks[task_id] = task
                tasks_created.append(task)
                task_counter += 1

        return tasks_created

    # ===== NODE VALIDATION =====

    def validate_node(
        self,
        node_id: str,
        status: ValidationStatus,
        comments: str = "",
        confidence: Optional[float] = None,
        modifications: Optional[Dict[str, Any]] = None,
        validation_criteria: Optional[List[str]] = None,
        references: Optional[List[str]] = None
    ) -> Validation:
        """
        Validate a node.

        Args:
            node_id: ID of node to validate
            status: Validation status (APPROVED, REJECTED, NEEDS_REVIEW, MODIFIED)
            comments: Validator comments
            confidence: Updated confidence score (optional)
            modifications: Modifications to apply (optional)
            validation_criteria: Criteria used for validation (optional)
            references: Supporting legal references (optional)

        Returns:
            Validation object

        Raises:
            ValueError: If node doesn't exist
        """
        node = self.graph.get_node(node_id)

        if not node:
            raise ValueError(f"Node not found: {node_id}")

        # Apply modifications if provided
        changes_made = {}

        if modifications:
            if "label" in modifications:
                node.label = modifications["label"]
                changes_made["label"] = modifications["label"]

            if "description" in modifications:
                node.description = modifications["description"]
                changes_made["description"] = modifications["description"]

            if "attributes" in modifications:
                node.attributes.update(modifications["attributes"])
                changes_made["attributes"] = modifications["attributes"]

            if "entity_type" in modifications:
                from .models import EntityType
                node.entity_type = EntityType(modifications["entity_type"])
                changes_made["entity_type"] = modifications["entity_type"]

        # Update confidence if provided
        if confidence is not None:
            node.confidence = confidence
            changes_made["confidence"] = confidence

        # Create validation record
        validation = Validation(
            validator_id=self.validator_id,
            validation_timestamp=datetime.now(),
            status=status,
            comments=comments,
            confidence=confidence or node.confidence,
            changes_made=changes_made,
            validation_criteria=validation_criteria or [],
            references=references or []
        )

        # Add validation to node
        node.add_validation(validation)

        # Mark corresponding task as complete if it exists
        for task in self.tasks.values():
            if task.entity_type == "node" and task.entity_id == node_id:
                task.complete(validation)

        return validation

    def approve_node(
        self,
        node_id: str,
        comments: str = "",
        references: Optional[List[str]] = None
    ) -> Validation:
        """
        Approve a node as correct.

        Args:
            node_id: ID of node to approve
            comments: Optional comments
            references: Optional supporting references

        Returns:
            Validation object
        """
        return self.validate_node(
            node_id=node_id,
            status=ValidationStatus.APPROVED,
            comments=comments,
            confidence=1.0,
            references=references
        )

    def reject_node(
        self,
        node_id: str,
        reason: str,
        remove_from_graph: bool = False
    ) -> Validation:
        """
        Reject a node as incorrect.

        Args:
            node_id: ID of node to reject
            reason: Reason for rejection
            remove_from_graph: Whether to remove the node

        Returns:
            Validation object
        """
        validation = self.validate_node(
            node_id=node_id,
            status=ValidationStatus.REJECTED,
            comments=reason,
            confidence=0.0
        )

        if remove_from_graph:
            self.editor.remove_node(node_id, remove_connected_edges=True)

        return validation

    def modify_node(
        self,
        node_id: str,
        modifications: Dict[str, Any],
        comments: str = ""
    ) -> Validation:
        """
        Modify and approve a node.

        Args:
            node_id: ID of node to modify
            modifications: Modifications to apply
            comments: Comments explaining modifications

        Returns:
            Validation object
        """
        return self.validate_node(
            node_id=node_id,
            status=ValidationStatus.MODIFIED,
            comments=comments,
            modifications=modifications,
            confidence=1.0
        )

    # ===== EDGE VALIDATION =====

    def validate_edge(
        self,
        edge_id: str,
        status: ValidationStatus,
        comments: str = "",
        confidence: Optional[float] = None,
        modifications: Optional[Dict[str, Any]] = None,
        validation_criteria: Optional[List[str]] = None,
        references: Optional[List[str]] = None
    ) -> Validation:
        """
        Validate an edge.

        Args:
            edge_id: ID of edge to validate
            status: Validation status
            comments: Validator comments
            confidence: Updated confidence score (optional)
            modifications: Modifications to apply (optional)
            validation_criteria: Criteria used for validation (optional)
            references: Supporting legal references (optional)

        Returns:
            Validation object

        Raises:
            ValueError: If edge doesn't exist
        """
        edge = self.graph.get_edge(edge_id)

        if not edge:
            raise ValueError(f"Edge not found: {edge_id}")

        # Apply modifications if provided
        changes_made = {}

        if modifications:
            if "description" in modifications:
                edge.description = modifications["description"]
                changes_made["description"] = modifications["description"]

            if "relation_type" in modifications:
                from .models import RelationType
                edge.relation_type = RelationType(modifications["relation_type"])
                changes_made["relation_type"] = modifications["relation_type"]

            if "weight" in modifications:
                edge.weight = modifications["weight"]
                changes_made["weight"] = modifications["weight"]

            if "attributes" in modifications:
                edge.attributes.update(modifications["attributes"])
                changes_made["attributes"] = modifications["attributes"]

        # Update confidence if provided
        if confidence is not None:
            edge.confidence = confidence
            changes_made["confidence"] = confidence

        # Create validation record
        validation = Validation(
            validator_id=self.validator_id,
            validation_timestamp=datetime.now(),
            status=status,
            comments=comments,
            confidence=confidence or edge.confidence,
            changes_made=changes_made,
            validation_criteria=validation_criteria or [],
            references=references or []
        )

        # Add validation to edge
        edge.add_validation(validation)

        # Mark corresponding task as complete if it exists
        for task in self.tasks.values():
            if task.entity_type == "edge" and task.entity_id == edge_id:
                task.complete(validation)

        return validation

    def approve_edge(
        self,
        edge_id: str,
        comments: str = "",
        references: Optional[List[str]] = None
    ) -> Validation:
        """
        Approve an edge as correct.

        Args:
            edge_id: ID of edge to approve
            comments: Optional comments
            references: Optional supporting references

        Returns:
            Validation object
        """
        return self.validate_edge(
            edge_id=edge_id,
            status=ValidationStatus.APPROVED,
            comments=comments,
            confidence=1.0,
            references=references
        )

    def reject_edge(
        self,
        edge_id: str,
        reason: str,
        remove_from_graph: bool = False
    ) -> Validation:
        """
        Reject an edge as incorrect.

        Args:
            edge_id: ID of edge to reject
            reason: Reason for rejection
            remove_from_graph: Whether to remove the edge

        Returns:
            Validation object
        """
        validation = self.validate_edge(
            edge_id=edge_id,
            status=ValidationStatus.REJECTED,
            comments=reason,
            confidence=0.0
        )

        if remove_from_graph:
            self.editor.remove_edge(edge_id)

        return validation

    def modify_edge(
        self,
        edge_id: str,
        modifications: Dict[str, Any],
        comments: str = ""
    ) -> Validation:
        """
        Modify and approve an edge.

        Args:
            edge_id: ID of edge to modify
            modifications: Modifications to apply
            comments: Comments explaining modifications

        Returns:
            Validation object
        """
        return self.validate_edge(
            edge_id=edge_id,
            status=ValidationStatus.MODIFIED,
            comments=comments,
            modifications=modifications,
            confidence=1.0
        )

    # ===== BATCH OPERATIONS =====

    def batch_approve(
        self,
        entity_ids: List[str],
        entity_type: str,
        comments: str = ""
    ) -> List[Validation]:
        """
        Approve multiple entities at once.

        Args:
            entity_ids: List of entity IDs to approve
            entity_type: "node" or "edge"
            comments: Comments for all approvals

        Returns:
            List of Validation objects
        """
        validations = []

        for entity_id in entity_ids:
            try:
                if entity_type == "node":
                    validation = self.approve_node(entity_id, comments)
                elif entity_type == "edge":
                    validation = self.approve_edge(entity_id, comments)
                else:
                    continue

                validations.append(validation)

            except ValueError:
                # Entity doesn't exist, skip
                continue

        return validations

    # ===== REPORTING =====

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of validation activities.

        Returns:
            Dictionary with validation statistics
        """
        total_nodes = len(self.graph.nodes)
        total_edges = len(self.graph.edges)

        validated_nodes = sum(1 for n in self.graph.nodes.values() if n.validations)
        validated_edges = sum(1 for e in self.graph.edges.values() if e.validations)

        approved_nodes = sum(1 for n in self.graph.nodes.values() if n.is_validated())
        approved_edges = sum(1 for e in self.graph.edges.values() if e.is_validated())

        pending_tasks = len(self.get_pending_validations())
        completed_tasks = sum(1 for t in self.tasks.values() if t.completed_at is not None)

        return {
            "validator_id": self.validator_id,
            "validator_name": self.validator_name,
            "expertise_areas": self.expertise_areas,
            "nodes": {
                "total": total_nodes,
                "validated": validated_nodes,
                "approved": approved_nodes,
                "validation_rate": validated_nodes / total_nodes if total_nodes > 0 else 0,
            },
            "edges": {
                "total": total_edges,
                "validated": validated_edges,
                "approved": approved_edges,
                "validation_rate": validated_edges / total_edges if total_edges > 0 else 0,
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": pending_tasks,
                "completed": completed_tasks,
            },
        }

    def export_validation_report(self) -> Dict[str, Any]:
        """
        Export a comprehensive validation report.

        Returns:
            Detailed validation report
        """
        summary = self.get_validation_summary()

        # Collect all validations
        all_validations = []

        for node in self.graph.nodes.values():
            for validation in node.validations:
                all_validations.append({
                    "entity_type": "node",
                    "entity_id": node.id,
                    "entity_label": node.label,
                    "validation": validation.to_dict(),
                })

        for edge in self.graph.edges.values():
            for validation in edge.validations:
                all_validations.append({
                    "entity_type": "edge",
                    "entity_id": edge.id,
                    "validation": validation.to_dict(),
                })

        # Sort by timestamp
        all_validations.sort(
            key=lambda v: v["validation"]["validation_timestamp"],
            reverse=True
        )

        return {
            "summary": summary,
            "validations": all_validations,
            "tasks": [t.to_dict() for t in self.tasks.values()],
        }
