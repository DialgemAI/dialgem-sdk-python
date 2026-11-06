"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dialgem.types._base import DialgemModel, Number
from dialgem.types.agent_resources import AgentFunction


class AgentVersionSummary(DialgemModel):
    """A published agent version: a frozen copy of the agent's configuration, its
    functions and its MCP servers.
    
    The editable agent is the **draft**, version `0`, and is what a call runs
    unless something pins a version. Publishing never changes the draft, and a
    published version never changes at all — editing a function's URL afterwards
    does not move the copy inside a version that already shipped.
    
    Pin one on a phone number (`inbound_agent_version` / `outbound_agent_version`),
    on an outbound call, or on a registered call. The version a call ran is
    reported as `agent_version` on its call record and in every webhook."""

    id: str
    agent_id: str
    #: 1 for the first publish, then upwards. The draft is 0 and is not listed here.
    version: Number
    #: The agent's name at publish time.
    name: str
    #: Your label for the release, if you gave one.
    title: Optional[str]
    description: Optional[str]
    #: ISO 8601, no timezone suffix (UTC).
    published_at: Optional[str]
    #: Whoever published it, as the API identity that made the call.
    published_by: Optional[str]
    function_count: Number
    mcp_server_count: Number


class AgentVersion(AgentVersionSummary):
    """A version with its snapshot, returned by `publish` and `retrieve`."""

    #: The frozen configuration. Same fields as {@link Agent}, minus the ones that
    #: belong to the agent rather than to a snapshot (`id`, `created_at`,
    #: `call_count`). `webhook_signing_secret` is never included; read it from the
    #: agent itself.
    config: AgentVersionConfig
    functions: List[AgentFunction]
    #: `auth_token` is stripped; `has_auth_token` says whether one is set.
    mcp_servers: List[AgentVersionMCPServer]


AgentVersionConfig = Any


AgentVersionMCPServer = Any


class AgentVersionListResponse(DialgemModel):
    #: Newest first.
    versions: List[AgentVersionSummary]
    #: Whether older versions remain below the last one returned.
    has_more: bool
