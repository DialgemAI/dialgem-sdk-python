"""Response models for saved LLM settings, written from the API's own serializer (``llm_to_dict``)."""

from __future__ import annotations

from typing import Dict, Optional

from dialgem.types._base import DialgemModel, Number


class LLM(DialgemModel):
    id: str
    #: Same as ``id``.
    llm_id: str
    name: str
    #: Epoch milliseconds.
    created_timestamp: Optional[Number] = None
    last_modification_timestamp: Optional[Number] = None
    system_prompt: str = ""
    first_message: Optional[str] = None
    #: ``anthropic`` or ``openai``.
    llm_provider: str
    llm_model: str
    temperature: Number
    max_tokens: Number
    fallback_llm_provider: Optional[str] = None
    fallback_llm_model: Optional[str] = None
    default_dynamic_variables: Dict[str, str] = {}


class LLMDeleteResponse(DialgemModel):
    deleted: bool
    id: str
