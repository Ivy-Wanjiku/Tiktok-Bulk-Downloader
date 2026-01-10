#!/usr/bin/env python3
"""
Database Service Layer
Handles all database operations for profiles, videos, and jobs
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict
from contextlib import contextmanager
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import desc, func

from models import TikTokProfile, TikTokVideo, DownloadJob, init_db

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service layer for database operations"""
    
    def __init__(self, db_path: str = None):
        self.engine = init_db(db_path)
        self.SessionFactory = sessionmaker(bind=self.engine)
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope with automatic cleanup"""
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    # ==================== Profile Operations ====================
    
    def create_or_update_profile(self, username: str, profile_data: Dict) -> TikTokProfile:
        """Create or update a TikTok profile"""
        with self.session_scope() as session:
            profile = session.query(TikTokProfile).filter_by(username=username).first()
            
            if profile:
                # Update existing profile
                for key, value in profile_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                profile.last_scraped = datetime.utcnow()
                logger.info(f"Updated profile: {username}")
            else:
                # Create new profile
                profile = TikTokProfile(
                    username=username,
                    first_scraped=datetime.utcnow(),
                    **profile_data
                )
                session.add(profile)
                logger.info(f"Created new profile: {username}")
            
            session.flush()
            session.refresh(profile)
            return profile
    
    def get_profile(self, username: str) -> Optional[TikTokProfile]:
        """Get a profile by username"""
        with self.session_scope() as session:
            profile = session.query(TikTokProfile).filter_by(username=username).first()
            if profile:
                session.expunge(profile)
            return profile
    
    def get_all_profiles(self) -> List[TikTokProfile]:
        """Get all profiles"""
        with self.session_scope() as session:
            profiles = session.query(TikTokProfile).order_by(desc(TikTokProfile.last_scraped)).all()
            for profile in profiles:
                session.expunge(profile)
            return profiles
    
    def update_profile_stats(self, username: str, stats: Dict):
        """Update profile download statistics"""
        with self.session_scope() as session:
            profile = session.query(TikTokProfile).filter_by(username=username).first()
            if profile:
                for key, value in stats.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                logger.info(f"Updated stats for profile: {username}")
    
    # ==================== Video Operations ====================
    
    def create_or_update_video(self, video_id: str, profile_username: str, video_data: Dict) -> TikTokVideo:
        """Create or update a video"""
        with self.session_scope() as session:
            video = session.query(TikTokVideo).filter_by(video_id=video_id).first()
            
            if video:
                # Update existing video
                for key, value in video_data.items():
                    if hasattr(video, key):
                        setattr(video, key, value)
                video.last_updated = datetime.utcnow()
                logger.info(f"Updated video: {video_id}")
            else:
                # Create new video
                video = TikTokVideo(
                    video_id=video_id,
                    profile_username=profile_username,
                    first_seen=datetime.utcnow(),
                    **video_data
                )
                session.add(video)
                logger.info(f"Created new video: {video_id} for profile {profile_username}")
            
            session.flush()
            session.refresh(video)
            session.expunge(video)
            return video
    
    def get_video(self, video_id: str) -> Optional[TikTokVideo]:
        """Get a video by ID"""
        with self.session_scope() as session:
            video = session.query(TikTokVideo).filter_by(video_id=video_id).first()
            if video:
                session.expunge(video)
            return video
    
    def get_videos_by_profile(self, username: str, downloaded_only: bool = False) -> List[TikTokVideo]:
        """Get all videos for a profile"""
        with self.session_scope() as session:
            query = session.query(TikTokVideo).filter_by(profile_username=username)
            if downloaded_only:
                query = query.filter_by(is_downloaded=True)
            videos = query.order_by(desc(TikTokVideo.upload_date)).all()
            for video in videos:
                session.expunge(video)
            return videos
    
    def mark_video_downloaded(self, video_id: str, file_path: str, file_hash: str):
        """Mark a video as downloaded"""
        with self.session_scope() as session:
            video = session.query(TikTokVideo).filter_by(video_id=video_id).first()
            if video:
                video.is_downloaded = True
                video.download_status = 'downloaded'
                video.local_file_path = file_path
                video.file_hash = file_hash
                video.downloaded_at = datetime.utcnow()
                logger.info(f"Marked video {video_id} as downloaded")
    
    def mark_video_failed(self, video_id: str, error: str = None):
        """Mark a video download as failed"""
        with self.session_scope() as session:
            video = session.query(TikTokVideo).filter_by(video_id=video_id).first()
            if video:
                video.download_status = 'failed'
                if error:
                    video.description = f"Error: {error}"
                logger.warning(f"Marked video {video_id} as failed: {error}")
    
    def mark_video_skipped(self, video_id: str):
        """Mark a video as skipped (duplicate)"""
        with self.session_scope() as session:
            video = session.query(TikTokVideo).filter_by(video_id=video_id).first()
            if video:
                video.download_status = 'skipped'
                logger.info(f"Marked video {video_id} as skipped (duplicate)")
    
    def check_video_exists(self, video_id: str) -> bool:
        """Check if a video exists in database"""
        with self.session_scope() as session:
            return session.query(TikTokVideo).filter_by(video_id=video_id).count() > 0
    
    def get_video_by_hash(self, file_hash: str) -> Optional[TikTokVideo]:
        """Find video by file hash (for duplicate detection)"""
        with self.session_scope() as session:
            video = session.query(TikTokVideo).filter_by(file_hash=file_hash).first()
            if video:
                session.expunge(video)
            return video
    
    # ==================== Job Operations ====================
    
    def create_job(self, job_id: str, job_data: Dict) -> DownloadJob:
        """Create a new download job"""
        with self.session_scope() as session:
            job = DownloadJob(
                job_id=job_id,
                created_at=datetime.utcnow(),
                **job_data
            )
            session.add(job)
            session.flush()
            session.refresh(job)
            session.expunge(job)
            logger.info(f"Created job: {job_id}")
            return job
    
    def get_job(self, job_id: str) -> Optional[DownloadJob]:
        """Get a job by ID"""
        with self.session_scope() as session:
            job = session.query(DownloadJob).filter_by(job_id=job_id).first()
            if job:
                session.expunge(job)
            return job
    
    def get_all_jobs(self) -> List[DownloadJob]:
        """Get all jobs"""
        with self.session_scope() as session:
            jobs = session.query(DownloadJob).order_by(desc(DownloadJob.created_at)).all()
            for job in jobs:
                session.expunge(job)
            return jobs
    
    def update_job(self, job_id: str, updates: Dict):
        """Update a job"""
        with self.session_scope() as session:
            job = session.query(DownloadJob).filter_by(job_id=job_id).first()
            if job:
                for key, value in updates.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                job.updated_at = datetime.utcnow()
                logger.debug(f"Updated job {job_id}: {updates}")
    
    def delete_job(self, job_id: str):
        """Delete a job"""
        with self.session_scope() as session:
            job = session.query(DownloadJob).filter_by(job_id=job_id).first()
            if job:
                session.delete(job)
                logger.info(f"Deleted job: {job_id}")
    
    # ==================== Statistics ====================
    
    def get_statistics(self) -> Dict:
        """Get overall statistics"""
        with self.session_scope() as session:
            return {
                'total_profiles': session.query(TikTokProfile).count(),
                'total_videos': session.query(TikTokVideo).count(),
                'downloaded_videos': session.query(TikTokVideo).filter_by(is_downloaded=True).count(),
                'total_jobs': session.query(DownloadJob).count(),
                'active_jobs': session.query(DownloadJob).filter(
                    DownloadJob.status.in_(['pending', 'downloading', 'paused'])
                ).count()
            }
    
    def get_profile_statistics(self, username: str) -> Dict:
        """Get statistics for a specific profile"""
        with self.session_scope() as session:
            profile = session.query(TikTokProfile).filter_by(username=username).first()
            if not profile:
                return None
            
            videos = session.query(TikTokVideo).filter_by(profile_username=username)
            
            return {
                'username': username,
                'total_videos': videos.count(),
                'downloaded': videos.filter_by(is_downloaded=True).count(),
                'failed': videos.filter_by(download_status='failed').count(),
                'pending': videos.filter_by(download_status='pending').count(),
                'total_views': session.query(func.sum(TikTokVideo.view_count)).filter_by(
                    profile_username=username
                ).scalar() or 0,
                'first_scraped': profile.first_scraped,
                'last_scraped': profile.last_scraped
            }


    def cleanup_stale_jobs(self, timeout_hours: int = 2):
        """Clean up jobs that have been stuck in downloading state"""
        from datetime import timedelta
        
        with self.session_scope() as session:
            cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)
            stale_jobs = session.query(DownloadJob).filter(
                DownloadJob.status == 'downloading',
                DownloadJob.created_at < cutoff_time
            ).all()
            
            for job in stale_jobs:
                job.status = 'timeout'
                job.error_message = f'Job exceeded {timeout_hours} hour timeout'
                logger.warning(f"Cleaned up stale job: {job.job_id}")
            
            return len(stale_jobs)


# Global instance
db_service = DatabaseService()
