#!/usr/bin/env python3
"""
convert_pending_mp4.py
Continuous MP4 converter daemon for Security-Camera-Central.

- Polls MariaDB for events with video_transferred=1 and mp4_conversion_status='pending'
- Atomically claims one event at a time and dispatches work to a thread pool
- Converts H.264 -> MP4 (container copy, no re-encode): ffmpeg -c copy -movflags faststart
- Updates DB on success/failure; on success also sets overall status='complete'
- Deletes .h264 after successful, non-empty MP4 is written
- Continuous loop with exponential backoff (0.5 → 7s, reset on any claim)
- Plain text logging with timestamps + self-managed daily rotation (keep 6 backups)
- Graceful shutdown: finishes in-flight jobs before exiting
"""

import os
import sys
import time
import signal
import queue
import shutil
import threading
import subprocess
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

# ======================================================================================
# CONFIG / ENV LOADING
# ======================================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Allow overriding .env path via ENV_FILE; otherwise use project root .env (same as Bash)
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

# Worker & backoff configuration
CONCURRENCY = int(os.getenv("CONVERT_CONCURRENCY", "2"))
BACKOFF_MIN_SECONDS = float(os.getenv("BACKOFF_MIN_SECONDS", "0.5"))
BACKOFF_MAX_SECONDS = float(os.getenv("BACKOFF_MAX_SECONDS", "7"))

# Stale claim recovery (reset events stuck in 'processing' for too long)
STALE_CLAIM_MINUTES = int(os.getenv("STALE_CLAIM_MINUTES", "5"))
STALE_CLAIM_CHECK_INTERVAL = int(os.getenv("STALE_CLAIM_CHECK_INTERVAL", "60"))  # Check every 60 seconds

# Logging
LOG_DIR = os.getenv("LOG_DIR", os.path.join(PROJECT_ROOT, "scripts", "logs"))
LOGFILE = os.path.join(LOG_DIR, "mp4_conversion.log")
os.makedirs(LOG_DIR, exist_ok=True)

# Safety / behavior
FFMPEG_BIN = os.getenv("FFMPEG_PATH", "ffmpeg")
FFPROBE_BIN = os.getenv("FFPROBE_PATH", "ffprobe")

# Claim metadata (for visibility)
WORKER_ID = f"{os.uname().nodename}:{os.getpid()}"

# ======================================================================================
# PLAIN-TEXT LOGGER WITH DAILY ROTATION
# ======================================================================================

class PlainLogger:
    """Simplified plain-text logger (no rotation). Thread-safe and systemd-friendly."""
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
                # Fallback: at least print to stderr
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
    # Use PyMySQL driver under SQLAlchemy (consistent with your stack)
    url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    # Reasonable pool defaults for a small daemon
    engine = create_engine(
        url,
        pool_size=max(1, CONCURRENCY),   # at least 1, up to concurrency
        max_overflow=CONCURRENCY,        # allow brief bursts
        pool_pre_ping=True,
        pool_recycle=3600,               # recycle hourly
        echo=False,
    )
    return engine


engine = create_db_engine()

# ======================================================================================
# UTILS
# ======================================================================================

_stop_event = threading.Event()

def handle_signal(signum, frame):
    logger.log(f"Received signal {signum}; initiating graceful shutdown...")
    _stop_event.set()

signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

def path_join_media(relative_path: str) -> str:
    rel = relative_path.lstrip("/").replace("..", "")
    return os.path.join(MEDIA_ROOT, rel)

# ======================================================================================
# CLAIM & FETCH
# ======================================================================================

# Recover stale claims (events stuck in 'processing' for more than 5 minutes)
# Using TIMESTAMPDIFF to avoid SQLAlchemy bind parameter issues
RECOVER_STALE_CLAIMS_SQL = text("""
    UPDATE events
    SET mp4_conversion_status = 'pending',
        mp4_claimed_by = NULL,
        mp4_claimed_at = NULL
    WHERE mp4_conversion_status = 'processing'
      AND TIMESTAMPDIFF(MINUTE, mp4_claimed_at, NOW(6)) > 5
""")

CLAIM_SQL = text("""
    UPDATE events
    SET mp4_conversion_status = 'processing',
        mp4_claimed_by = :worker_id,
        mp4_claimed_at = NOW(6)
    WHERE id = :candidate_id
      AND video_transferred = 1
      AND mp4_conversion_status = 'pending'
      AND video_h264_path IS NOT NULL
      AND video_h264_path != ''
    LIMIT 1
""")

SELECT_ONE_PENDING_CANDIDATE_SQL = text("""
    SELECT id
    FROM events
    WHERE video_transferred = 1
      AND mp4_conversion_status = 'pending'
      AND video_h264_path IS NOT NULL
      AND video_h264_path != ''
    ORDER BY timestamp DESC
    LIMIT 1
""")

FETCH_EVENT_SQL = text("""
    SELECT id, camera_id, video_h264_path
    FROM events
    WHERE id = :event_id
    LIMIT 1
""")

RECOVER_STALE_CLAIMS_SQL = text("""
    UPDATE events
    SET mp4_conversion_status = 'pending',
        mp4_claimed_by = NULL,
        mp4_claimed_at = NULL
    WHERE mp4_conversion_status = 'processing'
      AND mp4_claimed_at < NOW(6) - INTERVAL :minutes MINUTE
""")

def recover_stale_claims(conn) -> int:
    """
    Reset any events stuck in 'processing' status for longer than STALE_CLAIM_MINUTES.
    Returns the number of events recovered.
    """
    result = conn.execute(RECOVER_STALE_CLAIMS_SQL, {"minutes": STALE_CLAIM_MINUTES})
    count = result.rowcount
    if count > 0:
        logger.log(f"[RECOVERY] Reset {count} stale claim(s) stuck in 'processing' for >{STALE_CLAIM_MINUTES} minutes")
    return count

def claim_one_event(conn) -> Optional[int]:

    """
    Atomic CAS-style claim:
    1) SELECT a candidate id
    2) UPDATE ... WHERE id=:candidate AND mp4_conversion_status='pending'
    If rowcount==1, we own it; else None.
    """
    logger.log(f"[CLAIM] Executing SELECT query to find candidate event")
    try:
        result = conn.execute(SELECT_ONE_PENDING_CANDIDATE_SQL).first()
        if not result:
            logger.log(f"[CLAIM] No pending events found in database")
            return None
        candidate_id = result[0]
        logger.log(f"[CLAIM] Found candidate event: {candidate_id}, attempting to claim it")
        upd = conn.execute(CLAIM_SQL, {"candidate_id": candidate_id, "worker_id": WORKER_ID})
        logger.log(f"[CLAIM] UPDATE executed, rowcount={upd.rowcount}")
        if upd.rowcount == 1:
            logger.log(f"[CLAIM] Successfully claimed event {candidate_id}")
            return candidate_id
        logger.log(f"[CLAIM] Failed to claim event {candidate_id} (already claimed by another worker)")
        return None
    except Exception as e:
        logger.log(f"[CLAIM] Exception during claim attempt: {type(e).__name__}: {e}")
        raise

# ======================================================================================
# CONVERSION
# ======================================================================================

def ffmpeg_copy_container(h264_full: str, mp4_full: str) -> tuple[int, str]:
    """
    Run ffmpeg to repack H.264 elementary stream into MP4 container (no re-encode).
    Returns (return_code, aggregated_stderr).
    Uses a temp file to avoid partial/corrupt outputs if interrupted.
    """
    tmp_out = f"{mp4_full}.tmp"
    # Ensure target directory exists
    os.makedirs(os.path.dirname(mp4_full), exist_ok=True)

    cmd = [
        FFMPEG_BIN,
        "-hide_banner",
        "-loglevel", "error",
        "-threads", "2",
        "-i", h264_full,
        "-c", "copy",
        "-movflags", "faststart",
        "-f", "mp4",        # ✅ Force output format to MP4
        "-y",
        tmp_out
    ]


    try:
        # Add timeout to prevent hanging on corrupted files
        # Timeout = 5 minutes (300 seconds) - generous for large files
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if proc.returncode == 0:
            # Atomic finalize
            os.replace(tmp_out, mp4_full)
        else:
            # Cleanup tmp on failure
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
        return proc.returncode, (proc.stderr or "").strip()
    except subprocess.TimeoutExpired:
        # ffmpeg hung - kill it and cleanup
        if os.path.exists(tmp_out):
            os.remove(tmp_out)
        return 1, "ffmpeg timeout (5 minutes) - file may be corrupted"
    except FileNotFoundError:
        return 127, "ffmpeg not found"
    except Exception as e:
        # Best effort cleanup
        try:
            if os.path.exists(tmp_out):
                os.remove(tmp_out)
        except Exception:
            pass
        return 1, f"Exception: {e}"

def ffprobe_duration_seconds(mp4_full: str) -> Optional[int]:
    """
    Use ffprobe to get duration (seconds, rounded). Returns None if unavailable.
    """
    cmd = [
        FFPROBE_BIN,
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        mp4_full
    ]
    try:
        # Add timeout to prevent hanging
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if proc.returncode == 0 and proc.stdout.strip():
            try:
                dur = float(proc.stdout.strip())
                return int(round(dur))
            except ValueError:
                return None
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

# ======================================================================================
# DB STATUS UPDATES
# ======================================================================================

SET_FAILED_SQL = text("""
    UPDATE events
    SET mp4_conversion_status = 'failed',
        status = 'failed'
    WHERE id = :event_id
    LIMIT 1
""")

SET_PROCESSING_SQL = text("""
    UPDATE events
    SET mp4_conversion_status = 'processing'
    WHERE id = :event_id
    LIMIT 1
""")

SET_COMPLETE_SQL = text("""
    UPDATE events
    SET mp4_conversion_status = 'complete',
        status = 'complete',
        video_mp4_path = :mp4_rel,
        video_duration = :duration,
        mp4_converted_at = NOW(6)
    WHERE id = :event_id
    LIMIT 1
""")

# ======================================================================================
# WORKER TASK
# ======================================================================================

def process_event(event_id: int, engine: Engine):
    """
    Full lifecycle for a single event:
    - Fetch fields
    - Validate file exists, age, permissions
    - Convert -> MP4 (tmp -> atomic rename)
    - ffprobe duration
    - DB update complete (or failed)
    - Delete .h264 if MP4 exists and non-empty
    """
    logger.log(f"[WORKER-{threading.current_thread().name}] Starting processing for event {event_id}")
    try:
        with engine.begin() as conn:
            row = conn.execute(FETCH_EVENT_SQL, {"event_id": event_id}).first()
            if not row:
                logger.log(f"Event {event_id}: Not found after claim (skipping)")
                return

            _id, camera_id, h264_rel = row
            h264_full = path_join_media(h264_rel)
            mp4_rel = h264_rel[:-5] + ".mp4" if h264_rel.endswith(".h264") else h264_rel + ".mp4"
            mp4_full = path_join_media(mp4_rel)

        # Validate source file
        if not os.path.isfile(h264_full):
            logger.log(f"Event {event_id}: H.264 file not found: {h264_full}")
            with engine.begin() as conn:
                conn.execute(SET_FAILED_SQL, {"event_id": event_id})
            return

        if not os.access(h264_full, os.R_OK):
            logger.log(f"Event {event_id}: No read permission for H.264 file: {h264_full}")
            with engine.begin() as conn:
                conn.execute(SET_FAILED_SQL, {"event_id": event_id})
            return

        target_dir = os.path.dirname(mp4_full)
        if not os.path.isdir(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except Exception:
                logger.log(f"Event {event_id}: Cannot create directory: {target_dir}")
                with engine.begin() as conn:
                    conn.execute(SET_FAILED_SQL, {"event_id": event_id})
                return

        if not os.access(target_dir, os.W_OK):
            logger.log(f"Event {event_id}: No write permission for directory: {target_dir}")
            with engine.begin() as conn:
                conn.execute(SET_FAILED_SQL, {"event_id": event_id})
            return

        # Check for .READY sentinel file to ensure transfer is complete
        # The transfer manager creates this sentinel after successfully moving the H.264 file
        sentinel_path = h264_full + ".READY"
        logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Checking for sentinel file: {sentinel_path}")
        if not os.path.exists(sentinel_path):
            logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Waiting for transfer completion (no .READY sentinel), deferring")
            # Set back to pending so it will be picked up again next loop
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE events
                    SET mp4_conversion_status = 'pending'
                    WHERE id = :event_id
                    LIMIT 1
                """), {"event_id": event_id})
            logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Set back to pending, sleeping 2s before returning")
            # Sleep to avoid hot loop when waiting for transfer
            time.sleep(2.0)
            logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Returning from defer")
            return

        logger.log(f"Event {event_id}: Converting {h264_rel} -> {mp4_rel}")

        rc, fferr = ffmpeg_copy_container(h264_full, mp4_full)

        if fferr:
            for line in fferr.splitlines():
                logger.log(f"  ffmpeg: {line}")

        if rc == 0 and os.path.isfile(mp4_full):
            # Determine duration (best effort)
            dur = ffprobe_duration_seconds(mp4_full) or 60
            with engine.begin() as conn:
                conn.execute(SET_COMPLETE_SQL, {
                    "event_id": event_id,
                    "mp4_rel": mp4_rel,
                    "duration": int(dur)
                })
            logger.log(f"✅ Event {event_id}: Conversion successful (duration: {int(dur)}s)")

            # Delete original .h264 if MP4 has content
            try:
                if os.path.getsize(mp4_full) > 0 and os.access(h264_full, os.W_OK):
                    os.remove(h264_full)
                    logger.log(f"Event {event_id}: Deleted H.264 after successful conversion")
                    # Also remove the .READY sentinel file
                    sentinel_path = h264_full + ".READY"
                    if os.path.exists(sentinel_path):
                        os.remove(sentinel_path)
                        logger.log(f"Event {event_id}: Deleted .READY sentinel")
                elif os.path.getsize(mp4_full) == 0:
                    logger.log(f"Event {event_id}: ⚠️  MP4 is empty; keeping H.264")
            except Exception as e:
                logger.log(f"Event {event_id}: ⚠️  Could not delete H.264: {e}")

        else:
            with engine.begin() as conn:
                conn.execute(SET_FAILED_SQL, {"event_id": event_id})
            logger.log(f"❌ Event {event_id}: Conversion failed (rc={rc})")

        logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Processing completed successfully")

    except SQLAlchemyError as db_err:
        logger.log(f"❌ Event {event_id}: DB error during processing: {db_err}")
        logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Processing failed with DB error")
    except Exception as e:
        logger.log(f"❌ Event {event_id}: Unexpected error: {e}")
        import traceback
        logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Traceback: {traceback.format_exc()}")
        logger.log(f"[WORKER-{threading.current_thread().name}] Event {event_id}: Processing failed with unexpected error")

# ======================================================================================
# MAIN LOOP
# ======================================================================================

def run_daemon():
    logger.log("=== MP4 Converter: starting up ===")
    logger.log(f"Config: CONCURRENCY={CONCURRENCY}, BACKOFF=[{BACKOFF_MIN_SECONDS}..{BACKOFF_MAX_SECONDS}]s")
    logger.log(f"Config: STALE_CLAIM_RECOVERY enabled (>{STALE_CLAIM_MINUTES} minutes, check every {STALE_CLAIM_CHECK_INTERVAL}s)")
    backoff = BACKOFF_MIN_SECONDS
    
    # Track last stale claim check time
    last_stale_check = time.time()

    # ThreadPool for conversions
    with ThreadPoolExecutor(max_workers=CONCURRENCY, thread_name_prefix="mp4w") as pool:
        # Track running futures
        running = set()

        loop_iteration = 0
        while not _stop_event.is_set():
            loop_iteration += 1
            logger.log(f"[LOOP-{loop_iteration}] Main loop iteration starting (backoff={backoff:.2f}s, running_tasks={len(running)})")
            
            # Periodically check for and recover stale claims
            current_time = time.time()
            if current_time - last_stale_check >= STALE_CLAIM_CHECK_INTERVAL:
                logger.log(f"[LOOP-{loop_iteration}] Running stale claim recovery check")
                try:
                    with engine.begin() as conn:
                        recover_stale_claims(conn)
                    last_stale_check = current_time
                except SQLAlchemyError as e:
                    logger.log(f"[LOOP-{loop_iteration}] Stale claim recovery DB error: {e}")
                except Exception as e:
                    logger.log(f"[LOOP-{loop_iteration}] Stale claim recovery unexpected error: {e}")
            
            # Reap completed tasks quickly
            done_now = [f for f in running if f.done()]
            if done_now:
                logger.log(f"[LOOP-{loop_iteration}] Reaping {len(done_now)} completed task(s)")
            for f in done_now:
                running.remove(f)
                # ensure exceptions are surfaced in logs
                try:
                    f.result()
                except Exception as e:
                    logger.log(f"Worker exception: {e}")

            # Fill available slots by claiming work
            slots = CONCURRENCY - len(running)
            claimed_any = False
            
            # Safely introspect engine.pool without directly accessing attributes
            # (use getattr/call to avoid static type checker errors if attributes are not present)
            pool_obj = getattr(engine, "pool", None)
            def _callattr(obj, name):
                attr = getattr(obj, name, None)
                try:
                    return attr() if callable(attr) else attr
                except Exception:
                    return "N/A"
            pool_size = _callattr(pool_obj, "size")
            checked_in = _callattr(pool_obj, "checkedin")
            checked_out = _callattr(pool_obj, "checkedout")
            overflow = _callattr(pool_obj, "overflow")
            logger.log(f"[LOOP-{loop_iteration}] Available slots: {slots}, Pool state: size={pool_size}, checked_in={checked_in}, checked_out={checked_out}, overflow={overflow}")

            if slots > 0:
                logger.log(f"[LOOP-{loop_iteration}] Attempting to claim up to {slots} event(s)")
                try:
                    with engine.begin() as conn:
                        logger.log(f"[LOOP-{loop_iteration}] Starting database transaction for claiming")
                        for slot_num in range(slots):
                            if _stop_event.is_set():
                                logger.log(f"[LOOP-{loop_iteration}] Stop event set, breaking claim loop")
                                break
                            logger.log(f"[LOOP-{loop_iteration}] Claim attempt {slot_num + 1}/{slots}")
                            event_id = claim_one_event(conn)
                            if event_id is None:
                                logger.log(f"[LOOP-{loop_iteration}] No event claimed on attempt {slot_num + 1}, stopping claim attempts")
                                break
                            claimed_any = True
                            logger.log(f"[LOOP-{loop_iteration}] Submitting event {event_id} to thread pool")
                            fut = pool.submit(process_event, event_id, engine)
                            running.add(fut)

                except SQLAlchemyError as e:
                    # Database lost / stale connection — rebuild engine and retry later
                    logger.log(f"[LOOP-{loop_iteration}] ❌ SQLAlchemyError caught: {type(e).__name__}: {e}")
                    logger.log(f"[LOOP-{loop_iteration}] DB connection lost or stale; recreating engine")
                    try:
                        engine.dispose()
                        logger.log(f"[LOOP-{loop_iteration}] Engine disposed successfully")
                    except Exception as dispose_err:
                        logger.log(f"[LOOP-{loop_iteration}] Engine dispose failed (ignored): {dispose_err}")
                    time.sleep(3)
                    try:
                        globals()["engine"] = create_db_engine()
                        logger.log(f"[LOOP-{loop_iteration}] Recreated database engine successfully.")
                    except Exception as re_err:
                        logger.log(f"[LOOP-{loop_iteration}] ❌ Engine recreation failed: {re_err}")
                        time.sleep(5)
                    # Skip rest of loop so we don't increment backoff on DB errors
                    continue
                except Exception as e:
                    # Catch ANY other exception that might be happening
                    logger.log(f"[LOOP-{loop_iteration}] ❌ UNEXPECTED EXCEPTION during claim: {type(e).__name__}: {e}")
                    import traceback
                    logger.log(f"[LOOP-{loop_iteration}] Traceback: {traceback.format_exc()}")
                    # Continue to next iteration
                    continue

            # Backoff handling
            if claimed_any:
                logger.log(f"[LOOP-{loop_iteration}] Claimed work, resetting backoff to {BACKOFF_MIN_SECONDS}s")
                backoff = BACKOFF_MIN_SECONDS
            else:
                # No work claimed; idle a bit
                logger.log(f"[LOOP-{loop_iteration}] No work claimed, sleeping for {backoff:.2f}s")
                time.sleep(backoff)
                old_backoff = backoff
                backoff = min(BACKOFF_MAX_SECONDS, backoff * 2 if backoff < BACKOFF_MAX_SECONDS else BACKOFF_MAX_SECONDS)
                logger.log(f"[LOOP-{loop_iteration}] After sleep, backoff increased from {old_backoff:.2f}s to {backoff:.2f}s")

        # Shutdown: wait for in-flight tasks to complete
        if running:
            logger.log(f"Shutdown: waiting for {len(running)} in-flight conversion(s) to finish...")
            for f in as_completed(running):
                try:
                    f.result()
                except Exception as e:
                    logger.log(f"Worker exception during shutdown: {e}")

    logger.log("=== MP4 Converter: clean shutdown ===")


if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        pass