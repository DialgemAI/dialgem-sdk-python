"""Types shared by request params and responses.

These stay loosely typed on purpose. A conversation-flow definition is a large discriminated
union that the server validates; modelling it here would make the SDK reject, or silently
drop, shapes the server has since learned to accept.
"""

from __future__ import annotations

from typing import Any, Dict

FlowConfig = Dict[str, Any]
PromptState = Dict[str, Any]
PostCallAnalysisVariable = Dict[str, Any]
PostCallBuiltinFields = Dict[str, Any]
KeyValuePair = Dict[str, Any]
AgentWeight = Dict[str, Any]

AgentType = str
WebhookEventType = str
FunctionKind = str
