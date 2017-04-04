from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

import logging.config

db = SQLAlchemy()

VERSION = '2'

"""
    DB VERSIONS:
    ------------
    1       alpha-1(-fix)
    2       alpha-2

"""

def reset_database(app):
    """
    Resets the database
    """
    log = logging.getLogger(__name__)

    from database.models import User, Pool, Host, Datastore, Task, Schedule, Setting
    log.info('Creating database')

    # drop everything
    db.drop_all(app=app)

    # create again
    db.create_all(app=app)

def check_version(app):
    """
    Reads the version from the database and checks if the database needs to be updated
    """
    log = logging.getLogger(__name__)

    from database.models import Setting

    db.app = app
    # check version
    try:
        dbversion = db.session.query(Setting).filter(Setting.key == 'dbversion').one()
    except NoResultFound as e:
        # error no results
        dbversion = None
    except:
        # this is a call to create the database
        reset_database(app)
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

        # database migrations 

        # from alpha-1 to alpha-2: unsupported due to a lot of db changes and no use of alpha-1 (alpha-1 = demo version) 
        if int(VERSION) >= 2 and int(dbversion.value) == 1:
            log.error('Database version 1 is deprecated, no upgrade possible!')
            print 'Database version 1 is deprecated, no upgrade possible!'
            exit()


    

