import json, os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
tmp = tempfile.mkdtemp(); os.environ["DOCS_DIR"] = tmp
shutil.copy(os.path.join(os.path.dirname(__file__), "..", "docs", "feed.json"), tmp)
import web_publish
def check(c, m): print(("PASS  " if c else "FAIL  ") + m); sys.exit(1) if not c else None
url = web_publish.publish_web("SI, Super Intelligence Super Wealth", "Read <b>this</b> & enjoy.", "https://mamachi-engine.s.gy/aQT4PX", ["#SuperIntelligence", "AIEconomy"], "p1", brand="Mamachi")
check(url and url.startswith("https://mamachiad.github.io/mamachi-ad-engine/posts/"), "1. Returns the live URL like engine.py expects")
page = open(os.path.join(tmp, "posts", url.split("/")[-1])).read()
check("&lt;b&gt;this&lt;/b&gt;" in page and "<b>this</b>" not in page, "2. Post text is HTML-escaped (no injection)")
check("https://mamachi-engine.s.gy/aQT4PX" in page and "GET IT HERE" in page and "og:title" in page, "3. Button uses the short link; link-preview tags present")
feed = json.load(open(os.path.join(tmp, "feed.json")))
check(len(feed) == 4 and feed[0]["body"].startswith("Read") and feed[0]["tags"] == ["SuperIntelligence", "AIEconomy"], "4. Feed updated: new post first, 3 old posts kept")
check(web_publish.publish_web("x", None, "https://a.b", None, None) is not None, "5. Missing body/tags does not crash (the old KeyError)")
