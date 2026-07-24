import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file if present
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Steam API Settings
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "878B66DB9CC7971C204DC107EC4EABB8")

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "gamecheck")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")

# Directory & File Paths
APPS_FILE = os.path.join(BASE_DIR, "steam_apps.json")
RAW_DATA_DIR = os.path.join(BASE_DIR, "app_rawdata")
SQL_DIR = os.path.join(BASE_DIR, "new_sql_files")
SQL_OUTPUT_FILE = os.path.join(SQL_DIR, "new_games_update.sql")
LOG_FILE = os.path.join(BASE_DIR, "update_log.txt")

# Pipeline Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 10000))
RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", 1.5))
