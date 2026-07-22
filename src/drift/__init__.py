"""
Drift Detection — Observation and Classification Layer

Detects differences between the approved extension baseline and observed
runtime state. Classifies findings as PASS, OBSERVATION, or REVOKE.

This layer is separate from enforcement:
  Enforcement: Active blocks on every operation (see src/enforcement/)
  Drift Detection: Periodic comparison against approved baseline (this module)

Drift domains:
  1. Identity drift — extension_id, version changes
  2. Capability drift — tools added or removed
  3. Permission drift — risk level escalation
  4. Contract version drift — contract version changes
"""
