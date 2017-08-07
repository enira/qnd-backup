

from database import db
import database

from flask import Flask

import settings

# flask
app = Flask(__name__)

database.assign(app)

app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP
app.config['SQLALCHEMY_POOL_SIZE'] = settings.SQLALCHEMY_POOL_SIZE
app.config['SQLALCHEMY_MAX_OVERFLOW'] = settings.SQLALCHEMY_MAX_OVERFLOW

db.init_app(app)

if __name__ == "__main__":
    """
    Reset the database data. In case you want to reset all data.
    Can be runned with 'python reset_db.py'
    """
    database.reset_database(app) 
    database.check_version(app, None)
    exit()
 