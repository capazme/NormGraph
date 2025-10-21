"""
Complete workflow example for NormRAG 2.0

This example demonstrates:
1. Reading legal texts from multiple sources
2. Extracting entities and relationships
3. Building a knowledge graph with multiple strategies
4. Manually editing the graph
5. Versioning and comparing different graph versions
6. Expert validation workflow
7. Audit trail and reporting
"""

from pathlib import Path
from norm_rag import (
    # Core classes
    TextReader,
    InformationExtractor,
    GraphBuilder,
    GraphEditor,
    GraphVersionManager,
    DomainValidator,
    AuditTrail,

    # Models
    EntityType,
    RelationType,
    ValidationStatus,
)


def main():
    """Complete workflow example."""

    print("=" * 80)
    print("NORMRAG 2.0 - COMPLETE WORKFLOW EXAMPLE")
    print("=" * 80)
    print()

    # =========================================================================
    # PHASE 1: TEXT READING WITH PROVENANCE
    # =========================================================================

    print("PHASE 1: Reading legal texts...")
    print("-" * 80)

    reader = TextReader()

    # Read from a text file
    text_file = Path("../src/data/penale/1.txt")

    if text_file.exists():
        segments = reader.read_file(text_file, segment_by="paragraph")
        print(f"✓ Read {len(segments)} segments from {text_file.name}")

        # Show first segment with provenance
        if segments:
            first_seg = segments[0]
            print(f"\nFirst segment preview:")
            print(f"  Text: {first_seg.text[:100]}...")
            print(f"  Source: {first_seg.provenance.source_file}")
            print(f"  Lines: {first_seg.provenance.line_start}-{first_seg.provenance.line_end}")
    else:
        # Create sample text
        sample_text = """
        Art. 1 - Reati e pene: disposizioni generali
        Nessuno può essere punito per un fatto che non sia espressamente preveduto
        come reato dalla legge, né con pene che non siano da essa stabilite.

        Art. 2 - Successione di leggi penali
        Nessuno può essere punito per un fatto che, secondo una legge posteriore,
        non costituisce reato; e, se vi è stata condanna, ne cessano l'esecuzione
        e gli effetti penali.
        """

        segments = reader.read_string(
            sample_text,
            source_name="sample_codice_penale",
            segment_by="paragraph"
        )
        print(f"✓ Created {len(segments)} segments from sample text")

    print()

    # =========================================================================
    # PHASE 2: INFORMATION EXTRACTION
    # =========================================================================

    print("PHASE 2: Extracting entities and relationships...")
    print("-" * 80)

    extractor = InformationExtractor()
    extraction_result = extractor.extract_from_segments(segments, actor_id="system")

    print(f"✓ Extracted {extraction_result.extraction_stats['nodes_extracted']} nodes")
    print(f"✓ Extracted {extraction_result.extraction_stats['edges_extracted']} edges")
    print(f"✓ Average confidence: {extraction_result.extraction_stats['average_confidence']:.2f}")

    # Show extracted nodes
    if extraction_result.nodes:
        print(f"\nSample extracted nodes:")
        for node in extraction_result.nodes[:3]:
            print(f"  - {node.label} ({node.entity_type.value})")
            print(f"    Confidence: {node.confidence:.2f}")
            if node.provenance and node.provenance.source_file:
                print(f"    Source: {node.provenance.source_file}")

    print()

    # =========================================================================
    # PHASE 3: GRAPH BUILDING WITH DIFFERENT STRATEGIES
    # =========================================================================

    print("PHASE 3: Building knowledge graphs with different strategies...")
    print("-" * 80)

    # Strategy 1: Entity-Centric
    builder_entity = GraphBuilder(strategy="entity_centric")
    graph_entity = builder_entity.build_graph(
        extraction_result,
        graph_name="Codice Penale - Entity Centric",
        graph_description="Grafo centrato su entità giuridiche"
    )
    print(f"✓ Entity-centric graph: {len(graph_entity.nodes)} nodes, {len(graph_entity.edges)} edges")

    # Strategy 2: Hierarchical
    builder_hierarchical = GraphBuilder(strategy="hierarchical")
    graph_hierarchical = builder_hierarchical.build_graph(
        extraction_result,
        graph_name="Codice Penale - Hierarchical",
        graph_description="Grafo gerarchico (codice → articoli → concetti)"
    )
    print(f"✓ Hierarchical graph: {len(graph_hierarchical.nodes)} nodes, {len(graph_hierarchical.edges)} edges")

    # Strategy 3: Hybrid (recommended)
    builder_hybrid = GraphBuilder(strategy="hybrid")
    graph = builder_hybrid.build_graph(
        extraction_result,
        graph_name="Codice Penale - Hybrid",
        graph_description="Grafo ibrido con entità, gerarchie, e clustering semantico"
    )
    print(f"✓ Hybrid graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    print()

    # =========================================================================
    # PHASE 4: MANUAL GRAPH EDITING
    # =========================================================================

    print("PHASE 4: Manual graph editing and enrichment...")
    print("-" * 80)

    editor = GraphEditor(graph, actor_id="legal_expert_01")

    # Add a custom node
    custom_node = editor.add_node(
        label="Principio di Legalità",
        entity_type=EntityType.CONCETTO_GIURIDICO,
        description="Principio fondamentale del diritto penale: nullum crimen sine lege",
        attributes={
            "importanza": "fondamentale",
            "ambito": "diritto penale costituzionale"
        },
        tags={"principio", "costituzionale"}
    )
    print(f"✓ Added custom node: {custom_node.label}")

    # Find article nodes and connect to principle
    article_nodes = graph.get_nodes_by_type(EntityType.NORMA)
    if article_nodes:
        art1 = article_nodes[0]

        # Add edge connecting article to principle
        edge = editor.add_edge(
            source_id=art1.id,
            target_id=custom_node.id,
            relation_type=RelationType.APPLICA,
            description=f"{art1.label} applica il principio di legalità",
            confidence=1.0
        )
        print(f"✓ Added edge: {art1.label} → {custom_node.label}")

    # Batch transformation: add tag to all NORMA nodes
    count = editor.batch_transform(
        filter_func=lambda n: n.entity_type == EntityType.NORMA,
        transform_func=lambda n: n.tags.add("codice_penale"),
        entity_type="node"
    )
    print(f"✓ Batch tagged {count} article nodes")

    print()

    # =========================================================================
    # PHASE 5: VERSIONING AND COMPARISON
    # =========================================================================

    print("PHASE 5: Graph versioning and comparison...")
    print("-" * 80)

    # Create version manager
    version_manager = GraphVersionManager(graph)
    print(f"✓ Created version manager with initial snapshot: {version_manager.current_version}")

    # Make some modifications
    if len(graph.nodes) > 0:
        first_node = list(graph.nodes.values())[0]
        editor.modify_node(
            first_node.id,
            description=first_node.description + " [MODIFICATO PER TEST]"
        )

    # Create a new version
    version_manager.create_snapshot(
        graph,
        version_id="v1.1",
        description="Dopo modifiche manuali dell'esperto"
    )
    print(f"✓ Created snapshot v1.1")

    # Compare versions
    diff = version_manager.compare_versions("v1.0", "v1.1")
    print(f"\nVersion comparison (v1.0 → v1.1):")
    print(diff.get_summary())

    # Create a branch for experimental changes
    experimental = version_manager.branch(
        from_version="v1.1",
        new_version_id="v1.1-experimental",
        description="Branch sperimentale per test strutture alternative"
    )
    print(f"✓ Created experimental branch")

    print()

    # =========================================================================
    # PHASE 6: EXPERT VALIDATION
    # =========================================================================

    print("PHASE 6: Domain expert validation workflow...")
    print("-" * 80)

    # Create validator
    validator = DomainValidator(
        graph,
        validator_id="prof_rossi",
        validator_name="Prof. Mario Rossi",
        expertise_areas=["diritto penale", "diritto costituzionale"]
    )

    # Create validation tasks for low-confidence entities
    tasks = validator.create_validation_tasks(confidence_threshold=0.9)
    print(f"✓ Created {len(tasks)} validation tasks")

    # Simulate validation workflow
    pending = validator.get_pending_validations()

    if pending:
        # Approve first task
        first_task = pending[0]

        if first_task.entity_type == "node":
            validation = validator.approve_node(
                first_task.entity_id,
                comments="Entità verificata e confermata corretta",
                references=["Art. 1 CP", "Costituzione Art. 25"]
            )
            print(f"✓ Approved node: {first_task.entity_id}")

        # Modify second task (if exists)
        if len(pending) > 1:
            second_task = pending[1]

            if second_task.entity_type == "node":
                validation = validator.modify_node(
                    second_task.entity_id,
                    modifications={
                        "description": "Descrizione corretta dall'esperto",
                        "attributes": {"validato_da": "prof_rossi"}
                    },
                    comments="Corretta descrizione per maggiore precisione giuridica"
                )
                print(f"✓ Modified and approved node: {second_task.entity_id}")

    # Get validation summary
    summary = validator.get_validation_summary()
    print(f"\nValidation Summary:")
    print(f"  Validator: {summary['validator_name']}")
    print(f"  Nodes validated: {summary['nodes']['validated']}/{summary['nodes']['total']}")
    print(f"  Edges validated: {summary['edges']['validated']}/{summary['edges']['total']}")
    print(f"  Tasks completed: {summary['tasks']['completed']}/{summary['tasks']['total']}")

    print()

    # =========================================================================
    # PHASE 7: AUDIT TRAIL AND REPORTING
    # =========================================================================

    print("PHASE 7: Audit trail and reporting...")
    print("-" * 80)

    # Get audit log from editor
    audit_log = editor.export_audit_log()
    print(f"✓ Exported {len(audit_log)} audit entries from editor")

    # Create comprehensive audit trail
    audit_trail = AuditTrail()

    # Import entries from editor
    for entry_data in audit_log:
        from datetime import datetime
        audit_trail.log(
            operation=entry_data["operation"],
            entity_type=entry_data["entity_type"],
            entity_id=entry_data["entity_id"],
            actor_id=entry_data["actor_id"],
            actor_type=entry_data["actor_type"],
            old_value=entry_data.get("old_value"),
            new_value=entry_data.get("new_value"),
            comments=entry_data.get("comments", "")
        )

    # Get statistics
    stats = audit_trail.get_statistics()
    print(f"\nAudit Trail Statistics:")
    print(f"  Total operations: {stats['total_entries']}")
    print(f"  Operations by type:")
    for operation, count in sorted(stats['operations'].items(), key=lambda x: x[1], reverse=True):
        print(f"    - {operation}: {count}")

    # Generate report
    report = audit_trail.generate_report(format="text", include_details=False)
    print(f"\n{report}")

    # Save audit trail to file
    audit_file = Path("audit_trail.json")
    audit_trail.export_to_json(audit_file)
    print(f"\n✓ Saved audit trail to {audit_file}")

    # =========================================================================
    # PHASE 8: EXPORT RESULTS
    # =========================================================================

    print("\nPHASE 8: Exporting results...")
    print("-" * 80)

    # Calculate final statistics
    graph.calculate_statistics()

    print(f"\nFinal Graph Statistics:")
    print(f"  Name: {graph.metadata.name}")
    print(f"  Strategy: {graph.metadata.construction_strategy}")
    print(f"  Nodes: {graph.metadata.node_count}")
    print(f"  Edges: {graph.metadata.edge_count}")
    print(f"  Validated nodes: {graph.metadata.validated_node_count}")
    print(f"  Validated edges: {graph.metadata.validated_edge_count}")
    print(f"  Average confidence: {graph.metadata.average_confidence:.2f}")
    print(f"  Completeness score: {graph.metadata.completeness_score:.2%}")

    # Export graph to NetworkX format
    nx_graph = graph.to_networkx()
    print(f"\n✓ Converted to NetworkX DiGraph")

    # Save version to file
    version_file = Path("graph_version_v1.1.json")
    version_manager.save_version_to_file("v1.1", version_file)
    print(f"✓ Saved graph version to {version_file}")

    # Export validation report
    validation_report = validator.export_validation_report()
    print(f"✓ Generated validation report with {len(validation_report['validations'])} validations")

    print()
    print("=" * 80)
    print("WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print()
    print("Key Features Demonstrated:")
    print("✓ Multi-format text reading with full provenance tracking")
    print("✓ Automatic information extraction with confidence scores")
    print("✓ Multiple graph building strategies (entity, hierarchical, hybrid)")
    print("✓ Manual graph editing (add, modify, merge, batch operations)")
    print("✓ Version control (snapshots, diff, branches, merge)")
    print("✓ Expert validation workflow with task management")
    print("✓ Complete audit trail for scientific rigor")
    print("✓ Comprehensive reporting and export capabilities")
    print()


if __name__ == "__main__":
    main()
