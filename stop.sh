#!/bin/bash
# Stop TikTok Bulk Downloader services

echo "🛑 Stopping TikTok Bulk Downloader services..."

# Kill processes on specific ports
lsof -ti:3000 | xargs -r kill -9 2>/dev/null
lsof -ti:8080 | xargs -r kill -9 2>/dev/null

# Also kill by process name as backup
pkill -f "python.*api.py" 2>/dev/null
pkill -f "http.server 8080" 2>/dev/null

sleep 1

echo "✅ All services stopped"
