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


CSS = ("body{font:17px/1.6 Andika,Arial,sans-serif;background:#FFF6DF;color:#3A1A0A;margin:0}"
       "header{background:linear-gradient(#4FB3EE,#D3EEFB);padding:28px 20px;text-align:center}"
       "main{max-width:760px;margin:0 auto;padding:20px}"
       "article{background:#fff;border:3px solid #3A1A0A;border-radius:16px;padding:16px 20px;margin:16px 0}"
       "a.btn{display:inline-block;background:#E8661A;color:#fff;padding:10px 20px;border:3px solid #3A1A0A;"
       "border-radius:24px;text-decoration:none;font-weight:700}small{color:#6b4a35}")


def _page(title: str, body: str, desc: str = "", canonical: str = "") -> str:
    can = f'<link rel="canonical" href="{E(canonical)}">' if canonical else ""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{E(title)}</title><meta name="description" content="{E(desc[:160])}">'
            f'<meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc[:200])}">{can}'
            f'<link rel="alternate" type="application/rss+xml" href="feed.xml"><style>{CSS}</style></head><body>{body}</body></html>')


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
        for p in posts:
            art = (f'<main><p><a href="../index.html">All posts</a></p><article><h1>{E(p["title"])}</h1><p>{E(p["body"])}</p>'
                   f'<p><a class="btn" href="{E(p["link"])}" rel="noopener">Get it here</a></p>'
                   f'<small>{E(p["date"][:10])}</small></article></main>')
            (out / "posts" / f'{p["id"]}.html').write_text(
                _page(f'{p["title"]} | {brand}', f"<header><h2>{E(brand)}</h2></header>{art}", p["body"],
                      f'{base}/posts/{p["id"]}.html' if base else ""), encoding="utf-8")

        cards = "".join(
            f'<article><h2><a href="posts/{p["id"]}.html">{E(p["title"])}</a></h2><p>{E(p["body"])}</p>'
            f'<p><a class="btn" href="{E(p["link"])}" rel="noopener">Get it here</a></p><small>{E(p["date"][:10])}</small></article>'
            for p in posts[:40])
        (out / "index.html").write_text(_page(f"{brand}: books and more", f"<header><h1>{E(brand)}</h1><p>New picks, tips and stories.</p></header><main>{cards}</main>",
                                              f"Latest from {brand}", f"{base}/" if base else ""), encoding="utf-8")

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
