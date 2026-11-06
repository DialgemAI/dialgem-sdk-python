"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from dialgem.types._base import DialgemModel, Number
from dialgem.types.call import Call
from dialgem.types.chat import Chat


class CallEventBase(DialgemModel):
    call_id: str
    agent_id: str
    #: The full call record at the moment the event was sent.
    call: Call


class CallStartedEvent(CallEventBase):
    event: Literal['call_started']


class CallEndedEvent(CallEventBase):
    """Sent as soon as the call ends; post-call analysis follows in `call_analyzed`."""

    event: Literal['call_ended']


class CallAnalyzedEvent(CallEventBase):
    """Sent after `call_ended`, once analysis has run, and only for calls that produced a transcript."""

    event: Literal['call_analyzed']


class ChatEventBase(DialgemModel):
    """Chat events carry ``chat_id``, not ``call_id``."""

    chat_id: str
    agent_id: str
    #: The full chat record, with its messages, at the moment the event was sent.
    chat: Chat


class ChatStartedEvent(ChatEventBase):
    event: Literal['chat_started']


class ChatEndedEvent(ChatEventBase):
    """The chat ended (``chats.end`` or the agent). Analysis follows in ``chat_analyzed``."""

    event: Literal['chat_ended']


class ChatAnalyzedEvent(ChatEventBase):
    """Sent once a chat's analysis has run."""

    event: Literal['chat_analyzed']


class WebhookTranscriptTurn(DialgemModel):
    """A transcript turn as carried by `transcript_updated`."""

    role: Union[Literal['user', 'agent'], str]
    text: str
    timestamp: str
    start_ms: Optional[Number] = None


class TranscriptUpdatedEvent(CallEventBase):
    """Sent each time a caller or agent turn is added to the live transcript.
    
    `transcript` is the whole transcript so far, so a receiver that misses or
    reorders a delivery still ends up correct. `turn_index` increases by one per
    event within a call; keep the highest."""

    event: Literal['transcript_updated']
    #: Who spoke the turn that triggered this event.
    role: Union[Literal['user', 'agent'], str]
    turn_index: Number
    transcript: List[WebhookTranscriptTurn]


class WebhookTransferInfo(DialgemModel):
    """What a transfer event says about the transfer. Fields are present only when known."""

    #: The number the call is being transferred to.
    target: Optional[str] = None
    mode: Optional[Union[Literal['cold'], Literal['warm'], str]] = None
    #: Why a transfer was cancelled: a carrier dial status (`busy`, `no-answer`, ...) or a failure reason.
    reason: Optional[str] = None


class TransferStartedEvent(CallEventBase):
    """The agent asked for the call to be transferred."""

    event: Literal['transfer_started']
    transfer: WebhookTransferInfo


class TransferBridgedEvent(CallEventBase):
    """The transferee answered and was connected to the caller. For a cold transfer
    this is delivered when the transferred leg finishes, immediately followed by
    `transfer_ended`."""

    event: Literal['transfer_bridged']
    transfer: WebhookTransferInfo


class TransferCancelledEvent(CallEventBase):
    """The transfer did not connect: busy, no answer, failed, or could not be placed."""

    event: Literal['transfer_cancelled']
    transfer: WebhookTransferInfo


class TransferEndedEvent(CallEventBase):
    """A connected transfer finished."""

    event: Literal['transfer_ended']
    transfer: WebhookTransferInfo


class FunctionCallRequest(DialgemModel):
    """The body Dialgem POSTs to a custom function's URL when the agent calls it,
    unless the function has `args_at_root`, in which case the body is `args` alone."""

    #: The function's name.
    name: str
    call: FunctionCallContext
    #: The arguments the agent supplied, per the function's `parameters` schema.
    args: Any


class FunctionCallContext(DialgemModel):
    call_id: str
    agent_id: Optional[str]
    call_type: Union[Literal['phone_call', 'web_call'], str]
    direction: Optional[Union[Literal['inbound', 'outbound'], str]]
    from_number: Optional[str]
    to_number: Optional[str]
    dynamic_variables: Dict[str, str]
    metadata: Dict[str, Any]


_WebhookEventsExhaustive = Any
