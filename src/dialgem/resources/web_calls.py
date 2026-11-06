"""Browser calls: mint a one-use token for a visitor to talk to an agent from a web page."""

from __future__ import annotations

from typing import Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._resource import Resource
from dialgem.types.params import WebCallCreateParams, WebCallSettingsUpdateParams
from dialgem.types.web_call import WebCall, WebCallSettings


class WebCalls(Resource):
    """``dialgem.web_calls``.

    Your **backend** calls :meth:`create` with its API key and hands the returned ``access_token`` to the
    page, which connects with ``@dialgem/client`` using that token alone. The key never reaches the browser.
    Allow the page's origin with :meth:`update_settings` first.
    """

    def create(self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[WebCallCreateParams]) -> WebCall:
        """Create a call for one visitor and get its 60-second, single-use access token.

        ``metadata`` and ``dialgem_llm_dynamic_variables`` are fixed here and cannot be changed by the page.
        409 ``web_origins_not_configured`` until an origin is allowed; 402 if the organization cannot pay for calls;
        429 when too many calls are created in a minute.
        """
        return self._client.post("/v1/calls/web", body=body, cast_to=WebCall, options=request_options)

    def retrieve_settings(self, *, request_options: Optional[RequestOptions] = None) -> WebCallSettings:
        """The origins browser calls may start from, and the limits that apply."""
        return self._client.get("/v1/web-calls/settings", cast_to=WebCallSettings, options=request_options)

    def update_settings(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[WebCallSettingsUpdateParams]
    ) -> WebCallSettings:
        """Replace the allowed origins. Each is ``scheme://host[:port]``; ``https://*.example.com`` allows
        any subdomain (not the bare domain) and ``*`` allows any website. Tokens already issued keep the
        list they were issued with."""
        return self._client.put("/v1/web-calls/settings", body=body, cast_to=WebCallSettings, options=request_options)
