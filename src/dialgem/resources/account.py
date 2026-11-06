"""Account-level reads: calls in progress right now, and what this API key is."""

from __future__ import annotations

from typing import Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._resource import Resource, pid
from dialgem.types.api_key import ApiKeyInfo
from dialgem.types.params import SessionSayParams, SessionUpdateParams
from dialgem.types.session import (
    AgentSessionList,
    AgentSessionReleaseResult,
    AgentSessionSayResult,
    AgentSessionUpdateResult,
)


class Sessions(Resource):
    """``dialgem.sessions``: calls in progress right now."""

    def list(self, *, request_options: Optional[RequestOptions] = None) -> AgentSessionList:
        return self._client.get("/v1/agent/sessions", cast_to=AgentSessionList, options=request_options)

    def update(
        self,
        session_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[SessionUpdateParams],
    ) -> AgentSessionUpdateResult:
        """Change a live call's prompt and/or variables. It applies from the agent's **next turn**.

        ``session_id`` is a session's ``session_id`` from ``list``, or the call's own ``call_id``. Only this
        call changes: the agent, its published versions and other calls are untouched, and the change is
        gone when the call ends. A turn already being spoken finishes as it was. ``dynamic_variables`` are
        merged over the call's variables; ``system_prompt`` replaces the prompt for the rest of the call.

        The call may be on any service instance. ``NotFoundError`` if it is not live (or is another
        organization's), ``ConflictError`` with ``err_code`` ``session_ended`` once it is over,
        ``UnprocessableEntityError`` with ``err_code`` ``flow_agent_prompt`` for a flow agent's prompt (its
        variables can still change). This is a PATCH and is not retried by default.
        """
        return self._client.patch(
            f"/v1/agent/sessions/{pid(session_id)}", body=body, cast_to=AgentSessionUpdateResult, options=request_options
        )

    def say(
        self,
        session_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[SessionSayParams],
    ) -> AgentSessionSayResult:
        """Make the agent say ``text`` on a live call, in its own voice. Answers at once; the line plays
        behind what the agent is saying, or now with ``interrupt=True``. The agent's conversation records it
        as something it said.

        Off unless the deployment enables live control: ``PermissionDeniedError`` with ``err_code``
        ``live_control_disabled``. ``ConflictError`` ``human_has_call`` while a human has taken the call.
        Owners, admins and API keys only. This is a POST and is not retried by default.
        """
        return self._client.post(
            f"/v1/agent/sessions/{pid(session_id)}/say", body=body, cast_to=AgentSessionSayResult, options=request_options
        )

    def release(
        self, session_id: str, /, *, request_options: Optional[RequestOptions] = None
    ) -> AgentSessionReleaseResult:
        """Hand a taken-over call back to the agent, for when the socket that took it is gone. The agent is
        told a human had the call and that it did not hear what was said. Same availability and limits as
        ``say``. Listening in and taking over run over a WebSocket (``/v1/agent/sessions/{id}/live``), which
        this SDK does not wrap."""
        return self._client.post(
            f"/v1/agent/sessions/{pid(session_id)}/release", cast_to=AgentSessionReleaseResult, options=request_options
        )


class ApiKey(Resource):
    """``dialgem.api_key``."""

    def retrieve(self, *, request_options: Optional[RequestOptions] = None) -> ApiKeyInfo:
        """Who this key is: your organization and the key's name, prefix, scopes, allowed addresses
        and expiry. Answers for any valid key whatever its scopes. Never returns the secret."""
        return self._client.get("/v1/api-key-info", cast_to=ApiKeyInfo, options=request_options)
