"""Response models for chats, written from the API's own serializer (``chat_to_dict``)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dialgem.types._base import DialgemModel, Number


class ChatMessage(DialgemModel):
    """One entry in a chat. Tool use is shown between the user's message and the agent's reply."""

    message_id: str
    #: ``user``, ``agent``, ``tool_call_invocation`` or ``tool_call_result``.
    role: str
    #: The text. Empty on a ``tool_call_invocation``; the tool's answer on a ``tool_call_result``.
    content: str
    #: Epoch milliseconds.
    created_timestamp: Number
    #: On the two tool roles: ties an invocation to its result.
    tool_call_id: Optional[str] = None
    #: On ``tool_call_invocation``.
    name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None


class Chat(DialgemModel):
    id: str
    #: Same as ``id``.
    chat_id: str
    chat_type: str
    #: ``ongoing`` or ``ended``.
    chat_status: str
    agent_id: str
    #: The version the chat answers with; 0 is the live draft.
    agent_version: Number
    metadata: Dict[str, Any]
    dynamic_variables: Dict[str, str]
    #: Epoch milliseconds.
    start_timestamp: Optional[Number] = None
    end_timestamp: Optional[Number] = None
    #: ``user_ended``, ``agent_ended``, ... ``None`` while ongoing.
    end_reason: Optional[str] = None
    #: User and agent messages, not counting tool entries.
    message_count: Number
    #: ``User: ...`` / ``Agent: ...`` lines.
    transcript: str
    #: Same shape as a call's ``analysis``; ``None`` until it has run (a moment after the chat ends).
    analysis: Optional[Dict[str, Any]] = None
    #: What the chat has cost so far (``combined_cost`` in $0.0001 units, 50 = $0.005) and how many agent
    #: messages it holds (the greeting is one, and is not billed). ``None`` for a team-member session.
    #: Estimates until the price list is published.
    chat_cost: Optional[Dict[str, Number]] = None
    #: Left out of ``list`` entries; ``retrieve`` a chat for them.
    messages: Optional[List[ChatMessage]] = None


class ChatReply(DialgemModel):
    """What ``chats.send_message`` returns: only the new entries, in order."""

    chat_id: str
    chat_status: str
    messages: List[ChatMessage]


class ChatDeleteResponse(DialgemModel):
    deleted: bool
    id: str
