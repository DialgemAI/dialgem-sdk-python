"""Calls: list, fetch, place and register."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, Optional, Union

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._pagination import SyncPage
from dialgem._resource import Resource, pid
from dialgem.types.call import (
    Call,
    CallDeleteResponse,
    CallRegisterResponse,
    CallStopResponse,
    PhoneCallCreateResponse,
)
from dialgem.types.params import CallCreatePhoneCallParams, CallRegisterParams

_Many = Union[str, List[str]]


class Calls(Resource):
    """``dialgem.calls``."""

    def list(
        self,
        *,
        agent_id: Optional[_Many] = None,
        status: Optional[_Many] = None,
        direction: Optional[Literal["inbound", "outbound"]] = None,
        call_type: Optional[Literal["phone_call", "web_call"]] = None,
        disconnection_reason: Optional[_Many] = None,
        from_number: Optional[str] = None,
        to_number: Optional[str] = None,
        user_sentiment: Optional[Literal["Positive", "Neutral", "Negative"]] = None,
        call_successful: Optional[bool] = None,
        start_after: Optional[int] = None,
        start_before: Optional[int] = None,
        metadata: Optional[Mapping[str, Union[str, int, float, bool]]] = None,
        search: Optional[str] = None,
        sort_order: Optional[Literal["asc", "desc"]] = None,
        limit: int = 10,
        request_options: Optional[RequestOptions] = None,
    ) -> SyncPage[Call]:
        """List calls, newest first. Iterate the result to walk every page.

        ``start_after``/``start_before`` are epoch milliseconds. ``metadata`` matches the metadata you
        attached when the call was created.
        """
        query: Dict[str, Any] = {
            "agent_id": agent_id,
            "status": status,
            "direction": direction,
            "call_type": call_type,
            "disconnection_reason": disconnection_reason,
            "from_number": from_number,
            "to_number": to_number,
            "user_sentiment": user_sentiment,
            "call_successful": call_successful,
            "start_after": start_after,
            "start_before": start_before,
            "search": search,
            "sort_order": sort_order,
            "limit": limit,
        }
        for key, value in (metadata or {}).items():
            query[f"metadata.{key}"] = value
        return self._client.paginate(
            "/v1/calls",
            query=query,
            cast_to=Call,
            items_key="calls",
            cursor_param="pagination_key",
            next_key="pagination_key",
            options=request_options,
        )

    def retrieve(self, call_id: str, /, *, request_options: Optional[RequestOptions] = None) -> Call:
        return self._client.get(f"/v1/calls/{pid(call_id)}", cast_to=Call, options=request_options)

    def update(
        self, call_id: str, /, *, metadata: Dict[str, Any], request_options: Optional[RequestOptions] = None
    ) -> Call:
        """Replace the call's ``metadata``."""
        return self._client.patch(
            f"/v1/calls/{pid(call_id)}", body={"metadata": metadata}, cast_to=Call, options=request_options
        )

    def delete(self, call_id: str, /, *, request_options: Optional[RequestOptions] = None) -> CallDeleteResponse:
        return self._client.delete(f"/v1/calls/{pid(call_id)}", cast_to=CallDeleteResponse, options=request_options)

    def rerun_analysis(self, call_id: str, /, *, request_options: Optional[RequestOptions] = None) -> Call:
        """Run a finished call's post-call analysis again with the agent's *current* analysis settings.

        Use it after changing the fields or the model and wanting an older call read the new way.
        It replaces ``analysis``; it does not bill the call again and does not send ``call_analyzed``
        again, so read the result from the return value or from ``retrieve``. The model call can take
        a while. Raises ``ConflictError`` (``call_in_progress``, ``no_transcript``, ``agent_deleted``).
        Not retried by default.
        """
        return self._client.post(f"/v1/calls/{pid(call_id)}/rerun-analysis", cast_to=Call, options=request_options)

    def stop(self, call_id: str, /, *, request_options: Optional[RequestOptions] = None) -> CallStopResponse:
        """Hang up a call that is in progress."""
        return self._client.post(f"/v1/calls/{pid(call_id)}/stop", cast_to=CallStopResponse, options=request_options)

    def create_phone_call(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[CallCreatePhoneCallParams]
    ) -> PhoneCallCreateResponse:
        """Place an outbound call. ``from_`` (note the underscore) must be a number on your organization.

        This is a POST and is **not retried** on a failure: a retry after an ambiguous 502 could ring the
        person twice. Pass ``request_options={"max_retries": 2}`` only if you accept that.
        """
        return self._client.post(
            "/v1/calls/outbound", body=body, cast_to=PhoneCallCreateResponse, options=request_options
        )

    def register(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[CallRegisterParams]
    ) -> CallRegisterResponse:
        """Register a call you carry on your own Twilio account so Dialgem can take the media stream."""
        return self._client.post(
            "/v1/calls/register", body=body, cast_to=CallRegisterResponse, options=request_options
        )
