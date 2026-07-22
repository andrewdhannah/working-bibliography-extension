"""
Contract Enforcement — Runtime Verification Against Approved Contract

Implements continuous enforcement of WB-LIBRARIAN-CONTRACT-v1 during
extension operation. Validates every operation, detects drift, enforces
ownership boundaries, and produces enforcement evidence.

The enforcement layer sits between the MCP server and the handshake/
permissions layer:

  MCP Call → Permissions → ENFORCEMENT → Tool Execution → Receipt
                              |
                    ┌─────────┴──────────┐
                    |                      |
              validator.py          boundary_checker.py
              drift_detector.py     policy_engine.py
              receipts.py
"""
