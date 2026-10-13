import os
import time
import requests
from google import genai
from supabase import Client, create_client

# 1. Load Environment Secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().strip('"\'')
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip().strip('"\'')
SHORTIO_API_KEY = os.environ.get("SHORTIO_API_KEY", "").strip().strip('"\'')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip().strip('"\'')

# Free Platform Tokens (Facebook & LinkedIn)
FB_PAGE_ACCESS_TOKEN = os.environ.get("FB_PAGE_ACCESS_TOKEN", "").strip().strip('"\'')
FB_PAGE_ID = os.environ.get("FB_PAGE_ID", "").strip().strip('"\'')

LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip().strip('"\'')
LINKEDIN_AUTHOR_URN = os.environ.get("LINKEDIN_AUTHOR_URN", "").strip().strip('"\'')

# 2. Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY)


def post_to_facebook(text, link):
    """Posts free updates to your Facebook Author Page via Meta Graph API."""
    if not all([FB_PAGE_ACCESS_TOKEN, FB_PAGE_ID]):
        print("⏭️ Facebook credentials missing. Skipping Facebook post.")
        return False
    try:
        url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/feed"
        payload = {
            "message": text,
            "link": link,
            "access_token": FB_PAGE_ACCESS_TOKEN
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("Successfully posted to Facebook Page!")
            return True
        print(f"❌ Facebook Error: {response.text}")
    except Exception as e:
        print(f"❌ Facebook Exception: {e}")
    return False


def post_to_linkedin(text, link):
    """Posts free updates to your LinkedIn profile/page via LinkedIn API."""
    if not all([LINKEDIN_ACCESS_TOKEN, LINKEDIN_AUTHOR_URN]):
        print("⏭️ LinkedIn credentials missing. Skipping LinkedIn post.")
        return False
    try:
        url = "https://api.linkedin.com/v2/ugcPosts"
        headers = {
            "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0"
        }
        payload = {
            "author": LINKEDIN_AUTHOR_URN,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [{
                        "status": "READY",
                        "originalUrl": link
                    }]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code in [200, 201]:
            print("Successfully posted to LinkedIn!")
            return True
        print(f"❌ LinkedIn Error: {response.text}")
    except Exception as e:
        print(f"❌ LinkedIn Exception: {e}")
    return False


def run_campaign():
    # Fetch active product
    response = (
        supabase.table("mamachi_products")
        .select("*")
        .eq("is_active", True)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        print("No active products found in Supabase.")
        return

    product = response.data[0]
    title = product.get("product_title")
    destination_url = product.get("destination_url")
    manuscript = product.get("manuscript_text", "")

    print(f"Processing product: {title}")

    # Shorten link using Short.io
    short_link = destination_url
    try:
        shortio_url = "https://api.short.io/links"
        headers = {"authorization": SHORTIO_API_KEY, "content-type": "application/json"}
        payload = {"originalURL": destination_url, "domain": "mamachi-engine.s.gy"}
        short_res = requests.post(shortio_url, json=payload, headers=headers)
        if short_res.status_code in [200, 201]:
            short_link = short_res.json().get("secureShortURL", destination_url)
    except Exception as e:
        print(f"Short.io Exception: {e}")

    # Generate promo content with Gemini
    snippet = manuscript[:500] if manuscript else title
    prompt = (
        f"Write an engaging 2-sentence promotional post for the book '{title}'. "
        f"Details/Manuscript snippet: {snippet}... "
        f"Include this link: {short_link}"
    )

    print("Generating promotional copy with Gemini...")
    promo_text = None
    for model_name in ["gemini-3.8-flash"]:
        try:
            ai_response = ai_client.models.generate_content(model=model_name, contents=prompt)
            promo_text = ai_response.text
            break
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            time.sleep(2)

    if not promo_text:
        raise RuntimeError("Failed to generate content from Gemini.")

    print(f"Generated Copy:\n{promo_text}")

    # Broadcast to Social Platforms
    post_to_facebook(promo_text, short_link)
    post_to_linkedin(promo_text, short_link)

    # Publish to Web Feed (Supabase `mamachi_campaign_logs`)
    log_entry = {
        "product_id": product.get("product_id"),
        "platform": "omni-channel",
        "generated_caption": promo_text,
        "short_url": short_link,
        "clicks_count": 0,
    }
    supabase.table("mamachi_campaign_logs").insert(log_entry).execute()
    print("Campaign logged to Web Feed & Supabase successfully!")


if __name__ == "__main__":
    run_campaign()
