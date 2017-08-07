import os.path
import uuid

# Flask settings
FLASK_SERVER_NAME = '0.0.0.0:80'
FLASK_DEBUG = True  # Do not use debug mode in production
use_reloader=False

# Flask-Restplus settings
RESTPLUS_SWAGGER_UI_DOC_EXPANSION = 'list'
RESTPLUS_VALIDATE = True
RESTPLUS_MASK_SWAGGER = True
RESTPLUS_ERROR_404_HELP = False

# SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = 'postgres://qnd:quickndirty@localhost/qnd'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_POOL_SIZE = 5
SQLALCHEMY_MAX_OVERFLOW	= 0

SESSION_TYPE = 'filesystem'

def secret_key():
    cwd = os.path.dirname(os.path.realpath(__file__))

    if os.path.isfile(os.path.join(cwd,'.session')):
        file = open(os.path.join(cwd,'.session'), "r")
        return file.read() 
    else:
        file = open(os.path.join(cwd,'.session'),"w")
        key = str(uuid.uuid4())
        file.write(key)
        file.close()
        return key