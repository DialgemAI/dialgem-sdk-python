"""Receive and verify Dialgem webhooks with FastAPI.

    pip install fastapi uvicorn dialgem
    DIALGEM_WEBHOOK_SECRET=whsec_... uvicorn examples.webhook_fastapi:app
"""

import os

from fastapi import FastAPI, Request, Response

from dialgem import WebhookVerificationError, webhooks

app = FastAPI()
SECRET = os.environ["DIALGEM_WEBHOOK_SECRET"]


@app.post("/dialgem")
async def receive(request: Request) -> Response:
    raw = await request.body()  # the raw bytes: do not parse and re-serialize before verifying
    try:
        event = webhooks.construct_event(raw, request.headers.get("x-dialgem-signature"), SECRET)
    except WebhookVerificationError:
        return Response(status_code=400)

    if event.event == "call_ended":
        print("call ended:", event.call.id, event.call.duration_ms)
    elif event.event == "call_analyzed":
        print("analysis ready for", event.call_id)
    return Response(status_code=204)
