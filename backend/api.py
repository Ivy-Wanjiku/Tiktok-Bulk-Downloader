#!/usr/bin/env python3
"""
TikTok Bulk Downloader - Main API Server
FastAPI backend for managing TikTok video downloads
"""

import os
import json
import re
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator, Field
import uvicorn

from config import (
    API_HOST, API_PORT, DOWNLOADS_DIR, MANIFEST_FILE,
    ALLOWED_ORIGINS, USERNAME_PATTERN,
    MAX_USERNAME_LENGTH, MAX_URL_LENGTH
)
from downloader import TikTokDownloader
from db_service import db_service

logger = logging.getLogger(__name__)

app = FastAPI(title="TikTok Bulk Downloader API", version="1.0.0")

# CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Restricted from ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Only needed methods
    allow_headers=["*"],
)

# Initialize downloader
downloader = TikTokDownloader()

# Thread pool for running downloads
executor = ThreadPoolExecutor(max_workers=2)

# Input validation helper
def sanitize_username(username: str) -> str:
    """Sanitize username to prevent path traversal and injection"""
    if not username:
        raise ValueError("Username cannot be empty")
    
    # Remove @ prefix if present
    username = username.lstrip('@')
    
    # Validate length
    if len(username) > MAX_USERNAME_LENGTH:
        raise ValueError(f"Username too long (max {MAX_USERNAME_LENGTH} characters)")
    
    # Validate pattern (alphanumeric, dots, underscores only)
    if not re.match(USERNAME_PATTERN, username):
        raise ValueError("Username contains invalid characters")
    
    return username

def sanitize_url(url: str) -> str:
    """Sanitize URL to prevent injection attacks"""
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Validate length
    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f"URL too long (max {MAX_URL_LENGTH} characters)")
    
    # Must be TikTok URL
    if not re.match(r'^https?://(www\.)?(tiktok\.com|vm\.tiktok\.com)/', url):
        raise ValueError("URL must be a valid TikTok URL")
    
    return url

# Pydantic models with validation
class DownloadJobCreate(BaseModel):
    username: Optional[str] = Field(None, max_length=MAX_USERNAME_LENGTH)
    urls: Optional[List[str]] = Field(None, max_items=1000)
    job_name: Optional[str] = Field(None, max_length=200)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v:
            return sanitize_username(v)
        return v
    
    @field_validator('urls')
    @classmethod
    def validate_urls(cls, v):
        if v:
            if len(v) > 1000:
                raise ValueError("Too many URLs (max 1000)")
            return [sanitize_url(url) for url in v]
        return v

class DownloadJob(BaseModel):
    job_id: str
    job_name: str
    status: str
    created_at: str
    username: Optional[str] = None
    total_videos: int = 0
    downloaded: int = 0
    failed: int = 0
    download_path: str = ""

# Manifest management
class ManifestManager:
    def __init__(self, manifest_file: Path):
        self.manifest_file = manifest_file
        self._load_manifest()
    
    def _load_manifest(self):
        if self.manifest_file.exists():
            with open(self.manifest_file, 'r') as f:
                self.manifest = json.load(f)
        else:
            self.manifest = {"jobs": []}
    
    def _save_manifest(self):
        with open(self.manifest_file, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def create_job(self, job_data: dict) -> dict:
        job_id = str(uuid4())
        
        # Use username for folder name if available, otherwise use job_id
        username = job_data.get("username")
        if username:
            # Username already sanitized by validator
            folder_name = username.lstrip('@')
        else:
            folder_name = job_id
        
        job = {
            "job_id": job_id,
            "job_name": job_data.get("job_name", f"Job {job_id[:8]}"),
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "username": job_data.get("username"),
            "urls": job_data.get("urls", []),
            "total_videos": 0,
            "downloaded": 0,
            "failed": 0,
            "download_path": str(DOWNLOADS_DIR / folder_name)
        }
        self.manifest["jobs"].append(job)
        self._save_manifest()
        return job
    
    def get_job(self, job_id: str) -> Optional[dict]:
        for job in self.manifest["jobs"]:
            if job["job_id"] == job_id:
                return job
        return None
    
    def update_job(self, job_id: str, updates: dict):
        for job in self.manifest["jobs"]:
            if job["job_id"] == job_id:
                job.update(updates)
                self._save_manifest()
                return job
        return None
    
    def list_jobs(self) -> List[dict]:
        # Sort jobs by created_at descending (newest first)
        jobs = self.manifest["jobs"]
        return sorted(jobs, key=lambda x: x.get('created_at', ''), reverse=True)

manifest_manager = ManifestManager(MANIFEST_FILE)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and cleanup stale jobs on startup"""
    logger.info("Starting TikTok Bulk Downloader API")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    
    # Initialize database
    try:
        from config import DB_PATH
        db_service.engine = db_service.engine or db_service.__init__(str(DB_PATH))
        logger.info(f"Database initialized: {DB_PATH}")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Cleanup stale jobs
    try:
        from config import JOB_TIMEOUT_HOURS
        stale_count = db_service.cleanup_stale_jobs(timeout_hours=JOB_TIMEOUT_HOURS)
        if stale_count > 0:
            logger.warning(f"Cleaned up {stale_count} stale job(s)")
        else:
            logger.info("No stale jobs found")
    except Exception as e:
        logger.error(f"Stale job cleanup failed: {e}")
    
    logger.info("API startup complete")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down TikTok Bulk Downloader API")
    executor.shutdown(wait=False)
    logger.info("API shutdown complete")

# API Routes
@app.get("/")
async def root():
    return {
        "name": "TikTok Bulk Downloader API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "downloads_dir": str(DOWNLOADS_DIR)}

@app.get("/api/manifest")
async def list_jobs():
    """List all download jobs"""
    jobs = manifest_manager.list_jobs()
    return {"jobs": jobs, "total": len(jobs)}

@app.get("/api/manifest/{job_id}")
async def get_job(job_id: str):
    """Get specific job details"""
    job = manifest_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.post("/api/manifest/create")
async def create_job(job_data: DownloadJobCreate, background_tasks: BackgroundTasks):
    """Create a new download job"""
    if not job_data.username and not job_data.urls:
        raise HTTPException(
            status_code=400,
            detail="Either username or urls must be provided"
        )
    
    job = manifest_manager.create_job(job_data.dict())
    
    # Start download in background
    background_tasks.add_task(process_download_job, job["job_id"])
    
    return {"job": job, "message": "Download job created and started"}

@app.post("/api/download/user/{username}")
async def download_user_videos(username: str, background_tasks: BackgroundTasks):
    """Download all videos from a TikTok user"""
    job_data = {
        "username": username,
        "job_name": f"Download @{username}"
    }
    job = manifest_manager.create_job(job_data)
    background_tasks.add_task(process_download_job, job["job_id"])
    
    return {
        "job_id": job["job_id"],
        "username": username,
        "message": f"Started downloading videos from @{username}"
    }

@app.get("/api/preview/user/{username}")
async def preview_user_videos(username: str):
    """Preview video count and info for a TikTok user without downloading"""
    try:
        result = await downloader.preview_user_videos(username)
        
        if result['success']:
            return {
                "username": result['username'],
                "total_videos": result['total_videos'],
                "videos": result['videos'],
                "message": f"Found {result['total_videos']} videos"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result['error'] or "Failed to fetch video information"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/videos/user/{username}")
async def get_user_video_urls(username: str):
    """Get direct download URLs for all videos from a TikTok user (for extension)"""
    try:
        result = await downloader.get_video_download_urls(username)
        
        if result['success']:
            return {
                "username": result['username'],
                "total_videos": result['total_videos'],
                "videos": result['videos'],
                "message": f"Found {result['total_videos']} videos with download URLs"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result['error'] or "Failed to fetch video URLs"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download/urls")
async def download_from_urls(urls: List[str], background_tasks: BackgroundTasks):
    """Download videos from a list of URLs"""
    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided")
    
    job_data = {
        "urls": urls,
        "job_name": f"Download {len(urls)} videos"
    }
    job = manifest_manager.create_job(job_data)
    background_tasks.add_task(process_download_job, job["job_id"])
    
    return {
        "job_id": job["job_id"],
        "total_urls": len(urls),
        "message": f"Started downloading {len(urls)} videos"
    }

@app.delete("/api/manifest/{job_id}")
async def delete_job(job_id: str):
    """Delete a download job"""
    job = manifest_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Remove from manifest
    manifest_manager.manifest["jobs"] = [
        j for j in manifest_manager.manifest["jobs"] 
        if j["job_id"] != job_id
    ]
    manifest_manager._save_manifest()
    
    return {"message": f"Job {job_id} deleted"}

# Control endpoints
@app.post("/api/jobs/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a running download job"""
    job = manifest_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "downloading":
        raise HTTPException(status_code=400, detail="Job is not currently downloading")
    
    if downloader.current_job_id == job_id:
        downloader.pause_download()
        manifest_manager.update_job(job_id, {"status": "paused"})
        return {"message": f"Job {job_id} paused", "status": "paused"}
    
    raise HTTPException(status_code=400, detail="Job is not active")

@app.post("/api/jobs/{job_id}/resume")
async def resume_job(job_id: str):
    """Resume a paused download job"""
    job = manifest_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] != "paused":
        raise HTTPException(status_code=400, detail="Job is not paused")
    
    if downloader.current_job_id == job_id:
        downloader.resume_download()
        manifest_manager.update_job(job_id, {"status": "downloading"})
        return {"message": f"Job {job_id} resumed", "status": "downloading"}
    
    raise HTTPException(status_code=400, detail="Job is not active")

@app.post("/api/jobs/{job_id}/stop")
async def stop_job(job_id: str):
    """Stop a running or paused download job"""
    job = manifest_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job["status"] not in ["downloading", "paused"]:
        raise HTTPException(status_code=400, detail="Job is not active")
    
    if downloader.current_job_id == job_id:
        downloader.stop_download()
        manifest_manager.update_job(job_id, {"status": "stopped"})
        return {"message": f"Job {job_id} stopped", "status": "stopped"}
    
    raise HTTPException(status_code=400, detail="Job is not active")

# Background task processor
async def process_download_job(job_id: str):
    """Process a download job in the background using thread pool"""
    job = manifest_manager.get_job(job_id)
    if not job:
        return
    
    # Progress callback to update manifest in real-time
    async def progress_callback(progress_data):
        manifest_manager.update_job(job_id, {
            'downloaded': progress_data.get('downloaded', 0),
            'failed': progress_data.get('failed', 0),
            'skipped': progress_data.get('skipped', 0)
        })
    
    # Set progress callback
    downloader.set_progress_callback(progress_callback)
    
    # Run download in thread pool to avoid blocking
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _sync_download_job, job_id)

def _sync_download_job(job_id: str):
    """Synchronous download job runner"""
    job = manifest_manager.get_job(job_id)
    if not job:
        return
    
    try:
        # Reset downloader state for this job
        downloader.reset_state(job_id)
        manifest_manager.update_job(job_id, {"status": "downloading"})
        
        # Create job download directory
        job_path = Path(job["download_path"])
        job_path.mkdir(parents=True, exist_ok=True)
        
        # Run async function in new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            if job.get("username"):
                # Download user's videos
                result = loop.run_until_complete(
                    downloader.download_user_videos(
                        job["username"],
                        str(job_path)
                    )
                )
                # Check if stopped
                if downloader.is_stopped:
                    manifest_manager.update_job(job_id, {
                        "status": "stopped",
                        "total_videos": result["total"],
                        "downloaded": result["downloaded"],
                        "failed": result["failed"],
                        "skipped": result.get("skipped", 0)
                    })
                else:
                    manifest_manager.update_job(job_id, {
                        "status": "completed",
                        "total_videos": result["total"],
                        "downloaded": result["downloaded"],
                        "failed": result["failed"],
                        "skipped": result.get("skipped", 0)
                    })
            elif job.get("urls"):
                # Download from URL list
                result = loop.run_until_complete(
                    downloader.download_from_urls(
                        job["urls"],
                        str(job_path),
                        username=job.get("username")
                    )
                )
                # Check if stopped
                if downloader.is_stopped:
                    manifest_manager.update_job(job_id, {
                        "status": "stopped",
                        "total_videos": len(job["urls"]),
                        "downloaded": result["downloaded"],
                        "failed": result["failed"],
                        "skipped": result.get("skipped", 0)
                    })
                else:
                    manifest_manager.update_job(job_id, {
                        "status": "completed",
                        "total_videos": len(job["urls"]),
                        "downloaded": result["downloaded"],
                        "failed": result["failed"],
                        "skipped": result.get("skipped", 0)
                    })
        finally:
            loop.close()
            
    except Exception as e:
        manifest_manager.update_job(job_id, {
            "status": "failed",
            "error": str(e)
        })

# ==================== Database API Endpoints ====================

@app.get("/api/statistics")
async def get_statistics():
    """Get overall download statistics from database"""
    try:
        stats = db_service.get_statistics()
        return {"success": True, "statistics": stats}
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles")
async def list_profiles():
    """Get all TikTok profiles in database"""
    try:
        profiles = db_service.get_all_profiles()
        return {
            "success": True,
            "total": len(profiles),
            "profiles": [
                {
                    "username": p.username,
                    "display_name": p.display_name,
                    "video_count": p.video_count,
                    "total_downloaded": p.total_videos_downloaded,
                    "total_failed": p.total_download_fails,
                    "profile_url": p.profile_url,
                    "last_scraped": p.last_scraped.isoformat() if p.last_scraped else None
                }
                for p in profiles
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{username}")
async def get_profile(username: str):
    """Get profile details and statistics"""
    try:
        username = sanitize_username(username)
        profile = db_service.get_profile(username)
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        stats = db_service.get_profile_statistics(username)
        
        return {
            "success": True,
            "profile": {
                "username": profile.username,
                "display_name": profile.display_name,
                "bio": profile.bio,
                "follower_count": profile.follower_count,
                "video_count": profile.video_count,
                "profile_url": profile.profile_url,
                "first_scraped": profile.first_scraped.isoformat() if profile.first_scraped else None,
                "last_scraped": profile.last_scraped.isoformat() if profile.last_scraped else None,
            },
            "statistics": stats
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get profile {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profiles/{username}/videos")
async def get_profile_videos(username: str, downloaded_only: bool = False):
    """Get all videos for a profile"""
    try:
        username = sanitize_username(username)
        videos = db_service.get_videos_by_profile(username, downloaded_only)
        
        return {
            "success": True,
            "username": username,
            "total": len(videos),
            "videos": [
                {
                    "video_id": v.video_id,
                    "title": v.title,
                    "video_url": v.video_url,
                    "view_count": v.view_count,
                    "like_count": v.like_count,
                    "duration": v.duration,
                    "upload_date": v.upload_date.isoformat() if v.upload_date else None,
                    "download_status": v.download_status,
                    "is_downloaded": v.is_downloaded,
                    "local_file_path": v.local_file_path,
                    "downloaded_at": v.downloaded_at.isoformat() if v.downloaded_at else None,
                }
                for v in videos
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get videos for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/videos/{video_id}")
async def get_video(video_id: str):
    """Get detailed information about a specific video"""
    try:
        video = db_service.get_video(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return {
            "success": True,
            "video": {
                "video_id": video.video_id,
                "profile_username": video.profile_username,
                "title": video.title,
                "description": video.description,
                "video_url": video.video_url,
                "view_count": video.view_count,
                "like_count": video.like_count,
                "comment_count": video.comment_count,
                "share_count": video.share_count,
                "duration": video.duration,
                "width": video.width,
                "height": video.height,
                "format": video.format,
                "music_title": video.music_title,
                "music_author": video.music_author,
                "hashtags": video.hashtags,
                "upload_date": video.upload_date.isoformat() if video.upload_date else None,
                "download_status": video.download_status,
                "is_downloaded": video.is_downloaded,
                "local_file_path": video.local_file_path,
                "file_hash": video.file_hash,
                "downloaded_at": video.downloaded_at.isoformat() if video.downloaded_at else None,
                "first_seen": video.first_seen.isoformat() if video.first_seen else None,
            }
        }
    except Exception as e:
        logger.error(f"Failed to get video {video_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# File Download Endpoints
@app.get("/api/downloads")
async def list_downloads():
    """List all downloaded files organized by username"""
    try:
        downloads = {}
        if not DOWNLOADS_DIR.exists():
            return {"downloads": {}, "total_files": 0}
        
        for user_dir in DOWNLOADS_DIR.iterdir():
            if user_dir.is_dir():
                files = []
                for file in user_dir.iterdir():
                    if file.is_file():
                        stat = file.stat()
                        files.append({
                            "filename": file.name,
                            "size": stat.st_size,
                            "size_mb": round(stat.st_size / (1024 * 1024), 2),
                            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "download_url": f"/api/downloads/{user_dir.name}/{file.name}"
                        })
                if files:
                    downloads[user_dir.name] = {
                        "files": files,
                        "count": len(files),
                        "total_size_mb": round(sum(f["size"] for f in files) / (1024 * 1024), 2)
                    }
        
        total_files = sum(d["count"] for d in downloads.values())
        return {
            "downloads": downloads,
            "total_users": len(downloads),
            "total_files": total_files
        }
    except Exception as e:
        logger.error(f"Failed to list downloads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads/{username}")
async def list_user_downloads(username: str):
    """List all downloaded files for a specific username"""
    try:
        user_dir = DOWNLOADS_DIR / username
        if not user_dir.exists():
            raise HTTPException(status_code=404, detail=f"No downloads found for user: {username}")
        
        files = []
        for file in user_dir.iterdir():
            if file.is_file():
                stat = file.stat()
                files.append({
                    "filename": file.name,
                    "size": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "download_url": f"/api/downloads/{username}/{file.name}"
                })
        
        return {
            "username": username,
            "files": files,
            "count": len(files),
            "total_size_mb": round(sum(f["size"] for f in files) / (1024 * 1024), 2)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list downloads for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads/{username}/{filename}")
async def download_file(username: str, filename: str):
    """Download a specific video file"""
    try:
        # Validate username to prevent path traversal
        if not re.match(USERNAME_PATTERN, username):
            raise HTTPException(status_code=400, detail="Invalid username format")
        
        file_path = DOWNLOADS_DIR / username / filename
        
        # Security check: ensure file is within downloads directory
        if not str(file_path.resolve()).startswith(str(DOWNLOADS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Not a file")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="video/mp4"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to download file {username}/{filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", API_PORT))  # Render uses PORT env variable
    
    print(f"🚀 Starting TikTok Bulk Downloader API")
    print(f"📁 Downloads directory: {DOWNLOADS_DIR}")
    print(f"📋 Manifest file: {MANIFEST_FILE}")
    print(f"🌐 API will be available at: http://{API_HOST}:{port}")
    print(f"\n📖 API Documentation: http://localhost:{port}/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Required for Render
        port=port,
        log_level="info"
    )
