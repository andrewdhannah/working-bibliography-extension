"""
Extension Validation — Reusable Compliance Test Suite

Tests whether an extension conforms to the Librarian extension contract
model. Validation is designed to be run BEFORE trust is granted.

Validation domains:
  1. Identity — extension ID format, contract reference, version
  2. Contract — capabilities declared, forbidden ops defined, boundaries present
  3. Capability — tool declarations match, risk levels valid, permissions aligned
  4. Lifecycle — state transitions valid, guard conditions work
  5. Permission — R0/R1 integrity, scope alignment

Principle: An extension should be testable before it is trusted.
"""
