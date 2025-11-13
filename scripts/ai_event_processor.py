#!/usr/bin/env python3
"""
ai_event_processor.py
Continuous AI event analysis daemon for Security-Camera-Central.

- Polls MariaDB for events with ai_processed=0 and non-null image paths
- Processes one event at a time (newest first)
- Resizes images and sends to moondream:latest for visual analysis
- Passes moondream output to deepseek-r1:8b for phrase extraction
- Updates DB with ai_description, ai_phrase, ai_processed, ai_processed_at
- On error: populates ai_error and enforces 24-hour retry cooldown
- Continuous loop with 5s sleep when no work
- Plain text logging with timestamps
- Graceful shutdown on SIGINT/SIGTERM
"""

import os
import sys
import time
import signal
import threading
import base64
import json
import tempfile
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Tuple

# ======================================================================================
# CONFIG
# ======================================================================================

# AI Server Configuration
AI_SERVER = "192.168.1.59:11434"
MOONDREAM_MODEL = "moondream:latest"
DEEPSEEK_MODEL = "deepseek-r1:8b"

# Image Optimization Settings
IMAGE_QUALITY = 60
IMAGE_RESIZE_PERCENT = 60

# Processing Configuration
POLL_INTERVAL = 5  # seconds to sleep when no work
ERROR_RETRY_HOURS = 24  # hours to wait before retrying failed events
AI_TIMEOUT_SECONDS = 600  # timeout for AI API calls (10 minutes)

# Prompts
MOONDREAM_PROMPT = (
    "these pictures are taken from a security camera four seconds apart mounted on a house. "
    "tell me the differences between the two pictures."
)

DEEPSEEK_PROMPT_PREFIX = (
    "this is a description of an image taken from a security camera. Motion was detected "
    "causing this picture to be taken. describe for me in a short phrase what this motion was "
    "based on this description given. The phrase is used for efficiency of alerts in logs of "
    "security footage. Give the phrase only, nothing else."
)

# ======================================================================================
# ENV LOADING
# ======================================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

ENV_FILE = os.environ.get("ENV_FILE", os.path.join(PROJECT_ROOT, ".env"))
if os.path.isfile(ENV_FILE):
    load_dotenv(ENV_FILE)

# Required DB config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "security_cameras")
DB_USER = os.getenv("DB_USER", "securitycam")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Paths
MEDIA_ROOT = os.getenv("MEDIA_ROOT", "/mnt/sdcard/security_camera/security_footage")

# Logging
LOG_DIR = os.getenv("LOG_DIR", os.path.join(PROJECT_ROOT, "scripts", "logs"))
LOGFILE = os.path.join(LOG_DIR, "ai_event_processor.log")
os.makedirs(LOG_DIR, exist_ok=True)

# ======================================================================================
# PLAIN-TEXT LOGGER
# ======================================================================================

class PlainLogger:
    """Simplified plain-text logger. Thread-safe and systemd-friendly."""
    def __init__(self, logfile: str):
        self.logfile = logfile
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
        # Ensure file exists
        open(self.logfile, "a").close()

    def log(self, msg: str):
        """Append timestamped message to log file and echo to stdout."""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}\n"
        with self._lock:
            try:
                with open(self.logfile, "a", encoding="utf-8") as f:
                    f.write(line)
            except Exception as e:
                sys.stderr.write(f"[logger error] {e}\n")
        try:
            sys.stdout.write(line)
            sys.stdout.flush()
        except Exception:
            pass

logger = PlainLogger(LOGFILE)

# ======================================================================================
# DATABASE
# ======================================================================================

def create_db_engine() -> Engine:
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    engine = create_engine(
        url,
        pool_size=2,
        max_overflow=3,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
    )
    return engine

engine = create_db_engine()

# ======================================================================================
# SIGNAL HANDLING
# ======================================================================================

_stop_event = threading.Event()

def handle_signal(signum, frame):
    logger.log(f"Received signal {signum}; initiating graceful shutdown...")
    _stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# ======================================================================================
# DATABASE QUERIES
# ======================================================================================

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
    ORDER BY 
      CASE WHEN ai_error IS NULL OR ai_error = '' THEN 0 ELSE 1 END,
      timestamp DESC
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

UPDATE_PARTIAL_SUCCESS_SQL = text("""
    UPDATE events
    SET ai_processed_at = NOW(6),
        ai_description = :description,
        ai_error = :error
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

# ======================================================================================
# IMAGE PROCESSING
# ======================================================================================

def optimize_image(image_path: str) -> str:
    """
    Load image, resize to IMAGE_RESIZE_PERCENT, reduce quality, return base64.
    """
    try:
        img = Image.open(image_path)
        
        # Calculate new size
        new_width = int(img.width * IMAGE_RESIZE_PERCENT / 100)
        new_height = int(img.height * IMAGE_RESIZE_PERCENT / 100)
        
        # Resize
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary (for JPEG compatibility)
        if img_resized.mode in ("RGBA", "P"):
            img_resized = img_resized.convert("RGB")
        
        # Save to bytes with quality reduction
        buffer = BytesIO()
        img_resized.save(buffer, format="JPEG", quality=IMAGE_QUALITY, optimize=True)
        buffer.seek(0)
        
        # Encode to base64
        b64_str = base64.b64encode(buffer.read()).decode('utf-8')
        return b64_str
        
    except Exception as e:
        raise RuntimeError(f"Failed to optimize image {image_path}: {e}")

# ======================================================================================
# AI API CALLS
# ======================================================================================

def call_moondream(image_a_b64: str, image_b_b64: str) -> str:
    """
    Call moondream model with two base64-encoded images.
    Returns the text response.
    """
    url = f"http://{AI_SERVER}/api/generate"
    payload = {
        "model": MOONDREAM_MODEL,
        "prompt": MOONDREAM_PROMPT,
        "images": [image_a_b64, image_b_b64],
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=AI_TIMEOUT_SECONDS)
        elapsed = time.time() - start_time
        logger.log(f"Moondream API call completed in {elapsed:.1f}s")
        
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Moondream API call timed out after {AI_TIMEOUT_SECONDS}s")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Moondream API call failed: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Moondream API response parsing failed: {e}")

def call_deepseek(moondream_description: str) -> str:
    """
    Call deepseek model with moondream's description to extract a short phrase.
    Returns the text response.
    """
    url = f"http://{AI_SERVER}/api/generate"
    prompt = f"{DEEPSEEK_PROMPT_PREFIX}\n\"{moondream_description}\""
    payload = {
        "model": DEEPSEEK_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=AI_TIMEOUT_SECONDS)
        elapsed = time.time() - start_time
        logger.log(f"Deepseek API call completed in {elapsed:.1f}s")
        
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except requests.exceptions.Timeout:
        raise RuntimeError(f"Deepseek API call timed out after {AI_TIMEOUT_SECONDS}s")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Deepseek API call failed: {e}")
    except (KeyError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Deepseek API response parsing failed: {e}")

# ======================================================================================
# EVENT PROCESSING
# ======================================================================================

def path_join_media(relative_path: str) -> str:
    """Join relative path with MEDIA_ROOT."""
    rel = relative_path.lstrip("/").replace("..", "")
    return os.path.join(MEDIA_ROOT, rel)

def process_event(event_id: int, image_a_rel: str, image_b_rel: str):
    """
    Process a single event:
    1. Load and optimize both images
    2. Call moondream for visual analysis
    3. Call deepseek for phrase extraction
    4. Update database with results
    """
    moondream_result = None
    start_time = time.time()
    
    try:
        # Build full paths
        image_a_full = path_join_media(image_a_rel)
        image_b_full = path_join_media(image_b_rel)
        
        logger.log(f"Event {event_id}: Processing images {image_a_rel} and {image_b_rel}")
        
        # Validate files exist
        if not os.path.isfile(image_a_full):
            raise RuntimeError(f"Image A not found: {image_a_full}")
        if not os.path.isfile(image_b_full):
            raise RuntimeError(f"Image B not found: {image_b_full}")
        
        # Optimize images
        logger.log(f"Event {event_id}: Optimizing images...")
        image_a_b64 = optimize_image(image_a_full)
        image_b_b64 = optimize_image(image_b_full)
        
        # Call moondream
        logger.log(f"Event {event_id}: Calling Moondream...")
        moondream_result = call_moondream(image_a_b64, image_b_b64)
        logger.log(f"Event {event_id}: Moondream result: {moondream_result[:100]}...")
        
        # Call deepseek
        logger.log(f"Event {event_id}: Calling Deepseek...")
        deepseek_result = call_deepseek(moondream_result)
        logger.log(f"Event {event_id}: Deepseek phrase: {deepseek_result}")
        
        # Update database with success
        with engine.begin() as conn:
            conn.execute(UPDATE_SUCCESS_SQL, {
                "event_id": event_id,
                "description": moondream_result,
                "phrase": deepseek_result
            })
        
        total_time = time.time() - start_time
        logger.log(f"✅ Event {event_id}: Successfully processed in {total_time:.1f}s")
        
    except Exception as e:
        error_msg = str(e)
        total_time = time.time() - start_time
        logger.log(f"❌ Event {event_id}: Error after {total_time:.1f}s - {error_msg}")
        
        # Update database with error
        # If we have moondream result, save it (partial success)
        try:
            with engine.begin() as conn:
                if moondream_result:
                    conn.execute(UPDATE_PARTIAL_SUCCESS_SQL, {
                        "event_id": event_id,
                        "description": moondream_result,
                        "error": error_msg
                    })
                else:
                    conn.execute(UPDATE_ERROR_SQL, {
                        "event_id": event_id,
                        "error": error_msg
                    })
        except SQLAlchemyError as db_err:
            logger.log(f"❌ Event {event_id}: Failed to update error in DB: {db_err}")

# ======================================================================================
# MAIN LOOP
# ======================================================================================

def run_daemon():
    logger.log("=== AI Event Processor: starting up ===")
    logger.log(f"Config: AI_SERVER={AI_SERVER}, POLL_INTERVAL={POLL_INTERVAL}s, ERROR_RETRY={ERROR_RETRY_HOURS}h")
    logger.log(f"Config: IMAGE_RESIZE={IMAGE_RESIZE_PERCENT}%, IMAGE_QUALITY={IMAGE_QUALITY}")
    logger.log(f"Config: AI_TIMEOUT={AI_TIMEOUT_SECONDS}s ({AI_TIMEOUT_SECONDS/60:.1f} minutes)")
    
    while not _stop_event.is_set():
        try:
            # Look for next unprocessed event
            with engine.begin() as conn:
                result = conn.execute(
                    SELECT_UNPROCESSED_EVENT_SQL, 
                    {"retry_hours": ERROR_RETRY_HOURS}
                ).first()
                
                if result:
                    event_id, image_a_rel, image_b_rel = result
                    # Process this event
                    process_event(event_id, image_a_rel, image_b_rel)
                else:
                    # No work available, sleep
                    time.sleep(POLL_INTERVAL)
                    
        except SQLAlchemyError as e:
            logger.log(f"DB error in main loop: {e}")
            logger.log("Recreating database engine...")
            try:
                engine.dispose()
            except Exception:
                pass
            time.sleep(5)
            try:
                globals()["engine"] = create_db_engine()
                logger.log("Database engine recreated successfully")
            except Exception as re_err:
                logger.log(f"Engine recreation failed: {re_err}")
                time.sleep(10)
        
        except Exception as e:
            logger.log(f"Unexpected error in main loop: {e}")
            time.sleep(POLL_INTERVAL)
    
    logger.log("=== AI Event Processor: clean shutdown ===")

if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        pass