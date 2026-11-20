"""Tool behaviour through a real MCP client session, with ScrapeCreators stubbed. Run: python test_tools.py"""
import asyncio
import base64
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ["PROXY_TELEMETRY"] = "0"
os.environ["SCRAPECREATORS_API_KEY"] = "test"

import requests
from mcp.shared.memory import create_connected_server_and_client_session as connect

from src import ad_history, telemetry
from src.services import media_cache_service, scrapecreators_service

telemetry.STATE_FILE = Path(tempfile.mkdtemp()) / "state.json"
ad_history.HISTORY_FILE = Path(tempfile.mkdtemp()) / "history.json"
media_cache_service.image_cache.get_cached_image = lambda url: None
media_cache_service.image_cache.cache_image = lambda **kw: None
scrapecreators_service.time.sleep = lambda s: None

import mcp_server

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")
VIDEO_AD = {"ad_archive_id": "1", "page_id": "p1", "page_name": "Acme", "start_date": 1700000000,
            "snapshot": {"display_format": "VIDEO", "body": {"text": "hi"}, "videos": [{"video_sd_url": "http://v"}]}}


class Resp:
    def __init__(self, status, payload=None, content=b"", content_type="application/json"):
        self.status_code, self._payload, self.content = status, payload, content
        self.headers = {"content-type": content_type}

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


calls = []


def fake_get(url, headers=None, params=None, timeout=None):
    calls.append((url, dict(params or {})))
    if "search/ads" in url:
        first = sum("search/ads" in u for u, _ in calls) == 1
        return Resp(502) if first else Resp(200, {"searchResultsCount": 999, "searchResults": [VIDEO_AD], "cursor": None})
    if "company/ads" in url:
        return Resp(400, {"error": "bad page id"})
    return Resp(200, content=PNG, content_type="image/png")


requests.get = fake_get


async def main():
    async with connect(mcp_server.mcp._mcp_server) as c:
        tools = {t.name for t in (await c.list_tools()).tools}
        assert {"search_meta_ads_by_keyword", "get_playbook"} <= tools and "analyze_ad_videos_batch" not in tools, tools
        assert len((await c.list_prompts()).prompts) == 5

        r = await c.call_tool("get_playbook", {"job": "competitor watch"})
        assert r.content[0].text.startswith("PLAYBOOK: competitor_watch")

        # Keyword search: a 502 is retried once; "video" maps to upstream's enum; page fields always present.
        r = json.loads((await c.call_tool("search_meta_ads_by_keyword", {"query": "shoes", "media_type": "Video"})).content[0].text)
        assert r["success"] and r["count"] == 1 and r["total_matches"] == 999, r
        assert r["results"][0]["page_id"] == "p1" and r["results"][0]["page_name"] == "Acme"
        assert [p["media_type"] for u, p in calls if "search/ads" in u] == ["VIDEO", "VIDEO"]

        r = json.loads((await c.call_tool("search_meta_ads_by_keyword", {"query": "shoes", "sort_by": "impressions"})).content[0].text)
        assert not r["success"] and "total_impressions" in r["message"]

        # A failed lookup in a batch stays visible instead of reading as "no ads".
        r = json.loads((await c.call_tool("get_meta_ads", {"platform_ids": ["a", "b"]})).content[0].text)
        assert r["results"]["a"] == {"error": "400"} and r["batch_info"]["failed"] == 2 and "failed" in r["message"], r

        # The image comes back as an image block the model can see.
        r = await c.call_tool("analyze_ad_image", {"media_url": "http://img", "ad_id": "9"})
        assert [b.type for b in r.content] == ["text", "image"] and not r.isError
        assert "?id=9" in json.loads(r.content[0].text)["ad_library_url"]


asyncio.run(main())

# Diff: first fetch is a baseline, inside 24h keeps it, 24h+ later reports new and dropped.
t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
ads = lambda *ids: [{"ad_id": i, "start_date": "2026-10-01T00:00:00"} for i in ids]
assert "baseline saved" in ad_history.changes("k", ads("1", "2"), t0)["note"]
assert "under 24h" in ad_history.changes("k", ads("3"), t0 + timedelta(hours=2))["note"]
later = ad_history.changes("k", ads("2", "3"), t0 + timedelta(days=2))
assert later["new_since_last_fetch"] == ["3"] and later["dropped_since_last_fetch"] == 1 and later["since_last_fetch"] == "2026-11-01"
recent = [{"ad_id": "n", "start_date": "2026-11-05T10:00:00"}, {"ad_id": "o", "start_date": "2026-09-01T10:00:00"}]
assert ad_history.launched_recently(recent, t0 + timedelta(days=6)) == ["n"]

print("tool tests passed")
