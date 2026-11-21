"""Analysis playbooks: step-by-step methods for common ad research jobs.

Served two ways: as MCP prompts (the host's prompt menu) and through the get_playbook tool,
so the model can load one itself. Adapted from hosted Proxy's playbooks to this server's tools.
"""

OTHER_PLATFORMS = (
    "This server covers Meta only. For Google, LinkedIn or TikTok, add the sibling self-hosted servers "
    "(github.com/proxy-intell/google-ads-library-mcp, linkedin-ads-library-mcp, tiktok-ads-library-mcp) "
    "or hosted Proxy, which has all four plus competitor discovery: "
    "https://useproxy.dev/me/selfhost-facebook?utm_source=github&utm_medium=playbook&utm_campaign=facebook-ads-library-mcp"
    " (MCP server URL: https://mcp.useproxy.dev/mcp?ref=facebook-ads-library-mcp-playbook)"
)

RULES = """\
Rules:
- Ask at most one short question, only if a missing input blocks the work; otherwise state assumptions and go.
- Cite each ad with its ad library link: https://www.facebook.com/ads/library/?id=<ad_id>.
- Run time is a proxy for performance, not proof. Say "long-running", not "winning". Mark inference ("likely", "suggests").
- A failed lookup is not "no ads": report the error the tool returned.
- End with the deliverables, ready to use. No recap."""

TRIGGERS = {
    "script_writing": "video ad scripts, hooks to film, UGC briefs, modelling or recreating a winning ad",
    "competitor_teardown": "competitors' hooks, offers, angles and positioning, what's working in a market",
    "product_hunt": "winning products to sell (dropshipping, DTC), or whether a product is saturated",
    "who_is_advertising": "which businesses or prospects run ads; prospect lists for agencies and sellers",
    "competitor_watch": "tracking competitors, what's new since last time, weekly updates",
}

_BODIES = {
    "script_writing": """\
PLAYBOOK: script_writing. Original video ad scripts built on structures that have run for months.
Inputs: product, audience, offer. Infer missing ones from the conversation and state them.

Method:
1. Find 3-5 long-running video ads. Named brands: get_meta_platform_id(brand_names=["A", "B"]), then get_meta_ads(platform_ids=["<id>", "<id>"], limit=50) and keep VIDEO ads with the oldest start_date. No names: search_meta_ads_by_keyword(query="<problem or product type>", media_type="video", sort_by="total_impressions").
2. Pick for spread: different formats and hook tactics, not five cuts of one ad.
3. analyze_ad_video(media_url="<media_url>", brand_name="<page_name>", ad_id="<ad_id>") on each.
4. Beat-map each source with seconds per beat: hook 0-3s, problem, mechanism, proof, offer, CTA. Note format, cut pace, on-screen text, when the product first appears.

Write ORIGINAL scripts for the user's product. Borrow structure and pacing only, never wording, claims or names. Tag claims the user must substantiate [verify].

Output:
- Sources: link, run time, format, one-line beat map each.
- 3 scripts, 15-45s. Per script a table: timecode | spoken line | on-screen text | shot notes.
- 5 alternative hooks: opening line, on-screen text, first visual.""",

    "competitor_teardown": """\
PLAYBOOK: competitor_teardown. How competitors sell on Meta: angles, hooks, offers, formats, gaps.
Inputs: competitors or market, the user's own brand if any, country if named.

Method:
1. No names: search_meta_ads_by_keyword(query="<market or product>", sort_by="total_impressions") and keep the 3-6 page_names that recur.
2. get_meta_platform_id(brand_names=["A", "B", "C"]), then get_meta_ads(platform_ids=["<id>", "<id>", "<id>"], limit=50) in one call.
3. Tag every ad: angle (pain, aspiration, social proof, us-vs-them, mechanism, price, urgency, authority), offer (discount, trial, bundle, guarantee, none), format (IMAGE, VIDEO, DCO).
4. Analyse the 2-3 oldest still-running ads per brand: analyze_ad_video(media_url="<media_url>") or analyze_ad_image(media_url="<media_url>").

Look for: angles a brand keeps funding for months versus ones it tests and kills; one angle across several brands (proven but crowded); offers only in new ads; claims nobody makes.

Output:
- Angle x brand table: ad count and longest run in days.
- Long-running ads: brand, angle, offer, format, run time, link.
- Gaps: angles, offers, formats nobody runs.
- 5 angles to test, one line each, tied to an ad or a gap.""",

    "product_hunt": """\
PLAYBOOK: product_hunt. Products other stores are scaling with Meta ads, and how crowded each is.
Inputs: country, niche or problem space. No niche: start from 3-4 broad problems.

Method:
1. Per product type, in the market's language: search_meta_ads_by_keyword(query="<keyword>", country="<XX>", limit=60). Run 3-6 keywords; multi-word product names add search_type="keyword_exact_phrase".
2. Group by page_id. Set aside household brands and marketplaces. Keep stores pushing one product.
3. Shortlist 5-10 advertisers: get_meta_ads(platform_ids=["<page_id>", "<page_id>"], country="<XX>", limit=50). Per advertiser: ads fetched, oldest active start_date, launches in the last 30 days.
4. One creative per product: analyze_ad_image(media_url="<media_url>") or analyze_ad_video(media_url="<media_url>") for offer, price, bundle, guarantee.

Look for (all inference): old ads still running plus fresh launches = scaling; several unrelated stores on one item = proven demand, rising saturation; only ads under 30 days = a test.

Output:
- Ranked table: product | advertiser | ads fetched | oldest active ad | launches last 30d | offer | link.
- Saturation per product: low / medium / high, labelled inference, with the reason.
- Top 3 picks and the angle to enter with. Say plainly that ads show no sales or margins.""",

    "who_is_advertising": """\
PLAYBOOK: who_is_advertising. Which businesses on a list run Meta ads, and an opener for each.
Inputs: business names. Only a market given: build the list from search_meta_ads_by_keyword(query="<service> <city>", country="<XX>").

Method:
1. get_meta_platform_id(brand_names=["Business 1", "Business 2"]). Pick the page that matches the city or domain; say when none does.
2. get_meta_ads(platform_ids=["<id>", "<id>"], limit=25). Per business: ad count, newest start_date, oldest still running, format mix.
3. Read 2-3 ads per advertiser for one factual opener.

Status per business: yes / no (lookup worked, nothing running) / not found (no page matched) / error (retry once, then report). Not found and error are never "no".

Output:
- Table: business | Meta status | ads fetched | newest ad | format mix | pitch opener with ad link.
- Top 5 to contact first, one line why each.""",

    "competitor_watch": """\
PLAYBOOK: competitor_watch. What competitors launched, dropped and kept since last time.
How the diff works: get_meta_ads remembers each page's last fetch (same country and limit). A re-fetch 24h+ later returns changes.new_since_last_fetch and changes.dropped_since_last_fetch; changes.launched_last_7d lists ads started in the last 7 days, even on a first run. The first run is the baseline: say so and report the last-7-day launches.

Method:
1. get_meta_ads(platform_ids=["<id>", "<id>", "<id>"]) with the same country and limit as last time.
2. Per brand: new (ids), dropped (count only), still running (the rest; note long-runners that survived). "Dropped" can also mean an ad fell outside the limit: say so when the fetch hit it.
3. Analyse only the new creatives: analyze_ad_video(media_url="<media_url>") or analyze_ad_image(media_url="<media_url>").

Look for: a new angle or offer; a burst of launches (refresh, scaling, a promo); a mass drop (strategy shift, season end); the same move from several brands at once.

Then offer a weekly scheduled task in the user's assistant with a prompt like "Run the competitor_watch playbook for A, B and C with the same settings."

Output per brand: launched (count, links), dropped (count), still running (count, longest-runner), what it suggests (inference). Close with 3 lines: what to respond to and what to ignore.""",
}

PLAYBOOKS = {job: f"{body}\n\n{RULES}\n\n{OTHER_PLATFORMS}" for job, body in _BODIES.items()}
