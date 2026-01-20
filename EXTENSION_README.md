# TikTok Bulk Downloader - Browser Extension

## 🎭 Demo Mode (NEW!)

**Test the extension without any backend setup!**

The extension now includes a built-in demo mode that lets you test all features without installing or running the backend server. Perfect for:
- First-time users exploring the extension
- Reviewers testing functionality
- Understanding how the extension works before full setup

### How to Use Demo Mode:
1. Install the extension
2. Click the extension icon
3. Enable the "🎭 Demo Mode" toggle
4. Visit any TikTok profile (e.g., https://www.tiktok.com/@tiktok)
5. Use all features - they'll work with simulated data!

---

## Installation Instructions

### Chrome/Edge/Brave:
1. Open Chrome/Edge and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` folder (NOT the root folder)
5. The extension is now installed!

### Firefox:
1. Open Firefox and go to `about:debugging#/runtime/this-firefox`
2. Click "Load Temporary Add-on"
3. Navigate to the `extension` folder
4. Select the `manifest.json` file
5. The extension is now installed!

---

## How to Use

### Quick Start (Demo Mode - No Backend Required):
1. **Click the extension icon** in your browser toolbar
2. **Enable Demo Mode** using the toggle at the top
3. **Visit a TikTok profile** (e.g., https://www.tiktok.com/@downykenya)
4. **Click "Start Auto-Scroll"** - Watch simulated URL collection
5. **Click "Stop Scrolling"** when ready
6. **Click "Download Videos"** - See simulated success message

### Full Setup (With Backend):
1. **Start the backend server:**
   ```bash
   cd ~/tiktok-bulk-downloader
   ./start.sh
   ```

2. **Navigate to a TikTok profile:**
   - Example: https://www.tiktok.com/@downykenya

3. **Click the extension icon** in your browser toolbar

4. **Click "Start Auto-Scroll"**
   - The extension will automatically scroll the page
   - Video URLs will be collected in real-time
   - You'll see a counter showing collected URLs

5. **Click "Stop Scrolling"** when you have enough videos

6. **Click "Download Videos"**
   - Videos will be sent to your backend
   - Check the Downloads folder: `~/tiktok-bulk-downloader/downloads/`

## Features

✅ **Demo Mode (NEW!)** - Test without backend setup
✅ **Setup Guide** - Click "Setup Guide for Reviewers" button for complete instructions
✅ **Automatic scrolling** - No manual work required
✅ **Real-time URL collection** - See count as it collects
✅ **Visual indicator** - Shows collection progress on the page
✅ **Smart URL cleaning** - Removes query parameters
✅ **Configurable scroll speed** - Adjust in settings
✅ **Direct API integration** - Sends URLs to backend automatically (real mode)
✅ **Badge counter** - Shows collected URLs on extension icon

## Settings

- **Demo Mode**: Enable to test without backend (NEW!)
- **Scroll Interval**: Time between scrolls (default: 2000ms)
- **API URL**: Backend server URL (default: http://localhost:3000)

## Troubleshooting

- **Want to test quickly?**: Enable Demo Mode toggle
- **API Status shows Offline**: Make sure backend is running (`./start.sh`) or enable Demo Mode
- **Not collecting URLs**: Refresh the TikTok page and try again
- **Extension not working**: Check browser console for errors
