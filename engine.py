import os
import sys
import time
import random
import logging
from typing import Optional, Any, Dict, List

import requests
from google import genai
from google.genai import types
from supabase import Client, create_client

from pathlib import Path

import platforms
from platforms import Post
from web_publish import publish_web
from video_engine import (
    generate_short_video,
    prepare_tiktok_package,
    prepare_instagram_package,
)

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


SUPABASE_URL = _get_env("SUPABASE_URL", required=True)
# IMPORTANT: use the *service_role* key here (GitHub secret only, never in a web page).
# The anon key is blocked by row-level security when inserting campaign logs.
SUPABASE_KEY = _get_env("SUPABASE_KEY", required=True)
SHORTIO_API_KEY = _get_env("SHORTIO_API_KEY", required=True)
GEMINI_API_KEY = _get_env("GEMINI_API_KEY", required=True)

SHORTIO_DOMAIN = _get_env("SHORTIO_DOMAIN") or "mamachi-engine.s.gy"
DRY_RUN = _get_env("DRY_RUN").lower() in ("1", "true", "yes")
ALERT_WEBHOOK_URL = _get_env("ALERT_WEBHOOK_URL")

GEMINI_MODELS: List[str] = [
    "gemini-3.8-flash",
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash",
]
GEMINI_TIMEOUT_MS = 60_000      # one request may take at most 60 s
GEMINI_TOTAL_BUDGET_S = 120     # give up on text generation after 2 minutes

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY, http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS))


# -----------------------------------------------------------------------------
# Text helpers
# -----------------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Remove Markdown marks that social sites would show literally."""
    return " ".join(text.replace("*", "").replace("`", "").split()) if "\n" not in text else \
        "\n".join(" ".join(line.replace("*", "").replace("`", "").split()) for line in text.splitlines()).strip()


def strip_link(text: str, link: str) -> str:
    return text.replace(link, "").strip()


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
# Short.io (allowDuplicates=False reuses the existing short link for the same URL)
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
# Gemini: fast-fail on bad models, overall time budget, calm static fallback
# -----------------------------------------------------------------------------
def generate_promo(title: str, snippet: str, short_link: str) -> str:
    prompt = (
        f"Write a promotional post (2 sentences, under 230 characters, plain text, no Markdown, no asterisks) "
        f"for the book titled '{title}'.\n"
        f"Use this manuscript snippet for inspiration:\n{snippet}\n\n"
        "Rules: be specific and honest. Do not promise results, income or returns. "
        "Do not use urgency or fear-of-missing-out phrases. Do not include a link or hashtags.\n"
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
                if code in (400, 401, 403, 404):   # retrying will not help, try the next model
                    break
                time.sleep(min(2 ** attempt * 3, 20))

    logger.error("All Gemini models failed. Using static fallback. Last error: %s", last_error)
    send_alert("Gemini unavailable, used static fallback promo", {"last_error": str(last_error)})
    return f"New from Mamachi: '{title}'. Take a look at what's inside."


# -----------------------------------------------------------------------------
# Product rotation: promote the product that was promoted longest ago
# -----------------------------------------------------------------------------
def pick_product() -> Optional[Dict[str, Any]]:
    rows = supabase.table("mamachi_products").select("*").eq("is_active", True).execute().data or []
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
# Public video URL (Instagram needs one). Uses a PUBLIC Supabase Storage bucket.
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
        logger.warning("Public video upload failed (is the bucket '%s' created and public?): %s", bucket, e)
        return None


# -----------------------------------------------------------------------------
# Main campaign. Returns True only if something was really published.
# -----------------------------------------------------------------------------
def run_campaign() -> bool:
    if DRY_RUN:
        logger.info("=== DRY-RUN MODE: no real posts or DB writes ===")

    product = pick_product()
    if not product:
        logger.error("No active products found")
        send_alert("No active products found")
        return False

    title = product.get("product_title")
    destination_url = product.get("destination_url")
    manuscript = product.get("manuscript_text") or ""
    product_id = product.get("product_id")
    if not title or not destination_url:
        msg = "Product missing product_title or destination_url"
        logger.error(msg)
        send_alert(msg, {"product": product})
        return False
    logger.info("Processing product: %s", title)

    short_data = shorten_link(destination_url)
    short_link = short_data["short_url"]

    snippet = manuscript[:500] if manuscript else title
    promo_text = generate_promo(title, snippet, short_link)
    body = clean_text(strip_link(promo_text, short_link))
    logger.info("Post text: %s | link: %s", body, short_link)

    tags = product.get("hashtags")             # optional column: "#a #b" or a list
    style = product.get("image_style") or ""   # optional column: how the images should look
    tag_list = [t.lstrip("#") for t in (tags.replace(",", " ").split() if isinstance(tags, str) else (tags or []))]

    # Video (only if VIDEO_ENABLED). A public URL is made only when Instagram is configured.
    video_path, video_url = None, None
    try:
        video_path = generate_short_video(title, snippet, short_link, script=body, style=style, tags=tags)
        if video_path and platforms.is_active("instagram") and not DRY_RUN:
            video_url = upload_public_video(video_path)
    except Exception as e:
        logger.exception("Multi-media generation failed: %s", e)

    post = Post(title=title, body=body, link=short_link, tags=tag_list,
                video_path=video_path, video_url=video_url, product_id=product_id)

    # Every configured platform posts; the rest stay 'pending' until their secrets are added.
    statuses = platforms.publish_all(post)
    manual = {}
    if video_path:
        full = f"{body}\n\n{short_link}"
        if prepare_tiktok_package(video_path, title, full, short_link, tags=tags):
            manual["tiktok"] = ("manual", "package ready in generated_media/")
        if statuses.get("instagram", ("",))[0] in ("pending", "failed", "skipped"):
            if prepare_instagram_package(video_path, title, full, short_link, tags=tags):
                manual["instagram (manual)"] = ("manual", "package ready in generated_media/")

    # Web channel: always on, no secrets needed.
    web_url = None if DRY_RUN else publish_web(title, body, short_link, tag_list, product_id,
                                               brand=os.environ.get("BRAND_NAME", "Mamachi"))
    manual["web"] = ("posted", web_url or "docs/ updated") if web_url else (("dry-run", "") if DRY_RUN else ("failed", "see log"))
    platforms.write_summary(statuses, manual)

    posted = [n for n, s in {**statuses, **manual}.items() if s[0] == "posted"]
    if DRY_RUN:
        logger.info("[DRY-RUN] Skipping campaign log")
        return True
    if not posted:
        logger.error("Nothing was published. Check the platform status table above.")
        send_alert("Run finished but nothing was published", {"product": title})
        return False

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
        hint = " (row-level security: use the service_role key in SUPABASE_KEY)" if "42501" in str(e) else ""
        logger.error("Failed to log campaign: %s%s", e, hint)
        send_alert("Failed to insert campaign log" + hint, {"error": str(e)})
    return True


if __name__ == "__main__":
    try:
        ok = run_campaign()
    except Exception as e:
        logger.exception("Campaign crashed: %s", e)
        send_alert(f"Campaign crashed: {e}")
        raise
    sys.exit(0 if ok else 1)
