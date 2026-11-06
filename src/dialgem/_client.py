"""The two clients: :class:`Dialgem` (sync) and :class:`AsyncDialgem` (asyncio)."""

from __future__ import annotations

import os
from typing import Any, Mapping, Optional, Tuple

import httpx

from dialgem import aresources
from dialgem import resources as sync
from dialgem._base_client import (
    BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    AsyncAPIClient,
    SyncAPIClient,
    _validate_retries,
    _validate_timeout,
)
from dialgem._errors import DialgemError
from dialgem._webhooks import Webhooks, webhooks


def _resolve(api_key: Optional[str], timeout: float, max_retries: int, base_url: Any) -> Tuple[str, float, int]:
    if base_url is not None:
        raise DialgemError("`base_url` is not an option: the SDK always talks to https://api.dialgem.com. Remove it.")
    key = api_key or (os.environ.get("DIALGEM_API_KEY") or "").strip()
    if not key:
        raise DialgemError(
            "Missing API key. Pass `api_key` to `Dialgem(api_key=...)` or set the DIALGEM_API_KEY environment variable."
        )
    return key, _validate_timeout(timeout), _validate_retries(max_retries)


class Dialgem:
    """Synchronous client.

        from dialgem import Dialgem

        dialgem = Dialgem()                       # reads DIALGEM_API_KEY
        agent = dialgem.agents.create(name="Front desk", system_prompt="You answer the phone.")

    For your **backend only**: an organization API key grants full access to your organization.
    To let a visitor talk to an agent from a web page, mint a token with ``web_calls.create`` and use
    ``@dialgem/client`` in the browser.

    Args:
        api_key: Organization API key (``zk_...``). Defaults to ``$DIALGEM_API_KEY``.
        timeout: Seconds per attempt. Default 60.
        max_retries: Retries for GET/PUT/PATCH/DELETE on 408/429/5xx and connection errors. Default 2.
            POST is never retried unless you pass ``request_options={"max_retries": n}``.
        default_headers: Sent with every request.
        http_client: Your own ``httpx.Client`` (proxy, mTLS, instrumentation). You close it.
    """

    BASE_URL = BASE_URL
    webhooks: Webhooks = webhooks

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.Client] = None,
        base_url: Any = None,
    ) -> None:
        key, timeout, max_retries = _resolve(api_key, timeout, max_retries, base_url)
        self._client = SyncAPIClient(
            api_key=key, timeout=timeout, max_retries=max_retries, default_headers=default_headers, http_client=http_client
        )
        c = self._client
        self.agents = sync.agents.Agents(c)
        self.calls = sync.calls.Calls(c)
        self.chats = sync.chats.Chats(c)
        self.flows = sync.flows.Flows(c)
        self.llms = sync.llms.LLMs(c)
        self.phone_numbers = sync.phone_numbers.PhoneNumbers(c)
        self.voices = sync.catalog.Voices(c)
        self.extraction_models = sync.catalog.ExtractionModels(c)
        self.flow_templates = sync.catalog.FlowTemplates(c)
        self.prompt_templates = sync.catalog.PromptTemplates(c)
        self.sessions = sync.account.Sessions(c)
        self.api_key = sync.account.ApiKey(c)
        self.contacts = sync.contacts.Contacts(c)
        self.contact_lists = sync.contacts.ContactLists(c)
        self.web_calls = sync.web_calls.WebCalls(c)
        self.simulations = sync.simulations.Simulations(c)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> Dialgem:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class AsyncDialgem:
    """Asyncio client. Same surface as :class:`Dialgem`; every method is awaited.

        async with AsyncDialgem() as dialgem:
            agent = await dialgem.agents.create(name="Front desk")
            async for call in dialgem.calls.list(limit=50):
                ...
    """

    BASE_URL = BASE_URL
    webhooks: Webhooks = webhooks

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Optional[Mapping[str, str]] = None,
        http_client: Optional[httpx.AsyncClient] = None,
        base_url: Any = None,
    ) -> None:
        key, timeout, max_retries = _resolve(api_key, timeout, max_retries, base_url)
        self._client = AsyncAPIClient(
            api_key=key, timeout=timeout, max_retries=max_retries, default_headers=default_headers, http_client=http_client
        )
        c = self._client
        self.agents = aresources.agents.AsyncAgents(c)
        self.calls = aresources.calls.AsyncCalls(c)
        self.chats = aresources.chats.AsyncChats(c)
        self.flows = aresources.flows.AsyncFlows(c)
        self.llms = aresources.llms.AsyncLLMs(c)
        self.phone_numbers = aresources.phone_numbers.AsyncPhoneNumbers(c)
        self.voices = aresources.catalog.AsyncVoices(c)
        self.extraction_models = aresources.catalog.AsyncExtractionModels(c)
        self.flow_templates = aresources.catalog.AsyncFlowTemplates(c)
        self.prompt_templates = aresources.catalog.AsyncPromptTemplates(c)
        self.sessions = aresources.account.AsyncSessions(c)
        self.api_key = aresources.account.AsyncApiKey(c)
        self.contacts = aresources.contacts.AsyncContacts(c)
        self.contact_lists = aresources.contacts.AsyncContactLists(c)
        self.web_calls = aresources.web_calls.AsyncWebCalls(c)
        self.simulations = aresources.simulations.AsyncSimulations(c)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> AsyncDialgem:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
