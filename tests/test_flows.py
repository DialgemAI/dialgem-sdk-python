from __future__ import annotations

import json

import httpx
import pytest
import respx

from dialgem import Dialgem

from .conftest import BASE

pytestmark = pytest.mark.filterwarnings("ignore:dialgem:UserWarning")


@pytest.fixture
def mock():
    with respx.mock(base_url=BASE, assert_all_called=False) as m:
        yield m


def flow(i: str) -> dict:
    return {"id": i, "flow_id": i, "name": "n", "language": "en", "version": 1, "node_count": 2}


def test_list_walks_every_page(mock):
    route = mock.get("/v1/flows").mock(
        side_effect=[
            httpx.Response(200, json={"flows": [flow("a"), flow("b")], "has_more": True, "pagination_key": "k1"}),
            httpx.Response(200, json={"flows": [flow("c")], "has_more": False, "pagination_key": None}),
        ]
    )
    ids = [f.id for f in Dialgem(api_key="zk").flows.list(limit=2)]
    assert ids == ["a", "b", "c"]
    assert route.calls[0].request.url.params["limit"] == "2"
    assert route.calls[1].request.url.params["pagination_key"] == "k1"


def test_update_sends_only_what_was_given(mock):
    route = mock.patch("/v1/flows/fl1").mock(return_value=httpx.Response(200, json=flow("fl1")))
    Dialgem(api_key="zk").flows.update("fl1", name="New")
    assert json.loads(route.calls[0].request.content) == {"name": "New"}


def test_agents_accept_a_flow_id(mock):
    create = mock.post("/v1/agents").mock(return_value=httpx.Response(201, json={"agent_id": "ag"}))
    update = mock.patch("/v1/agents/ag").mock(return_value=httpx.Response(200, json={"agent_id": "ag"}))
    c = Dialgem(api_key="zk")
    c.agents.create(name="a", agent_type="flow", flow_id="fl1")
    c.agents.update("ag", flow_id="fl2")
    assert json.loads(create.calls[0].request.content)["flow_id"] == "fl1"
    assert json.loads(update.calls[0].request.content) == {"flow_id": "fl2"}
