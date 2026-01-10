#!/bin/bash
# Stop TikTok Bulk Downloader services

echo "🛑 Stopping TikTok Bulk Downloader services..."

# Kill backend
pkill -f "python.*api.py"
pkill -f "python.*server.py"

# Kill frontend
pkill -f "http.server 8080"

echo "✅ All services stopped"
