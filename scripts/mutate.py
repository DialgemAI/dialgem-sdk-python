"""Mutation spot-check: break one rule at a time and confirm the suite notices.

    python scripts/mutate.py

Each mutation edits a source file in place, runs the tests, and restores the file. A mutation that the
suite does NOT catch is printed as SURVIVED and the script exits 1: either the rule is untested, or
the mutation is equivalent and should be justified here.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "src" / "dialgem"

MUTATIONS = [
    ("POST becomes retryable", "_base_client.py", '{"GET", "PUT", "PATCH", "DELETE"}', '{"GET", "PUT", "PATCH", "DELETE", "POST"}'),
    ("409 becomes retryable", "_base_client.py", "status in (408, 429) or status >= 500", "status in (408, 409, 429) or status >= 500"),
    ("auth moves to Bearer", "_base_client.py", '"X-API-Key": api_key', '"Authorization": "Bearer " + api_key'),
    ("redirects are followed (per request)", "_base_client.py", "timeout=httpx.Timeout(timeout), follow_redirects=False, **kwargs\n                )\n            except httpx.HTTPError as exc:\n                if left > 0:\n                    time.sleep", "timeout=httpx.Timeout(timeout), follow_redirects=True, **kwargs\n                )\n            except httpx.HTTPError as exc:\n                if left > 0:\n                    time.sleep"),
    ("Retry-After ignored", "_base_client.py", "time.sleep(_retry_after(response.headers) or _backoff(attempt))", "time.sleep(_backoff(attempt))"),
    ("Retry-After uncapped", "_base_client.py", "return min(seconds, MAX_RETRY_DELAY)", "return seconds"),
    ("multipart becomes retryable", "_base_client.py", "        if is_form:\n            return 0\n", ""),
    ("None query values are sent", "_base_client.py", "        if value is None:\n            continue\n        for item", "        for item"),
    ("webhook compares with ==", "_webhooks.py", "hmac.compare_digest(expected, received)", "True"),
    ("webhook ignores the timestamp window", "_webhooks.py", "if abs(now - int(timestamp)) > tolerance_ms:", "if False:"),
    ("webhook signs the body only", "_webhooks.py", "_to_bytes(payload) + timestamp.encode(\"ascii\")", "_to_bytes(payload)"),
    ("empty ids are accepted", "_resource.py", "if not isinstance(value, str) or not value.strip():", "if not isinstance(value, str):"),
    ("ids are not percent-encoded", "_resource.py", 'return quote(value, safe="")', "return value"),
    ("base_url becomes an option", "_client.py", "if base_url is not None:", "if False:"),
    ("outbound call path typo", "resources/calls.py", '"/v1/calls/outbound"', '"/v1/calls/outbond"'),
    ("agents path typo", "resources/agents.py", 'f"/v1/agents/{pid(agent_id)}/mcp-servers/{pid(server_id)}/test"', 'f"/v1/agents/{pid(agent_id)}/mcp-servers/{pid(server_id)}/tst"'),
    ("pagination ignores the cursor", "_base_client.py", "query={**(query or {}), cursor_param: cursor}, options=options)\n            items = [cast_response(item, cast_to) for item in envelope.get(items_key) or []]\n            token = envelope.get(next_key)\n            return PageData(items, bool(envelope.get(\"has_more\", token is not None)), token)\n\n        return SyncPage", "query={**(query or {})}, options=options)\n            items = [cast_response(item, cast_to) for item in envelope.get(items_key) or []]\n            token = envelope.get(next_key)\n            return PageData(items, bool(envelope.get(\"has_more\", token is not None)), token)\n\n        return SyncPage"),
    ("voice clone skips consent", "resources/catalog.py", "if consent_confirmed is not True:", "if False:"),
]


def run_tests() -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider"], cwd=ROOT, capture_output=True, text=True
    )
    return proc.returncode == 0


def main() -> int:
    if not run_tests():
        print("baseline is red; fix that first")
        return 2
    survived = []
    for label, rel, old, new in MUTATIONS:
        path = PKG / rel
        original = path.read_text(encoding="utf8")
        if original.count(old) != 1:
            print(f"SKIPPED  {label}: pattern occurs {original.count(old)} times in {rel}")
            survived.append(label)
            continue
        try:
            path.write_text(original.replace(old, new), encoding="utf8", newline="")
            if rel.startswith("resources/"):
                subprocess.run([sys.executable, str(ROOT / "scripts" / "unasync.py")], cwd=ROOT, capture_output=True)
            caught = not run_tests()
        finally:
            path.write_text(original, encoding="utf8", newline="")
            if rel.startswith("resources/"):
                subprocess.run([sys.executable, str(ROOT / "scripts" / "unasync.py")], cwd=ROOT, capture_output=True)
        print(("killed   " if caught else "SURVIVED ") + label)
        if not caught:
            survived.append(label)
    print(f"\n{len(MUTATIONS) - len(survived)}/{len(MUTATIONS)} killed")
    return 1 if survived else 0


if __name__ == "__main__":
    raise SystemExit(main())
