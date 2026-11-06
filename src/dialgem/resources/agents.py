"""Agents and their tools, knowledge and MCP servers.

NOTE: ``dialgem/aresources/agents.py`` is GENERATED from this file by ``scripts/unasync.py``.
Write each method as ``def`` returning ``self._client.<verb>(...)``; the generator adds ``async``/``await``.
"""

from __future__ import annotations

from typing import List, Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions, SyncAPIClient
from dialgem._errors import DialgemError
from dialgem._resource import Resource, pid
from dialgem.types.agent import Agent, AgentDeleteResponse
from dialgem.types.agent_resources import AgentFunction, KnowledgeDocument, MCPServer, MCPServerTestResult, MCPToolList
from dialgem.types.agent_version import AgentVersion, AgentVersionListResponse
from dialgem.types.params import (
    AgentCreateParams,
    AgentUpdateParams,
    FunctionCreateParams,
    FunctionReorderParams,
    FunctionUpdateParams,
    KnowledgeDocumentCreateParams,
    MCPServerCreateParams,
    MCPServerUpdateParams,
)


class Agents(Resource):
    """``dialgem.agents``: create and configure voice agents."""

    def __init__(self, client: SyncAPIClient) -> None:
        super().__init__(client)
        self.functions = AgentFunctions(client)
        self.knowledge = AgentKnowledge(client)
        self.mcp_servers = AgentMCPServers(client)
        self.versions = AgentVersions(client)

    def create(self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[AgentCreateParams]) -> Agent:
        return self._client.post("/v1/agents", body=body, cast_to=Agent, options=request_options)

    def retrieve(self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None) -> Agent:
        return self._client.get(f"/v1/agents/{pid(agent_id)}", cast_to=Agent, options=request_options)

    def list(self, *, request_options: Optional[RequestOptions] = None) -> List[Agent]:
        return self._client.get("/v1/agents", cast_to=List[Agent], options=request_options)

    def update(
        self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[AgentUpdateParams]
    ) -> Agent:
        return self._client.patch(f"/v1/agents/{pid(agent_id)}", body=body, cast_to=Agent, options=request_options)

    def delete(self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None) -> AgentDeleteResponse:
        return self._client.delete(f"/v1/agents/{pid(agent_id)}", cast_to=AgentDeleteResponse, options=request_options)


class AgentVersions(Resource):
    """``dialgem.agents.versions``: frozen, publishable snapshots of an agent."""

    def publish(
        self,
        agent_id: str,
        /,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AgentVersion:
        body = {k: v for k, v in (("title", title), ("description", description)) if v is not None}
        return self._client.post(
            f"/v1/agents/{pid(agent_id)}/versions", body=body, cast_to=AgentVersion, options=request_options
        )

    def list(
        self,
        agent_id: str,
        /,
        *,
        limit: Optional[int] = None,
        before_version: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> AgentVersionListResponse:
        """Newest first. ``has_more`` says whether older versions remain; pass the last
        ``version`` as ``before_version`` to continue."""
        return self._client.get(
            f"/v1/agents/{pid(agent_id)}/versions",
            query={"limit": limit, "before_version": before_version},
            cast_to=AgentVersionListResponse,
            options=request_options,
        )

    def retrieve(self, agent_id: str, version: int, /, *, request_options: Optional[RequestOptions] = None) -> AgentVersion:
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise DialgemError(
                f"Expected a published version number (a positive integer), got {version!r}. "
                "Version 0 is the draft: read it with agents.retrieve()."
            )
        return self._client.get(
            f"/v1/agents/{pid(agent_id)}/versions/{version}", cast_to=AgentVersion, options=request_options
        )


class AgentFunctions(Resource):
    """``dialgem.agents.functions``: tools the agent can call."""

    def list(self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None) -> List[AgentFunction]:
        return self._client.get(
            f"/v1/agents/{pid(agent_id)}/functions", cast_to=List[AgentFunction], options=request_options
        )

    def create(
        self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[FunctionCreateParams]
    ) -> AgentFunction:
        return self._client.post(
            f"/v1/agents/{pid(agent_id)}/functions", body=body, cast_to=AgentFunction, options=request_options
        )

    def update(
        self,
        agent_id: str,
        function_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[FunctionUpdateParams],
    ) -> AgentFunction:
        return self._client.patch(
            f"/v1/agents/{pid(agent_id)}/functions/{pid(function_id)}",
            body=body,
            cast_to=AgentFunction,
            options=request_options,
        )

    def delete(self, agent_id: str, function_id: str, /, *, request_options: Optional[RequestOptions] = None) -> None:
        return self._client.delete(
            f"/v1/agents/{pid(agent_id)}/functions/{pid(function_id)}", options=request_options
        )

    def reorder(
        self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[FunctionReorderParams]
    ) -> None:
        return self._client.post(
            f"/v1/agents/{pid(agent_id)}/functions/reorder", body=body, options=request_options
        )


class AgentKnowledge(Resource):
    """``dialgem.agents.knowledge``: documents the agent can retrieve from."""

    def list(self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None) -> List[KnowledgeDocument]:
        return self._client.get(
            f"/v1/agents/{pid(agent_id)}/knowledge", cast_to=List[KnowledgeDocument], options=request_options
        )

    def create(
        self,
        agent_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[KnowledgeDocumentCreateParams],
    ) -> KnowledgeDocument:
        return self._client.post(
            f"/v1/agents/{pid(agent_id)}/knowledge", body=body, cast_to=KnowledgeDocument, options=request_options
        )

    def delete(self, agent_id: str, source_id: str, /, *, request_options: Optional[RequestOptions] = None) -> None:
        return self._client.delete(
            f"/v1/agents/{pid(agent_id)}/knowledge/{pid(source_id)}", options=request_options
        )


class AgentMCPServers(Resource):
    """``dialgem.agents.mcp_servers``: external MCP tool servers."""

    def list(self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None) -> List[MCPServer]:
        return self._client.get(
            f"/v1/agents/{pid(agent_id)}/mcp-servers", cast_to=List[MCPServer], options=request_options
        )

    def create(
        self, agent_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[MCPServerCreateParams]
    ) -> MCPServer:
        return self._client.post(
            f"/v1/agents/{pid(agent_id)}/mcp-servers", body=body, cast_to=MCPServer, options=request_options
        )

    def update(
        self,
        agent_id: str,
        server_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[MCPServerUpdateParams],
    ) -> MCPServer:
        return self._client.patch(
            f"/v1/agents/{pid(agent_id)}/mcp-servers/{pid(server_id)}",
            body=body,
            cast_to=MCPServer,
            options=request_options,
        )

    def delete(self, agent_id: str, server_id: str, /, *, request_options: Optional[RequestOptions] = None) -> None:
        return self._client.delete(
            f"/v1/agents/{pid(agent_id)}/mcp-servers/{pid(server_id)}", options=request_options
        )

    def list_tools(
        self, agent_id: str, server_id: str, /, *, request_options: Optional[RequestOptions] = None
    ) -> MCPToolList:
        """What the server offers right now, with each tool's description and argument schema.

        Connects live like ``test`` but stores nothing. An unreachable server is not an error: ``tools`` is
        empty and ``error`` says why.
        """
        return self._client.get(
            f"/v1/agents/{pid(agent_id)}/mcp-servers/{pid(server_id)}/tools",
            cast_to=MCPToolList,
            options=request_options,
        )

    def test(
        self, agent_id: str, server_id: str, /, *, request_options: Optional[RequestOptions] = None
    ) -> MCPServerTestResult:
        return self._client.post(
            f"/v1/agents/{pid(agent_id)}/mcp-servers/{pid(server_id)}/test",
            cast_to=MCPServerTestResult,
            options=request_options,
        )
