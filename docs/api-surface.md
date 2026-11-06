# API surface: what each Dialgem SDK can reach

Dialgem ships three SDKs. They are deliberately not three views of the same thing: each is limited to
the routes its credential can actually use, and a contract test in each repo fails if that limit moves.

| SDK | Package | Runs in | Credential | Reaches |
|---|---|---|---|---|
| Server (TypeScript) | `@dialgem/sdk` | your backend | organization API key `zk_…` | the customer API |
| Server (Python) | `dialgem` | your backend | organization API key `zk_…` | the same customer API |
| Client | `@dialgem/client` | a web page | one-use call token | one call's WebSocket, nothing else |

## Server SDKs (`@dialgem/sdk`, `dialgem`)

**In.** Everything an organization API key can do, grouped as the API groups it:

| Resource | Routes |
|---|---|
| `agents` (+ `functions`, `knowledge`, `mcp_servers`, `versions`) | `/v1/agents/**` |
| `calls` | `/v1/calls`, `/v1/calls/{id}`, `/v1/calls/{id}/stop`, `/v1/calls/{id}/rerun-analysis`, `/v1/calls/outbound`, `/v1/calls/register` |
| `chats` | `/v1/chats/**` |
| `flows` | `/v1/flows/**` |
| `llms` | `/v1/llms/**` |
| `web_calls` | `/v1/calls/web`, `/v1/web-calls/settings` |
| `phone_numbers` | `/v1/phone-numbers/**` |
| `contacts` (+ `imports`), `contact_lists` | `/v1/contacts/**` (incl. `by-phone/{phone}`; not `erase-data` or `do-not-call`), `/v1/contact-lists/**` |
| `simulations` | `/v1/simulations/**` |
| `voices`, `extraction_models`, `flow_templates`, `prompt_templates` | `/v1/voices`, `/v1/models/extraction`, `/v1/flow-templates`, `/v1/prompt-templates` |
| `sessions`, `api_key` | `/v1/agent/sessions`, `/v1/api-key-info` |
| `webhooks` (local) | signature verification, no network |

**Out, and why.**

| Not exposed | Reason |
|---|---|
| `/v1/auth/**`, `/v1/mfa`, `/v1/sso`, passkeys, sessions | Dashboard sign-in. An API key is not a user. |
| `/v1/orgs/{slug}/**` (members, invitations, API keys, SIP trunks), `/v1/invitations`, `/scim/**` | Need a user `Membership`; an API key answers 403 `NOT_A_MEMBER`. Manage these in the dashboard. |
| `/v1/admin/**`, `/v1/internal/**` | Platform staff and service-to-service. |
| `/v1/gem/**` | The in-dashboard assistant. |
| `/v1/test/**`, `/v1/agent/call` (WebSocket) | Dashboard test sockets and the media socket. The media socket is what `@dialgem/client` is for. |
| `/v1/billing/**`, `/v1/usage` | Money is read and moved in the dashboard, with a human, not from a key. |
| `/v1/campaigns/**` | Campaigns are run from the dashboard. Dialling lists of people is a decision for a person, not an integration script. |
| `/v1/webhooks/**` (endpoints, deliveries, resend) | Webhook destinations are managed in the dashboard. The SDK only verifies signatures. |
| `/v1/analytics/**` | Reporting lives in the dashboard. |
| Contact `erase-data` and `do-not-call` | Privacy and compliance actions that must leave a human trail. |
| `/v1/audit-log`, `/v1/api-key-scopes` | Administrative; not part of the integration surface. |

**Rules every server SDK follows** (so the two behave the same):

1. Auth is `X-API-Key`. `Authorization: Bearer` is only tried as a session token.
2. The API address is fixed at `https://api.dialgem.com`. There is no `base_url` option.
3. POST is never retried unless the caller opts in per request. GET, PUT, PATCH and DELETE retry on 408/429/5xx and connection errors, honouring `Retry-After` (capped at 60 s). A retried `create_phone_call` after an ambiguous 502 would dial the person twice.
4. A 409 is a real conflict and is never retried.
5. Redirects are never followed; the API does not redirect, and following one could re-send the key elsewhere.
6. A multipart upload is never retried.
7. Field names are the API's own snake_case, sent exactly as written (`from_` on `create_phone_call` is the wire name).
8. Response models tolerate additions: unknown fields are kept, and a response that does not fit is returned unvalidated with one warning rather than raising.
9. A signed webhook is never dropped over a model mismatch.

## Client SDK (`@dialgem/client`)

The browser is untrusted. The SDK therefore holds **no API key and can call no REST route**. Its whole job:

1. Your backend calls `web_calls.create(agent_id=…)` and receives `{call_id, access_token}`.
2. The page gives `@dialgem/client` that token. The token is 60 seconds, single-use, bound to one call, one
   agent and the origins allowed when it was issued.
3. The client opens the call WebSocket with the token, streams the microphone (16 kHz mono PCM), plays the
   agent's audio, and surfaces events (`started`, `transcript`, `agent_speaking`, `interrupted`, `ended`, `error`).

The page cannot choose the agent, its prompt, its tools, or the call's metadata and variables; those are
fixed by your backend when it creates the call.

## How the limits are enforced

* **Python:** `tests/test_contract.py` replays every public method against a recording transport and asserts
  the `(method, path)` exists in `openapi/openapi.json` and does not start with a forbidden prefix.
  `tests/sdk_calls.py` must list every public method; the test fails if one is missing or stale.
* **TypeScript:** `tests/contract.test.ts` does the same against its copy of the snapshot.
* **The snapshot** is a filtered copy of the service's OpenAPI document (customer routes only). Refresh it with
  the sync script in the TypeScript repo, copy it here, then run `python scripts/gen_params.py`.
