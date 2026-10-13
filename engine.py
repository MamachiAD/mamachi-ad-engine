import os
import json
import random
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BRAND_NAME = os.environ.get("BRAND_NAME", "Mamachi")

# Creative Pool for Dynamic Variations
MARKETING_ANGLES = [
    {"angle": "Problem-Solution", "hook_prefix": "Are you ready to unlock the future of AI wealth?"},
    {"angle": "Viral Storyteller", "hook_prefix": "This single shift in super-intelligence is redefining modern wealth creation..."},
    {"angle": "Curiosity & FOMO", "hook_prefix": "Why early adopters are positioning themselves for super-intelligence right now."},
    {"angle": "Expert Analysis", "hook_prefix": "A practical breakdown on navigating the super-intelligence economy."}
]

VISUAL_STYLES = [
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1639762681485-074b7f938ba0?auto=format&fit=crop&w=1600&q=80",
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1600&q=80"
]

VOICE_TONES = ["High-Energy Launch", "Conversational Story", "Authoritative Briefing"]

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_web_post(product: dict, run_count: int = 1) -> tuple:
    title = product.get("product_title", "Mamachi Featured Promotion")
    base_body = product.get("manuscript_text", "Discover how Mamachi automates round-the-clock organic promotion.")
    link = product.get("destination_url", "https://mamachiad.github.io/mamachi-ad-engine/advertise.html")
    category = product.get("service_category", "book_publication")
    
    # Select dynamic elements for this specific run
    angle_obj = random.choice(MARKETING_ANGLES)
    hero_img = random.choice(VISUAL_STYLES)
    voice_tone = random.choice(VOICE_TONES)
    
    # Dynamic copy generation based on current run
    dynamic_hook = angle_obj["hook_prefix"]
    dynamic_body = f"{dynamic_hook} {base_body}"

    now = datetime.utcnow()
    date_str = now.strftime("%b %d, %Y")
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.html"
    
    docs_dir = Path("docs")
    posts_dir = docs_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    filepath = posts_dir / filename

    html_content = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {BRAND_NAME} Creative Release #{run_count}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{ extend: {{ colors: {{ brand: {{ 500: '#0ea5e9' }} }} }} }}
        }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>.glass-panel {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); }}</style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen">

    <header class="sticky top-0 z-40 w-full glass-panel border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
            <a href="../index.html" class="flex items-center gap-2">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center text-white font-black text-xl">M</div>
                <span class="font-extrabold text-xl text-white">{BRAND_NAME}<span class="text-sky-500">.</span></span>
            </a>
            <a href="../advertise.html" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-bold text-xs uppercase">⚡ Launch Ad</a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-10 space-y-8">
        <a href="../index.html" class="inline-flex items-center gap-2 text-xs font-bold text-sky-400 hover:underline">
            ← Back to Feed
        </a>

        <div class="text-center space-y-3">
            <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-bold uppercase">
                Dynamic Creative Angle: {angle_obj['angle']}
            </div>
            <h1 class="text-3xl sm:text-5xl font-black text-white leading-tight">{title}</h1>
            <p class="text-xs text-slate-400">{date_str} &bull; Unique Ad Variation #{run_count} &bull; Tone: {voice_tone}</p>
        </div>

        <div class="relative rounded-3xl overflow-hidden shadow-2xl border border-slate-800 aspect-video">
            <img src="{hero_img}" alt="{title}" class="w-full h-full object-cover">
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent"></div>
            <div class="absolute bottom-6 left-6 right-6 flex items-end justify-between">
                <span class="text-xs font-bold text-sky-400 uppercase bg-slate-900/80 px-3 py-1 rounded-full border border-slate-700">Fresh AI Visual Style</span>
                <a href="{link}" target="_blank" class="px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-black text-xs uppercase">⚡ GET IT HERE</a>
            </div>
        </div>

        <div class="p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-4">
            <h2 class="text-xl font-bold text-white border-b border-slate-800 pb-3">Promotional Overview</h2>
            <p class="text-slate-300 text-base leading-relaxed">{dynamic_body}</p>
            <div class="pt-4 border-t border-slate-800 flex justify-between items-center">
                <span class="text-xs text-slate-400">Official Link:</span>
                <a href="{link}" target="_blank" class="px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-bold text-xs uppercase">Visit Destination ↗</a>
            </div>
        </div>
    </main>
    <script>lucide.createIcons();</script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return filename, title, dynamic_body, link

def main():
    print("🚀 Starting Dynamic Mamachi Ad Engine...")
    supabase = get_supabase_client()
    products = []
    
    if supabase:
        try:
            res = supabase.table("mamachi_products").select("*").eq("is_active", True).execute()
            products = res.data
        except Exception as e:
            print(f"⚠️ Error: {e}")
            
    if not products:
        products = [{
            "product_title": "SI, Super Intelligence Super Wealth",
            "manuscript_text": "How Super-Intelligence (SI), Will Rewrite the Rules of Wealth and How to Position Yourself before Everyone Else.",
            "destination_url": "https://mamachiad.github.io/mamachi-ad-engine/advertise.html",
            "service_category": "book_publication"
        }]

    # Generate fresh dynamic variants for every product
    for idx, p in enumerate(products, start=1):
        filename, title, body, link = generate_web_post(p, run_count=idx)
        print(f"✅ Generated Dynamic Variation #{idx} for: {title}")

if __name__ == "__main__":
    main()
