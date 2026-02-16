# How to View Extension Logs

## Step 1: Open Extension Popup
1. Click the **TikTok Bulk Downloader** extension icon in your browser toolbar
2. The popup will appear

## Step 2: Open Developer Console for the Popup
**For Chrome:**
1. Right-click the extension popup window
2. Click **"Inspect"** or **"Inspect Element"**
3. The DevTools will open showing the extension console

**For Firefox:**
1. Right-click the extension popup window  
2. Click **"Inspect"**
3. The DevTools will open showing the extension console

## Step 3: View the Logs
The console will show all extension activities with emojis:

```
🎬 TikTok Bulk Downloader Extension Loaded
📡 API URL: https://tiktok-bulk-downloader.onrender.com
🔍 Checking API status...
🔗 Checking API health: https://tiktok-bulk-downloader.onrender.com/api/health
✅ API health check passed
📥 Starting download for @amazon...
🔗 Requesting: https://tiktok-bulk-downloader.onrender.com/api/videos/user/amazon
📊 API Response status: 200
✅ Found 1270 videos
📥 Starting download of 1270 videos...
  📹 Downloading [1/1270]: video_1.mp4
  ✅ Progress: 5/1270
✅ SUCCESS: All 1270 videos downloaded to Downloads/TikTok/amazon/
```

## What the Logs Show

| Log | Meaning |
|-----|---------|
| 🎬 | Extension loaded |
| 📡 | API URL configured |
| 🔍 | Starting API check |
| 🔗 | Making request to backend |
| ✅ | Success |
| ❌ | Error |
| ⚠️ | Warning |
| 📥 | Download operation |
| 📊 | Response from server |
| 📹 | Processing video |

## Common Issues & Fixes

### No Logs Appearing
- **Reload the extension:** Go to `chrome://extensions/` (Chrome) or `about:addons` (Firefox) and click reload
- **Reload the popup:** Close and reopen the extension

### API Connection Errors
```
❌ API health check timed out after 8s
```
- Backend is too slow or offline
- Check Render logs: https://dashboard.render.com

### Network Errors
```
❌ Network error (CORS or connection issue)
```
- Check the API URL in the popup settings
- Ensure it's accessible from your location

## Compare with Backend Logs

**Extension Console:** Real-time debugging of extension behavior  
**Render Logs:** Backend processing and API requests

Both should show request/response flowing correctly if everything is working!
