import app
from app import application
import logging.config

log = logging.getLogger(__name__)

if __name__ == "__main__":
    """
    Reset database data

    select datid, usename, application_name,query  from pg_stat_activity ;

    """
    app.reset_db()
    exit()
 