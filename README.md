<div align="center">

# Dialgem

**The official Python SDK for the [Dialgem](https://dialgem.com) voice AI API.**

Build voice agents, put them on phone numbers, place calls, steer them live, and read transcripts, all from your backend.

[![PyPI](https://img.shields.io/pypi/v/dialgem?color=3775A9&logo=pypi&logoColor=white)](https://pypi.org/project/dialgem/)
[![Python](https://img.shields.io/pypi/pyversions/dialgem?logo=python&logoColor=white)](https://pypi.org/project/dialgem/)
[![CI](https://img.shields.io/github/actions/workflow/status/DialgemAI/dialgem-sdk-python/ci.yml?branch=main&label=CI&logo=github)](https://github.com/DialgemAI/dialgem-sdk-python/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Typed](https://img.shields.io/badge/typing-typed-2a6db2)](https://peps.python.org/pep-0561/)
[![Stars](https://img.shields.io/github/stars/DialgemAI/dialgem-sdk-python?style=flat&logo=github)](https://github.com/DialgemAI/dialgem-sdk-python/stargazers)

[Website](https://dialgem.com) · [Issues](https://github.com/DialgemAI/dialgem-sdk-python/issues) · [Changelog](CHANGELOG.md) · [API surface](docs/api-surface.md)

</div>

---

```python
from dialgem import Dialgem

dialgem = Dialgem()  # reads DIALGEM_API_KEY

agent = dialgem.agents.create(name="Front desk", system_prompt="You answer for Acme Dental.")
call = dialgem.calls.create_phone_call(to="+14155550123", from_="+14155550100", agent_id=agent.id)
```

## Why this SDK

- **Sync and async, one surface.** `Dialgem` and `AsyncDialgem` expose the same methods.
- **Typed end to end.** Request bodies are `TypedDict`s generated from the API schema; responses are pydantic v2 models, so your editor and `mypy` know every field.
- **Safe by default.** `POST` is never retried (a retry could ring someone twice), `GET`/`PUT`/`PATCH`/`DELETE` retry with backoff and `Retry-After`, and an API change never crashes your integration: unknown or mismatched fields come back as-is with one warning.
- **Everything a backend needs.** Agents (with tools, knowledge and MCP servers), phone numbers, calls and chats, saved flows and LLMs, contacts, simulations, web calls, live call control, and webhook signature verification.
- **Small.** Python 3.10+, three dependencies: `httpx`, `pydantic`, `typing_extensions`.
- **Server-side only.** An organization API key grants full access to your organization. To let a visitor talk to an agent from a web page, see [Web calls](#web-calls).

## Contents

[Install](#install) · [Quickstart](#quickstart) · [Async](#async) · [Recipes](#recipes) · [Live call control](#live-call-control) · [Errors](#errors) · [Retries](#retries) · [Responses](#responses) · [Development](#development) · [License](#license)

> Which routes this SDK can and cannot reach, and why: [docs/api-surface.md](docs/api-surface.md).

## Install

```sh
pip install dialgem
```

## Quickstart

Create an organization API key (`zk_…`) in the Dialgem dashboard and keep it in your server's environment.

```python
from dialgem import Dialgem

dialgem = Dialgem()  # reads DIALGEM_API_KEY

agent = dialgem.agents.create(
    name="Front desk",
    system_prompt="You are the front desk for {{business_name}}.",
    first_message="Thanks for calling, how can I help?",
    default_dynamic_variables={"business_name": "Acme Dental"},
)
```

| Option | Default | |
|---|---|---|
| `api_key` | `$DIALGEM_API_KEY` | Organization API key. |
| `timeout` | `60` | Seconds per attempt. |
| `max_retries` | `2` | See [Retries](#retries). |
| `default_headers` | `{}` | Sent with every request. |
| `http_client` | a new `httpx.Client` | Your own client (proxy, mTLS, instrumentation). You close it. |

Every method also takes `request_options={"timeout": 10, "max_retries": 0, "headers": {...}}` for that one request.

Field names are the API's own snake_case, passed as keyword arguments and sent exactly as written.

## Async

```python
import asyncio
from dialgem import AsyncDialgem

async def main():
    async with AsyncDialgem() as dialgem:
        agent = await dialgem.agents.create(name="Front desk")
        async for call in dialgem.calls.list(limit=50):   # walks every page
            print(call.id, call.call_status)

asyncio.run(main())
```

## Recipes

### Provision an agent on a phone number

```python
agent = dialgem.agents.create(name="Front desk", system_prompt="…")
number = dialgem.phone_numbers.create(phone_number="+14155550100")

dialgem.phone_numbers.update(
    number.id,
    inbound_agent_id=agent.id,
    set_inbound_agent=True,  # inbound_agent_id is ignored without this
)
```

Agents also have tools, knowledge and MCP servers:

```python
dialgem.agents.functions.create(
    agent.id,
    name="lookup_order",
    url="https://example.com/api/orders/lookup",
    parameters={"type": "object", "properties": {"order_id": {"type": "string"}}},
)
dialgem.agents.knowledge.create(agent.id, filename="faq.txt", content=faq_text)
```

### Place an outbound call

```python
call = dialgem.calls.create_phone_call(
    to="+14155550123",
    from_="+14155550100",          # `from_`: the wire name; must be a number on your organization
    agent_id=agent.id,
    metadata={"order": "A-1042"},
    dialgem_llm_dynamic_variables={"customer_name": "Ada"},
)
```

`create_phone_call` is a POST and is **not retried**. A retry after an ambiguous 502 could ring the person twice.

### List calls

```python
for call in dialgem.calls.list(agent_id=agent.id, start_after=1730000000000, limit=50):
    print(call.id, call.transcript_text)

page = dialgem.calls.list(limit=50)        # or one page at a time
page.data, page.has_next_page(), page.get_next_page()
```

### Web calls

Your **server** mints a one-use token; the page connects with `@dialgem/client` using that token alone, so your API key never reaches the browser.

```python
# once: allow the page's origin
dialgem.web_calls.update_settings(allowed_origins=["https://app.example.com"])

# per visitor, from your own endpoint
web_call = dialgem.web_calls.create(agent_id="AGENT_ID", metadata={"visitor": "v_123"})
return {"access_token": web_call.access_token}   # 60 seconds, single use
```

### Verify webhooks

Verify against the **raw request body** exactly as received. A body parsed and re-serialized no longer matches.

```python
from dialgem import webhooks, WebhookVerificationError

# FastAPI
@app.post("/dialgem")
async def hook(request: Request):
    body = await request.body()
    try:
        event = webhooks.construct_event(body, request.headers.get("x-dialgem-signature"), SECRET)
    except WebhookVerificationError:
        return Response(status_code=400)
    if event.event == "call_ended":
        print(event.call.id, event.call.duration_ms)
    return Response(status_code=204)
```

`construct_function_call` does the same for the requests Dialgem sends to your agent's custom functions. Signatures carry a timestamp and are rejected after five minutes (`tolerance_ms=`).

## Live call control

Steer a call while it is happening. `session_id` is the session's id from `sessions.list()` or the call's own `call_id`, and the call can be on any service instance.

```python
# Change this call's prompt or variables from the agent's next turn (not saved, only this call).
dialgem.sessions.update(call.id, dynamic_variables={"plan": "pro"})

# Make the agent say a line in its own voice; interrupt=True cuts in now.
dialgem.sessions.say(call.id, text="One moment while I check that.")

# Give a taken-over call back to the agent.
dialgem.sessions.release(call.id)
```

`say` and `release` are **off unless your deployment enables live control** (`PermissionDeniedError` with `err_code == "live_control_disabled"`), and are for owners, admins and API keys only. Listening in and taking a call over run over a WebSocket (`/v1/agent/sessions/{id}/live`), which this SDK does not wrap.

## Errors

```python
from dialgem import NotFoundError, APIError, APIConnectionError

try:
    dialgem.agents.retrieve("nope")
except NotFoundError as e:
    print(e.status, e.err_code, e.request_id)   # quote request_id to support
except APIError as e:
    print(e.status, e.issues)                   # e.g. 422 validation issues
except APIConnectionError:
    ...                                         # no response (APITimeoutError is a subclass)
```

`400 BadRequestError`, `401 AuthenticationError`, `403 PermissionDeniedError`, `404 NotFoundError`, `409 ConflictError`, `422 UnprocessableEntityError`, `429 RateLimitError`, `5xx InternalServerError`. All derive from `APIError` → `DialgemError`.

## Retries

GET, PUT, PATCH and DELETE retry up to `max_retries` times on 408, 429, 5xx and connection errors, with exponential backoff and jitter, honouring `Retry-After` / `Retry-After-Ms` (capped at 60 s). **POST is never retried** unless you pass `request_options={"max_retries": n}`. 409 is never retried. File uploads are never retried.

## Responses

Responses are pydantic models. Unknown fields are kept (as attributes and in `model.model_extra`), and `model.to_dict()` returns the JSON as the API sent it. If the API returns something that does not fit the SDK's model (a field changed type or went missing), the SDK returns it **unvalidated** and issues one `UserWarning` per model instead of raising, so an API change never takes your integration down. Upgrade the SDK when you see it.

## Development

```sh
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
pytest
mypy src && ruff check .
python scripts/unasync.py       # regenerate src/dialgem/aresources from src/dialgem/resources
python scripts/gen_params.py    # regenerate request types from openapi/openapi.json
python scripts/mutate.py        # mutation spot-check of the safety rules
```

`src/dialgem/aresources/` and `src/dialgem/types/params.py` are generated; edit the sync resources and the OpenAPI snapshot, never the generated files. CI fails if they are stale.

## License

Apache-2.0. Copyright 2026 Achroweb Solutions. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

---

<div align="center">

If this SDK saves you time, a ⭐ on [GitHub](https://github.com/DialgemAI/dialgem-sdk-python) helps other developers find it.

</div>
