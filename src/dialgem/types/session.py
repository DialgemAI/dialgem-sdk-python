"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from dialgem.types._base import DialgemModel, Number


class AgentSession(DialgemModel):
    """A call in progress right now, as the service holds it in memory.
    
    This is live state, not a record: a finished call is a `Call`, reachable
    through `calls.retrieve`. The shape of a session is not a stable contract
    beyond the fields below, so it is deliberately open."""

    session_id: str
    agent_id: str
    status: Any
    #: ISO 8601.
    started_at: Optional[str] = None


class AgentSessionSayResult(DialgemModel):
    """What ``sessions.say`` returns: the line plays behind the call's audio, so this answers at once."""

    status: str


class AgentSessionReleaseResult(DialgemModel):
    """What ``sessions.release`` returns."""

    #: ``handed_back``, or ``not_taken_over`` when nobody had the call.
    status: str
    reason: Optional[str] = None


class AgentSessionUpdateResult(DialgemModel):
    """What ``sessions.update`` returns."""

    session_id: str
    status: Any
    #: Which of ``system_prompt`` and ``dynamic_variables`` were changed.
    updated: List[str]
    applies_from: str


class AgentSessionList(DialgemModel):
    sessions: List[AgentSession]
    #: How many are live. This is what "how busy am I right now?" asks for.
    count: Number
