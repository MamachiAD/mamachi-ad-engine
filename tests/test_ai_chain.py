import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import ai_chain
time.sleep = lambda s: None          # keep the test instant
class Err(Exception):
    def __init__(s, code, msg): super().__init__(msg); s.code = code
DAILY = "429 RESOURCE_EXHAUSTED. Quota exceeded for metric generate_content_free_tier_requests, limit: 20 'quotaId': 'GenerateRequestsPerDayPerProjectPerModel-FreeTier' Please retry in 2h52m39.20480653s. 'retryDelay': '10359s'"
def check(c, m): print(("PASS  " if c else "FAIL  ") + m); sys.exit(0 if c else 1) if not c else None
# 1 daily limit on model 1 -> straight to model 2, exactly one call to model 1 (the real log wasted ~100 s here)
calls = []
def g1(m, p):
    calls.append(m)
    if m == "m1": raise Err(429, DAILY)
    return "hello from " + m
t, who = ai_chain.ask_text("x", g1, ["m1", "m2"])
check(who == "gemini:m2" and calls == ["m1", "m2"], "1. Daily quota error -> next model at once, no retries")
# 2 server errors -> one quick retry then next model
calls.clear()
def g2(m, p):
    calls.append(m)
    if m == "m1": raise Err(503, "UNAVAILABLE high demand")
    return "ok"
t, who = ai_chain.ask_text("x", g2, ["m1", "m2"])
check(who == "gemini:m2" and calls == ["m1", "m1", "m2"], "2. 503 -> one retry, then next model")
# 3 short rate limit waits once and succeeds
calls.clear()
def g3(m, p):
    calls.append(m)
    if len(calls) == 1: raise Err(429, "RESOURCE_EXHAUSTED. Please retry in 7.5s.")
    return "ok"
t, who = ai_chain.ask_text("x", g3, ["m1"])
check(who == "gemini:m1" and len(calls) == 2, "3. Per-minute limit (7.5s) -> wait once, then succeed on the same model")
# 4 all Gemini models exhausted -> Groq takes over
os.environ["GROQ_API_KEY"] = "k"
class R:
    status_code = 200; headers = {}; text = ""
    def json(self): return {"choices": [{"message": {"content": "from groq"}}]}
ai_chain.requests.post = lambda *a, **k: R()
def g4(m, p): raise Err(429, DAILY)
t, who = ai_chain.ask_text("x", g4, ["m1", "m2", "m3"])
check(t == "from groq" and who.startswith("groq:"), "4. Every Gemini model out of quota -> Groq takes over")
# 5 everything fails -> (None, None) so the caller can use the static fallback
os.environ.pop("GROQ_API_KEY")
t, who = ai_chain.ask_text("x", g4, ["m1", "m2"])
check(t is None and who is None, "5. Nothing available -> returns None for the static fallback")
