"""Drift guards against the OpenAPI snapshot, and the API-surface policy.

Unit tests with a fake transport can only show the SDK sends what the SDK expects. These show the
backend still has those routes, that nothing reaches a route outside the customer surface, and that
every public method is covered by the table in ``sdk_calls.py``.
"""

from __future__ import annotations

import inspect
import json
import re
from pathlib import Path

import pytest
import respx

from dialgem import AsyncDialgem, Dialgem

from .conftest import BASE, call
from .sdk_calls import SDK_CALLS

pytestmark = pytest.mark.filterwarnings("ignore:dialgem:UserWarning")

SNAPSHOT = json.loads((Path(__file__).parent.parent / "openapi" / "openapi.json").read_text(encoding="utf8"))
PATHS: dict = SNAPSHOT["paths"]

#: Route families that must never be reachable through this SDK. Each needs a session, an admin
#: role, a service credential or a socket, none of which an organization API key carries.
FORBIDDEN_PREFIXES = (
    "/v1/auth",
    "/v1/admin",
    "/v1/orgs",
    "/v1/gem",
    "/v1/internal",
    "/v1/test",
    "/scim",
    "/v1/invitations",
    "/v1/audit-log",
    "/v1/agent/call",
    # Left out on purpose (docs/api-surface.md): money, campaigns, webhook management, privacy and DNC writes.
    "/v1/campaigns",
    "/v1/webhooks",
    "/v1/billing",
    "/v1/usage",
    "/v1/analytics",
)
FORBIDDEN_FRAGMENTS = ("/erase-data", "/do-not-call")


def match_template(concrete: str) -> str | None:
    def placeholders(t: str) -> int:
        return len(re.findall(r"\{[^}]+\}", t))

    hits = [t for t in PATHS if re.fullmatch(re.sub(r"\{[^}]+\}", "[^/]+", t), concrete)]
    return sorted(hits, key=placeholders)[0] if hits else None


@pytest.fixture(params=["sync", "async"])
def client(request):
    cls = Dialgem if request.param == "sync" else AsyncDialgem
    return cls(api_key="zk_test", max_retries=0)


@pytest.mark.parametrize("sdk_call", SDK_CALLS, ids=lambda c: c.name)
async def test_every_sdk_call_hits_a_route_in_the_snapshot(client, sdk_call):
    with respx.mock(base_url=BASE, assert_all_called=False) as mock:
        route = mock.route().respond(200, json={"calls": [], "items": [], "contacts": [], "deliveries": []})
        await call(client, sdk_call.invoke)
        # Pagination is lazy for async: touch the first page so the request is actually made.
        assert route.called, f"{sdk_call.name} made no request"
        request = route.calls[0].request
    assert request.url.host == "api.dialgem.com"
    assert request.url.scheme == "https"
    template = match_template(request.url.path)
    assert template is not None, f"{sdk_call.name}: {request.method} {request.url.path} is not in the OpenAPI snapshot"
    assert request.method.lower() in PATHS[template], (
        f"{sdk_call.name}: {request.method} {template} is not defined in the snapshot"
    )


@pytest.mark.parametrize("sdk_call", SDK_CALLS, ids=lambda c: c.name)
async def test_no_sdk_call_leaves_the_customer_surface(client, sdk_call):
    with respx.mock(base_url=BASE, assert_all_called=False) as mock:
        route = mock.route().respond(200, json={"calls": [], "items": [], "contacts": [], "deliveries": []})
        await call(client, sdk_call.invoke)
        path = route.calls[0].request.url.path
    assert not path.startswith(FORBIDDEN_PREFIXES), f"{sdk_call.name} reaches {path}, outside the customer surface"
    assert not any(x in path for x in FORBIDDEN_FRAGMENTS), f"{sdk_call.name} reaches {path}, outside the customer surface"


def _public_methods(obj, prefix: str = "") -> list[str]:
    names: list[str] = []
    for attr in sorted(vars(obj)):
        value = getattr(obj, attr)
        if attr.startswith("_"):
            continue
        if hasattr(value, "_client") and not isinstance(value, (Dialgem, AsyncDialgem)):
            for method, _member in inspect.getmembers(value, inspect.ismethod):
                if not method.startswith("_"):
                    names.append(f"{prefix}{attr}.{method}")
            names.extend(_public_methods(value, f"{prefix}{attr}."))
    return names


def test_every_public_method_is_in_the_call_table():
    documented = {c.name for c in SDK_CALLS}
    actual = set(_public_methods(Dialgem(api_key="zk")))
    assert actual - documented == set(), f"add these to tests/sdk_calls.py: {sorted(actual - documented)}"
    assert documented - actual == set(), f"stale rows in tests/sdk_calls.py: {sorted(documented - actual)}"


def test_sync_and_async_clients_expose_the_same_surface():
    assert set(_public_methods(Dialgem(api_key="zk"))) == set(_public_methods(AsyncDialgem(api_key="zk")))


def test_async_methods_are_coroutines_and_sync_ones_are_not():
    sync, aio = Dialgem(api_key="zk"), AsyncDialgem(api_key="zk")
    assert not inspect.iscoroutinefunction(sync.agents.retrieve)
    assert inspect.iscoroutinefunction(aio.agents.retrieve)
    # Paginated lists on the async client return an awaitable/async-iterable, not a coroutine.
    assert not inspect.iscoroutinefunction(aio.calls.list)
