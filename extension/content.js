// TikTok Auto-Scroll Content Script
// This runs on all TikTok pages and handles automatic scrolling

let isScrolling = false;
let scrollInterval = null;
let collectedUrls = new Set();
let scrollCount = 0;
let settings = {
    scrollIntervalMs: 2000
};

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'startScroll') {
        startAutoScroll(request.settings);
        sendResponse({ success: true });
    } else if (request.action === 'stopScroll') {
        stopAutoScroll();
        sendResponse({ success: true });
    } else if (request.action === 'getStatus') {
        sendResponse({
            isScrolling,
            urlCount: collectedUrls.size,
            scrollCount,
            urls: Array.from(collectedUrls)
        });
    } else if (request.action === 'clearUrls') {
        collectedUrls.clear();
        scrollCount = 0;
        sendResponse({ success: true, urlCount: 0 });
    }
    return true;
});

function startAutoScroll(userSettings) {
    if (isScrolling) return;
    
    isScrolling = true;
    settings = { ...settings, ...userSettings };
    
    console.log('🚀 TikTok Auto-Scroll Started');
    
    // Collect initial URLs
    collectVideoUrls();
    
    // Start auto-scrolling
    scrollInterval = setInterval(() => {
        // Scroll to bottom
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
        
        scrollCount++;
        
        // Collect URLs after scroll
        setTimeout(() => {
            const newUrls = collectVideoUrls();
            console.log(`📊 Scroll #${scrollCount} | Total URLs: ${collectedUrls.size} | New: ${newUrls}`);
            
            // Update badge
            chrome.runtime.sendMessage({
                action: 'updateBadge',
                count: collectedUrls.size
            });
        }, 500);
        
    }, settings.scrollIntervalMs);
}

function stopAutoScroll() {
    if (!isScrolling) return;
    
    isScrolling = false;
    if (scrollInterval) {
        clearInterval(scrollInterval);
        scrollInterval = null;
    }
    
    console.log('⏹️ Auto-Scroll Stopped');
    console.log(`✅ Collected ${collectedUrls.size} URLs total`);
    
    // Update badge
    chrome.runtime.sendMessage({
        action: 'updateBadge',
        count: collectedUrls.size
    });
}

function collectVideoUrls() {
    let newUrlsCount = 0;
    
    // Find all TikTok video links
    const videoLinks = document.querySelectorAll('a[href*="/video/"]');
    
    videoLinks.forEach(link => {
        const url = link.href;
        if (url && url.includes('/video/') && !collectedUrls.has(url)) {
            // Clean the URL (remove query parameters)
            const cleanUrl = url.split('?')[0];
            collectedUrls.add(cleanUrl);
            newUrlsCount++;
        }
    });
    
    // Also try to find video containers with data attributes
    const videoContainers = document.querySelectorAll('[data-e2e="user-post-item"]');
    videoContainers.forEach(container => {
        const link = container.querySelector('a');
        if (link && link.href && link.href.includes('/video/')) {
            const cleanUrl = link.href.split('?')[0];
            if (!collectedUrls.has(cleanUrl)) {
                collectedUrls.add(cleanUrl);
                newUrlsCount++;
            }
        }
    });
    
    return newUrlsCount;
}

// Initial collection when page loads
if (window.location.hostname === 'www.tiktok.com') {
    setTimeout(() => {
        collectVideoUrls();
        console.log(`📋 Initial collection: ${collectedUrls.size} URLs`);
    }, 2000);
}

// Inject a visual indicator
function showIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'tiktok-downloader-indicator';
    indicator.innerHTML = `
        <div style="
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            z-index: 10000;
            font-family: sans-serif;
            font-size: 14px;
            font-weight: 600;
        ">
            🔄 Collecting TikTok Videos...
            <div style="font-size: 12px; margin-top: 5px; opacity: 0.9;">
                <span id="indicator-count">0</span> URLs collected
            </div>
        </div>
    `;
    document.body.appendChild(indicator);
    
    // Update count periodically
    setInterval(() => {
        const countEl = document.getElementById('indicator-count');
        if (countEl && isScrolling) {
            countEl.textContent = collectedUrls.size;
        }
    }, 500);
}

// Show indicator when scrolling starts
chrome.runtime.onMessage.addListener((request) => {
    if (request.action === 'startScroll' && !document.getElementById('tiktok-downloader-indicator')) {
        showIndicator();
    } else if (request.action === 'stopScroll') {
        const indicator = document.getElementById('tiktok-downloader-indicator');
        if (indicator) indicator.remove();
    }
});
