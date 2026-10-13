"""
Mamachi Free Multi-Media Engine (Final)
100% free tools only
"""

import os
import time
import base64
import logging
import tempfile
import subprocess
import shutil
from pathlib import Path
from typing import List, Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
VIDEO_ENABLED = os.environ.get("VIDEO_ENABLED", "false").lower() in ("1", "true", "yes")
YOUTUBE_ENABLED = os.environ.get("YOUTUBE_ENABLED", "false").lower() in ("1", "true", "yes")
TIKTOK_ENABLED = os.environ.get("TIKTOK_ENABLED", "false").lower() in ("1", "true", "yes")
INSTAGRAM_ENABLED = os.environ.get("INSTAGRAM_ENABLED", "false").lower() in ("1", "true", "yes")

OUTPUT_DIR = Path(os.environ.get("VIDEO_OUTPUT_DIR", "generated_media"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICE = "en-US-AriaNeural"
MUSIC_PATH = os.environ.get("FREE_MUSIC_PATH", "assets/free_bg_music.mp3")

ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


def run_cmd(cmd: List[str], timeout: int = 300) -> bool:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.warning("Command failed:\n%s", result.stderr[-1200:] if result.stderr else "No stderr")
            return False
        return True
    except Exception as e:
        logger.warning("Command error: %s", e)
        return False


def check_ffmpeg() -> bool:
    return run_cmd(["ffmpeg", "-version"], timeout=10)


# -----------------------------------------------------------------------------
# Free Images
# -----------------------------------------------------------------------------
def generate_images(title: str, snippet: str, count: int = 5) -> List[str]:
    if not ai_client:
        return []

    image_paths = []
    models = ["gemini-3.1-flash-image", "gemini-3.1-flash-lite-image", "gemini-nano-banana-2.1"]

    base_prompt = (
        f"Cinematic vertical 9:16 promotional image for the book '{title}'. "
        f"Luxurious futuristic AI & wealth aesthetic, elegant lighting, high detail, "
        f"no text, no watermarks. Inspiration: {snippet[:180]}"
    )

    for i in range(count):
        prompt = f"{base_prompt} Variation {i+1}."
        saved = False
        for model in models:
            try:
                response = ai_client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="9:16",
                            output_mime_type="image/png",
                        ),
                    ),
                )
                for part in response.parts:
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
            except Exception as e:
                logger.debug("%s failed: %s", model, e)
        if not saved:
            logger.warning("Image %d could not be generated", i + 1)
    return image_paths


# -----------------------------------------------------------------------------
# Free Voice (Improved with strong fallback)
# -----------------------------------------------------------------------------
def generate_voiceover(text: str, output_path: str) -> bool:
    """
    Free voiceover generation with strong fallback.
    1. Tries edge-tts (best quality)
    2. Falls back to gTTS if edge-tts fails
    """
    # --- Try edge-tts first ---
    try:
        cmd = [
            "edge-tts",
            "--voice", DEFAULT_VOICE,
            "--text", text,
            "--write-media", output_path,
        ]
        success = run_cmd(cmd, timeout=60)
        if success and Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
            logger.info("Voice generated successfully with edge-tts")
            return True
        else:
            logger.warning("edge-tts produced empty or failed file, falling back to gTTS...")
    except Exception as e:
        logger.warning("edge-tts failed: %s → falling back to gTTS", e)

    # --- Fallback to gTTS ---
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(output_path)

        if Path(output_path).exists() and Path(output_path).stat().st_size > 500:
            logger.info("Voice generated successfully with gTTS (fallback)")
            return True
        else:
            logger.error("gTTS also produced empty file")
            return False
    except Exception as e:
        logger.error("All TTS methods failed: %s", e)
        return False


# -----------------------------------------------------------------------------
# Free Video Assembly
# -----------------------------------------------------------------------------
def create_vertical_video(
    images: List[str],
    voice_path: str,
    title: str,
    short_link: str,
    output_path: str,
    duration_per_image: float = 3.8,
) -> bool:
    if not images or not check_ffmpeg():
        return False

    filter_parts = []
    inputs = []

    for img in images:
        inputs.extend(["-loop", "1", "-t", str(duration_per_image), "-i", img])

    for i in range(len(images)):
        filter_parts.append(
            f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,"
            f"zoompan=z='min(zoom+0.0012,1.12)':d={int(duration_per_image*25)}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920,"
            f"setpts=PTS-STARTPTS[v{i}]"
        )

    concat = "".join(f"[v{i}]" for i in range(len(images)))
    filter_parts.append(f"{concat}concat=n={len(images)}:v=1:a=0[base]")

    safe_title = title.replace(":", "\\:").replace("'", "")[:48]
    safe_link = short_link.replace(":", "\\:")

    filter_parts.append(
        f"[base]drawtext=text='{safe_title}':fontsize=40:fontcolor=white:"
        f"borderw=3:bordercolor=black@0.65:x=(w-text_w)/2:y=70:"
        f"enable='between(t,0.4,999)'[titled]"
    )
    filter_parts.append(
        f"[titled]drawtext=text='{safe_link}':fontsize=34:fontcolor=gold:"
        f"borderw=2:bordercolor=black@0.7:x=(w-text_w)/2:y=h-130:"
        f"enable='between(t,1.2,999)'[finalv]"
    )

    has_music = Path(MUSIC_PATH).exists()
    cmd = ["ffmpeg", "-y", *inputs, "-i", voice_path]
    if has_music:
        cmd.extend(["-i", MUSIC_PATH])
        filter_parts.append(
            f"[{len(images)+1}:a]volume=0.15[music];"
            f"[{len(images)}:a]volume=1.0[voice];"
            f"[music][voice]amix=inputs=2:duration=first[aout]"
        )
        audio_map = ["-map", "[aout]"]
    else:
        audio_map = ["-map", f"{len(images)}:a"]

    cmd.extend([
        "-filter_complex", ";".join(filter_parts),
        "-map", "[finalv]", *audio_map,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", "-r", "25",
        output_path,
    ])

    return run_cmd(cmd, timeout=360)


def generate_short_video(title: str, snippet: str, short_link: str) -> Optional[str]:
    if not VIDEO_ENABLED:
        logger.info("VIDEO_ENABLED=false → skipping video")
        return None

    logger.info("Free multi-media pipeline started → %s", title)

    voice_script = (
        f"Discover {title}. "
        f"{snippet[:150].strip()}... "
        f"Position yourself before everyone else. Link in bio."
    )

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        voice_path = tmp.name

    if not generate_voiceover(voice_script, voice_path):
        logger.error("Voice generation failed completely")
        return None

    images = generate_images(title, snippet, count=5)
    output_path = str(OUTPUT_DIR / f"promo_{int(time.time())}.mp4")

    success = create_vertical_video(images, voice_path, title, short_link, output_path)

    # Cleanup
    try:
        os.unlink(voice_path)
    except Exception:
        pass
    for img in images:
        try:
            os.unlink(img)
        except Exception:
            pass

    if success and Path(output_path).exists():
        logger.info("Vertical short video ready → %s", output_path)
        return output_path
    return None


# -----------------------------------------------------------------------------
# Free YouTube Shorts
# -----------------------------------------------------------------------------
def post_to_youtube_shorts(video_path: str, title: str, description: str) -> bool:
    if not YOUTUBE_ENABLED:
        return False

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.auth.transport.requests import Request
        import pickle

        SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
        token_path = "youtube_token.pickle"
        creds = None

        if Path(token_path).exists():
            with open(token_path, "rb") as f:
                creds = pickle.load(f)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file("client_secrets.json", SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, "wb") as f:
                pickle.dump(creds, f)

        youtube = build("youtube", "v3", credentials=creds)

        body = {
            "snippet": {
                "title": f"{title[:85]} #Shorts",
                "description": f"{description}\n\n#Shorts #AI #Wealth #Book",
                "tags": ["shorts", "book", "AI", "superintelligence", "wealth"],
                "categoryId": "22",
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        }

        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info("YouTube upload progress: %d%%", int(status.progress() * 100))

        logger.info("YouTube Short published → https://youtube.com/shorts/%s", response["id"])
        return True
    except Exception as e:
        logger.exception("YouTube Shorts failed: %s", e)
        return False


# -----------------------------------------------------------------------------
# Free TikTok + Instagram ready packages
# -----------------------------------------------------------------------------
def _create_ready_package(
    platform: str,
    video_path: str,
    title: str,
    caption: str,
    short_link: str,
) -> Optional[str]:
    if not Path(video_path).exists():
        return None

    package_dir = OUTPUT_DIR / f"{platform}_ready_{int(time.time())}"
    package_dir.mkdir(exist_ok=True)

    dest_video = package_dir / "video.mp4"
    shutil.copy2(video_path, dest_video)

    full_caption = f"{caption}\n\n{short_link}\n\n#BookTok #AI #Wealth #SuperIntelligence #Reels"
    (package_dir / "caption.txt").write_text(full_caption, encoding="utf-8")

    instructions = f"""{platform.upper()} READY PACKAGE
================================
1. Open the {platform} app (or Creator Studio)
2. Upload the file: video.mp4
3. Paste everything from caption.txt
4. Add a trending sound if you want
5. Post

Video is already vertical 9:16 and optimized for mobile.
"""
    (package_dir / "README.txt").write_text(instructions, encoding="utf-8")

    logger.info("%s ready package created → %s", platform.capitalize(), package_dir)
    return str(package_dir)


def prepare_tiktok_package(video_path: str, title: str, caption: str, short_link: str) -> Optional[str]:
    if not TIKTOK_ENABLED:
        return None
    return _create_ready_package("tiktok", video_path, title, caption, short_link)


def prepare_instagram_package(video_path: str, title: str, caption: str, short_link: str) -> Optional[str]:
    if not INSTAGRAM_ENABLED:
        return None
    return _create_ready_package("instagram", video_path, title, caption, short_link)
