"""Tip schedule and HTTP bearer guard. Run: python test_telemetry.py"""
import os
import tempfile
from pathlib import Path

os.environ["PROXY_TELEMETRY"] = "0"

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from src import telemetry
from src.http_server import require_bearer

telemetry.STATE_FILE = Path(tempfile.mkdtemp()) / "state.json"
tips = [n for n in range(1, 301) if telemetry.record_call("get_meta_ads")]
assert tips == [25, 100, 200, 300], tips
assert "made 101 calls" in telemetry.tip(101) and "$0.19" in telemetry.tip(101)
assert "useproxy.dev/me/selfhost-" in telemetry.tip(1)

inner = Starlette(routes=[Route("/mcp", lambda r: PlainTextResponse("ok"))])
client = TestClient(require_bearer(inner, "s3cret-token-1234567"))
assert client.get("/mcp").status_code == 401
assert client.get("/mcp", headers={"Authorization": "Bearer wrong"}).status_code == 401
assert client.get("/mcp", headers={"Authorization": "Bearer s3cret-token-1234567"}).text == "ok"
# The tip is appended to both result shapes FastMCP returns: content list, or (content, structured).
import asyncio
from mcp.server.fastmcp import FastMCP
telemetry.STATE_FILE.write_text('{"install_id": "t", "calls": 24}')
for shape in (["a"], (["a"], {"k": 1})):
    async def fake(self, name, arguments, shape=shape):
        return shape
    FastMCP.call_tool, original = fake, FastMCP.call_tool
    out = asyncio.run(telemetry.TrackedFastMCP("t").call_tool("x", {}))
    FastMCP.call_tool = original
    content = out[0] if isinstance(out, tuple) else out
    assert content[0] == "a" and "Tip from the maintainers" in content[-1].text, out
    assert not isinstance(shape, tuple) or out[1] == {"k": 1}
    telemetry.STATE_FILE.write_text('{"install_id": "t", "calls": 24}')

print("telemetry tests passed")
