"""
Extension Handshake — Identity, Contract Validation, and Lifecycle Management

Implements the 6-state lifecycle and handshake protocol defined in
WB-LIBRARIAN-CONTRACT-v1 and EXTENSION-HANDSHAKE-CONTRACT.md.

The handshake transitions an extension from unknown service to
trusted governed participant:
  REGISTERED → CONTRACT_VERIFIED → OWNER_APPROVED → ACTIVE
                                                    → SUSPENDED → REVOKED
"""
