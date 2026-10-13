import os
import time
import logging
from typing import Optional, Any, Dict

import requests
from google import genai
from supabase import Client, create_client

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Environment helpers
# -----------------------------------------------------------------------------
def _get_env(key: str, required: bool = False) -> str:
    value = os.environ.get(key, "").strip().strip('"\'')
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


# Required
SUPABASE_URL = _get_env("SUPABASE_URL", required=True)
SUPABASE_KEY = _get_env("SUPABASE_KEY", required=True)
SHORTIO_API_KEY = _get_env("SHORTIO_API_KEY", required=True)
GEMINI_API_KEY = _get_env("GEMINI_API_KEY", required=True)

# Optional social credentials (everything still works without them)
FB_PAGE_ACCESS_TOKEN = _get_env("FB_PAGE_ACCESS_TOKEN")
FB_PAGE_ID = _get_env("FB_PAGE_ID")
LINKEDIN_ACCESS_TOKEN = _get_env("LINKEDIN_ACCESS_TOKEN")
LINKEDIN_AUTHOR_URN = _get_env("LINKEDIN_AUTHOR_URN")
X_BEARER_TOKEN = _get_env("X_BEARER_TOKEN")

# Optional extras
SHORTIO_DOMAIN = _get_env("SHORTIO_DOMAIN") or "mamachi-engine.s.gy"
DRY_RUN = _get_env("DRY_RUN").lower() in ("1", "true", "yes")
ALERT_WEBHOOK_URL = _get_env("ALERT_WEBHOOK_URL")

# -----------------------------------------------------------------------------
# Clients
# -----------------------------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# -----------------------------------------------------------------------------
# Alert helper
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
# Social posting (all optional – safe to run with zero credentials)
# -----------------------------------------------------------------------------
def post_to_facebook(text: str, link: str) -> bool:
    if DRY_RUN:
        logger.info("[DRY-RUN] Would post to Facebook")
        return True
    if not (FB_PAGE_ACCESS_TOKEN and FB_PAGE_ID):
        logger.info("Facebook credentials not set — skipping")
        return False

    try:
        response = requests.post(
            f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed",
            data={
                "message": text,
                "link": link,
                "access_token": FB_PAGE_ACCESS_TOKEN,
            },
            timeout=15,
        )
        if response.status_code == 200:
            logger.info("Posted to Facebook")
            return True
        logger.error("Facebook error (%s): %s", response.status_code, response.text)
    except Exception as e:
        logger.exception("Facebook exception: %s", e)
    return False


def post_to_linkedin(text: str, link: str) -> bool:
    if DRY_RUN:
        logger.info("[DRY-RUN] Would post to LinkedIn")
        return True
    if not (LINKEDIN_ACCESS_TOKEN and LINKEDIN_AUTHOR_URN):
        logger.info("LinkedIn credentials not set — skipping")
        return False

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": LINKEDIN_AUTHOR_URN,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "ARTICLE",
                "media": [{"status": "READY", "originalUrl": link}],
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    try:
        response = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            json=payload,
            headers=headers,
            timeout=15,
        )
        if response.status_code in (200, 201):
            logger.info("Posted to LinkedIn")
            return True
        logger.error("LinkedIn error (%s): %s", response.status_code, response.text)
    except Exception as e:
        logger.exception("LinkedIn exception: %s", e)
    return False


def post_to_x(text: str) -> bool:
    if DRY_RUN:
        logger.info("[DRY-RUN] Would post to X")
        return True
    if not X_BEARER_TOKEN:
        logger.info("X credentials not set — skipping")
        return False

    try:
        response = requests.post(
            "https://api.twitter.com/2/tweets",
            json={"text": text},
            headers={
                "Authorization": f"Bearer {X_BEARER_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        if response.status_code in (200, 201):
            logger.info("Posted to X")
            return True
        logger.error("X error (%s): %s", response.status_code, response.text)
    except Exception as e:
        logger.exception("X exception: %s", e)
    return False


# -----------------------------------------------------------------------------
# Short.io
# -----------------------------------------------------------------------------
def shorten_link(original_url: str) -> Dict[str, Any]:
    result = {"short_url": original_url, "shortio_id": None, "raw": None}

    if not SHORTIO_API_KEY:
        logger.warning("SHORTIO_API_KEY missing — using original URL")
        return result

    try:
        response = requests.post(
            "https://api.short.io/links",
            json={
                "originalURL": original_url,
                "domain": SHORTIO_DOMAIN,
                "allowDuplicates": False,
            },
            headers={
                "Authorization": SHORTIO_API_KEY,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=10,
        )
        if response.status_code in (200, 201):
            data = response.json()
            short = data.get("secureShortURL") or data.get("shortURL")
            if short:
                result["short_url"] = short
                result["shortio_id"] = data.get("idString") or data.get("id")
                result["raw"] = data
                logger.info("Short link created: %s", short)
                return result
        logger.warning("Short.io failed (%s): %s", response.status_code, response.text)
    except Exception as e:
        logger.warning("Short.io exception: %s", e)

    return result


# -----------------------------------------------------------------------------
# Gemini
# -----------------------------------------------------------------------------
def generate_promo(title: str, snippet: str, short_link: str) -> str:
    prompt = (
        f"Write an engaging 2-sentence promotional post for the book titled '{title}'.\n"
        f"Use this manuscript snippet for inspiration:\n{snippet}\n\n"
        f"End the post with this exact link: {short_link}\n"
        "Tone: professional yet exciting. Avoid hashtags unless they feel natural."
    )

    logger.info("Generating promo with Gemini...")
    last_error = None

    for attempt in range(1, 4):
        try:
            response = ai_client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
            )
            text = (response.text or "").strip()
            if text:
                return text
            raise ValueError("Empty response from Gemini")
        except Exception as e:
            last_error = e
            wait = 2 ** attempt
            logger.warning("Gemini attempt %d failed: %s → retry in %ds", attempt, e, wait)
            time.sleep(wait)

    raise RuntimeError(f"Gemini failed after 3 attempts: {last_error}")


# -----------------------------------------------------------------------------
# Main campaign
# -----------------------------------------------------------------------------
def run_campaign() -> None:
    if DRY_RUN:
        logger.info("=== DRY-RUN MODE — no real posts or DB writes ===")

    # 1. Fetch latest active product
    response = (
        supabase.table("mamachi_products")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        logger.warning("No active products found")
        return

    product = response.data[0]
    title = product.get("product_title")
    destination_url = product.get("destination_url")
    manuscript = product.get("manuscript_text") or ""
    product_id = product.get("product_id")

    if not title or not destination_url:
        msg = "Product missing product_title or destination_url"
        logger.error(msg)
        send_alert(msg, {"product": product})
        return

    logger.info("Processing product: %s", title)

    # 2. Shorten link
    short_data = shorten_link(destination_url)
    short_link = short_data["short_url"]

    # 3. Generate promo
    snippet = manuscript[:500] if manuscript else title
    promo_text = generate_promo(title, snippet, short_link)
    logger.info("Generated copy:\n%s", promo_text)

    # 4. Post to social platforms (all optional)
    results = {
        "facebook": post_to_facebook(promo_text, short_link),
        "linkedin": post_to_linkedin(promo_text, short_link),
        "x": post_to_x(promo_text),
    }

    posted = [p for p, ok in results.items() if ok]
    if posted:
        logger.info("Posted to: %s", ", ".join(posted))
    else:
        logger.info("No social platforms configured or all skipped — continuing with logging only")

    # 5. Log to Supabase (skip in dry-run)
    if DRY_RUN:
        logger.info("[DRY-RUN] Skipping campaign log")
        return

    log_entry = {
        "product_id": product_id,
        "platform": "omni-channel",
        "generated_caption": promo_text,
        "short_url": short_link,
        "shortio_id": short_data.get("shortio_id"),
        "clicks_count": 0,
    }

    try:
        supabase.table("mamachi_campaign_logs").insert(log_entry).execute()
        logger.info("Campaign logged successfully")
    except Exception as e:
        logger.exception("Failed to log campaign: %s", e)
        send_alert("Failed to insert campaign log", {"error": str(e)})


if __name__ == "__main__":
    try:
        run_campaign()
    except Exception as e:
        logger.exception("Campaign crashed: %s", e)
        send_alert(f"Campaign crashed: {e}")
        raise
