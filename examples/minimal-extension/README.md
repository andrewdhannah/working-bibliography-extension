# Minimal Librarian Extension — Starter Template

This is a minimal starter for creating a Librarian-compatible extension.

## Files

| File | Purpose | Required |
|---|---|---|
| `identity.json` | Extension identity (ID, version, contract reference) | ✅ Yes |
| `contract.json` | Formal contract with Librarian core | ✅ Yes |
| `capabilities.json` | Declared tools, risk levels, permissions | ✅ Yes |
| `permissions.json` | Allowed operations, forbidden actions, enforcement | ✅ Yes |

## Next Steps

1. **Copy** this directory as a starting point
2. **Edit** each file to match your extension's domain
3. **Implement** your MCP server following the reference implementation at `src/mcp/`
4. **Implement** handshake lifecycle following `src/handshake/`
5. **Add** enforcement, drift detection, and revocation following `src/enforcement/`, `src/drift/`, `src/revocation/`

## Required Reading

| Document | What It Covers |
|---|---|
| `docs/EXTENSION-SPECIFICATION-v1.md` | Formal compliance requirements |
| `docs/EXTENSION-DEVELOPER-GUIDE.md` | Step-by-step implementation guide |
| `docs/COMPLIANCE-MATRIX.md` | Requirement-to-validator mapping |
| `docs/contracts/WB-LIBRARIAN-CONTRACT-v1.json` | Full reference contract |
| `MILESTONE-ROADMAP.md` | Reference implementation progress |

## License

This template is part of the Working Bibliography Extension reference implementation.

Librarian extensions are not granted access.
They establish a contract, declare capabilities, pass validation,
and operate within defined ownership boundaries.
