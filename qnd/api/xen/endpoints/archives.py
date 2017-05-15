import logging

from flask import request
from flask_restplus import Resource

from api.xen.business import create_archive, delete_archive, update_archive
from api.xen.serializers import archive, archive_ro, archive_rw
from api.restplus import api

from database.models import Archive
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/archive', description='Operations related to archives')

@ns.route('/')
class ArchiveCollection(Resource):

    @api.marshal_list_with(archive_ro)
    def get(self):
        """
        Returns list of archives.
        """
        pools = db.session.query(Archive).all()
        return pools

    @api.response(201, 'Archive successfully created.')
    @api.expect(archive_rw)
    def post(self):
        """
        Creates a new archive.
        Use this method to change the properties of an archive.
        * Send a JSON object with the new properties in the request body.
        ```
        {
          "name": "Archive name",
          "source_id": "Source datastore",
          "target_id": "Target datastore",
          "encryption_key": "Archive encryption key",
          "retention": "Retention copies. If source datastore has more backups available than this value. Archive it.",
          "incremental": "0 = no, 1 = yes (currently unimplemented)",
        }
        ```
        """
        data = request.json
        create_archive(data)
        return None, 201

    
@ns.route('/<int:id>')
@api.response(404, 'Archive not found.')
class ArchiveItem(Resource):

    @api.marshal_with(archive_ro)
    def get(self, id):
        """
        Returns an archive.
        """
        return db.session.query(Archive).filter(Archive.id == id).one()
    
    @api.expect(archive_rw)
    @api.response(204, 'Archive successfully updated.')
    def put(self, id):
        """
        Updates an archive.
        Use this method to change the properties of an archive.
        * Send a JSON object with the new properties in the request body.
        ```
        {
          "name": "Archive name",
          "source_id": "Source datastore",
          "target_id": "Target datastore",
          "encryption_key": "Archive encryption key",
          "retention": "Retention copies. If source datastore has more backups available than this value. Archive it.",
          "incremental": "0 = no, 1 = yes (currently unimplemented)",
        }
        ```
        * Specify the ID of the pool to modify in the request URL path.
        """
        data = request.json
        update_archive(id, data)
        return None, 204

    @api.response(204, 'Archive successfully deleted.')
    def delete(self, id):
        """
        Deletes an archive.
        """
        delete_archive(id)
        return None, 204