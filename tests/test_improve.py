"""Test of the self-improvement loop. Run: python3 tests/test_improve.py"""
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

import requests, improve, learning, random
CLICKS = {"s1": 40, "s2": 50, "o1": 2, "o2": 0, "b1": 10}
class Resp:
    def __init__(s, j, code=200): s._j, s.status_code = j, code
    def json(s): return s._j
requests.get = lambda url, **kw: Resp({"totalClicks": CLICKS[url.rsplit("/", 1)[-1]]}) if url.rsplit("/", 1)[-1] in CLICKS else Resp({}, 404)
sb = SB(); now = datetime(2026, 10, 18, 5, tzinfo=timezone.utc)
for i, (ang, sid) in enumerate([("story", "s1"), ("story", "s2"), ("offer", "o1"), ("offer", "o2"), ("benefit", "b1"), ("proof", "missing")], 1):
    sb.t.setdefault("mamachi_learning", []).append({"id": i, "kind": "ad", "angle": ang, "shortio_id": sid, "clicks": 0, "checked_at": None})
sent = []; res = improve.run(sb, "KEY", sent.append, now)
ok(res["refreshed"] == 5, "1. Clicks refreshed for the 5 posts the link service knows (the unknown link is skipped, not guessed)")
w = sb.t["mamachi_settings"][0]["value"]
ok(w["story"] > 1.4 and w["offer"] < 0.7 and w["story"] > w["benefit"] > w["offer"], "2. Angles that earn clicks gain weight, weak ones lose it: " + json.dumps(w))
ok(sent and "story" in sent[0] and "avg clicks" in sent[0], "3. You get a plain digest: " + sent[0].splitlines()[0])
sent.clear(); improve.run(sb, "KEY", sent.append, now); ok(not sent, "4. Posts checked in the last 20 hours are not re-fetched (no repeat digest, no wasted calls)")
rnd = random.Random(3); picks = [learning.pick_angle(sb, rnd) for _ in range(900)]
ok(picks.count("story") > picks.count("offer") * 1.6 and set(picks) == set(learning.ANGLES), "5. The engine now picks story clearly more often than offer, yet still tries every angle (cautious with little data)")
sb2 = SB(); improve.run(sb2, "", sent.append, now); ok(all(v == 1.0 for v in sb2.t["mamachi_settings"][0]["value"].values()), "6. With no data yet every angle keeps equal weight 1.0")
print("ALL PASSED" if not fails else f"{fails} FAILED"); sys.exit(1 if fails else 0)
