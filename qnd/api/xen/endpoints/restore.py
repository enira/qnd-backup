import logging

from flask import request
from flask_restplus import Resource

#from api.xen.business import submit_restore
from api.xen.serializers import available_backups, restore_rw
from api.restplus import api

from database.models import Backup, Pool, Datastore
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/restore', description='Operations related to restores')

@ns.route('/restore/<int:pool_id>/<int:datastore_id>')
class RestoreCollection(Resource):

    @api.marshal_list_with(available_backups)
    def get(self, pool_id, datastore_id):
        """
        Selects all backups for a pool & datastore.
        """
        backups = db.session.query(Backup).filter(Pool.id == pool_id).filter(Datastore.id == datastore_id).all()
        return backups

@ns.route('/restore/<int:backup>')
class RestoreItem(Resource):

    @api.response(201, 'Pool successfully created.')
    @api.expect(restore_rw)
    def post(self):
        """
        Creates a new pool.
        """
        data = request.json
        create_pool(data)
        return None, 201
