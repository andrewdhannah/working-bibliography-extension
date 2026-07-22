"""
Access Revocation — Suspension and Revocation of Extension Capabilities

Implements the action side of the extension lifecycle:

  ACTIVE → SUSPENDED (drift investigation, capabilities blocked)
  ACTIVE → REVOKED   (contract violation, permanent termination)
  SUSPENDED → ACTIVE (owner clears drift)
  SUSPENDED → REVOKED (owner terminates)

Key principle: Revocation is not deletion.
The extension remains a known governed object with identity, historical
receipts, drift findings, and lifecycle state preserved.
"""
