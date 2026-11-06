from __future__ import annotations

import json

import httpx
import pytest
import respx

from dialgem import AsyncDialgem, Dialgem, InternalServerError

from .conftest import BASE

pytestmark = pytest.mark.filterwarnings("ignore:dialgem:UserWarning")


@pytest.fixture
def mock():
    with respx.mock(base_url=BASE, assert_all_called=False) as m:
        yield m


def chat(i: str) -> dict:
    return {"id": i, "chat_id": i, "chat_status": "ongoing"}


def test_list_walks_every_page_and_keeps_the_filters(mock):
    route = mock.get("/v1/chats").mock(
        side_effect=[
            httpx.Response(200, json={"chats": [chat("a"), chat("b")], "has_more": True, "pagination_key": "k1"}),
            httpx.Response(200, json={"chats": [chat("c")], "has_more": False, "pagination_key": None}),
        ]
    )
    ids = [c.id for c in Dialgem(api_key="zk").chats.list(status="ended", agent_id="ag1")]
    assert ids == ["a", "b", "c"]
    for call in route.calls:
        assert call.request.url.params["status"] == "ended"
        assert call.request.url.params["agent_id"] == "ag1"
    assert route.calls[1].request.url.params["pagination_key"] == "k1"


def test_send_message_posts_the_text_as_content(mock):
    route = mock.post("/v1/chats/ch1/messages").mock(
        return_value=httpx.Response(200, json={"chat_id": "ch1", "chat_status": "ongoing", "messages": [
            {"message_id": "m1", "role": "agent", "content": "Hello", "created_timestamp": 1}]})
    )
    reply = Dialgem(api_key="zk").chats.send_message("ch1", "hi there")
    assert json.loads(route.calls[0].request.content) == {"content": "hi there"}
    assert reply.messages[0].content == "Hello"


def test_send_message_is_not_retried(mock):
    route = mock.post("/v1/chats/ch1/messages").mock(return_value=httpx.Response(503, json={"err_code": "x", "err_msg": "down"}))
    with pytest.raises(InternalServerError):
        Dialgem(api_key="zk", max_retries=2).chats.send_message("ch1", "hi")
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_the_async_client_has_the_same_chats(mock):
    mock.post("/v1/chats/ch1/end").mock(return_value=httpx.Response(200, json=chat("ch1")))
    got = await AsyncDialgem(api_key="zk").chats.end("ch1")
    assert got.id == "ch1"


def test_an_empty_chat_id_is_refused_before_any_request(mock):
    from dialgem import DialgemError

    with pytest.raises(DialgemError):
        Dialgem(api_key="zk").chats.send_message("", "hi")
