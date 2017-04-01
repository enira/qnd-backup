import logging.config

import os
from flask import Flask, Blueprint, request, send_from_directory, redirect
import settings
import threading

from xen.flow import Flow

from api.xen.endpoints.users import ns as xen_users_namespace
from api.xen.endpoints.pools import ns as xen_pools_namespace
from api.xen.endpoints.hosts import ns as xen_hosts_namespace
from api.xen.endpoints.datastores import ns as xen_datastores_namespace
from api.xen.endpoints.tasks import ns as xen_tasks_namespace
#from api.xen.endpoints.schedules import ns as xen_schedules_namespace
#from api.xen.endpoints.archives import ns as xen_archives_namespace
from api.xen.endpoints.vms import ns as xen_vms_namespace
from api.xen.endpoints.ui import ns as xen_ui_namespace

from api.restplus import api

from database import db
import database

application = Flask(__name__)
logging.config.fileConfig(os.path.join(os.path.dirname(os.path.realpath(__file__)),'logging.conf'))
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

def configure_app(flask_app):
    # flask_app.config['SERVER_NAME'] = settings.FLASK_SERVER_NAME
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = settings.SQLALCHEMY_DATABASE_URI
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP

def routes(app):
    """
    Prints all routes known to the application. Only to be used for debugging
    """
    import pprint
    pprint.pprint(list(map(lambda x: repr(x), app.url_map.iter_rules())))

def initialize_app(flask_app):
    log.error('Initializing application...')
    """
    initialize the application
    """
    """
    TODO
    if not os.path.exists('uuid'):

        key = str(uuid.uuid4())

        file = open('uuid','w')
        file.write(key)
        file.close()
    else:
        file = open('uuid','r')
        key = file.read()
        file.close()
    """

    configure_app(flask_app)

    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)

    api.add_namespace(xen_users_namespace)
    api.add_namespace(xen_pools_namespace)
    api.add_namespace(xen_hosts_namespace)
    api.add_namespace(xen_datastores_namespace)
    api.add_namespace(xen_tasks_namespace)
    api.add_namespace(xen_vms_namespace)
    api.add_namespace(xen_ui_namespace)

    flask_app.register_blueprint(blueprint)

    db.init_app(flask_app)

    # if there is no database, create one
    if not os.path.exists('db.sqlite'):
        database.reset_database(flask_app) 

    # check database version and mirate if needed
    database.check_version(flask_app)


@application.route('/gui/<path:path>')
def send_js(path):
    """
    Hendler for GUI component
    """
    return send_from_directory('gui', path)

@application.route('/')
def hello():
    """
    Default route, redirects to the gui index.html page
    """
    return redirect('gui/index.html')

def main():
    print os.path.dirname(os.path.realpath(__file__))

    """
    Main running configuration
    """
    initialize_app(application)

    # start a background thread
    threading.Timer(1, Flow.instance().run).start()

    log.info('>>>>> Starting server <<<<<')
    try:
        # run flask
        application.run(port=8080, host='0.0.0.0', debug=settings.FLASK_DEBUG, use_reloader=False)
    except:
        log.error('That \'s an uncaught error.')

if __name__ == "__main__":
    main()


