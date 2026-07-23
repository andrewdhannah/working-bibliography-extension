# Conversation History Ingestion — Add-on Planning

**Status:** Planning capture — distilled from architecture discussion (2026-07-22)
**Prerequisite:** EPIC-LIBRARIAN-CAPABILITY-PROJECTION-INTEGRATION-1 (sealed #542–#545)
**Related:** `docs/vision/EXTENSION-ECOSYSTEM-ROADMAP.md`, `docs/vision/DISTRIBUTED-CAPABILITY-PLATFORM.md`

---

## Overview

A knowledge ingestion add-on that imports full chat histories from AI providers
(ChatGPT, Claude, Gemini, etc.) and converts them into canonical bibliography
sources. This lets agents reference historical conversations as evidence,
preserving context across provider switches and making years of chat history
searchable, citable, and governed.

### Why This Matters

The single biggest problem when switching AI providers is losing conversation
history. Current options are export-and-forget (data leaves, context lost) or
stay-locked-in (convenience wins). This add-on solves the underlying issue:
conversation history becomes governed evidence, not provider lock-in.

```
ChatGPT Export ─────┐
                    ├──▶ Conversation Ingester ──▶ Canonical Bibliography
Claude Export ──────┘                                    │
                                                    Search | Evidence | Context
```

---

## Architecture

### Canonical Conversation Model

Rather than storing provider-specific JSON forever, normalize into a common schema:

```
Conversation
  id                (UUID)
  provider           (chatgpt, claude, gemini, ...)
  provider_id        (original conversation ID from provider)
  title
  created_at
  updated_at
  model              (model used for this conversation)
  project_id         (optional Librarian project association)
  checksum           (SHA-256 of canonical form)

Message
  id                 (UUID)
  conversation_id    (FK to Conversation)
  parent_id          (FK to parent Message for threading)
  author             (user, assistant, system)
  role               (user, assistant, system, tool)
  timestamp
  content            (canonical text)
  attachments        (file references, images, code files)
  tool_calls         (tool invocations and results)
  metadata           (provider-specific fields as JSON blob)
  checksum           (SHA-256)

  --- Governance fields (reserved in Phase 1, enforced in Phase 6) ---
  confidence         (original, verified, superseded, disputed)
  authority          (human_decision, model_proposal, system_output)
  supersedes         (message ID this message supersedes)
  superseded_by      (message ID that supersedes this message)
  conflicts_with     (message ID of conflicting message)
  resolved_by        (message ID or receipt that resolves the conflict)
```

Provider-specific fields stay in the `metadata` JSON blob. Future providers
become adapter implementations, not schema changes.

**Design note:** Governance fields are reserved at schema creation time (Phase 1)
even though the governance behavior (confidence evaluation, supersession,
conflict detection) is not activated until Phase 6. This follows the pattern
established elsewhere in the Librarian: establish contracts before capabilities,
and avoid schema migrations by anticipating governance requirements early.

### Provider Adapters

Each provider gets an adapter that converts its export format to the canonical model:

| Provider | Export Format | Adapter |
|----------|--------------|---------|
| ChatGPT | JSON (conversations.json) | `adapters/chatgpt.py` |
| Claude | JSON (claude.json) / markdown | `adapters/claude.py` |
| Gemini | Google Takeout JSON | `adapters/gemini.py` |
| OpenWebUI | JSON | `adapters/openwebui.py` |
| LibreChat | JSON | `adapters/librechat.py` |
| OpenHands | JSON | `adapters/openhands.py` |
| OpenRouter | JSON | `adapters/openrouter.py` |
| Future | TBD | `adapters/future.py` |

Every adapter produces exactly the same internal model.

### Bibliography Integration

Conversations become bibliography sources. Each import produces governed artifacts:

```
Conversation Import
    │
    ├── Conversation record (canonical)
    ├── Bibliography entry per topic
    ├── Evidence receipts
    └── Search index entries
```

Agents can reference:

```
Conversation → Message → Evidence → Claim → Current work
```

So if an agent says "We discussed startup architecture last October," it can cite
the exact conversation instead of relying on model memory.

---

## Semantic Enrichment

The ingester can optionally extract structured knowledge from conversations:

| Extract | Example |
|---------|---------|
| Topics | "startup protocol", "GRDB migrations" |
| Decisions | "Use SQLite with GRDB" |
| Open questions | "Should we use pgvector?" |
| Action items | "Add node health receipts" |
| Architecture | "Three-layer governance model" |
| Code snippets | Key implementation fragments |
| Document references | Links to specs, receipts, sprints |

These become bibliography nodes that integrate with existing project knowledge:

```
Conversation
    ├── Decision
    ├── Topic
    ├── Sprint
    ├── Epic
    ├── Document
    └── Repository
```

### Conversation Provenance Graph

A further extension: identify references within conversations to:

- Repository commits
- Sprint receipts
- Documents
- Epics
- Architectural decisions
- Bibliography entries

This creates explicit links into the existing knowledge graph, enabling queries like:

- "When did this design decision first appear?"
- "Which conversations led to Sprint #540?"
- "Show the complete chain of evidence from initial discussion to implementation."

This elevates imported chat history from archival reference to first-class,
traceable project evidence.

---

## Cross-Provider Continuity

One of the strongest features is provider independence:

```
2024: ChatGPT ─────────────┐
                           │
2025: Claude ──────────────┤
                           ├──▶ Librarian Bibliography
2026: The Librarian ───────┤
                           │
Future Provider ───────────┘
```

A new model can answer using all prior conversations regardless of where they
originated. This solves the core switching-cost problem.

### Timeline View

Effectively a personal engineering history:

```
2024  ████████████████  ChatGPT
2025  ████████████████  Claude
2026  ████████████████  Librarian
```

Clicking a date opens the conversation, showing:

- What was discussed
- What decisions were made
- What evidence was referenced
- What provider was used

---

## Suggested Epic Sequencing

Place after current release stabilization, before broad agent autonomy.

### EPIC-CONVERSATION-HISTORY-INGESTION-1

| Phase | Scope | Dependency |
|-------|-------|------------|
| **Phase 1: Import + Normalization** | ChatGPT/Claude export parsers, canonical conversation model, storage schema | Export formats available |
| **Phase 2: Bibliography Integration** | Conversation bibliography nodes, evidence linking, canonical references | Phase 1 |
| **Phase 3: Provenance Graph** | Cross-reference detection (commits, receipts, decisions), knowledge graph linking | Phase 2 |
| **Phase 4: Retrieval Integration** | Keyword + metadata + semantic indexing, context query APIs | Phase 3 |
| **Phase 5: Semantic Enrichment** | Topic extraction, decision extraction, action items, entity linking | Phase 4 |
| **Phase 6: Governance Lifecycle** | Message confidence/authority markers, supersession, conflict detection | Phase 5 |

**Sequencing note:** Do not start with embeddings. Start with canonical storage and
provenance. The retrieval layer comes later. The vector index is one access path,
not the foundation.

---

## Search

| Mode | Query Example |
|------|--------------|
| Keyword | "startup protocol discussion" |
| Semantic | "conversations about evidence models" |
| Date | "conversations from October 2025" |
| Provider | "all Claude conversations" |
| Project | "discussions about librarian" |
| Participant | "conversations with Sarah" |
| Attachment | "conversations with architecture diagrams" |
| Model | "GPT-4 conversations" |
| Decision | "past architectural decisions" |
| Topic | "everything about GRDB migrations" |

### Context Retrieval for Agents

```
Query: "Find every conversation about GRDB migrations"
     → Results become citations, not model memory

Query: "Show previous architectural decisions around runtime nodes"
     → Results reference specific messages with provenance

Query: "Find the latest discussion about onboarding"
     → Returns most recent relevant conversation
```

---

## Privacy

Aligns with the project's local-first philosophy:

- Import from local export files only
- Perform all indexing locally
- Never upload conversation history
- Allow selective import by provider, date range, project, or conversation
- Support deletion and re-indexing
- All storage in existing project-local database

---

## Suggested Epics

### EPIC-CONVERSATION-HISTORY-INGESTION-1

| Sprint | Scope |
|--------|-------|
| **EXPORT-ADAPTERS-1** | ChatGPT export parser, Claude export parser, canonical conversation model |
| **CONVERSATION-STORAGE-1** | Database schema, checksums, incremental imports, deduplication |
| **BIBLIOGRAPHY-INTEGRATION-1** | Conversation bibliography nodes, evidence linking, canonical references |
| **SEARCH-INDEX-1** | Full-text indexing, semantic indexing, timeline indexing |
| **CONTEXT-QUERY-1** | Agent APIs, conversation citations, retrieval contracts |
| **IMPORT-UX-1** | Drag-and-drop imports, progress reporting, duplicate detection, validation receipts |
| **CONVERSATION-INTELLIGENCE-1** | Topic extraction, decision extraction, action item extraction, entity linking |
| **CONVERSATION-PROVENANCE-GRAPH-1** | Cross-reference detection (commits, receipts, decisions), knowledge graph linking |

---

## Retrieval Architecture Note

This add-on also surfaces a broader architectural insight about retrieval in the
Librarian. The conversation ingester feeds the **bibliography**, not a vector
database. The retrieval stack should be:

```
                Query
                  │
      ┌───────────┼────────────┐
      │           │            │
 Keyword      Bibliography    Graph
 Search        Search         Search
      │           │            │
      └───────────┼────────────┘
                  │
            Vector Recall
                  │
             Candidate Set
                  │
            Provenance Filter
                  │
         Canonical Evidence Rank
                  │
              Context Builder
                  │
                 LLM
```

Vectors are one access path into the bibliography, not the primary index.
The canonical knowledge model (bibliography + provenance + governance) remains
authoritative. Vector embeddings are a derived index, not the source of truth.

This is consistent with ADR-WB-001 (The embedding is not the artifact) and
ensures the system remains provider-agnostic at the retrieval layer as well as
the governance layer.

For the vector store specifically: since the canonical store is SQLite/GRDB,
the first question is whether SQLite with a vector extension meets performance
needs. If not, vectors can be a secondary index while SQLite remains canonical.
Only if both are insufficient would a standalone vector database be warranted.

---

## Conversation Lifecycle Governance

Imported conversations will eventually need the same governance rules as other
bibliography artifacts. Questions that arise:

- When does an imported conversation become canonical?
- Can a conversation be superseded?
- Can two conversations conflict?
- How are hallucinated assistant statements marked?
- How is human-approved reasoning separated from model-generated suggestions?

### Message Confidence and Authority

Each message can carry governance metadata:

```json
{
  "role": "assistant",
  "content": "The architecture should use SQLite with GRDB.",
  "confidence": "model_proposal",
  "authority": "system_output",
  "superseded_by": "conversation-uuid-2"
}
```

| Confidence | Meaning |
|------------|---------|
| `original` | Raw export — unverified, as-provided |
| `verified` | A human has confirmed this content |
| `superseded` | Replaced by a later decision or conversation |
| `disputed` | Contradicted by other evidence |

| Authority | Meaning |
|-----------|---------|
| `human_decision` | A person made this statement or approved it |
| `model_proposal` | AI-generated suggestion, not yet validated |
| `system_output` | Tool output, generated artifact, automatic response |

This prevents the system from accidentally treating old AI suggestions as
authoritative facts. A search for architecture decisions would surface
`human_decision` entries first; `model_proposal` entries would be marked as
unvalidated suggestions.

### Supersession and Conflict

When two conversations discuss the same topic with different conclusions:

```
Conversation A (2025-10): "Use PostgreSQL"
Conversation B (2026-03): "Use SQLite"
```

The provenance graph would show:

```
Topic: Database Selection
  Conversation A (2025-10): suggested PostgreSQL [confidence: model_proposal]
  Conversation B (2026-03): decided SQLite     [confidence: human_decision]
  Status: Conversation B supersedes A on this topic
  Receipt: architecture-decision-2026-03-15
```

### Relationship to Existing Governance

Conversations are governed artifacts. They can be:

- **Imported** (automatic, R0) — raw export, as-is
- **Indexed** (automatic, R0) — extracted metadata
- **Verified** (human, R1) — human confirms accuracy
- **Cited** (automatic, R0) — agent references as evidence
- **Superseded** (human, R1) — replaced by newer conversation
- **Disputed** (system, R0) — drift detected between conversations

This completes the three memory horizons:

| Horizon | Source | Answers |
|---------|--------|---------|
| **Current state** | SQLite, project state, receipts | "What is true now?" |
| **Operational history** | Sprints, commits, lifecycle records | "How did we get here?" |
| **Reasoning history** | Conversations, decisions, discussions | "Why did we get here?" |
