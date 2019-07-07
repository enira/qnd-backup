import os
from flask import Flask, Blueprint, request, send_from_directory, redirect
from flask_admin import Admin

import settings
import threading

from xen.flow import Flow

# enpoint binding
from api.xen.endpoints.users import ns as xen_users_namespace
from api.xen.endpoints.pools import ns as xen_pools_namespace
from api.xen.endpoints.hosts import ns as xen_hosts_namespace
from api.xen.endpoints.datastores import ns as xen_datastores_namespace
from api.xen.endpoints.tasks import ns as xen_tasks_namespace
from api.xen.endpoints.schedules import ns as xen_schedules_namespace
from api.xen.endpoints.archives import ns as xen_archives_namespace
from api.xen.endpoints.vms import ns as xen_vms_namespace
from api.xen.endpoints.ui import ns as xen_ui_namespace
from api.xen.endpoints.backups import ns as xen_backups_namespace

from api.restplus import api

from database import db
import database

# setting logging
import logging.config
logging.config.fileConfig(os.path.join(os.path.dirname(os.path.realpath(__file__)),'logging.conf'), disable_existing_loggers=False)
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# flask
app = Flask(__name__)
# flask admin
admin = Admin(app, name='qnd', template_mode='bootstrap3')

database.assign(app)

app.secret_key = settings.secret_key()

app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP
app.config['SQLALCHEMY_POOL_SIZE'] = settings.SQLALCHEMY_POOL_SIZE
app.config['SQLALCHEMY_MAX_OVERFLOW'] = settings.SQLALCHEMY_MAX_OVERFLOW
app.config['SESSION_TYPE'] = settings.SESSION_TYPE


db.init_app(app)

blueprint = Blueprint('api', __name__, url_prefix='/api')
api.init_app(blueprint)

api.add_namespace(xen_users_namespace)
api.add_namespace(xen_pools_namespace)
api.add_namespace(xen_hosts_namespace)
api.add_namespace(xen_datastores_namespace)
api.add_namespace(xen_tasks_namespace)
api.add_namespace(xen_vms_namespace)
api.add_namespace(xen_archives_namespace)
api.add_namespace(xen_schedules_namespace)
api.add_namespace(xen_ui_namespace)
api.add_namespace(xen_backups_namespace)

app.register_blueprint(blueprint)

def routes(app):
    """
    Prints all routes known to the application. Only to be used for debugging
    """
    import pprint
    pprint.pprint(list(map(lambda x: repr(x), app.url_map.iter_rules())))

def reset_db():
    database.reset_database(app) 
    database.check_version(app, admin)

def initialize_app():
    """
    Initialize the application
    """
    log.info('Initializing application...')

    # check database version and mirate if needed
    database.check_version(app, admin)

    # cleanup
    Flow.instance().cleanup_start()

    # initialize the scheduler
    Flow.instance().initialize_scheduler()

@app.route('/')
def index():
    """
    Default route, redirects to the gui index.html page
    """
    return redirect('gui/index.html')

@app.route('/gui/<path:path>')
def send_gui(path):
    """
    Handler for GUI component.
    Only used by test, in production overridden by nginx
    """
    return send_from_directory('gui', path)

def main():
    """
    Main running configuration
    """

    log.info('>>>>> Starting server <<<<<')
    try:
        # run flask
        app.run(port=8080, host='0.0.0.0', debug=settings.FLASK_DEBUG, use_reloader=False)
    except:
        log.error('That \'s an uncaught error.')

# initialize application
initialize_app()

if __name__ == "__main__":
    main()


