# Test Extension

**Extension ID:** `test-extension-extension`
**Domain:** `knowledge.testing`
**Status:** REGISTERED

## Purpose

Test Extension — a governed Librarian extension in the knowledge.testing domain.

## Non-Goals

- Produce Librarian Owner decisions
- Mutate Librarian authority state
- Access other extensions' data
- Operate without an active, verified contract

## Extension Lifecycle

```
REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE
                                                     → SUSPENDED → REVOKED
```

Capabilities are only available in ACTIVE state.

## Governance Boundaries

| Owns | Does Not Own |
|------|-------------|
| knowledge.testing artifacts | Librarian authority state |
| Capability declarations | Owner decisions |
| Domain receipts | Sprint ledger |
| Extension lifecycle | Core custody records |

## Relationship to Librarian

This extension operates under the Librarian extension contract model.
It connects through MCP and is governed by contract, handshake,
enforcement, and drift detection.
