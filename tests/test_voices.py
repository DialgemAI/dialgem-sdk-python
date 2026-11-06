from __future__ import annotations

import io

import httpx
import pytest
import respx

from dialgem import AsyncDialgem, Dialgem, DialgemError, InternalServerError

from .conftest import BASE, call

pytestmark = pytest.mark.filterwarnings("ignore:dialgem:UserWarning")

VOICE = {"id": "v1", "name": "Mine"}


@pytest.fixture(params=["sync", "async"])
def client(request):
    cls = Dialgem if request.param == "sync" else AsyncDialgem
    return cls(api_key="zk_test", max_retries=3)


@pytest.fixture
def mock():
    with respx.mock(base_url=BASE, assert_all_called=False) as m:
        yield m


async def test_clone_requires_explicit_consent(client, mock):
    route = mock.post("/v1/voices/clone").respond(201, json=VOICE)
    for bad in (False, None, 1, "true"):
        with pytest.raises(DialgemError, match="consent_confirmed must be True"):
            await call(client, lambda c, bad=bad: c.voices.clone(name="n", files=[b"x"], consent_confirmed=bad))
    assert not route.called


async def test_clone_requires_a_file(client, mock):
    with pytest.raises(DialgemError, match="At least one audio file"):
        await call(client, lambda c: c.voices.clone(name="n", files=[], consent_confirmed=True))


async def test_clone_sends_multipart_with_filenames(client, mock):
    route = mock.post("/v1/voices/clone").respond(201, json=VOICE)
    await call(
        client,
        lambda c: c.voices.clone(
            name="Mine",
            files=[("one.wav", b"AAA"), io.BytesIO(b"BBB"), b"CCC"],
            filenames=[None, "two.wav"],  # type: ignore[list-item]
            consent_confirmed=True,
            engine="cartesia",
            language="en",
        ),
    )
    req = route.calls.last.request
    assert req.headers["content-type"].startswith("multipart/form-data; boundary=")
    body = req.content
    assert b'name="name"' in body and b"Mine" in body
    assert b'name="consent_confirmed"' in body and b"true" in body
    assert b'name="engine"' in body and b"cartesia" in body
    assert body.count(b'name="files"') == 3
    assert b'filename="two.wav"' in body
    assert b'filename="clip-3.wav"' in body
    # The key header is still ours, and no JSON content-type leaked in.
    assert req.headers["x-api-key"] == "zk_test"


async def test_multipart_uploads_are_never_retried_even_on_request(client, mock):
    route = mock.post("/v1/voices/clone").respond(503)
    with pytest.raises(InternalServerError):
        await call(
            client,
            lambda c: c.voices.clone(
                name="n", files=[b"x"], consent_confirmed=True, request_options={"max_retries": 3}
            ),
        )
    assert route.call_count == 1


async def test_ids_reach_the_wire_percent_encoded(client, mock):
    route = mock.get(url__regex=r"https://api\.dialgem\.com/v1/agents/.*").respond(200, json={"id": "a"})
    await call(client, lambda c: c.agents.retrieve("a/b?c#d"))
    assert route.calls.last.request.url.raw_path == b"/v1/agents/a%2Fb%3Fc%23d"


async def test_a_path_segment_cannot_escape_to_another_route(client, mock):
    route = mock.route().respond(200, json={})
    await call(client, lambda c: c.agents.retrieve("../../orgs"))
    assert route.calls.last.request.url.raw_path == b"/v1/agents/..%2F..%2Forgs"
    assert httpx.URL(str(route.calls.last.request.url)).path.startswith("/v1/agents/")
