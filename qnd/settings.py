
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