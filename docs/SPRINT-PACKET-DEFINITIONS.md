# Sprint Packet Definitions — Working Bibliography Extension

**Project:** `working-bibliography-extension`
**Status:** Candidate — each requires Owner authorization before execution
**Sequence:** Contract-first. Intent → Contract → Implementation → Proof.

---

## Epic: EPIC-WORKING-BIBLIOGRAPHY-FOUNDATION-1

**Authorization type:** `category_bounded`
**Advancement rule:** `owner_must_confirm_each`

---

### Sprint: WB-REPOSITORY-CREATION-1 ✅ COMPLETE

**Authorization prompt:**
> Authorize sprint WB-REPOSITORY-CREATION-1 for project working-bibliography-extension.

**Objective:** Establish the standalone governed project repository and initial Librarian registration surfaces.

**Scope:**
- Create repository structure
- Confirm project identity files
- Add Librarian project registration artifacts
- Create startup entrypoint documentation
- Establish initial commit and evidence receipt

**Required outputs:**
- PROJECT-IDENTITY.md
- CLAUDE.md
- `.librarian/project-index.json`
- current-project.json
- Initial repository scaffold
- Foundation commit receipt

**Constraints:**
- No implementation code
- No Librarian core changes
- No extension runtime
- No mutation of existing governance records

**Acceptance criteria:**
- Project is visible through registered project surfaces
- Repository identity is reproducible
- Purpose, hypothesis, and non-goals are captured

---

### Sprint: WB-ARCHITECTURE-VISION-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-ARCHITECTURE-VISION-1 for project working-bibliography-extension.

**Objective:** Capture the architectural intent and boundaries of the Working Bibliography extension before implementation.

**Scope:**
- Vision document
- Architecture document
- Extension boundary model
- Relationship definition between Working Bibliography and Librarian core

**Required decisions:**
- Working Bibliography remains standalone
- Librarian core remains unchanged
- MCP is the extension boundary
- Custody applies to external knowledge artifacts

**Required outputs:**
- `docs/vision/WORKING-BIBLIOGRAPHY-VISION.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/EXTENSION-PORT-MODEL.md`

**Constraints:**
- No schema implementation
- No MCP implementation
- No capability registration

**Acceptance criteria:**
- Architecture can explain attach/detach behavior
- Ownership boundaries are explicit
- Non-goals are documented

---

### Sprint: WB-ARTIFACT-MODEL-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-ARTIFACT-MODEL-1 for project working-bibliography-extension.

**Objective:** Define the canonical governed artifact model for external knowledge artifacts.

**Scope:**
- Artifact identity
- Provenance metadata
- Content representation
- Relationships
- Lifecycle states
- Derived index references

**Required outputs:**
- `docs/schemas/wb-artifact.schema.json`
- Valid fixtures (`tests/fixtures/artifacts/valid/`)
- Invalid fixtures (`tests/fixtures/artifacts/invalid/`)
- Artifact model documentation

**Constraints:**
- Embeddings are derived data, not canonical artifacts
- Artifact custody remains within Working Bibliography
- No Librarian state mutation

**Acceptance criteria:**
- Artifact schema validates expected cases
- Provenance survives transformation
- Artifact identity remains stable

---

### Sprint: WB-EXTENSION-CONTRACT-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-EXTENSION-CONTRACT-1 for project working-bibliography-extension.

**Objective:** Capture the extension contract before any implementation begins. The contract *is* the experiment — code only proves the contract is implementable.

**Scope:**
- Define WB-Librarian contract terms
- Define extension handshake protocol
- Define capability declaration schema
- Define forbidden actions and enforcement

**Required outputs:**
- `docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json`
- `docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md`
- `mcp/capabilities.json`
- `mcp/permissions.json`

**Constraints:**
- No MCP server implementation
- No ingestion code
- Contract must be independently reviewable

**Acceptance criteria:**
- Contract can be verified without running code
- Handshake states are defined (REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE → SUSPENDED → REVOKED)
- Forbidden actions are enumerated
- Capability declarations match intended tool surface

---

## Epic: EPIC-KNOWLEDGE-CUSTODY-IMPLEMENTATION-1

**Authorization type:** `category_bounded`
**Advancement rule:** `owner_must_confirm_each`

---

### Sprint: WB-INGESTION-PIPELINE-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-INGESTION-PIPELINE-1 for project working-bibliography-extension.

**Objective:** Implement artifact capture and normalization pipeline.

**Supported inputs:**
- URL capture
- HTML capture
- Text capture
- Chat export capture

**Pipeline stages:** Capture → Normalize → Extract → Store → Receipt

**Required outputs:**
- Ingestion pipeline (`src/capture/`)
- Capture receipts
- Sample artifacts with provenance

**Constraints:**
- No automatic ingestion without explicit trigger
- Preserve source provenance

**Acceptance criteria:**
- Three input types produce governed artifacts
- Each artifact has identity and provenance

---

### Sprint: WB-METADATA-EXTRACTION-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-METADATA-EXTRACTION-1 for project working-bibliography-extension.

**Objective:** Establish source metadata and integrity tracking.

**Scope:**
- URL metadata (title, author, publisher)
- Retrieval timestamp
- Content hashing (SHA-256)

**Required outputs:**
- Metadata extraction (`src/model/metadata.py`)
- Hash validation tests
- Metadata extraction fixtures

**Acceptance criteria:**
- Artifact identity can be verified independently
- Source information remains traceable

---

### Sprint: WB-EMBEDDING-LAYER-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-EMBEDDING-LAYER-1 for project working-bibliography-extension.

**Objective:** Add derived retrieval indexes without making embeddings the source of truth.

**Scope:**
- Chunking strategy
- Embedding generation
- Vector storage reference

**Constraints:**
- Embeddings remain replaceable
- Canonical artifact remains text plus provenance

**Acceptance criteria:**
- Query results resolve back to artifact identity
- Index loss does not destroy custody records

---

### Sprint: WB-RETRIEVAL-INTERFACE-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-RETRIEVAL-INTERFACE-1 for project working-bibliography-extension.

**Objective:** Provide governed knowledge retrieval.

**Required behavior:**
- Search returns matching content + Artifact ID + Source + Timestamp + Hash

**Acceptance criteria:**
- Retrieval is provenance-aware
- Results are traceable to captured artifacts

---

## Epic: EPIC-LIBRARIAN-EXTENSION-PORT-VALIDATION-1

**Authorization type:** `category_bounded`
**Advancement rule:** `owner_must_confirm_each`

---

### Sprint: WB-MCP-INTERFACE-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-MCP-INTERFACE-1 for project working-bibliography-extension.

**Objective:** Implement Working Bibliography MCP surface following Librarian MCP conventions.

**Initial tools:**
- `wb_register_artifact`
- `wb_get_artifact`
- `wb_list_artifacts`

**Required outputs:**
- MCP server (`src/mcp/`)
- Tool registration
- Permission declarations

**Constraints:**
- Read/write boundaries explicit
- No core mutation tools

**Acceptance criteria:**
- MCP `tools/list` succeeds
- Tools execute through declared permissions

---

### Sprint: WB-EXTENSION-HANDSHAKE-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-EXTENSION-HANDSHAKE-1 for project working-bibliography-extension.

**Objective:** Implement extension identity and contract handshake.

**Lifecycle states:** REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE → (SUSPENDED | REVOKED)

**Required outputs:**
- Extension manifest
- Handshake contract validation
- Registration receipt

**Acceptance criteria:**
- Extension identity verified
- Capability declaration validated
- Activation requires approval state

---

### Sprint: WB-CONTRACT-ENFORCEMENT-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-CONTRACT-ENFORCEMENT-1 for project working-bibliography-extension.

**Objective:** Validate that extension behavior matches declared contract.

**Required checks:**
- Declared capabilities match available tools
- Forbidden actions are blocked
- Ownership boundaries enforced

**Acceptance criteria:**
- Contract violations detected
- Valid behavior accepted

---

## Epic: EPIC-EXTENSION-TRUST-GOVERNANCE-1

**Authorization type:** `category_bounded`
**Advancement rule:** `owner_must_confirm_each`

---

### Sprint: WB-DRIFT-DETECTION-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-DRIFT-DETECTION-1 for project working-bibliography-extension.

**Objective:** Apply Librarian drift governance to extensions.

**Classifications:** PASS | OBSERVATION | REVOKE

**Acceptance criteria:**
- Expected behavior compared against observed behavior
- Drift produces evidence

---

### Sprint: WB-ACCESS-REVOCATION-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-ACCESS-REVOCATION-1 for project working-bibliography-extension.

**Objective:** Prove extension isolation and controlled removal.

**Test sequence:**
1. Suspend extension
2. Remove access
3. Verify Librarian operation
4. Restore extension

**Acceptance criteria:**
- Core survives extension failure
- Extension state remains recoverable

---

### Sprint: WB-VALIDATION-FIXTURES-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-VALIDATION-FIXTURES-1 for project working-bibliography-extension.

**Objective:** Establish repeatable validation fixtures.

**Required fixtures:**
- Valid artifact
- Invalid artifact
- Boundary violation
- Contract mismatch

**Acceptance criteria:**
- Validation failures are deterministic

---

## Epic: EPIC-INTEGRATION-DEMONSTRATION-1

**Authorization type:** `category_bounded`
**Advancement rule:** `owner_must_confirm_each`

---

### Sprint: WB-END-TO-END-TEST-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-END-TO-END-TEST-1 for project working-bibliography-extension.

**Objective:** Demonstrate complete governed knowledge lifecycle.

**Flow:** Article → Artifact → Metadata → Embedding → Retrieval → Receipt

**Acceptance criteria:**
- Full evidence chain exists
- Retrieval references governed artifact
- Receipt links reasoning context

---

### Sprint: WB-DETACHMENT-TEST-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-DETACHMENT-TEST-1 for project working-bibliography-extension.

**Objective:** Prove extension independence.

**Test sequence:**
1. Attach extension
2. Use capability
3. Disconnect extension
4. Verify core health
5. Reconnect

**Acceptance criteria:**
- Core unaffected
- No custody loss

---

### Sprint: WB-DOCUMENTATION-SPRINT-1 ⏳ PENDING

**Authorization prompt:**
> Authorize sprint WB-DOCUMENTATION-SPRINT-1 for project working-bibliography-extension.

**Objective:** Capture final reference implementation documentation.

**Required outputs:**
- `docs/architecture/EXTENSION-PORT-MODEL.md`
- `docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md`
- `docs/governance/DRIFT-GOVERNANCE.md`
- `docs/whitepaper/KNOWLEDGE-CUSTODY-WHITEPAPER-NOTE.md`
- Final architecture documentation

**Acceptance criteria:**
- Reference implementation can be understood without tribal knowledge

---

## Execution Sequence Summary

```
Step 0: Refresh state                                  ✅
Step 1: Register project identity                      ✅
    ↓
EPIC-WORKING-BIBLIOGRAPHY-FOUNDATION-1
    ├── WB-REPOSITORY-CREATION-1                       ✅
    ├── WB-ARCHITECTURE-VISION-1                       ⏳
    ├── WB-ARTIFACT-MODEL-1                            ⏳
    └── WB-EXTENSION-CONTRACT-1                        ⏳
    ↓
EPIC-KNOWLEDGE-CUSTODY-IMPLEMENTATION-1
    ├── WB-INGESTION-PIPELINE-1                        ⏳
    ├── WB-METADATA-EXTRACTION-1                       ⏳
    ├── WB-EMBEDDING-LAYER-1                           ⏳
    └── WB-RETRIEVAL-INTERFACE-1                       ⏳
    ↓
EPIC-LIBRARIAN-EXTENSION-PORT-VALIDATION-1
    ├── WB-MCP-INTERFACE-1                             ⏳
    ├── WB-EXTENSION-HANDSHAKE-1                       ⏳
    └── WB-CONTRACT-ENFORCEMENT-1                      ⏳
    ↓
EPIC-EXTENSION-TRUST-GOVERNANCE-1
    ├── WB-DRIFT-DETECTION-1                           ⏳
    ├── WB-ACCESS-REVOCATION-1                         ⏳
    └── WB-VALIDATION-FIXTURES-1                       ⏳
    ↓
EPIC-INTEGRATION-DEMONSTRATION-1
    ├── WB-END-TO-END-TEST-1                           ⏳
    ├── WB-DETACHMENT-TEST-1                           ⏳
    └── WB-DOCUMENTATION-SPRINT-1                      ⏳
```

**State transition key:** ✅ Complete | ⏳ Pending Owner authorization | 🔒 Future
