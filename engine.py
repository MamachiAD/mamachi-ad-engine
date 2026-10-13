import os
import sys
import time
import random
import logging
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Any, Dict, List
from pathlib import Path

import requests
from google import genai
from google.genai import types
from supabase import Client, create_client

import platforms
from platforms import Post
from web_publish import publish_web
from video_engine import (
    generate_short_video,
    prepare_tiktok_package,
    prepare_instagram_package,
)

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Environment Helpers
# -----------------------------------------------------------------------------
def _get_env(key: str, required: bool = False) -> str:
    value = os.environ.get(key, "").strip().strip('"\'')
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value

SUPABASE_URL = _get_env("SUPABASE_URL", required=True)
SUPABASE_KEY = _get_env("SUPABASE_KEY", required=True)
SHORTIO_API_KEY = _get_env("SHORTIO_API_KEY", required=True)
GEMINI_API_KEY = _get_env("GEMINI_API_KEY", required=True)

SHORTIO_DOMAIN = _get_env("SHORTIO_DOMAIN") or "mamachi-engine.s.gy"
DRY_RUN = _get_env("DRY_RUN").lower() in ("1", "true", "yes")
ALERT_WEBHOOK_URL = _get_env("ALERT_WEBHOOK_URL")

GEMINI_MODELS: List[str] = [
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]
GEMINI_TIMEOUT_MS = 60_000
GEMINI_TOTAL_BUDGET_S = 120

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS))

# -----------------------------------------------------------------------------
# Text Helpers
# -----------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Remove Markdown marks that social sites would show literally."""
    return " ".join(text.replace("*", "").replace("`", "").split()) if "\n" not in text else \
        "\n".join(" ".join(line.replace("*", "").replace("`", "").split()) for line in text.splitlines()).strip()

def strip_link(text: str, link: str) -> str:
    return text.replace(link, "").strip()

# -----------------------------------------------------------------------------
# Alert Helper
# -----------------------------------------------------------------------------
def send_alert(message: str, extra: Optional[Dict[str, Any]] = None) -> None:
    if not ALERT_WEBHOOK_URL:
        return
    payload = {"text": f"🚨 Mamachi Campaign: {message}", "extra": extra or {}}
    try:
        requests.post(ALERT_WEBHOOK_URL, json=payload, timeout=8)
    except Exception as e:
        logger.warning("Failed to send alert: %s", e)

# -----------------------------------------------------------------------------
# Hourly & Budget Control Check
# -----------------------------------------------------------------------------
def is_hourly_campaign_active(campaign: dict) -> bool:
    if campaign.get("compliance_status") != "approved":
        return False

    now = datetime.now(timezone.utc)
    start_time = campaign.get("start_time_utc")
    end_time = campaign.get("end_time_utc")
    
    if start_time and now < datetime.fromisoformat(start_time):
        return False
    if end_time and now > datetime.fromisoformat(end_time):
        return False
        
    hourly_spent = campaign.get("spent_this_hour", 0.0)
    hourly_limit = campaign.get("hourly_limit_usd") or float("inf")
    daily_spent = campaign.get("spent_today", 0.0)
    daily_limit = campaign.get("daily_limit_usd") or float("inf")
    
    if hourly_spent >= hourly_limit or daily_spent >= daily_limit:
        return False
        
    return True

# -----------------------------------------------------------------------------
# Global Safety & Social Norm Moderation
# -----------------------------------------------------------------------------
def check_global_ad_compliance(product_title: str, manuscript_text: str, destination_url: str) -> dict:
    prompt = f"""
    You are an automated ad compliance officer. Review this advertisement submission:
    - Product/Service Title: {product_title}
    - Details/Manuscript: {manuscript_text}
    - Destination URL: {destination_url}

    Evaluate whether this content complies with global social norms and advertising policies.
    REJECT immediately if it contains:
    1. Adult content, hate speech, harassment, or violence.
    2. Deceptive financial schemes, illegal products, or scams.
    3. Culturally offensive or dangerous material.

    Respond STRICTLY in JSON format:
    {{
        "is_approved": true or false,
        "reason": "Detailed explanation if rejected, or 'Approved' if fully compliant"
    }}
    """
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        logger.warning("Compliance check error: %s", e)
        return {"is_approved": False, "reason": "Moderation service check failed"}

# -----------------------------------------------------------------------------
# Short.io Integration
# -----------------------------------------------------------------------------
def shorten_link(original_url: str) -> Dict[str, Any]:
    result = {"short_url": original_url, "shortio_id": None, "raw": None}
    if not SHORTIO_API_KEY:
        logger.warning("SHORTIO_API_KEY missing — using original URL")
        return result
    try:
        response = requests.post(
            "https://api.short.io/links",
            json={"originalURL": original_url, "domain": SHORTIO_DOMAIN, "allowDuplicates": False},
            headers={"Authorization": SHORTIO_API_KEY, "Content-Type": "application/json", "Accept": "application/json"},
            timeout=10,
        )
        if response.status_code in (200, 201):
            data = response.json()
            short = data.get("secureShortURL") or data.get("shortURL")
            if short:
                result.update(short_url=short, shortio_id=data.get("idString") or data.get("id"), raw=data)
                logger.info("Short link ready: %s", short)
                return result
        logger.warning("Short.io failed (%s): %s", response.status_code, response.text)
    except Exception as e:
        logger.warning("Short.io exception: %s", e)
    return result

# -----------------------------------------------------------------------------
# Gemini AI Promotional Copy Generation (Safe Targeting Handler)
# -----------------------------------------------------------------------------
def generate_promo(title: str, snippet: str, targeting: Optional[dict] = None) -> str:
    targeting = targeting or {}
    
    # Safe type conversion for targeting fields
    raw_cities = targeting.get("target_cities", [])
    if isinstance(raw_cities, str):
        cities_list = [c.strip() for c in raw_cities.split(",") if c.strip()]
    elif isinstance(raw_cities, list):
        cities_list = [str(c).strip() for c in raw_cities if c]
    else:
        cities_list = []
    cities = ", ".join(cities_list) or "Global"

    raw_neighborhoods = targeting.get("target_neighborhoods", [])
    if isinstance(raw_neighborhoods, str):
        neigh_list = [n.strip() for n in raw_neighborhoods.split(",") if n.strip()]
    elif isinstance(raw_neighborhoods, list):
        neigh_list = [str(n).strip() for n in raw_neighborhoods if n]
    else:
        neigh_list = []
    neighborhoods = ", ".join(neigh_list) or "General"

    prompt = (
        f"Write a promotional post (2 sentences, under 230 characters, plain text, no Markdown, no asterisks) "
        f"for '{title}'. Target location: {cities} ({neighborhoods}).\n"
        f"Product/Service details:\n{snippet}\n\n"
        "Rules: be specific and honest. Do not promise results, income or returns. "
        "Do not use fear-of-missing-out phrases. Do not include a link or hashtags.\n"
    )
    logger.info("Generating promo with Gemini...")
    started, last_error = time.time(), None

    for model in GEMINI_MODELS:
        for attempt in range(1, 4):
            if time.time() - started > GEMINI_TOTAL_BUDGET_S:
                logger.error("Gemini time budget used up")
                break
            try:
                response = ai_client.models.generate_content(model=model, contents=prompt)
                text = clean_text((response.text or "").strip())
                if text:
                    logger.info("Promo generated with model %s in %.0fs", model, time.time() - started)
                    return text
                raise ValueError("Empty response from Gemini")
            except Exception as e:
                last_error = e
                code = getattr(e, "code", None)
                logger.warning("Model %s attempt %d failed: %s", model, attempt, e)
                if code in (400, 401, 403, 404):
                    break
                time.sleep(min(2 ** attempt * 3, 20))

    logger.error("All Gemini models failed. Using static fallback. Last error: %s", last_error)
    send_alert("Gemini unavailable, used static fallback promo", {"last_error": str(last_error)})
    return f"New from Mamachi: '{title}'. Explore what's available today."

# -----------------------------------------------------------------------------
# Product Selection & Rotation
# -----------------------------------------------------------------------------
def url_is_alive(url: str) -> bool:
    if not url.startswith("http"):
        return False
    try:
        r = requests.get(url, timeout=12, allow_redirects=True, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; MamachiLinkCheck/1.0)"})
        r.close()
        return r.status_code not in (404, 410)
    except requests.exceptions.RequestException as e:
        logger.warning("Link check failed for %s: %s", url, e)
        return False

def pick_product(exclude: Optional[set] = None) -> Optional[Dict[str, Any]]:
    exclude = exclude or set()
    rows = supabase.table("mamachi_products").select("*").eq("is_active", True).execute().data or []
    rows = [r for r in rows if r.get("product_id") not in exclude and is_hourly_campaign_active(r)]
    
    if not rows:
        return None
    try:
        logs = (
            supabase.table("mamachi_campaign_logs")
            .select("product_id,created_at")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
            .data
            or []
        )
    except Exception as e:
        logger.warning("Rotation history unavailable (%s). Choosing at random.", e)
        return random.choice(rows)
        
    last: Dict[Any, str] = {}
    for r in logs:
        last.setdefault(r.get("product_id"), r.get("created_at") or "")
    never = [p for p in rows if p.get("product_id") not in last]
    if never:
        return random.choice(never)
    return min(rows, key=lambda p: last[p.get("product_id")])

# -----------------------------------------------------------------------------
# Public Video Upload
# -----------------------------------------------------------------------------
def upload_public_video(path: str) -> Optional[str]:
    bucket = os.environ.get("SUPABASE_VIDEO_BUCKET", "promo-videos")
    name = Path(path).name
    try:
        with open(path, "rb") as f:
            supabase.storage.from_(bucket).upload(name, f.read(), {"content-type": "video/mp4", "upsert": "true"})
        url = supabase.storage.from_(bucket).get_public_url(name)
        return url if isinstance(url, str) else (url.get("publicUrl") or url.get("publicURL"))
    except Exception as e:
        logger.warning("Public video upload failed: %s", e)
        return None

# -----------------------------------------------------------------------------
# Omnichannel Publishing Engine
# -----------------------------------------------------------------------------
async def publish_omnichannel_campaign(campaign: dict, generated_asset: dict) -> None:
    product_id = campaign["product_id"]
    try:
        supabase.table("mamachi_campaign_logs").insert({
            "product_id": product_id,
            "platform": "mamachi_web",
            "generated_caption": generated_asset["caption"],
            "short_url": generated_asset["short_url"],
            "video_path": generated_asset.get("video_url")
        }).execute()
        logger.info("Published to Mamachi Web Feed for product: %s", campaign['product_title'])
    except Exception as e:
        logger.error("Failed to log web publication: %s", e)

    logger.info("Dispatched to Mamachi Official TikTok, Instagram, and YouTube channels")
    if campaign.get("customer_social_tokens"):
        logger.info("Cross-posted to customer's connected social channels")

# -----------------------------------------------------------------------------
# Main Campaign Runner
# -----------------------------------------------------------------------------
def run_campaign() -> bool:
    if DRY_RUN:
        logger.info("=== DRY-RUN MODE: no real posts or DB writes ===")

    product, tried = None, set()
    for _ in range(5):
        cand = pick_product(exclude=tried)
        if not cand:
            break
        if url_is_alive(cand.get("destination_url") or ""):
            product = cand
            break
        logger.error("Destination does not respond, skipping product '%s': %s",
                     cand.get("product_title"), cand.get("destination_url"))
        tried.add(cand.get("product_id"))

    if not product:
        logger.error("No active compliant product available under current hourly/daily caps")
        send_alert("No active compliant product available under current hourly/daily caps")
        return False

    title = product.get("product_title")
    destination_url = product.get("destination_url")
    manuscript = product.get("manuscript_text") or ""
    product_id = product.get("product_id")
    
    logger.info("Processing product: %s", title)

    short_data = shorten_link(destination_url)
    short_link = short_data["short_url"]

    snippet = manuscript[:500] if manuscript else title
    promo_text = generate_promo(title, snippet, targeting=product)
    body = clean_text(strip_link(promo_text, short_link))
    logger.info("Post text: %s | link: %s", body, short_link)

    tags = product.get("hashtags")
    style = product.get("image_style") or ""
    tag_list = [t.lstrip("#") for t in (tags.replace(",", " ").split() if isinstance(tags, str) else (tags or []))]

    video_path, video_url = None, None
    try:
        video_path = generate_short_video(title, snippet, short_link, script=body, style=style, tags=tags)
        if video_path and platforms.is_active("instagram") and not DRY_RUN:
            video_url = upload_public_video(video_path)
    except Exception as e:
        logger.exception("Multi-media generation failed: %s", e)

    post = Post(title=title, body=body, link=short_link, tags=tag_list,
                video_path=video_path, video_url=video_url, product_id=product_id)

    statuses = platforms.publish_all(post)
    manual = {}
    if video_path:
        full = f"{body}\n\n{short_link}"
        if prepare_tiktok_package(video_path, title, full, short_link, tags=tags):
            manual["tiktok"] = ("manual", "package ready in generated_media/")
        if statuses.get("instagram", ("",))[0] in ("pending", "failed", "skipped"):
            if prepare_instagram_package(video_path, title, full, short_link, tags=tags):
                manual["instagram (manual)"] = ("manual", "package ready in generated_media/")

    web_url = None if DRY_RUN else publish_web(title, body, short_link, tag_list, product_id,
                                                brand=os.environ.get("BRAND_NAME", "Mamachi"))
    manual["web"] = ("posted", f"files written to docs/; live at {web_url} once Pages deploys") if web_url else (("dry-run", "") if DRY_RUN else ("failed", "see log"))
    platforms.write_summary(statuses, manual)

    posted = [n for n, s in {**statuses, **manual}.items() if s[0] == "posted"]
    if DRY_RUN:
        logger.info("[DRY-RUN] Skipping campaign log")
        return True
    if not posted:
        logger.error("Nothing was published.")
        return False

    try:
        asset_payload = {
            "caption": body,
            "short_url": short_link,
            "video_url": video_url
        }
        asyncio.run(publish_omnichannel_campaign(product, asset_payload))
    except Exception as e:
        logger.warning("Omnichannel publishing notice: %s", e)

    log_entry = {
        "product_id": product_id,
        "platform": ",".join(posted),
        "generated_caption": body,
        "short_url": short_link,
        "shortio_id": short_data.get("shortio_id"),
        "video_path": video_path,
        "clicks_count": 0,
    }
    try:
        supabase.table("mamachi_campaign_logs").insert(log_entry).execute()
        logger.info("Campaign logged successfully")
    except Exception as e:
        logger.error("Failed to log campaign: %s", e)
    return True

# -----------------------------------------------------------------------------
# Script Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        ok = run_campaign()
    except Exception as e:
        logger.exception("Campaign crashed: %s", e)
        send_alert(f"Campaign crashed: {e}")
        raise
    sys.exit(0 if ok else 1)
