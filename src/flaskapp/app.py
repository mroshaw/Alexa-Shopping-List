"""Flask application factory for the Alexa Shopping List web app."""

import logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from . import config
from routes.shopping import shopping_bp
from routes.login import login_bp
from . import alexa_api, auth

logging.basicConfig(
    level=config.LOG_LEVEL_INT,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if config.LOG_LEVEL_INT > logging.DEBUG:
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("nodriver").setLevel(logging.WARNING)


def perform_keep_alive():
    """Periodically fetches the shopping list to keep the Amazon session alive."""
    if not auth.cookies_exist():
        logger.info("Keep-alive skipped: no cookie file found.")
        return
    items = alexa_api.get_shopping_list_items()
    if items is not None:
        logger.info(f"Keep-alive successful: {len(items)} items fetched.")
    else:
        logger.warning("Keep-alive failed: could not retrieve shopping list. Re-authentication may be needed.")


def create_app() -> Flask:
    """Creates and configures the Flask application."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = config.SECRET_KEY

    # Register blueprints
    app.register_blueprint(shopping_bp)
    app.register_blueprint(login_bp)

    # Start keep-alive background scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        perform_keep_alive,
        trigger="interval",
        seconds=config.KEEP_ALIVE_INTERVAL,
        id="keep_alive_job",
    )

    scheduler.start()
    logger.info(f"Keep-alive scheduler started (interval: {config.KEEP_ALIVE_INTERVAL}s).")

    return app
