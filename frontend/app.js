// TikTok Bulk Downloader Frontend
const API_BASE_URL = 'http://localhost:3000/api';

let currentTab = 'download';
let jobsRefreshInterval = null;
let lastJobsData = null; // Cache to prevent unnecessary re-renders

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadJobs();
    // Auto-refresh jobs every 5 seconds when on jobs tab
    startJobsAutoRefresh();
});

// Tab Management
function switchTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tab}-tab`).classList.add('active');
    
    if (tab === 'jobs') {
        loadJobs();
        startJobsAutoRefresh();
    } else {
        stopJobsAutoRefresh();
    }
}

function startJobsAutoRefresh() {
    if (jobsRefreshInterval) return;
    jobsRefreshInterval = setInterval(() => {
        if (currentTab === 'jobs') {
            loadJobs();
        }
    }, 2000);  // Refresh every 2 seconds for real-time updates
}

function stopJobsAutoRefresh() {
    if (jobsRefreshInterval) {
        clearInterval(jobsRefreshInterval);
        jobsRefreshInterval = null;
    }
}

// Download Functions
async function downloadFromUser() {
    const username = document.getElementById('username').value.trim().replace('@', '');
    
    if (!username) {
        showMessage('Please enter a username', 'error');
        return;
    }
    
    showMessage('Starting download...', 'success');
    
    try {
        const response = await fetch(`${API_BASE_URL}/download/user/${username}`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`✅ Started downloading videos from @${username}`, 'success');
            document.getElementById('username').value = '';
            
            // Switch to jobs tab
            setTimeout(() => {
                document.querySelector('.tab:nth-child(2)').click();
            }, 1000);
        } else {
            showMessage(`❌ Error: ${data.detail || 'Failed to start download'}`, 'error');
        }
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    }
}

async function downloadFromUrls() {
    const urlsText = document.getElementById('urls').value.trim();
    
    if (!urlsText) {
        showMessage('Please enter at least one URL', 'error');
        return;
    }
    
    const urls = urlsText.split('\n').map(url => url.trim()).filter(url => url);
    
    if (urls.length === 0) {
        showMessage('Please enter valid URLs', 'error');
        return;
    }
    
    showMessage(`Starting download of ${urls.length} videos...`, 'success');
    
    try {
        const response = await fetch(`${API_BASE_URL}/download/urls`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(urls)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage(`✅ Started downloading ${urls.length} videos`, 'success');
            document.getElementById('urls').value = '';
            
            // Switch to jobs tab
            setTimeout(() => {
                document.querySelector('.tab:nth-child(2)').click();
            }, 1000);
        } else {
            showMessage(`❌ Error: ${data.detail || 'Failed to start download'}`, 'error');
        }
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    }
}

// Jobs Management
async function loadJobs(forceRefresh = false) {
    const jobsList = document.getElementById('jobs-list');
    
    // Show loading only on first load
    if (!lastJobsData || forceRefresh) {
        jobsList.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading jobs...</p></div>';
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/manifest`);
        const data = await response.json();
        
        // Check if data actually changed to avoid unnecessary re-renders
        const dataString = JSON.stringify(data.jobs);
        if (lastJobsData === dataString && !forceRefresh) {
            return; // No changes, skip re-render
        }
        lastJobsData = dataString;
        
        if (data.jobs && data.jobs.length > 0) {
            // Update existing jobs or create new list
            const existingList = jobsList.querySelector('.jobs-list');
            if (existingList) {
                // Update each job card individually
                data.jobs.forEach((job, index) => {
                    const jobCard = document.getElementById(`job-${job.job_id}`);
                    if (jobCard) {
                        // Update only dynamic content
                        updateJobCard(jobCard, job);
                    } else {
                        // New job, add it at the top
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = renderJob(job);
                        existingList.insertBefore(tempDiv.firstElementChild, existingList.firstChild);
                    }
                });
            } else {
                // First render
                jobsList.innerHTML = '<div class="jobs-list">' + 
                    data.jobs.map(job => renderJob(job)).join('') + 
                    '</div>';
            }
        } else {
            jobsList.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">
                        <i class="fas fa-inbox"></i>
                    </div>
                    <h3>No download jobs yet</h3>
                    <p>Start downloading TikTok videos to see your jobs here</p>
                    <button onclick="switchTab('download')" style="margin-top: 20px;">
                        <i class="fas fa-plus"></i> Create New Job
                    </button>
                </div>
            `;
        }
    } catch (error) {
        jobsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h3>Failed to load jobs</h3>
                <p>${error.message}</p>
                <button onclick="loadJobs(true)" style="margin-top: 20px;">
                    <i class="fas fa-sync-alt"></i> Retry
                </button>
            </div>
        `;
    }
}

// Update only dynamic parts of a job card to prevent flickering
function updateJobCard(jobCard, job) {
    const progress = job.total_videos > 0 
        ? Math.round((job.downloaded / job.total_videos) * 100)
        : 0;
    
    // Update status badge
    const statusBadge = jobCard.querySelector('.status-badge');
    if (statusBadge) {
        statusBadge.className = `status-badge status-${job.status}`;
        const statusIcons = {
            'pending': 'fa-clock',
            'downloading': 'fa-spinner fa-spin',
            'paused': 'fa-pause',
            'stopped': 'fa-stop',
            'completed': 'fa-check',
            'failed': 'fa-times'
        };
        const icon = statusIcons[job.status] || 'fa-question';
        statusBadge.innerHTML = `<i class="fas ${icon}"></i> ${job.status}`;
    }
    
    // Update progress bar
    const progressFill = jobCard.querySelector('.progress-fill');
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    const progressText = jobCard.querySelector('.progress-text');
    if (progressText) {
        progressText.textContent = `${job.downloaded} / ${job.total_videos} videos (${progress}%)`;
    }
    
    // Update control buttons if status changed
    const controlsDiv = jobCard.querySelector('.job-controls');
    if (controlsDiv) {
        let newButtons = '';
        if (job.status === 'downloading') {
            newButtons = `
                <button onclick="pauseJob('${job.job_id}')" class="control-btn pause-btn">
                    <i class="fas fa-pause"></i> Pause
                </button>
                <button onclick="stopJob('${job.job_id}')" class="control-btn stop-btn">
                    <i class="fas fa-stop"></i> Stop
                </button>
            `;
        } else if (job.status === 'paused') {
            newButtons = `
                <button onclick="resumeJob('${job.job_id}')" class="control-btn resume-btn">
                    <i class="fas fa-play"></i> Resume
                </button>
                <button onclick="stopJob('${job.job_id}')" class="control-btn stop-btn">
                    <i class="fas fa-stop"></i> Stop
                </button>
            `;
        } else if (job.status === 'failed' || job.status === 'stopped') {
            newButtons = `
                <button onclick="retryJob('${job.job_id}')" class="control-btn resume-btn">
                    <i class="fas fa-redo"></i> Retry
                </button>
            `;
        }
        if (controlsDiv.innerHTML.trim() !== newButtons.trim()) {
            controlsDiv.innerHTML = newButtons;
        }
    }
}

function renderJob(job) {
    const statusClass = `status-${job.status}`;
    const createdDate = new Date(job.created_at).toLocaleString();
    
    // Calculate progress percentage
    const progress = job.total_videos > 0 
        ? Math.round((job.downloaded / job.total_videos) * 100)
        : 0;
    
    // Status icons
    const statusIcons = {
        'pending': 'fa-clock',
        'downloading': 'fa-spinner fa-spin',
        'paused': 'fa-pause',
        'stopped': 'fa-stop',
        'completed': 'fa-check',
        'failed': 'fa-times'
    };
    
    const statusIcon = statusIcons[job.status] || 'fa-question';
    
    // Control buttons based on status
    let controlButtons = '';
    if (job.status === 'downloading') {
        controlButtons = `
            <div class="job-controls">
                <button class="btn-control btn-pause" onclick="pauseJob('${job.job_id}')">
                    <i class="fas fa-pause"></i> Pause
                </button>
                <button class="btn-control btn-stop" onclick="stopJob('${job.job_id}')">
                    <i class="fas fa-stop"></i> Stop
                </button>
            </div>
        `;
    } else if (job.status === 'paused') {
        controlButtons = `
            <div class="job-controls">
                <button class="btn-control btn-resume" onclick="resumeJob('${job.job_id}')">
                    <i class="fas fa-play"></i> Resume
                </button>
                <button class="btn-control btn-stop" onclick="stopJob('${job.job_id}')">
                    <i class="fas fa-stop"></i> Stop
                </button>
            </div>
        `;
    }
    
    return `
        <div class="job-item" id="job-${job.job_id}">
            <div class="job-header">
                <div class="job-title-section">
                    <div class="job-name">
                        <i class="fas fa-folder"></i>
                        ${job.job_name}
                    </div>
                    <div class="job-meta">
                        <i class="fas fa-calendar"></i>
                        ${createdDate}
                        ${job.username ? `<span style="margin-left: 12px;"><i class="fas fa-user"></i> @${job.username}</span>` : ''}
                    </div>
                </div>
                <div class="job-status ${statusClass} status-badge">
                    <i class="fas ${statusIcon}"></i>
                    ${job.status.toUpperCase()}
                </div>
            </div>
            
            ${job.total_videos > 0 && (job.status === 'downloading' || job.status === 'paused') ? `
                <div class="job-progress">
                    <div class="progress-bar-container">
                        <div class="progress-bar progress-fill" style="width: ${progress}%"></div>
                    </div>
                    <div class="progress-text">
                        <span>${progress}% Complete</span>
                        <span>${job.downloaded}/${job.total_videos} videos</span>
                    </div>
                </div>
            ` : ''}
            
            <div class="job-stats">
                ${job.total_videos > 0 ? `
                    <div class="stat-item info">
                        <i class="fas fa-video"></i>
                        <span>${job.total_videos} Total</span>
                    </div>
                ` : ''}
                ${job.downloaded > 0 ? `
                    <div class="stat-item success">
                        <i class="fas fa-check-circle"></i>
                        <span>${job.downloaded} Downloaded</span>
                    </div>
                ` : ''}
                ${job.failed > 0 ? `
                    <div class="stat-item error">
                        <i class="fas fa-times-circle"></i>
                        <span>${job.failed} Failed</span>
                    </div>
                ` : ''}
                ${job.skipped > 0 ? `
                    <div class="stat-item warning">
                        <i class="fas fa-forward"></i>
                        <span>${job.skipped} Skipped</span>
                    </div>
                ` : ''}
            </div>
            
            ${controlButtons}
            
            ${job.download_path ? `
                <div class="job-path">
                    <i class="fas fa-folder-open"></i> ${job.download_path}
                </div>
            ` : ''}
        </div>
    `;
}

// Preview Functions
async function previewUser() {
    const username = document.getElementById('username').value.trim().replace('@', '');
    
    if (!username) {
        showMessage('Please enter a username', 'error');
        return;
    }
    
    const previewSection = document.getElementById('previewSection');
    const previewContent = document.getElementById('previewContent');
    
    previewSection.style.display = 'block';
    previewContent.innerHTML = '<div class="loading"><div class="spinner"></div><p>Fetching video information...</p></div>';
    
    showMessage('Fetching video information...', 'success');
    
    try {
        const response = await fetch(`${API_BASE_URL}/preview/user/${username}`);
        const data = await response.json();
        
        if (response.ok) {
            // Build status message
            let statusMessage = '';
            let statusIcon = 'fa-video';
            let statusColor = 'var(--text-secondary)';
            
            if (data.profile_exists) {
                if (data.new_videos > 0) {
                    statusMessage = `${data.new_videos} new video${data.new_videos !== 1 ? 's' : ''} found! (${data.downloaded_videos} already downloaded)`;
                    statusIcon = 'fa-sparkles';
                    statusColor = '#00f2ea';
                } else {
                    statusMessage = `All ${data.total_videos} videos already tracked (${data.downloaded_videos} downloaded)`;
                    statusIcon = 'fa-check-circle';
                    statusColor = '#4ade80';
                }
            } else {
                statusMessage = `New profile: ${data.total_videos} videos discovered`;
                statusIcon = 'fa-user-plus';
                statusColor = '#00f2ea';
            }
            
            previewContent.innerHTML = `
                <div class="preview-header">
                    <div>
                        <h4 style="margin-bottom: 8px; color: var(--text-primary); display: flex; align-items: center; gap: 8px;">
                            <i class="fas fa-user"></i> @${data.username}
                        </h4>
                        <div class="preview-status" style="color: ${statusColor}; font-size: 0.95em; margin-bottom: 12px; display: flex; align-items: center; gap: 6px;">
                            <i class="fas ${statusIcon}"></i>
                            <strong>${statusMessage}</strong>
                        </div>
                        <div class="preview-stats" style="display: flex; gap: 20px; flex-wrap: wrap; margin-bottom: 16px;">
                            <div class="stat-item" style="display: flex; align-items: center; gap: 6px; color: var(--text-secondary); font-size: 0.9em;">
                                <i class="fas fa-video"></i>
                                <span>${data.total_videos} Total</span>
                            </div>
                            ${data.profile_exists ? `
                                <div class="stat-item" style="display: flex; align-items: center; gap: 6px; color: #00f2ea; font-size: 0.9em;">
                                    <i class="fas fa-sparkles"></i>
                                    <span>${data.new_videos} New</span>
                                </div>
                                <div class="stat-item" style="display: flex; align-items: center; gap: 6px; color: #4ade80; font-size: 0.9em;">
                                    <i class="fas fa-check"></i>
                                    <span>${data.downloaded_videos} Downloaded</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                
                ${data.videos && data.videos.length > 0 ? `
                    <p style="color: var(--text-secondary); margin-bottom: 12px; font-size: 0.9em;">
                        <i class="fas fa-info-circle"></i> Showing first ${data.videos.length} videos
                        ${data.new_videos > 0 && data.profile_exists ? `<span style="color: #00f2ea;"> • ${data.new_videos} new</span>` : ''}
                    </p>
                    <div class="video-list">
                        ${data.videos.map((v, i) => `
                            <div class="video-item" style="${v.is_new ? 'border-left: 3px solid #00f2ea; padding-left: 12px;' : ''}">
                                <div class="video-number">${i + 1}.</div>
                                <div class="video-title">
                                    ${v.is_new ? '<span style="color: #00f2ea; font-size: 0.8em; margin-right: 6px;"><i class="fas fa-sparkles"></i> NEW</span>' : ''}
                                    ${v.title}
                                </div>
                                ${v.view_count ? `
                                    <div class="video-views">
                                        <i class="fas fa-eye"></i>
                                        ${formatNumber(v.view_count)}
                                    </div>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                <div class="button-group" style="margin-top: 20px;">
                    ${data.new_videos > 0 || !data.profile_exists ? `
                        <button onclick="downloadFromUser()">
                            <i class="fas fa-download"></i> Download ${data.new_videos > 0 ? `${data.new_videos} New Video${data.new_videos !== 1 ? 's' : ''}` : `All ${data.total_videos} Videos`}
                        </button>
                    ` : `
                        <button onclick="downloadFromUser()">
                            <i class="fas fa-sync-alt"></i> Re-download (${data.total_videos} videos)
                        </button>
                    `}
                    <button onclick="closePreview()" class="secondary">
                        <i class="fas fa-list"></i> Select URLs to Download
                    </button>
                </div>
            `;
            
            // Store preview data for later use
            window.previewData = data;
            
            showMessage(`Found ${data.total_videos} videos from @${data.username}`, 'success');
        } else {
            previewContent.innerHTML = `
                <div style="text-align: center; padding: 40px; color: var(--error);">
                    <i class="fas fa-exclamation-circle" style="font-size: 3em; margin-bottom: 16px;"></i>
                    <p style="font-size: 1.1em;">${data.detail || 'Failed to fetch video information'}</p>
                </div>
            `;
            showMessage(`Error: ${data.detail || 'Failed to fetch videos'}`, 'error');
        }
    } catch (error) {
        previewContent.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--error);">
                <i class="fas fa-exclamation-circle" style="font-size: 3em; margin-bottom: 16px;"></i>
                <p style="font-size: 1.1em;">${error.message}</p>
            </div>
        `;
        showMessage(`Error: ${error.message}`, 'error');
    }
}

async function downloadSelectedFromPreview() {
    if (!window.previewData || !window.previewData.videos) {
        showMessage('No preview data available', 'error');
        return;
    }
    
    // Extract URLs from preview data
    const urls = window.previewData.videos.map(v => v.url).filter(url => url);
    
    if (urls.length === 0) {
        showMessage('No video URLs found in preview', 'error');
        return;
    }
    
    // Put URLs in the textarea
    document.getElementById('urls').value = urls.join('\n');
    
    // Scroll to the URLs section
    document.getElementById('urls').scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    showMessage(`📋 ${urls.length} URLs added to the list. Review and click "Download Videos"`, 'success');
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num;
}

// Job Control Functions
async function pauseJob(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/pause`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('⏸️ Download paused', 'success');
            loadJobs();
        } else {
            showMessage(`❌ Error: ${data.detail || 'Failed to pause'}`, 'error');
        }
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    }
}

async function resumeJob(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/resume`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('▶️ Download resumed', 'success');
            loadJobs();
        } else {
            showMessage(`❌ Error: ${data.detail || 'Failed to resume'}`, 'error');
        }
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    }
}

async function stopJob(jobId) {
    if (!confirm('Are you sure you want to stop this download? Progress will be saved but incomplete downloads will be lost.')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showMessage('⏹️ Download stopped', 'success');
            loadJobs();
        } else {
            showMessage(`❌ Error: ${data.detail || 'Failed to stop'}`, 'error');
        }
    } catch (error) {
        showMessage(`❌ Error: ${error.message}`, 'error');
    }
}

// UI Helpers
function showMessage(text, type) {
    const messageEl = document.getElementById('message');
    const icon = type === 'success' ? '<i class="fas fa-check-circle"></i>' : '<i class="fas fa-exclamation-circle"></i>';
    messageEl.innerHTML = icon + '<span>' + text + '</span>';
    messageEl.className = `message ${type} show`;
    
    setTimeout(() => {
        messageEl.classList.remove('show');
    }, 5000);
}
