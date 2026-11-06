"""The HTTP engine: auth, retries, timeouts, error mapping and response parsing.

Rules, all deliberate and shared with the TypeScript SDK:

* **Auth is** ``X-API-Key``. ``Authorization: Bearer`` is only tried as a session JWT by the API.
* **POST is never retried by default.** GET, PUT, PATCH and DELETE retry on 408/429/5xx and on
  connection errors, honouring ``Retry-After``. A POST retried after an ambiguous 502 can dial a
  person twice; opt in per request with ``request_options={"max_retries": n}``.
* **Redirects are never followed.** The API does not redirect; following one could re-send the
  API key to wherever ``Location`` points. A 3xx raises :class:`APIError`.
* **A multipart upload is never retried**, even on request: its parts may be one-shot streams.
"""

from __future__ import annotations

import asyncio
import email.utils
import json
import platform
import random
import time
import warnings
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Type, TypeVar

import httpx
from pydantic import BaseModel, TypeAdapter, ValidationError
from typing_extensions import TypedDict

from dialgem._errors import APIConnectionError, APIError, APITimeoutError, DialgemError
from dialgem._pagination import AsyncPaginator, PageData, SyncPage
from dialgem._version import VERSION

BASE_URL = "https://api.dialgem.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_MAX_RETRIES = 2
MAX_RETRY_DELAY = 60.0
_RETRYABLE_METHODS = frozenset({"GET", "PUT", "PATCH", "DELETE"})

T = TypeVar("T")


class RequestOptions(TypedDict, total=False):
    """Per-request overrides, accepted as ``request_options=`` by every resource method."""

    #: Seconds before an attempt is abandoned. Applies per attempt, not across retries.
    timeout: float
    #: Retries on 408/429/5xx and connection errors. POST defaults to 0; set it to opt in.
    max_retries: int
    #: Extra headers for this request only.
    headers: Dict[str, str]


Query = Mapping[str, Any]
CastTo = Any


# --------------------------------------------------------------------------- shared helpers


def _user_agent() -> str:
    return f"dialgem-sdk-python/{VERSION} python/{platform.python_version()}"


def _build_headers(
    api_key: str, default_headers: Mapping[str, str], extra: Optional[Mapping[str, str]], has_json_body: bool
) -> Dict[str, str]:
    # Merged case-insensitively, later layers winning, so a caller's ``x-api-key`` replaces ours
    # instead of being sent alongside it.
    merged: Dict[str, Tuple[str, str]] = {}

    def layer(headers: Optional[Mapping[str, str]]) -> None:
        for name, value in (headers or {}).items():
            merged[name.lower()] = (name, value)

    layer({"Accept": "application/json", "X-API-Key": api_key, "User-Agent": _user_agent()})
    layer(default_headers)
    layer(extra)
    if has_json_body:
        layer({"Content-Type": "application/json"})
    return dict(merged.values())


def _clean_query(query: Optional[Query]) -> Optional[List[Tuple[str, str]]]:
    """``None`` values are dropped; lists repeat the parameter; booleans are ``true``/``false``."""
    if not query:
        return None
    pairs: List[Tuple[str, str]] = []
    for key, value in query.items():
        if value is None:
            continue
        for item in value if isinstance(value, (list, tuple)) else [value]:
            pairs.append((key, "true" if item is True else "false" if item is False else str(item)))
    return pairs


def _clean_body(body: Optional[Mapping[str, Any]]) -> Optional[Dict[str, Any]]:
    return None if body is None else dict(body)


def _is_retryable_status(status: int) -> bool:
    # Not 409: the API's 409s are real conflicts, which a retry would only repeat.
    return status in (408, 429) or status >= 500


def _backoff(attempt: int) -> float:
    base = min(0.5 * 2**attempt, 8.0)
    return base * (1 - random.random() * 0.25)


def _retry_after(headers: Mapping[str, str]) -> Optional[float]:
    ms = headers.get("retry-after-ms")
    if ms:
        try:
            value = float(ms) / 1000
            if value > 0:
                return min(value, MAX_RETRY_DELAY)
        except ValueError:
            pass
    raw = headers.get("retry-after")
    if not raw:
        return None
    try:
        seconds = float(raw)
        if seconds >= 0:
            return min(seconds, MAX_RETRY_DELAY)
    except ValueError:
        pass
    parsed = email.utils.parsedate_to_datetime(raw) if raw else None
    if parsed is not None:
        return min(max(parsed.timestamp() - time.time(), 0.0), MAX_RETRY_DELAY)
    return None


def _validate_timeout(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise DialgemError(f"`timeout` must be a positive number of seconds, got {value!r}.")
    return float(value)


def _validate_retries(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DialgemError(f"`max_retries` must be a non-negative integer, got {value!r}.")
    return value


def _parse_success(response: httpx.Response) -> Any:
    text = response.text
    if response.status_code == 204 or not text.strip():
        return None
    try:
        return json.loads(text)
    except ValueError as exc:
        raise DialgemError(
            f"Expected a JSON response (status {response.status_code}) but could not parse it: {exc}"
        ) from exc


def _parse_error_body(response: httpx.Response) -> Any:
    text = response.text
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        return text


_adapters: Dict[Any, TypeAdapter[Any]] = {}
_warned: Set[str] = set()


def _adapter(cast_to: Any) -> TypeAdapter[Any]:
    try:
        return _adapters[cast_to]
    except KeyError:
        return _adapters.setdefault(cast_to, TypeAdapter(cast_to))
    except TypeError:  # unhashable annotation
        return TypeAdapter(cast_to)


def cast_response(data: Any, cast_to: CastTo) -> Any:
    """Turn parsed JSON into ``cast_to``.

    The API adds fields over time, so a response that does not fit the model exactly (a field
    changed type, a required one went missing) must not take a customer's integration down. On a
    validation failure the data is returned *unvalidated* in the model (``model_construct``) and
    a :class:`UserWarning` is issued once per model, so the drift is visible but not fatal.
    """
    if cast_to is None or data is None:
        return data
    if cast_to is dict or cast_to is Any:
        return data
    try:
        return _adapter(cast_to).validate_python(data)
    except ValidationError as exc:
        name = getattr(cast_to, "__name__", str(cast_to))
        if name not in _warned:
            _warned.add(name)
            warnings.warn(
                f"dialgem: a {name} response did not match the SDK's model ({exc.error_count()} problem(s)); "
                "returning it unvalidated. Update the SDK, and report this if it persists.",
                UserWarning,
                stacklevel=2,
            )
        return _construct(cast_to, data)


def _construct(cast_to: Any, data: Any) -> Any:
    origin = getattr(cast_to, "__origin__", None)
    if origin in (list, List) and isinstance(data, list):
        (inner,) = cast_to.__args__
        return [_construct(inner, item) for item in data]
    if isinstance(cast_to, type) and issubclass(cast_to, BaseModel) and isinstance(data, dict):
        values = dict(data)
        for name, field in cast_to.model_fields.items():
            key = field.alias or name
            if key in values:
                values[key] = _construct_field(field.annotation, values[key])
        return cast_to.model_construct(**values)
    return data


def _model_in(annotation: Any) -> Tuple[Any, bool]:
    """Find a response model inside ``Optional[M]`` / ``List[M]`` / ``Optional[List[M]]``: (model, is_list)."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation, False
    for arg in getattr(annotation, "__args__", ()) or ():
        if arg is type(None):
            continue
        model, is_list = _model_in(arg)
        if model is not None:
            return model, is_list or getattr(annotation, "__origin__", None) in (list, List)
    return None, False


def _construct_field(annotation: Any, value: Any) -> Any:
    """Give a nested object its model type even when the parent had to be built unvalidated."""
    model, is_list = _model_in(annotation)
    if model is None:
        return value
    if is_list and isinstance(value, list):
        return [_build(model, item) for item in value]
    return _build(model, value)


def _build(model: Any, value: Any) -> Any:
    if not isinstance(value, dict):
        return value
    try:
        return model.model_validate(value)
    except ValidationError:
        return _construct(model, value)


class _Config:
    """Everything both clients need to build a request."""

    def __init__(
        self,
        api_key: str,
        timeout: float,
        max_retries: int,
        default_headers: Optional[Mapping[str, str]],
    ) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.default_headers = dict(default_headers or {})
        self.base_url = BASE_URL

    def url(self, path: str) -> str:
        return f"{self.base_url}{path if path.startswith('/') else '/' + path}"

    def retries_for(self, method: str, options: Optional[RequestOptions], is_form: bool) -> int:
        if is_form:
            return 0
        if options and "max_retries" in options:
            return _validate_retries(options["max_retries"])
        return self.max_retries if method in _RETRYABLE_METHODS else 0


def _raise_for_status(response: httpx.Response) -> None:
    raise APIError.from_response(
        response.status_code, _parse_error_body(response), response.reason_phrase, response.headers
    )


def _connection_error(exc: Exception, timeout: float) -> APIConnectionError:
    if isinstance(exc, httpx.TimeoutException):
        return APITimeoutError(f"Request timed out after {timeout:g}s.")
    return APIConnectionError(f"Connection error: {exc}")


# --------------------------------------------------------------------------- sync


class SyncAPIClient:
    def __init__(
        self,
        *,
        api_key: str,
        timeout: float,
        max_retries: int,
        default_headers: Optional[Mapping[str, str]],
        http_client: Optional[httpx.Client],
    ) -> None:
        self._cfg = _Config(api_key, timeout, max_retries, default_headers)
        self._owns_client = http_client is None
        self._http = http_client or httpx.Client(follow_redirects=False)

    def close(self) -> None:
        if self._owns_client:
            self._http.close()

    # verbs ------------------------------------------------------------------------------------

    def get(self, path: str, *, query: Optional[Query] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return self.request("GET", path, query=query, cast_to=cast_to, options=options)

    def post(self, path: str, *, body: Optional[Mapping[str, Any]] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return self.request("POST", path, body=body, cast_to=cast_to, options=options)

    def post_form(self, path: str, *, data: Mapping[str, str], files: List[Tuple[str, Any]], cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return self.request("POST", path, form=(data, files), cast_to=cast_to, options=options)

    def put(self, path: str, *, body: Optional[Mapping[str, Any]] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return self.request("PUT", path, body=body, cast_to=cast_to, options=options)

    def patch(self, path: str, *, body: Optional[Mapping[str, Any]] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return self.request("PATCH", path, body=body, cast_to=cast_to, options=options)

    def delete(self, path: str, *, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return self.request("DELETE", path, cast_to=cast_to, options=options)

    def paginate(
        self,
        path: str,
        *,
        query: Optional[Query],
        cast_to: Type[Any],
        items_key: str,
        cursor_param: str,
        next_key: str,
        options: Optional[RequestOptions] = None,
    ) -> SyncPage[Any]:
        def fetch(cursor: Optional[str]) -> PageData[Any]:
            envelope = self.get(path, query={**(query or {}), cursor_param: cursor}, options=options)
            items = [cast_response(item, cast_to) for item in envelope.get(items_key) or []]
            token = envelope.get(next_key)
            return PageData(items, bool(envelope.get("has_more", token is not None)), token)

        return SyncPage(fetch(None), fetch)

    # engine -----------------------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Query] = None,
        body: Optional[Mapping[str, Any]] = None,
        form: Optional[Tuple[Mapping[str, str], List[Tuple[str, Any]]]] = None,
        cast_to: CastTo = None,
        options: Optional[RequestOptions] = None,
    ) -> Any:
        cfg = self._cfg
        timeout = _validate_timeout((options or {}).get("timeout", cfg.timeout))
        retries = cfg.retries_for(method, options, form is not None)
        has_json = body is not None
        headers = _build_headers(cfg.api_key, cfg.default_headers, (options or {}).get("headers"), has_json)
        kwargs: Dict[str, Any] = {"params": _clean_query(query), "headers": headers}
        if has_json:
            kwargs["content"] = json.dumps(_clean_body(body)).encode("utf-8")
        if form is not None:
            kwargs["data"], kwargs["files"] = form
        for attempt in range(retries + 1):
            left = retries - attempt
            try:
                response = self._http.request(
                    method, cfg.url(path), timeout=httpx.Timeout(timeout), follow_redirects=False, **kwargs
                )
            except httpx.HTTPError as exc:
                if left > 0:
                    time.sleep(_backoff(attempt))
                    continue
                raise _connection_error(exc, timeout) from exc
            if 200 <= response.status_code < 300:
                return cast_response(_parse_success(response), cast_to)
            if left > 0 and _is_retryable_status(response.status_code):
                time.sleep(_retry_after(response.headers) or _backoff(attempt))
                continue
            _raise_for_status(response)
        raise AssertionError("unreachable")  # pragma: no cover


# --------------------------------------------------------------------------- async


class AsyncAPIClient:
    def __init__(
        self,
        *,
        api_key: str,
        timeout: float,
        max_retries: int,
        default_headers: Optional[Mapping[str, str]],
        http_client: Optional[httpx.AsyncClient],
    ) -> None:
        self._cfg = _Config(api_key, timeout, max_retries, default_headers)
        self._owns_client = http_client is None
        self._http = http_client or httpx.AsyncClient(follow_redirects=False)

    async def aclose(self) -> None:
        if self._owns_client:
            await self._http.aclose()

    async def get(self, path: str, *, query: Optional[Query] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("GET", path, query=query, cast_to=cast_to, options=options)

    async def post(self, path: str, *, body: Optional[Mapping[str, Any]] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("POST", path, body=body, cast_to=cast_to, options=options)

    async def post_form(self, path: str, *, data: Mapping[str, str], files: List[Tuple[str, Any]], cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("POST", path, form=(data, files), cast_to=cast_to, options=options)

    async def put(self, path: str, *, body: Optional[Mapping[str, Any]] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("PUT", path, body=body, cast_to=cast_to, options=options)

    async def patch(self, path: str, *, body: Optional[Mapping[str, Any]] = None, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("PATCH", path, body=body, cast_to=cast_to, options=options)

    async def delete(self, path: str, *, cast_to: CastTo = None, options: Optional[RequestOptions] = None) -> Any:
        return await self.request("DELETE", path, cast_to=cast_to, options=options)

    def paginate(
        self,
        path: str,
        *,
        query: Optional[Query],
        cast_to: Type[Any],
        items_key: str,
        cursor_param: str,
        next_key: str,
        options: Optional[RequestOptions] = None,
    ) -> AsyncPaginator[Any]:
        async def fetch(cursor: Optional[str]) -> PageData[Any]:
            envelope = await self.get(path, query={**(query or {}), cursor_param: cursor}, options=options)
            items = [cast_response(item, cast_to) for item in envelope.get(items_key) or []]
            token = envelope.get(next_key)
            return PageData(items, bool(envelope.get("has_more", token is not None)), token)

        return AsyncPaginator(fetch)

    async def request(
        self,
        method: str,
        path: str,
        *,
        query: Optional[Query] = None,
        body: Optional[Mapping[str, Any]] = None,
        form: Optional[Tuple[Mapping[str, str], List[Tuple[str, Any]]]] = None,
        cast_to: CastTo = None,
        options: Optional[RequestOptions] = None,
    ) -> Any:
        cfg = self._cfg
        timeout = _validate_timeout((options or {}).get("timeout", cfg.timeout))
        retries = cfg.retries_for(method, options, form is not None)
        has_json = body is not None
        headers = _build_headers(cfg.api_key, cfg.default_headers, (options or {}).get("headers"), has_json)
        kwargs: Dict[str, Any] = {"params": _clean_query(query), "headers": headers}
        if has_json:
            kwargs["content"] = json.dumps(_clean_body(body)).encode("utf-8")
        if form is not None:
            kwargs["data"], kwargs["files"] = form
        for attempt in range(retries + 1):
            left = retries - attempt
            try:
                response = await self._http.request(
                    method, cfg.url(path), timeout=httpx.Timeout(timeout), follow_redirects=False, **kwargs
                )
            except httpx.HTTPError as exc:
                if left > 0:
                    await asyncio.sleep(_backoff(attempt))
                    continue
                raise _connection_error(exc, timeout) from exc
            if 200 <= response.status_code < 300:
                return cast_response(_parse_success(response), cast_to)
            if left > 0 and _is_retryable_status(response.status_code):
                await asyncio.sleep(_retry_after(response.headers) or _backoff(attempt))
                continue
            _raise_for_status(response)
        raise AssertionError("unreachable")  # pragma: no cover
