```markdown
# NormRAG 2.0 - Legal Knowledge Graph System

Sistema completo per la lettura, estrazione e costruzione di grafi di conoscenza giuridica con **tracciabilità completa** e **rigore scientifico-giuridico**.

## 📋 Indice

- [Caratteristiche Principali](#caratteristiche-principali)
- [Architettura](#architettura)
- [Installazione](#installazione)
- [Guida Rapida](#guida-rapida)
- [Componenti Dettagliati](#componenti-dettagliati)
- [Workflow Completo](#workflow-completo)
- [Esempi Avanzati](#esempi-avanzati)

---

## 🎯 Caratteristiche Principali

### ✅ Tracciabilità Completa (Provenance)
- Ogni informazione estratta è tracciabile alla sua fonte originale
- Riferimenti precisi a file, pagina, riga, carattere
- Metadati di estrazione (metodo, timestamp, versione)
- Contesto prima/dopo per verificabilità

### ✅ Rigore Scientifico-Giuridico
- Validazione da esperti di dominio
- Versionamento completo dei grafi
- Audit trail di tutte le operazioni
- Confidence scores su ogni estrazione
- Sistema di annotazioni e riferimenti normativi

### ✅ Flessibilità nella Costruzione dei Grafi
- **5 strategie diverse** di costruzione:
  - Entity-Centric: focus su entità giuridiche
  - Hierarchical: struttura gerarchica (codice → articoli → concetti)
  - Temporal: ordinamento cronologico
  - Semantic Clustering: clustering semantico
  - Hybrid: combinazione di tutte le strategie

### ✅ Manipolazione Manuale Completa
- CRUD operations su nodi e archi
- Merge e split di nodi
- Trasformazioni batch
- Pieno controllo editoriale

### ✅ Versioning Avanzato
- Snapshot di versioni
- Diff tra versioni
- Branching per sviluppi paralleli
- Merge con risoluzione conflitti
- Rollback a versioni precedenti

---

## 🏗️ Architettura

```
┌──────────────────────────────────────────────────────────────┐
│                      NORMRAG 2.0                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐         ┌─────────────────┐             │
│  │  TEXT READER   │────────>│   EXTRACTOR     │             │
│  │  Multi-format  │         │  Entities/      │             │
│  │  + Provenance  │         │  Relations      │             │
│  └────────────────┘         └─────────────────┘             │
│          │                          │                        │
│          v                          v                        │
│  ┌────────────────────────────────────────┐                 │
│  │        GRAPH BUILDER                   │                 │
│  │  • Entity-Centric Strategy             │                 │
│  │  • Hierarchical Strategy               │                 │
│  │  • Temporal Strategy                   │                 │
│  │  • Semantic Clustering Strategy        │                 │
│  │  • Hybrid Strategy                     │                 │
│  └────────────────────────────────────────┘                 │
│                   │                                          │
│                   v                                          │
│  ┌────────────────────────────────────────┐                 │
│  │     LEGAL KNOWLEDGE GRAPH              │                 │
│  │  Nodes + Edges + Metadata              │                 │
│  └────────────────────────────────────────┘                 │
│         │              │              │                      │
│         v              v              v                      │
│  ┌──────────┐  ┌─────────────┐  ┌──────────┐               │
│  │  EDITOR  │  │  VERSIONING │  │VALIDATOR │               │
│  │  Manual  │  │  Snapshots  │  │  Expert  │               │
│  │  CRUD    │  │  Diff/Merge │  │  Review  │               │
│  └──────────┘  └─────────────┘  └──────────┘               │
│         │              │              │                      │
│         └──────────────┴──────────────┘                      │
│                       │                                      │
│                       v                                      │
│              ┌─────────────────┐                            │
│              │  AUDIT TRAIL    │                            │
│              │  Full Tracking  │                            │
│              └─────────────────┘                            │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Installazione

```bash
# Requisiti base
pip install networkx pandas numpy

# Per lettura PDF
pip install PyPDF2

# Per lettura Word
pip install python-docx

# Per visualizzazione (opzionale)
pip install pyvis matplotlib
```

---

## 🚀 Guida Rapida

### Esempio Minimo

```python
from norm_rag import (
    TextReader,
    InformationExtractor,
    GraphBuilder,
)

# 1. Leggi testo
reader = TextReader()
segments = reader.read_file("codice_penale.txt", segment_by="paragraph")

# 2. Estrai informazioni
extractor = InformationExtractor()
result = extractor.extract_from_segments(segments)

# 3. Costruisci grafo
builder = GraphBuilder(strategy="hybrid")
graph = builder.build_graph(
    result,
    graph_name="Codice Penale",
    graph_description="Grafo del codice penale italiano"
)

print(f"Creato grafo con {len(graph.nodes)} nodi e {len(graph.edges)} archi")
```

### Esempio con Validazione Esperto

```python
from norm_rag import DomainValidator, ValidationStatus

# Crea validatore
validator = DomainValidator(
    graph,
    validator_id="prof_rossi",
    validator_name="Prof. Mario Rossi",
    expertise_areas=["diritto penale"]
)

# Crea task di validazione per entità a bassa confidenza
tasks = validator.create_validation_tasks(confidence_threshold=0.8)

# Valida un nodo
validator.approve_node(
    node_id="node_123",
    comments="Entità verificata e corretta",
    references=["Art. 1 CP", "Sent. Cass. 12345/2020"]
)

# Report validazioni
summary = validator.get_validation_summary()
print(f"Validati {summary['nodes']['validated']} nodi su {summary['nodes']['total']}")
```

---

## 📚 Componenti Dettagliati

### 1. TextReader - Lettura Multi-Formato

Legge testi da diverse fonti mantenendo la tracciabilità:

```python
from norm_rag import TextReader

reader = TextReader()

# Da file di testo
segments = reader.read_file("documento.txt", segment_by="paragraph")

# Da PDF
segments = reader.read_file("documento.pdf", segment_by="paragraph")

# Da Word
segments = reader.read_file("documento.docx")

# Da JSON
segments = reader.read_file("dati.json")

# Da stringa
segments = reader.read_string(
    "Art. 1 - Principio di legalità...",
    source_name="sample",
    segment_by="sentence"
)

# Da risposta API
segments = reader.read_api_response(
    response_data={"articles": [{"text": "..."}]},
    source_url="https://api.example.com/articles"
)

# Ogni segmento ha provenance completa
seg = segments[0]
print(seg.text)
print(f"Fonte: {seg.provenance.source_file}")
print(f"Righe: {seg.provenance.line_start}-{seg.provenance.line_end}")
print(f"Estratto con: {seg.provenance.extraction_method.value}")
```

### 2. InformationExtractor - Estrazione Tracciabile

Estrae entità e relazioni con confidence scores:

```python
from norm_rag import InformationExtractor, EntityType, RelationType

extractor = InformationExtractor()

# Estrazione automatica
result = extractor.extract_from_segments(segments, actor_id="system")

print(f"Nodi estratti: {result.extraction_stats['nodes_extracted']}")
print(f"Archi estratti: {result.extraction_stats['edges_extracted']}")
print(f"Confidenza media: {result.extraction_stats['average_confidence']:.2f}")

# Creazione manuale di nodi
node = extractor.create_manual_node(
    label="Principio di Legalità",
    entity_type=EntityType.CONCETTO_GIURIDICO,
    description="Nullum crimen sine lege",
    article_number=None,
    law_reference="Costituzione Art. 25",
    confidence=1.0
)

# Creazione manuale di archi
edge = extractor.create_manual_edge(
    source_node=node1,
    target_node=node2,
    relation_type=RelationType.APPLICA,
    description="Art. 1 applica il principio di legalità",
    confidence=1.0
)
```

### 3. GraphBuilder - Strategie Multiple

Costruzione del grafo con diverse strategie:

```python
from norm_rag import GraphBuilder

# Strategia 1: Entity-Centric
builder = GraphBuilder(strategy="entity_centric")
graph1 = builder.build_graph(result, graph_name="Grafo Entity-Centric")

# Strategia 2: Hierarchical (consigliata per codici)
builder = GraphBuilder(strategy="hierarchical")
graph2 = builder.build_graph(result, graph_name="Grafo Gerarchico")

# Strategia 3: Temporal (per evoluzione normativa)
builder = GraphBuilder(strategy="temporal")
graph3 = builder.build_graph(result, graph_name="Grafo Temporale")

# Strategia 4: Semantic Clustering
builder = GraphBuilder(strategy="semantic_clustering")
graph4 = builder.build_graph(result, graph_name="Grafo con Clustering")

# Strategia 5: Hybrid (RACCOMANDATO - combina tutte)
builder = GraphBuilder(strategy="hybrid")
graph = builder.build_graph(result, graph_name="Grafo Ibrido Completo")

# Visualizza strategie disponibili
print(builder.get_available_strategies())
```

### 4. GraphEditor - Manipolazione Manuale

CRUD completo su nodi e archi:

```python
from norm_rag import GraphEditor, EntityType, RelationType

editor = GraphEditor(graph, actor_id="expert_01")

# ===== OPERAZIONI SU NODI =====

# Aggiungi nodo
node = editor.add_node(
    label="Dolo Eventuale",
    entity_type=EntityType.CONCETTO_GIURIDICO,
    description="Forma di dolo in cui l'agente accetta il rischio...",
    confidence=1.0,
    tags={"dolo", "elemento_soggettivo"}
)

# Modifica nodo
editor.modify_node(
    node_id=node.id,
    description="Descrizione aggiornata",
    attributes={"importanza": "alta"},
    confidence=0.95
)

# Rimuovi nodo
editor.remove_node(node_id, remove_connected_edges=True)

# Merge di nodi (unisci nodi duplicati)
merged = editor.merge_nodes(
    node_ids=["node1", "node2", "node3"],
    merged_label="Nodo Unificato",
    keep_all_attributes=True
)

# Split di nodo (dividi concetto complesso)
new_nodes = editor.split_node(
    node_id="complex_node",
    split_configs=[
        {"label": "Parte A", "description": "..."},
        {"label": "Parte B", "description": "..."},
    ]
)

# ===== OPERAZIONI SU ARCHI =====

# Aggiungi arco
edge = editor.add_edge(
    source_id=node1.id,
    target_id=node2.id,
    relation_type=RelationType.MODIFICA,
    description="Art. 5 modifica Art. 3",
    weight=1.0,
    confidence=1.0
)

# Modifica arco
editor.modify_edge(
    edge_id=edge.id,
    relation_type=RelationType.INTEGRA,
    weight=0.8
)

# Rimuovi arco
editor.remove_edge(edge_id)

# ===== TRASFORMAZIONI BATCH =====

# Aggiungi tag a tutti i nodi NORMA
count = editor.batch_transform(
    filter_func=lambda n: n.entity_type == EntityType.NORMA,
    transform_func=lambda n: n.tags.add("codice_penale"),
    entity_type="node"
)

# ===== AUDIT LOG =====
audit_log = editor.get_audit_log()
print(f"Operazioni registrate: {len(audit_log)}")
```

### 5. GraphVersionManager - Versioning

Gestione completa delle versioni:

```python
from norm_rag import GraphVersionManager

# Crea version manager
vm = GraphVersionManager(graph)

# Crea snapshot
vm.create_snapshot(
    graph,
    version_id="v1.0",
    description="Versione iniziale dopo estrazione automatica"
)

# Dopo modifiche, crea nuova versione
vm.create_snapshot(
    graph,
    version_id="v1.1",
    description="Dopo validazione esperto"
)

# Confronta versioni
diff = vm.compare_versions("v1.0", "v1.1")
print(diff.get_summary())
# Output: Diff: v1.0 → v1.1
#         Nodes: +5 -2 ~8
#         Edges: +10 -3 ~15

# Crea branch per esperimenti
vm.branch(
    from_version="v1.1",
    new_version_id="v1.1-experimental",
    description="Test struttura alternativa"
)

# Merge di branch
merged_graph, conflicts = vm.merge(
    version_a="v1.1",
    version_b="v1.1-experimental",
    merged_version_id="v1.2",
    conflict_resolution="take_b"  # o "take_a", "manual"
)

# Rollback a versione precedente
restored_graph = vm.rollback("v1.0")

# Salva versione su file
vm.save_version_to_file("v1.1", Path("graph_v1.1.json"))

# Carica versione da file
snapshot = vm.load_version_from_file(Path("graph_v1.1.json"))

# Storia delle versioni
history = vm.get_version_history("v1.2")
print(f"Storia: {' → '.join(history)}")
```

### 6. DomainValidator - Validazione Esperto

Workflow di validazione per esperti di dominio:

```python
from norm_rag import DomainValidator, ValidationStatus

# Crea validatore
validator = DomainValidator(
    graph,
    validator_id="prof_rossi",
    validator_name="Prof. Mario Rossi",
    expertise_areas=["diritto penale", "procedura penale"]
)

# Crea task automaticamente per entità a bassa confidenza
tasks = validator.create_validation_tasks(
    confidence_threshold=0.8,  # < 0.8 richiede validazione
    filter_entity_type="node"   # solo nodi
)

# Ottieni task pendenti
pending = validator.get_pending_validations(priority="high")

# ===== VALIDAZIONE NODI =====

# Approva nodo
validator.approve_node(
    node_id="node_123",
    comments="Entità corretta",
    references=["Art. 1 CP", "Costituzione Art. 25"]
)

# Rifiuta nodo
validator.reject_node(
    node_id="node_456",
    reason="Entità non pertinente al contesto",
    remove_from_graph=True
)

# Modifica e approva
validator.modify_node(
    node_id="node_789",
    modifications={
        "label": "Responsabilità Penale",
        "description": "Descrizione corretta dall'esperto",
        "attributes": {"validato_da": "prof_rossi"}
    },
    comments="Correzione terminologia giuridica"
)

# ===== VALIDAZIONE ARCHI =====

validator.approve_edge(edge_id="edge_123")
validator.reject_edge(edge_id="edge_456", remove_from_graph=True)
validator.modify_edge(
    edge_id="edge_789",
    modifications={"weight": 0.9, "relation_type": "INTEGRA"}
)

# ===== BATCH OPERATIONS =====

# Approva multipli nodi
validator.batch_approve(
    entity_ids=["node1", "node2", "node3"],
    entity_type="node",
    comments="Batch validation OK"
)

# ===== REPORTING =====

# Summary
summary = validator.get_validation_summary()
print(f"""
Validatore: {summary['validator_name']}
Nodi validati: {summary['nodes']['validated']}/{summary['nodes']['total']}
Archi validati: {summary['edges']['validated']}/{summary['edges']['total']}
Task completati: {summary['tasks']['completed']}/{summary['tasks']['total']}
""")

# Report completo
report = validator.export_validation_report()
# Contiene: summary, validations, tasks
```

### 7. AuditTrail - Tracciabilità Completa

Sistema di audit trail per ogni operazione:

```python
from norm_rag import AuditTrail

audit = AuditTrail()

# Log manuale di operazione
audit.log(
    operation="custom_operation",
    entity_type="node",
    entity_id="node_123",
    actor_id="user_01",
    actor_type="user",
    comments="Operazione personalizzata"
)

# Query audit log
entries = audit.get_entries(
    entity_id="node_123",
    operation="modify_node",
    actor_id="expert_01"
)

# Storia completa di un'entità
history = audit.get_entity_history("node_123")
for entry in history:
    print(f"{entry.timestamp}: {entry.operation} by {entry.actor_id}")

# Timeline
timeline = audit.get_timeline(
    start_time=datetime(2025, 1, 1),
    end_time=datetime(2025, 12, 31)
)

# Operazioni per attore
user_ops = audit.get_operations_by_actor("expert_01")

# Statistiche
stats = audit.get_statistics()
print(f"""
Totale operazioni: {stats['total_entries']}
Operazioni per tipo: {stats['operations']}
Attori: {stats['actors']}
""")

# Report
report = audit.generate_report(format="markdown", include_details=True)
print(report)

# Export/Import
audit.export_to_json(Path("audit_trail.json"), pretty=True)
audit.import_from_json(Path("audit_trail.json"))
```

---

## 🔄 Workflow Completo

### Scenario: Creazione Grafo del Codice Penale con Validazione

```python
from pathlib import Path
from norm_rag import *

# 1. LETTURA TESTI
reader = TextReader()
segments = []

# Leggi tutti gli articoli
for file in Path("data/codice_penale").glob("*.txt"):
    segs = reader.read_file(file, segment_by="paragraph")
    segments.extend(segs)

print(f"Letti {len(segments)} segmenti da {len(list(Path('data/codice_penale').glob('*.txt')))} file")

# 2. ESTRAZIONE
extractor = InformationExtractor()
result = extractor.extract_from_segments(segments, actor_id="system")

# 3. COSTRUZIONE GRAFO (strategia ibrida)
builder = GraphBuilder(strategy="hybrid")
graph = builder.build_graph(
    result,
    graph_name="Codice Penale Italiano",
    graph_description="Grafo completo del codice penale con struttura ibrida"
)

# 4. VERSIONING
vm = GraphVersionManager(graph)
vm.create_snapshot(graph, "v1.0", "Estrazione automatica iniziale")

# 5. EDITING MANUALE
editor = GraphEditor(graph, actor_id="legal_expert")

# Aggiungi nodi per principi fondamentali
principio_legalita = editor.add_node(
    label="Principio di Legalità",
    entity_type=EntityType.CONCETTO_GIURIDICO,
    description="Nullum crimen, nulla poena sine lege",
    tags={"principio", "fondamentale"}
)

# Collega articoli al principio
articoli = graph.get_nodes_by_type(EntityType.NORMA)
for art in articoli[:10]:  # primi 10 articoli
    if "legalità" in art.description.lower():
        editor.add_edge(
            source_id=art.id,
            target_id=principio_legalita.id,
            relation_type=RelationType.APPLICA,
            description=f"{art.label} applica il principio di legalità"
        )

# 6. SNAPSHOT DOPO EDITING
vm.create_snapshot(graph, "v1.1", "Dopo arricchimento manuale")

# 7. VALIDAZIONE ESPERTO
validator = DomainValidator(
    graph,
    validator_id="prof_bianchi",
    validator_name="Prof.ssa Laura Bianchi",
    expertise_areas=["diritto penale sostanziale"]
)

# Crea task di validazione
tasks = validator.create_validation_tasks(confidence_threshold=0.85)
print(f"Creati {len(tasks)} task di validazione")

# Valida primi 10 task
for task in tasks[:10]:
    if task.entity_type == "node":
        node = graph.get_node(task.entity_id)
        if node and node.confidence > 0.7:
            validator.approve_node(
                task.entity_id,
                comments=f"Nodo verificato: {node.label}",
                references=["Codice Penale"]
            )

# 8. SNAPSHOT POST-VALIDAZIONE
vm.create_snapshot(graph, "v1.2", "Dopo prima validazione esperto")

# 9. AUDIT E REPORTING
audit = AuditTrail()

# Importa log da editor
for entry in editor.export_audit_log():
    audit.log(**entry)

# Report
stats = audit.get_statistics()
validation_report = validator.export_validation_report()

print(f"""
========================================
REPORT FINALE
========================================
Grafo: {graph.metadata.name}
Versione: {vm.current_version}
Nodi: {graph.metadata.node_count}
Archi: {graph.metadata.edge_count}
Validati: {graph.metadata.validated_node_count} nodi, {graph.metadata.validated_edge_count} archi
Confidenza media: {graph.metadata.average_confidence:.2%}
Completezza: {graph.metadata.completeness_score:.2%}

Operazioni audit: {stats['total_entries']}
Validazioni: {len(validation_report['validations'])}
========================================
""")

# 10. EXPORT
# Salva versione finale
vm.save_version_to_file("v1.2", Path("codice_penale_v1.2.json"))

# Salva audit trail
audit.export_to_json(Path("audit_trail.json"))

# Converti a NetworkX per analisi/visualizzazione
nx_graph = graph.to_networkx()

# Salva come GraphML
import networkx as nx
nx.write_graphml(nx_graph, "codice_penale.graphml")
```

---

## 🎓 Esempi Avanzati

### Esempio 1: Confronto tra Diverse Strategie

```python
from norm_rag import GraphBuilder

# Costruisci con tutte le strategie
strategies = ["entity_centric", "hierarchical", "temporal", "semantic_clustering", "hybrid"]
graphs = {}

for strategy in strategies:
    builder = GraphBuilder(strategy=strategy)
    graphs[strategy] = builder.build_graph(result, graph_name=f"Graph {strategy}")

# Confronta
for name, g in graphs.items():
    print(f"{name:20s}: {len(g.nodes):4d} nodi, {len(g.edges):4d} archi")

# Usa versioning per salvare tutte le varianti
vm = GraphVersionManager(graphs["hybrid"])
for strategy, graph in graphs.items():
    vm.create_snapshot(graph, f"v1.0-{strategy}", f"Strategia: {strategy}")
```

### Esempio 2: Merge di Grafi da Fonti Diverse

```python
# Grafo 1: Codice Penale
segments_cp = reader.read_file("codice_penale.txt")
result_cp = extractor.extract_from_segments(segments_cp)
graph_cp = builder.build_graph(result_cp, graph_name="Codice Penale")

# Grafo 2: Procedura Penale
segments_cpp = reader.read_file("codice_procedura_penale.txt")
result_cpp = extractor.extract_from_segments(segments_cpp)
graph_cpp = builder.build_graph(result_cpp, graph_name="Procedura Penale")

# Crea version manager e merge
vm = GraphVersionManager(graph_cp)
vm.create_snapshot(graph_cp, "v1.0-cp", "Solo Codice Penale")

# Estendi con procedura penale
for node in graph_cpp.nodes.values():
    graph_cp.add_node(node)
for edge in graph_cpp.edges.values():
    graph_cp.add_edge(edge)

vm.create_snapshot(graph_cp, "v1.1-merged", "CP + CPP merged")

# Confronta
diff = vm.compare_versions("v1.0-cp", "v1.1-merged")
print(diff.get_summary())
```

### Esempio 3: Workflow Multi-Validatore

```python
# Validatore 1: Esperto di diritto sostanziale
v1 = DomainValidator(
    graph,
    validator_id="prof_rossi",
    expertise_areas=["diritto penale sostanziale"]
)

# Validatore 2: Esperto di procedura
v2 = DomainValidator(
    graph,
    validator_id="prof_bianchi",
    expertise_areas=["diritto processuale penale"]
)

# Assegna task per area di competenza
for node in graph.nodes.values():
    if "procedura" in node.description.lower():
        # Task per v2
        v2.create_validation_tasks()
    else:
        # Task per v1
        v1.create_validation_tasks()

# Report comparativo
s1 = v1.get_validation_summary()
s2 = v2.get_validation_summary()

print(f"""
Validatore 1 ({s1['validator_name']}): {s1['tasks']['completed']} task completati
Validatore 2 ({s2['validator_name']}): {s2['tasks']['completed']} task completati
""")
```

---

## 📖 API Reference

Documentazione completa delle API:

### Data Models

- `EntityType`: Enum per tipi di entità giuridiche
- `RelationType`: Enum per tipi di relazioni
- `ValidationStatus`: Enum per stati di validazione
- `Provenance`: Classe per tracciabilità fonte
- `Node`: Classe per nodi del grafo
- `Edge`: Classe per archi del grafo
- `GraphMetadata`: Metadati del grafo
- `AuditLogEntry`: Entry del log di audit

### Core Classes

- `TextReader`: Lettore multi-formato con provenance
- `InformationExtractor`: Estrattore di entità/relazioni
- `GraphBuilder`: Costruttore di grafi con strategie
- `LegalKnowledgeGraph`: Grafo di conoscenza giuridica
- `GraphEditor`: Editor per manipolazione manuale
- `GraphVersionManager`: Gestore versioni
- `DomainValidator`: Interfaccia per validatori esperti
- `AuditTrail`: Sistema di audit trail

---

## 🤝 Contribuire

Per contribuire al progetto:

1. Implementa nuove strategie di costruzione grafi
2. Aggiungi nuovi tipi di entità/relazioni giuridiche
3. Migliora l'estrazione automatica con LLM
4. Estendi il supporto formati (HTML, XML, etc.)
5. Implementa metriche di qualità del grafo

---

## 📝 Licenza

Vedere file LICENSE per dettagli.

---

## 📬 Contatti

Per domande o supporto, contattare il team di sviluppo.
```
