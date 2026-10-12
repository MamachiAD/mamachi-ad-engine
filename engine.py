import os
import requests
from supabase import create_client, Client
from google import genai

# Load environment secrets
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SHORTIO_API_KEY = os.environ.get("SHORTIO_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ai_client = genai.Client(api_key=GEMINI_API_KEY)

def run_campaign():
    # 1. Fetch active product from Supabase
    response = supabase.table("mamachi_products").select("*").eq("is_active", True).limit(1).execute()
    if not response.data:
        print("No active products found in Supabase.")
        return
    
    product = response.data[0]
    print(f"Processing product: {product['name']}")

    # 2. Shorten link using Short.io API
    short_link = product['target_url'] # Default fallback
    try:
        shortio_url = "https://api.short.io/links"
        headers = {
            "authorization": SHORTIO_API_KEY,
            "content-type": "application/json"
        }
        payload = {
            "originalURL": product['target_url'],
            "domain": "mamachi-engine.s.gy"  # Ensure this matches your Short.io domain/subdomain exact name
        }
        short_res = requests.post(shortio_url, json=payload, headers=headers)
        if short_res.status_code in [200, 201]:
            short_data = short_res.json()
            short_link = short_data.get("secureShortURL", product['target_url'])
        else:
            print(f"Short.io Warning ({short_res.status_code}): {short_res.text}")
    except Exception as e:
        print(f"Short.io Exception: {e}")

    # 3. Generate promo content with Google GenAI
    prompt = f"Write an engaging 2-sentence promotional post for {product['name']}. Description: {product['description']}. Include link: {short_link}"
    
    ai_response = ai_client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    promo_text = ai_response.text

    # 4. Save campaign execution log in Supabase
    log_entry = {
        "product_id": product['id'],
        "generated_link": short_link,
        "promo_text": promo_text,
        "status": "published"
    }
    supabase.table("mamachi_campaign_logs").insert(log_entry).execute()
    print("Campaign created and logged successfully!")

if __name__ == "__main__":
    run_campaign()
