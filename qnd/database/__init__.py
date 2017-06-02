from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound

import logging.config

db = SQLAlchemy()

VERSION = '4'

"""
    DB VERSIONS:
    ------------
    1       alpha-1(-fix)           deprecated: no upgrade possible (alpha)
    2       alpha-2                 deprecated: no upgrade possible (alpha)
    3       alpha-3                 deprecated: no upgrade possible (alpha)
    4       alpha-4                 current

"""

def assign(app):
    """
    Assign app to db context
    """
    db.app = app

def reset_database(app):
    """
    Resets the database
    """
    log = logging.getLogger(__name__)

    from database.models import User, Pool, Host, Datastore, BackupTask, ArchiveTask, RestoreTask, Backup, Archive, Schedule, Setting
    log.info('Creating database')

    # drop everything
    db.reflect(app=app)
    db.drop_all(app=app)

    # create again
    db.create_all(app=app)

def check_version(app):
    """
    Reads the version from the database and checks if the database needs to be updated
    """
    log = logging.getLogger(__name__)

    from database.models import Setting
    
    session = db.session

    # check version
    try:
        dbversion = session.query(Setting).filter(Setting.key == 'dbversion').one()
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

        session.add(dbversion)
        session.commit()
    
    log.info('Running database version: '  + dbversion.value)

    session.close()

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

        # alpha-1 & alpha-2: unsupported by this version. 
        if int(dbversion.value) < 3:
            log.error('Database version 1 & 2 are deprecated, no upgrade possible!')
            print 'Database version 1 & 2 are deprecated, no upgrade possible!'
            exit()


    

