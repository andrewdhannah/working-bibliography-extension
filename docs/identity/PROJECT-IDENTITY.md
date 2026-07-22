# PROJECT-IDENTITY.md — Working Bibliography Extension

**Project ID:** `working-bibliography-extension`
**Display Name:** Working Bibliography Extension
**Version:** 0.1.0-proposed
**Created:** 2026-07-21
**Owner:** Andrew Hannah

---

## Purpose

Reference implementation proving the Librarian extension port model via an external knowledge custody provider. The Working Bibliography is the first tenant of the extension ecosystem — an independently governed capability that attaches to Librarian through existing contracts.

## Primary Hypothesis

The Librarian custody model applies equally to internally created artifacts and externally sourced knowledge artifacts. The same governance primitives that govern AI-generated work products (identity, provenance, version, relationships, lifecycle) can govern what AI reads and remembers.

## Secondary Hypothesis

The Librarian MCP layer can act as an extension port system where capabilities are granted, monitored, and revoked through contracts. An independently governed capability can attach to Librarian through existing contracts without core expansion.

## Relationship to Librarian

```
Librarian Core (governance kernel)
    |
MCP Extension Port Model
    |
Working Bibliography Extension (first tenant)
```

The extension operates entirely within **addon-owned space** per `ADDON-BOUNDARY-CONTRACT.md`. It connects through the MCP JSON-RPC 2.0 port using existing tool registration patterns (`tools/list`, `tools/call`). The extension announces identity, proves declared capabilities, and receives Owner-controlled activation — the same governance sequence Librarian applies to its own artifacts.

## Extension Boundary Assumptions

| Assumption | Rationale |
|---|---|
| No Librarian core changes | The experiment tests whether the existing core can support an ecosystem without modification |
| Extension is independently governed | WB artifacts have their own lifecycle, schema, and custody — they are not Librarian artifacts |
| Core survives detachment | If the extension disappears, Librarian must function without degradation |
| Contracts before code | The extension contract is the experiment. Code only proves the contract is implementable. |
| Discovery ≠ Trust | REGISTERED state is separate from OWNER_APPROVED. Unknown does not equal untrusted. |

## Non-Goals

- Produce Librarian Owner decisions
- Mutate Librarian authority state or sprint ledger
- Write governed sprint state
- Mutate Librarian custody records outside own domain
- Modify Librarian MCPController.swift
- Create a parallel architecture
- Multi-user collaboration (deferred — existing multi-user docs provide the model when needed)
- Cloud/edge sync (deferred — CLOUD-EDGE-CUSTODY-ARCHITECTURE.md defines the pattern)

## Source Authority

| Class | Source | Authority |
|---|---|---|
| A — Entrypoint | `CLAUDE.md` (this project) | Platform routing |
| B — Contract | `project-index.json`, `startup-contract.json` | Machine identity |
| C — MCP Context | Librarian project tools | Governed context |
| G — Receipts | `receipts/` | Audit trail |
| F — Reference | Librarian governance docs (`docs/governance/`, `docs/rules/`, `docs/schemas/`) | Existing contracts and patterns |

## Extension Lifecycle

```
REGISTERED
    ↓
CONTRACT VERIFIED
    ↓
OWNER APPROVED
    ↓
ACTIVE
    ↓
SUSPENDED (drift review) | REVOKED (contract failure)
```
