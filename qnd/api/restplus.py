import logging
import traceback

from flask_restplus import Api
import settings
from sqlalchemy.orm.exc import NoResultFound

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

api = Api(version='alpha-1-fix', title='Quick \'n Dirty XenServer Backup', description='Quick \'n Dirty XenServer Backup API')

@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not settings.FLASK_DEBUG:
        return {'message': message}, 500


@api.errorhandler(NoResultFound)
def database_not_found_error_handler(e):
    log.warning(traceback.format_exc())
    return {'message': 'A database result was required but none was found.'}, 404