import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Telegram Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
REQUIRED_CHANNELS = [int(ch) for ch in os.getenv('REQUIRED_CHANNELS', '').split(',') if ch.strip()]

# Log configuration on startup
logger.info(f"Config loaded - ADMIN_ID: {ADMIN_ID}, BOT_TOKEN: {'Set' if BOT_TOKEN else 'Missing'}")

if ADMIN_ID == 0:
    logger.warning("⚠️ ADMIN_ID is 0! Check your .env file!")

# Database Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'job_bot')
}

# Redis Configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': int(os.getenv('REDIS_DB', 0))
}

# Scraping Configuration
SCRAPE_INTERVAL_HOURS = int(os.getenv('SCRAPE_INTERVAL_HOURS', 12))
NOTIFICATION_TIMES = os.getenv('NOTIFICATION_TIMES', '09:00,18:00').split(',')

# Job Types and Domains
JOB_TYPES = ['Internship', 'Job']
WORK_MODES = ['Remote', 'Onsite', 'Hybrid']
DOMAINS = [
    'Python Developer',
    'Web Development',
    'Data Science',
    'Machine Learning',
    'Android Development',
    'iOS Development',
    'DevOps',
    'Digital Marketing',
    'UI/UX Design',
    'Content Writing'
]

# Cache TTL (seconds)
CACHE_TTL = SCRAPE_INTERVAL_HOURS * 3600
