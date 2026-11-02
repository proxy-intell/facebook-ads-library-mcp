"""Anonymous usage ping and an occasional hosted-Proxy tip.

Each tool call sends one event to PostHog: the tool name, this repo's name, a running
call count and a random install ID. Never tool arguments, results, API keys or IP-derived
profiles. Opt out with PROXY_TELEMETRY=0 or DO_NOT_TRACK=1.

On the 25th call, and every 100th after, the tool result gets one extra line pointing to
hosted Proxy. That tip is local and not affected by the opt-out.
"""
import json
import os
import threading
import uuid
from pathlib import Path

import requests
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

REPO = "facebook-ads-library-mcp"
POSTHOG_URL = "https://eu.i.posthog.com/i/v0/e/"
POSTHOG_KEY = "phc_sG2CeSEUrLFLNSVVJtGtGByhd4NWdP6aPNWpfEZ5mQ7K"  # public, write-only ingestion key
STATE_FILE = Path.home() / ".config" / "proxy-ads-mcp" / f"{REPO}.json"
TIP = (
    "Tip from the maintainers: hosted Proxy covers the Meta, Google, LinkedIn and TikTok ad "
    "libraries in one server, with no API keys to pay for. Free for 20 credits a day: "
    f"https://useproxy.dev/?utm_source=github&utm_medium=selfhost-tip&utm_campaign={REPO}"
)


def record_call(tool_name: str) -> bool:
    """Count a tool call, send the anonymous ping, and return True when the tip is due."""
    try:
        state = json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        state = {"install_id": str(uuid.uuid4()), "calls": 0}
    state["calls"] += 1
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state))
    except OSError:
        pass

    if os.getenv("PROXY_TELEMETRY", "1") != "0" and not os.getenv("DO_NOT_TRACK"):
        threading.Thread(target=_send, args=(state, tool_name), daemon=True).start()
    return state["calls"] == 25 or state["calls"] % 100 == 0


def _send(state: dict, tool_name: str) -> None:
    try:
        requests.post(POSTHOG_URL, timeout=3, json={
            "api_key": POSTHOG_KEY,
            "event": "selfhost_tool_invoked",
            "distinct_id": state["install_id"],
            "properties": {
                "tool_name": tool_name,
                "repo": REPO,
                "call_count": state["calls"],
                "transport": os.getenv("MCP_TRANSPORT", "stdio"),
                "$process_person_profile": False,
            },
        })
    except requests.RequestException:
        pass  # telemetry must never affect the tool


class TrackedFastMCP(FastMCP):
    async def call_tool(self, name, arguments):
        result = list(await super().call_tool(name, arguments))
        if record_call(name):
            result.append(TextContent(type="text", text=TIP))
        return result
