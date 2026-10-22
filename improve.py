"""Run daily (see .github/workflows/self-improve.yml). Reads link clicks for recent posts, finds which writing angles earn the most,
saves new angle weights for the engine, and sends you a short digest. Safe by design: it changes weights only, never code or prices."""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

import requests

import learning

log = logging.getLogger(__name__)


def short_clicks(link_id: str, key: str) -> Optional[int]:
    r = requests.get(f"https://statistics.short.io/statistics/link/{link_id}", params={"period": "total", "tz": "UTC"}, headers={"Authorization": key}, timeout=20)
    if r.status_code != 200:
        return None
    j = r.json()
    v = j.get("totalClicks", j.get("humanClicks"))
    return int(v) if v is not None else None


def refresh(sb, key: str, now: datetime, limit: int = 60) -> int:
    rows = sb.table("mamachi_learning").select("*").execute().data or []
    stale = [r for r in rows if r.get("shortio_id") and (not r.get("checked_at") or datetime.fromisoformat(r["checked_at"].replace("Z", "+00:00")) < now - timedelta(hours=20))]
    done = 0
    for r in stale[:limit]:
        c = short_clicks(r["shortio_id"], key)
        if c is not None:
            sb.table("mamachi_learning").update({"clicks": c, "checked_at": now.isoformat()}).eq("id", r["id"]).execute()
            r["clicks"] = c
            done += 1
    return done


def reweight(sb) -> Dict[str, Dict[str, float]]:
    rows = sb.table("mamachi_learning").select("*").execute().data or []
    stats: Dict[str, List[int]] = {}
    for r in rows:
        if r.get("angle") in learning.ANGLES and r.get("checked_at"):
            stats.setdefault(r["angle"], []).append(int(r.get("clicks") or 0))
    overall = sum(sum(v) for v in stats.values()) / max(1, sum(len(v) for v in stats.values()))
    out: Dict[str, Dict[str, float]] = {}
    for a in learning.ANGLES:
        v = stats.get(a, [])
        avg = (sum(v) + overall * 3) / (len(v) + 3)                 # shrink small samples toward the overall average
        out[a] = {"posts": len(v), "avg_clicks": round(avg, 2), "weight": round(max(0.2, min(3.0, avg / overall)), 2) if overall > 0 else 1.0}
    sb.table("mamachi_settings").upsert({"key": "angle_weights", "value": {a: x["weight"] for a, x in out.items()}}).execute()
    return out


def digest(res: Dict[str, Dict[str, float]]) -> str:
    ranked = sorted(res.items(), key=lambda kv: -kv[1]["avg_clicks"])
    lines = [f"{a}: {x['avg_clicks']} avg clicks over {x['posts']} posts (weight {x['weight']})" for a, x in ranked]
    return "Learning report. The engine now favours: " + ", ".join(a for a, _ in ranked[:2]) + ".\n" + "\n".join(lines)


def run(sb, key: str, tell: Callable[[str], None], now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    n = refresh(sb, key, now) if key else 0
    res = reweight(sb)
    if n:
        tell(digest(res))
    return {"refreshed": n, "weights": res}


if __name__ == "__main__":
    from supabase import create_client
    logging.basicConfig(level=logging.INFO)

    def tell(text: str) -> None:
        t, c = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
        if t and c:
            requests.post(f"https://api.telegram.org/bot{t}/sendMessage", data={"chat_id": c, "text": text[:4000]}, timeout=20)
        print(text)
    print(run(create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"]), os.environ.get("SHORTIO_API_KEY", ""), tell))
