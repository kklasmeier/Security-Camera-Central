#!/bin/bash
# =============================================================================
# central_server_controller.sh — Control Script for Security Camera Central API
# =============================================================================
# Usage:
#   ./central_server_controller.sh start     → Start the Central API service
#   ./central_server_controller.sh stop      → Stop the Central API service
#   ./central_server_controller.sh restart   → Restart the Central API service
#   ./central_server_controller.sh status    → Show current service status
#   ./central_server_controller.sh log       → View or follow logs live
#
# Description:
#   Simplifies management of the "security-camera-central.service"
#   systemd unit, which hosts the Security Camera Central API (middle tier).
#   Logs are viewable both through journalctl and via a persistent logfile.
#
# Example:
#   ./central_server_controller.sh restart
#   ./central_server_controller.sh log
# =============================================================================

SERVICE="security-camera-central.service"
LOG_FILE="/home/pi/Security-Camera-Central/run_api.log"

show_help() {
    cat <<'EOF'
===============================================================================
🖥️  Security Camera Central Server — Control Utility
===============================================================================
Usage:
  ./central_server_controller.sh start     → Start the Central API service
  ./central_server_controller.sh stop      → Stop the Central API service
  ./central_server_controller.sh restart   → Restart the Central API service
  ./central_server_controller.sh status    → Display current service status
  ./central_server_controller.sh log       → View live logs (Ctrl+C to exit)
  ./central_server_controller.sh log last  → Show last 100 lines of persistent log
  ./central_server_controller.sh help      → Show this help message

Description:
  Controls the middle-tier service:
      security-camera-central.service

  This API connects all camera nodes to the central database.
  Logs are available via systemd (journalctl) and also stored persistently at:
      /home/pi/Security-Camera-Central/run_api.log
===============================================================================
EOF
}

# If no argument provided, show help
if [ -z "$1" ]; then
    show_help
    exit 0
fi

ACTION="$1"

case "$ACTION" in
    start)
        echo "🚀 Starting Central API service..."
        sudo systemctl start "$SERVICE"
        ;;
    stop)
        echo "🛑 Stopping Central API service..."
        sudo systemctl stop "$SERVICE"
        ;;
    restart)
        echo "🔄 Restarting Central API service..."
        sudo systemctl restart "$SERVICE"
        ;;
    status)
        echo "📋 Checking Central API service status..."
        sudo systemctl status "$SERVICE" --no-pager
        ;;
    log)
        if [ "$2" == "last" ]; then
            echo "📄 Showing last 100 lines from persistent log file:"
            if [ -f "$LOG_FILE" ]; then
                tail -n 100 "$LOG_FILE"
            else
                echo "⚠️  Log file not found: $LOG_FILE"
            fi
        else
            echo "📜 Following journalctl logs for Central API (Ctrl+C to exit)..."
            sudo journalctl -u "$SERVICE" -f
        fi
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        echo "❌ Unknown option: $ACTION"
        show_help
        exit 1
        ;;
esac
