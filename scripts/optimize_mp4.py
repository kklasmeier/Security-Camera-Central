#!/usr/bin/env python3
# =============================================================================
# optimize_mp4.py
# Nightly MP4 Optimization Script
#
# Purpose:
#   Compress existing MP4 videos to smaller sizes using ffmpeg/libx264.
#   Replaces originals in place and updates mp4_conversion_status in DB
#   to 'optimized' or 'failed'.
#
# Schedule:
#   Run via cron daily at 1:00 AM, automatically stops by 7:00 AM.
# =============================================================================

import os
import sys
import time
import shutil
import subprocess
from datetime import datetime, time as dtime
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Ensure we run from the script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Explicitly load .env from the project root
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))


# =============================================================================
# CONFIGURATION
# =============================================================================
BASE_PATH = "/mnt/sdcard/security_camera/security_footage"
LOG_DIR = "/home/pi/Security-Camera-Central/scripts/logs"
LOG_FILE = os.path.join(LOG_DIR, "mp4_optimize.log")
FFMPEG_BIN = "ffmpeg"

# polite processing
SLEEP_BETWEEN = 2        # seconds between files
NICE_LEVEL = 10           # OS-level niceness
#STOP_TIME = dtime(7, 0)   # stop after this time (07:00 AM)
STOP_TIME = dtime(23, 59)
# =============================================================================
# UTILITIES
# =============================================================================

def log(msg: str):
    """Write timestamped messages to log file and stdout."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def is_after_stop_time() -> bool:
    """Check if current time is past STOP_TIME (local time)."""
    now = datetime.now().time()
    return now >= STOP_TIME

def ffmpeg_optimize(in_path: str, tmp_out: str) -> tuple[int, str]:
    """Run ffmpeg optimization, return (exit_code, stderr_output)."""
    cmd = [
        "nice", "-n", str(NICE_LEVEL),
        "ionice", "-c2", "-n7",
        FFMPEG_BIN,
        "-hide_banner", "-loglevel", "error", "-y",
        "-i", in_path,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        tmp_out,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stderr.strip()
    except Exception as e:
        return 1, str(e)

def file_size_mb(path: str) -> float:
    """Return file size in MB."""
    try:
        return os.path.getsize(path) / (1024 * 1024)
    except FileNotFoundError:
        return 0.0

# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def create_db_engine():
    load_dotenv()
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "3306")
    db_name = os.getenv("DB_NAME", "security_cameras")
    db_user = os.getenv("DB_USER", "securitycam")
    db_pass = os.getenv("DB_PASSWORD", "")

    url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(url, pool_pre_ping=True)
    return engine

# =============================================================================
# MAIN OPTIMIZATION LOOP
# =============================================================================

def optimize_videos():
    log("=== Starting Nightly MP4 Optimization ===")

    # set niceness
    try:
        os.nice(NICE_LEVEL)
    except PermissionError:
        log(f"⚠️ Could not set nice({NICE_LEVEL}); continuing politely")

    engine = create_db_engine()
    with engine.begin() as conn:
        results = conn.execute(text("""
            SELECT id, video_mp4_path
            FROM events
            WHERE mp4_conversion_status = 'complete'
        """)).fetchall()

    if not results:
        log("No MP4s found with status 'complete'; nothing to do.")
        return

    log(f"Found {len(results)} MP4(s) to optimize")

    for row in results:
        event_id = row.id
        rel_path = row.video_mp4_path
        full_path = os.path.join(BASE_PATH, rel_path)

        # check if stop time reached
        if is_after_stop_time():
            log("Reached stop window (after 7:00 AM). Finishing current file and stopping.")
            break

        if not os.path.exists(full_path):
            log(f"❌ Event {event_id}: File not found ({rel_path})")
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE events SET mp4_conversion_status='failed' WHERE id=:id"),
                    {"id": event_id},
                )
            continue

        # build temp path
        tmp_out = f"{full_path}.opt.tmp.mp4"
        log(f"Event {event_id}: Optimizing {rel_path}")

        rc, err = ffmpeg_optimize(full_path, tmp_out)
        if rc != 0:
            log(f"❌ Event {event_id}: Optimization failed (rc={rc}) {err}")
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE events SET mp4_conversion_status='failed' WHERE id=:id"),
                    {"id": event_id},
                )
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
            continue

        old_size = file_size_mb(full_path)
        new_size = file_size_mb(tmp_out)

        if new_size > 0 and new_size < old_size:
            try:
                # preserve timestamps
                ts = os.path.getmtime(full_path)
                shutil.move(tmp_out, full_path)
                os.utime(full_path, (ts, ts))

                log(f"✅ Event {event_id}: Optimized from {old_size:.1f} MB → {new_size:.1f} MB")
                with engine.begin() as conn:
                    conn.execute(
                        text("UPDATE events SET mp4_conversion_status='optimized' WHERE id=:id"),
                        {"id": event_id},
                    )

            except Exception as e:
                log(f"❌ Event {event_id}: Replace failed ({e})")
                with engine.begin() as conn:
                    conn.execute(
                        text("UPDATE events SET mp4_conversion_status='failed' WHERE id=:id"),
                        {"id": event_id},
                    )
        else:
            log(f"ℹ️ Event {event_id}: Output not smaller ({old_size:.1f} MB → {new_size:.1f} MB); keeping original")
            os.remove(tmp_out)
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE events SET mp4_conversion_status='optimized' WHERE id=:id"),
                    {"id": event_id},
                )

        time.sleep(SLEEP_BETWEEN)

    log("=== Nightly optimization complete ===")

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    try:
        optimize_videos()
    except KeyboardInterrupt:
        log("Received keyboard interrupt; exiting cleanly.")
    except Exception as e:
        log(f"❌ Fatal error: {e}")
        sys.exit(1)
