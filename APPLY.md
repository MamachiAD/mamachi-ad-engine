# Mamachi fixes: how to apply (about 10 minutes, all in the GitHub website)

Upload these into your repo (**Add file > Upload files**, then Commit):
- `web_publish.py`  -> repo root, next to `engine.py` (replaces the old one; this is what fixes `KeyError: 'body'`)
- `ai_chain.py`     -> repo root, next to `engine.py` (new file)
- `docs/index.html` -> replaces `docs/index.html` (home page now builds itself from the feed)
- `docs/feed.json`  -> new file in `docs/` (starts with your 3 existing posts; the engine adds new ones on top)
- `tests/`          -> optional, for local checks

## 1. Edit engine.py (two small changes)
Add this line with the other imports at the top:
    from ai_chain import ask_text

Replace the whole `generate_promo` function with:

    def generate_promo(title: str, snippet: str, short_link: str) -> str:
        prompt = (
            f"Write a promotional post (2 sentences, under 230 characters, plain text, no Markdown, no asterisks) "
            f"for the book titled '{title}'.\n"
            f"Use this manuscript snippet for inspiration:\n{snippet}\n\n"
            "Rules: be specific and honest. Do not promise results, income or returns. "
            "Do not use urgency or fear-of-missing-out phrases. Do not include a link or hashtags.\n"
        )
        logger.info("Generating promo...")
        text, used = ask_text(
            prompt,
            lambda model, p: ai_client.models.generate_content(model=model, contents=p).text,
            GEMINI_MODELS, GEMINI_TOTAL_BUDGET_S,
        )
        text = clean_text(text) if text else ""
        if text:
            logger.info("Promo generated with %s", used)
            return text
        logger.error("All AI providers failed. Using static fallback.")
        send_alert("AI unavailable, used static fallback promo")
        return f"New from Mamachi: '{title}'. Take a look at what's inside."

Also change `GEMINI_TIMEOUT_MS = 60_000` to `25_000` so one slow call cannot hold a run up.

## 2. Edit your workflow file (.github/workflows/<your run-engine file>.yml)
Replace the commit/push step so it pulls first, and add the concurrency block near the top:

    concurrency:
      group: run-engine
      cancel-in-progress: false

    - name: Commit web feed
      run: |
        git config user.name "mamachi-bot"
        git config user.email "mamachi-bot@users.noreply.github.com"
        git add -A docs
        git diff --cached --quiet || git commit -m "update web feed"
        git pull --rebase origin main
        git push

Your repo settings must allow it: Settings > Actions > General > Workflow permissions > Read and write.

## 3. Optional free backup AI
Add any of these as repository secrets so the engine keeps working when Gemini's free quota runs out:
GROQ_API_KEY, OPENROUTER_API_KEY, MISTRAL_API_KEY.
