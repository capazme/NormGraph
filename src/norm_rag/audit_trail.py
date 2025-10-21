"""
Comprehensive audit trail system for tracking all graph operations.

Provides complete traceability for scientific rigor and legal compliance.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json

from .models import AuditLogEntry


class AuditTrail:
    """
    Complete audit trail for all graph operations.

    Records every modification to the knowledge graph with full context
    for scientific reproducibility and legal traceability.
    """

    def __init__(self):
        """Initialize audit trail."""
        self.entries: List[AuditLogEntry] = []

    def log(
        self,
        operation: str,
        entity_type: str,
        entity_id: str,
        actor_id: str = "system",
        actor_type: str = "system",
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        diff: Optional[Dict[str, Any]] = None,
        operation_context: Optional[Dict[str, Any]] = None,
        comments: str = ""
    ) -> AuditLogEntry:
        """
        Log an operation.

        Args:
            operation: Operation name (e.g., "add_node", "validate", "merge")
            entity_type: Type of entity ("node", "edge", "graph")
            entity_id: ID of the entity
            actor_id: ID of the actor performing the operation
            actor_type: Type of actor ("system", "user", "validator", "script")
            old_value: State before operation
            new_value: State after operation
            diff: Differential changes
            operation_context: Additional context
            comments: Human-readable comments

        Returns:
            Created AuditLogEntry
        """
        entry = AuditLogEntry(
            timestamp=datetime.now(),
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_id=actor_id,
            actor_type=actor_type,
            old_value=old_value,
            new_value=new_value,
            diff=diff,
            operation_context=operation_context or {},
            comments=comments,
        )

        self.entries.append(entry)
        return entry

    def get_entries(
        self,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        operation: Optional[str] = None,
        actor_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """
        Query audit log entries with filters.

        Args:
            entity_id: Filter by entity ID
            entity_type: Filter by entity type
            operation: Filter by operation type
            actor_id: Filter by actor
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            Filtered list of audit log entries
        """
        entries = self.entries

        if entity_id:
            entries = [e for e in entries if e.entity_id == entity_id]

        if entity_type:
            entries = [e for e in entries if e.entity_type == entity_type]

        if operation:
            entries = [e for e in entries if e.operation == operation]

        if actor_id:
            entries = [e for e in entries if e.actor_id == actor_id]

        if start_time:
            entries = [e for e in entries if e.timestamp >= start_time]

        if end_time:
            entries = [e for e in entries if e.timestamp <= end_time]

        return entries

    def get_entity_history(self, entity_id: str) -> List[AuditLogEntry]:
        """
        Get complete history for a specific entity.

        Args:
            entity_id: ID of the entity

        Returns:
            Chronological list of all operations on this entity
        """
        entries = self.get_entries(entity_id=entity_id)
        entries.sort(key=lambda e: e.timestamp)
        return entries

    def get_timeline(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[AuditLogEntry]:
        """
        Get chronological timeline of operations.

        Args:
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            Chronologically sorted list of audit entries
        """
        entries = self.get_entries(start_time=start_time, end_time=end_time)
        entries.sort(key=lambda e: e.timestamp)
        return entries

    def get_operations_by_actor(self, actor_id: str) -> List[AuditLogEntry]:
        """
        Get all operations performed by a specific actor.

        Args:
            actor_id: ID of the actor

        Returns:
            List of operations by this actor
        """
        return self.get_entries(actor_id=actor_id)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get audit trail statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.entries:
            return {
                "total_entries": 0,
                "operations": {},
                "actors": {},
                "entity_types": {},
                "time_range": None,
            }

        # Count by operation type
        operations: Dict[str, int] = {}
        for entry in self.entries:
            operations[entry.operation] = operations.get(entry.operation, 0) + 1

        # Count by actor
        actors: Dict[str, int] = {}
        for entry in self.entries:
            actors[entry.actor_id] = actors.get(entry.actor_id, 0) + 1

        # Count by entity type
        entity_types: Dict[str, int] = {}
        for entry in self.entries:
            entity_types[entry.entity_type] = entity_types.get(entry.entity_type, 0) + 1

        # Time range
        timestamps = [e.timestamp for e in self.entries]
        time_range = {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
        }

        return {
            "total_entries": len(self.entries),
            "operations": operations,
            "actors": actors,
            "entity_types": entity_types,
            "time_range": time_range,
        }

    def export_to_json(self, file_path: Path, pretty: bool = True):
        """
        Export audit trail to JSON file.

        Args:
            file_path: Path to save JSON file
            pretty: Whether to pretty-print JSON
        """
        data = {
            "audit_trail": [entry.to_dict() for entry in self.entries],
            "statistics": self.get_statistics(),
            "exported_at": datetime.now().isoformat(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)

    def import_from_json(self, file_path: Path):
        """
        Import audit trail from JSON file.

        Args:
            file_path: Path to JSON file
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for entry_data in data.get("audit_trail", []):
            entry = AuditLogEntry(
                id=entry_data["id"],
                timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                operation=entry_data["operation"],
                entity_type=entry_data["entity_type"],
                entity_id=entry_data["entity_id"],
                actor_id=entry_data["actor_id"],
                actor_type=entry_data["actor_type"],
                old_value=entry_data.get("old_value"),
                new_value=entry_data.get("new_value"),
                diff=entry_data.get("diff"),
                operation_context=entry_data.get("operation_context", {}),
                comments=entry_data.get("comments", ""),
            )
            self.entries.append(entry)

    def generate_report(
        self,
        format: str = "markdown",
        include_details: bool = False
    ) -> str:
        """
        Generate a human-readable audit report.

        Args:
            format: Output format ("markdown", "text")
            include_details: Whether to include detailed entry information

        Returns:
            Formatted report string
        """
        stats = self.get_statistics()

        if format == "markdown":
            return self._generate_markdown_report(stats, include_details)
        elif format == "text":
            return self._generate_text_report(stats, include_details)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_markdown_report(
        self,
        stats: Dict[str, Any],
        include_details: bool
    ) -> str:
        """Generate markdown report."""
        lines = [
            "# Audit Trail Report",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "## Summary",
            "",
            f"- **Total Entries:** {stats['total_entries']}",
        ]

        if stats["time_range"]:
            lines.extend([
                f"- **Time Range:** {stats['time_range']['start']} to {stats['time_range']['end']}",
                "",
            ])

        # Operations
        lines.extend([
            "## Operations",
            "",
            "| Operation | Count |",
            "|-----------|-------|",
        ])

        for operation, count in sorted(stats["operations"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {operation} | {count} |")

        lines.append("")

        # Actors
        lines.extend([
            "## Actors",
            "",
            "| Actor | Operations |",
            "|-------|------------|",
        ])

        for actor, count in sorted(stats["actors"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {actor} | {count} |")

        lines.append("")

        # Entity types
        lines.extend([
            "## Entity Types",
            "",
            "| Type | Operations |",
            "|------|------------|",
        ])

        for entity_type, count in sorted(stats["entity_types"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {entity_type} | {count} |")

        lines.append("")

        # Detailed entries
        if include_details:
            lines.extend([
                "## Detailed Entries",
                "",
            ])

            for entry in sorted(self.entries, key=lambda e: e.timestamp, reverse=True):
                lines.extend([
                    f"### {entry.operation} ({entry.timestamp.isoformat()})",
                    "",
                    f"- **Entity:** {entry.entity_type} / {entry.entity_id}",
                    f"- **Actor:** {entry.actor_id} ({entry.actor_type})",
                    f"- **Comments:** {entry.comments}",
                    "",
                ])

        return "\n".join(lines)

    def _generate_text_report(
        self,
        stats: Dict[str, Any],
        include_details: bool
    ) -> str:
        """Generate plain text report."""
        lines = [
            "=" * 60,
            "AUDIT TRAIL REPORT",
            "=" * 60,
            "",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "-" * 60,
            "SUMMARY",
            "-" * 60,
            "",
            f"Total Entries: {stats['total_entries']}",
        ]

        if stats["time_range"]:
            lines.extend([
                f"Time Range: {stats['time_range']['start']} to {stats['time_range']['end']}",
                "",
            ])

        # Operations
        lines.extend([
            "-" * 60,
            "OPERATIONS",
            "-" * 60,
            "",
        ])

        for operation, count in sorted(stats["operations"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {operation:.<40} {count:>5}")

        lines.append("")

        # Actors
        lines.extend([
            "-" * 60,
            "ACTORS",
            "-" * 60,
            "",
        ])

        for actor, count in sorted(stats["actors"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {actor:.<40} {count:>5}")

        lines.append("")

        # Entity types
        lines.extend([
            "-" * 60,
            "ENTITY TYPES",
            "-" * 60,
            "",
        ])

        for entity_type, count in sorted(stats["entity_types"].items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {entity_type:.<40} {count:>5}")

        lines.append("")

        # Detailed entries
        if include_details:
            lines.extend([
                "-" * 60,
                "DETAILED ENTRIES",
                "-" * 60,
                "",
            ])

            for entry in sorted(self.entries, key=lambda e: e.timestamp, reverse=True):
                lines.extend([
                    f"[{entry.timestamp.isoformat()}] {entry.operation}",
                    f"  Entity: {entry.entity_type} / {entry.entity_id}",
                    f"  Actor: {entry.actor_id} ({entry.actor_type})",
                    f"  Comments: {entry.comments}",
                    "",
                ])

        lines.append("=" * 60)

        return "\n".join(lines)

    def clear(self):
        """Clear all audit log entries."""
        self.entries.clear()

    def __len__(self) -> int:
        """Get number of audit entries."""
        return len(self.entries)

    def __repr__(self) -> str:
        """String representation."""
        return f"AuditTrail(entries={len(self.entries)})"
