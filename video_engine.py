"""
Mamachi Free Multi-Media Engine (v2)
Free tools only: Gemini images (if quota allows), Pillow text cards (always works), gTTS/edge-tts voice, ffmpeg.
"""

import os
import re
import json
import time
import base64
import logging
import tempfile
import subprocess
import shutil
import textwrap
from pathlib import Path
from typing import List, Optional, Union

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
def _flag(name: str) -> bool:
    return os.environ.get(name, "false").lower() in ("1", "true", "yes")


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VIDEO_ENABLED = _flag("VIDEO_ENABLED")
YOUTUBE_ENABLED = _flag("YOUTUBE_ENABLED")
TIKTOK_ENABLED = _flag("TIKTOK_ENABLED")
INSTAGRAM_ENABLED = _flag("INSTAGRAM_ENABLED")
TTS_ENGINE = os.environ.get("TTS_ENGINE", "auto").lower()          # auto | gtts | edge  (use gtts on GitHub Actions)
YOUTUBE_PRIVACY = os.environ.get("YOUTUBE_PRIVACY", "public")       # unaudited API projects are forced to private by YouTube
IMAGE_MODELS = [m.strip() for m in os.environ.get("IMAGE_MODELS", "").split(",") if m.strip()] or [
    "gemini-3.1-flash-image",
    "gemini-2.5-flash-image",
]

OUTPUT_DIR = Path(os.environ.get("VIDEO_OUTPUT_DIR", "generated_media"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICE = "en-US-AriaNeural"
MUSIC_PATH = os.environ.get("FREE_MUSIC_PATH", "assets/free_bg_music.mp3")
FONT_CANDIDATES = [
    "assets/Fredoka-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def _font_path() -> Optional[str]:
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return p
    return None


def _tags(value: Union[str, List[str], None]) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        value = re.split(r"[,\s]+", value)
    return [v.lstrip("#") for v in value if v.strip("# ")]


def run_cmd(cmd: List[str], timeout: int = 300) -> bool:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.warning("Command failed (%s):\n%s", cmd[0], result.stderr[-1500:] if result.stderr else "No stderr")
            return False
        return True
    except Exception as e:
        logger.warning("Command error (%s): %s", cmd[0], e)
        return False


def check_ffmpeg() -> bool:
    return run_cmd(["ffmpeg", "-version"], timeout=10)


def probe_duration(path: str) -> Optional[float]:
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
            capture_output=True, text=True, timeout=20,
        )
        return float(out.stdout.strip())
    except Exception:
        return None


# -----------------------------------------------------------------------------
# Images: Gemini first (errors are now logged), Pillow text cards as a reliable fallback
# -----------------------------------------------------------------------------
_dead_models = {}


def _list_image_models() -> None:
    try:
        names = [m.name for m in ai_client.models.list() if "image" in (m.name or "").lower()]
        logger.warning("Image-capable models your key can see: %s", names or "none")
    except Exception as e:
        logger.warning("Could not list models: %s", e)


def generate_images(title: str, snippet: str, count: int = 5, style: str = "") -> List[str]:
    if not ai_client:
        return []

    image_paths: List[str] = []
    base_prompt = (
        f"Vertical 9:16 promotional image for the book '{title}'. "
        f"{style or 'Clean, elegant, modern book-promo look, soft lighting, high detail.'} "
        f"No text, no letters, no watermarks. Inspiration: {snippet[:180]}"
    )

    for i in range(count):
        saved = False
        for model in IMAGE_MODELS:
            if model in _dead_models:
                continue
            try:
                response = ai_client.models.generate_content(
                    model=model,
                    contents=f"{base_prompt} Variation {i + 1}.",
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        # NOTE: output_mime_type is not supported by the Gemini API and raised an error before any request was sent.
                        image_config=types.ImageConfig(aspect_ratio="9:16"),
                    ),
                )
                for part in (response.parts or []):
                    if part.inline_data:
                        data = part.inline_data.data
                        if isinstance(data, str):
                            data = base64.b64decode(data)
                        path = OUTPUT_DIR / f"img_{int(time.time())}_{i}.png"
                        path.write_bytes(data)
                        image_paths.append(str(path))
                        logger.info("Image %d created with %s", i + 1, model)
                        saved = True
                        break
                if saved:
                    break
                logger.warning("%s returned no image data", model)
            except Exception as e:
                code = getattr(e, "code", None)
                logger.warning("Image model %s failed: %s", model, e)
                if code in (400, 401, 403, 404, 429) or isinstance(e, ValueError):
                    _dead_models[model] = str(e)          # do not retry this model in this run
                    if code == 404:
                        _list_image_models()
        if not saved:
            logger.warning("Image %d could not be generated by Gemini", i + 1)
    return image_paths


def fallback_cards(title: str, script: str, count: int) -> List[str]:
    """Branded 1080x1920 text cards. Free, offline, never fails."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as e:
        logger.warning("Pillow missing, no fallback cards: %s", e)
        return []
    fp = _font_path()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()] or [title]
    paths = []
    for i in range(count):
        img = Image.new("RGB", (1080, 1920))
        d = ImageDraw.Draw(img)
        for y in range(1920):
            t = y / 1920
            d.line([(0, y), (1080, y)], fill=(int(79 + 60 * t), int(179 - 20 * t), int(238 - 10 * t)))
        f_big = ImageFont.truetype(fp, 72) if fp else ImageFont.load_default()
        text = sentences[i % len(sentences)]
        lines = textwrap.wrap(text, 22)[:9]
        d.rounded_rectangle([70, 420, 1010, 420 + len(lines) * 92 + 80], 40, fill=(255, 246, 223), outline=(58, 26, 10), width=6)
        for k, ln in enumerate(lines):
            d.text((110, 460 + k * 92), ln, font=f_big, fill=(58, 26, 10))
        p = OUTPUT_DIR / f"card_{int(time.time())}_{i}.png"
        img.save(p)
        paths.append(str(p))
    return paths


# -----------------------------------------------------------------------------
# Voice
# -----------------------------------------------------------------------------
def _edge_tts(text: str, output_path: str) -> bool:
    ok = run_cmd(["edge-tts", "--voice", DEFAULT_VOICE, "--text", text, "--write-media", output_path], timeout=60)
    return ok and Path(output_path).exists() and Path(output_path).stat().st_size > 1000


def _gtts(text: str, output_path: str) -> bool:
    try:
        from gtts import gTTS
        gTTS(text=text, lang="en", slow=False).save(output_path)
        return Path(output_path).exists() and Path(output_path).stat().st_size > 500
    except Exception as e:
        logger.error("gTTS failed: %s", e)
        return False


def generate_voiceover(text: str, output_path: str) -> bool:
    if TTS_ENGINE in ("auto", "edge"):
        if _edge_tts(text, output_path):
            logger.info("Voice generated with edge-tts")
            return True
        if TTS_ENGINE == "edge":
            return False
        logger.info("edge-tts unavailable (often blocked on cloud servers), using gTTS")
    if _gtts(text, output_path):
        logger.info("Voice generated with gTTS")
        return True
    return False


# -----------------------------------------------------------------------------
# Video assembly (one frame per image + zoompan, text from files so no escaping problems)
# -----------------------------------------------------------------------------
def create_vertical_video(images: List[str], voice_path: str, title: str, short_link: str,
                          output_path: str, voice_seconds: float = 20.0) -> bool:
    if not images or not check_ffmpeg():
        return False

    n = len(images)
    per = max(3.0, min(11.0, voice_seconds / n + 0.2))
    frames = int(per * 25)
    total = min(58.0, per * n)          # YouTube Shorts must stay under 60 s

    tmp = Path(tempfile.mkdtemp(prefix="vid_"))
    (tmp / "title.txt").write_text("\n".join(textwrap.wrap(title, 30)[:3]), encoding="utf-8")
    (tmp / "link.txt").write_text(short_link, encoding="utf-8")
    fp = _font_path()
    font_opt = f":fontfile={fp}" if fp else ""

    parts = []
    for i in range(n):
        parts.append(
            f"[{i}:v]scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
            f"zoompan=z='min(zoom+0.0012,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=25,"
            f"setsar=1,format=yuv420p[v{i}]"
        )
    parts.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[base]")
    parts.append(
        f"[base]drawtext=textfile={tmp / 'title.txt'}:expansion=none{font_opt}:fontsize=52:fontcolor=white:"
        f"borderw=4:bordercolor=black@0.65:line_spacing=10:x=(w-text_w)/2:y=90[titled]"
    )
    parts.append(
        f"[titled]drawtext=textfile={tmp / 'link.txt'}:expansion=none{font_opt}:fontsize=42:fontcolor=gold:"
        f"borderw=3:bordercolor=black@0.7:x=(w-text_w)/2:y=h-160[finalv]"
    )

    cmd = ["ffmpeg", "-y"]
    for img in images:
        cmd += ["-i", img]
    cmd += ["-i", voice_path]
    if Path(MUSIC_PATH).exists():
        cmd += ["-stream_loop", "-1", "-i", MUSIC_PATH]
        parts.append(f"[{n + 1}:a]volume=0.15[music];[{n}:a]volume=1.0[voice];[music][voice]amix=inputs=2:duration=shortest[aout]")
        audio_map = ["-map", "[aout]"]
    else:
        audio_map = ["-map", f"{n}:a"]

    cmd += [
        "-filter_complex", ";".join(parts),
        "-map", "[finalv]", *audio_map,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-t", f"{total:.2f}", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-r", "25", output_path,
    ]
    ok = run_cmd(cmd, timeout=600)
    shutil.rmtree(tmp, ignore_errors=True)
    return ok


def generate_short_video(title: str, snippet: str, short_link: str, script: Optional[str] = None,
                         style: str = "", tags=None) -> Optional[str]:
    if not VIDEO_ENABLED:
        logger.info("VIDEO_ENABLED=false, skipping video")
        return None

    logger.info("Video pipeline started: %s", title)
    script = (script or f"Discover {title}.").strip()[:700]

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        voice_path = tmp.name
    images: List[str] = []
    try:
        if not generate_voiceover(script, voice_path):
            logger.error("Voice generation failed completely")
            return None
        voice_seconds = probe_duration(voice_path) or 20.0

        images = generate_images(title, snippet, count=5, style=style)
        if len(images) < 3:
            need = 5 - len(images)
            logger.warning("Only %d Gemini images, adding %d text cards", len(images), need)
            images += fallback_cards(title, script, need)
        if not images:
            logger.error("No images and no fallback cards, cannot build video")
            return None

        output_path = str(OUTPUT_DIR / f"promo_{int(time.time())}.mp4")
        ok = create_vertical_video(images, voice_path, title, short_link, output_path, voice_seconds)
        if ok and Path(output_path).exists():
            logger.info("Vertical video ready: %s (%.0fs)", output_path, probe_duration(output_path) or 0)
            return output_path
        return None
    finally:
        for f in [voice_path, *images]:
            try:
                os.unlink(f)
            except Exception:
                pass


# -----------------------------------------------------------------------------
# YouTube Shorts (works on GitHub Actions through a stored token, no browser needed)
# -----------------------------------------------------------------------------
YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _youtube_creds():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    info = os.environ.get("YOUTUBE_TOKEN_JSON", "").strip()
    if not info:
        return None
    creds = Credentials.from_authorized_user_info(json.loads(info), YT_SCOPES)
    if not creds.valid:
        creds.refresh(Request())
    return creds


def post_to_youtube_shorts(video_path: str, title: str, description: str, tags=None) -> bool:
    if not YOUTUBE_ENABLED:
        return False
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = _youtube_creds()
        if not creds:
            logger.error("YOUTUBE_TOKEN_JSON secret is missing. Run youtube_auth_once.py on your computer once and store its output.")
            return False
        youtube = build("youtube", "v3", credentials=creds)
        tag_list = _tags(tags)
        hashtags = " ".join(f"#{t}" for t in tag_list[:5])
        body = {
            "snippet": {
                "title": f"{title[:85]} #Shorts",
                "description": f"{description}\n\n#Shorts {hashtags}".strip(),
                "tags": ["shorts"] + tag_list[:10],
                "categoryId": "22",
            },
            "status": {"privacyStatus": YOUTUBE_PRIVACY, "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("YouTube upload progress: %d%%", int(status.progress() * 100))
        logger.info("YouTube Short uploaded: https://youtube.com/shorts/%s (privacy: %s)", response["id"], YOUTUBE_PRIVACY)
        return True
    except Exception as e:
        logger.exception("YouTube Shorts failed: %s", e)
        return False


# -----------------------------------------------------------------------------
# TikTok + Instagram ready packages
# -----------------------------------------------------------------------------
def _create_ready_package(platform: str, video_path: str, title: str, caption: str, short_link: str, tags=None) -> Optional[str]:
    if not Path(video_path).exists():
        return None
    package_dir = OUTPUT_DIR / f"{platform}_ready_{int(time.time())}"
    package_dir.mkdir(exist_ok=True)
    shutil.copy2(video_path, package_dir / "video.mp4")
    hashtags = " ".join(f"#{t}" for t in _tags(tags)) or "#books"
    (package_dir / "caption.txt").write_text(f"{caption}\n\n{short_link}\n\n{hashtags}", encoding="utf-8")
    (package_dir / "README.txt").write_text(
        f"{platform.upper()} READY PACKAGE\n1. Open the {platform} app\n2. Upload video.mp4\n"
        "3. Paste everything from caption.txt\n4. Add a sound if you like\n5. Post\n"
        "The video is already vertical 9:16.\n", encoding="utf-8")
    logger.info("%s package ready: %s", platform.capitalize(), package_dir)
    return str(package_dir)


def prepare_tiktok_package(video_path: str, title: str, caption: str, short_link: str, tags=None) -> Optional[str]:
    return _create_ready_package("tiktok", video_path, title, caption, short_link, tags) if TIKTOK_ENABLED else None


def prepare_instagram_package(video_path: str, title: str, caption: str, short_link: str, tags=None) -> Optional[str]:
    return _create_ready_package("instagram", video_path, title, caption, short_link, tags) if INSTAGRAM_ENABLED else None
