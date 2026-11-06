"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dialgem.types._base import DialgemModel, Number
from dialgem.types._shared import FunctionKind, KeyValuePair


class AgentFunction(DialgemModel):
    """A tool the agent can call, as returned by `/v1/agents/{id}/functions`."""

    id: str
    agent_id: str
    name: str
    description: str
    #: JSON Schema for the arguments the LLM supplies.
    parameters: Dict[str, Any]
    url: str
    method: str
    timeout_ms: Number
    headers: List[KeyValuePair]
    query_params: List[KeyValuePair]
    speak_during_execution: Optional[str]
    speak_after_execution: bool
    #: `false` (the default for new functions): the request body is
    #: `{ name, call, args }`. `true`: the body is the arguments object alone.
    args_at_root: bool
    sort_order: Number
    kind: FunctionKind
    #: Kind-specific settings (e.g. Cal.com credentials for the `*_cal` kinds).
    config: Dict[str, Any]
    #: Maps dynamic-variable names to JSON paths in the function's response.
    response_variables: Dict[str, str]
    created_at: Optional[str]


class KnowledgeDocument(DialgemModel):
    """A text document in the agent's knowledge base, summarised across its chunks."""

    source_id: str
    filename: str
    chunk_count: Number
    #: From `list()`: false if **any** chunk failed to embed (those chunks are not
    #: retrievable). From `create()`: true if **at least one** chunk embedded, so a
    #: partial failure still reads true there; re-check with `list()`.
    embedded: bool
    #: Present on `list()`; absent from the `create()` response.
    created_at: Optional[str] = None


class MCPServer(DialgemModel):
    """A remote MCP tool server attached to an agent. The `auth_token` is write-only."""

    id: str
    agent_id: str
    name: str
    url: str
    has_auth_token: bool
    enabled: bool
    timeout_ms: Number
    headers: List[KeyValuePair]
    query_params: List[KeyValuePair]
    last_status: Optional[MCPServerTestResult]
    created_at: Optional[str]


class MCPTool(DialgemModel):
    """One tool an MCP server offers."""

    name: str
    description: str = ""
    #: JSON Schema for the tool's arguments.
    input_schema: Dict[str, Any] = {}


class MCPToolList(DialgemModel):
    """What ``mcp_servers.list_tools`` returns. When the server is unreachable ``tools`` is empty and ``error`` says why."""

    tools: List[MCPTool]
    error: Optional[str] = None


class MCPServerTestResult(DialgemModel):
    ok: bool
    #: Tool names the server advertised.
    tools: List[str]
    error: Optional[str]
    #: ISO 8601.
    at: str
