from __future__ import annotations

import httpx
import pytest
import respx

from dialgem import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncDialgem,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    Dialgem,
    DialgemError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from .conftest import BASE, call

pytestmark = pytest.mark.filterwarnings("ignore:dialgem:UserWarning")

AGENT = {"id": "a1", "agent_id": "a1", "name": "x"}


@pytest.fixture(params=["sync", "async"])
def client(request: pytest.FixtureRequest):
    cls = Dialgem if request.param == "sync" else AsyncDialgem
    return cls(api_key="zk_test", max_retries=2)


@pytest.fixture
def mock():
    with respx.mock(base_url=BASE, assert_all_called=False) as m:
        yield m


async def get_agent(client, agent_id="a1", **kw):
    return await call(client, lambda c: c.agents.retrieve(agent_id, **kw))


# ------------------------------------------------------------------ request shape


async def test_auth_is_x_api_key_not_bearer(client, mock):
    route = mock.get("/v1/agents/a1").respond(200, json=AGENT)
    await get_agent(client)
    req = route.calls.last.request
    assert req.headers["x-api-key"] == "zk_test"
    assert "authorization" not in req.headers
    assert req.headers["accept"] == "application/json"
    assert req.headers["user-agent"].startswith("dialgem-sdk-python/")


async def test_json_body_is_sent_as_written_in_snake_case(client, mock):
    route = mock.post("/v1/agents").respond(201, json=AGENT)
    await call(client, lambda c: c.agents.create(name="Front desk", default_dynamic_variables={"a": "b"}))
    req = route.calls.last.request
    assert req.headers["content-type"] == "application/json"
    assert req.content == b'{"name": "Front desk", "default_dynamic_variables": {"a": "b"}}'


async def test_query_drops_none_repeats_lists_and_lowercases_bools(client, mock):
    route = mock.get("/v1/calls").respond(200, json={"calls": [], "has_more": False, "pagination_key": None})
    await call(client, lambda c: c.calls.list(agent_id=["a", "b"], call_successful=True, search=None, limit=5))
    url = route.calls.last.request.url
    assert url.params.get_list("agent_id") == ["a", "b"]
    assert url.params["call_successful"] == "true"
    assert url.params["limit"] == "5"
    assert "search" not in url.params


async def test_default_headers_merge_case_insensitively(mock):
    c = Dialgem(api_key="zk_test", default_headers={"x-api-key": "zk_override", "X-Trace": "1"})
    route = mock.get("/v1/agents/a1").respond(200, json=AGENT)
    c.agents.retrieve("a1")
    req = route.calls.last.request
    assert req.headers.get_list("x-api-key") == ["zk_override"]
    assert req.headers["x-trace"] == "1"


async def test_per_request_headers_win(client, mock):
    route = mock.get("/v1/agents/a1").respond(200, json=AGENT)
    await get_agent(client, request_options={"headers": {"X-Trace": "abc"}})
    assert route.calls.last.request.headers["x-trace"] == "abc"


async def test_ids_are_percent_encoded_and_empty_ids_refused(client, mock):
    route = mock.get("/v1/agents/a%2Fb").respond(200, json=AGENT)
    await get_agent(client, "a/b")
    assert route.called
    with pytest.raises(DialgemError, match="non-empty id"):
        await get_agent(client, "")
    with pytest.raises(DialgemError, match="non-empty id"):
        await get_agent(client, "   ")


# ------------------------------------------------------------------ retries


async def test_get_is_retried_on_503(client, mock):
    route = mock.get("/v1/agents/a1").mock(side_effect=[httpx.Response(503), httpx.Response(200, json=AGENT)])
    result = await get_agent(client)
    assert route.call_count == 2
    assert result.id == "a1"


async def test_post_is_never_retried_by_default(client, mock):
    route = mock.post("/v1/calls/outbound").respond(502)
    with pytest.raises(InternalServerError):
        await call(client, lambda c: c.calls.create_phone_call(to="+14155550100", from_="+14155550101"))
    assert route.call_count == 1


async def test_post_can_opt_in_to_retries(client, mock):
    route = mock.post("/v1/calls/outbound").mock(
        side_effect=[httpx.Response(502), httpx.Response(201, json={"call_id": "c1"})]
    )
    await call(
        client,
        lambda c: c.calls.create_phone_call(
            to="+14155550100", from_="+14155550101", request_options={"max_retries": 1}
        ),
    )
    assert route.call_count == 2


async def test_409_is_not_retried(client, mock):
    route = mock.get("/v1/agents/a1").respond(409, json={"err_code": "conflict", "err_msg": "dup", "request_id": "r"})
    with pytest.raises(ConflictError):
        await get_agent(client)
    assert route.call_count == 1


async def test_retry_after_seconds_is_honoured(client, mock, no_sleep):
    mock.get("/v1/agents/a1").mock(
        side_effect=[httpx.Response(429, headers={"retry-after": "2"}), httpx.Response(200, json=AGENT)]
    )
    await get_agent(client)
    assert no_sleep == [2.0]


async def test_retry_after_ms_wins_and_is_capped(client, mock, no_sleep):
    mock.get("/v1/agents/a1").mock(
        side_effect=[
            httpx.Response(429, headers={"retry-after-ms": "1500", "retry-after": "9"}),
            httpx.Response(429, headers={"retry-after": "3600"}),
            httpx.Response(200, json=AGENT),
        ]
    )
    await get_agent(client)
    assert no_sleep == [1.5, 60.0]


async def test_exhausted_retries_raise_the_last_error(client, mock):
    route = mock.get("/v1/agents/a1").respond(500, json={"err_code": "boom", "err_msg": "down", "request_id": "r1"})
    with pytest.raises(InternalServerError) as info:
        await get_agent(client)
    assert route.call_count == 3
    assert info.value.request_id == "r1"


async def test_max_retries_zero_means_one_attempt(client, mock):
    route = mock.get("/v1/agents/a1").respond(503)
    with pytest.raises(InternalServerError):
        await get_agent(client, request_options={"max_retries": 0})
    assert route.call_count == 1


async def test_connection_error_is_retried_for_get(client, mock):
    route = mock.get("/v1/agents/a1").mock(side_effect=[httpx.ConnectError("reset"), httpx.Response(200, json=AGENT)])
    await get_agent(client)
    assert route.call_count == 2


async def test_connection_error_on_post_raises_immediately(client, mock):
    route = mock.post("/v1/agents").mock(side_effect=httpx.ConnectError("reset"))
    with pytest.raises(APIConnectionError):
        await call(client, lambda c: c.agents.create(name="x"))
    assert route.call_count == 1


async def test_timeout_is_a_distinct_error(client, mock):
    mock.get("/v1/agents/a1").mock(side_effect=httpx.ReadTimeout("slow"))
    with pytest.raises(APITimeoutError):
        await get_agent(client, request_options={"max_retries": 0})


# ------------------------------------------------------------------ redirects, bodies, errors


async def test_redirects_are_not_followed(client, mock):
    mock.get("/v1/agents/a1").respond(301, headers={"location": "https://evil.example/steal"})
    elsewhere = mock.get(url="https://evil.example/steal").respond(200, json={})
    with pytest.raises(APIError) as info:
        await get_agent(client)
    assert info.value.status == 301
    assert not elsewhere.called


@pytest.mark.parametrize(
    ("status", "cls"),
    [
        (400, BadRequestError),
        (401, AuthenticationError),
        (403, PermissionDeniedError),
        (404, NotFoundError),
        (409, ConflictError),
        (422, UnprocessableEntityError),
        (429, RateLimitError),
        (500, InternalServerError),
    ],
)
async def test_status_maps_to_error_class(client, mock, status, cls):
    mock.get("/v1/agents/a1").respond(status, json={"err_code": "x", "err_msg": "nope", "request_id": "r"})
    with pytest.raises(cls) as info:
        await get_agent(client, request_options={"max_retries": 0})
    assert info.value.status == status
    assert str(info.value) == f"{status} nope"


async def test_error_envelope_fields(client, mock):
    mock.get("/v1/agents/a1").respond(
        422,
        json={"err_code": "invalid_flow", "err_msg": "bad", "request_id": "req_9", "issues": [{"code": "x"}]},
    )
    with pytest.raises(UnprocessableEntityError) as info:
        await get_agent(client)
    assert (info.value.err_code, info.value.request_id, info.value.issues) == ("invalid_flow", "req_9", [{"code": "x"}])


async def test_non_json_error_body_is_surfaced(client, mock):
    mock.get("/v1/agents/a1").respond(502, text="<html>Bad gateway</html>", headers={"x-request-id": "edge-1"})
    with pytest.raises(InternalServerError) as info:
        await get_agent(client, request_options={"max_retries": 0})
    assert "Bad gateway" in str(info.value)
    assert info.value.request_id == "edge-1"


async def test_204_returns_none(client, mock):
    mock.delete("/v1/agents/a1/functions/f1").respond(204)
    assert await call(client, lambda c: c.agents.functions.delete("a1", "f1")) is None


async def test_unparseable_success_body_is_a_dialgem_error(client, mock):
    mock.get("/v1/agents/a1").respond(200, text="not json")
    with pytest.raises(DialgemError, match="could not parse"):
        await get_agent(client)


# ------------------------------------------------------------------ construction


def test_missing_api_key(monkeypatch):
    monkeypatch.delenv("DIALGEM_API_KEY", raising=False)
    with pytest.raises(DialgemError, match="Missing API key"):
        Dialgem()
    with pytest.raises(DialgemError, match="Missing API key"):
        AsyncDialgem()


def test_api_key_from_environment(monkeypatch):
    monkeypatch.setenv("DIALGEM_API_KEY", "  zk_env  ")
    Dialgem()  # does not raise


def test_base_url_is_not_an_option():
    with pytest.raises(DialgemError, match="base_url"):
        Dialgem(api_key="zk", base_url="https://elsewhere.example")


@pytest.mark.parametrize("bad", [0, -1, True, "5"])
def test_timeout_must_be_positive_number(bad):
    with pytest.raises(DialgemError, match="timeout"):
        Dialgem(api_key="zk", timeout=bad)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [-1, 1.5, True])
def test_max_retries_must_be_non_negative_int(bad):
    with pytest.raises(DialgemError, match="max_retries"):
        Dialgem(api_key="zk", max_retries=bad)  # type: ignore[arg-type]


async def test_context_managers_close_owned_clients():
    with Dialgem(api_key="zk") as c:
        assert not c._client._http.is_closed
    assert c._client._http.is_closed
    async with AsyncDialgem(api_key="zk") as a:
        assert not a._client._http.is_closed
    assert a._client._http.is_closed


def test_injected_http_client_is_not_closed_by_the_sdk():
    http = httpx.Client()
    Dialgem(api_key="zk", http_client=http).close()
    assert not http.is_closed
    http.close()
