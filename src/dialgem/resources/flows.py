"""Flows: conversation flows you save once and attach to agents."""

from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._pagination import SyncPage
from dialgem._resource import Resource, pid
from dialgem.types.flow import Flow, FlowDeleteResponse
from dialgem.types.params import FlowCreateParams


class Flows(Resource):
    """``dialgem.flows``: conversation flows you save once and attach to agents.

        flow = dialgem.flows.create(name="Intake", flow_config=flow_config)
        dialgem.agents.create(name="Front desk", agent_type="flow", flow_id=flow.id)

    A flow is checked the way an agent's ``flow_config`` is, so a saved flow is one that would have saved on
    an agent. **Attaching copies it**: ``agents.create`` / ``agents.update`` with ``flow_id`` takes a
    snapshot, and editing or deleting the flow afterwards changes no agent, no published version and no call.
    """

    def create(self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[FlowCreateParams]) -> Flow:
        """Validate and save a flow.

        Raises ``UnprocessableEntityError`` (``err_code`` ``flow_invalid``) listing every problem. Not
        retried by default.
        """
        return self._client.post("/v1/flows", body=body, cast_to=Flow, options=request_options)

    def list(self, *, limit: int = 50, request_options: Optional[RequestOptions] = None) -> SyncPage[Flow]:
        """Flows, newest first. Iterate the result to walk every page. Entries leave out ``flow_config``."""
        query: Dict[str, Any] = {"limit": limit}
        return self._client.paginate(
            "/v1/flows",
            query=query,
            cast_to=Flow,
            items_key="flows",
            cursor_param="pagination_key",
            next_key="pagination_key",
            options=request_options,
        )

    def retrieve(self, flow_id: str, /, *, request_options: Optional[RequestOptions] = None) -> Flow:
        """One flow with its ``flow_config``."""
        return self._client.get(f"/v1/flows/{pid(flow_id)}", cast_to=Flow, options=request_options)

    def update(
        self,
        flow_id: str,
        /,
        *,
        name: Optional[str] = None,
        flow_config: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> Flow:
        """Rename a flow and/or replace its ``flow_config`` (checked again). Attached agents are not changed."""
        body: Dict[str, Any] = {
            k: v for k, v in (("name", name), ("flow_config", flow_config), ("language", language)) if v is not None
        }
        return self._client.patch(f"/v1/flows/{pid(flow_id)}", body=body, cast_to=Flow, options=request_options)

    def delete(self, flow_id: str, /, *, request_options: Optional[RequestOptions] = None) -> FlowDeleteResponse:
        """Delete a saved flow. Agents it was attached to keep their copy."""
        return self._client.delete(f"/v1/flows/{pid(flow_id)}", cast_to=FlowDeleteResponse, options=request_options)
