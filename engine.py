import os
import json
import re
from datetime import datetime
from pathlib import Path
from supabase import create_client, Client

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
BRAND_NAME = os.environ.get("BRAND_NAME", "Mamachi")

def get_supabase_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_static_pages():
    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Privacy Policy Page
    policy_html = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - {BRAND_NAME}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>.glass-panel {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); }}</style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col justify-between">
    <header class="sticky top-0 z-40 w-full glass-panel border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <a href="index.html" class="font-extrabold text-xl text-white">{BRAND_NAME}<span class="text-sky-500">.</span></a>
            <a href="advertise.html" class="px-4 py-2 rounded-xl bg-sky-500 text-white font-bold text-xs uppercase">Launch Ad</a>
        </div>
    </header>
    <main class="max-w-3xl mx-auto px-6 py-12 space-y-6">
        <h1 class="text-4xl font-black text-white">Privacy Policy</h1>
        <p class="text-slate-400 text-sm leading-relaxed">At {BRAND_NAME}, we prioritize your privacy. All vendor data, campaign metrics, and custom media uploads are securely encrypted and utilized strictly for 24/7 automated omnichannel promotion across authorized networks.</p>
        <h2 class="text-xl font-bold text-white pt-4">Data Protection & Compliance</h2>
        <p class="text-slate-400 text-sm leading-relaxed">We adhere to rigorous data protection standards. Campaign assets and contact information are never sold or shared with unauthorized third parties.</p>
    </main>
    <footer class="py-6 border-t border-slate-800 text-center text-xs text-slate-500">&copy; 2026 {BRAND_NAME}. All rights reserved.</footer>
</body>
</html>"""
    with open(docs_dir / "policy.html", "w", encoding="utf-8") as f:
        f.write(policy_html)

    # 2. Contact Us Page (Routes securely to mitiku.woldesenbe.org@gmail.com)
    contact_html = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Contact Us - {BRAND_NAME}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>.glass-panel {{ background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(16px); }}</style>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col justify-between">
    <header class="sticky top-0 z-40 w-full glass-panel border-b border-slate-800">
        <div class="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
            <a href="index.html" class="font-extrabold text-xl text-white">{BRAND_NAME}<span class="text-sky-500">.</span></a>
            <a href="advertise.html" class="px-4 py-2 rounded-xl bg-sky-500 text-white font-bold text-xs uppercase">Launch Ad</a>
        </div>
    </header>
    <main class="max-w-xl mx-auto px-6 py-12 space-y-6 w-full">
        <div class="text-center space-y-2">
            <h1 class="text-3xl font-black text-white">Contact Our Support Team</h1>
            <p class="text-slate-400 text-xs">Have questions about your campaign or media uploads? Send us a message below.</p>
        </div>
        <!-- Form submission securely routed via Formspree or backend to mitiku.woldesenbe.org@gmail.com -->
        <form action="https://formspree.io/f/mitiku.woldesenbe.org@gmail.com" method="POST" class="p-8 rounded-3xl bg-slate-900 border border-slate-800 space-y-4">
            <div>
                <label class="block text-xs font-bold text-slate-300 mb-1">Your Name</label>
                <input type="text" name="name" required class="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-sky-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-xs font-bold text-slate-300 mb-1">Your Email</label>
                <input type="email" name="email" required class="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-sky-500 focus:outline-none">
            </div>
            <div>
                <label class="block text-xs font-bold text-slate-300 mb-1">Message</label>
                <textarea name="message" rows="4" required class="w-full px-4 py-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-sky-500 focus:outline-none"></textarea>
            </div>
            <button type="submit" class="w-full py-4 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 text-white font-black text-xs uppercase tracking-wider shadow-lg">Send Secure Message</button>
        </form>
    </main>
    <footer class="py-6 border-t border-slate-800 text-center text-xs text-slate-500">&copy; 2026 {BRAND_NAME}. All rights reserved.</footer>
</body>
</html>"""
    with open(docs_dir / "contact.html", "w", encoding="utf-8") as f:
        f.write(contact_html)

def update_main_feed(posts: list):
    docs_dir = Path("docs")
    cards_html = ""
    for p in posts:
        cards_html += f"""
        <div class="group rounded-3xl bg-slate-900 border border-slate-800 overflow-hidden shadow-2xl hover:border-slate-700 transition-all flex flex-col justify-between transform hover:-translate-y-1 duration-300">
            <div>
                <div class="relative aspect-video overflow-hidden">
                    <img src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=800&q=80" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 animate-pulse-slow" alt="Thumbnail">
                    <div class="absolute top-4 left-4 bg-sky-500 text-white font-extrabold text-[10px] uppercase px-3 py-1 rounded-full shadow">
                        Live Campaign
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
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{BRAND_NAME} Intelligence Feed & Automated Ads</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{ brand: {{ 500: '#0ea5e9', 600: '#0284c7' }} }},
                    fontFamily: {{ sans: ['Inter', 'sans-serif'] }},
                    animation: {{ 'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite' }}
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
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen flex flex-col justify-between">

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

    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12 w-full">
        <section class="max-w-4xl mx-auto text-center space-y-6">
            <div class="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-bold uppercase tracking-wider animate-pulse-slow">
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

    <footer class="max-w-7xl mx-auto px-4 py-10 mt-12 border-t border-slate-800 text-center text-xs text-slate-500 space-y-3 w-full">
        <div class="flex justify-center gap-6 font-semibold">
            <a href="policy.html" class="hover:text-sky-400 transition-colors">Privacy & Policy</a>
            <a href="contact.html" class="hover:text-sky-400 transition-colors">Contact Us</a>
        </div>
        <p>&copy; 2026 {BRAND_NAME} Automated Advertising Engine. All rights reserved.</p>
    </footer>
    <script>lucide.createIcons();</script>
</body>
</html>
"""
    with open(docs_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(index_html)

def main():
    print("🚀 Starting Mamachi Ad Engine...")
    generate_static_pages()
    
    supabase = get_supabase_client()
    products = []
    if supabase:
        try:
            res = supabase.table("mamachi_products").select("*").eq("is_active", True).execute()
            products = res.data
        except Exception:
            pass
            
    if not products:
        products = [{
            "product_title": "Mamachi AD Engine Launch",
            "manuscript_text": "Discover how the Mamachi AD Engine automates round-the-clock organic promotion for authors and digital creators.",
            "destination_url": "https://mamachiad.github.io/mamachi-ad-engine/advertise.html",
            "service_category": "book_publication"
        }]
        
    published_posts = []
    for p in products:
        # Generate web post logic here (or reuse your existing generator)
        published_posts.append({
            "filename": "20261013-155255.html",
            "title": p.get("product_title"),
            "body": p.get("manuscript_text"),
            "link": p.get("destination_url")
        })
        
    update_main_feed(published_posts)
    print("✨ Intelligence Feed, Policy, and Contact pages generated successfully!")

if __name__ == "__main__":
    main()
