"""Remember each fetch's ad ids so a repeat fetch can say what changed.

One JSON file in ~/.config/proxy-ads-mcp/ maps (advertiser, filters) to the ad ids of the
last fetch. A fetch 24h+ later reports which ads are new and how many dropped out; repeat
fetches inside 24h (pagination, retries, follow-up questions) keep the older baseline and
report nothing. Best-effort: a storage failure never touches the tool result.
"""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

HISTORY_FILE = Path.home() / ".config" / "proxy-ads-mcp" / "facebook-ads-library-mcp-history.json"
MIN_GAP = timedelta(hours=24)
RECENT_DAYS = 7


def record(key: str, ids: List[str], now: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
    """Store this fetch's ids under key. Returns None on a first fetch, {"since"} inside 24h of the
    baseline, or {"since", "new", "dropped"} against a baseline 24h+ old."""
    now = now or datetime.now(timezone.utc)
    try:
        history = json.loads(HISTORY_FILE.read_text())
    except (OSError, ValueError):
        history = {}
    prev = history.get(key)
    if prev and now - datetime.fromisoformat(prev["at"]) < MIN_GAP:
        return {"since": prev["at"][:10]}  # keep the older baseline
    if prev:
        seen = set(prev["ids"])
        result = {"since": prev["at"][:10], "new": [i for i in ids if i not in seen], "dropped": len(seen - set(ids))}
    else:
        result = None
    history[key] = {"at": now.isoformat(), "ids": ids}
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        HISTORY_FILE.write_text(json.dumps(history))
    except OSError:
        pass
    return result


def launched_recently(ads: List[Dict[str, Any]], now: Optional[datetime] = None) -> List[str]:
    """Ad ids whose start_date is inside the last 7 days. Works on a first fetch too."""
    today = (now or datetime.now(timezone.utc)).date()
    out = []
    for ad in ads:
        start = ad.get("start_date")
        try:
            if start and (today - date.fromisoformat(start[:10])).days <= RECENT_DAYS:
                out.append(ad["ad_id"])
        except ValueError:
            continue
    return list(dict.fromkeys(out))


def changes(key: str, ads: List[Dict[str, Any]], now: Optional[datetime] = None) -> Dict[str, Any]:
    """The changes block for a tool result: diff vs the last fetch plus recent launches."""
    ids = list(dict.fromkeys(a["ad_id"] for a in ads if a.get("ad_id")))
    diff = record(key, ids, now)
    out: Dict[str, Any] = {"launched_last_7d": launched_recently(ads, now)}
    if diff is None:
        out["note"] = "First fetch with these filters: baseline saved. Fetch again 24h+ later to see what changed."
    elif "new" not in diff:
        out["note"] = f"Baseline from {diff['since']} is under 24h old; changes show once 24h have passed."
    else:
        out.update({
            "since_last_fetch": diff["since"],
            "new_since_last_fetch": diff["new"],
            "dropped_since_last_fetch": diff["dropped"],
        })
    return out
