"""Self-improvement: every post is tagged with the writing ANGLE used. improve.py later measures link clicks per angle and
raises the weight of angles that earn more clicks. The engine picks the next angle using those weights (85% of the time;
15% it explores a random angle so it can keep discovering). It only adjusts writing angles. It never edits its own code."""
import logging
import random
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

ANGLES: Dict[str, str] = {
    "benefit": "lead with the main benefit for the customer",
    "question": "open with a question the customer would really ask",
    "story": "tell a two-sentence micro-story",
    "proof": "lead with one concrete detail from the description (never invent numbers)",
    "offer": "lead with the offer and what to do next",
    "curiosity": "create honest curiosity without clickbait",
}


def weights(sb) -> Dict[str, float]:
    rows = sb.table("mamachi_settings").select("*").eq("key", "angle_weights").execute().data or []
    value = (rows[0].get("value") if rows else None) or {}
    return {a: max(0.2, float(value.get(a, 1.0))) for a in ANGLES}


def pick_angle(sb, rnd=random) -> Optional[str]:
    names: List[str] = list(ANGLES)
    if rnd.random() < 0.15:
        return rnd.choice(names)                                   # keep exploring
    w = weights(sb)
    return rnd.choices(names, weights=[w[n] for n in names], k=1)[0]


def log_post(sb, kind: str, ref: Optional[str], angle: Optional[str], platforms: str, short_data: Dict[str, Any]) -> None:
    sb.table("mamachi_learning").insert({"kind": kind, "ref": ref, "angle": angle, "platforms": platforms,
                                         "shortio_id": short_data.get("shortio_id"), "short_url": short_data.get("short_url")}).execute()
