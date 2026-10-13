"""
Web channel: always available, needs no secrets. Builds a static site in docs/ (index, one page per post, RSS feed, sitemap)
for GitHub Pages (Settings > Pages > Deploy from branch > main > /docs).
"""
import os
import json
import html
import logging
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)
E = html.escape


def site_url() -> str:
    url = os.environ.get("SITE_URL", "").strip().rstrip("/")
    if url:
        return url
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner.lower()}.github.io/{name}"
    return ""


def _page(title: str, body: str, desc: str = "", canonical: str = "") -> str:
    can = f'<link rel="canonical" href="{E(canonical)}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{E(title)}</title>
    <meta name="description" content="{E(desc[:160])}">
    <meta property="og:title" content="{E(title)}">
    <meta property="og:description" content="{E(desc[:200])}">
    {can}
    <link rel="alternate" type="application/rss+xml" href="feed.xml">
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        brand: {{
                            50: '#f0f9ff', 100: '#e0f2fe', 400: '#38bdf8', 500: '#0ea5e9', 600: '#0284c7', 700: '#0369a1', 900: '#0c4a6e'
                        }},
                        tiktok: '#ff0050', instagram: '#e1306c', youtube: '#ff0000', twitter: '#1da1f2', linkedin: '#0a66c2'
                    }},
                    fontFamily: {{ sans: ['Inter', 'sans-serif'] }}
                }}
            }}
        }}
    </script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        .glass-panel {{ background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }}
        .dark .glass-panel {{ background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); }}
        .gradient-text {{ background: linear-gradient(135deg, #0ea5e9 0%, #6366f1 50%, #ec4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
        #toast {{ transform: translateY(100px); opacity: 0; transition: all 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55); }}
        #toast.show {{ transform: translateY(0); opacity: 1; }}
    </style>
</head>
<body class="bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 font-sans transition-colors duration-300 min-h-screen">
    {body}
    <script>
        lucide.createIcons();
        // Theme Toggle script
        const themeToggleBtn = document.getElementById('theme-toggle');
        if (themeToggleBtn) {
            themeToggleBtn.addEventListener('click', () => {
                document.documentElement.classList.toggle('dark');
                localStorage.theme = document.documentElement.classList.contains('dark') ? 'dark' : 'light';
            });
        }
        if (localStorage.theme === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
        }
        
        // Ad Studio Tab Switcher
        function switchAdTab(platform) {
            document.querySelectorAll('.ad-view').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.ad-tab').forEach(el => {
                el.classList.remove('bg-white', 'dark:bg-slate-800', 'shadow-sm', 'text-youtube');
                el.classList.add('text-slate-600', 'dark:text-slate-400');
            });
            const targetView = document.getElementById('ad-view-' + platform);
            const targetTab = document.getElementById('tab-' + platform);
            if (targetView) targetView.classList.remove('hidden');
            if (targetTab) {
                targetTab.classList.remove('text-slate-600', 'dark:text-slate-400');
                targetTab.classList.add('bg-white', 'dark:bg-slate-800', 'shadow-sm');
            }
            lucide.createIcons();
        }

        // Simulate Ad Click & Toast Notification
        function simulateAdClick(platform) {
            showToast(`Redirecting user from ${platform} Ad to checkout offer...`);
        }

        function showToast(msg) {
            const toast = document.getElementById('toast');
            const toastMsg = document.getElementById('toast-message');
            if (toast && toastMsg) {
                toastMsg.innerText = msg;
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 3500);
            }
        }

        function copyArticleLink() {
            navigator.clipboard.writeText(window.location.href);
            showToast("Page link copied to clipboard!");
        }
    </script>
</body>
</html>"""


def publish_web(title: str, body: str, link: str, tags: list, product_id=None, brand: str = "Mamachi", out_dir: str = "docs") -> Optional[str]:
    try:
        out = Path(out_dir)
        (out / "posts").mkdir(parents=True, exist_ok=True)
        db = out / "posts.json"
        posts = json.loads(db.read_text(encoding="utf-8")) if db.exists() else []
        now = datetime.now(timezone.utc)
        pid = now.strftime("%Y%m%d-%H%M%S")
        posts.insert(0, {"id": pid, "date": now.isoformat(), "title": title, "body": body, "link": link, "tags": tags, "product_id": product_id})
        posts = posts[:200]
        db.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")

        base = site_url()
        
        # Shared Header HTML template
        header_html = f"""
        <!-- Toast Notification -->
        <div id="toast" class="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-slate-900 text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-slate-700">
            <i data-lucide="check-circle-2" class="w-5 h-5 text-emerald-400"></i>
            <span id="toast-message" class="text-sm font-semibold">Action completed successfully!</span>
        </div>

        <header class="sticky top-0 z-40 w-full glass-panel border-b border-slate-200 dark:border-slate-800 transition-colors">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <a href="../index.html" class="flex items-center gap-2.5 group">
                    <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-500 via-indigo-600 to-pink-500 flex items-center justify-center text-white font-black text-xl shadow-lg shadow-brand-500/30 group-hover:scale-105 transition-transform">
                        M
                    </div>
                    <div class="flex flex-col">
                        <span class="font-extrabold text-xl tracking-tight text-slate-900 dark:text-white leading-none">{E(brand)}<span class="text-brand-500">.</span></span>
                        <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">Ad Engine & Publishing</span>
                    </div>
                </a>
                <div class="flex items-center gap-3">
                    <button id="theme-toggle" class="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors" aria-label="Toggle dark mode">
                        <i data-lucide="moon" class="w-5 h-5 hidden dark:block"></i>
                        <i data-lucide="sun" class="w-5 h-5 block dark:hidden"></i>
                    </button>
                    <button onclick="copyArticleLink()" class="flex items-center gap-2 px-4 py-2 text-sm font-semibold text-white bg-brand-600 hover:bg-brand-500 rounded-xl shadow-lg shadow-brand-500/25 transition-all active:scale-95">
                        <i data-lucide="share-2" class="w-4 h-4"></i>
                        <span class="hidden sm:inline">Share Page</span>
                    </button>
                </div>
            </div>
        </header>
        """

        # Build individual post pages
        for p in posts:
            art = f"""
            <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10">
                <div class="space-y-4">
                    <a href="../index.html" class="inline-flex items-center gap-2 text-sm font-bold text-brand-600 dark:text-brand-400 hover:underline">
                        <i data-lucide="arrow-left" class="w-4 h-4"></i> All Posts
                    </a>
                    <h1 class="text-3xl sm:text-5xl font-black text-slate-900 dark:text-white tracking-tight leading-tight">{E(p["title"])}</h1>
                    <div class="flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400 pb-4 border-b border-slate-200 dark:border-slate-800">
                        <span><i data-lucide="calendar" class="w-3.5 h-3.5 inline mr-1"></i> {E(p["date"][:10])}</span>
                        <span>&bull;</span>
                        <span class="text-emerald-500 font-bold">Verified Release</span>
                    </div>
                </div>

                <article class="prose dark:prose-invert max-w-none text-lg text-slate-700 dark:text-slate-300 leading-relaxed space-y-6 bg-white dark:bg-slate-900 p-8 sm:p-12 rounded-3xl shadow-xl border border-slate-200 dark:border-slate-800">
                    <p>{E(p["body"])}</p>
                    
                    <div class="pt-6 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-4">
                        <span class="text-sm font-semibold text-slate-500">Ready to get started?</span>
                        <a class="px-8 py-4 rounded-2xl bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-extrabold text-sm uppercase tracking-wider shadow-xl shadow-brand-500/30 transition-all flex items-center gap-3" href="{E(p["link"])}" rel="noopener">
                            <i data-lucide="zap" class="w-5 h-5"></i> Get it here
                        </a>
                    </div>
                </article>

                <!-- Embedded Multi-Platform Ad Preview Studio -->
                <section class="space-y-6 pt-6">
                    <div class="text-center space-y-2">
                        <span class="text-xs font-bold text-brand-500 uppercase tracking-widest bg-brand-500/10 px-3 py-1 rounded-full">Omnichannel Ad Engine Preview</span>
                        <h3 class="text-2xl font-black">How This Post Converts Across Platforms</h3>
                    </div>
                    
                    <div class="flex justify-center gap-2 flex-wrap p-2 rounded-2xl bg-slate-200 dark:bg-slate-900">
                        <button onclick="switchAdTab('youtube')" id="tab-youtube" class="ad-tab px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider bg-white dark:bg-slate-800 shadow-sm text-youtube flex items-center gap-2"><i data-lucide="youtube" class="w-4 h-4"></i> YouTube</button>
                        <button onclick="switchAdTab('instagram')" id="tab-instagram" class="ad-tab px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-2"><i data-lucide="instagram" class="w-4 h-4"></i> Instagram</button>
                        <button onclick="switchAdTab('tiktok')" id="tab-tiktok" class="ad-tab px-4 py-2 rounded-xl font-bold text-xs uppercase tracking-wider text-slate-600 dark:text-slate-400 flex items-center gap-2"><i data-lucide="video" class="w-4 h-4"></i> TikTok</button>
                    </div>

                    <div class="p-6 rounded-3xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl flex justify-center">
                        <!-- YouTube Ad View -->
                        <div id="ad-view-youtube" class="ad-view w-full max-w-2xl space-y-4">
                            <div class="relative rounded-2xl overflow-hidden aspect-video bg-slate-950 flex items-center justify-center">
                                <div class="absolute top-3 right-3 bg-yellow-500 text-black text-[10px] font-extrabold uppercase px-2 py-0.5 rounded">Sponsored Ad</div>
                                <div class="text-center p-6 space-y-3">
                                    <h4 class="text-lg font-bold text-white">{E(p["title"])}</h4>
                                    <button onclick="simulateAdClick('YouTube')" class="px-5 py-2.5 rounded-xl bg-blue-600 text-white font-bold text-xs uppercase tracking-wider">Visit Offer &bull; Free Access</button>
                                </div>
                            </div>
                        </div>
                        <!-- Instagram Ad View -->
                        <div id="ad-view-instagram" class="ad-view hidden w-full max-w-xs">
                            <div class="relative aspect-[9/16] rounded-3xl overflow-hidden bg-slate-950 p-6 flex flex-col justify-between border-4 border-slate-800">
                                <div class="flex items-center justify-between text-white text-xs"><span class="font-bold">mamachi_official</span><span class="bg-white/20 px-2 py-0.5 rounded">Sponsored</span></div>
                                <div class="space-y-3 text-white text-center">
                                    <p class="text-xs font-medium">{E(p["title"])}</p>
                                    <button onclick="simulateAdClick('Instagram')" class="w-full py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold text-xs uppercase">Learn More</button>
                                </div>
                            </div>
                        </div>
                        <!-- TikTok Ad View -->
                        <div id="ad-view-tiktok" class="ad-view hidden w-full max-w-xs">
                            <div class="relative aspect-[9/16] rounded-3xl overflow-hidden bg-slate-950 p-6 flex flex-col justify-between border-4 border-slate-800">
                                <div class="text-white text-xs font-bold">@mamachi_insights</div>
                                <div class="space-y-3 text-white text-center">
                                    <p class="text-xs font-medium">{E(p["title"])}</p>
                                    <button onclick="simulateAdClick('TikTok')" class="w-full py-2.5 rounded-xl bg-tiktok text-white font-black text-xs uppercase">Get Report</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
            """
            (out / "posts" / f'{p["id"]}.html').write_text(
                _page(f'{p["title"]} | {brand}', f"{header_html}{art}", p["body"],
                      f'{base}/posts/{p["id"]}.html' if base else ""), encoding="utf-8")

        # Build index / home page cards
        cards = "".join(f"""
            <article class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 sm:p-8 shadow-xl hover:shadow-2xl transition-all space-y-4 group">
                <div class="flex items-center justify-between text-xs text-slate-400">
                    <span class="flex items-center gap-1"><i data-lucide="calendar" class="w-3.5 h-3.5"></i> {E(p["date"][:10])}</span>
                    <span class="bg-brand-500/10 text-brand-600 dark:text-brand-400 px-3 py-1 rounded-full font-bold uppercase tracking-wider text-[10px]">Featured Post</span>
                </div>
                <h2 class="text-xl sm:text-2xl font-black text-slate-900 dark:text-white group-hover:text-brand-500 transition-colors">
                    <a href="posts/{p["id"]}.html">{E(p["title"])}</a>
                </h2>
                <p class="text-slate-600 dark:text-slate-300 line-clamp-3 leading-relaxed">{E(p["body"])}</p>
                <div class="pt-4 flex items-center justify-between border-t border-slate-100 dark:border-slate-800">
                    <a href="posts/{p["id"]}.html" class="text-sm font-bold text-brand-600 dark:text-brand-400 flex items-center gap-1.5 hover:translate-x-1 transition-transform">
                        Read Full Story <i data-lucide="arrow-right" class="w-4 h-4"></i>
                    </a>
                    <a class="px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs uppercase tracking-wider shadow-md transition-all" href="{E(p["link"])}" rel="noopener">Get it here</a>
                </div>
            </article>
        """ for p in posts[:40])

        index_body = f"""
        {header_html}
        <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
            <section class="text-center space-y-4 py-6">
                <div class="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-brand-500/10 text-brand-600 dark:text-brand-400 border border-brand-500/20 text-xs font-bold uppercase tracking-wider">
                    <i data-lucide="sparkles" class="w-3.5 h-3.5"></i> Mamachi Intelligence Feed
                </div>
                <h1 class="text-4xl sm:text-6xl font-black tracking-tight text-slate-900 dark:text-white">
                    Super Intelligence & <span class="gradient-text">Super Wealth</span>
                </h1>
                <p class="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                    New picks, tips, viral reports, and omnichannel advertising breakdowns.
                </p>
            </section>
            
            <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
                {cards}
            </section>
        </main>
        """

        (out / "index.html").write_text(_page(f"{brand}: Books, Reports & Ad Engine", index_body,
                                              f"Latest from {brand}", f"{base}/" if base else ""), encoding="utf-8")

        # Build RSS feed
        items = "".join(
            f'<item><title>{E(p["title"])}</title><link>{E(base)}/posts/{p["id"]}.html</link><guid isPermaLink="false">{p["id"]}</guid>'
            f'<description>{E(p["body"])}</description><pubDate>{format_datetime(datetime.fromisoformat(p["date"]))}</pubDate></item>'
            for p in posts[:50])
        (out / "feed.xml").write_text(
            f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>{E(brand)}</title><link>{E(base)}/</link>'
            f'<description>Latest from {E(brand)}</description>{items}</channel></rss>', encoding="utf-8")
        
        if base:
            urls = "".join(f"<url><loc>{E(base)}/posts/{p['id']}.html</loc></url>" for p in posts)
            (out / "sitemap.xml").write_text(
                f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{E(base)}/</loc></url>{urls}</urlset>',
                encoding="utf-8")
                
        (out / ".nojekyll").write_text("", encoding="utf-8")
        logger.info("Web page published to %s/ (live after the workflow commits docs/)", out_dir)
        return f"{base}/posts/{pid}.html" if base else pid
    except Exception as e:
        logger.exception("Web publish failed: %s", e)
        return None
