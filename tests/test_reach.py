"""Test of the real-audience counter. Run: python3 tests/test_reach.py"""
import json, os, sys, tempfile, types
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
class Q:
    def __init__(s, db, n): s.db, s.n, s.f, s.op, s.v = db, n, [], "select", None
    def select(s, *_): return s
    def eq(s, c, v): s.f.append((c, v)); return s
    def update(s, d): s.op, s.v = "update", d; return s
    def insert(s, d): s.op, s.v = "insert", d; return s
    def upsert(s, d): s.op, s.v = "upsert", d; return s
    def execute(s):
        rows = s.db.t.setdefault(s.n, []); hit = [r for r in rows if all(r.get(c) == v for c, v in s.f)]
        if s.op == "insert": rows.append(dict(s.v, id=len(rows) + 1)); return types.SimpleNamespace(data=[rows[-1]])
        if s.op == "upsert":
            for r in rows:
                if r.get("key") == s.v.get("key"): r.update(s.v); break
            else: rows.append(dict(s.v))
            return types.SimpleNamespace(data=[s.v])
        if s.op == "update": [r.update(s.v) for r in hit]; return types.SimpleNamespace(data=hit)
        return types.SimpleNamespace(data=[dict(r) for r in hit])
class SB:
    def __init__(s): s.t = {}
    def table(s, n): return Q(s, n)
fails = 0
def ok(c, m):
    global fails; print(("PASS  " if c else "FAIL  ") + m); fails += 0 if c else 1

import requests
os.environ.update(BSKY_HANDLE="mamachi.bsky.social", MASTODON_INSTANCE="https://mastodon.social", MASTODON_TOKEN="t", TELEGRAM_BOT_TOKEN="BOT", TELEGRAM_CHAT_ID="-100", YOUTUBE_API_KEY="yk")
class Resp:
    def __init__(s, j, code=200): s._j, s.status_code = j, code
    def json(s): return s._j
def get(url, **kw):
    if "bsky" in url: return Resp({"followersCount": 80})
    if "verify_credentials" in url: return Resp({"followers_count": 15})
    if "getChatMemberCount" in url: return Resp({"ok": True, "result": 120})
    if "googleapis" in url: return Resp({"items": [{"statistics": {"subscriberCount": "9", "hiddenSubscriberCount": False}}]})
    return Resp({}, 404)
requests.get = get
import reach
sb, d = SB(), tempfile.mkdtemp(); v = reach.run(sb, d)
ok(v["bluesky"]["followers"] == 80 and v["mastodon"]["followers"] == 15 and v["telegram"]["followers"] == 120 and v["youtube"]["followers"] == 9, "1. Real follower counts read from Bluesky, Mastodon, Telegram and YouTube")
ok(sb.t["mamachi_settings"][0]["key"] == "audience" and json.load(open(os.path.join(d, "audience.json")))["telegram"]["followers"] == 120 and v["_asOf"], "2. Saved for the tracking pages and the website, with the date it was counted")
requests.get = lambda url, **kw: Resp({}, 500)
v2 = reach.collect(); ok(v2 == {}, "3. When a platform will not tell us, the channel is left out. Nothing is estimated or invented")
print("ALL PASSED" if not fails else f"{fails} FAILED"); sys.exit(1 if fails else 0)
