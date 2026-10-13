# Switch platforms on, one at a time

**How it works:** every platform is OFF until all of its secrets exist (GitHub repo: Settings, Secrets and variables, Actions). Add them whenever you have them. The next run posts there automatically. After every run, open the run page: the **Summary** shows each platform as posted, pending (with the exact missing secret) or failed.
**Already working with zero setup:** the web channel (a site plus RSS feed in `docs/`) and the TikTok/Instagram ready-to-upload packages (set variable `VIDEO_ENABLED=true`, `TIKTOK_ENABLED=true`, `INSTAGRAM_ENABLED=true`).

## Turn on the web channel (2 minutes)
Repo Settings, Pages, "Deploy from a branch", branch `main`, folder `/docs`. Your site appears at `https://<owner>.github.io/<repo>/` after the next run.

## Easiest, free, stable (start here)
| Platform | Secrets | How |
|---|---|---|
| Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | @BotFather makes the bot token. Add the bot as admin of your channel. Chat id is `@yourchannel`. Sends the video when there is one. |
| Bluesky | `BSKY_HANDLE`, `BSKY_APP_PASSWORD` | Settings, App Passwords. Handle like `you.bsky.social`. Link is clickable. |
| Mastodon | `MASTODON_INSTANCE`, `MASTODON_TOKEN` | On your server: Preferences, Development, New application (scope `write:statuses`). Instance like `https://mastodon.social`. |
| Discord | `DISCORD_WEBHOOK_URL` | Channel settings, Integrations, Webhooks. |

## Needs a developer app (more steps, check each platform's current rules)
| Platform | Secrets | Notes |
|---|---|---|
| Facebook Page | `FB_PAGE_ID`, `FB_PAGE_ACCESS_TOKEN` | Meta developer app, long-lived Page token with page posting permission. Optional `FB_API_VERSION` (default v23.0, check Meta's changelog). |
| Instagram Reels | `IG_USER_ID`, `IG_ACCESS_TOKEN` | Professional account linked to a Facebook Page, token with publish permission. Instagram must download the video from a public URL, so create a **public** Supabase Storage bucket named `promo-videos` (or set `SUPABASE_VIDEO_BUCKET`). Until then you get the manual package. |
| YouTube Shorts | `YOUTUBE_TOKEN_JSON` | Run `youtube_auth_once.py` once on your computer, paste its output. Set the Google OAuth screen to "In production" or the token expires in 7 days. Unaudited API projects are forced to private uploads. Daily upload quota is small. |
| LinkedIn | `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_AUTHOR_URN` | Tokens expire (about 60 days), so expect to renew. |
| X | `X_BEARER_TOKEN` | Must be an OAuth 2.0 **user** token with tweet.write. An app-only token cannot post. Check X's current free limits. |

## Not automatic yet
- **TikTok:** its posting API needs app review. Until then the engine makes a ready package (video.mp4, caption.txt) in the `generated-media` artifact on each run. Download it and upload in the app.
- **Pinterest, Reddit, Threads, blogs:** can be added later as new entries in `platforms.py`. Reddit and group posting are strict about self-promotion, so I'd keep those manual.

## Safety switches
- `DISABLE_PLATFORMS=x,linkedin` (a repository Variable) pauses platforms without deleting secrets.
- Run the workflow with "Dry run" ticked to test without posting.
- Add `DISCLAIMER` (a Variable) such as "Not financial advice." for the wealth book. It is added to Facebook, LinkedIn and Telegram.
