"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List

from dialgem.types._base import DialgemModel, Number


class WebCall(DialgemModel):
    """What `webCalls.create` returns. Hand `access_token` to the page; keep your API key on the server."""

    #: The call's id. The call record exists from now, with status `queued` until the browser connects.
    call_id: str
    agent_id: str
    #: The published version this call will run (0 is the live draft).
    agent_version: Number
    #: A one-use credential for exactly this call and agent. It cannot be used for anything else, and it works
    #: from the origins you have allowed, once.
    access_token: str
    #: ISO 8601, UTC. 60 seconds after creation: long enough to reach the page, not to be stockpiled.
    expires_at: str
    expires_in: Number


class WebCallSettings(DialgemModel):
    #: The websites (origins, like `https://app.example.com`) browser calls may start from. Empty means none.
    allowed_origins: List[str]
    #: True when the list contains `*`: any website may start a call with a token it was given.
    any_origin: bool
    limits: Dict[str, Any]
