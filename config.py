"""Environment variable loading and constants."""
import os

from dotenv import load_dotenv

load_dotenv()

FANTASYPROS_API_KEY = os.environ.get("FANTASYPROS_API_KEY", "")
FANTASYPROS_BASE_URL = "https://api.fantasypros.com/public/v2/json"

EMAIL_PROVIDER_API_KEY = os.environ.get("EMAIL_PROVIDER_API_KEY", "")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

DB_PATH = os.environ.get("DB_PATH", "ff_digest.db")

SPORT = "nfl"
SEASON = os.environ.get("SEASON", "2025")
SCORING = os.environ.get("SCORING", "PPR")
POSITIONS = ["QB", "RB", "WR", "TE", "K", "DST"]
