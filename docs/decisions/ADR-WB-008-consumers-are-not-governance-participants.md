# ADR-WB-008 — Consumers Are Not Governance Participants

**Status:** Accepted
**Date:** 2026-07-21
**Context:** Milestone 4 — Consumer Capability Discovery
**Supersedes:** None
**Cross-ref:** ADR-WB-001 through ADR-WB-007, EXTENSION-SPECIFICATION-v1.md

---

## Decision

The Librarian governance model must remain independent of consuming applications. Agents (OpenWork, Claude, DeepSeek, GPT), desktop applications, workflow engines, human operator interfaces, and other services consume capability projections but **do not define capability authority**.

The capability projection is a **governance artifact**, not an agent-specific protocol.

## Rationale

The most common failure mode in platform architectures is coupling the governance model to a specific consumer:

```
Bad:
  OpenWork Agent → Librarian → Extensions
  (Librarian becomes "OpenWork's extension system")

Good:
  Any Consumer → MCP → Librarian → Extensions
  (Librarian is a governance kernel, not an agent platform)
```

Librarian does not need to know what the consumer is, only that the consumer is authorized to request a capability projection. The consumer decides what to do with the information.

### What This Protects Against

| Risk | Without ADR-WB-008 | With ADR-WB-008 |
|---|---|---|
| Consumer coupling | Librarian assumes OpenWork agent format | Librarian returns standard projection |
| Consumer-specific logic | "Only OpenWork can query capabilities" | Any MCP client can query |
| Agent loop coupling | "Refresh when agent starts session" | "Refresh when consumer requests" |
| Platform lock-in | Extension model tied to one client | Extension model works with any client |

## Consumer-Agnostic Projection

The projection is a governance artifact that any consumer can request:

```json
{
  "projection_id": "CP-20260721-0001",
  "generated_at": "2026-07-21T18:00:00Z",
  "authority": "librarian-core",
  "extensions": [
    {
      "extension_id": "working-bibliography-extension",
      "lifecycle": "ACTIVE",
      "contract": "WB-LIBRARIAN-CONTRACT-v1",
      "capabilities": [
        { "name": "search_context", "risk": "R0" }
      ]
    }
  ]
}
```

The consumer (AI agent, CLI tool, web UI, workflow engine) interprets this artifact according to its own needs. Librarian does not enforce consumer-side behavior.

## Consequences

- OpenWork is one consumer. Claude is one consumer. DeepSeek is one consumer. Future unknown systems can participate without modifying Librarian.
- The capability projection tool (`librarian_capability_projection`) must not contain consumer-specific logic.
- The extension harness (Milestone 4) should be a consumer-agnostic conformance test, not an OpenWork-specific integration.
- The Working Bibliography extension proves: "Can Librarian govern independently developed capability providers without knowing what they are?" — not "Can Librarian add a bibliography plugin for one specific agent."

## Affected Components

- Milestone 4 sprint naming: "Agent" → "Consumer"
- Capability projection contract: generic consumer, not agent-specific
- Extension harness: conformance test, not agent integration
- Any future consumer integration: consumer-side, not Librarian-side

## Unaffected

- Existing extension governance model (handshake, enforcement, drift, revocation)
- ADR-WB-001 through ADR-WB-007
- Working Bibliography artifact model and MCP surface
- Runtime Node capability provider model
