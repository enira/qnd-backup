import logging

from flask import request
from flask_restplus import Resource

from api.xen.business import create_host, delete_host, update_host
from api.xen.serializers import host
from api.restplus import api

from database.models import Host

from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/host', description='Operations related to hosts')


@ns.route('/')
class HostCollection(Resource):

    @api.marshal_list_with(host)
    def get(self):
        """
        Returns list of hosts.
        """
        hosts = db.session.query(Host).all()
        return hosts

    @api.response(201, 'Host successfully created.')
    @api.expect(host)
    def post(self):
        """
        Creates a new host.
        """
        data = request.json
        create_host(data)
        return None, 201

    
@ns.route('/<int:id>')
@api.response(404, 'Host not found.')
class HostItem(Resource):

    @api.marshal_with(host)
    def get(self, id):
        """
        Returns a host.
        """
        return db.session.query(Host).filter(Host.id == id).one()
    
    @api.expect(host)
    @api.response(204, 'Host successfully updated.')
    def put(self, id):
        """
        Updates a host.
        Use this method to change the properties of a host.
        * Send a JSON object with the new name in the request body.
        ```
        {
          "username": "New host username",
          "password": "New host password",
          "address": "New host address",
          "type": "New host type",
          "pool_id": "Pool id"
        }
        ```
        * Specify the ID of the pool to modify in the request URL path.
        """
        data = request.json
        update_host(id, data)
        return None, 204

    @api.response(204, 'Host successfully deleted.')
    def delete(self, id):
        """
        Deletes a pool.
        """
        delete_host(id)
        return None, 204