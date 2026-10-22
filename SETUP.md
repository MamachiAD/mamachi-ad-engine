# GO LIVE TODAY: Mamachi Ads checklist (about 60 to 90 minutes)

Do these in order. Each step ends with a check, so you know it worked before you move on.

## A. Database (5 minutes)
You already ran `supabase.sql` and `SEED.sql`. Now run ONE more file:
1. Supabase > **SQL Editor > New query** > paste the contents of `supabase-update.sql` > **Run**. It is safe to run twice.
2. Check: **Table Editor** shows `mamachi_kv`, `mamachi_learning` and `mamachi_settings`, and `mamachi_orders` has the new columns `geo_country`, `geo_areas` and `ad_prompt`.

## B. PayPal (already mostly done)
- Your Live app "MamachiAD" exists and its **Client ID is already inside `docs/advertise.html`**. Compare it with your PayPal screen: a capital I and a lowercase l look alike.
- The **Secret key** goes ONLY into Cloudflare in step C. Never into a web page or a chat.
- All card payments, and every other method PayPal offers, arrive in your PayPal account. Withdraw to your Kenyan bank from inside PayPal.

## C. Cloudflare worker (15 minutes, no KV needed any more)
1. cloudflare.com > **Workers & Pages > Create > Create Worker**, name it `mamachi-api` > **Deploy** > **Edit code** > replace everything with `worker/worker.js` > **Deploy**.
2. **Settings > Variables and Secrets > Add**, as type **Secret**. Only five are needed to take payments:

| Secret | Value |
|---|---|
| `PAYPAL_CLIENT_ID` | the same Client ID as in advertise.html |
| `PAYPAL_SECRET` | your PayPal secret key |
| `SUPABASE_URL` | `https://hwmuvewmkytzqnivperx.supabase.co` |
| `SUPABASE_KEY` | your Supabase **service_role** key |
| `NOTIFY_SECRET` | a long random text (also goes into GitHub in step E) |

Optional, add any time: `TELEGRAM_BOT_TOKEN` and `OWNER_TELEGRAM_CHAT_ID` (alerts to you), `EMAIL_WEBHOOK` and `EMAIL_SECRET` (vendor emails, see `email-gateway.gs`), `SHORTIO_API_KEY` (click statistics), `VAULT_KEY` (own-account posting).
To make a random text, press F12 in your browser, open Console and run: `[...crypto.getRandomValues(new Uint8Array(24))].map(b=>b.toString(16).padStart(2,'0')).join('')`
3. **Check:** open `https://YOUR-WORKER-ADDRESS/health` in a browser (the address ends in `.workers.dev`). You want `paypal_login`, `supabase_orders_table`, `supabase_kv_table`, `price_list` and `place_list` all saying `ok`. Anything else tells you exactly what to fix. The page reveals no secrets.

## D. Tell the site where the worker is (1 minute, ONE place)
Edit `docs/site.json` and replace `https://YOUR-WORKER.workers.dev` with your worker address. The checkout page, tracking page and contact form all read it from there.

## E. GitHub (15 minutes)
1. Upload to the repo root: `engine.py`, `platforms.py`, `ads.py`, `ai_chain.py`, `web_publish.py`, `scout.py`, `learning.py`, `improve.py`, `reach.py`. Upload the whole `docs/` folder over your `docs/`. Upload `.github/workflows/scout.yml` and `.github/workflows/self-improve.yml`.
2. **Settings > Secrets and variables > Actions > New repository secret**: `WORKER_BASE_URL` (worker address, no slash at the end), `NOTIFY_SECRET` (the same text as in the worker), `SITE_URL` (`https://mamachiad.github.io/mamachi-ad-engine`).
3. Your run-engine workflow must run at `0 */6 * * *` (00:00, 06:00, 12:00, 18:00 UTC). The posting times shown to buyers are built on those hours.
4. **Check:** Actions tab > run **self-improve** manually. It should go green.

## F. Test the whole flow before real customers (10 minutes)
1. Open your site > **Launch Your Smart Ads Campaign**, order the cheapest ad ($2, one hour, local, feed) for a place you choose, and pay with a **different** PayPal account (a friend's). You cannot pay yourself.
2. You get a Telegram message (if set up). In Supabase > `mamachi_orders` the row says `paid_review` and `amount` is correct.
3. Set `status` to `approved`. At the next run time (00, 06, 12 or 18 UTC) the ad posts. The tracking page link (shown after payment) shows the area covered, posts made, reach and clicks.
4. Refund the test payment inside PayPal.

## G. Everyday use
- **Approve or reject ads:** Supabase > `mamachi_orders` > set `status` to `approved` or `rejected`. Rejected orders are refunded automatically.
- **Your own products and services (free, unlimited):** Supabase > `mamachi_products` > Insert row.
- **Change prices:** edit `docs/pricing.json` on GitHub. The worker reads the same file, so the site and server never disagree. Optional `"minOrder": 5` stops tiny orders being eaten by PayPal fees (PayPal's fee on small international payments is a large share of $2).
- **The system learns:** every day `self-improve` counts link clicks per writing style and gives more weight to what works. It also counts the real followers of each channel for the reach reports. It only changes writing styles, never code or prices.
- **Locations:** buyers pick a country and up to 3 areas. We name them in the ad, add local hashtags, post at local prime time, and report the area covered, our reach and where clicks came from. Social platforms do not allow ordinary posts to be fenced by country, so we say so openly.

## H. Tests (optional, nothing is sent anywhere)
`node tests/worker.test.mjs`, `python3 tests/test_engine.py`, `python3 tests/test_improve.py`, `python3 tests/test_reach.py`, `python3 tests/test_scout.py`
