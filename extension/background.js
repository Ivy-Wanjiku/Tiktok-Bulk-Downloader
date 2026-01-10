// Background service worker

// Update badge when URLs are collected
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'updateBadge') {
        chrome.action.setBadgeText({ 
            text: request.count > 0 ? String(request.count) : '',
            tabId: sender.tab.id
        });
        chrome.action.setBadgeBackgroundColor({ 
            color: '#667eea',
            tabId: sender.tab.id
        });
    }
});

// Clear badge when tab is closed or navigated away from TikTok
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && !tab.url.includes('tiktok.com')) {
        chrome.action.setBadgeText({ text: '', tabId: tabId });
    }
});

console.log('TikTok Bulk Downloader extension loaded');
