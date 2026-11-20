from dotenv import load_dotenv

# Load .env before the services read their settings (GEMINI_MODEL, API keys).
load_dotenv()

from src.telemetry import TrackedFastMCP
from src.services.scrapecreators_service import get_platform_id, get_ads, get_scrapecreators_api_key, get_platform_ids_batch, get_ads_batch, search_ads, SEARCH_SORTS, SEARCH_STATUSES, SEARCH_MEDIA_TYPES, SEARCH_TYPES, CreditExhaustedException, RateLimitException
from src.services.media_cache_service import media_cache, image_cache  # Keep image_cache for backward compatibility
from src.services.gemini_service import GEMINI_MODEL, configure_gemini, upload_video_to_gemini, analyze_video_with_gemini, cleanup_gemini_file
from src import ad_history
from src.playbooks import PLAYBOOKS, TRIGGERS
from mcp.server.fastmcp import Image
from typing import Dict, Any, List, Optional, Union
import json
import re
import requests
import os


INSTRUCTIONS = """
This server provides access to Meta's Ad Library (Facebook, Instagram) through the ScrapeCreators API.

Workflow:
1. A brand's ads: get_meta_platform_id finds its page ID, then get_meta_ads returns its ads.
2. Ads by topic, product or phrase, any advertiser: search_meta_ads_by_keyword.
3. Creatives: analyze_ad_image and analyze_ad_video on any returned media_url.

Re-running get_meta_ads for a page 24h+ later reports which ads are new and how many dropped
out since the last fetch. For a research job (video scripts, competitor teardown, product
hunting, prospect lists, weekly competitor tracking) call get_playbook first and follow it.
"""


IMAGE_ANALYSIS_PROMPT = """Analyze this ad image and extract:
- Overall: what is shown, the story or message, emotional tone.
- Text: transcribe ALL text; tag each as Headline Hook, Value Proposition, CTA, Disclaimer, Brand Name or Other.
- People: age range, gender, appearance, pose, expression, setting.
- Brand: logos (position), products shown, brand colors.
- Composition: layout, visual hierarchy (first, second, third), text overlay vs separate text.
- Style: dominant colors, background, photography style (studio, UGC, lifestyle), filters.
- Audience cues: who this targets and why.
Report facts first; mark inference as such."""


mcp = TrackedFastMCP(
   name="Meta Ads Library",
   instructions=INSTRUCTIONS
)


@mcp.tool(
  description="Search for companies or brands in the Meta Ad Library and return their platform IDs. Use this tool when you need to find a brand's Meta Platform ID before retrieving their ads. This tool searches the Facebook Ad Library to find matching brands and their associated Meta Platform IDs for ad retrieval.",
  annotations={
    "title": "Search Meta Ad Library Brands",
    "readOnlyHint": True,
    "openWorldHint": True
  }
)
def get_meta_platform_id(brand_names: Union[str, List[str]]) -> Dict[str, Any]:
    """Search for companies/brands in the Meta Ad Library and return their platform IDs.
    
    This endpoint searches the Facebook Ad Library for companies matching the provided name(s).
    It returns matching brands with their Meta Platform IDs, which can then be used
    to retrieve their current advertisements. Supports both single brand searches and batch processing.
    
    Args:
        brand_names: Single brand name (str) or list of brand names (List[str]) to search for.
                    Examples: "Nike", ["Nike", "Coca-Cola", "Apple"]
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if the search was successful
        - message: Status message describing the result
        - results: For single input - dict mapping platform names to IDs
                  For batch input - dict mapping brand names to their platform results
        - batch_info: Information about batch processing (if applicable)
        - credit_info: API credit usage information (if available)
        - total_results: Number of matching brands found
        - error: Error details if the search failed
    """
    # Input validation
    if isinstance(brand_names, str):
        if not brand_names or not brand_names.strip():
            return {
                "success": False, 
                "message": "Brand name must be provided and cannot be empty.",
                "results": {},
                "total_results": 0,
                "error": "Missing or empty brand name"
            }
        brand_list = [brand_names.strip()]
        is_single = True
    elif isinstance(brand_names, list):
        if not brand_names or all(not name or not str(name).strip() for name in brand_names):
            return {
                "success": False,
                "message": "At least one valid brand name must be provided.",
                "results": {},
                "total_results": 0,
                "error": "Missing or empty brand names"
            }
        brand_list = [str(name).strip() for name in brand_names if name and str(name).strip()]
        is_single = False
    else:
        return {
            "success": False,
            "message": "Brand names must be a string or list of strings.",
            "results": {},
            "total_results": 0,
            "error": "Invalid input type"
        }
    
    try:
        # Get API key first
        get_scrapecreators_api_key()
        
        # Process single or batch request
        if is_single:
            # Single brand request
            platform_ids = get_platform_id(brand_list[0])
            results = platform_ids
            total_found = len(platform_ids)
            batch_info = None
        else:
            # Batch request
            batch_results = get_platform_ids_batch(brand_list)
            results = batch_results
            total_found = sum(len(ids) for ids in batch_results.values())
            successful_brands = sum(1 for ids in batch_results.values() if ids)
            batch_info = {
                "total_requested": len(brand_list),
                "successful": successful_brands,
                "failed": len(brand_list) - successful_brands,
                "api_calls_used": len(brand_list)  # One call per brand
            }
        
        if total_found == 0:
            brand_desc = brand_list[0] if is_single else f"{len(brand_list)} brands"
            return {
                "success": True,
                "message": f"No brands found matching '{brand_desc}' in the Meta Ad Library. Try different search terms or check the spelling.",
                "results": results,
                "batch_info": batch_info,
                "total_results": 0,
                "error": None
            }
        
        brand_desc = brand_list[0] if is_single else f"{len(brand_list)} brands"
        return {
            "success": True,
            "message": f"Found {total_found} matching platform ID(s) for '{brand_desc}' in the Meta Ad Library.",
            "results": results,
            "batch_info": batch_info,
            "total_results": total_found,
            "ad_library_search_url": "https://www.facebook.com/ads/library/",
            "source_citation": f"[Facebook Ad Library Search](https://www.facebook.com/ads/library/)",
            "error": None
        }
        
    except CreditExhaustedException as e:
        brand_desc = brand_list[0] if is_single else f"{len(brand_list)} brands"
        return {
            "success": False,
            "message": f"ScrapeCreators API credits exhausted while searching for '{brand_desc}'. Please top up your account at {e.topup_url} to continue using the Facebook Ads Library.",
            "results": {},
            "batch_info": batch_info if not is_single else None,
            "credit_info": {
                "credits_remaining": e.credits_remaining,
                "topup_url": e.topup_url
            },
            "total_results": 0,
            "error": f"Credit exhaustion: {str(e)}"
        }
    except RateLimitException as e:
        brand_desc = brand_list[0] if is_single else f"{len(brand_list)} brands"
        return {
            "success": False,
            "message": f"ScrapeCreators API rate limit exceeded while searching for '{brand_desc}'. Please wait {e.retry_after or 'a few minutes'} before making more requests.",
            "results": {},
            "batch_info": batch_info if not is_single else None,
            "total_results": 0,
            "error": f"Rate limit exceeded: {str(e)}"
        }
    except requests.exceptions.RequestException as e:
        brand_desc = brand_list[0] if is_single else f"{len(brand_list)} brands"
        return {
            "success": False,
            "message": f"Network error while searching for '{brand_desc}': {str(e)}",
            "results": {},
            "batch_info": batch_info if not is_single else None,
            "total_results": 0,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        brand_desc = brand_list[0] if is_single else f"{len(brand_list)} brands"
        return {
            "success": False,
            "message": f"Failed to search for '{brand_desc}': {str(e)}",
            "results": {},
            "batch_info": batch_info if not is_single else None,
            "total_results": 0,
            "error": str(e)
        }


@mcp.tool(
  description="Retrieve currently running ads for a brand using their Meta Platform ID. Use this tool after getting a platform ID from get_meta_platform_id. This tool fetches active advertisements from the Meta Ad Library, including ad content, media URLs, dates, and targeting information. The result's changes block lists ads launched in the last 7 days and, when the same page was fetched with the same filters 24h+ ago, which ads are new since then and how many dropped out. For complete analysis of visual elements, colors, design, or image content, you MUST also use analyze_ad_image on the media_url from each ad.",
  annotations={
    "title": "Get Meta Ad Library Ads",
    "readOnlyHint": True,
    "openWorldHint": True
  }
)
def get_meta_ads(
    platform_ids: Union[str, List[str]], 
    limit: Optional[int] = 50,
    country: Optional[str] = None,
    trim: Optional[bool] = True
) -> Dict[str, Any]:
    """Retrieve currently running ads for brand(s) using their Meta Platform ID(s).
    
    This endpoint fetches active advertisements from the Meta Ad Library for the specified platform(s).
    It supports pagination, country filtering, and both single and batch processing. The response includes 
    ad content, media URLs, start/end dates, and other metadata.
    
    Args:
        platform_ids: Single platform ID (str) or list of platform IDs (List[str]) obtained from get_meta_platform_id.
                     Examples: "123456789", ["123456789", "987654321"]
        limit: Maximum number of ads to retrieve per platform ID (default: 50, max: 500).
               Higher limits allow comprehensive brand analysis but may take longer to process.
        country: Optional country code to filter ads by geographic targeting.
                 Examples: "US", "CA", "GB", "AU". If not provided, returns ads from all countries.
        trim: Whether to trim the response to essential fields only (default: True).
              Set to False to get full ad metadata including targeting details.
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if the ads were retrieved successfully
        - message: Status message describing the result
        - results: For single input - list of ad objects
                  For batch input - dict mapping platform IDs to their ad lists
        - batch_info: Information about batch processing (if applicable)
        - credit_info: API credit usage information (if available)
        - count: Total number of ads found and returned
        - error: Error details if the retrieval failed
    """
    # Input validation
    if isinstance(platform_ids, str):
        if not platform_ids or not platform_ids.strip():
            return {
                "success": False,
                "message": "Platform ID must be provided and cannot be empty.",
                "results": [],
                "count": 0,
                "error": "Missing or empty platform ID"
            }
        platform_list = [platform_ids.strip()]
        is_single = True
    elif isinstance(platform_ids, list):
        if not platform_ids or all(not pid or not str(pid).strip() for pid in platform_ids):
            return {
                "success": False,
                "message": "At least one valid platform ID must be provided.",
                "results": [],
                "count": 0,
                "error": "Missing or empty platform IDs"
            }
        platform_list = [str(pid).strip() for pid in platform_ids if pid and str(pid).strip()]
        is_single = False
    else:
        return {
            "success": False,
            "message": "Platform IDs must be a string or list of strings.",
            "results": [],
            "count": 0,
            "error": "Invalid input type"
        }
    
    # Validate limit parameter
    if limit is not None:
        if not isinstance(limit, int) or limit <= 0:
            return {
                "success": False,
                "message": "Limit must be a positive integer.",
                "results": [],
                "count": 0,
                "error": "Invalid limit parameter"
            }
        if limit > 500:
            limit = 500  # Cap at 500 for reasonable performance
    
    # Validate country parameter
    if country is not None:
        if not isinstance(country, str) or len(country) != 2:
            return {
                "success": False,
                "message": "Country must be a valid 2-letter country code (e.g., 'US', 'CA').",
                "results": [],
                "count": 0,
                "error": "Invalid country code format"
            }
        country = country.upper()
    
    try:
        # Get API key first
        get_scrapecreators_api_key()
        
        # Process single or batch request
        if is_single:
            # Single platform ID request
            ads = get_ads(platform_list[0], limit or 50, country, trim)
            results = ads
            total_count = len(ads)
            batch_info = None
            platform_desc = platform_list[0]
            changes = ad_history.changes(f"meta:{platform_list[0]}:{country}:{limit}", ads)
        else:
            # Batch request
            batch_results = get_ads_batch(platform_list, limit or 50, country, trim)
            results = batch_results
            fetched = {pid: ads for pid, ads in batch_results.items() if isinstance(ads, list)}
            total_count = sum(len(ads) for ads in fetched.values())
            batch_info = {
                "total_requested": len(platform_list),
                "successful": len(fetched),
                "failed": len(batch_results) - len(fetched),
                "api_calls_used": len(platform_list)  # One call per platform ID
            }
            platform_desc = f"{len(platform_list)} platform IDs"
            changes = {pid: ad_history.changes(f"meta:{pid}:{country}:{limit}", ads) for pid, ads in fetched.items()}
        
        failed_note = ""
        if batch_info and batch_info["failed"]:
            failed_note = f" {batch_info['failed']} lookup(s) failed: see the error in results; a failed lookup is not 'no ads'."
        if total_count == 0:
            return {
                "success": True,
                "message": f"No current ads found for {platform_desc} in the Meta Ad Library.{failed_note}",
                "results": results,
                "batch_info": batch_info,
                "changes": changes,
                "count": 0,
                "error": None
            }
        
        return {
            "success": True,
            "message": f"Successfully retrieved {total_count} ads for {platform_desc} from the Meta Ad Library.{failed_note}",
            "results": results,
            "batch_info": batch_info,
            "changes": changes,
            "count": total_count,
            "ad_library_url": "https://www.facebook.com/ads/library/",
            "source_citation": f"[Facebook Ad Library - {platform_desc}](https://www.facebook.com/ads/library/)",
            "error": None
        }
        
    except CreditExhaustedException as e:
        platform_desc = platform_list[0] if is_single else f"{len(platform_list)} platform IDs"
        return {
            "success": False,
            "message": f"ScrapeCreators API credits exhausted while retrieving ads for {platform_desc}. Please top up your account at {e.topup_url} to continue using the Facebook Ads Library.",
            "results": [],
            "batch_info": batch_info if not is_single else None,
            "credit_info": {
                "credits_remaining": e.credits_remaining,
                "topup_url": e.topup_url
            },
            "count": 0,
            "error": f"Credit exhaustion: {str(e)}"
        }
    except RateLimitException as e:
        platform_desc = platform_list[0] if is_single else f"{len(platform_list)} platform IDs"
        return {
            "success": False,
            "message": f"ScrapeCreators API rate limit exceeded while retrieving ads for {platform_desc}. Please wait {e.retry_after or 'a few minutes'} before making more requests.",
            "results": [],
            "batch_info": batch_info if not is_single else None,
            "count": 0,
            "error": f"Rate limit exceeded: {str(e)}"
        }
    except requests.exceptions.RequestException as e:
        platform_desc = platform_list[0] if is_single else f"{len(platform_list)} platform IDs"
        return {
            "success": False,
            "message": f"Network error while retrieving ads for {platform_desc}: {str(e)}",
            "results": [],
            "batch_info": batch_info if not is_single else None,
            "count": 0,
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        platform_desc = platform_list[0] if is_single else f"{len(platform_list)} platform IDs"
        return {
            "success": False,
            "message": f"Failed to retrieve ads for {platform_desc}: {str(e)}",
            "results": [],
            "batch_info": batch_info if not is_single else None,
            "count": 0,
            "error": str(e)
        }


@mcp.tool(
  description="Search the whole Meta Ad Library by keyword, topic or phrase, without knowing the advertiser. Use it to find who advertises a product or problem, ads in a niche, or partnership ads run through creators (get_meta_ads only returns a brand's own page). Returns ads with page_id and page_name, so you can follow up with get_meta_ads on any advertiser.",
  annotations={
    "title": "Search Meta Ads by Keyword",
    "readOnlyHint": True,
    "openWorldHint": True
  }
)
def search_meta_ads_by_keyword(
    query: str,
    country: Optional[str] = None,
    status: Optional[str] = None,
    media_type: Optional[str] = None,
    sort_by: Optional[str] = None,
    search_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = 30,
    trim: Optional[bool] = True
) -> Dict[str, Any]:
    """Search Meta Ad Library ads by keyword across all advertisers.

    Args:
        query: Keyword or phrase, e.g. "running shoes".
        country: Two-letter country code, e.g. "US". Default: all countries.
        status: "ACTIVE" (default upstream), "INACTIVE" or "ALL".
        media_type: "all" (default), "image" (stills and carousels) or "video".
        sort_by: "relevancy_monthly_grouped" (default, on-topic, last month only) or "total_impressions" (biggest advertisers first, any age).
        search_type: "keyword_unordered" (default) or "keyword_exact_phrase" (better for multi-word product names).
        start_date: Only ads shown from this date, YYYY-MM-DD.
        end_date: Only ads shown up to this date, YYYY-MM-DD.
        limit: Max ads to return (default 30, max 150). Each page of results is one ScrapeCreators credit.
        trim: True (default) returns essential fields only.

    Returns:
        success, message, results (ads), count, total_matches (library-wide), cursor, error.
    """
    if not query or not query.strip():
        return {"success": False, "message": "query must be a non-empty keyword or phrase.", "results": [], "count": 0, "error": "Missing query"}
    status = status.upper() if status else None
    media_type = media_type.lower() if media_type else None
    checks = [
        ("status", status, SEARCH_STATUSES),
        ("media_type", media_type, SEARCH_MEDIA_TYPES),
        ("sort_by", sort_by, SEARCH_SORTS),
        ("search_type", search_type, SEARCH_TYPES),
    ]
    for name, value, allowed in checks:
        if value and value not in allowed:
            return {"success": False, "message": f"{name} must be one of {', '.join(allowed)}; got '{value}'.", "results": [], "count": 0, "error": f"Invalid {name}"}
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return {"success": False, "message": f"{name} must be YYYY-MM-DD; got '{value}'.", "results": [], "count": 0, "error": f"Invalid {name}"}
    if country and len(country) != 2:
        return {"success": False, "message": "country must be a 2-letter code, e.g. 'US'.", "results": [], "count": 0, "error": "Invalid country"}

    try:
        found = search_ads(query.strip(), min(max(limit or 30, 1), 150), country.upper() if country else None,
                           status, media_type, sort_by, search_type, start_date, end_date, trim is not False)
        ads = found["ads"]
        return {
            "success": True,
            "message": f"Found {len(ads)} ads matching '{query}'" + (f" (about {found['total']} in the library)" if found["total"] else "") + ".",
            "results": ads,
            "count": len(ads),
            "total_matches": found["total"],
            "cursor": found["cursor"],
            "ad_library_url": "https://www.facebook.com/ads/library/",
            "error": None
        }
    except CreditExhaustedException as e:
        return {"success": False, "message": f"ScrapeCreators API credits exhausted. Top up at {e.topup_url}.", "results": [], "count": 0, "error": f"Credit exhaustion: {str(e)}"}
    except RateLimitException as e:
        return {"success": False, "message": f"ScrapeCreators API rate limit exceeded. Wait {e.retry_after or 'a few minutes'} and retry.", "results": [], "count": 0, "error": f"Rate limit exceeded: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Keyword search for '{query}' failed: {str(e)}", "results": [], "count": 0, "error": str(e)}


@mcp.tool(
  description="Analyze a Facebook ad image: returns the image itself so you can see it, plus a checklist (text, hooks, people, brand elements, composition, colors). Pass one media_url from get_meta_ads or search_meta_ads_by_keyword. Downloads are cached locally.",
  annotations={
    "title": "Analyze Ad Image Content",
    "readOnlyHint": True,
    "openWorldHint": True
  }
)
def analyze_ad_image(media_url: str, brand_name: Optional[str] = None, ad_id: Optional[str] = None) -> Any:
    """Download a Facebook ad image and hand it to the model for visual analysis.

    The image comes back as an image content block, so the model sees it with its own vision,
    plus a short checklist of what to extract. Downloads are cached locally.

    Args:
        media_url: The image URL from a get_meta_ads or search_meta_ads_by_keyword result.
        brand_name: Optional brand name for cache organization.
        ad_id: Optional ad ID, used for the ad library link.
    """
    if not media_url or not media_url.strip():
        return {"success": False, "message": "media_url must be provided and cannot be empty.", "error": "Missing media URL"}
    media_url = media_url.strip()
    try:
        cached = image_cache.get_cached_image(media_url)
        image_bytes, content_type = None, None
        if cached:
            try:
                with open(cached['file_path'], 'rb') as f:
                    image_bytes = f.read()
                content_type = cached['content_type']
            except OSError:
                cached = None  # cache file gone, download again
        if not cached:
            response = requests.get(media_url, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get('content-type', '').lower()
            if not content_type.startswith('image/'):
                return {"success": False, "message": f"URL does not point to an image (content type: {content_type}). Media URLs expire; re-fetch the ad for a fresh one.", "error": f"Invalid content type: {content_type}"}
            image_cache.cache_image(url=media_url, image_data=response.content, content_type=content_type, brand_name=brand_name, ad_id=ad_id)
            image_bytes = response.content

        info = {
            "success": True,
            "media_url": media_url,
            "brand_name": brand_name,
            "ad_id": ad_id,
            "ad_library_url": f"https://www.facebook.com/ads/library/?id={ad_id}" if ad_id else "https://www.facebook.com/ads/library/",
            "cache_status": "Used cached image" if cached else "Downloaded and cached new image",
            "analysis_instructions": IMAGE_ANALYSIS_PROMPT,
        }
        fmt = content_type.split('/')[-1].split(';')[0].replace('jpg', 'jpeg')
        return [json.dumps(info), Image(data=image_bytes, format=fmt)]
    except requests.exceptions.RequestException as e:
        return {"success": False, "message": f"Failed to download image from {media_url}: {str(e)}. Media URLs expire; re-fetch the ad for a fresh one.", "error": f"Network error: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Failed to process image from {media_url}: {str(e)}", "error": str(e)}


@mcp.tool(
  description="REQUIRED for checking media cache status and storage usage. Use this tool when users ask about cache statistics, storage space used by cached media (images and videos), or how many files have been analyzed and cached. Essential for cache management and monitoring.",
  annotations={
    "title": "Get Media Cache Statistics",
    "readOnlyHint": True,
    "openWorldHint": False
  }
)
def get_cache_stats() -> Dict[str, Any]:
    """Get comprehensive statistics about the media cache (images and videos).
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if stats were retrieved successfully
        - message: Status message
        - stats: Cache statistics including:
            * total_files: Total number of cached files
            * total_images: Number of cached images
            * total_videos: Number of cached videos
            * total_size_mb/gb: Storage space used
            * analyzed_files: Number of files with cached analysis
            * unique_brands: Number of different brands cached
        - error: Error details if retrieval failed
    """
    try:
        stats = media_cache.get_cache_stats()
        
        total_files = stats.get('total_files', 0)
        total_images = stats.get('total_images', 0)
        total_videos = stats.get('total_videos', 0)
        
        return {
            "success": True,
            "message": f"Cache contains {total_files} files ({total_images} images, {total_videos} videos) using {stats.get('total_size_gb', 0)}GB storage",
            "stats": stats,
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to retrieve cache statistics: {str(e)}",
            "stats": {},
            "error": str(e)
        }


@mcp.tool(
  description="REQUIRED for finding previously analyzed ad media (images and videos) in cache. Use this tool when users want to search for cached media by brand name, find media with people, search by colors, or filter by media type. Essential for retrieving past analysis results without re-downloading media.",
  annotations={
    "title": "Search Cached Media",
    "readOnlyHint": True,
    "openWorldHint": True
  }
)
def search_cached_media(
    brand_name: Optional[str] = None,
    has_people: Optional[bool] = None,
    color_contains: Optional[str] = None,
    media_type: Optional[str] = None,
    limit: Optional[int] = 20
) -> Dict[str, Any]:
    """Search cached media (images and videos) by various criteria.
    
    Args:
        brand_name: Filter by exact brand name match
        has_people: Filter by presence of people in media (True/False)
        color_contains: Filter by dominant color (partial match, e.g., "red", "blue")
        media_type: Filter by media type ('image' or 'video')
        limit: Maximum number of results to return (default: 20)
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if search was successful
        - message: Status message
        - results: List of matching cached media with metadata
        - count: Number of results returned
        - error: Error details if search failed
    """
    try:
        results = media_cache.search_cached_media(
            brand_name=brand_name,
            has_people=has_people,
            color_contains=color_contains,
            media_type=media_type
        )
        
        # Limit results
        if limit and len(results) > limit:
            results = results[:limit]
        
        # Remove large base64 data from results for cleaner output
        clean_results = []
        for result in results:
            clean_result = result.copy()
            if 'analysis_results' in clean_result and clean_result['analysis_results']:
                # Keep analysis but remove any base64 image data if present
                analysis = clean_result['analysis_results'].copy()
                if 'image_data_base64' in analysis:
                    analysis['image_data_base64'] = "[Image data available]"
                clean_result['analysis_results'] = analysis
            clean_results.append(clean_result)
        
        search_criteria = []
        if brand_name:
            search_criteria.append(f"brand: {brand_name}")
        if has_people is not None:
            search_criteria.append(f"has_people: {has_people}")
        if color_contains:
            search_criteria.append(f"color: {color_contains}")
        if media_type:
            search_criteria.append(f"media_type: {media_type}")
        
        criteria_str = ", ".join(search_criteria) if search_criteria else "no filters"
        
        return {
            "success": True,
            "message": f"Found {len(clean_results)} cached media files matching criteria: {criteria_str}",
            "results": clean_results,
            "count": len(clean_results),
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to search cached images: {str(e)}",
            "results": [],
            "count": 0,
            "error": str(e)
        }


@mcp.tool(
  description="REQUIRED for cleaning up old cached media files (images and videos) and freeing disk space. Use this tool when users want to remove old cached media, clean up storage space, or when cache becomes too large. Essential for cache maintenance and storage management.",
  annotations={
    "title": "Cleanup Media Cache",
    "readOnlyHint": False,
    "openWorldHint": False
  }
)
def cleanup_media_cache(max_age_days: Optional[int] = 30) -> Dict[str, Any]:
    """Clean up old cached media files (images and videos) and database entries.
    
    Args:
        max_age_days: Maximum age in days before media files are deleted (default: 30)
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if cleanup was successful
        - message: Status message with cleanup results
        - cleanup_stats: Statistics about what was cleaned up
        - error: Error details if cleanup failed
    """
    try:
        # Get stats before cleanup
        stats_before = media_cache.get_cache_stats()
        
        # Perform cleanup
        media_cache.cleanup_old_cache(max_age_days=max_age_days or 30)
        
        # Get stats after cleanup
        stats_after = media_cache.get_cache_stats()
        
        files_removed = stats_before.get('total_files', 0) - stats_after.get('total_files', 0)
        images_removed = stats_before.get('total_images', 0) - stats_after.get('total_images', 0)
        videos_removed = stats_before.get('total_videos', 0) - stats_after.get('total_videos', 0)
        space_freed_mb = stats_before.get('total_size_mb', 0) - stats_after.get('total_size_mb', 0)
        
        return {
            "success": True,
            "message": f"Cleanup completed: removed {files_removed} files ({images_removed} images, {videos_removed} videos), freed {space_freed_mb:.2f}MB",
            "cleanup_stats": {
                "total_files_removed": files_removed,
                "images_removed": images_removed,
                "videos_removed": videos_removed,
                "space_freed_mb": round(space_freed_mb, 2),
                "max_age_days": max_age_days or 30,
                "files_remaining": stats_after.get('total_files', 0),
                "images_remaining": stats_after.get('total_images', 0),
                "videos_remaining": stats_after.get('total_videos', 0),
                "space_remaining_mb": stats_after.get('total_size_mb', 0)
            },
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to cleanup cache: {str(e)}",
            "cleanup_stats": {},
            "error": str(e)
        }


# Backward compatibility aliases
def search_cached_images(brand_name: Optional[str] = None, has_people: Optional[bool] = None, 
                        color_contains: Optional[str] = None, limit: Optional[int] = 20) -> Dict[str, Any]:
    """Search cached images by criteria (backward compatibility)."""
    return search_cached_media(brand_name, has_people, color_contains, 'image', limit)

cleanup_image_cache = cleanup_media_cache


@mcp.tool(
  description="REQUIRED for analyzing video ads from Facebook. Download and analyze ad videos using Gemini's advanced video understanding capabilities. Extracts visual storytelling, audio elements, pacing, scene transitions, brand messaging, and marketing strategy insights. Uses intelligent caching for efficiency and includes comprehensive video analysis.",
  annotations={
    "title": "Analyze Ad Video Content",
    "readOnlyHint": True,
    "openWorldHint": True
  }
)
def analyze_ad_video(media_url: str, brand_name: Optional[str] = None, ad_id: Optional[str] = None) -> Dict[str, Any]:
    """Download Facebook ad videos and analyze them using Gemini's video understanding capabilities.
    
    This tool downloads videos from Facebook Ad Library URLs and provides comprehensive analysis
    using Google's Gemini AI model. Videos are cached locally to avoid re-downloading, and 
    analysis results are cached to improve performance and reduce API costs.
    
    Args:
        media_url: The direct URL to the Facebook ad video to analyze.
        brand_name: Optional brand name for cache organization.
        ad_id: Optional ad ID for tracking purposes.
    
    Returns:
        A dictionary containing:
        - success: Boolean indicating if analysis was successful
        - message: Status message
        - cached: Boolean indicating if video was retrieved from cache
        - analysis: Comprehensive video analysis results
        - media_url: Original video URL
        - brand_name: Brand name if provided
        - ad_id: Ad ID if provided
        - cache_status: Information about cache usage
        - error: Error details if analysis failed
    """
    if not media_url or not media_url.strip():
        return {
            "success": False,
            "message": "Media URL must be provided and cannot be empty.",
            "cached": False,
            "analysis": {},
            "cache_info": {},
            "error": "Missing or empty media URL"
        }
    
    try:
        # Check cache first
        cached_data = media_cache.get_cached_media(media_url.strip(), media_type='video')
        
        if cached_data and cached_data.get('analysis_results'):
            # Return cached analysis results
            return {
                "success": True,
                "message": f"Retrieved cached video analysis for {media_url}",
                "cached": True,
                "analysis": cached_data['analysis_results'],
                "cache_info": {
                    "cached_at": cached_data.get('downloaded_at'),
                    "analysis_cached_at": cached_data.get('analysis_cached_at'),
                    "file_size": cached_data.get('file_size'),
                    "brand_name": cached_data.get('brand_name'),
                    "ad_id": cached_data.get('ad_id'),
                    "duration_seconds": cached_data.get('duration_seconds')
                },
                "ad_library_url": "https://www.facebook.com/ads/library/",
                "source_citation": f"[Facebook Ad Library - {brand_name if brand_name else 'Ad'} #{ad_id if ad_id else 'Unknown'}]({media_url})",
                "error": None
            }
        
        # Download video if not cached or no analysis available
        video_path = None
        file_size = None
        duration_seconds = None
        
        if cached_data:
            # Video is cached but no analysis results yet
            video_path = cached_data['file_path']
            file_size = cached_data['file_size']
            duration_seconds = cached_data.get('duration_seconds')
        else:
            # Download the video
            response = requests.get(media_url.strip(), timeout=60)  # Longer timeout for videos
            response.raise_for_status()
            
            # Check if it's a video
            content_type = response.headers.get('content-type', '').lower()
            if not any(vid_type in content_type for vid_type in ['video/', 'mp4', 'mov', 'webm', 'avi']):
                return {
                    "success": False,
                    "message": f"URL does not point to a valid video. Content type: {content_type}",
                    "cached": False,
                    "analysis": {},
                    "cache_info": {},
                    "error": f"Invalid content type: {content_type}"
                }
            
            # Cache the downloaded video
            file_path = media_cache.cache_media(
                url=media_url.strip(),
                media_data=response.content,
                content_type=content_type,
                media_type='video',
                brand_name=brand_name,
                ad_id=ad_id
            )
            
            video_path = file_path
            file_size = len(response.content)
        
        # Configure Gemini API
        try:
            model = configure_gemini()
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to configure Gemini API: {str(e)}. Ensure --gemini-api-key is provided or GEMINI_API_KEY environment variable is set.",
                "cached": bool(cached_data),
                "analysis": {},
                "cache_info": {},
                "error": f"Gemini configuration error: {str(e)}"
            }
        
        # Create structured video analysis prompt based on user requirements
        analysis_prompt = """
Analyze this Facebook ad video and provide a comprehensive, structured breakdown following this exact format:

**SCENE ANALYSIS:**
Analyze the video at a scene-by-scene level. For each identified scene, provide:

Scene [Number]: [Brief scene title]
1. Visual Description:
   - Detailed description of key visuals within the scene
   - Appearance and demographics of featured individuals (age, gender, notable characteristics)
   - Specific camera angles and movements used

2. Text Elements:
   - Document ALL text elements appearing in the scene
   - Categorize each text element as:
     * "Text Hook" (introductory text designed to grab attention)
     * "CTA (middle)" (call-to-action appearing mid-video)
     * "CTA (end)" (final call-to-action)

3. Brand Elements:
   - Note any visible brand logos or product placements
   - Provide brief descriptions and specific timing within the scene

4. Audio Analysis:
   - Transcription or detailed summary of any voiceover present
   - Describe voiceover characteristics: tone, pitch, conveyed emotions
   - Identify and briefly describe notable sound effects

5. Music Analysis:
   - Music present: [true/false]
   - If true: Brief description or identification of music style/track

6. Scene Transition:
   - Describe the style and pacing of transition to next scene (quick cuts, fades, dynamic transitions, etc.)

**OVERALL VIDEO ANALYSIS:**

**Ad Format:**
- Identify the specific ad format (single video, carousel, story, etc.)
- Aspect ratio and orientation
- Duration and pacing style

**Notable Angles:**
- List all significant camera angles used throughout the video
- Comment on their effectiveness and purpose

**Overall Messaging:**
- Primary message or value proposition
- Secondary messages or supporting points
- Target audience indicators

**Hook Analysis:**
- Primary hook type: Text, Visual, or VoiceOver
- Description of the hook and its placement
- Effectiveness assessment of attention-grabbing elements

Provide detailed, factual observations that would help understand the video's marketing strategy and effectiveness. Focus on specific, actionable insights.
"""
        
        # Upload video to Gemini and analyze
        gemini_file = None
        try:
            # Upload video to Gemini File API
            gemini_file = upload_video_to_gemini(model, video_path)

            # Analyze video with Gemini
            analysis_text = analyze_video_with_gemini(model, gemini_file, analysis_prompt)
            
            # Structure the analysis results
            analysis_results = {
                "raw_analysis": analysis_text,
                "analysis_timestamp": media_cache._generate_url_hash(str(hash(analysis_text))),
                "model_used": GEMINI_MODEL,
                "video_metadata": {
                    "file_size_mb": round(file_size / (1024 * 1024), 2) if file_size else None,
                    "duration_seconds": duration_seconds,
                    "content_type": cached_data.get('content_type') if cached_data else response.headers.get('content-type')
                }
            }
            
            # Cache analysis results
            media_cache.update_analysis_results(media_url.strip(), analysis_results)
            
            # Cleanup Gemini file to save storage
            if gemini_file:
                cleanup_gemini_file(model, gemini_file.name)
            
            return {
                "success": True,
                "message": f"Video analysis completed successfully",
                "cached": bool(cached_data),
                "analysis": analysis_results,
                "media_url": media_url,
                "brand_name": brand_name,
                "ad_id": ad_id,
                "cache_status": "Used cached video" if cached_data else "Downloaded and cached new video",
                "ad_library_url": "https://www.facebook.com/ads/library/",
                "source_citation": f"[Facebook Ad Library - {brand_name if brand_name else 'Ad'} #{ad_id if ad_id else 'Unknown'}]({media_url})",
                "error": None
            }
            
        except Exception as e:
            # Cleanup Gemini file in case of error
            if gemini_file:
                try:
                    cleanup_gemini_file(model, gemini_file.name)
                except:
                    pass
            raise e
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Failed to download video from {media_url}: {str(e)}",
            "cached": False,
            "analysis": {},
            "cache_info": {},
            "error": f"Network error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to analyze video from {media_url}: {str(e)}",
            "cached": bool(cached_data) if 'cached_data' in locals() else False,
            "analysis": {},
            "cache_info": {},
            "error": str(e)
        }


@mcp.tool(
  description="Load a playbook: the step-by-step method for an ad research job (which tool calls, what to look for, output format). Call it BEFORE starting when the request matches a job, then follow it. Jobs:\n" + "\n".join(f"- {job}: {trigger}" for job, trigger in TRIGGERS.items()),
  annotations={
    "title": "Get Analysis Playbook",
    "readOnlyHint": True,
    "openWorldHint": False
  }
)
def get_playbook(job: str) -> str:
    """Return the playbook text for a job: script_writing, competitor_teardown, product_hunt, who_is_advertising, competitor_watch."""
    key = job.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in PLAYBOOKS:
        return f"Unknown job '{job}'. Valid jobs: {', '.join(PLAYBOOKS)}."
    return PLAYBOOKS[key]


def _playbook_prompt(job: str):
    def prompt(brief: str = "") -> str:
        return f"Run this playbook.{f' My brief: {brief}' if brief else ''}\n\n{PLAYBOOKS[job]}"
    return prompt


# The same playbooks in the host's prompt menu (Claude Desktop, Claude Code, Cursor).
for _job, _trigger in TRIGGERS.items():
    mcp.prompt(name=_job, title=_job.replace("_", " ").capitalize(), description=f"Playbook for {_trigger}.")(_playbook_prompt(_job))


if __name__ == "__main__":
   if os.getenv("MCP_TRANSPORT") == "http":
      from src.http_server import run_http
      run_http(mcp)
   else:
      mcp.run()
