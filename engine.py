import os
import time
import requests
from google import genai
from google.genai.errors import ServerError
from supabase import Client, create_client

# 1. Load and sanitize environment secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip().strip('"\'')
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "").strip().strip('"\'')
SHORTIO_API_KEY = os.environ.get("SHORTIO_API_KEY", "").strip().strip('"\'')
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip().strip('"\'')

# Safe diagnostic check
print(
    f"DEBUG: SUPABASE_URL status -> Length: {len(SUPABASE_URL)}, Starts"
    f" with https: {SUPABASE_URL.startswith('https://')}"
)

if not SUPABASE_URL or not SUPABASE_URL.startswith("https://"):
  raise ValueError(
      "ERROR: SUPABASE_URL is empty or does not start with 'https://'. Please"
      " check your GitHub Repository Secrets."
  )

if not SUPABASE_KEY:
  raise ValueError("ERROR: SUPABASE_KEY is missing.")

# 2. Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY)


def run_campaign():
  # 3. Fetch active product, prioritizing the newest row
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

  # Map table columns
  title = product.get("product_title")
  destination_url = product.get("destination_url")
  manuscript = product.get("manuscript_text", "")

  print(f"Processing product: {title}")
  print(f"Destination URL: {destination_url}")

  # 4. Shorten link using Short.io API
  short_link = destination_url
  try:
    shortio_url = "https://api.short.io/links"
    headers = {"authorization": SHORTIO_API_KEY, "content-type": "application/json"}
    payload = {"originalURL": destination_url, "domain": "mamachi-engine.s.gy"}
    short_res = requests.post(shortio_url, json=payload, headers=headers)
    if short_res.status_code in [200, 201]:
      short_data = short_res.json()
      short_link = short_data.get("secureShortURL", destination_url)
    else:
      print(f"Short.io Warning ({short_res.status_code}): {short_res.text}")
  except Exception as e:
    print(f"Short.io Exception: {e}")

  # 5. Generate promo content with Gemini (with built-in retry handling for 503s)
  snippet = manuscript[:500] if manuscript else title
  prompt = (
      f"Write an engaging 2-sentence promotional post for the book '{title}'. "
      f"Details/Manuscript snippet: {snippet}... "
      f"Include this link: {short_link}"
  )

  print("Generating promotional copy with Gemini...")
  promo_text = None
  models_to_try = ["gemini-flash-latest", "gemini-2.5-flash"]
  
  for model_name in models_to_try:
    retries = 3
    for attempt in range(retries):
      try:
        ai_response = ai_client.models.generate_content(
            model=model_name,
            contents=prompt,
        )
        promo_text = ai_response.text
        break
      except ServerError as e:
        print(f"Model {model_name} busy (Attempt {attempt+1}/{retries}): {e}")
        time.sleep(3)  # Wait 3 seconds before retrying
      except Exception as e:
        print(f"Error with model {model_name}: {e}")
        break
    if promo_text:
      break

  if not promo_text:
    raise RuntimeError("Failed to generate content from Gemini after multiple attempts due to high demand.")

  print(f"Generated Copy:\n{promo_text}")

  # 6. Save campaign execution log in Supabase
  log_entry = {
      "product_id": product.get("product_id"),
      "generated_link": short_link,
      "promo_text": promo_text,
      "status": "published",
  }
  supabase.table("mamachi_campaign_logs").insert(log_entry).execute()
  print("Campaign created and logged successfully in Supabase!")


if __name__ == "__main__":
  run_campaign()
