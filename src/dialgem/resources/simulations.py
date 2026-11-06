"""Simulations: scripted test calls against an agent."""

from __future__ import annotations

from typing import Optional

from typing_extensions import Unpack

from dialgem._base_client import RequestOptions
from dialgem._resource import Resource, pid
from dialgem.types.params import (
    SimulationCaseParams,
    SimulationCaseUpdateParams,
    SimulationRunCreateParams,
    SimulationSuiteCreateParams,
    SimulationSuiteUpdateParams,
)
from dialgem.types.simulation import (
    SimulationCase,
    SimulationRun,
    SimulationRunDetail,
    SimulationRunList,
    SimulationSuite,
    SimulationSuiteDetail,
    SimulationSuiteList,
)


class Simulations(Resource):
    """``dialgem.simulations``."""

    def create_suite(
        self, *, request_options: Optional[RequestOptions] = None, **body: Unpack[SimulationSuiteCreateParams]
    ) -> SimulationSuite:
        return self._client.post("/v1/simulations/suites", body=body, cast_to=SimulationSuite, options=request_options)

    def list_suites(
        self, *, agent_id: Optional[str] = None, request_options: Optional[RequestOptions] = None
    ) -> SimulationSuiteList:
        return self._client.get(
            "/v1/simulations/suites", query={"agent_id": agent_id}, cast_to=SimulationSuiteList, options=request_options
        )

    def retrieve_suite(self, suite_id: str, /, *, request_options: Optional[RequestOptions] = None) -> SimulationSuiteDetail:
        return self._client.get(
            f"/v1/simulations/suites/{pid(suite_id)}", cast_to=SimulationSuiteDetail, options=request_options
        )

    def update_suite(
        self,
        suite_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[SimulationSuiteUpdateParams],
    ) -> SimulationSuite:
        return self._client.patch(
            f"/v1/simulations/suites/{pid(suite_id)}", body=body, cast_to=SimulationSuite, options=request_options
        )

    def delete_suite(self, suite_id: str, /, *, request_options: Optional[RequestOptions] = None) -> None:
        return self._client.delete(f"/v1/simulations/suites/{pid(suite_id)}", options=request_options)

    def create_case(
        self, suite_id: str, /, *, request_options: Optional[RequestOptions] = None, **body: Unpack[SimulationCaseParams]
    ) -> SimulationCase:
        return self._client.post(
            f"/v1/simulations/suites/{pid(suite_id)}/cases", body=body, cast_to=SimulationCase, options=request_options
        )

    def update_case(
        self,
        case_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[SimulationCaseUpdateParams],
    ) -> SimulationCase:
        return self._client.patch(
            f"/v1/simulations/cases/{pid(case_id)}", body=body, cast_to=SimulationCase, options=request_options
        )

    def delete_case(self, case_id: str, /, *, request_options: Optional[RequestOptions] = None) -> None:
        return self._client.delete(f"/v1/simulations/cases/{pid(case_id)}", options=request_options)

    def run(
        self,
        suite_id: str,
        /,
        *,
        request_options: Optional[RequestOptions] = None,
        **body: Unpack[SimulationRunCreateParams],
    ) -> SimulationRun:
        """Start a run of every case in the suite."""
        return self._client.post(
            f"/v1/simulations/suites/{pid(suite_id)}/runs", body=dict(body), cast_to=SimulationRun, options=request_options
        )

    def list_runs(
        self,
        *,
        suite_id: Optional[str] = None,
        limit: Optional[int] = None,
        request_options: Optional[RequestOptions] = None,
    ) -> SimulationRunList:
        return self._client.get(
            "/v1/simulations/runs",
            query={"suite_id": suite_id, "limit": limit},
            cast_to=SimulationRunList,
            options=request_options,
        )

    def retrieve_run(self, run_id: str, /, *, request_options: Optional[RequestOptions] = None) -> SimulationRunDetail:
        return self._client.get(
            f"/v1/simulations/runs/{pid(run_id)}", cast_to=SimulationRunDetail, options=request_options
        )

    def cancel_run(self, run_id: str, /, *, request_options: Optional[RequestOptions] = None) -> SimulationRun:
        return self._client.post(
            f"/v1/simulations/runs/{pid(run_id)}/cancel", cast_to=SimulationRun, options=request_options
        )
