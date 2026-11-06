"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from dialgem.types._base import DialgemModel, Number
from dialgem.types._shared import AgentType, FlowConfig, PostCallAnalysisVariable, PostCallBuiltinFields, PromptState, WebhookEventType


class Agent(DialgemModel):
    """An agent, as returned by `GET /v1/agents/{id}` and the create/update calls.
    The shape is the same across all of those endpoints."""

    id: str
    #: Same value as `id`.
    agent_id: str
    name: str
    agent_type: AgentType
    system_prompt: str
    llm_provider: str
    llm_model: str
    tts_engine: str
    voice_id: str
    first_message: Optional[str]
    temperature: Number
    max_tokens: Number
    #: Set for `agent_type: "flow"`.
    flow_config: Optional[FlowConfig]
    #: Set for `agent_type: "multi_prompt"`.
    states: List[PromptState]
    starting_state: Optional[str]
    #: Fallback values for `{{variables}}` not supplied by the call.
    default_dynamic_variables: Dict[str, str]
    responsiveness: Number
    #: Wait a little longer (up to 1.5 s) when the caller sounds unfinished: a
    #: trailing "and", a comma, a half-read number. Off by default.
    adaptive_response_wait: bool
    interruption_sensitivity: Number
    enable_backchannel: bool
    backchannel_frequency: Number
    reminder_trigger_ms: Number
    reminder_message: str
    ambient_sound: Any
    ambient_sound_volume: Number
    voice_speed: Number
    voice_temperature: Number
    stt_model: str
    language: str
    enable_transcription_formatting: bool
    boosted_keywords: List[str]
    #: `noise-and-background-speech-cancellation` is a stronger setting of the same
    #: stationary-noise filter, scaled by `denoising_strength`; it does not isolate
    #: the caller from other voices.
    denoising_mode: Any
    #: 0-1. Only read by `noise-and-background-speech-cancellation`.
    denoising_strength: Number
    #: `fast` uses Deepgram; `accurate` uses AssemblyAI when the server has it
    #: configured (English only) and falls back to Deepgram otherwise. Only
    #: applies when `stt_model` is `deepgram`.
    stt_mode: Any
    #: `medical` uses Deepgram's medical model (English only), in either `stt_mode`.
    vocab_specialization: Any
    begin_message_delay_ms: Number
    end_call_after_silence_ms: Number
    max_call_duration_ms: Number
    ring_duration_ms: Number
    voicemail_detection_enabled: bool
    voicemail_action: Any
    voicemail_message: str
    #: When set, the voicemail is written by the LLM from this instruction (outbound calls).
    voicemail_prompt: str
    #: Hang up when an automated phone menu is detected (outbound calls).
    ivr_hangup_enabled: bool
    #: How the agent should handle a menu when `ivr_hangup_enabled` is off.
    ivr_prompt: str
    #: Say `call_screen_message` once to a phone's call-screening assistant (outbound calls).
    call_screen_handling_enabled: bool
    call_screen_message: str
    #: Offer the agent a do-not-call tool: a contact who asks to stop being called is
    #: added to the organization's do-not-call list and the call ends.
    dnc_detection_enabled: bool
    post_call_analysis_data: List[PostCallAnalysisVariable]
    post_call_analysis_model: str
    #: Settings for the always-on analysis fields. A missing key means defaults;
    #: `{ enabled: false }` stops that field being extracted (it is stored null).
    post_call_builtin_fields: PostCallBuiltinFields
    fallback_llm_provider: Optional[str]
    fallback_llm_model: Optional[str]
    fallback_voice_id: Optional[str]
    pii_redaction_enabled: bool
    opt_out_call_recording: bool
    opt_out_transcript_storage: bool
    data_retention_days: Optional[Number]
    webhook_url: Optional[str]
    webhook_events: List[WebhookEventType]
    #: Returned by `retrieve`, `create` and `update` only. **Always `null` in
    #: `list()`**; use `has_webhook_signing_secret` there.
    webhook_signing_secret: Optional[str]
    has_webhook_signing_secret: bool
    #: How long, in ms, a receiver gets to answer one delivery attempt. 1000–30000, default 10000.
    webhook_timeout_ms: Number
    #: ISO 8601, no timezone suffix (UTC).
    created_at: Optional[str]
    call_count: Number
    #: Present only on `create` / `update` responses of a flow agent that saved with
    #: warnings. Check it: an issue with `meta.not_runnable === true` means the agent
    #: saved but cannot take calls; attaching it to a number or dialing with it is
    #: refused with `err_code` `flow_not_runnable`.
    flow_validation: Optional[Dict[str, Any]] = None


class AgentDeleteResponse(DialgemModel):
    deleted: bool
    id: str
