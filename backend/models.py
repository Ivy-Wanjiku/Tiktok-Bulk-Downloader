#!/usr/bin/env python3
"""
Database Models for TikTok Bulk Downloader
SQLAlchemy ORM models for profiles and videos
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, BigInteger, Float, Text, Boolean, Index, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool
from pathlib import Path

Base = declarative_base()


class TikTokProfile(Base):
    """TikTok user profile - Primary entity"""
    __tablename__ = 'tiktok_profiles'
    
    # Primary Key
    username = Column(String(100), primary_key=True, index=True)
    
    # Profile Metadata
    display_name = Column(String(200))
    bio = Column(Text)
    follower_count = Column(BigInteger)
    following_count = Column(BigInteger)
    likes_count = Column(BigInteger)
    video_count = Column(Integer)
    verified = Column(Boolean, default=False)
    
    # Profile URLs
    profile_url = Column(String(500))
    avatar_url = Column(String(500))
    
    # Tracking Information
    first_scraped = Column(DateTime, default=datetime.utcnow)
    last_scraped = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_download = Column(DateTime)
    
    # Download Statistics
    total_videos_found = Column(Integer, default=0)
    total_videos_downloaded = Column(Integer, default=0)
    total_download_fails = Column(Integer, default=0)
    
    # Relationships
    videos = relationship("TikTokVideo", back_populates="profile", cascade="all, delete-orphan")
    download_jobs = relationship("DownloadJob", back_populates="profile", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<TikTokProfile(username='{self.username}', videos={len(self.videos)})>"


class TikTokVideo(Base):
    """TikTok video - Child of Profile"""
    __tablename__ = 'tiktok_videos'
    
    # Primary Key
    video_id = Column(String(100), primary_key=True, index=True)
    
    # Foreign Key to Profile
    profile_username = Column(String(100), ForeignKey('tiktok_profiles.username', ondelete='CASCADE'), nullable=False, index=True)
    
    # Video Metadata
    title = Column(Text)
    description = Column(Text)
    video_url = Column(String(500), nullable=False)
    download_url = Column(String(500))
    
    # Video Statistics
    view_count = Column(BigInteger)
    like_count = Column(BigInteger)
    comment_count = Column(Integer)
    share_count = Column(Integer)
    play_count = Column(BigInteger)
    
    # Video Properties
    duration = Column(Float)  # in seconds
    width = Column(Integer)
    height = Column(Integer)
    format = Column(String(20))
    file_size = Column(BigInteger)
    
    # Content Information
    music_title = Column(String(500))
    music_author = Column(String(200))
    hashtags = Column(Text)  # Comma-separated or JSON
    
    # Upload Information
    upload_date = Column(DateTime)
    create_time = Column(BigInteger)  # Unix timestamp
    
    # Download Information
    is_downloaded = Column(Boolean, default=False)
    download_status = Column(String(50))  # 'pending', 'downloaded', 'failed', 'skipped'
    local_file_path = Column(String(1000))
    file_hash = Column(String(64))  # SHA256 hash
    downloaded_at = Column(DateTime)
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("TikTokProfile", back_populates="videos")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_video_status', 'download_status'),
        Index('idx_video_uploaded', 'upload_date'),
        Index('idx_video_profile_status', 'profile_username', 'download_status'),
        Index('idx_video_hash', 'file_hash'),
    )
    
    def __repr__(self):
        return f"<TikTokVideo(id='{self.video_id}', profile='{self.profile_username}', downloaded={self.is_downloaded})>"


class DownloadJob(Base):
    """Download job tracking"""
    __tablename__ = 'download_jobs'
    
    # Primary Key
    job_id = Column(String(100), primary_key=True, index=True)
    
    # Foreign Key to Profile (optional - jobs can be URL-based)
    profile_username = Column(String(100), ForeignKey('tiktok_profiles.username', ondelete='SET NULL'), index=True)
    
    # Job Information
    job_name = Column(String(200), nullable=False)
    job_type = Column(String(50))  # 'profile', 'urls', 'single'
    status = Column(String(50), default='pending')  # 'pending', 'downloading', 'paused', 'stopped', 'completed', 'failed'
    
    # Statistics
    total_videos = Column(Integer, default=0)
    downloaded = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    skipped = Column(Integer, default=0)
    
    # Paths and Configuration
    download_path = Column(String(1000))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Error Information
    error_message = Column(Text)
    
    # Relationships
    profile = relationship("TikTokProfile", back_populates="download_jobs")
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_job_status', 'status'),
        Index('idx_job_created', 'created_at'),
        Index('idx_job_status_created', 'status', 'created_at'),
    )
    
    def __repr__(self):
        return f"<DownloadJob(id='{self.job_id}', status='{self.status}', downloaded={self.downloaded}/{self.total_videos})>"


# Database initialization
def init_db(db_path: str = None):
    """
    Initialize database and create all tables with thread-safe configuration
    """
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / "tiktok_downloader.db")
    
    # Create engine with thread-safe pooling configuration
    # CRITICAL FIX: Added connection pool limits and thread safety
    from sqlalchemy.pool import QueuePool
    engine = create_engine(
        f'sqlite:///{db_path}',
        echo=False,  # Set to True for SQL query debugging
        poolclass=QueuePool,
        pool_size=1,  # Single connection to prevent concurrent access issues
        max_overflow=0,  # No overflow connections
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={
            'check_same_thread': False,  # Allow SQLite usage across threads
            'timeout': 30  # 30 second timeout for lock acquisition
        }
    )
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """Get a database session"""
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Test database creation
    engine = init_db()
    print(f"✅ Database initialized successfully")
    print(f"📊 Tables created: {', '.join(Base.metadata.tables.keys())}")
