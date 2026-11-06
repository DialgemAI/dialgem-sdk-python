"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from dialgem.types._base import DialgemModel, Number


#: Which published agent version a number answers on.
#: 
#: A number is the frozen version with that number; `0` is the live draft, which
#: is what a number does when nothing is pinned. `"latest_published"` is a
#: pointer rather than a choice — it follows the newest publish, so shipping a
#: new version moves every number set to it without touching them.
#: 
#: A *call* never reports this type: `Call.agent_version` is always the concrete
#: number that ran, resolved when the call was placed.
AgentVersionRef = Union[Number, Literal['latest_published']]


class PhoneNumber(DialgemModel):
    """A phone number, as returned by `/v1/phone-numbers`.
    The shape is the same across all phone-number endpoints."""

    #: Dialgem id. Use this (not the E.164 number) for update/assign/delete.
    id: str
    status: str
    provider: str
    #: E.164, e.g. `+14155550123`.
    phone_number: str
    phone_number_pretty: str
    phone_number_type: str
    nickname: str
    inbound_agent_id: Optional[str]
    inbound_agent_version: AgentVersionRef
    outbound_agent_id: Optional[str]
    outbound_agent_version: AgentVersionRef
    #: Weighted inbound routing. `inbound_agent_id` is its primary entry.
    inbound_agents: List[PhoneNumberAgentWeight]
    outbound_agents: List[PhoneNumberAgentWeight]
    custom_sms_enabled: bool
    flow_sms_sender_enabled: bool
    #: Epoch milliseconds (0 if unknown).
    creation_timestamp: Number
    #: Epoch milliseconds (0 if unknown).
    last_modification_timestamp: Number
    sip_outbound_trunk_config: Optional[SipOutboundTrunkConfig]
    #: The inbound routing webhook, asked before an inbound call is answered. `null` when none is set.
    inbound_webhook_url: Optional[str]
    #: The last four characters of the signing secret; `null` with no webhook.
    inbound_webhook_secret_hint: Optional[str]
    #: The full signing secret. Present **only** in the response that created or rotated it, never again.
    inbound_webhook_secret: Optional[str] = None


class InboundWebhookTestResult(DialgemModel):
    """What `phoneNumbers.testInboundWebhook` reports."""

    #: Your endpoint answered with a 2xx.
    ok: bool
    status_code: Optional[Number]
    latency_ms: Number
    #: The time your endpoint has for a real call (`INBOUND_ROUTING_TIMEOUT_S`).
    budget_ms: Number
    error: Optional[str]
    #: What a real call would have done with the answer.
    decision: Dict[str, Any]


class PhoneNumberAgentWeight(DialgemModel):
    agent_id: str
    agent_version: AgentVersionRef
    weight: Number


class SipOutboundTrunkConfig(DialgemModel):
    termination_uri: Optional[str] = None
    transport: Optional[str] = None
    auth_username: Optional[str] = None
