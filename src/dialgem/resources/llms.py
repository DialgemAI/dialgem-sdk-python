"""LLMs: a prompt and model you set up once and attach to agents."""

from __future__ import annotations

from typing import Any, Dict, Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._pagination import SyncPage
from dialgem._resource import Resource, pid
from dialgem.types.llm import LLM, LLMDeleteResponse
from dialgem.types.params import LLMCreateParams, LLMUpdateParams


class LLMs(Resource):
    """``dialgem.llms``: a prompt and model you set up once and attach to agents.

        llm = dialgem.llms.create(name="Booking", system_prompt=prompt, llm_model="gpt-4o-mini")
        dialgem.agents.create(name="Front desk", llm_id=llm.id)

    It holds ``system_prompt``, ``first_message``, ``llm_provider``, ``llm_model``, ``temperature``,
    ``max_tokens``, the fallback pair and ``default_dynamic_variables``. **Attaching copies it**:
    ``agents.create`` / ``agents.update`` with ``llm_id`` writes those values into the agent, and editing or
    deleting the saved LLM afterwards changes no agent, no published version and no call. Sending ``llm_id``
    together with any of those fields is refused.
    """

    def create(self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[LLMCreateParams]) -> LLM:
        """Save LLM settings. Anything left out takes the default a new agent gets. Not retried by default."""
        return self._client.post("/v1/llms", body=body, cast_to=LLM, options=request_options)

    def list(self, *, limit: int = 50, request_options: Optional[RequestOptions] = None) -> SyncPage[LLM]:
        """Saved LLMs, newest first. Iterate the result to walk every page."""
        query: Dict[str, Any] = {"limit": limit}
        return self._client.paginate(
            "/v1/llms",
            query=query,
            cast_to=LLM,
            items_key="llms",
            cursor_param="pagination_key",
            next_key="pagination_key",
            options=request_options,
        )

    def retrieve(self, llm_id: str, /, *, request_options: Optional[RequestOptions] = None) -> LLM:
        return self._client.get(f"/v1/llms/{pid(llm_id)}", cast_to=LLM, options=request_options)

    def update(
        self, llm_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[LLMUpdateParams]
    ) -> LLM:
        """Change the fields you send. Agents it was attached to are not changed."""
        return self._client.patch(f"/v1/llms/{pid(llm_id)}", body=body, cast_to=LLM, options=request_options)

    def delete(self, llm_id: str, /, *, request_options: Optional[RequestOptions] = None) -> LLMDeleteResponse:
        """Delete saved LLM settings. Agents they were attached to keep their copy."""
        return self._client.delete(f"/v1/llms/{pid(llm_id)}", cast_to=LLMDeleteResponse, options=request_options)
