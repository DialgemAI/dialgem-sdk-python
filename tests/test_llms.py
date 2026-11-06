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


def llm(i: str) -> dict:
    return {
        "id": i, "llm_id": i, "name": "n", "system_prompt": "", "llm_provider": "openai", "llm_model": "gpt-4o-mini",
        "temperature": 0.7, "max_tokens": 150,
    }


def test_list_walks_every_page(mock):
    route = mock.get("/v1/llms").mock(
        side_effect=[
            httpx.Response(200, json={"llms": [llm("a"), llm("b")], "has_more": True, "pagination_key": "k1"}),
            httpx.Response(200, json={"llms": [llm("c")], "has_more": False, "pagination_key": None}),
        ]
    )
    ids = [x.id for x in Dialgem(api_key="zk").llms.list(limit=2)]
    assert ids == ["a", "b", "c"]
    assert route.calls[1].request.url.params["pagination_key"] == "k1"


def test_update_sends_only_what_was_given(mock):
    route = mock.patch("/v1/llms/l1").mock(return_value=httpx.Response(200, json=llm("l1")))
    Dialgem(api_key="zk").llms.update("l1", temperature=0.3)
    assert json.loads(route.calls[0].request.content) == {"temperature": 0.3}


def test_agents_accept_an_llm_id(mock):
    create = mock.post("/v1/agents").mock(return_value=httpx.Response(201, json={"agent_id": "ag"}))
    update = mock.patch("/v1/agents/ag").mock(return_value=httpx.Response(200, json={"agent_id": "ag"}))
    c = Dialgem(api_key="zk")
    c.agents.create(name="a", llm_id="l1")
    c.agents.update("ag", llm_id="l2")
    assert json.loads(create.calls[0].request.content)["llm_id"] == "l1"
    assert json.loads(update.calls[0].request.content) == {"llm_id": "l2"}
