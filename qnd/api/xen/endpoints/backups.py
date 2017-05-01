import logging

from flask import request
from flask_restplus import Resource

from api.xen.serializers import available_backups
from api.restplus import api

from database.models import Backup
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/backups', description='Operations related to backups')

@ns.route('/<int:pool_id>/<int:datastore_id>')
class BackupsCollection(Resource):

    @api.marshal_list_with(available_backups)
    def get(self, pool_id, datastore_id):
        """
        Selects all backups for a pool & datastore.
        """
        backups = db.session.query(Backup).filter(Backup.pool_id == pool_id, Backup.datastore_id == datastore_id).all()
        return backups
