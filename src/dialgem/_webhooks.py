"""Webhook signature verification.

Dialgem signs every delivery. The header is ``x-dialgem-signature: v=<epoch ms>,d=<hex>`` where
``d`` is ``HMAC-SHA256(secret, raw_body + timestamp)``. Verify against the **raw request body**
exactly as received: a body parsed and re-serialized (different whitespace, escaped non-ASCII)
no longer matches and is rejected.

    from dialgem import webhooks

    event = webhooks.construct_event(request.body, request.headers["x-dialgem-signature"], secret)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
from typing import Any, Dict, Optional, Sequence, Type, Union

from dialgem._base_client import cast_response
from dialgem._errors import DialgemError, WebhookVerificationError
from dialgem.types._base import DialgemModel
from dialgem.types.webhook import (
    CallAnalyzedEvent,
    CallEndedEvent,
    CallStartedEvent,
    ChatAnalyzedEvent,
    ChatEndedEvent,
    ChatStartedEvent,
    FunctionCallRequest,
    TranscriptUpdatedEvent,
    TransferBridgedEvent,
    TransferCancelledEvent,
    TransferEndedEvent,
    TransferStartedEvent,
)

WEBHOOK_SIGNATURE_HEADER = "x-dialgem-signature"
WEBHOOK_PREVIOUS_SIGNATURE_HEADER = "x-dialgem-signature-previous"
WEBHOOK_EVENT_HEADER = "x-dialgem-event"
WEBHOOK_DELIVERY_HEADER = "x-dialgem-delivery"
DEFAULT_SIGNATURE_TOLERANCE_MS = 5 * 60 * 1000

_SIGNATURE_RE = re.compile(r"^v=(\d{10,16}),d=([0-9a-f]{64})$")

_EVENT_MODELS: Dict[str, Type[DialgemModel]] = {
    "call_started": CallStartedEvent,
    "call_ended": CallEndedEvent,
    "call_analyzed": CallAnalyzedEvent,
    "transcript_updated": TranscriptUpdatedEvent,
    "transfer_started": TransferStartedEvent,
    "transfer_bridged": TransferBridgedEvent,
    "transfer_cancelled": TransferCancelledEvent,
    "transfer_ended": TransferEndedEvent,
    "chat_started": ChatStartedEvent,
    "chat_ended": ChatEndedEvent,
    "chat_analyzed": ChatAnalyzedEvent,
}

Payload = Union[str, bytes, bytearray, memoryview]
SignatureHeader = Union[str, Sequence[str], None]


class Webhooks:
    """Verify and parse Dialgem webhook deliveries. Also available as the module-level ``webhooks``."""

    def verify(
        self,
        payload: Payload,
        signature: SignatureHeader,
        secret: str,
        *,
        tolerance_ms: int = DEFAULT_SIGNATURE_TOLERANCE_MS,
        now_ms: Optional[float] = None,
    ) -> bool:
        """``True`` if ``signature`` is valid for ``payload`` and recent enough.

        Never raises for a bad signature; raises :class:`DialgemError` only for an empty ``secret``.
        """
        if not secret:
            raise DialgemError(
                "Webhook secret is empty. Set the agent's `webhook_signing_secret` and pass the same value here."
            )
        match = _SIGNATURE_RE.match((_first(signature) or "").strip().lower())
        if not match:
            return False
        timestamp, received = match.group(1), match.group(2)
        now = time.time() * 1000 if now_ms is None else now_ms
        if abs(now - int(timestamp)) > tolerance_ms:
            return False
        expected = hmac.new(
            secret.encode("utf-8"), _to_bytes(payload) + timestamp.encode("ascii"), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, received)

    def construct_event(
        self,
        payload: Payload,
        signature: SignatureHeader,
        secret: str,
        *,
        tolerance_ms: int = DEFAULT_SIGNATURE_TOLERANCE_MS,
        now_ms: Optional[float] = None,
    ) -> DialgemModel:
        """Verify, then parse a call event into its model (``CallEndedEvent`` and so on).

        An event type this SDK does not know yet is returned as a plain :class:`DialgemModel`
        carrying every field, and a payload that does not fit its model is returned unvalidated
        with a warning: a signed delivery is never dropped over a model mismatch.
        """
        data = self._verified_json(payload, signature, secret, tolerance_ms, now_ms)
        if not isinstance(data, dict) or not isinstance(data.get("event"), str):
            raise WebhookVerificationError("Webhook body has no `event` field.")
        model = _EVENT_MODELS.get(data["event"], DialgemModel)
        return cast_response(data, model)

    def construct_function_call(
        self,
        payload: Payload,
        signature: SignatureHeader,
        secret: str,
        *,
        tolerance_ms: int = DEFAULT_SIGNATURE_TOLERANCE_MS,
        now_ms: Optional[float] = None,
    ) -> FunctionCallRequest:
        """Verify, then parse the request Dialgem sends to a custom function's URL."""
        data = self._verified_json(payload, signature, secret, tolerance_ms, now_ms)
        if not isinstance(data, dict) or not isinstance(data.get("name"), str) or not isinstance(data.get("call"), dict):
            raise WebhookVerificationError(
                "Function request body has no `name` and `call`. Does this function have args_at_root set?"
            )
        return cast_response(data, FunctionCallRequest)

    def _verified_json(
        self, payload: Payload, signature: SignatureHeader, secret: str, tolerance_ms: int, now_ms: Optional[float]
    ) -> Any:
        if not _first(signature):
            raise WebhookVerificationError(
                f"Missing {WEBHOOK_SIGNATURE_HEADER} header. Is a webhook_signing_secret set on the agent?"
            )
        if not self.verify(payload, signature, secret, tolerance_ms=tolerance_ms, now_ms=now_ms):
            raise WebhookVerificationError(
                "Signature is invalid or older than the allowed tolerance. Check the secret, the server clock, "
                "and that the body was not re-serialized before verification."
            )
        try:
            return json.loads(_to_bytes(payload).decode("utf-8"))
        except ValueError as exc:
            raise WebhookVerificationError("Body is signed but is not valid JSON.") from exc


def _first(value: SignatureHeader) -> Optional[str]:
    if value is None or isinstance(value, str):
        return value
    return value[0] if len(value) else None


def _to_bytes(payload: Payload) -> bytes:
    return payload.encode("utf-8") if isinstance(payload, str) else bytes(payload)


webhooks = Webhooks()
