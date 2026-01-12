#!/usr/bin/env python3
"""
TikTok Downloader Module
Uses yt-dlp to download TikTok videos
"""

import asyncio
import os
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
import yt_dlp
from tqdm import tqdm
import threading

from db_service import db_service
from config import MAX_RETRY_ATTEMPTS, RETRY_DELAYS

logger = logging.getLogger(__name__)


class TikTokDownloader:
    def __init__(self):
        self.is_stopped = False
        self.is_paused = False
        self.current_job_id = None
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        self.progress_callback: Optional[Callable] = None
        self.downloaded_hashes = set()  # Track downloaded file hashes (bounded to 10000)
        self.db = db_service  # Database service
        logger.info("TikTokDownloader initialized")
        
        self.ydl_opts_base = {
            'format': 'best',
            'outtmpl': '%(id)s.%(ext)s',  # Simple template using only video ID
            'quiet': False,
            'no_warnings': True,  # Suppress warnings including impersonation warnings
            'extract_flat': False,
            'restrictfilenames': True,  # Use only ASCII chars and avoid special characters
            'windowsfilenames': True,   # Restrict to Windows-compatible filenames
            'trim_file_name': 200,       # Limit filename length to 200 characters
            # TikTok-specific options
            'extractor_args': {
                'tiktok': {
                    'api_hostname': 'api22-normal-c-useast2a.tiktokv.com',
                }
            },
            # Add user agent to avoid detection
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.tiktok.com/',
            },
            # Continue on errors for individual videos
            'ignoreerrors': True,
            'no_color': False,
            # Force no playlist and direct download to avoid URL-based filenames
            'noplaylist': True,
        }
    
    def stop_download(self):
        """Stop the current download"""
        self.is_stopped = True
        self.is_paused = False
        self.pause_event.set()  # Unpause if paused
        print("\n🛑 Stop requested - stopping download...")
    
    def pause_download(self):
        """Pause the current download"""
        if not self.is_paused:
            self.is_paused = True
            self.pause_event.clear()
            print("\n⏸️  Download paused")
    
    def resume_download(self):
        """Resume a paused download"""
        if self.is_paused:
            self.is_paused = False
            self.pause_event.set()
            print("\n▶️  Download resumed")
    
    def reset_state(self, job_id: str = None):
        """Reset download state for a new job"""
        self.is_stopped = False
        self.is_paused = False
        self.current_job_id = job_id
        self.pause_event.set()
        
        # Bound the hash set to prevent memory leaks
        if len(self.downloaded_hashes) > 10000:
            logger.warning(f"Hash set exceeded 10000 entries, clearing oldest hashes")
            # Keep only the most recent 5000 hashes
            self.downloaded_hashes = set(list(self.downloaded_hashes)[-5000:])
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def _calculate_file_hash(self, filepath: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {filepath}: {e}")
            return None
    
    def _is_duplicate(self, filepath: str) -> bool:
        """Check if file is a duplicate based on hash"""
        if not os.path.exists(filepath):
            return False
        
        file_hash = self._calculate_file_hash(filepath)
        if file_hash and file_hash in self.downloaded_hashes:
            logger.info(f"Duplicate detected: {filepath}")
            return True
        
        if file_hash:
            self.downloaded_hashes.add(file_hash)
            # Bound the set
            if len(self.downloaded_hashes) > 10000:
                self.downloaded_hashes = set(list(self.downloaded_hashes)[-5000:])
        return False
    
    def check_pause_stop(self):
        """Check if download should pause or stop"""
        # Wait if paused
        self.pause_event.wait()
        # Return True if should stop
        return self.is_stopped
    
    def _download_with_retry(self, ydl, url: str, max_attempts: int = MAX_RETRY_ATTEMPTS) -> tuple[bool, str]:
        """
        Download with exponential backoff retry
        Returns: (success: bool, error_msg: str)
        """
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Download attempt {attempt}/{max_attempts} for {url}")
                ydl.download([url])
                return True, None
            except Exception as e:
                error_msg = str(e)
                
                # Check for rate limiting
                if '429' in error_msg or 'rate limit' in error_msg.lower():
                    logger.warning(f"Rate limited on attempt {attempt}, waiting...")
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    asyncio.sleep(delay)
                    continue
                
                # Check for network errors
                if any(err in error_msg.lower() for err in ['connection', 'timeout', 'network']):
                    if attempt < max_attempts:
                        delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                        logger.warning(f"Network error on attempt {attempt}, retrying in {delay}s: {error_msg}")
                        asyncio.sleep(delay)
                        continue
                
                # Photo/slideshow posts are not recoverable
                if '/photo/' in url or 'Unsupported URL' in error_msg:
                    logger.error(f"Photo/slideshow post not supported: {url}")
                    return False, "TikTok photo/slideshow posts are not supported"
                
                # Other errors - retry if attempts remain
                if attempt < max_attempts:
                    delay = RETRY_DELAYS[min(attempt - 1, len(RETRY_DELAYS) - 1)]
                    logger.warning(f"Error on attempt {attempt}, retrying in {delay}s: {error_msg}")
                    asyncio.sleep(delay)
                else:
                    logger.error(f"Failed after {max_attempts} attempts: {error_msg}")
                    return False, error_msg
        
        return False, f"Failed after {max_attempts} attempts"
    
    async def preview_user_videos(self, username: str) -> Dict:
        """Get video count and info for a user without downloading"""
        print(f"\n🔍 Fetching video information for @{username}")
        
        username = username.lstrip('@')
        user_url = f"https://www.tiktok.com/@{username}"
        
        ydl_opts = self.ydl_opts_base.copy()
        ydl_opts['extract_flat'] = 'in_playlist'  # Don't download, just get metadata
        ydl_opts['quiet'] = True
        
        result = {
            'username': username,
            'total_videos': 0,
            'new_videos': 0,
            'existing_videos': 0,
            'downloaded_videos': 0,
            'videos': [],
            'success': False,
            'error': None,
            'profile_exists': False
        }
        
        try:
            # Check if profile exists in database
            existing_profile = self.db.get_profile(username)
            if existing_profile:
                result['profile_exists'] = True
                result['existing_videos'] = self.db.get_videos_by_profile(username).__len__()
                result['downloaded_videos'] = self.db.get_videos_by_profile(username, downloaded_only=True).__len__()
                logger.info(f"Profile @{username} found in database with {result['existing_videos']} videos ({result['downloaded_videos']} downloaded)")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(user_url, download=False)
                
                if 'entries' in info:
                    videos = list(info['entries'])
                    result['total_videos'] = len(videos)
                    result['success'] = True
                    
                    # Create or update profile in database
                    profile_data = {
                        'profile_url': user_url,
                        'video_count': len(videos),
                        'total_videos_found': len(videos),
                    }
                    
                    # Extract profile info if available
                    if 'uploader' in info:
                        profile_data['display_name'] = info.get('uploader')
                    
                    self.db.create_or_update_profile(username, profile_data)
                    
                    # Get existing video IDs from database
                    existing_video_ids = set()
                    if existing_profile:
                        existing_videos = self.db.get_videos_by_profile(username)
                        existing_video_ids = {v.video_id for v in existing_videos}
                    
                    # Track new videos found
                    new_video_count = 0
                    
                    # Get basic info for each video and save to database
                    for video in videos[:50]:  # Limit to first 50 for preview
                        if video:
                            video_id = video.get('id', 'unknown')
                            video_info = {
                                'id': video_id,
                                'title': video.get('title', 'Untitled'),
                                'url': video.get('url') or video.get('webpage_url', ''),
                                'duration': video.get('duration'),
                                'view_count': video.get('view_count'),
                                'is_new': video_id not in existing_video_ids
                            }
                            result['videos'].append(video_info)
                            
                            # Count new videos
                            if video_id not in existing_video_ids:
                                new_video_count += 1
                            
                            # Save video metadata to database
                            video_data = {
                                'title': video_info['title'],
                                'video_url': video_info['url'],
                                'duration': video_info['duration'],
                                'view_count': video_info['view_count'],
                                'download_status': 'pending',
                                'upload_date': datetime.fromtimestamp(video.get('timestamp', 0)) if video.get('timestamp') else None,
                            }
                            
                            self.db.create_or_update_video(
                                video_id=video_id,
                                profile_username=username,
                                video_data=video_data
                            )
                    
                    result['new_videos'] = new_video_count
                    
                    if result['profile_exists']:
                        if new_video_count > 0:
                            print(f"✅ Found {len(videos)} total videos from @{username} ({new_video_count} new, {result['existing_videos']} existing)")
                            logger.info(f"Discovered {new_video_count} new videos for @{username}")
                        else:
                            print(f"✅ Found {len(videos)} videos from @{username} (no new videos since last check)")
                            logger.info(f"No new videos found for @{username}")
                    else:
                        print(f"✅ Found {len(videos)} videos from @{username} (new profile)")
                        logger.info(f"New profile @{username} added with {len(videos)} videos")
                else:
                    result['error'] = 'No videos found'
        
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error fetching videos: {str(e)}")
            logger.error(f"Error fetching videos for @{username}: {e}")
        
        return result
    
    async def download_user_videos(self, username: str, output_dir: str) -> Dict:
        """
        Download all videos from a TikTok user
        
        Args:
            username: TikTok username (without @)
            output_dir: Directory to save videos
            
        Returns:
            Dict with download statistics
        """
        print(f"\n📥 Downloading videos from @{username}")
        
        # Clean username
        username = username.lstrip('@')
        user_url = f"https://www.tiktok.com/@{username}"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = self.ydl_opts_base.copy()
        # Use video ID only to avoid filename length issues
        ydl_opts['outtmpl'] = str(output_path / '%(id)s.%(ext)s')
        ydl_opts['progress_hooks'] = [self._progress_hook]
        
        result = {
            'total': 0,
            'downloaded': 0,
            'failed': 0,
            'username': username
        }
        
        try:
            # Check database FIRST before fetching from TikTok
            existing_profile = self.db.get_profile(username)
            existing_videos_in_db = {}
            pending_videos_count = 0
            already_downloaded_count = 0
            
            if existing_profile:
                existing_vids = self.db.get_videos_by_profile(username)
                existing_videos_in_db = {v.video_id: v for v in existing_vids}
                already_downloaded_count = len([v for v in existing_vids if v.is_downloaded])
                pending_videos_count = len([v for v in existing_vids if not v.is_downloaded and v.download_status != 'failed'])
                
                logger.info(f"Profile @{username} found in database: {len(existing_videos_in_db)} videos tracked, {already_downloaded_count} downloaded, {pending_videos_count} pending")
                print(f"📊 Profile exists: {len(existing_videos_in_db)} videos tracked, {already_downloaded_count} downloaded")
                
                # If all videos are already downloaded, skip fetching from TikTok entirely
                if already_downloaded_count > 0 and pending_videos_count == 0:
                    print(f"✅ All videos already downloaded! Skipping fetch.")
                    logger.info(f"All {already_downloaded_count} videos already downloaded for @{username}, skipping")
                    result['total'] = already_downloaded_count
                    result['downloaded'] = already_downloaded_count
                    return result
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract user info and video list
                print(f"🔍 Fetching video list for @{username}...")
                logger.info(f"Fetching videos for @{username}")
                
                info = ydl.extract_info(user_url, download=False)
                
                if 'entries' in info:
                    videos = list(info['entries'])
                    result['total'] = len(videos)
                    
                    # Ensure profile exists in database
                    profile_data = {
                        'profile_url': user_url,
                        'video_count': len(videos),
                        'total_videos_found': len(videos)
                    }
                    if 'uploader' in info:
                        profile_data['display_name'] = info.get('uploader')
                    
                    self.db.create_or_update_profile(username, profile_data)
                    
                    # Filter videos to download
                    videos_to_download = []
                    new_videos_count = 0  # Initialize counter
                    for video in videos:
                        video_id = video.get('id', f'unknown_{len(videos_to_download)}')
                        
                        # Check if already downloaded
                        if video_id in existing_videos_in_db:
                            existing_video = existing_videos_in_db[video_id]
                            if existing_video.is_downloaded:
                                print(f"⏭️  Skipping {video_id} - already downloaded")
                                logger.debug(f"Skipping {video_id} - already downloaded")
                                result['downloaded'] += 1  # Count as downloaded
                                continue
                            else:
                                print(f"🔄 Video {video_id} exists but not downloaded, will retry")
                                logger.info(f"Video {video_id} exists but not downloaded, will retry")
                                new_videos_count += 1
                        else:
                            new_videos_count += 1
                        
                        videos_to_download.append(video)
                    
                    if new_videos_count > 0:
                        print(f"✅ Found {len(videos)} total videos ({new_videos_count} new/pending, {already_downloaded_count} already downloaded)")
                        logger.info(f"Will download {new_videos_count} new/pending videos")
                    else:
                        print(f"✅ All {len(videos)} videos already downloaded! Nothing to do.")
                        logger.info(f"All videos for @{username} already downloaded")
                        return result
                    
                    # Download each video that needs downloading
                    for idx, video in enumerate(videos_to_download, 1):
                        # Check for stop/pause
                        if self.check_pause_stop():
                            print("\n🛑 Download stopped by user")
                            break
                        
                        try:
                            # Use webpage_url (clean TikTok URL) to avoid filename length issues
                            # Don't use 'url' as it contains the direct video URL with long parameters
                            video_url = video.get('webpage_url') or f"https://www.tiktok.com/@{username}/video/{video.get('id')}"
                            video_id = video.get('id', f'unknown_{idx}')
                            
                            if not video_url:
                                continue
                            
                            # Save video metadata to database
                            video_data = {
                                'title': video.get('title', 'Untitled'),
                                'description': video.get('description', ''),
                                'video_url': video_url,
                                'download_url': video.get('url'),
                                'view_count': video.get('view_count'),
                                'like_count': video.get('like_count'),
                                'comment_count': video.get('comment_count'),
                                'share_count': video.get('repost_count'),
                                'duration': video.get('duration'),
                                'width': video.get('width'),
                                'height': video.get('height'),
                                'format': video.get('ext', 'mp4'),
                                'upload_date': datetime.fromtimestamp(video.get('timestamp', 0)) if video.get('timestamp') else None,
                                'download_status': 'pending',
                            }
                            self.db.create_or_update_video(video_id, username, video_data)
                            
                            # Check for duplicates
                            ext = video.get('ext', 'mp4')
                            expected_file = output_path / f"{video_id}.{ext}"
                            
                            # Check if video is already downloaded (file exists and in database)
                            if video_id in existing_videos_in_db and existing_videos_in_db[video_id].is_downloaded:
                                print(f"✅ [{idx}/{len(videos_to_download)}] Already Downloaded: {video.get('title', 'Unknown')} (ID: {video_id})")
                                logger.info(f"Video {video_id} already downloaded, skipping")
                                result['downloaded'] += 1
                                continue
                            
                            if expected_file.exists():
                                if self._is_duplicate(str(expected_file)):
                                    print(f"⏭️  [{idx}/{len(videos_to_download)}] Skipping duplicate file: {video_id}")
                                    self.db.mark_video_skipped(video_id)
                                    result['downloaded'] += 1  # Count as downloaded
                                    continue
                            
                            # Determine if new or retry
                            if video_id in existing_videos_in_db:
                                print(f"\n🔄 [{idx}/{len(videos_to_download)}] Retrying: {video.get('title', 'Unknown')} (ID: {video_id})")
                            else:
                                print(f"\n📥 [{idx}/{len(videos_to_download)}] New Download: {video.get('title', 'Unknown')} (ID: {video_id})")
                            
                            # Download with retry
                            success, error_msg = self._download_with_retry(ydl, video_url)
                            
                            if not success:
                                # Don't raise, just log and continue
                                print(f"⚠️  Failed to download video {idx} after retries: {error_msg}")
                                logger.warning(f"Video {video_id} failed after retries: {error_msg}")
                                try:
                                    self.db.mark_video_failed(video_id, error_msg)
                                except:
                                    pass
                                result['failed'] += 1
                                continue
                            
                            # Mark as downloaded in database
                            if expected_file.exists():
                                file_hash = self._calculate_file_hash(str(expected_file))
                                if file_hash:
                                    self.downloaded_hashes.add(file_hash)
                                    self.db.mark_video_downloaded(
                                        video_id=video_id,
                                        file_path=str(expected_file),
                                        file_hash=file_hash
                                    )
                            
                            result['downloaded'] += 1
                            logger.info(f"Successfully downloaded video {video_id}")
                        except Exception as e:
                            error_msg = str(e)
                            print(f"❌ Failed to download video {idx}: {error_msg}")
                            logger.error(f"Download failed for video {idx}: {error_msg}")
                            # Mark as failed in database
                            try:
                                self.db.mark_video_failed(video_id, error_msg)
                            except:
                                pass
                            result['failed'] += 1
                            
                            # Clean up partial downloads
                            try:
                                for part_file in output_path.glob(f"{video_id}*.part"):
                                    part_file.unlink()
                                    logger.info(f"Cleaned up partial file: {part_file}")
                            except Exception as cleanup_error:
                                logger.warning(f"Failed to clean up partial file: {cleanup_error}")
                else:
                    print("⚠️  No videos found")
        
        except Exception as e:
            print(f"❌ Error downloading from @{username}: {str(e)}")
            logger.error(f"Error downloading from @{username}: {e}")
            # Don't mark all as failed - keep the actual counts
            # result['failed'] is already tracking individual failures
        
        print(f"\n✅ Download complete!")
        print(f"   Total: {result['total']}")
        print(f"   Downloaded: {result['downloaded']}")
        print(f"   Failed: {result['failed']}")
        
        return result
    
    async def download_from_urls(self, urls: List[str], output_dir: str, username: str = None) -> Dict:
        """
        Download videos from a list of URLs
        
        Args:
            urls: List of TikTok video URLs
            output_dir: Directory to save videos
            username: Optional username to extract from URLs if not provided
            
        Returns:
            Dict with download statistics
        """
        # Try to extract username from first URL if not provided
        if not username and urls:
            import re
            match = re.search(r'@([\w.]+)', urls[0])
            if match:
                username = match.group(1)
        
        print(f"\n📥 Downloading {len(urls)} videos")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = self.ydl_opts_base.copy()
        # Use video ID only to avoid filename length issues
        ydl_opts['outtmpl'] = str(output_path / '%(id)s.%(ext)s')
        ydl_opts['progress_hooks'] = [self._progress_hook]
        
        result = {
            'total': len(urls),
            'downloaded': 0,
            'failed': 0,
            'skipped': 0
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            for idx, url in enumerate(urls, 1):
                # Check for stop/pause
                if self.check_pause_stop():
                    print("\n🛑 Download stopped by user")
                    break
                
                # Update progress
                if self.progress_callback:
                    await self.progress_callback({
                        'current': idx,
                        'total': len(urls),
                        'downloaded': result['downloaded'],
                        'failed': result['failed'],
                        'skipped': result['skipped']
                    })
                
                try:
                    print(f"\n[{idx}/{len(urls)}] Downloading: {url}")
                    
                    # Check if it's a photo/slideshow URL (not currently supported by yt-dlp)
                    if '/photo/' in url:
                        print(f"⚠️  Warning: TikTok photo/slideshow posts are not currently supported by yt-dlp")
                        print(f"   Only video posts can be downloaded. Please use video URLs instead.")
                        result['failed'] += 1
                        continue
                    
                    # Get expected filename before download
                    info = ydl.extract_info(url, download=False)
                    video_id = info.get('id', 'unknown')
                    ext = info.get('ext', 'mp4')
                    expected_file = output_path / f"{video_id}.{ext}"
                    
                    # Extract username from URL or info
                    profile_username = username
                    if not profile_username:
                        import re
                        match = re.search(r'@([\w.]+)', url)
                        if match:
                            profile_username = match.group(1)
                        elif 'uploader' in info:
                            profile_username = info.get('uploader')
                    
                    # Save video metadata to database
                    if profile_username:
                        video_data = {
                            'title': info.get('title', 'Untitled'),
                            'description': info.get('description', ''),
                            'video_url': url,
                            'download_url': info.get('url'),
                            'view_count': info.get('view_count'),
                            'like_count': info.get('like_count'),
                            'comment_count': info.get('comment_count'),
                            'share_count': info.get('repost_count'),
                            'duration': info.get('duration'),
                            'width': info.get('width'),
                            'height': info.get('height'),
                            'format': ext,
                            'upload_date': datetime.fromtimestamp(info.get('timestamp', 0)) if info.get('timestamp') else None,
                            'download_status': 'pending',
                        }
                        
                        # Ensure profile exists
                        if not self.db.get_profile(profile_username):
                            self.db.create_or_update_profile(profile_username, {
                                'profile_url': f"https://www.tiktok.com/@{profile_username}"
                            })
                        
                        self.db.create_or_update_video(video_id, profile_username, video_data)
                    
                    # Check if already exists and is duplicate
                    if expected_file.exists():
                        if self._is_duplicate(str(expected_file)):
                            print(f"⏭️  Skipping duplicate: {video_id}")
                            if profile_username:
                                self.db.mark_video_skipped(video_id)
                            result['skipped'] += 1
                            continue
                    
                    # Download the video with retry logic
                    success, error_msg = self._download_with_retry(ydl, url)
                    
                    if not success:
                        raise Exception(error_msg)
                    
                    # Add hash to tracking and update database
                    if expected_file.exists():
                        file_hash = self._calculate_file_hash(str(expected_file))
                        if file_hash:
                            self.downloaded_hashes.add(file_hash)
                            if profile_username:
                                self.db.mark_video_downloaded(
                                    video_id=video_id,
                                    file_path=str(expected_file),
                                    file_hash=file_hash
                                )
                    
                    result['downloaded'] += 1
                    logger.info(f"Successfully downloaded video {video_id}")
                except Exception as e:
                    error_msg = str(e)
                    if 'Unsupported URL' in error_msg and '/photo/' in url:
                        print(f"❌ TikTok photo/slideshow posts are not supported. Only video posts can be downloaded.")
                        logger.warning(f"Attempted to download unsupported photo/slideshow: {url}")
                    else:
                        print(f"❌ Failed to download {url}: {error_msg}")
                        logger.error(f"Download failed for {url}: {error_msg}")
                    
                    # Mark as failed in database
                    try:
                        if profile_username and video_id:
                            self.db.mark_video_failed(video_id, error_msg)
                    except:
                        pass
                    
                    result['failed'] += 1
                    
                    # Clean up partial downloads
                    try:
                        for part_file in output_path.glob(f"{video_id}*.part"):
                            part_file.unlink()
                            logger.info(f"Cleaned up partial file: {part_file}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up partial file: {cleanup_error}")
        
        print(f"\n✅ Download complete!")
        print(f"   Total: {result['total']}")
        print(f"   Downloaded: {result['downloaded']}")
        print(f"   Failed: {result['failed']}")
        
        return result
    
    async def download_single_video(self, url: str, output_dir: str) -> bool:
        """Download a single TikTok video"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        ydl_opts = self.ydl_opts_base.copy()
        # Use video ID only to avoid filename length issues
        ydl_opts['outtmpl'] = str(output_path / '%(id)s.%(ext)s')
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True
        except Exception as e:
            print(f"❌ Failed to download {url}: {str(e)}")
            return False
    
    def _progress_hook(self, d):
        """Progress hook for yt-dlp"""
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                print(f"\r⬇️  {percent:.1f}% - {d['_speed_str']} - ETA: {d['_eta_str']}", end='')
        elif d['status'] == 'finished':
            print(f"\n✅ Download complete: {d['filename']}")


# Standalone CLI usage
async def main():
    """CLI interface for the downloader"""
    import argparse
    
    parser = argparse.ArgumentParser(description='TikTok Bulk Downloader')
    parser.add_argument('--username', '-u', help='TikTok username to download from')
    parser.add_argument('--url', help='Single video URL to download')
    parser.add_argument('--urls-file', help='File containing video URLs (one per line)')
    parser.add_argument('--output', '-o', default='downloads', help='Output directory')
    
    args = parser.parse_args()
    
    downloader = TikTokDownloader()
    
    if args.username:
        await downloader.download_user_videos(args.username, args.output)
    elif args.url:
        await downloader.download_single_video(args.url, args.output)
    elif args.urls_file:
        with open(args.urls_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        await downloader.download_from_urls(urls, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
