# Changelog

v1.1.0 · Nov 20 · Facebook

## Keyword search, and what changed since last week

331 of you starred this repo, and video analysis had quietly stopped working. So we fixed it, then added the three things people ask for most.

### new
- **Search ads by keyword:** `search_meta_ads_by_keyword` finds ads from any advertiser by topic, product or phrase. Filter by country, format, dates and status. Useful when you don't know who's advertising yet.
- **See what's new since your last pull:** fetch a brand again a day or more later and the result lists its new ads and how many stopped. Ads launched in the last 7 days show up on the first pull too.
- **Playbooks:** five step-by-step methods in your client's prompt menu: video scripts, competitor teardowns, product hunting, prospect lists and a weekly competitor watch. Or just ask, and the model loads the right one.
- **Google, LinkedIn and TikTok, self-hosted too:** the same setup now covers [Google](https://github.com/proxy-intell/google-ads-library-mcp), [LinkedIn](https://github.com/proxy-intell/linkedin-ads-library-mcp) and [TikTok](https://github.com/proxy-intell/tiktok-ads-library-mcp). Run one, or all four side by side.

### fixed
- **Video analysis works again:** the Gemini model it used was retired. It now defaults to `gemini-3.1-flash-lite`, and `GEMINI_MODEL` in `.env` switches it.
- **Image analysis works again:** `analyze_ad_image` failed on every call. Now your AI actually sees the image instead of a wall of base64.
- **No more false "no ads":** a failed lookup used to look like a brand with zero ads. It now says it failed, and retries once first.

### removed
- **Batch video analysis:** past a few videos it silently dropped results. Call `analyze_ad_video` per ad instead.

Upgrade: `git pull && ./venv/bin/pip install -r requirements.txt`, then restart your MCP client.

Rather skip the keys and the server? [Proxy](https://useproxy.dev/me/selfhost-facebook?utm_source=github&utm_medium=release&utm_campaign=facebook-ads-library-mcp) is the hosted version: all four libraries in one connection, 20 free credits a day.
