# 🧪 Testing Instructions for Microsoft Edge Add-ons Reviewers

**Product**: TikTok Bulk Downloader  
**Product ID**: 21a9bdeb-b990-40df-8913-6e75822f5f8c  
**Publisher**: Sevens  

---

## 📋 Quick Start - Two Testing Methods

### ✅ Method 1: Demo Mode (NO BACKEND REQUIRED - Recommended for Quick Testing)

This is the **fastest way to test** the extension functionality without any setup:

1. **Install the extension** in Microsoft Edge
2. **Navigate** to any TikTok profile page:
   - Example: https://www.tiktok.com/@downykenya
   - Or: https://www.tiktok.com/@tiktok
3. **Click** the extension icon in the browser toolbar
4. **Click** the "📖 Setup Guide for Reviewers" button (blue button at top)
5. **Enable** the "🎭 Demo Mode" toggle
6. **Click** "🚀 Start Auto-Scroll"
   - The extension will simulate collecting video URLs
   - Watch the counter increase (simulated data)
7. **Click** "⏹️ Stop Scrolling" after a few seconds
8. **Click** "📥 Download Videos"
   - Success message will appear (simulated backend response)

**Expected Results:**
- ✅ Extension UI loads correctly
- ✅ Demo mode toggle works
- ✅ Simulated URL collection shows increasing counter
- ✅ Download button triggers success message
- ✅ All UI elements responsive and functional

---

### ✅ Method 2: Full Backend Setup (For Comprehensive Testing)

This method tests the complete functionality with a real backend API:

#### Prerequisites:
- Python 3.12+ installed
- Command line/terminal access
- ~5 minutes for setup

#### Step-by-Step Setup:

1. **Download the Backend Code**
   ```bash
   # Clone or download from GitHub
   git clone https://github.com/Joombah/Tiktok-Bulk-Downloader.git
   cd Tiktok-Bulk-Downloader
   ```
   
   Or download ZIP from: https://github.com/Joombah/Tiktok-Bulk-Downloader/archive/refs/heads/main.zip

2. **Create Virtual Environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Start the Backend Server**
   ```bash
   python backend/api.py
   ```
   
   **Expected output:**
   ```
   INFO:     Uvicorn running on http://0.0.0.0:3000
   INFO:     Application startup complete.
   ```

5. **Test the Extension**
   - Open Edge and navigate to: https://www.tiktok.com/@downykenya
   - Click the extension icon
   - API Status should show: "✅ Connected"
   - Click "🚀 Start Auto-Scroll"
   - Wait 10-15 seconds (collect ~10-20 URLs)
   - Click "⏹️ Stop Scrolling"
   - Click "📥 Download Videos"
   - Success message with Job ID will appear

6. **Verify Downloads** (Optional)
   - Check the `downloads/` folder in the project directory
   - Videos will be downloaded with filenames like: `@username_videoID.mp4`

---

## 🔍 Feature Testing Checklist

### Core Features:
- [ ] Extension popup opens correctly
- [ ] Setup guide displays complete instructions
- [ ] Demo mode toggle enables/disables demo functionality
- [ ] API status indicator shows connection state
- [ ] Auto-scroll collects video URLs from TikTok pages
- [ ] URL counter updates in real-time
- [ ] Download button sends URLs to backend (or simulates in demo mode)
- [ ] Clear URLs button resets the counter
- [ ] Settings (scroll interval, API URL) can be modified and saved

### User Interface:
- [ ] All buttons are visible and labeled clearly
- [ ] Status messages appear for user actions
- [ ] Progress indicators show current state
- [ ] Responsive design works at different sizes
- [ ] No layout issues or overlapping elements

### Error Handling:
- [ ] Extension shows appropriate message when not on TikTok
- [ ] Offline backend triggers clear error message
- [ ] Invalid settings (e.g., scroll interval) are rejected with helpful feedback

---

## 🎯 Specific Test Scenarios

### Scenario 1: First-Time User Experience
1. Install extension
2. Click extension icon
3. See "Setup Guide for Reviewers" button
4. Click guide button → Comprehensive instructions appear
5. **Result**: User immediately understands how to test

### Scenario 2: Demo Mode Testing
1. Enable demo mode toggle
2. Visit TikTok profile
3. Start auto-scroll
4. Observe simulated collection
5. Click download
6. **Result**: All features work without backend

### Scenario 3: Full Backend Integration
1. Start backend server (see Method 2)
2. Disable demo mode
3. Visit TikTok profile
4. Collect real URLs
5. Download creates actual job
6. **Result**: Complete end-to-end functionality

### Scenario 4: Settings Persistence
1. Change API URL
2. Change scroll interval
3. Close popup
4. Reopen popup
5. **Result**: Settings are saved

---

## 📝 API Endpoints (For Reference)

When backend is running at `http://localhost:3000`:

- **Health Check**: `GET /api/health`
  - Returns: `{"status": "healthy"}`
  
- **Create Download Job**: `POST /api/manifest/create`
  - Body: `{"urls": ["url1", "url2"], "job_name": "My Job"}`
  - Returns: `{"job_id": "...", "status": "queued"}`

- **API Documentation**: http://localhost:3000/docs
  - Interactive Swagger UI with all endpoints

---

## 🛠️ Troubleshooting

### Issue: "API Status shows Offline"
**Solution**: 
- Enable Demo Mode for testing without backend, OR
- Start the backend server (see Method 2)

### Issue: "Extension not collecting URLs"
**Solution**: 
- Ensure you're on a TikTok profile page (e.g., `tiktok.com/@username`)
- Refresh the page and try again
- Check that you're scrolled to the video grid section

### Issue: "Download button doesn't appear"
**Solution**: 
- First collect some URLs by clicking "Start Auto-Scroll"
- Wait until counter shows > 0
- Download button appears automatically

### Issue: "Cannot connect to page" error
**Solution**: 
- Refresh the TikTok page
- Make sure you clicked the extension icon AFTER the page fully loaded

---

## 📞 Support & Additional Information

- **GitHub Repository**: https://github.com/Joombah/Tiktok-Bulk-Downloader
- **Documentation**: See README.md in the repository
- **Issues/Questions**: https://github.com/Joombah/Tiktok-Bulk-Downloader/issues

---

## ✅ Certification Compliance

### Policy 1.3 - Product is Testable

**How this addresses the requirement:**

1. **Demo Mode**: Extension can be fully tested WITHOUT requiring external setup
2. **Clear Instructions**: Setup guide button provides comprehensive testing steps
3. **In-App Documentation**: All testing methods documented within the extension UI
4. **Quick Testing Path**: Demo mode allows testing in < 2 minutes
5. **Full Setup Documentation**: Complete backend setup instructions provided for thorough testing

**No External Dependencies Required**: Reviewers can test all core functionality using Demo Mode without installing Python, setting up servers, or any configuration.

---

## 📸 Expected Screenshots

### 1. Extension Popup (Initial State)
- Setup Guide button visible at top
- Demo Mode toggle present
- All controls clearly labeled
- API status indicator visible

### 2. Demo Mode Enabled
- Blue info box appears
- API status shows "🎭 Demo Mode"
- All features functional

### 3. URL Collection in Progress
- Counter incrementing
- Stop button visible
- Status shows "Scrolling..."

### 4. Ready to Download
- Download button visible
- URL count > 0
- Success messages appear

---

Thank you for reviewing TikTok Bulk Downloader! We've made significant improvements to ensure the extension is fully testable with minimal setup. Demo Mode allows immediate testing, while complete setup instructions enable thorough evaluation of all features.
