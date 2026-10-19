"""Agent base class and the context object the orchestrator hands to agents.

Tool access is explicit and per-agent: an agent only receives a context
carrying the capabilities listed in its ``tools`` declaration. The planner
gets no source access at all; only the researcher can query connectors;
only the critic can look up full source text for verification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from ..blackboard import Blackboard
from ..config import OrchestratorConfig
from ..connectors import ConnectorRegistry
from ..trace import RunTrace


@dataclass
class AgentContext:
    blackboard: Blackboard
    config: OrchestratorConfig
    trace: RunTrace
    state: str
    registry: Optional[ConnectorRegistry] = None
    spend: Callable[[int], None] = field(default=lambda n: None)

    def require_registry(self) -> ConnectorRegistry:
        if self.registry is None:
            raise PermissionError("this agent has no source-connector access")
        return self.registry


class Agent:
    """One specialized step of the workflow. Subclasses implement ``run``."""

    name: str = "agent"
    tools: tuple[str, ...] = ()

    def run(self, ctx: AgentContext) -> None:  # pragma: no cover - abstract
        raise NotImplementedError
