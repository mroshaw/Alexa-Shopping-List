"""Authentication: opens a browser for manual Amazon login and saves cookies locally."""

import asyncio
import json
import logging
import os
from typing import List, Dict
from pathlib import Path

import nodriver as uc

from . import config

logger = logging.getLogger(__name__)

SIGNIN_URL = f"{config.AMAZON_URL}/"

profile_path = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "nodriver_profile"
)

def save_cookies_to_file(cookies: List[Dict]) -> bool:
    """Saves a list of cookie dicts to the configured cookie file path."""
    cookie_dir = os.path.dirname(config.COOKIE_PATH)
    try:
        os.makedirs(cookie_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Could not create cookie directory '{cookie_dir}': {e}")
        return False

    try:
        with open(config.COOKIE_PATH, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2)
        logger.info(f"Saved {len(cookies)} cookies to {config.COOKIE_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to save cookies to {config.COOKIE_PATH}: {e}", exc_info=True)
        return False


def cookies_exist() -> bool:
    """Returns True if a cookie file already exists on disk."""
    return os.path.exists(config.COOKIE_PATH)


async def run_login_flow() -> bool:
    """
    Opens a browser to the Amazon sign-in page for manual login.
    After login is confirmed, extracts and saves cookies locally.
    Returns True on success, False on failure.
    """
    logger.info("Starting Amazon login flow with nodriver...")
    browser = None

    try:
        # browser = await uc.start()
        browser = await uc.start()

        _ = await browser.get(SIGNIN_URL)
        logger.info(f"Navigated to: {SIGNIN_URL}")

        # Signal to the caller that the browser is open and waiting.
        # The Flask route will have set a session flag before calling this;
        # the confirmation step is handled by a separate /auth/confirm route.
        # We yield here by waiting for an external signal file to appear.
        signal_path = Path(config.COOKIE_PATH).parent / ".login_confirm"

        logger.info("Waiting for login confirmation signal...")
        while not os.path.exists(signal_path):
            await asyncio.sleep(1)

        # Clean up the signal file
        try:
            os.remove(signal_path)
        except OSError:
            pass

        logger.info("Login confirmed. Extracting cookies...")
        raw_cookies = await browser.cookies.get_all(requests_cookie_format=True)

        if not raw_cookies:
            logger.error("No cookies extracted after login confirmation.")
            return False

        logger.info(f"Extracted {len(raw_cookies)} raw cookie objects.")

        serializable_cookies = []
        for cookie in raw_cookies:
            cookie_dict = {
                "name": getattr(cookie, "name", None),
                "value": getattr(cookie, "value", None),
                "domain": getattr(cookie, "domain", None),
                "path": getattr(cookie, "path", None),
                "expires": getattr(cookie, "expires", None),
                "secure": getattr(cookie, "secure", False),
                "httpOnly": getattr(cookie, "httpOnly", False),
            }
            serializable_cookies.append({k: v for k, v in cookie_dict.items() if v is not None})

        logger.info(f"Formatted {len(serializable_cookies)} cookies for saving.")
        return save_cookies_to_file(serializable_cookies)

    except Exception as e:
        logger.exception(f"Unexpected error during login flow: {e}")
        return False
    finally:
        if browser:
            logger.info("Closing browser...")
            try:
                browser.stop()
                logger.info("Browser closed.")
            except Exception as e:
                logger.warning(f"Error closing browser: {e}")


def trigger_login_confirm(data_dir: str | None = None) -> bool:
    """
    Creates the signal file that tells run_login_flow() the user has confirmed login.
    Called from the Flask /auth/confirm route.
    """
    if data_dir is None:
        data_dir = os.path.dirname(config.COOKIE_PATH)
    signal_path = os.path.join(data_dir, ".login_confirm")
    try:
        open(signal_path, "w").close()
        logger.info(f"Login confirmation signal written to {signal_path}")
        return True
    except OSError as e:
        logger.error(f"Could not write login confirmation signal: {e}")
        return False
