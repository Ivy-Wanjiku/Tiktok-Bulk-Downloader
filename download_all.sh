#!/bin/bash

# Bulk Download Script for TikTok Videos
# Downloads all videos from Render server to local machine

set -e

# Configuration
BASE_URL="https://tiktok-bulk-downloader.onrender.com"
DOWNLOAD_DIR="./downloads"
USERNAME="${1:-taurenwellsofficial}"

echo "🚀 TikTok Bulk Downloader - Download Script"
echo "============================================"
echo "Target: @${USERNAME}"
echo "Destination: ${DOWNLOAD_DIR}/${USERNAME}/"
echo ""

# Create download directory
mkdir -p "${DOWNLOAD_DIR}/${USERNAME}"

# Fetch file list from API
echo "📋 Fetching file list from server..."
FILE_LIST=$(curl -s "${BASE_URL}/api/downloads/${USERNAME}")

# Extract download URLs and filenames
URLS=$(echo "$FILE_LIST" | jq -r '.files[] | .download_url')
TOTAL_COUNT=$(echo "$FILE_LIST" | jq -r '.count')
TOTAL_SIZE=$(echo "$FILE_LIST" | jq -r '.total_size_mb')

if [ -z "$URLS" ] || [ "$TOTAL_COUNT" == "0" ]; then
    echo "❌ No files found for @${USERNAME}"
    exit 1
fi

echo "✅ Found ${TOTAL_COUNT} files (${TOTAL_SIZE} MB)"
echo ""

# Download each file with progress
CURRENT=0
FAILED=0

echo "$URLS" | while read -r url; do
    CURRENT=$((CURRENT + 1))
    FILENAME=$(basename "$url")
    OUTPUT_PATH="${DOWNLOAD_DIR}/${USERNAME}/${FILENAME}"
    
    # Skip if already exists
    if [ -f "$OUTPUT_PATH" ]; then
        echo "⏭️  [${CURRENT}/${TOTAL_COUNT}] Skipping (exists): ${FILENAME}"
        continue
    fi
    
    echo "⬇️  [${CURRENT}/${TOTAL_COUNT}] Downloading: ${FILENAME}"
    
    # Download with retry logic
    if curl -f -s --retry 3 --retry-delay 2 -o "$OUTPUT_PATH" "${BASE_URL}${url}"; then
        echo "✅ [${CURRENT}/${TOTAL_COUNT}] Downloaded: ${FILENAME}"
    else
        echo "❌ [${CURRENT}/${TOTAL_COUNT}] Failed: ${FILENAME}"
        FAILED=$((FAILED + 1))
        rm -f "$OUTPUT_PATH"  # Clean up partial download
    fi
    
    # Small delay to avoid overwhelming the server
    sleep 0.2
done

echo ""
echo "============================================"
echo "✅ Download Complete!"
echo "Location: ${DOWNLOAD_DIR}/${USERNAME}/"
echo "Total Files: ${TOTAL_COUNT}"
echo "Failed: ${FAILED}"
echo ""
echo "💡 Tip: Check the folder with: ls -lh ${DOWNLOAD_DIR}/${USERNAME}/"
