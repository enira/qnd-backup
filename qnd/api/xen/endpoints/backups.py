from flask import request
from flask_restplus import Resource

from api.xen.serializers import available_backups, host_sr
from api.xen.business import delete_backup
from api.restplus import api

from database.models import Backup, Host
from database import db
from xen.flow import Flow

import logging.config
log = logging.getLogger(__name__)

ns = api.namespace('xen/backups', description='Operations related to backups')

@ns.route('/<int:pool_id>/<int:datastore_id>')
class BackupsCollection(Resource):

    @api.marshal_list_with(available_backups)
    def get(self, pool_id, datastore_id):
        """
        Selects all backups for a pool & datastore.
        """
        backups = db.session.query(Backup).filter(Backup.pool_id == pool_id, Backup.datastore_id == datastore_id).order_by(Backup.created.asc()).all()
        return backups

@ns.route('/sr/<int:pool_id>/<int:host_id>')
class LocalStorageCollection(Resource):

    @api.marshal_list_with(host_sr)
    def get(self, pool_id, host_id):
        """
        Gets all SR available for a host (based on host id).
        """

        host = db.session.query(Host).filter(Host.id == host_id).one()
        srs = Flow.instance().get_sr(pool_id, host.address)

        wrapped = []
        if srs == None:
            return wrapped

        for sr in srs:
            # create object
            obj = type('',(object,),{"name": sr[1]["name_label"], 
                                     "sr": sr[0].split(':')[1],
                                    })()
           
            wrapped.append(obj)
        return wrapped

@ns.route('/<int:id>')
@api.response(404, 'Backup not found.')
class BackupItem(Resource):

    @api.marshal_with(available_backups)
    def get(self, id):
        """
        Returns a backup.
        """
        return db.session.query(Backup).filter(Backup.id == id).one()

    @api.response(204, 'Backup successfully deleted.')
    def delete(self, id):
        """
        Deletes a backup.
        """
        delete_backup(id)
        return None, 204