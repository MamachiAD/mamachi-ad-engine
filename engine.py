import os
import json
import re
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client

# --- ENVIRONMENT CONFIG ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BRAND_NAME = os.environ.get("BRAND_NAME", "Mamachi")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ Supabase credentials missing. Running in mock/dry mode.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_web_post(product: dict) -> tuple:
    title = product.get("product_title", "Mamachi Featured Promotion")
    body = product.get("manuscript_text", "Discover how Mamachi automates round-the-clock organic promotion for authors and digital creators.")
    link = product.get("destination_url", "https://mamachiad.github.io/mamachi-ad-engine/advertise.html")
    category = product.get("service_category", "book_publication")
    
    now = datetime.utcnow()
    date_str = now.strftime("%b %d, %Y")
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}.html"
    
    docs_dir = Path("docs")
    posts_dir = docs_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = posts_dir / filename
    hero_img = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1600&q=80"

    html_content = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {BRAND_NAME} Intelligence Feed</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{ brand: {{ 500: '#0ea5e9', 600: '#0284c7' }} }},
                    fontFamily: {{ sans: ['Inter', 'sans-serif'] }}
                }}
            }}
        }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .glass-panel {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); }}
        .gradient-text {{ background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen">

    <header class="sticky top-0 z-40 w-full glass-panel border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="../index.html" class="flex items-center gap-2.5">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-600 to-pink-500 flex items-center justify-center text-white font-black text-xl shadow-lg">M</div>
                <span class="font-extrabold text-xl tracking-tight text-white">{BRAND_NAME}<span class="text-sky-500">.</span></span>
            </a>
            <a href="../advertise.html" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg shadow-sky-500/25">
                ⚡ Create Campaign
            </a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-10 space-y-10">
        <a href="../index.html" class="inline-flex items-center gap-2 text-xs font-bold text-sky-400 hover:underline">
            <i data-lucide="arrow-left" class="w-4 h-4"></i> Back to Intelligence Feed
        </a>

        <div class="space-y-4 text-center">
            <span class="px-3.5 py-1.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-bold uppercase tracking-wider">
                {category.replace('_', ' ').title()}
            </span>
            <h1 class="text-3xl sm:text-5xl font-black text-white leading-tight">{title}</h1>
            <p class="text-xs text-slate-400">{date_str} &bull; Verified AI Campaign &bull; Syndicated Globally</p>
        </div>

        <div class="relative rounded-3xl overflow-hidden shadow-2xl border border-slate-800 aspect-video">
            <img src="{hero_img}" alt="{title}" class="w-full h-full object-cover">
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/40 to-transparent"></div>
            <div class="absolute bottom-6 left-6 right-6 flex items-end justify-between">
                <span class="text-xs font-bold text-sky-400 uppercase tracking-widest bg-slate-900/80 px-3 py-1 rounded-full border border-slate-700">Active Omnichannel Promotion</span>
                <a href="{link}" target="_blank" class="px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-black text-xs uppercase tracking-wider shadow-2xl">
                    ⚡ GET IT HERE
                </a>
            </div>
        </div>

        <div class="p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-6">
            <h2 class="text-xl font-bold text-white border-b border-slate-800 pb-3">Campaign Overview</h2>
            <p class="text-slate-300 text-base sm:text-lg leading-relaxed">{body}</p>
            <div class="pt-4 border-t border-slate-800 flex justify-between items-center">
                <span class="text-xs text-slate-400">Official Secure Link:</span>
                <a href="{link}" target="_blank" class="px-6 py-3 rounded-xl bg-sky-500 hover:bg-sky-400 text-white font-bold text-xs uppercase">
                    Visit Destination ↗
                </a>
            </div>
        </div>

        <!-- Omnichannel Social Preview Tabs -->
        <div class="space-y-6 p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl">
            <div class="text-center space-y-2">
                <span class="text-xs font-bold text-sky-400 uppercase tracking-widest bg-sky-500/10 px-3.5 py-1 rounded-full border border-sky-500/20">Omnichannel Ad Engine Preview</span>
                <h3 class="text-xl font-black text-white">How This Post Converts Across Social Platforms</h3>
                <p class="text-xs text-slate-400">Automatically syndicated with custom hashtags, short tracking links, and rich media.</p>
            </div>
            
            <div class="flex flex-wrap justify-center gap-2 border-b border-slate-800 pb-4">
                <button onclick="switchTab('youtube')" id="tab-youtube" class="px-4 py-2 rounded-xl bg-sky-500 text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5"><i data-lucide="youtube" class="w-4 h-4"></i> YouTube</button>
                <button onclick="switchTab('instagram')" id="tab-instagram" class="px-4 py-2 rounded-xl bg-slate-950 text-slate-400 hover:text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5"><i data-lucide="instagram" class="w-4 h-4"></i> Instagram</button>
                <button onclick="switchTab('tiktok')" id="tab-tiktok" class="px-4 py-2 rounded-xl bg-slate-950 text-slate-400 hover:text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5"><i data-lucide="video" class="w-4 h-4"></i> TikTok</button>
                <button onclick="switchTab('facebook')" id="tab-facebook" class="px-4 py-2 rounded-xl bg-slate-950 text-slate-400 hover:text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5"><i data-lucide="facebook" class="w-4 h-4"></i> Facebook</button>
                <button onclick="switchTab('twitter')" id="tab-twitter" class="px-4 py-2 rounded-xl bg-slate-950 text-slate-400 hover:text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5"><i data-lucide="twitter" class="w-4 h-4"></i> X / Twitter</button>
            </div>

            <!-- YouTube Tab Content -->
            <div id="content-youtube" class="platform-content space-y-4">
                <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <span class="text-xs font-bold text-red-400 uppercase">YouTube Shorts / Video Ad Caption</span>
                    <p class="text-sm text-white font-medium">{title} — Streamlining autonomous growth. Check out the full offering below! 🚀</p>
                    <div class="flex flex-wrap gap-2 text-xs text-sky-400 font-semibold">
                        <span>#AI</span><span>#MarketingAutomation</span><span>#{category.replace('_', '')}</span><span>#Mamachi</span>
                    </div>
                    <div class="pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Short Link: <a href="{link}" target="_blank" class="text-sky-400 hover:underline">{link}</a></span>
                        <span class="text-emerald-400 font-bold">● Active 24/7</span>
                    </div>
                </div>
            </div>

            <!-- Instagram Tab Content -->
            <div id="content-instagram" class="platform-content space-y-4" style="display:none;">
                <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <span class="text-xs font-bold text-pink-400 uppercase">Instagram Reel & Feed Post</span>
                    <p class="text-sm text-white font-medium">✨ {title} is now live! Transform your promotional reach with hyper-local AI precision. Link in bio & below!</p>
                    <div class="flex flex-wrap gap-2 text-xs text-sky-400 font-semibold">
                        <span>#DigitalCreator</span><span>#BookMarketing</span><span>#GrowthHacking</span><span>#MamachiAds</span>
                    </div>
                    <div class="pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Targeting Link: <a href="{link}" target="_blank" class="text-sky-400 hover:underline">{link}</a></span>
                        <span class="text-emerald-400 font-bold">● Active 24/7</span>
                    </div>
                </div>
            </div>

            <!-- TikTok Tab Content -->
            <div id="content-tiktok" class="platform-content space-y-4" style="display:none;">
                <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <span class="text-xs font-bold text-cyan-400 uppercase">TikTok Viral Ad Brief</span>
                    <p class="text-sm text-white font-medium">How {title} is changing the game for creators everywhere 📈 Tap to explore.</p>
                    <div class="flex flex-wrap gap-2 text-xs text-sky-400 font-semibold">
                        <span>#LearnOnTikTok</span><span>#TechTrends</span><span>#Creators</span><span>#Mamachi</span>
                    </div>
                    <div class="pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Promo Link: <a href="{link}" target="_blank" class="text-sky-400 hover:underline">{link}</a></span>
                        <span class="text-emerald-400 font-bold">● Active 24/7</span>
                    </div>
                </div>
            </div>

            <!-- Facebook Tab Content -->
            <div id="content-facebook" class="platform-content space-y-4" style="display:none;">
                <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <span class="text-xs font-bold text-blue-400 uppercase">Facebook Page Campaign Post</span>
                    <p class="text-sm text-white font-medium">📢 Now Available: {title}. Explore our latest verified release designed to scale your brand organically across global channels.</p>
                    <div class="flex flex-wrap gap-2 text-xs text-sky-400 font-semibold">
                        <span>#BusinessGrowth</span><span>#Publishing</span><span>#MamachiEngine</span>
                    </div>
                    <div class="pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Secure URL: <a href="{link}" target="_blank" class="text-sky-400 hover:underline">{link}</a></span>
                        <span class="text-emerald-400 font-bold">● Active 24/7</span>
                    </div>
                </div>
            </div>

            <!-- Twitter/X Tab Content -->
            <div id="content-twitter" class="platform-content space-y-4" style="display:none;">
                <div class="p-5 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
                    <span class="text-xs font-bold text-sky-400 uppercase">X / Twitter Post & Thread</span>
                    <p class="text-sm text-white font-medium">⚡ Automated Release: {title}. Experience 24/7 omnichannel promotion with hyper-local geo-targeting. 🧵👇</p>
                    <div class="flex flex-wrap gap-2 text-xs text-sky-400 font-semibold">
                        <span>#AIgrowth</span><span>#IndieHacker</span><span>#Mamachi</span>
                    </div>
                    <div class="pt-2 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
                        <span>Access Link: <a href="{link}" target="_blank" class="text-sky-400 hover:underline">{link}</a></span>
                        <span class="text-emerald-400 font-bold">● Active 24/7</span>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <footer class="max-w-7xl mx-auto px-4 py-10 border-t border-slate-800 text-center text-xs text-slate-500">
        <p>&copy; 2026 {BRAND_NAME} Automated Advertising Engine. All rights reserved.</p>
    </footer>

    <script>
        lucide.createIcons();
        function switchTab(platform) {{
            ['youtube', 'instagram', 'tiktok', 'facebook', 'twitter'].forEach(p => {{
                const content = document.getElementById('content-' + p);
                const tab = document.getElementById('tab-' + p);
                if (content && tab) {{
                    content.style.display = (p === platform) ? 'block' : 'none';
                    tab.className = (p === platform) ? 
                        'px-4 py-2 rounded-xl bg-sky-500 text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5' : 
                        'px-4 py-2 rounded-xl bg-slate-950 text-slate-400 hover:text-white font-bold text-xs uppercase transition-all flex items-center gap-1.5';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return filename, title, body, link

def update_main_feed(posts: list):
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    cards_html = ""
    for p in posts:
        cards_html += f"""
        <div class="group rounded-3xl bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl hover:border-slate-700 transition-all flex flex-col justify-between">
            <div>
                <div class="relative aspect-video overflow-hidden">
                    <img src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" alt="Thumbnail">
                    <div class="absolute top-4 left-4 bg-sky-500 text-white font-extrabold text-[10px] uppercase px-3 py-1 rounded-full shadow">
                        Verified Active
                    </div>
                </div>
                <div class="p-6 space-y-3">
                    <span class="text-xs font-semibold text-sky-400">Mamachi Intelligence Feed</span>
                    <h3 class="text-xl font-black text-white group-hover:text-sky-400 transition-colors">
                        {p['title']}
                    </h3>
                    <p class="text-slate-400 text-xs sm:text-sm line-clamp-3 leading-relaxed">
                        {p['body']}
                    </p>
                </div>
            </div>
            <div class="p-6 pt-0 flex items-center justify-between border-t border-slate-800/80 mt-4">
                <a href="posts/{p['filename']}" class="text-xs font-bold text-sky-400 hover:underline flex items-center gap-1">
                    Read Full Story <i data-lucide="arrow-right" class="w-3.5 h-3.5"></i>
                </a>
                <a href="{p['link']}" target="_blank" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-black text-xs uppercase tracking-wider shadow-lg">
                    GET IT HERE
                </a>
            </div>
        </div>
        """

    index_html = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{BRAND_NAME} Intelligence Feed & Automated Ads</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{ brand: {{ 500: '#0ea5e9', 600: '#0284c7' }} }},
                    fontFamily: {{ sans: ['Inter', 'sans-serif'] }}
                }}
            }}
        }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .glass-panel {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); }}
        .gradient-text {{ background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen">

    <header class="sticky top-0 z-40 w-full glass-panel border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <a href="index.html" class="flex items-center gap-2.5">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-indigo-600 to-pink-500 flex items-center justify-center text-white font-black text-xl shadow-lg">M</div>
                <span class="font-extrabold text-xl tracking-tight text-white">{BRAND_NAME}<span class="text-sky-500">.</span></span>
            </a>
            <a href="advertise.html" class="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-bold text-xs uppercase tracking-wider shadow-lg">
                ⚡ Launch Ad Campaign
            </a>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        <section class="max-w-4xl mx-auto text-center space-y-6">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-bold uppercase tracking-wider">
                <i data-lucide="sparkles" class="w-3.5 h-3.5"></i> Mamachi Intelligence Feed
            </div>
            <h1 class="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
                Discover Verified Offers & <span class="gradient-text">Omnichannel Campaigns</span>
            </h1>
            <p class="text-slate-400 text-base sm:text-lg max-w-2xl mx-auto">
                Explore active promotions, viral reports, and automated campaigns published 24/7 across our global publishing network.
            </p>
        </section>

        <section class="max-w-6xl mx-auto space-y-6">
            <div class="flex items-center justify-between border-b border-slate-800 pb-4">
                <h2 class="text-xl font-extrabold text-white flex items-center gap-2">
                    <i data-lucide="flame" class="w-5 h-5 text-amber-400"></i> Active Feed Releases
                </h2>
                <a href="advertise.html" class="text-xs font-bold text-sky-400 hover:underline">Promote Your Product →</a>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
                {cards_html}
            </div>
        </section>
    </main>

    <footer class="max-w-7xl mx-auto px-4 py-10 border-t border-slate-800 text-center text-xs text-slate-500">
        <p>&copy; 2026 {BRAND_NAME} Automated Advertising Engine. All rights reserved.</p>
    </footer>
    <script>lucide.createIcons();</script>
</body>
</html>
"""
    
    with open(docs_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
        
    with open(docs_dir / "posts.json", "w", encoding="utf-8") as f:
        json.dump([{"id": p["filename"].replace(".html", ""), "title": p["title"]} for p in posts], f, indent=2)

def main():
    print("🚀 Starting Mamachi Ad Engine...")
    supabase = get_supabase_client()
    
    products = []
    if supabase:
        try:
            res = supabase.table("mamachi_products").select("*").eq("is_active", True).execute()
            products = res.data
        except Exception as e:
            print(f"⚠️ Error fetching from Supabase: {e}")
            
    if not products:
        print("ℹ️ No active products found in Supabase. Using default featured campaign.")
        products = [{
            "product_title": "Mamachi AD Engine Launch",
            "manuscript_text": "Discover how the Mamachi AD Engine automates round-the-clock organic promotion for authors and digital creators.",
            "destination_url": "https://mamachiad.github.io/mamachi-ad-engine/advertise.html",
            "service_category": "book_publication"
        }]
        
    published_posts = []
    for p in products:
        filename, title, body, link = generate_web_post(p)
        published_posts.append({
            "filename": filename,
            "title": title,
            "body": body,
            "link": link
        })
        print(f"✅ Published web post: {title}")
        
    update_main_feed(published_posts)
    print("✨ Intelligence Feed & Social Tabs updated successfully in docs/")

if __name__ == "__main__":
    main()
