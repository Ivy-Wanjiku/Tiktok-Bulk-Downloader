// Extension popup script

let apiUrl = 'http://localhost:3000';

document.addEventListener('DOMContentLoaded', async () => {
    // Load saved settings
    const settings = await chrome.storage.local.get(['scrollInterval', 'apiUrl']);
    if (settings.scrollInterval) {
        document.getElementById('scrollInterval').value = settings.scrollInterval;
    }
    if (settings.apiUrl) {
        apiUrl = settings.apiUrl;
        document.getElementById('apiUrl').value = apiUrl;
    }
    
    // Check API status
    checkApiStatus();
    
    // Update status
    updateStatus();
    
    // Set up event listeners
    document.getElementById('startBtn').addEventListener('click', startScrolling);
    document.getElementById('stopBtn').addEventListener('click', stopScrolling);
    document.getElementById('downloadBtn').addEventListener('click', downloadVideos);
    document.getElementById('clearBtn').addEventListener('click', clearUrls);
    
    // Save settings on change
    document.getElementById('scrollInterval').addEventListener('change', saveSettings);
    document.getElementById('apiUrl').addEventListener('change', saveSettings);
    
    // Auto-update status every 2 seconds
    setInterval(updateStatus, 2000);
});

async function checkApiStatus() {
    try {
        const response = await fetch(`${apiUrl}/api/health`);
        if (response.ok) {
            document.getElementById('apiStatus').textContent = '✅ Connected';
            document.getElementById('apiStatus').style.color = '#4caf50';
        } else {
            document.getElementById('apiStatus').textContent = '❌ Error';
            document.getElementById('apiStatus').style.color = '#f44336';
        }
    } catch (error) {
        document.getElementById('apiStatus').textContent = '❌ Offline';
        document.getElementById('apiStatus').style.color = '#f44336';
    }
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
        showMessage('Please navigate to a TikTok page first', 'error');
        return;
    }
    
    const scrollInterval = parseInt(document.getElementById('scrollInterval').value);
    
    chrome.tabs.sendMessage(tab.id, {
        action: 'startScroll',
        settings: { scrollIntervalMs: scrollInterval }
    }, (response) => {
        if (response && response.success) {
            showMessage('Auto-scroll started!', 'success');
            updateStatus();
        }
    });
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
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    chrome.tabs.sendMessage(tab.id, { action: 'getStatus' }, async (response) => {
        if (!response || response.urls.length === 0) {
            showMessage('No URLs collected yet', 'error');
            return;
        }
        
        try {
            // Extract username from current TikTok page URL or first video URL
            let username = '';
            if (tab.url.includes('@')) {
                const match = tab.url.match(/@([\w.]+)/);
                if (match) username = match[1];
            } else if (response.urls.length > 0) {
                const match = response.urls[0].match(/@([\w.]+)/);
                if (match) username = match[1];
            }
            
            showMessage(`Sending ${response.urls.length} videos to download...`, 'success');
            
            // Create job with username if available
            const jobData = {
                urls: response.urls,
                job_name: username ? `Download @${username}` : `Download ${response.urls.length} videos`
            };
            if (username) {
                jobData.username = username;
            }
            
            const apiResponse = await fetch(`${apiUrl}/api/manifest/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jobData)
            });
            
            if (apiResponse.ok) {
                const data = await apiResponse.json();
                showMessage(`✅ Download started! Folder: ${username || 'default'}`, 'success');
            } else {
                showMessage('❌ Failed to start download', 'error');
            }
        } catch (error) {
            showMessage(`❌ Error: ${error.message}`, 'error');
        }
    });
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
    checkApiStatus();
}

function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    messageEl.textContent = text;
    messageEl.className = `message ${type} show`;
    
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 3000);
}
