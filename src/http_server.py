"""Streamable HTTP mode for cloud deploys (Render, Railway, any Docker host).

Set MCP_TRANSPORT=http and MCP_AUTH_TOKEN. Every request must send
`Authorization: Bearer <MCP_AUTH_TOKEN>`, otherwise anyone who finds the URL
could spend your ScrapeCreators credits. The endpoint is /mcp on $PORT.
"""
import hmac
import os

import uvicorn


def require_bearer(app, token: str):
    expected = f"Bearer {token}".encode()

    async def guarded(scope, receive, send):
        # Lifespan scopes have no headers: pass them straight through.
        if scope["type"] == "http" and not hmac.compare_digest(dict(scope["headers"]).get(b"authorization", b""), expected):
            await send({"type": "http.response.start", "status": 401, "headers": [(b"content-type", b"text/plain")]})
            await send({"type": "http.response.body", "body": b"Missing or wrong Authorization: Bearer token"})
            return
        await app(scope, receive, send)

    return guarded


def run_http(mcp) -> None:
    token = os.getenv("MCP_AUTH_TOKEN", "")
    if len(token) < 16:
        raise SystemExit("HTTP mode needs MCP_AUTH_TOKEN (16+ characters), or anyone could spend your API credits.")
    uvicorn.run(require_bearer(mcp.streamable_http_app(), token), host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
