"""Run daily. Reads the REAL audience size of each of our channels where the platform lets us, saves it for the tracking pages and
writes docs/audience.json for the website. Channels with no public count are simply left out. Nothing is estimated or invented."""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

log = logging.getLogger(__name__)
E = lambda k: os.environ.get(k, "").strip().strip('"\'')


def _get(url: str, **kw) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, timeout=20, **kw)
        return r.json() if r.status_code == 200 else None
    except Exception as e:
        log.warning("Audience lookup failed for %s: %s", url.split("?")[0], e)
        return None


def collect() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if E("BSKY_HANDLE"):
        j = _get("https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile", params={"actor": E("BSKY_HANDLE")})
        if j and "followersCount" in j:
            out["bluesky"] = {"followers": j["followersCount"]}
    if E("MASTODON_INSTANCE") and E("MASTODON_TOKEN"):
        j = _get(E("MASTODON_INSTANCE").rstrip("/") + "/api/v1/accounts/verify_credentials", headers={"Authorization": "Bearer " + E("MASTODON_TOKEN")})
        if j and "followers_count" in j:
            out["mastodon"] = {"followers": j["followers_count"]}
    if E("TELEGRAM_BOT_TOKEN") and E("TELEGRAM_CHAT_ID"):
        j = _get(f"https://api.telegram.org/bot{E('TELEGRAM_BOT_TOKEN')}/getChatMemberCount", params={"chat_id": E("TELEGRAM_CHAT_ID")})
        if j and j.get("ok"):
            out["telegram"] = {"followers": j["result"]}
    if E("YOUTUBE_API_KEY"):
        j = _get("https://www.googleapis.com/youtube/v3/channels", params={"part": "statistics", "id": E("YOUTUBE_CHANNEL_ID") or "UCdNtRcbA-UjtcMW_PENntBg", "key": E("YOUTUBE_API_KEY")})
        items = (j or {}).get("items") or []
        st = items[0]["statistics"] if items else {}
        if st and not st.get("hiddenSubscriberCount") and "subscriberCount" in st:
            out["youtube"] = {"followers": int(st["subscriberCount"])}
    return out


def run(sb, docs_dir: str = "docs") -> Dict[str, Any]:
    data = collect()
    value = {**data, "_asOf": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    sb.table("mamachi_settings").upsert({"key": "audience", "value": value}).execute()
    os.makedirs(docs_dir, exist_ok=True)
    with open(os.path.join(docs_dir, "audience.json"), "w", encoding="utf-8") as f:
        json.dump(value, f)
    return value


if __name__ == "__main__":
    from supabase import create_client
    logging.basicConfig(level=logging.INFO)
    print(run(create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])))
