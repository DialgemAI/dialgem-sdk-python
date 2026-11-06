from __future__ import annotations

import inspect
from typing import Any, Callable

import pytest

from dialgem import AsyncDialgem, Dialgem

BASE = "https://api.dialgem.com"


@pytest.fixture
def sync_client() -> Dialgem:
    return Dialgem(api_key="zk_test", max_retries=2)


@pytest.fixture
def async_client() -> AsyncDialgem:
    return AsyncDialgem(api_key="zk_test", max_retries=2)


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Retries must not slow the suite down; record what they would have waited."""
    waits: list[float] = []

    def fake_sleep(seconds: float) -> None:
        waits.append(seconds)

    async def fake_asleep(seconds: float) -> None:
        waits.append(seconds)

    monkeypatch.setattr("dialgem._base_client.time.sleep", fake_sleep)
    monkeypatch.setattr("dialgem._base_client.asyncio.sleep", fake_asleep)
    return waits


async def call(client: Any, fn: Callable[[Any], Any]) -> Any:
    """Invoke ``fn(client)`` on either client, awaiting when the client is async."""
    result = fn(client)
    if inspect.isawaitable(result):
        result = await result
    return result
