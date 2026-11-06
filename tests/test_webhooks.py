"""Signature checks run against vectors produced by the Dialgem service's own signing code
(tests/webhook-vectors.json, shared with the TypeScript SDK), not by this SDK."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dialgem import (
    DEFAULT_SIGNATURE_TOLERANCE_MS,
    Dialgem,
    DialgemError,
    WebhookVerificationError,
    webhooks,
)

FIXTURE = json.loads((Path(__file__).parent / "webhook-vectors.json").read_text(encoding="utf8"))
SECRET = FIXTURE["secret"]
VECTORS = FIXTURE["vectors"]
ENDED = next(v for v in VECTORS if '"event":"call_ended"' in v["body"])
ANALYZED = next(v for v in VECTORS if '"event":"call_analyzed"' in v["body"])
FUNCTION = next(v for v in VECTORS if v["kind"] == "function")


def at(v: dict, offset: int = 0) -> dict:
    return {"now_ms": int(v["timestamp"]) + offset}


@pytest.mark.parametrize("v", VECTORS, ids=lambda v: v["kind"])
def test_accepts_bodies_signed_by_the_service(v):
    assert webhooks.verify(v["body"], v["signature"], SECRET, **at(v)) is True


def test_accepts_str_bytes_bytearray_memoryview():
    for body in (ENDED["body"], ENDED["body"].encode(), bytearray(ENDED["body"].encode()), memoryview(ENDED["body"].encode())):
        assert webhooks.verify(body, ENDED["signature"], SECRET, **at(ENDED)) is True


def test_accepts_a_header_list():
    assert webhooks.verify(ENDED["body"], [ENDED["signature"]], SECRET, **at(ENDED)) is True


def test_is_case_and_whitespace_tolerant_on_the_header():
    assert webhooks.verify(ENDED["body"], f"  {ENDED['signature'].upper()} ", SECRET, **at(ENDED)) is True


def test_rejects_a_tampered_body():
    assert webhooks.verify(ENDED["body"].replace("42500", "4250"), ENDED["signature"], SECRET, **at(ENDED)) is False


def test_rejects_a_reserialized_body_even_though_the_json_is_equal():
    reserialized = json.dumps(json.loads(ENDED["body"]), indent=1)
    assert reserialized != ENDED["body"]
    assert webhooks.verify(reserialized, ENDED["signature"], SECRET, **at(ENDED)) is False


def test_rejects_non_ascii_escaped_by_a_proxy():
    assert "Zoë" in ENDED["body"]
    escaped = ENDED["body"].replace("Zoë", "Zo\\u00eb")
    assert webhooks.verify(escaped, ENDED["signature"], SECRET, **at(ENDED)) is False


def test_rejects_the_wrong_secret():
    assert webhooks.verify(ENDED["body"], ENDED["signature"], "whsec_other", **at(ENDED)) is False


@pytest.mark.parametrize("header", [None, "", "garbage", "v=1,d=zz", "d=" + "0" * 64])
def test_rejects_malformed_headers(header):
    assert webhooks.verify(ENDED["body"], header, SECRET, **at(ENDED)) is False


def test_tolerance_window():
    tol = DEFAULT_SIGNATURE_TOLERANCE_MS
    assert webhooks.verify(ENDED["body"], ENDED["signature"], SECRET, **at(ENDED, tol)) is True
    assert webhooks.verify(ENDED["body"], ENDED["signature"], SECRET, **at(ENDED, tol + 1)) is False
    assert webhooks.verify(ENDED["body"], ENDED["signature"], SECRET, **at(ENDED, -(tol + 1))) is False
    assert webhooks.verify(ENDED["body"], ENDED["signature"], SECRET, tolerance_ms=10, **at(ENDED, 11)) is False


def test_uses_the_wall_clock_by_default():
    # The vector is from 2026-01-01; verifying "now" must reject it as stale.
    assert webhooks.verify(ENDED["body"], ENDED["signature"], SECRET) is False


def test_empty_secret_is_a_programming_error():
    with pytest.raises(DialgemError, match="secret is empty"):
        webhooks.verify(ENDED["body"], ENDED["signature"], "")


def test_available_on_the_client_class():
    assert Dialgem.webhooks is webhooks


@pytest.mark.filterwarnings("ignore:dialgem:UserWarning")
def test_construct_event_returns_typed_models():
    ended = webhooks.construct_event(ENDED["body"], ENDED["signature"], SECRET, **at(ENDED))
    assert type(ended).__name__ == "CallEndedEvent"
    assert ended.event == "call_ended"
    assert ended.call.id == ended.call_id
    analyzed = webhooks.construct_event(ANALYZED["body"], ANALYZED["signature"], SECRET, **at(ANALYZED))
    assert type(analyzed).__name__ == "CallAnalyzedEvent"


def test_construct_event_missing_header():
    with pytest.raises(WebhookVerificationError, match="Missing x-dialgem-signature"):
        webhooks.construct_event(ENDED["body"], None, SECRET)


def test_construct_event_bad_signature():
    with pytest.raises(WebhookVerificationError, match="invalid or older"):
        webhooks.construct_event(ENDED["body"], ENDED["signature"], "whsec_other", **at(ENDED))


def test_construct_function_call():
    req = webhooks.construct_function_call(FUNCTION["body"], FUNCTION["signature"], SECRET, **at(FUNCTION))
    assert req.name == "lookup_order"
    assert req.call.call_id


def test_function_body_is_not_an_event_and_vice_versa():
    with pytest.raises(WebhookVerificationError, match="no `event` field"):
        webhooks.construct_event(FUNCTION["body"], FUNCTION["signature"], SECRET, **at(FUNCTION))
    with pytest.raises(WebhookVerificationError, match="no `name` and `call`"):
        webhooks.construct_function_call(ENDED["body"], ENDED["signature"], SECRET, **at(ENDED))


def test_unknown_event_types_do_not_break_the_receiver(monkeypatch):
    import hashlib
    import hmac

    body = json.dumps({"event": "brand_new_event", "extra": 1})
    ts = "1767225600000"
    sig = hmac.new(SECRET.encode(), body.encode() + ts.encode(), hashlib.sha256).hexdigest()
    event = webhooks.construct_event(body, f"v={ts},d={sig}", SECRET, now_ms=int(ts))
    assert event.event == "brand_new_event"  # type: ignore[attr-defined]
    assert event.extra == 1  # type: ignore[attr-defined]


def test_non_json_signed_body():
    import hashlib
    import hmac

    body = "not json"
    ts = "1767225600000"
    sig = hmac.new(SECRET.encode(), body.encode() + ts.encode(), hashlib.sha256).hexdigest()
    with pytest.raises(WebhookVerificationError, match="not valid JSON"):
        webhooks.construct_event(body, f"v={ts},d={sig}", SECRET, now_ms=int(ts))


def test_chat_events_parse_to_chat_models():
    import hashlib
    import hmac

    chat = {
        "id": "c1", "chat_id": "c1", "chat_type": "api_chat", "chat_status": "ended", "agent_id": "a",
        "agent_version": 0, "metadata": {}, "dynamic_variables": {}, "message_count": 2, "transcript": "",
        "chat_cost": {"combined_cost": 50, "reply_count": 1},
    }
    for name in ("chat_started", "chat_ended", "chat_analyzed"):
        body = json.dumps({"event": name, "chat_id": "c1", "agent_id": "a", "chat": chat})
        ts = "1767225600000"
        sig = hmac.new(SECRET.encode(), body.encode() + ts.encode(), hashlib.sha256).hexdigest()
        event = webhooks.construct_event(body, f"v={ts},d={sig}", SECRET, now_ms=int(ts))
        assert type(event).__name__ == {"chat_started": "ChatStartedEvent", "chat_ended": "ChatEndedEvent", "chat_analyzed": "ChatAnalyzedEvent"}[name]
        assert event.chat.chat_id == "c1" and event.chat.chat_cost == {"combined_cost": 50, "reply_count": 1}  # type: ignore[attr-defined]
