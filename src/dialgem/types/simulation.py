"""Response models for this resource. Bootstrapped from the TypeScript SDK; owned by hand now."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

from dialgem.types._base import DialgemModel, Number


#: What publishing a version of the agent does when the draft has not passed the suite.
SimulationPublishGate = Union[Literal['off', 'warn', 'block'], str]


SimulationCaller = Dict[str, Any]


class CheckBase(DialgemModel):
    #: Names the check in the results.
    label: Optional[str] = None


SimulationCheck = Any


class SimulationCaseInput(DialgemModel):
    name: str
    caller: SimulationCaller
    #: Fills `{{placeholders}}` in the agent's prompt and first message.
    dynamic_variables: Optional[Dict[str, Union[str, Number]]] = None
    #: What each tool answers. A tool without an entry answers `{"status": "ok"}`.
    tool_mocks: Optional[Dict[str, Any]] = None
    #: At least one. The case passes when all of them hold.
    checks: List[SimulationCheck]


class SimulationCase(DialgemModel):
    id: str
    suite_id: str
    position: Number
    dynamic_variables: Dict[str, str]
    tool_mocks: Dict[str, Any]
    created_at: Optional[str]
    updated_at: Optional[str]


SimulationRunStatus = Union[Literal['queued', 'running', 'completed', 'cancelled', 'failed'], str]


class SimulationRun(DialgemModel):
    id: str
    suite_id: str
    agent_id: str
    #: The version that was tested; `0` is the draft.
    agent_version: Number
    status: SimulationRunStatus
    trigger: str
    fresh: bool
    total: Number
    passed: Number
    failed: Number
    #: The model or the case broke; this says nothing about your agent.
    errored: Number
    #: Cancelled, or the run ran out of model turns.
    skipped: Number
    model_turn_budget: Number
    model_turns_used: Number
    budget_exhausted: bool
    created_at: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]


SimulationResultStatus = Union[Literal['pending', 'passed', 'failed', 'errored', 'skipped'], str]


class SimulationCheckResult(DialgemModel):
    #: Position in the case's `checks`.
    index: Number
    type: Any
    label: Optional[str] = None
    passed: bool
    detail: str


class SimulationResult(DialgemModel):
    id: str
    case_id: Optional[str]
    case_name: str
    position: Number
    status: SimulationResultStatus
    #: Why it failed, errored or was skipped.
    reason: Optional[str]
    #: Taken from an earlier identical run rather than run again.
    cached: bool
    transcript: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    #: A flow agent's variables at the end.
    variables: Dict[str, Any]
    checks: List[SimulationCheckResult]
    model_turns: Number
    duration_ms: Number
    finished_at: Optional[str]


class SimulationRunDetail(SimulationRun):
    results: List[SimulationResult]


class SimulationSuite(DialgemModel):
    id: str
    agent_id: str
    name: str
    description: Optional[str]
    publish_gate: SimulationPublishGate
    case_count: Number
    latest_run: Optional[SimulationRun]
    created_at: Optional[str]
    updated_at: Optional[str]


class SimulationSuiteDetail(SimulationSuite):
    cases: List[SimulationCase]


class SimulationSuiteList(DialgemModel):
    #: Whether simulations are switched on for the platform.
    enabled: bool
    suites: List[SimulationSuite]


class SimulationRunList(DialgemModel):
    runs: List[SimulationRun]
