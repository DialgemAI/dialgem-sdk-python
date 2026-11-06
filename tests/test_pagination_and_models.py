from __future__ import annotations

import subprocess
import sys
import warnings
from pathlib import Path

import httpx
import pytest
import respx

from dialgem import AsyncDialgem, Dialgem, DialgemError
from dialgem._base_client import cast_response
from dialgem.types.call import Call
from dialgem.types.contact import Contact

from .conftest import BASE

ROOT = Path(__file__).parent.parent


def calls_page(ids, more, key):
    return httpx.Response(200, json={"calls": [{"call_id": i} for i in ids], "has_more": more, "pagination_key": key})


@pytest.fixture
def mock():
    with respx.mock(base_url=BASE, assert_all_called=False) as m:
        yield m


@pytest.mark.filterwarnings("ignore:dialgem:UserWarning")
def test_sync_iteration_walks_every_page(mock):
    route = mock.get("/v1/calls").mock(
        side_effect=[calls_page(["a", "b"], True, "k1"), calls_page(["c"], True, "k2"), calls_page(["d"], False, None)]
    )
    ids = [c.call_id for c in Dialgem(api_key="zk").calls.list(limit=2)]
    assert ids == ["a", "b", "c", "d"]
    assert route.calls[1].request.url.params["pagination_key"] == "k1"
    assert route.calls[2].request.url.params["pagination_key"] == "k2"
    assert "pagination_key" not in route.calls[0].request.url.params


@pytest.mark.filterwarnings("ignore:dialgem:UserWarning")
def test_sync_page_is_usable_one_page_at_a_time(mock):
    mock.get("/v1/calls").mock(side_effect=[calls_page(["a"], True, "k1"), calls_page(["b"], False, None)])
    page = Dialgem(api_key="zk").calls.list()
    assert [c.call_id for c in page.data] == ["a"]
    assert page.has_next_page()
    nxt = page.get_next_page()
    assert [c.call_id for c in nxt.data] == ["b"]
    assert not nxt.has_next_page()
    with pytest.raises(DialgemError, match="No next page"):
        nxt.get_next_page()


@pytest.mark.filterwarnings("ignore:dialgem:UserWarning")
async def test_async_paginator_is_awaitable_and_async_iterable(mock):
    mock.get("/v1/calls").mock(
        side_effect=[calls_page(["a"], True, "k1"), calls_page(["b"], False, None), calls_page(["a"], True, "k1"), calls_page(["b"], False, None)]
    )
    client = AsyncDialgem(api_key="zk")
    seen = [c.call_id async for c in client.calls.list()]
    assert seen == ["a", "b"]
    page = await client.calls.list()
    assert [c.call_id for c in page.data] == ["a"]
    second = await page.get_next_page()
    assert [c.call_id for c in second.data] == ["b"]


@pytest.mark.filterwarnings("ignore:dialgem:UserWarning")
def test_cursor_endpoints_use_next_cursor(mock):
    route = mock.get("/v1/contacts").mock(
        side_effect=[
            httpx.Response(200, json={"contacts": [{"id": "t1"}], "next_cursor": "c2"}),
            httpx.Response(200, json={"contacts": [{"id": "t2"}], "next_cursor": None}),
        ]
    )
    ids = [t.id for t in Dialgem(api_key="zk").contacts.list()]
    assert ids == ["t1", "t2"]
    assert route.calls[1].request.url.params["cursor"] == "c2"


@pytest.mark.filterwarnings("ignore:dialgem:UserWarning")
def test_metadata_filters_are_flattened(mock):
    route = mock.get("/v1/calls").mock(return_value=calls_page([], False, None))
    list(Dialgem(api_key="zk").calls.list(metadata={"visitor": "v_1", "vip": True}))
    params = route.calls[0].request.url.params
    assert params["metadata.visitor"] == "v_1"
    assert params["metadata.vip"] == "true"


# ----------------------------------------------------------------- models


def test_unknown_fields_are_kept():
    call = Call.model_validate({"call_id": "c1", "brand_new_field": 7}) if False else None
    from dialgem.types._base import DialgemModel

    class M(DialgemModel):
        a: int

    m = M.model_validate({"a": 1, "later": {"x": 2}})
    assert m.later == {"x": 2}  # type: ignore[attr-defined]
    assert m.to_dict() == {"a": 1, "later": {"x": 2}}
    assert call is None


def test_a_response_that_does_not_fit_degrades_instead_of_raising():
    import dialgem._base_client as bc

    bc._warned.discard("Contact")
    with pytest.warns(UserWarning, match="Contact"):
        result = cast_response({"id": "t1", "surprise": True}, Contact)
    assert isinstance(result, Contact)
    assert result.id == "t1"
    assert result.surprise is True  # type: ignore[attr-defined]


def test_the_drift_warning_fires_once_per_model():
    import dialgem._base_client as bc

    bc._warned.discard("Contact")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cast_response({"id": "t1"}, Contact)
        cast_response({"id": "t2"}, Contact)
    assert len([w for w in caught if "Contact" in str(w.message)]) == 1


def test_list_casts_degrade_per_item():
    from typing import List

    import dialgem._base_client as bc

    bc._warned.discard("typing.List[dialgem.types.contact.Contact]")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = cast_response([{"id": "a"}, {"id": "b"}], List[Contact])
    assert [r.id for r in result] == ["a", "b"]


# ----------------------------------------------------------------- generated code stays generated


@pytest.mark.parametrize("script", ["unasync.py", "gen_params.py"])
def test_generated_files_are_current(script):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), "--check"], capture_output=True, text=True, cwd=ROOT
    )
    assert proc.returncode == 0, proc.stderr
