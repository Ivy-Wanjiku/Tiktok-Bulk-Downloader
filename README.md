# 🎬 TikTok Bulk Downloader

A production-ready TikTok video bulk downloader with FastAPI backend, modern web interface, and browser extension support. Features robust error handling, database persistence, and real-time progress tracking.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0.25-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## ✨ Features

### Core Functionality
- 📥 **Bulk Download** - Download entire TikTok user profiles or specific video lists
- ⏸️ **Pause/Resume/Stop** - Full download control with state management
- 🔄 **Smart Retry Logic** - Automatic retry with exponential backoff (3 attempts)
- 🚫 **Duplicate Detection** - SHA256 hash-based duplicate prevention
- 📊 **Real-Time Progress** - Live download status and statistics
- 🗄️ **Database Persistence** - SQLite with SQLAlchemy ORM for complete history tracking

### User Interface
- 🎨 **Modern Dark Theme** - TikTok-inspired design with gradient effects
- 📱 **Responsive Design** - Works on desktop and mobile
- 🔍 **Preview Mode** - Check video counts before downloading
- 📈 **Progress Bars** - Visual progress tracking with shimmer animations
- 🎯 **Job Management** - Create, monitor, pause, resume, and stop jobs

### Browser Extension
- 🌐 **Chrome/Firefox Extension** - Collect video URLs while browsing TikTok
- 📋 **Automatic URL Collection** - Gather URLs as you scroll through profiles
- 🔗 **Direct Integration** - Send collected URLs directly to downloader

### Technical Features
- 🔒 **Security** - Input validation, CORS protection, rate limit detection
- 📝 **Structured Logging** - Rotating logs with file and console output
- 💾 **Session Management** - Proper database connection pooling
- ⚡ **Performance** - Database indexing and query optimization
- 🧹 **Auto Cleanup** - Stale job detection and partial download cleanup
- 🔧 **Configurable** - Environment-based configuration with `.env` support

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd tiktok-bulk-downloader
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r backend/requirements.txt
```

4. **Configure environment (optional)**
```bash
cp .env.example .env
nano .env  # Edit configuration as needed
```

5. **Start the server**
```bash
python backend/api.py
```

The API will be available at `http://localhost:3000`  
Web interface: Open `frontend/index.html` in your browser  
API Documentation: `http://localhost:3000/docs`

### Using the Quick Start Script
```bash
./start.sh  # Starts backend and opens frontend
```

---

## 📖 Usage

### Web Interface

1. **Open Frontend**: Navigate to `frontend/index.html` in your browser
2. **Enter TikTok Username** or paste video URLs
3. **Preview** (optional): Click "Preview" to see video count
4. **Download**: Click "Download" to start
5. **Monitor**: View real-time progress in the Jobs section
6. **Control**: Use pause/resume/stop buttons as needed

### Browser Extension

1. **Load Extension**: 
   - Chrome: Go to `chrome://extensions/`, enable Developer mode, click "Load unpacked", select `extension/` folder
   - Firefox: Go to `about:debugging#/runtime/this-firefox`, click "Load Temporary Add-on", select `extension/manifest.json`

2. **Use Extension**:
   - Visit any TikTok profile page
   - Click the extension icon
   - Click "Start Collecting"
   - Scroll through the profile to collect video URLs
   - Click "Send to Downloader" when done

### API Usage

#### Download User Videos
```bash
curl -X POST "http://localhost:3000/api/download/user/username" \
  -H "Content-Type: application/json" \
  -d '{"job_name": "My Download Job"}'
```

#### Download from URLs
```bash
curl -X POST "http://localhost:3000/api/download/urls" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": [
      "https://www.tiktok.com/@user/video/123456789",
      "https://www.tiktok.com/@user/video/987654321"
    ],
    "job_name": "URL Download"
  }'
```

#### Preview User Videos
```bash
curl -X GET "http://localhost:3000/api/preview/user/username"
```

#### Get Statistics
```bash
curl -X GET "http://localhost:3000/api/statistics"
```

#### List Profiles
```bash
curl -X GET "http://localhost:3000/api/profiles"
```

#### Get Profile Videos
```bash
curl -X GET "http://localhost:3000/api/profiles/username/videos"
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```env
# Server Configuration
API_HOST=0.0.0.0
API_PORT=3000
ENVIRONMENT=development

# Security Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ENABLE_AUTH=false
API_KEY=

# Download Configuration
MAX_CONCURRENT_DOWNLOADS=3
JOB_TIMEOUT_HOURS=2
```

### Configuration File

Edit `backend/config.py` for advanced settings:
- Download directory location
- Quality settings
- Timeout values
- Retry attempts and delays
- Input validation rules

---

## 📁 Project Structure

```
tiktok-bulk-downloader/
├── backend/
│   ├── api.py              # FastAPI server with endpoints
│   ├── downloader.py       # yt-dlp wrapper with retry logic
│   ├── db_service.py       # Database service layer
│   ├── models.py           # SQLAlchemy ORM models
│   ├── config.py           # Configuration and logging setup
│   └── requirements.txt    # Python dependencies
├── frontend/
│   ├── index.html          # Web interface
│   ├── app.js              # Frontend JavaScript
│   └── (static assets)
├── extension/
│   ├── manifest.json       # Extension manifest
│   ├── background.js       # Background script
│   ├── content.js          # Content script
│   ├── popup.html          # Extension popup
│   └── popup.js            # Popup logic
├── downloads/              # Downloaded videos (auto-created)
├── logs/                   # Application logs (auto-created)
├── .env.example            # Environment configuration template
├── tiktok_downloader.db    # SQLite database (auto-created)
├── start.sh                # Quick start script
├── stop.sh                 # Stop server script
└── README.md               # This file
```

---

## 🗄️ Database Schema

### TikTokProfile
- Primary Key: `username`
- Tracks: Profile metadata, follower counts, download statistics
- Relationships: One-to-many with Videos and Jobs

### TikTokVideo
- Primary Key: `video_id`
- Foreign Key: `profile_username` (references TikTokProfile)
- Tracks: Video metadata, statistics, download status, file hash
- Indexed on: profile_username, download_status, upload_date, file_hash

### DownloadJob
- Primary Key: `job_id`
- Foreign Key: `profile_username` (optional)
- Tracks: Job status, progress, timestamps, error messages
- Indexed on: status, created_at

---

## 🛠️ API Endpoints

### Health & Information
- `GET /` - API information
- `GET /api/health` - Health check

### Download Operations
- `POST /api/download/user/{username}` - Download user's videos
- `POST /api/download/urls` - Download from URL list
- `GET /api/preview/user/{username}` - Preview video count

### Job Management
- `GET /api/manifest` - List all jobs
- `GET /api/manifest/{job_id}` - Get job details
- `POST /api/manifest/create` - Create new job
- `DELETE /api/manifest/{job_id}` - Delete job
- `POST /api/jobs/{job_id}/pause` - Pause job
- `POST /api/jobs/{job_id}/resume` - Resume job
- `POST /api/jobs/{job_id}/stop` - Stop job

### Database Queries
- `GET /api/statistics` - Overall statistics
- `GET /api/profiles` - List all profiles
- `GET /api/profiles/{username}` - Profile details
- `GET /api/profiles/{username}/videos` - Videos for profile
- `GET /api/videos/{video_id}` - Video details

**Interactive Documentation:** `http://localhost:3000/docs` (Swagger UI)

---

## 📝 Logging

Logs are automatically written to `logs/tiktok_downloader.log` with:
- **Rotation**: 10MB max file size, keeps 5 backups
- **Format**: Timestamp, logger name, level, file:line, message
- **Levels**: INFO (development), WARNING (production)

View logs in real-time:
```bash
tail -f logs/tiktok_downloader.log
```

---

## 🔒 Security Features

- ✅ **Input Validation** - Username and URL sanitization
- ✅ **CORS Protection** - Restricted origins
- ✅ **Path Traversal Prevention** - Secure file handling
- ✅ **Rate Limit Detection** - Handles TikTok API rate limits
- ✅ **SQL Injection Protection** - SQLAlchemy ORM parameterization
- ✅ **Length Limits** - Enforced on all inputs

---

## ⚠️ Known Limitations

1. **Photo/Slideshow Posts**: TikTok photo posts are not supported by yt-dlp. Only video posts can be downloaded.
2. **Rate Limiting**: TikTok may rate limit requests. The system will automatically retry with exponential backoff.
3. **Private Profiles**: Cannot download from private TikTok accounts.
4. **Sequential Downloads**: Currently downloads run sequentially. Concurrent downloading planned for future release.

---

## 🐛 Troubleshooting

### Port Already in Use
```bash
lsof -ti:3000 | xargs -r kill -9
```

### Database Issues
Delete and recreate:
```bash
rm tiktok_downloader.db
python backend/api.py  # Will auto-recreate
```

### Dependency Issues
```bash
pip install --upgrade -r backend/requirements.txt
```

### Download Failures
- Check logs: `logs/tiktok_downloader.log`
- Verify TikTok URL is valid
- Ensure the video is not a photo/slideshow post
- Check network connectivity

---

## 🚧 Roadmap

### Phase 2 (Planned)
- [ ] WebSocket real-time updates (replace polling)
- [ ] Frontend analytics dashboard
- [ ] Migrate existing manifest.json to database
- [ ] Bulk operations UI (delete multiple, retry failed)

### Phase 3 (Future)
- [ ] Unit and integration tests
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Docker containerization
- [ ] True concurrent downloads
- [ ] Cloud storage integration (S3, Google Drive)
- [ ] Scheduled downloads
- [ ] Mobile app

See `IMPROVEMENTS.md` for detailed feature ideas and analysis.

---

## 📊 Performance

- **Database Queries**: Optimized with 7 strategic indexes
- **Memory Management**: Bounded hash set (max 10,000 entries)
- **Session Pooling**: Proper connection lifecycle management
- **Retry Logic**: Smart backoff prevents server overload
- **Cleanup**: Automatic removal of partial downloads and stale jobs

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

---

## ⚖️ Legal Notice

This tool is for educational purposes and personal use only. Users are responsible for complying with TikTok's Terms of Service and respecting content creators' rights. Do not use this tool to:
- Download copyrighted content without permission
- Violate TikTok's Terms of Service
- Redistribute downloaded content
- Engage in any illegal activities

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video download engine
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM
- [Font Awesome](https://fontawesome.com/) - Icons

---

## 📧 Support

For issues, questions, or feature requests, please open an issue on GitHub.

**Version:** 1.0.0  
**Last Updated:** January 10, 2026
