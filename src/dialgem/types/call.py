"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from dialgem.types._base import DialgemModel, Number


class Call(DialgemModel):
    """A call, as returned by `GET /v1/calls`, `GET /v1/calls/{id}` and every call webhook.
    The shape is the same everywhere."""

    id: str
    #: Empty string when the call has no agent.
    agent_id: str
    #: The published agent version this call ran. 0 is the live draft, which is
    #: what a call runs unless a number or the request that created it pinned a
    #: version.
    agent_version: Number
    agent_name: str
    #: Dialgem's lifecycle state.
    status: CallStatus
    #: The same state in session vocabulary: active→ongoing, completed→ended, failed→error, queued→registered.
    call_status: CallSessionStatus
    call_type: Any
    direction: Any
    #: Your own data, attached when the call was created or later with `calls.update`.
    metadata: Dict[str, Any]
    #: The dynamic variables the call was started with.
    dynamic_variables: Dict[str, str]
    #: ISO 8601, no timezone suffix (UTC). Empty string if unknown.
    started_at: str
    #: ISO 8601, no timezone suffix (UTC). `null` while the call is ongoing.
    ended_at: Optional[str]
    #: Epoch milliseconds.
    start_timestamp: Optional[Number]
    #: Epoch milliseconds. `null` while the call is ongoing.
    end_timestamp: Optional[Number]
    duration_s: Number
    duration_ms: Optional[Number]
    phone_number: str
    from_number: str
    to_number: str
    #: Carrier call id (Twilio CallSid). Empty string if none.
    call_sid: str
    origination_state: Optional[str]
    #: One entry per turn. Empty when the agent opts out of transcript storage, and
    #: once the agent's `data_retention_days` purge has run. PII-redacted when
    #: redaction is on.
    transcript: List[TranscriptTurn]
    #: The same transcript as one string, `Agent: …` / `User: …` per line.
    transcript_text: str
    #: Presigned URL that expires; download it promptly rather than storing the link.
    recording_url: Optional[str]
    events: List[Dict[str, Any]]
    disconnection_reason: Optional[DisconnectionReason]
    #: Whether the call reached voicemail or an answering machine.
    in_voicemail: bool
    amd_result: Optional[Dict[str, Any]]
    #: Post-call analysis. `null` until the call has ended and been analyzed, and after a retention purge.
    analysis: Optional[CallAnalysis]
    #: Set once the call is finalized.
    call_cost: Optional[CallCost]
    #: Mean time from the caller's final transcript to the agent's first audio byte.
    end_to_end_latency_ms: Optional[Number]
    #: Per-stage latency percentiles, recorded when the call ends. `null` if no turn completed.
    latency: Optional[CallLatency]


DisconnectionReason = Any


class CallCost(DialgemModel):
    """Every amount is an integer in units of **$0.0001**: `combined_cost: 1700` is $0.17."""

    combined_cost: Number
    total_duration_seconds: Number
    total_duration_unit_price: Number
    product_costs: List[Dict[str, Any]]


CallStatus = Any


CallSessionStatus = Any


class TranscriptTurn(DialgemModel):
    role: Union[Literal['user', 'agent'], str]
    text: str
    #: ISO 8601.
    timestamp: str


class CallAnalysis(DialgemModel):
    #: A one-to-three sentence summary of the call.
    call_summary: Optional[str]
    user_sentiment: Optional[Any]
    call_successful: Optional[bool]
    in_voicemail: bool
    #: Values for the agent's `post_call_analysis_data` fields, keyed by name.
    variables: Dict[str, Any]
    model: str
    extracted_at: str
    #: Set when extraction failed; `variables` may then be partial or empty.
    error: Optional[str]


class LatencyStats(DialgemModel):
    """Milliseconds. Each stage has at least one sample, or is omitted."""

    p50: Number
    p90: Number
    p95: Number
    p99: Number
    min: Number
    max: Number
    num: Number


class CallLatency(DialgemModel):
    #: Caller's final transcript to the agent's first audio byte.
    e2e: Optional[LatencyStats] = None
    #: Time to the model's first sentence.
    llm: Optional[LatencyStats] = None
    #: Time to the first synthesized audio.
    tts: Optional[LatencyStats] = None
    #: How long end-of-speech detection waited.
    endpointing: Optional[LatencyStats] = None


class CallDeleteResponse(DialgemModel):
    deleted: bool
    id: str


class CallStopResponse(DialgemModel):
    id: str
    #: The call is tearing down; it becomes `completed` with `disconnection_reason: "manual_stopped"` shortly.
    stopping: bool


class PhoneCallCreateResponse(DialgemModel):
    """Result of `calls.createPhoneCall`. The call is dialing; its outcome arrives via webhooks or `calls.retrieve`."""

    call_id: str
    call_sid: str
    origination_state: Any


class CallRegisterResponse(DialgemModel):
    """Result of `calls.register`: return TwiML `<Connect><Stream url="{stream_url}"/></Connect>` to Twilio."""

    call_id: str
    #: Signed `wss://` Twilio Media Streams URL. Hand it to Twilio before `expires_in` elapses.
    stream_url: str
    #: Seconds until `stream_url`'s signature expires.
    expires_in: Number
