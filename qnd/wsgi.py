import app
from app import application
import logging.config

log = logging.getLogger(__name__)

if __name__ == "__main__":
    """
    Main running configuration for service
    """
    app.initialize_app()

    # start the server
    log.info('>>>>> Starting server ....')
    application.run()