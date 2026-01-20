import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from logging.handlers import RotatingFileHandler

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DOWNLOADS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 3000))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Security Configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080,http://0.0.0.0:8080").split(",")
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
API_KEY = os.getenv("API_KEY", None)

# Database Configuration
DB_PATH = BASE_DIR / "tiktok_downloader.db"

# TikTok Download Settings
TIKTOK_DOWNLOAD_QUALITY = "best"
MAX_CONCURRENT_DOWNLOADS = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", 3))
DOWNLOAD_TIMEOUT = 300  # seconds
JOB_TIMEOUT_HOURS = int(os.getenv("JOB_TIMEOUT_HOURS", 2))
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAYS = [5, 15, 45]  # seconds

# Manifest file location (legacy)
MANIFEST_FILE = BASE_DIR / "manifest.json"

# Allowed video formats
ALLOWED_FORMATS = ["mp4", "webm", "mov"]

# Input validation
MAX_USERNAME_LENGTH = 50
MAX_URL_LENGTH = 2000
USERNAME_PATTERN = r'^[a-zA-Z0-9._]+$'

# Logging Configuration
def setup_logging():
    """Configure structured logging with file rotation"""
    log_file = LOGS_DIR / "tiktok_downloader.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10MB max, keep 5 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if ENVIRONMENT == "development" else logging.WARNING)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    return root_logger

# Initialize logging
logger = setup_logging()
