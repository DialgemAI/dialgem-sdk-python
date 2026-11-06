"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from dialgem.types._base import DialgemModel, Number
from dialgem.types._shared import FlowConfig


class Voice(DialgemModel):
    """A TTS voice, as returned by `/v1/voices`."""

    #: Dialgem id.
    id: str
    provider: str
    #: The id to put in an agent's `voice_id`.
    provider_voice_id: str
    name: str
    gender: Optional[str]
    accent: Optional[str]
    age: Optional[str]
    voice_type: Optional[str]
    language: List[str]
    preview_url: Optional[str]
    raw_metadata: Optional[Dict[str, Any]]
    #: True for a voice your organization cloned; false for the shared catalog.
    is_custom: bool
    #: Who uploaded the audio, for a cloned voice.
    created_by: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class ExtractionModel(DialgemModel):
    """A model usable for an agent's post-call analysis (`post_call_analysis_model`)."""

    #: Put this in `post_call_analysis_model`.
    id: str
    provider: Union[Literal['anthropic', 'openai'], str]
    label: str
    #: Estimated USD for one typical extraction, derived from list prices. For
    #: comparing models; not a metered charge.
    est_cost_per_session: Number


class ExtractionModelList(DialgemModel):
    #: The model an agent gets when none is set.
    default: str
    models: List[ExtractionModel]


#: One audio sample for cloning. `Blob` and `File` both satisfy this.
VoiceCloneFile = Any


class VoiceDeleteResponse(DialgemModel):
    deleted: bool
    voice_id: str


PromptTemplateSummary = Any


#: Seed an agent from it: `agents.create({ name, system_prompt, first_message, default_dynamic_variables })`.
PromptTemplate = Any


class FlowTemplateSummary(DialgemModel):
    """A built-in flow template, as listed by `/v1/flow-templates`."""

    id: str
    name: str
    description: str
    setup_note: str
    category: str
    tags: List[str]
    use_case: str
    icon: str
    source: str
    node_count: Number
    node_types: List[str]
    unsupported_node_types: List[str]
    path_counts: Dict[str, Number]
    runnable: bool


class FlowTemplate(FlowTemplateSummary):
    """Seed a flow agent from it: `agents.create({ name, agent_type: "flow", flow_config })`."""

    unsupported_nodes: List[Dict[str, Any]]
    not_runnable_reasons: List[Dict[str, Any]]
    flow_config: FlowConfig
