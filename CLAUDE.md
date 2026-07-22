# Working Bibliography Extension — CLAUDE.md

**Project:** `working-bibliography-extension`
**Purpose:** Reference implementation of the Librarian extension port model.

## Startup

- `start` → normal governed startup via `.librarian/project-index.json` startup contract
- `start planning` → reserved intent for cross-project planning (not project-local)

See `docs/identity/PROJECT-IDENTITY.md` for full project identity and governance posture.

## Key Sources

- **Identity:** `docs/identity/PROJECT-IDENTITY.md`
- **Vision:** `docs/vision/WORKING-BIBLIOGRAPHY-VISION.md`
- **Architecture:** `docs/architecture/ARCHITECTURE.md`
- **Extension Port Model:** `docs/architecture/EXTENSION-PORT-MODEL.md`
- **Contracts:** `docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json`, `docs/contracts/EXTENSION-HANDSHAKE-CONTRACT.md`
- **Governance:** `docs/governance/DRIFT-GOVERNANCE.md`, `docs/governance/ACCESS-REVOCATION-PROTOCOL.md`
- **Schemas:** `docs/schemas/wb-artifact.schema.json`, `docs/schemas/wb-contract.schema.json`, `docs/schemas/wb-capability.schema.json`

## External Reference (Librarian)

The Librarian governance docs at `../active/librarian/docs/governance/` and `../active/librarian/docs/schemas/` are the authoritative source for existing contracts:
- `ADDON-BOUNDARY-CONTRACT.md` — core-owned vs addon-owned responsibilities
- `MULTINODE-MCP-DOCUMENT-CUSTODY.md` — custody modes and mutation allowances
- `LOOP-KERNEL-ADDONS.md` — add-on recipe and lifecycle
- `CODE-CAPABILITY-MODEL.md` — capability registration and invariants
- `CROSS-REPO-CONTRACT-MODEL.md` — contract types and stability levels
- `DRIFT-ESCALATION-PROTOCOL.md` — drift detection and escalation
