"""Configuration for the Alexa Shopping List Flask app."""

import logging
import os
from pathlib import Path

# Amazon URL for UK locale
AMAZON_URL = "https://www.amazon.co.uk"

# Path to the cookie file, relative to the project root
COOKIE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "cookies.json"
)

# Logging level
LOG_LEVEL = "INFO"

# Flask secret key for session management
SECRET_KEY = os.environ.get("SECRET_KEY", "G8gQxm7nHOUCSt3wopR@Rk2rT7lftld^")

# Keep-alive interval in seconds
KEEP_ALIVE_INTERVAL = 60

# --- Derived ---
LOG_LEVEL_INT = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
