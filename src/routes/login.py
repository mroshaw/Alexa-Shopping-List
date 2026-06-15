"""Flask routes for Amazon authentication."""

import asyncio
import logging
import threading

from flask import Blueprint, render_template, redirect, url_for, flash, current_app

from flaskapp import auth

logger = logging.getLogger(__name__)

login_bp = Blueprint("login", __name__)

# Track whether a login flow is currently in progress
_login_in_progress = False


def _run_login_in_thread():
    """Runs the async login flow in a background thread."""
    global _login_in_progress
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(auth.run_login_flow())
        if success:
            logger.info("Background login flow completed successfully.")
        else:
            logger.error("Background login flow failed.")
    except Exception as e:
        logger.exception(f"Exception in background login thread: {e}")
    finally:
        _login_in_progress = False


@login_bp.route("/login")
def login():
    """Shows the login page."""
    return render_template("login.html", login_in_progress=_login_in_progress)


@login_bp.route("/login/start", methods=["POST"])
def start_login():
    """Launches the browser-based Amazon login flow in a background thread."""
    global _login_in_progress

    if _login_in_progress:
        flash("A login is already in progress. Please complete it in the browser window.", "info")
        return redirect(url_for("login.login"))

    _login_in_progress = True
    thread = threading.Thread(target=_run_login_in_thread, daemon=True)
    thread.start()

    flash("A browser window has opened. Please log in to Amazon, then click 'I've logged in' below.", "info")
    return redirect(url_for("login.login"))


@login_bp.route("/login/confirm", methods=["POST"])
def confirm_login():
    """Called by the user after they've logged in to Amazon in the browser."""
    if not _login_in_progress:
        flash("No login is currently in progress. Please start a new login.", "error")
        return redirect(url_for("login.login"))

    success = auth.trigger_login_confirm()
    if success:
        flash("Login confirmed — extracting your session. This may take a moment.", "success")
    else:
        flash("Could not signal login confirmation. Please try again.", "error")

    return redirect(url_for("login.login"))


@login_bp.route("/login/status")
def login_status():
    """Simple endpoint to poll whether login is still in progress."""
    return {"in_progress": _login_in_progress, "has_cookies": auth.cookies_exist()}
