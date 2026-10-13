import os
import re
from datetime import datetime
from pathlib import Path

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'[\s-]+', '-', text).strip('-')[:50]

def publish_web(title: str, body: str, link: str, tags: list, product_id: str = "", brand: str = "Mamachi", video_url: str = None) -> str:
    now = datetime.utcnow()
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    slug = slugify(title)
    filename = f"{timestamp}.html"
    
    docs_dir = Path("docs")
    posts_dir = docs_dir / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = posts_dir / filename
    
    # Random rich hero image fallback if none provided
    hero_img = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80"

    html_content = f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {brand}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{ brand: {{ 500: '#0ea5e9', 600: '#0284c7' }} }}
                }}
            }}
        }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans min-h-screen">

    <!-- Sticky Header -->
    <header class="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800">
        <div class="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <a href="../index.html" class="flex items-center gap-2 font-black text-xl text-white">
                <div class="w-8 h-8 rounded-lg bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center">M</div>
                {brand}.
            </a>
            <a href="../advertise.html" class="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-bold text-xs uppercase tracking-wider shadow-lg">
                ⚡ Create Your Campaign
            </a>
        </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-10 space-y-8">
        <a href="../index.html" class="inline-flex items-center gap-2 text-xs font-bold text-sky-400 hover:underline">
            <i data-lucide="arrow-left" class="w-4 h-4"></i> Back to Main Feed
        </a>

        <!-- Header Titles -->
        <div class="space-y-3">
            <span class="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 text-xs font-bold border border-emerald-500/20 uppercase">
                Verified Release
            </span>
            <h1 class="text-3xl sm:text-5xl font-black text-white leading-tight">{title}</h1>
            <p class="text-xs text-slate-400">{date_str} &bull; Official Announcement</p>
        </div>

        <!-- Featured Visual Header Image -->
        <div class="relative rounded-3xl overflow-hidden shadow-2xl border border-slate-800 aspect-video">
            <img src="{hero_img}" alt="{title}" class="w-full h-full object-cover">
            <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent"></div>
        </div>

        <!-- Call To Action Card -->
        <div class="p-6 sm:p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-xl space-y-6">
            <p class="text-slate-300 text-base sm:text-lg leading-relaxed">{body}</p>
            
            <div class="pt-4 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                <span class="text-xs font-bold text-slate-400">Ready to boost your business or launch an ad?</span>
                <a href="{link}" target="_blank" class="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-black text-xs uppercase tracking-wider text-center shadow-lg active:scale-95 transition-all">
                    ⚡ GET IT HERE
                </a>
            </div>
        </div>
    </main>

    <script>lucide.createIcons();</script>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return f"https://mamachiad.github.io/mamachi-ad-engine/posts/{filename}"
