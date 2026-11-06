from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote

from dialgem._errors import DialgemError

if TYPE_CHECKING:
    from dialgem._base_client import AsyncAPIClient, SyncAPIClient


class Resource:
    _client: SyncAPIClient

    def __init__(self, client: SyncAPIClient) -> None:
        self._client = client


class AsyncResource:
    _client: AsyncAPIClient

    def __init__(self, client: AsyncAPIClient) -> None:
        self._client = client


def pid(value: object) -> str:
    """Percent-encode one path segment, refusing an empty id (``/v1/agents/`` would list, not fetch)."""
    if not isinstance(value, str) or not value.strip():
        raise DialgemError(f"Expected a non-empty id, got {value!r}.")
    return quote(value, safe="")
