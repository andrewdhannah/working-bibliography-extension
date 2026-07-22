"""
Capability Projection Service — Consumer-Agnostic Extension Awareness

Produces the canonical capability projection: a governed artifact describing
all registered extensions, their lifecycle state, and their declared capabilities.

This module implements the projection logic that belongs on Librarian core.
It is designed to be:
  1. Wired into Librarian's MCPController.swift as a new MCP tool
  2. Tested independently with fixtures
  3. Consumer-agnostic (any consumer can read the projection)

Per ADR-WB-009: Librarian is the sole authority for capability projection.
Extensions declare capabilities. Consumers consume projections.
Neither may define availability independently.
"""

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
