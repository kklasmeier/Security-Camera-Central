#!/bin/bash
# convert_pending_mp4.sh - Centralized MP4 conversion for all cameras
# Runs on Pi 5 central server
# Queries MariaDB for pending H.264 files and converts them to MP4

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env"
MEDIA_ROOT="/mnt/sdcard/security_camera/security_footage"
LOG_DIR="${SCRIPT_DIR}/logs"
LOGFILE="${LOG_DIR}/mp4_conversion.log"
LOCKFILE="/tmp/mp4_conversion.lock"
PATH="/usr/local/bin:/usr/bin:/bin"

# ==============================================================================
# LOAD CREDENTIALS FROM .ENV
# ==============================================================================

if [ ! -f "$ENV_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: .env file not found at $ENV_FILE" >&2
    exit 1
fi

# Parse .env file safely (handle quotes, comments, and blank lines)
while IFS='=' read -r key value; do
    # Skip comments and empty lines
    [[ "$key" =~ ^[[:space:]]*# ]] && continue
    [[ -z "$key" ]] && continue
    
    # Remove leading/trailing whitespace
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    
    # Remove quotes from value if present
    value="${value%\"}"
    value="${value#\"}"
    
    # Export only database-related variables
    case "$key" in
        DB_HOST) DB_HOST="$value" ;;
        DB_PORT) DB_PORT="$value" ;;
        DB_NAME) DB_NAME="$value" ;;
        DB_USER) DB_USER="$value" ;;
        DB_PASSWORD) DB_PASSWORD="$value" ;;
    esac
done < "$ENV_FILE"

# Validate required credentials
if [ -z "$DB_HOST" ] || [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Missing required database credentials in .env" >&2
    exit 1
fi

# ==============================================================================
# SETUP
# ==============================================================================

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# ==============================================================================
# LOGGING FUNCTION
# ==============================================================================

# Log to both file and stdout
log() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$message" | tee -a "$LOGFILE"
}

# ==============================================================================
# LOG ROTATION (DAILY)
# ==============================================================================

# Get today's date
TODAY=$(date '+%Y-%m-%d')
LOG_DATE_FILE="${LOG_DIR}/.last_rotation_date"

# Check if we need to rotate logs
if [ -f "$LOG_DATE_FILE" ]; then
    LAST_ROTATION=$(cat "$LOG_DATE_FILE")
    if [ "$LAST_ROTATION" != "$TODAY" ]; then
        # Rotate logs
        [ -f "${LOGFILE}.6" ] && rm -f "${LOGFILE}.6"
        [ -f "${LOGFILE}.5" ] && mv "${LOGFILE}.5" "${LOGFILE}.6"
        [ -f "${LOGFILE}.4" ] && mv "${LOGFILE}.4" "${LOGFILE}.5"
        [ -f "${LOGFILE}.3" ] && mv "${LOGFILE}.3" "${LOGFILE}.4"
        [ -f "${LOGFILE}.2" ] && mv "${LOGFILE}.2" "${LOGFILE}.3"
        [ -f "${LOGFILE}.1" ] && mv "${LOGFILE}.1" "${LOGFILE}.2"
        [ -f "${LOGFILE}" ] && mv "${LOGFILE}" "${LOGFILE}.1"
        
        # Update rotation date
        echo "$TODAY" > "$LOG_DATE_FILE"
        log "Log rotated - new day: $TODAY"
    fi
else
    # First run - create date file
    echo "$TODAY" > "$LOG_DATE_FILE"
fi

# ==============================================================================
# FILE LOCKING
# ==============================================================================

# Try to acquire lock
exec 200>"$LOCKFILE"
if ! flock -n 200; then
    log "Another conversion is still running - skipping this cycle."
    
    # Log memory snapshot even when skipping
    CMA_TOTAL_KB=$(grep CmaTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
    CMA_FREE_KB=$(grep CmaFree /proc/meminfo 2>/dev/null | awk '{print $2}')
    CMA_TOTAL_MB=$(awk -v kb="${CMA_TOTAL_KB:-0}" 'BEGIN {printf "%.2f", kb/1024}')
    CMA_FREE_MB=$(awk -v kb="${CMA_FREE_KB:-0}" 'BEGIN {printf "%.2f", kb/1024}')
    RAM_FREE=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
    SWAP_USED=$(free -m | awk '/Swap:/ {print $3}')
    
    log "CMA Free=${CMA_FREE_MB}MB / Total=${CMA_TOTAL_MB}MB | RAM Free=${RAM_FREE}MB | Swap Used=${SWAP_USED}MB"
    exit 0
fi

# ==============================================================================
# MEMORY MONITORING
# ==============================================================================

CMA_TOTAL_KB=$(grep CmaTotal /proc/meminfo 2>/dev/null | awk '{print $2}')
CMA_FREE_KB=$(grep CmaFree /proc/meminfo 2>/dev/null | awk '{print $2}')
CMA_TOTAL_MB=$(awk -v kb="${CMA_TOTAL_KB:-0}" 'BEGIN {printf "%.2f", kb/1024}')
CMA_FREE_MB=$(awk -v kb="${CMA_FREE_KB:-0}" 'BEGIN {printf "%.2f", kb/1024}')
RAM_FREE=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
SWAP_USED=$(free -m | awk '/Swap:/ {print $3}')

log "CMA Free=${CMA_FREE_MB}MB / Total=${CMA_TOTAL_MB}MB | RAM Free=${RAM_FREE}MB | Swap Used=${SWAP_USED}MB"

# Memory safety: skip if low RAM
if [ "$RAM_FREE" -lt 512 ]; then
    log "Skipping conversion (only ${RAM_FREE} MB free, need 512+ MB)"
    exit 0
fi

log "=== Conversion job started (Free: ${RAM_FREE} MB) ==="

# ==============================================================================
# QUERY DATABASE FOR PENDING CONVERSIONS
# ==============================================================================

QUERY="SELECT id, camera_id, video_h264_path FROM events 
       WHERE video_transferred = 1 
       AND mp4_conversion_status = 'pending' 
       AND video_h264_path IS NOT NULL 
       AND video_h264_path != '' 
       ORDER by timestamp DESC
       LIMIT 25;"

PENDING_EVENTS=$(mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -N -e "$QUERY" 2>/dev/null)

if [ -z "$PENDING_EVENTS" ]; then
    log "No pending conversions found"
    exit 0
fi

# ==============================================================================
# PROCESS EACH PENDING EVENT
# ==============================================================================

echo "$PENDING_EVENTS" | while IFS=$'\t' read -r event_id camera_id h264_relative_path; do
    
    # Build full paths
    h264_full_path="${MEDIA_ROOT}/${h264_relative_path}"
    mp4_relative_path="${h264_relative_path%.h264}.mp4"
    mp4_full_path="${MEDIA_ROOT}/${mp4_relative_path}"
    
    # Check if H.264 file exists
    if [ ! -f "$h264_full_path" ]; then
        log "Event $event_id: H.264 file not found: $h264_full_path"
        
        # Mark as failed in database
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
            "UPDATE events SET mp4_conversion_status = 'failed' WHERE id = $event_id;" 2>/dev/null
        continue
    fi
    
    # Check if we have read access to H.264 file
    if [ ! -r "$h264_full_path" ]; then
        log "Event $event_id: No read permission for H.264 file: $h264_full_path"
        log "Event $event_id: File owner: $(stat -c '%U:%G' "$h264_full_path"), Script user: $(whoami)"
        
        # Mark as failed in database
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
            "UPDATE events SET mp4_conversion_status = 'failed' WHERE id = $event_id;" 2>/dev/null
        continue
    fi
    
    # Check if we have write access to the directory
    camera_dir=$(dirname "$mp4_full_path")
    if [ ! -w "$camera_dir" ]; then
        log "Event $event_id: No write permission for directory: $camera_dir"
        log "Event $event_id: Directory owner: $(stat -c '%U:%G' "$camera_dir"), Script user: $(whoami)"
        
        # Mark as failed in database
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
            "UPDATE events SET mp4_conversion_status = 'failed' WHERE id = $event_id;" 2>/dev/null
        continue
    fi
    
    # Check if file is still being written (less than 15 seconds old)
    file_age=$(( $(date +%s) - $(stat -c %Y "$h264_full_path") ))
    if [ "$file_age" -lt 15 ]; then
        log "Event $event_id: File too new (${file_age}s old), skipping"
        continue
    fi
    
    # Skip if MP4 already exists
    if [ -f "$mp4_full_path" ]; then
        log "Event $event_id: MP4 already exists, updating database"
        
        # Get duration and update database
        duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$mp4_full_path" 2>/dev/null)
        duration_int=$(printf "%.0f" "${duration:-60}")
        
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
            "UPDATE events SET 
                mp4_conversion_status = 'complete',
                video_mp4_path = '$mp4_relative_path',
                video_duration = $duration_int,
                mp4_converted_at = NOW()
             WHERE id = $event_id;" 2>/dev/null
        
        # Delete H.264 file since MP4 exists (if we have permission and MP4 has content)
        if [ -s "$mp4_full_path" ] && [ -w "$h264_full_path" ]; then
            rm -f "$h264_full_path"
            log "Event $event_id: Deleted H.264 file (MP4 already existed)"
        elif [ ! -s "$mp4_full_path" ]; then
            log "Event $event_id: ⚠️  MP4 file is empty, keeping H.264 file"
        elif [ ! -w "$h264_full_path" ]; then
            log "Event $event_id: Cannot delete H.264 (no write permission)"
        fi
        continue
    fi
    
    # Mark as processing in database
    mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
        "UPDATE events SET mp4_conversion_status = 'processing' WHERE id = $event_id;" 2>/dev/null
    
    log "Event $event_id: Converting $h264_relative_path -> $mp4_relative_path"
    
    # Convert using ffmpeg (redirect stdin from /dev/null to prevent reading from pipe)
    ffmpeg_output=$(ffmpeg -hide_banner -loglevel error -threads 2 \
        -i "$h264_full_path" \
        -c copy \
        -movflags faststart \
        -y "$mp4_full_path" </dev/null 2>&1)
    
    rc=$?
    
    # Log any ffmpeg output
    if [ -n "$ffmpeg_output" ]; then
        echo "$ffmpeg_output" | while IFS= read -r line; do
            log "  ffmpeg: $line"
        done
    fi
    
    if [ $rc -eq 0 ]; then
        # Get exact duration from converted MP4
        duration=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$mp4_full_path" 2>/dev/null)
        
        if [ -n "$duration" ]; then
            duration_int=$(printf "%.0f" "$duration")
            
            # Update database: mark as complete
            mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
                "UPDATE events SET 
                    mp4_conversion_status = 'complete',
                    video_mp4_path = '$mp4_relative_path',
                    video_duration = $duration_int,
                    mp4_converted_at = NOW()
                 WHERE id = $event_id;" 2>/dev/null
            
            log "✅ Event $event_id: Conversion successful (duration: ${duration_int}s)"
        else
            # Duration unavailable but conversion succeeded
            mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
                "UPDATE events SET 
                    mp4_conversion_status = 'complete',
                    video_mp4_path = '$mp4_relative_path',
                    video_duration = 60,
                    mp4_converted_at = NOW()
                 WHERE id = $event_id;" 2>/dev/null
            
            log "✅ Event $event_id: Conversion successful (duration unavailable, defaulted to 60s)"
        fi
        
        # Delete H.264 file after successful conversion (if we have permission)
        # Only delete if MP4 file exists and has content
        if [ -f "$mp4_full_path" ] && [ -s "$mp4_full_path" ] && [ -w "$h264_full_path" ]; then
            rm -f "$h264_full_path"
            log "Event $event_id: Deleted H.264 file after successful conversion"
        elif [ ! -f "$mp4_full_path" ]; then
            log "Event $event_id: ⚠️  MP4 file not found, keeping H.264 file"
        elif [ ! -s "$mp4_full_path" ]; then
            log "Event $event_id: ⚠️  MP4 file is empty, keeping H.264 file"
        elif [ ! -w "$h264_full_path" ]; then
            log "Event $event_id: Cannot delete H.264 (no write permission)"
        fi
        
    else
        # Conversion failed
        mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" -e \
            "UPDATE events SET mp4_conversion_status = 'failed' WHERE id = $event_id;" 2>/dev/null
        
        log "❌ Event $event_id: Conversion failed (rc=$rc)"
    fi
    
done

log "=== Conversion job finished ==="

# Release lock automatically on exit
exit 0