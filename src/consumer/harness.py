"""
Consumer Harness — Deterministic Consumer Behaviors

Models how any compliant consumer should behave when given a capability
projection. The harness validates:

  1. Capabilities are only used when available (ACTIVE state)
  2. Unavailable capabilities are not invented or assumed
  3. Stale projections trigger refresh before execution
  4. Projection unavailability results in degraded mode (not failure)
  5. Multiple extensions keep capabilities isolated

The harness is NOT an AI agent. It is a conformance test consumer
that validates the consumer contract is implementable.
"""

from dataclasses import dataclass, field
from typing import Optional, Any
from .context import ConsumerContext, build_context_from_projection


class ConsumerAction:
    """Action taken by the consumer harness."""
    PASS = "pass"
    REJECT = "reject"
    REFRESH = "refresh"
    DEGRADE = "degrade"
    EXPLAIN = "explain"


@dataclass
@dataclass
class ConsumerDecision:
    """Result of a consumer reasoning step."""
    action: str = ""
    tool_name: str = ""
    reason: str = ""
    extension_id: str = ""
    refreshed: bool = False

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "tool_name": self.tool_name,
            "reason": self.reason,
            "extension_id": self.extension_id,
            "refreshed": self.refreshed
        }


class ConsumerHarness:
    """A deterministic consumer that tests the consumer contract.
    
    The harness is not an AI agent. It is a conformance test that
    validates any consumer would behave correctly given a projection.
    
    The harness follows these rules:
      - AR-001: Only use capabilities present in current projection
      - AR-002: Do not invent tools not in the projection
      - AR-003: Do not claim access to suspended/revoked extensions
      - AR-004: Refresh projection when stale or invalid
      - AR-005: Verify R1+ capabilities before execution
      - AR-006: Historical access does not imply current authorization
    """

    def __init__(self):
        self.context: Optional[ConsumerContext] = None
        self.projection_source = None  # Function to call for refresh
        self._refresh_count = 0
        self._decisions: list[ConsumerDecision] = []

    def load_projection(self, projection_data: dict) -> ConsumerContext:
        """Load a capability projection and build consumer context.
        
        Args:
            projection_data: The dict from librarian_capability_projection()
        
        Returns:
            ConsumerContext with available capabilities
        """
        self.context = build_context_from_projection(projection_data)
        return self.context

    def set_refresh_source(self, refresh_fn):
        """Set the function to call for projection refresh.
        
        Args:
            refresh_fn: A callable that returns new projection data
        """
        self.projection_source = refresh_fn

    def consider_tool(self, tool_name: str, arguments: dict = None) -> ConsumerDecision:
        """Consider whether a tool can be used.
        
        This is the core reasoning method. It models how any consumer
        should evaluate a capability before use.
        
        Returns:
            ConsumerDecision with action and reason
        """
        decision = ConsumerDecision(tool_name=tool_name)

        if not self.context:
            decision.action = ConsumerAction.DEGRADE
            decision.reason = "No capability projection loaded"
            self._decisions.append(decision)
            return decision

        # Check if tool is in context at all
        if not self.context.has_tool(tool_name):
            # Check if any known extension could have provided this tool but is unavailable
            for ext_id, ext_info in self.context.extensions.items():
                if not ext_info.available:
                    # Known extension, not available — informative message
                    decision.action = ConsumerAction.EXPLAIN
                    decision.reason = f"Extension '{ext_id}' is {ext_info.lifecycle}. {ext_info.explanation()}"
                    decision.extension_id = ext_id
                    self._decisions.append(decision)
                    return decision

            # Unknown tool from no known source
            decision.action = ConsumerAction.REJECT
            decision.reason = f"Tool '{tool_name}' not in capability projection. Consumer must not invent undeclared capabilities."
            decision.extension_id = "unknown"
            self._decisions.append(decision)
            return decision

        # Find which extension and capability this tool belongs to
        ext_id = ""
        cap_name = ""
        risk = "R0"
        for cap_ref in self.context.capabilities.values():
            if tool_name in cap_ref.tools:
                ext_id = cap_ref.extension_id
                cap_name = cap_ref.capability_name
                risk = cap_ref.risk
                break

        decision.extension_id = ext_id

        # Check if capability is available
        if not self.context.is_tool_available(tool_name):
            ext_info = self.context.get_extension_info(ext_id)
            reason = self.context.get_unavailable_reason(tool_name)

            if ext_info and ext_info.lifecycle == "suspended":
                decision.action = ConsumerAction.EXPLAIN
                decision.reason = f"Extension '{ext_id}' is suspended. {reason}"
            elif ext_info and ext_info.lifecycle == "revoked":
                decision.action = ConsumerAction.EXPLAIN
                decision.reason = f"Extension '{ext_id}' has been revoked. {reason}"
            else:
                decision.action = ConsumerAction.REJECT
                decision.reason = f"Tool '{tool_name}' is not currently available: {reason}"

            self._decisions.append(decision)
            return decision

        # Check stale context — attempt refresh before R1+ execution
        if risk == "R1" and self.projection_source:
            fresh_data = self.projection_source()
            fresh_ctx = build_context_from_projection(fresh_data)

            if fresh_ctx.projection_id != self.context.projection_id:
                self.context = fresh_ctx
                self._refresh_count += 1
                decision.refreshed = True

                # Re-check after refresh
                if not self.context.is_tool_available(tool_name):
                    decision.action = ConsumerAction.REJECT
                    decision.reason = f"After refresh, tool '{tool_name}' is no longer available."
                    self._decisions.append(decision)
                    return decision

        # All checks pass
        decision.action = ConsumerAction.PASS
        decision.reason = f"Capability '{cap_name}' available via '{ext_id}'"
        self._decisions.append(decision)
        return decision

    def handle_projection_unavailable(self) -> ConsumerDecision:
        """Handle the case where no projection is available.
        
        The consumer must not assume capabilities exist. It enters
        degraded mode: proceeds without extension capabilities.
        """
        decision = ConsumerDecision(action=ConsumerAction.DEGRADE)
        decision.reason = "Capability projection unavailable. Continuing without governed extensions."
        self._decisions.append(decision)
        return decision

    def check_invented_tool(self, tool_name: str) -> ConsumerDecision:
        """Check if a tool name is invented (not in projection).
        
        Returns:
            REJECT if the tool is not in the known tool set
        """
        decision = ConsumerDecision(tool_name=tool_name)

        if self.context and not self.context.has_tool(tool_name):
            decision.action = ConsumerAction.REJECT
            decision.reason = f"Consumer must not use '{tool_name}' — not in capability projection"
        else:
            decision.action = ConsumerAction.PASS
            decision.reason = f"'{tool_name}' is in the projection"

        self._decisions.append(decision)
        return decision

    def get_history(self) -> list[dict]:
        """Get the history of all consumer decisions."""
        return [d.to_dict() for d in self._decisions]

    @property
    def refresh_count(self) -> int:
        return self._refresh_count
