from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

import logging.config

db = SQLAlchemy()

VERSION = '1'

"""
    DB VERSIONS:
    ------------
    1       alpha-1

"""

def reset_database(app):
    log = logging.getLogger(__name__)

    # todo Archive
    from database.models import User, Pool, Host, Datastore, Task, Schedule, Setting
    log.info('Creating database')

    db.drop_all(app=app)
    db.create_all(app=app)

def check_version(app):
    log = logging.getLogger(__name__)

    from database.models import Setting

    db.app = app
    # check version
    try:
        dbversion = Setting().query.filter(Setting.key == 'dbversion').one()
    except NoResultFound as e:
        dbversion = None

    # no database version to be found, let's create one
    if dbversion == None:
        log.info('No database version found, setting version to ' + VERSION)
        dbversion = Setting(key='dbversion', value=VERSION)

        db.session.add(dbversion)
        db.session.commit()
    
    log.info('Running database version: '  + dbversion.value)

    # checking database version
    if dbversion.value == VERSION:
        log.info('Database is up to date.')
    elif dbversion.value > VERSION:
        # hmmm, the database is newer than the application. I can't do anything with that
        log.info('Unrecoverable error: database version is higher than the application can use.')
        exit()
    else:
        # database is not up to date
        log.info('Database migration started.')

        # No database migrations yet
    

