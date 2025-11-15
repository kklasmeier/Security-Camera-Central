#!/bin/bash
#
# jobctl.sh — Unified Manager for Security Camera Jobs
#
# Manages:
#   convert_pending_mp4   → systemd (mp4-converter.service)
#   optimize_mp4          → cron/manual job
#   ai_event_processor    → systemd (ai-event-processor.service)
#   api_service           → systemd (security-camera-central.service)
#
# ---------------------------------------------------------------
# SUPPORTED COMMANDS:
#
#   help                       Show this help message
#   list                       List all managed jobs
#
#   status                     Show status of all jobs
#   status <job>               Show status of a single job
#
#   start <job>                Start a systemd job
#   stop <job>                 Stop a systemd job
#                              (cron job optimize_mp4 cannot be stopped)
#
#   restart <job>              Restart a systemd job
#
#   run optimize_mp4           Manually execute the cron job
#
#   logs <job>                 Show last 200 log lines
#   follow <job>               Follow live logs (journal or logfile)
#
# ---------------------------------------------------------------
# USAGE EXAMPLES:
#
#   ./jobctl.sh list
#   ./jobctl.sh status
#   ./jobctl.sh status ai_event_processor
#   ./jobctl.sh restart api_service
#   ./jobctl.sh start api_service
#   ./jobctl.sh stop api_service
#   ./jobctl.sh run optimize_mp4
#   ./jobctl.sh logs convert_pending_mp4
#   ./jobctl.sh follow api_service
#
# ---------------------------------------------------------------


### CONFIGURATION ###
BASE="/home/pi/Security-Camera-Central/scripts"
VENV="$BASE/venv/bin/python3"

# Map job → script filename (only used for manual-run jobs)
declare -A JOB_SCRIPTS=(
    ["convert_pending_mp4"]="$BASE/convert_pending_mp4.py"
    ["optimize_mp4"]="$BASE/optimize_mp4.py"
    ["ai_event_processor"]="$BASE/ai_event_processor.py"
)

# Map job → systemd service name
declare -A JOB_SERVICES=(
    ["convert_pending_mp4"]="mp4-converter.service"
    ["ai_event_processor"]="ai-event-processor.service"
    ["api_service"]="security-camera-central.service"
)

### COLORS ###
GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"
NC="\e[0m"

### FUNCTIONS ###

function show_help() {
    sed -n '1,/^### CONFIGURATION ###/{p}' "$0"
}

function list_jobs() {
    echo "Available jobs:"
    echo "  convert_pending_mp4   (systemd)"
    echo "  optimize_mp4          (cron/manual)"
    echo "  ai_event_processor    (systemd)"
    echo "  api_service           (systemd - run_api.sh main API)"
}

function status_all() {
    echo ""
    for job in "${!JOB_SERVICES[@]}" "optimize_mp4"; do
        echo "=============================="
        echo "Job: $job"
        echo "=============================="
        status_job "$job"
        echo ""
    done
}

function status_job() {
    local job="$1"

    # -----------------------------
    # systemd-based jobs
    # -----------------------------
    if [[ -n "${JOB_SERVICES[$job]}" ]]; then
        local svc="${JOB_SERVICES[$job]}"
        if systemctl is-active --quiet "$svc"; then
            echo -e "${GREEN}ACTIVE${NC} — $svc"
        else
            echo -e "${RED}INACTIVE${NC} — $svc"
        fi
        systemctl status "$svc" --no-pager
        return
    fi

    # -----------------------------
    # cron/manual job
    # -----------------------------
    if [[ "$job" == "optimize_mp4" ]]; then
        echo -e "${YELLOW}CRON JOB${NC}"
        echo "Cron entry:"
        grep optimize_mp4 /etc/crontab 2>/dev/null \
            || grep optimize_mp4 /var/spool/cron/crontabs/pi 2>/dev/null \
            || echo "No cron entry found."

        echo ""
        LOGFILE="$BASE/logs/mp4_optimize.log"
        [[ -f "$LOGFILE" ]] && tail -n 20 "$LOGFILE" || echo "No optimize log found."
        return
    fi

    echo "Unknown job: $job"
}

function run_job() {
    local job="$1"

    if [[ "$job" == "optimize_mp4" ]]; then
        echo "Running optimize_mp4 manually..."
        cd "$BASE"
        $VENV "${JOB_SCRIPTS[$job]}"
        return
    fi

    echo "Job $job is not a manual-run job."
}

function restart_job() {
    local job="$1"

    # systemd jobs
    if [[ -n "${JOB_SERVICES[$job]}" ]]; then
        echo "Restarting ${JOB_SERVICES[$job]}..."
        sudo systemctl restart "${JOB_SERVICES[$job]}"
        return
    fi

    if [[ "$job" == "optimize_mp4" ]]; then
        run_job optimize_mp4
        return
    fi

    echo "Unknown job: $job"
}

function start_job() {
    local job="$1"
    if [[ -n "${JOB_SERVICES[$job]}" ]]; then
        sudo systemctl start "${JOB_SERVICES[$job]}"
        return
    fi

    echo "Job $job has no start action (cron job)."
}

function stop_job() {
    local job="$1"
    if [[ -n "${JOB_SERVICES[$job]}" ]]; then
        sudo systemctl stop "${JOB_SERVICES[$job]}"
        return
    fi

    echo "Job $job is cron-based and cannot be stopped."
}

# View logs (file-based or systemd journal)
function logs_job() {
    local job="$1"

    # Systemd-based logs
    if [[ -n "${JOB_SERVICES[$job]}" ]]; then
        local tag="${JOB_SERVICES[$job]}"
        echo "Viewing last 200 journal lines for $job:"
        sudo journalctl -u "${JOB_SERVICES[$job]}" -n 200 --no-pager
        return
    fi

    # File logs
    if [[ "$job" == "optimize_mp4" ]]; then
        LOGFILE="$BASE/logs/mp4_optimize.log"
        [[ -f "$LOGFILE" ]] && tail -n 200 "$LOGFILE"
        return
    fi

    echo "Unknown job: $job"
}

# Follow logs live
function follow_job() {
    local job="$1"
    local svc="${JOB_SERVICES[$job]}"

    if [[ -n "$svc" ]]; then
        echo "Following logs for service: $svc"
        sudo journalctl -u "$svc" -f --no-pager
        return
    fi

    if [[ "$job" == "optimize_mp4" ]]; then
        LOGFILE="$BASE/logs/mp4_optimize.log"
        tail -f "$LOGFILE"
        return
    fi

    echo "Unknown job: $job"
}


### COMMAND ROUTER ###
case "$1" in
    help|-h|--help)
        show_help
        ;;
    list)
        list_jobs
        ;;
    status)
        if [[ -n "$2" ]]; then status_job "$2"
        else status_all
        fi
        ;;
    start)
        start_job "$2"
        ;;
    stop)
        stop_job "$2"
        ;;
    restart)
        restart_job "$2"
        ;;
    run)
        run_job "$2"
        ;;
    logs)
        logs_job "$2"
        ;;
    follow)
        follow_job "$2"
        ;;
    *)
        show_help
        ;;
esac

