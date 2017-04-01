import app
from app import application
import logging.config

log = logging.getLogger(__name__)

if __name__ == "__main__":
    """
    Main running configuration
    """
    app.initialize_app()

    log.info('>>>>> Starting server ....')
    application.run()