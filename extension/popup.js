// Extension popup script

// Default API URL - Now includes deployed backend!
let apiUrl = 'https://tiktok-bulk-downloader.onrender.com';
let isDownloading = false;
let lastDownloadTime = 0;
const DOWNLOAD_COOLDOWN_MS = 2000; // 2 second cooldown between downloads
let demoMode = false; // Demo mode for testing without backend
let demoUrls = []; // Simulated collected URLs in demo mode

document.addEventListener('DOMContentLoaded', async () => {
    console.log('🎬 TikTok Bulk Downloader Extension Loaded');
    
    // Load saved settings
    const settings = await chrome.storage.local.get(['scrollInterval', 'apiUrl', 'demoMode']);
    if (settings.scrollInterval) {
        document.getElementById('scrollInterval').value = settings.scrollInterval;
    }
    if (settings.apiUrl) {
        apiUrl = settings.apiUrl;
        document.getElementById('apiUrl').value = apiUrl;
        console.log(`📡 API URL: ${apiUrl}`);
    } else {
        // Set default value in UI
        document.getElementById('apiUrl').value = apiUrl;
        console.log(`📡 Using default API URL: ${apiUrl}`);
    }
    
    // Check if demo mode is enabled
    if (settings.demoMode) {
        demoMode = true;
        document.getElementById('demoModeToggle').checked = true;
        toggleDemoMode(true);
        console.log('🎭 Demo mode enabled');
    }
    
    console.log('🔍 Checking API status...');
    // Check API status (non-blocking)
    checkApiStatus().catch(() => {
        document.getElementById('apiStatus').textContent = '❌ Unable to reach backend';
        document.getElementById('apiStatus').style.color = '#f44336';
        console.error('❌ API status check failed');
    });
    
    // Update status
    updateStatus();
    
    // Set up event listeners
    document.getElementById('startBtn').addEventListener('click', startScrolling);
    document.getElementById('stopBtn').addEventListener('click', stopScrolling);
    document.getElementById('downloadBtn').addEventListener('click', downloadVideos);
    document.getElementById('clearBtn').addEventListener('click', clearUrls);
    document.getElementById('demoModeToggle').addEventListener('change', (e) => {
        toggleDemoMode(e.target.checked);
    });
    document.getElementById('setupGuideBtn').addEventListener('click', showSetupGuide);
    
    // Save settings on change
    document.getElementById('scrollInterval').addEventListener('change', saveSettings);
    document.getElementById('apiUrl').addEventListener('change', saveSettings);
    
    // Auto-update status every 2 seconds
    setInterval(updateStatus, 2000);
});

function toggleDemoMode(enabled) {
    demoMode = enabled;
    chrome.storage.local.set({ demoMode: enabled });
    
    if (enabled) {
        document.getElementById('apiStatus').textContent = '🎭 Demo Mode';
        document.getElementById('apiStatus').style.color = '#ff9800';
        document.getElementById('demoInfo').style.display = 'block';
        showMessage('✅ Demo mode enabled - test without backend', 'success');
    } else {
        document.getElementById('demoInfo').style.display = 'none';
        checkApiStatus().catch(() => {
            document.getElementById('apiStatus').textContent = '❌ Unable to reach backend';
            document.getElementById('apiStatus').style.color = '#f44336';
        });
    }
}

function showSetupGuide() {
    const guide = `🚀 SETUP GUIDE FOR REVIEWERS

📝 Option 1: Demo Mode (No Backend Required - FASTEST!)
1. Enable "Demo Mode" toggle
2. Visit any TikTok profile page
3. Click "Start Auto-Scroll" to simulate collection
4. Click "Stop Scrolling" after a few seconds
5. Click "Download Videos" to see demo success

🌐 Option 2: Use Live Backend (RECOMMENDED!)
✅ Backend is already deployed and running!
✅ API URL: https://tiktok-bulk-downloader.onrender.com
1. Keep "Demo Mode" DISABLED
2. API URL is pre-configured (see settings below)
3. Visit any TikTok profile: tiktok.com/@tiktok
4. Click "Start Auto-Scroll" (collects real URLs)
5. Click "Stop Scrolling" after collecting
6. Click "Download Videos" (sends to live backend)
Note: First request may take 30s (free tier warm-up)

🖥️ Option 3: Local Backend Setup (Advanced)
1. Download/clone: github.com/Joombah/Tiktok-Bulk-Downloader
2. Open terminal in project folder
3. Run: python3 -m venv venv && source venv/bin/activate
4. Run: pip install -r backend/requirements.txt
5. Run: python backend/api.py
6. Change API URL to: http://localhost:3000

📋 Testing Instructions:
• Navigate to: tiktok.com/@tiktok
• Click extension icon in toolbar
• Choose any option above

✅ Expected behavior:
• Extension collects video URLs as you scroll
• Counter shows collected videos
• Download button sends to backend
• Status updates in real-time

📧 Support: github.com/Joombah/Tiktok-Bulk-Downloader/issues`;
    
    alert(guide);
}

async function checkApiStatus() {
    if (demoMode) {
        document.getElementById('apiStatus').textContent = '🎭 Demo Mode';
        document.getElementById('apiStatus').style.color = '#ff9800';
        console.log('✅ Demo mode active, skipping API check');
        return true;
    }
    
    console.log(`🔗 Checking API health: ${apiUrl}/api/health`);

    // Set checking state
    document.getElementById('apiStatus').textContent = '⏳ Checking...';
    document.getElementById('apiStatus').style.color = '#ff9800';

    // Retry logic for transient backend cold starts
    const attempts = 3;
    const baseTimeout = 15000; // 15s per attempt
    for (let attempt = 1; attempt <= attempts; attempt++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), baseTimeout);

            const response = await fetch(`${apiUrl}/api/health`, {
                signal: controller.signal,
                headers: {
                    'Accept': 'application/json'
                }
            });
            clearTimeout(timeoutId);

            if (response.ok) {
                document.getElementById('apiStatus').textContent = '✅ Connected';
                document.getElementById('apiStatus').style.color = '#4caf50';
                console.log(`✅ API health check passed (attempt ${attempt})`);
                return true;
            } else {
                console.warn(`⚠️ API health check returned status ${response.status} (attempt ${attempt})`);
                // show intermediate error but keep retrying
                document.getElementById('apiStatus').textContent = `❌ Error (${response.status})`;
                document.getElementById('apiStatus').style.color = '#f44336';
                // small backoff before next attempt
                await new Promise(r => setTimeout(r, attempt * 1000));
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.error(`❌ API health check timed out after ${baseTimeout/1000}s (attempt ${attempt})`);
                document.getElementById('apiStatus').textContent = `❌ Timeout (${baseTimeout/1000}s)`;
            } else {
                console.error(`❌ API health check error (attempt ${attempt}):`, error.message || error);
                document.getElementById('apiStatus').textContent = `❌ ${error.message || 'Network error'}`;
            }

            document.getElementById('apiStatus').style.color = '#f44336';
            // backoff before retrying
            if (attempt < attempts) await new Promise(r => setTimeout(r, attempt * 1500));
        }
    }

    // All attempts failed
    console.error('❌ API health check failed after retries');
    return false;
}

async function updateStatus() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab || !tab.url.includes('tiktok.com')) {
        document.getElementById('statusText').textContent = 'Not on TikTok';
        document.getElementById('status').className = 'status idle';
        return;
    }
    
    chrome.tabs.sendMessage(tab.id, { action: 'getStatus' }, (response) => {
        if (chrome.runtime.lastError || !response) return;
        
        document.getElementById('urlCount').textContent = response.urlCount;
        document.getElementById('scrollCount').textContent = response.scrollCount;
        
        if (response.isScrolling) {
            document.getElementById('statusText').textContent = 'Scrolling...';
            document.getElementById('status').className = 'status scrolling';
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'block';
        } else {
            document.getElementById('statusText').textContent = 'Idle';
            document.getElementById('status').className = 'status idle';
            document.getElementById('startBtn').style.display = 'block';
            document.getElementById('stopBtn').style.display = 'none';
        }
        
        if (response.urlCount > 0) {
            document.getElementById('downloadBtn').style.display = 'block';
        } else {
            document.getElementById('downloadBtn').style.display = 'none';
        }
    });
}

async function startScrolling() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab || !tab.url.includes('tiktok.com')) {
        showMessage('❌ Please navigate to a TikTok page first', 'error');
        return;
    }
    
    const scrollInterval = parseInt(document.getElementById('scrollInterval').value);
    
    if (scrollInterval < 500 || scrollInterval > 10000) {
        showMessage('❌ Scroll interval must be between 500-10000ms', 'error');
        return;
    }
    
    // Demo mode simulation
    if (demoMode) {
        showMessage('✅ Demo: Auto-scroll started!', 'success');
        simulateDemoCollection();
        return;
    }
    
    chrome.tabs.sendMessage(tab.id, {
        action: 'startScroll',
        settings: { scrollIntervalMs: scrollInterval }
    }, (response) => {
        if (chrome.runtime.lastError) {
            showMessage('❌ Cannot connect to page. Try refreshing.', 'error');
            return;
        }
        if (response && response.success) {
            showMessage('✅ Auto-scroll started!', 'success');
            updateStatus();
        } else {
            showMessage('❌ Failed to start scrolling', 'error');
        }
    });
}

function simulateDemoCollection() {
    // Simulate collecting URLs in demo mode
    demoUrls = [];
    let count = 0;
    const maxUrls = 15;
    
    const interval = setInterval(() => {
        if (count >= maxUrls) {
            clearInterval(interval);
            showMessage(`✅ Demo: Collected ${maxUrls} videos. Click "Download Videos" to test.`, 'success');
            document.getElementById('downloadBtn').style.display = 'block';
            return;
        }
        
        count++;
        demoUrls.push(`https://www.tiktok.com/@demo_user/video/demo_video_${count}`);
        document.getElementById('urlCount').textContent = count;
        document.getElementById('scrollCount').textContent = count;
    }, 300);
}

async function stopScrolling() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { action: 'stopScroll' }, (response) => {
        if (response && response.success) {
            showMessage('Auto-scroll stopped', 'success');
            updateStatus();
        }
    });
}

async function downloadVideos() {
    // Demo mode simulation
    if (demoMode) {
        if (demoUrls.length === 0) {
            showMessage('❌ Demo: No URLs collected. Click "Start Auto-Scroll" first!', 'error');
            return;
        }
        
        showMessage(`✅ Demo: Would download ${demoUrls.length} videos directly to Downloads folder`, 'success');
        setTimeout(() => {
            showMessage('✅ Demo: Complete! Check your Downloads/TikTok folder', 'success');
        }, 1000);
        return;
    }
    
    // Rate limiting check
    const now = Date.now();
    if (isDownloading) {
        showMessage('⏳ Download already in progress...', 'error');
        return;
    }
    if (now - lastDownloadTime < DOWNLOAD_COOLDOWN_MS) {
        const waitTime = Math.ceil((DOWNLOAD_COOLDOWN_MS - (now - lastDownloadTime)) / 1000);
        showMessage(`⏳ Please wait ${waitTime}s before next download`, 'error');
        return;
    }
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    // Check if on TikTok
    if (!tab || !tab.url.includes('tiktok.com')) {
        showMessage('❌ Please navigate to a TikTok page first', 'error');
        return;
    }
    
    // Extract username from URL
    let username = '';
    if (tab.url.includes('@')) {
        const match = tab.url.match(/@([\w.]+)/);
        if (match) username = match[1];
    }
    
    if (!username) {
        showMessage('❌ Cannot detect username. Please visit a TikTok profile page (@username)', 'error');
        return;
    }
    
    // Check API status before fetching
    const apiOnline = await checkApiStatus();
    if (!apiOnline) {
        showMessage('❌ Backend server is offline. Try again later.', 'error');
        console.error('❌ Download cancelled: API is offline');
        return;
    }
    
    isDownloading = true;
    document.getElementById('downloadBtn').disabled = true;
    
    try {
        console.log(`📥 Starting download for @${username}...`);
        showMessage(`⏳ Fetching videos from @${username}...`, 'success');
        
        const controller = new AbortController();
        const timeoutMs = 120000; // 120s timeout for large profiles
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        // Call new endpoint to get video download URLs
        console.log(`🔗 Requesting: ${apiUrl}/api/videos/user/${username}`);
        const apiResponse = await fetch(`${apiUrl}/api/videos/user/${username}`, {
            method: 'GET',
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        console.log(`📊 API Response status: ${apiResponse.status}`);
        
        if (!apiResponse.ok) {
            const errorData = await apiResponse.json().catch(() => ({}));
            console.error(`❌ API Error (${apiResponse.status}):`, errorData);
            showMessage(`❌ API Error: ${errorData.detail || 'Failed to fetch videos'}`, 'error');
            isDownloading = false;
            document.getElementById('downloadBtn').disabled = false;
            return;
        }
        
        const data = await apiResponse.json();
        console.log(`✅ Found ${data.videos.length} videos`);
        
        if (!data.videos || data.videos.length === 0) {
            console.warn('⚠️ No videos found for this profile');
            showMessage('❌ No videos found for this profile', 'error');
            isDownloading = false;
            document.getElementById('downloadBtn').disabled = false;
            return;
        }
        
        showMessage(`✅ Found ${data.videos.length} videos. Starting downloads...`, 'success');
        console.log(`📥 Starting download of ${data.videos.length} videos...`);
        
        // Download each video using Chrome downloads API
        let successCount = 0;
        let failCount = 0;
        
        for (let i = 0; i < data.videos.length; i++) {
            const video = data.videos[i];
            
            try {
                console.log(`  📹 Downloading [${i+1}/${data.videos.length}]: ${video.filename}`);
                // Download video directly to Downloads/TikTok/{username}/ folder
                await chrome.downloads.download({
                    url: video.download_url,
                    filename: `TikTok/${username}/${video.filename}`,
                    saveAs: false,
                    conflictAction: 'uniquify' // Auto-rename if file exists
                });
                
                successCount++;
                
                // Update progress every 5 videos
                if ((i + 1) % 5 === 0) {
                    console.log(`  ✅ Progress: ${i + 1}/${data.videos.length}`);
                    showMessage(`⏳ Downloading... ${i + 1}/${data.videos.length}`, 'success');
                }
                
                // Small delay to avoid overwhelming the browser
                await new Promise(resolve => setTimeout(resolve, 100));
                
            } catch (error) {
                console.error(`  ❌ Failed to download ${video.filename}:`, error);
                failCount++;
            }
        }
        
        // Final status
        if (failCount === 0) {
            console.log(`✅ SUCCESS: All ${successCount} videos downloaded to Downloads/TikTok/${username}/`);
            showMessage(`✅ All ${successCount} videos downloaded to Downloads/TikTok/${username}/`, 'success');
        } else {
            console.warn(`⚠️ PARTIAL: Downloaded ${successCount}/${data.videos.length} videos (${failCount} failed)`);
            showMessage(`⚠️ Downloaded ${successCount}/${data.videos.length} videos (${failCount} failed)`, 'success');
        }
        
        lastDownloadTime = Date.now();
        
    } catch (error) {
        if (error.name === 'AbortError') {
            console.error(`❌ Download timeout (${timeoutMs/1000}s)`);
            showMessage(`❌ Request timeout (${timeoutMs/1000}s). Backend may be slow.`, 'error');
        } else {
            console.error('❌ Download error:', error.message || error);
            showMessage(`❌ Download error: ${error.message || error}`, 'error');
        }
    } finally {
        isDownloading = false;
        document.getElementById('downloadBtn').disabled = false;
    }
}

async function clearUrls() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (tab && tab.url.includes('tiktok.com')) {
        chrome.tabs.sendMessage(tab.id, { action: 'clearUrls' }, (response) => {
            if (response && response.success) {
                showMessage('URLs cleared', 'success');
                updateStatus();
            }
        });
    }
}

async function saveSettings() {
    const scrollInterval = document.getElementById('scrollInterval').value;
    const newApiUrl = document.getElementById('apiUrl').value;
    
    await chrome.storage.local.set({ scrollInterval, apiUrl: newApiUrl });
    apiUrl = newApiUrl;
    
    showMessage('Settings saved', 'success');
    checkApiStatus().catch(() => {
        document.getElementById('apiStatus').textContent = '❌ Unable to reach backend';
        document.getElementById('apiStatus').style.color = '#f44336';
    });
}

function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message ${type} show`;
    
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 3000);
}
