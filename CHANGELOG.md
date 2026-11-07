# Changelog

## 0.1.0b2

`phone_numbers.search(country=, type=, area_code=, contains=, limit=)` lists numbers that can be bought, with the monthly price, and `phone_numbers.buy(phone_number=, type=, nickname=)` buys one (sync and asyncio). **Buying spends the organization's credit**: the first month is debited when you buy and the rental renews monthly until the number is released; nothing is charged if the purchase fails. The deployment must have number purchasing switched on, or `search` raises `NotFoundError` (`number_purchase_disabled`). A number looked up with `phone_numbers.retrieve` now carries `own_twilio`. Connecting your own Twilio account and importing its numbers is a dashboard feature, not in the SDK, because it handles your Twilio credentials.

## 0.1.0b1 (unreleased)

First release. Sync and asyncio clients covering the customer API: agents (functions, knowledge, MCP
servers, versions), calls, web calls, phone numbers, voices, templates, contacts and lists, simulations and
sessions; plus webhook signature verification. Campaigns, webhook endpoint management, usage, billing,
analytics, and contact erasure / do-not-call are deliberately not in the SDK (see `docs/api-surface.md`).

`chats` (create, list, retrieve, update, delete, send_message, end, rerun_analysis), `calls.rerun_analysis`, `contacts.retrieve_by_phone` and `api_key.retrieve` need the matching routes in the service.

``sessions.say(session_id, text=..., interrupt=...)`` and ``sessions.release(session_id)`` make the agent speak a line on a live call, and hand a taken-over call back. Off unless the deployment enables live control (``live_control_disabled``). Listening in and taking over run over a WebSocket this SDK does not wrap. ``sessions.update`` now reaches a call on any service instance.

`sessions.update(session_id, system_prompt=..., dynamic_variables=...)` changes a live call's prompt and/or variables from the agent's next turn. ``session_id`` is the session's id or the call's ``call_id``. Only that call changes and it is not saved.

`llms` (create, list, retrieve, update, delete) saves a prompt and model once; attach it with ``llm_id`` on ``agents.create`` / ``agents.update``. Attaching copies the values; later edits or deletion do not change the agent, and ``llm_id`` cannot be sent with the fields it carries.

`agents.mcp_servers.list_tools(agent_id, server_id)` returns the server's tools with descriptions and argument schemas, from a live connection; it stores nothing.

`flows` (create, list, retrieve, update, delete) saves a conversation flow once; attach it with ``flow_id`` on ``agents.create`` / ``agents.update``. Attaching copies the flow, so later edits or deletion do not change the agent.

Chats are billed per agent reply (a spent balance is a 402 `insufficient_credit`) and `Chat.chat_cost` shows the spend (`None` for a team-member session). `chat_started`, `chat_ended` and `chat_analyzed` webhook events parse to `ChatStartedEvent`, `ChatEndedEvent` and `ChatAnalyzedEvent` (they carry `chat_id` and `chat`, not `call_id`).

Mirrors the surface and the safety rules of `@dialgem/sdk` 0.1.0-beta.1 (see `docs/api-surface.md`).
