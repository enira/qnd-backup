import app
from app import application
import logging.config

log = logging.getLogger(__name__)

if __name__ == "__main__":
    """
    Reset the database data. In case you want to reset all data.
    Can be runned with 'python reset_db.py'
    """
    app.reset_db()
    exit()
 