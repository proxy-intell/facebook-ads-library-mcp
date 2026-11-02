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

inner = Starlette(routes=[Route("/mcp", lambda r: PlainTextResponse("ok"))])
client = TestClient(require_bearer(inner, "s3cret-token-1234567"))
assert client.get("/mcp").status_code == 401
assert client.get("/mcp", headers={"Authorization": "Bearer wrong"}).status_code == 401
assert client.get("/mcp", headers={"Authorization": "Bearer s3cret-token-1234567"}).text == "ok"
print("telemetry tests passed")
