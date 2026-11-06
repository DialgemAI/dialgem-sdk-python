"""The official Python SDK for the Dialgem voice AI API.

    from dialgem import Dialgem

    dialgem = Dialgem()  # reads DIALGEM_API_KEY
    agent = dialgem.agents.create(name="Front desk", system_prompt="You answer the phone.")

Server-side only. To let a visitor talk to an agent from a web page, create a call with
``dialgem.web_calls.create(...)`` and hand the token to ``@dialgem/client`` in the browser.
"""

from dialgem._base_client import BASE_URL, RequestOptions
from dialgem._client import AsyncDialgem, Dialgem
from dialgem._errors import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    DialgemError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
    WebhookVerificationError,
)
from dialgem._pagination import AsyncPage, AsyncPaginator, SyncPage
from dialgem._version import VERSION as __version__
from dialgem._webhooks import (
    DEFAULT_SIGNATURE_TOLERANCE_MS,
    WEBHOOK_DELIVERY_HEADER,
    WEBHOOK_EVENT_HEADER,
    WEBHOOK_PREVIOUS_SIGNATURE_HEADER,
    WEBHOOK_SIGNATURE_HEADER,
    Webhooks,
    webhooks,
)

__all__ = [
    "APIConnectionError",
    "APIError",
    "APITimeoutError",
    "AsyncDialgem",
    "AsyncPage",
    "AsyncPaginator",
    "AuthenticationError",
    "BASE_URL",
    "BadRequestError",
    "ConflictError",
    "DEFAULT_SIGNATURE_TOLERANCE_MS",
    "Dialgem",
    "DialgemError",
    "InternalServerError",
    "NotFoundError",
    "PermissionDeniedError",
    "RateLimitError",
    "RequestOptions",
    "SyncPage",
    "UnprocessableEntityError",
    "WEBHOOK_DELIVERY_HEADER",
    "WEBHOOK_EVENT_HEADER",
    "WEBHOOK_PREVIOUS_SIGNATURE_HEADER",
    "WEBHOOK_SIGNATURE_HEADER",
    "WebhookVerificationError",
    "Webhooks",
    "__version__",
    "webhooks",
]
