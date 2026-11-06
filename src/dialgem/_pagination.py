"""Pages.

``calls.list()`` and friends return a page that is also an iterator over *every* item, fetching
further pages as it goes::

    for call in dialgem.calls.list(limit=50):        # all pages
        ...
    page = dialgem.calls.list(limit=50)              # or one page at a time
    page.data, page.has_next_page(), page.get_next_page()

On the async client ``list()`` can be awaited for one page, or iterated with ``async for``.
"""

from __future__ import annotations

from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Generator,
    Generic,
    Iterator,
    List,
    Optional,
    TypeVar,
)

from dialgem._errors import DialgemError

T = TypeVar("T")


class PageData(Generic[T]):
    __slots__ = ("data", "has_more", "pagination_key")

    def __init__(self, data: List[T], has_more: bool, pagination_key: Optional[str]) -> None:
        self.data = data
        self.has_more = has_more
        self.pagination_key = pagination_key


class SyncPage(Generic[T]):
    """One page of results; iterating it continues across pages."""

    def __init__(self, page: PageData[T], fetch: Callable[[Optional[str]], PageData[T]]) -> None:
        self.data: List[T] = page.data
        self.has_more = page.has_more
        self.pagination_key = page.pagination_key
        self._fetch = fetch

    def has_next_page(self) -> bool:
        return self.has_more and self.pagination_key is not None

    def get_next_page(self) -> SyncPage[T]:
        if not self.has_next_page():
            raise DialgemError("No next page; check has_next_page() first.")
        return SyncPage(self._fetch(self.pagination_key), self._fetch)

    def iter_pages(self) -> Iterator[SyncPage[T]]:
        page = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = page.get_next_page()

    def __iter__(self) -> Iterator[T]:
        for page in self.iter_pages():
            yield from page.data

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"SyncPage(items={len(self.data)}, has_more={self.has_more})"


class AsyncPage(Generic[T]):
    """One page of results; ``async for`` over it continues across pages."""

    def __init__(self, page: PageData[T], fetch: Callable[[Optional[str]], Awaitable[PageData[T]]]) -> None:
        self.data: List[T] = page.data
        self.has_more = page.has_more
        self.pagination_key = page.pagination_key
        self._fetch = fetch

    def has_next_page(self) -> bool:
        return self.has_more and self.pagination_key is not None

    async def get_next_page(self) -> AsyncPage[T]:
        if not self.has_next_page():
            raise DialgemError("No next page; check has_next_page() first.")
        return AsyncPage(await self._fetch(self.pagination_key), self._fetch)

    async def iter_pages(self) -> AsyncIterator[AsyncPage[T]]:
        page = self
        while True:
            yield page
            if not page.has_next_page():
                return
            page = await page.get_next_page()

    async def __aiter__(self) -> AsyncIterator[T]:
        async for page in self.iter_pages():
            for item in page.data:
                yield item

    def __repr__(self) -> str:
        return f"AsyncPage(items={len(self.data)}, has_more={self.has_more})"


class AsyncPaginator(Generic[T]):
    """What the async ``list()`` methods return: ``await`` it for a page, or ``async for`` over it."""

    def __init__(self, fetch: Callable[[Optional[str]], Awaitable[PageData[T]]]) -> None:
        self._fetch = fetch

    async def _load(self) -> AsyncPage[T]:
        return AsyncPage(await self._fetch(None), self._fetch)

    def __await__(self) -> Generator[Any, None, AsyncPage[T]]:
        return self._load().__await__()

    async def __aiter__(self) -> AsyncIterator[T]:
        page = await self._load()
        async for item in page:
            yield item
