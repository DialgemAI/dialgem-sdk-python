"""Exceptions. Everything the SDK raises derives from :class:`DialgemError`."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional


class DialgemError(Exception):
    """Base class for every error this SDK raises."""


class APIError(DialgemError):
    """The API answered with a non-2xx status.

    ``err_code`` and ``request_id`` come from the API's error envelope
    (``{"err_code", "err_msg", "request_id"}``). Quote ``request_id`` when you contact support.
    """

    def __init__(self, status: int, body: Any, message: str, headers: Mapping[str, str]) -> None:
        super().__init__(message)
        self.status = status
        self.body = body
        self.headers = headers
        envelope = body if _is_envelope(body) else None
        self.err_code: Optional[str] = envelope["err_code"] if envelope else None
        self.request_id: Optional[str] = (
            (envelope.get("request_id") if envelope else None) or headers.get("x-request-id") or None
        )
        issues = envelope.get("issues") if envelope else None
        #: Validation issues, e.g. from a conversation flow the server rejected.
        self.issues: List[Dict[str, Any]] = list(issues) if isinstance(issues, list) else []

    @classmethod
    def from_response(cls, status: int, body: Any, reason: str, headers: Mapping[str, str]) -> APIError:
        envelope = body if _is_envelope(body) else None
        detail = ""
        if envelope and envelope.get("err_msg"):
            detail = str(envelope["err_msg"])
        elif isinstance(body, str) and body.strip():
            detail = body.strip()[:500]
        message = f"{status} {detail}" if detail else f"{status} {reason or 'status code (no body)'}"
        return _class_for(status)(status, body, message, headers)


class BadRequestError(APIError):
    """400."""


class AuthenticationError(APIError):
    """401: missing, invalid or revoked API key."""


class PermissionDeniedError(APIError):
    """403."""


class NotFoundError(APIError):
    """404."""


class ConflictError(APIError):
    """409: a real conflict (for example a phone number already registered). Never retried."""


class UnprocessableEntityError(APIError):
    """422: the request was well-formed but failed validation. See ``issues``."""


class RateLimitError(APIError):
    """429."""


class InternalServerError(APIError):
    """5xx."""


class APIConnectionError(DialgemError):
    """The request never produced a response (DNS, TLS, reset, ...)."""


class APITimeoutError(APIConnectionError):
    """The request timed out."""


class WebhookVerificationError(DialgemError):
    """A webhook body failed signature verification or was not what it claimed to be."""


def _is_envelope(body: Any) -> bool:
    return isinstance(body, dict) and isinstance(body.get("err_code"), str)


def _class_for(status: int) -> type:
    return {
        400: BadRequestError,
        401: AuthenticationError,
        403: PermissionDeniedError,
        404: NotFoundError,
        409: ConflictError,
        422: UnprocessableEntityError,
        429: RateLimitError,
    }.get(status, InternalServerError if status >= 500 else APIError)
