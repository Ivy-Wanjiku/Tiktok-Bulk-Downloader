#!/bin/bash
# View backend logs in real-time

LOG_FILE="logs/tiktok_downloader.log"

if [ ! -f "$LOG_FILE" ]; then
    echo "❌ Log file not found: $LOG_FILE"
    echo "Make sure the backend is running with: python backend/api.py"
    exit 1
fi

echo "📋 Backend Logs (Ctrl+C to stop)"
echo "========================================"
tail -f "$LOG_FILE"
