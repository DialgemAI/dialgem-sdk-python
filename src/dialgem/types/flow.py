"""Response models for saved flows, written from the API's own serializer (``flow_to_dict``)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from dialgem.types._base import DialgemModel, Number


class Flow(DialgemModel):
    id: str
    #: Same as ``id``.
    flow_id: str
    name: str
    language: str
    #: Bumped by the server when the flow's content changes.
    version: Optional[Number] = None
    node_count: Number
    #: Epoch milliseconds.
    created_timestamp: Optional[Number] = None
    last_modification_timestamp: Optional[Number] = None
    #: Left out of ``list`` entries; ``retrieve`` a flow for it.
    flow_config: Optional[Dict[str, Any]] = None
    #: Present on ``create`` / ``update`` when the flow saved with warnings: ``{"issues": [...]}``.
    flow_validation: Optional[Dict[str, Any]] = None


class FlowDeleteResponse(DialgemModel):
    deleted: bool
    id: str
