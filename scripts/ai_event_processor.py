#!/usr/bin/env python3
"""
ai_event_processor.py
Final version:
- Uses Moondream for a natural-language narrative diff
- Extracts keywords using Python (no extra LLM calls)
- DeepSeek summarizes keyword into a 2–5 word phrase
- Full logging
- Safe DB writes
"""

import re
import os
import sys
import time
import signal
import threading
import base64
import json
from datetime import datetime
from io import BytesIO
import requests
from PIL import Image
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

time.sleep(5)  # Delay to allow dependent services to start

# ======================================================================================
# CONFIG
# ======================================================================================

AI_SERVER = "192.168.1.59:11434"
IMAGE_INSPECTION_MODEL = "moondream:latest"
PHRASE_MODEL = "llama3.2:1b"

IMAGE_QUALITY = 60
IMAGE_RESIZE_PERCENT = 60

POLL_INTERVAL = 5
ERROR_RETRY_HOURS = 24
AI_TIMEOUT_SECONDS = 600

# Natural language narrative Moondream prompt
IMAGE_INSPECTION_PROMPT = (
    "These two images were taken from a security camera 4 seconds apart. "
    "Describe ONLY the visual differences caused by motion or change. "
    "Ignore lightbulbs, grass, and bushes. "
    "Keep the description short, factual, and focused on what changed."
)

# Phrase model receives ONLY the keyword signal
PHRASE_PROMPT_PREFIX = (

    "from this information summarize only the “{keyword}” into a 5-7 word phrase."
    "It must be accurate and realistic. Think about the right sumarization before you answer.\n\n"
    "{description}\n"   
)


# ======================================================================================
# ENV LOADING
# ======================================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

ENV_FILE = os.environ.get("ENV_FILE", os.path.join(PROJECT_ROOT, ".env"))
if os.path.isfile(ENV_FILE):
    load_dotenv(ENV_FILE)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "security_cameras")
DB_USER = os.getenv("DB_USER", "securitycam")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/mnt/sdcard/security_camera/security_footage")

LOG_DIR = os.getenv("LOG_DIR", os.path.join(PROJECT_ROOT, "scripts", "logs"))
LOGFILE = os.path.join(LOG_DIR, "ai_event_processor.log")
os.makedirs(LOG_DIR, exist_ok=True)

# ======================================================================================
# LOGGER
# ======================================================================================

class PlainLogger:
    def __init__(self, logfile):
        self.logfile = logfile
        self.lock = threading.Lock()
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        open(logfile, "a").close()

    def log(self, msg: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}\n"
        with self.lock:
            with open(self.logfile, "a", encoding="utf-8") as f:
                f.write(line)
        sys.stdout.write(line)
        sys.stdout.flush()

logger = PlainLogger(LOGFILE)

# ======================================================================================
# DATABASE
# ======================================================================================

def create_db_engine():
    url = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/"
        f"{DB_NAME}?charset=utf8mb4"
    )
    return create_engine(url, pool_size=2, max_overflow=3, pool_pre_ping=True)

engine = create_db_engine()

SELECT_UNPROCESSED_EVENT_SQL = text("""
    SELECT id, image_a_path, image_b_path
    FROM events
    WHERE ai_processed = 0
      AND image_a_path IS NOT NULL
      AND image_b_path IS NOT NULL
      AND (
        ai_error IS NULL
        OR ai_error = ''
        OR ai_processed_at < DATE_SUB(NOW(), INTERVAL :retry_hours HOUR)
      )
    ORDER BY timestamp DESC
    LIMIT 1
""")

UPDATE_SUCCESS_SQL = text("""
    UPDATE events
    SET ai_processed = 1,
        ai_processed_at = NOW(6),
        ai_description = :description,
        ai_phrase = :phrase,
        ai_error = NULL
    WHERE id = :event_id
    LIMIT 1
""")

UPDATE_ERROR_SQL = text("""
    UPDATE events
    SET ai_processed_at = NOW(6),
        ai_error = :error
    WHERE id = :event_id
    LIMIT 1
""")

UPDATE_PARTIAL_SUCCESS_SQL = text("""
    UPDATE events
    SET ai_processed_at = NOW(6),
        ai_description = :description,
        ai_error = :error
    WHERE id = :event_id
    LIMIT 1
""")

# ======================================================================================
# IMAGE PROCESSING
# ======================================================================================

def optimize_image(path: str) -> str:
    try:
        img = Image.open(path)

        new_w = int(img.width * IMAGE_RESIZE_PERCENT / 100)
        new_h = int(img.height * IMAGE_RESIZE_PERCENT / 100)
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        buf = BytesIO()
        img.save(buf, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
        buf.seek(0)

        return base64.b64encode(buf.read()).decode()
    except Exception as e:
        raise RuntimeError(f"Failed to optimize {path}: {e}")

# ======================================================================================
# KEYWORD EXTRACTION (Python-only)
# ======================================================================================


import re

def extract_motion_keywords(text: str) -> str:
    # Normalize and tokenize by words only (whole-word safety)
    words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    full_text = text.lower()

    # ------------------------------------------------------------------
    # NEGATION HELPERS
    # ------------------------------------------------------------------
    def negated(phrases):
        """Return True if any negation phrase appears in the full text."""
        return any(neg in full_text for neg in phrases)

    # ------------------------------------------------------------------
    # PERSON DETECTION (man / woman / child / person)
    # ------------------------------------------------------------------
    MAN_WORDS = {"man", "male", "gentleman", "guy"}
    WOMAN_WORDS = {"woman", "female", "lady"}
    CHILD_WORDS = {"child", "kid", "boy", "girl", "toddler", "infant", "teen"}
    PERSON_WORDS = {"person", "people", "human", "individual", "figure"}

    MAN_NEG = ["no man", "not a man", "no men", "no other people"]
    WOMAN_NEG = ["no woman", "not a woman", "no women", "no other people"]
    CHILD_NEG = ["no child", "no children", "no kid", "no kids", "not a child"]
    PERSON_NEG = ["no person", "no people", "no humans", "not a person"]

    # Man
    if not negated(MAN_NEG) and (words & MAN_WORDS):
        return "man detected"

    # Woman
    if not negated(WOMAN_NEG) and (words & WOMAN_WORDS):
        return "woman detected"

    # Child
    if not negated(CHILD_NEG) and (words & CHILD_WORDS):
        return "child detected"

    # Generic person
    if not negated(PERSON_NEG) and (words & PERSON_WORDS):
        return "person detected"

    # ------------------------------------------------------------------
    # VEHICLES
    # ------------------------------------------------------------------
    CAR_WORDS = {"car", "truck", "vehicle", "van", "suv", "jeep", "pickup"}
    CAR_NEG = ["no car", "no vehicle", "no cars", "no vehicles"]

    if not negated(CAR_NEG) and (words & CAR_WORDS):
        return "moving car detected"

    # ------------------------------------------------------------------
    # ANIMALS
    # ------------------------------------------------------------------
    ANIMAL_WORDS = {
        "dog", "cat", "bird", "deer", "raccoon", "squirrel",
        "fox", "coyote", "rabbit", "duck", "goose", "turkey"
    }
    ANIMAL_NEG = ["no animal", "no animals", "no dog", "no dogs", "no cats"]

    if not negated(ANIMAL_NEG) and (words & ANIMAL_WORDS):
        return "animal detected"

    # ------------------------------------------------------------------
    # TREE / PLANT MOTION
    # ------------------------------------------------------------------
    TREE_WORDS = {"branch", "branches", "tree", "trees", "bush", "bushes", "plant", "plants", "foliage", "leaves"}
    TREE_NEG = ["no tree", "no trees", "no branches", "no leaves"]

    if not negated(TREE_NEG) and (words & TREE_WORDS):
        return "tree motion"

    # ------------------------------------------------------------------
    # LIGHT / SHADOW MOTION
    # ------------------------------------------------------------------
    LIGHT_WORDS = {"shadow", "shadows", "light", "lights", "lighting", "reflection", "glare", "brightness"}
    LIGHT_NEG = ["no light", "no lights", "no shadow", "no shadows"]

    if not negated(LIGHT_NEG) and (words & LIGHT_WORDS):
        return "light change"

    # ------------------------------------------------------------------
    # OBJECT MOVEMENT
    # ------------------------------------------------------------------
    OBJECT_WORDS = {"object", "item", "moved", "shifted", "fell", "fallen", "dropped"}
    OBJECT_NEG = ["no object", "no movement", "nothing moved"]

    if not negated(OBJECT_NEG) and (words & OBJECT_WORDS):
        return "object moved"

    # ------------------------------------------------------------------
    # FINAL FALLBACK
    # ------------------------------------------------------------------
    return "unknown movement"



# ======================================================================================
# AI CALLS
# ======================================================================================

def call_moondream(a64: str, b64: str) -> str:
    url = f"http://{AI_SERVER}/api/generate"

    payload = {
        "model": IMAGE_INSPECTION_MODEL,
        "prompt": IMAGE_INSPECTION_PROMPT,
        "images": [a64, b64],
        "stream": False
    }

    logger.log("Image inspection prompt:")
    logger.log(IMAGE_INSPECTION_PROMPT)
    logger.log(f"Calling image inspection model ({IMAGE_INSPECTION_MODEL})...")

    start = time.time()
    resp = requests.post(url, json=payload, timeout=AI_TIMEOUT_SECONDS)
    elapsed = time.time() - start

    logger.log(f"{IMAGE_INSPECTION_MODEL} completed in {elapsed:.1f}s")
    resp.raise_for_status()

    text = resp.json().get("response", "").strip()
    logger.log("{IMAGE_INSPECTION_MODEL} output:")
    logger.log(text)

    return text


def sanitize_phrase_output(text: str) -> str:
    """Ensure output is 2–5 words, remove punctuation."""
    t = text.strip().lower()
    t = "".join(c for c in t if c.isalnum() or c == " ")
    words = t.split()
    if len(words) < 1 or len(words) > 5:
        return "unknown movement"
    return " ".join(words)


def call_phrase_model(event_id: int, keyword: str, description: str) -> str:
    """Generate the final motion phrase based on a keyword + narrative description."""
    prompt = PHRASE_PROMPT_PREFIX.format(keyword=keyword, description=description)

    logger.log(f"Event {event_id}: Phrase prompt:\n{prompt.strip()}")

    start = time.time()
    try:
        r = requests.post(
            f"http://{AI_SERVER}/api/generate",
            json={
                "model": PHRASE_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=AI_TIMEOUT_SECONDS,
        )
        r.raise_for_status()
        raw_output = r.json().get("response", "").strip()
    except Exception as e:
        raise RuntimeError(f"Phrase model error: {e}")

    elapsed = time.time() - start
    logger.log(f"Event {event_id}: Phrase model completed in {elapsed:.1f}s")
    logger.log(f"Event {event_id}: Phrase RAW output:\n{raw_output}")

    # Sanitize: keep only the first line, lowercase, strip junk
    phrase = raw_output.split("\n")[0].strip()

    # Safety: enforce word count and fallback
    wc = len(phrase.split())
    if not (3 <= wc <= 10):  # allow minor variance
        logger.log(f"Event {event_id}: Phrase invalid length ({wc} words), using fallback.")
        phrase = "Unknown movement"

    return phrase


# ======================================================================================
# EVENT PROCESSING
# ======================================================================================

def path_join_media(rel_path: str) -> str:
    return os.path.join(MEDIA_ROOT, rel_path.lstrip("/"))

def process_event(event_id: int, a_rel: str, b_rel: str):
    start = time.time()
    narrative = None

    try:
        full_a = path_join_media(a_rel)
        full_b = path_join_media(b_rel)

        logger.log(f"Event {event_id}: Processing {a_rel}, {b_rel}")

        if not os.path.isfile(full_a):
            raise RuntimeError(f"Missing image A: {full_a}")
        if not os.path.isfile(full_b):
            raise RuntimeError(f"Missing image B: {full_b}")

        a64 = optimize_image(full_a)
        b64 = optimize_image(full_b)

        # === CALL 1: Moondream ===
        narrative = call_moondream(b64, a64)
 # type: ignore
        # Python keyword extraction
        keyword = extract_motion_keywords(narrative)
        logger.log(f"Extracted keyword: {keyword}")

        # === CALL 2: DeepSeek ===
        phrase = call_phrase_model(event_id, keyword, narrative)
        safe_phrase = phrase[:250]

        # Save results
        with engine.begin() as conn:
            conn.execute(UPDATE_SUCCESS_SQL, {
                "event_id": event_id,
                "description": narrative,
                "phrase": safe_phrase
            })

        elapsed = time.time() - start
        logger.log(f"✓ Event {event_id} processed in {elapsed:.1f}s")

    except Exception as e:
        err = str(e)
        logger.log(f"❌ Event {event_id} failed: {err}")

        try:
            with engine.begin() as conn:
                if narrative:
                    conn.execute(UPDATE_PARTIAL_SUCCESS_SQL, {
                        "event_id": event_id,
                        "description": narrative,
                        "error": err
                    })
                else:
                    conn.execute(UPDATE_ERROR_SQL, {
                        "event_id": event_id,
                        "error": err
                    })
        except Exception as db_e:
            logger.log(f"DB update failed: {db_e}")


# ======================================================================================
# MAIN LOOP
# ======================================================================================

_stop_event = threading.Event()

def handle_signal(signum, frame):
    logger.log(f"Received signal {signum}; shutting down...")
    _stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def run_daemon():
    logger.log("=== AI Event Processor Starting ===")

    while not _stop_event.is_set():
        try:
            with engine.begin() as conn:
                row = conn.execute(
                    SELECT_UNPROCESSED_EVENT_SQL,
                    {"retry_hours": ERROR_RETRY_HOURS}
                ).first()

            if row:
                event_id, a_rel, b_rel = row
                process_event(event_id, a_rel, b_rel)
            else:
                time.sleep(POLL_INTERVAL)

        except Exception as e:
            logger.log(f"Unexpected main loop error: {e}")
            time.sleep(POLL_INTERVAL)

    logger.log("=== AI Event Processor Shutdown ===")

if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        pass
