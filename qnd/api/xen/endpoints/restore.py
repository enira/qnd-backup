import logging

from flask import request
from flask_restplus import Resource

from api.xen.business import submit_restore
from api.xen.serializers import restore
from api.restplus import api

from database.models import Backup
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/restore', description='Operations related to restores')

@ns.route('/restore/<int:pool>/<int:datastore>')
class RestoreItem(Resource):

    @api.response(201, 'Pool successfully created.')
    @api.expect(backup)
    def post(self):
        """
        Selects all backups for a pool & datastore.
        """

        backups = db.session.query(Backup).filter(Pool.id == id).one()

        backup = Backup(task_id=task.id, 
                        metafile=meta_name, 
                        backupfile=backup_name, 
                        comment='Backup created at :' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        session.add(backup)

        data = request.json
        create_pool(data)

        return backups

@ns.route('/restore/<int:backup>')
class RestoreItem(Resource):

    @api.response(201, 'Pool successfully created.')
    @api.expect(pool)
    def post(self):
        """
        Creates a new pool.
        """
        data = request.json
        create_pool(data)
        return None, 201
