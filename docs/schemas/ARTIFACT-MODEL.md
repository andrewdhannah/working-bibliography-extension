# Working Bibliography — Artifact Model

**Sprint:** WB-ARTIFACT-MODEL-1
**Status:** Ratified
**Schema:** `docs/schemas/wb-artifact.schema.json`
**Decisions:** ADR-WB-001, ADR-WB-002, ADR-WB-005, ADR-WB-006

---

## 1. Model Philosophy

The artifact model follows one governing principle from ADR-WB-001:

> **The canonical artifact is captured content plus provenance. The embedding is a derived index.**

This prevents the common RAG mistake where the vector database becomes the source of truth. In this model:

- The artifact is the source of truth.
- Provenance is non-negotiable.
- Content integrity is verifiable through hashing.
- Derived indexes (embeddings, search vectors) are replaceable without custody loss.

---

## 2. Canonical Object

### Required Fields

Every artifact must have:

| Field | Purpose | Validation |
|---|---|---|
| `artifact_id` | Stable unique identifier | Pattern `^WB-[0-9]{5}$` |
| `spec_version` | Schema version | Semantic versioning |
| `content_hash` | SHA-256 of canonical text | 64 hex characters |
| `content_hash_algorithm` | Always `sha-256` | Enum |
| `captured_at` | When source was captured | ISO 8601 datetime |
| `source` | Provenance metadata | Object with `retrieved_at` |
| `content.canonical_text` | Authoritative text | Non-empty string |
| `content.raw_format` | Original format | Enum (html, pdf, text, etc.) |
| `lifecycle` | Current state | Enum (active, archived, revoked) |

### Optional Fields

| Field | Purpose | When Needed |
|---|---|---|
| `source.url` | Original URL | Web-sourced artifacts |
| `source.title` | Human-readable title | Any named source |
| `source.author` | Creator attribution | Attributed sources |
| `source.publisher` | Publishing context | Published materials |
| `source.source_id` | External identifier | DOI, ISBN, archival ID |
| `source.language` | Language tag | Multi-language support |
| `content.chunks` | Segmented representation | Retrieval optimization |
| `content.word_count` | Derived statistic | Analytics |
| `content.character_count` | Derived statistic | Analytics |
| `relationships` | Inter-artifact links | Connected knowledge |
| `lifecycle_transitions` | Audit trail | Compliance |
| `metadata` | Custom annotations | Domain-specific needs |
| `index_references` | Derived index pointers | Retrieval integration |
| `receipts` | Evidence references | Governance tracing |

---

## 3. Identity

Artifact identity is established through three independent mechanisms:

### 3.1 Artifact ID (`artifact_id`)

```
WB-XXXXX
```

A sequentially assigned stable identifier. This is the human-facing identity for cross-referencing. Pattern: `WB-` followed by zero-padded 5-digit number.

**Examples:** `WB-00001`, `WB-00042`, `WB-99999`

### 3.2 Content Hash (`content_hash`)

SHA-256 digest of the `content.canonical_text` field. This is the verifiable identity — two artifacts with the same hash contain identical canonical content.

**Format:** 64 lowercase hex characters.

### 3.3 Temporal Anchor (`captured_at`)

ISO 8601 timestamp of when the source was captured by the extension. Combined with artifact_id and content_hash, this triple provides durable identity across index rebuilds and data migrations.

### Identity Invariants

| Invariant | Description |
|---|---|
| I-001 | artifact_id is immutable after creation |
| I-002 | content_hash changes only if canonical_text changes |
| I-003 | captured_at is immutable after creation |
| I-004 | artifact_id + content_hash uniquely identifies a version |
| I-005 | No two artifacts share the same artifact_id at the same time |

---

## 4. Provenance

Provenance is the traceable origin of the artifact. Every artifact must document at minimum when and how it was retrieved.

### Required Provenance

```json
{
  "source": {
    "retrieved_at": "2026-07-21T14:30:00Z"
  }
}
```

### Full Provenance

```json
{
  "source": {
    "url": "https://example.com/article",
    "title": "Article Title",
    "author": "Author Name",
    "publisher": "Publication Name",
    "retrieved_at": "2026-07-21T14:30:00Z",
    "source_id": "doi:10.1234/example",
    "language": "en"
  }
}
```

### Provenance Invariants

| Invariant | Description |
|---|---|
| P-001 | retrieved_at must be present on every artifact |
| P-002 | url should be present for web-sourced artifacts |
| P-003 | retrieved_at must not be in the future |
| P-004 | content_hash must be computable from canonical_text |
| P-005 | If source_id is present, it must match a known identifier format |

---

## 5. Content Representation

### Canonical Text

The `content.canonical_text` field is the authoritative content. It is:

- Always present
- Always non-empty
- What the content_hash is computed against
- What all derived representations reference

### Raw Format

The `content.raw_format` field preserves the original source type before normalization:

| Format | When Used |
|---|---|
| `html` | Web page or HTML document |
| `pdf` | PDF document |
| `text` | Plain text |
| `chat_export` | Conversation or chat transcript |
| `markdown` | Markdown document |
| `json` | Structured data |
| `unknown` | Undetermined or mixed |

### Chunks

When present, `content.chunks` provides a segmented view of the canonical text for retrieval. Chunks:

- Are derived from `canonical_text`
- Are not independently stored
- Are replaceable without artifact identity loss
- Must reference their position in the canonical text

---

## 6. Relationships

Relationships connect artifacts to form a knowledge graph. All relationships are advisory — they document connections without creating graph-level consistency guarantees.

### Relationship Types

| Type | Direction | Meaning |
|---|---|---|
| `derived_from` | Outgoing | This artifact was created from the referenced source |
| `supersedes` | Outgoing | This artifact replaces the referenced artifact |
| `superseded_by` | Incoming | This artifact has been replaced |
| `related_to` | Bidirectional | Conceptual relationship |
| `referenced_in` | Outgoing | External reference (session, conversation, work packet) |

### Relationship Invariants

| Invariant | Description |
|---|---|
| R-001 | Relationship references use artifact_id format |
| R-002 | An artifact cannot reference itself |
| R-003 | supersedes and superseded_by are complementary pairs |

---

## 7. Lifecycle

Artifact lifecycle is managed independently within Working Bibliography per ADR-WB-005. Lifecycle state does not cross into Librarian custody space.

### States

```
ACTIVE (default)
    │
    ├──→ ARCHIVED  (content preserved, excluded from search)
    │
    └──→ REVOKED   (content preserved, access denied)
```

| State | Capabilities | Searchable | Receipt-preserving |
|---|---|---|---|
| `active` | Full access | Yes | Yes |
| `archived` | Read-only | No | Yes |
| `revoked` | None | No | Yes |

### Transitions

| From | To | Typical Reason |
|---|---|---|
| active | archived | Source no longer relevant |
| active | revoked | Source found to be untrustworthy |
| archived | active | Reactivated for new context |
| revoked | — | Terminal state |

### Lifecycle Invariants

| Invariant | Description |
|---|---|
| L-001 | Lifecycle transitions are recorded in `lifecycle_transitions` |
| L-002 | REVOKED is a terminal state — no transition out |
| L-003 | Content is never deleted — lifecycle governs access, not storage |
| L-004 | Each transition produces a lifecycle_receipt reference |

---

## 8. Derived Index References

Per ADR-WB-001, embeddings and search indexes are derived from the canonical artifact. The `index_references` field provides pointers to these derived representations.

```json
{
  "index_references": {
    "embedding_id": "emb-wb-00001-v1",
    "search_index_id": "idx-wb-00001-v1"
  }
}
```

### Index Invariants

| Invariant | Description |
|---|---|
| D-001 | The artifact does not depend on the index |
| D-002 | Index loss does not destroy custody |
| D-003 | Index can be regenerated from canonical_text |
| D-004 | Each index generation increments the version suffix |

---

## 9. Schema Validation

The JSON Schema at `docs/schemas/wb-artifact.schema.json` validates artifacts at:

1. **Capture time** — before the artifact is stored
2. **Retrieval time** — before results are returned
3. **Batch operations** — before bulk processing
4. **Migration time** — when artifact schemas evolve

### Validation Priorities

| Priority | What Is Checked |
|---|---|
| Required | All required fields present |
| Format | Field types and patterns |
| Integrity | content_hash matches canonical_text |
| Relationships | Reference formats and consistency |
| Lifecycle | State transitions and audit trail |
