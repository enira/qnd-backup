import logging

from flask import request
from flask_restplus import Resource

from api.xen.business import create_datastore, delete_datastore, update_datastore
from api.xen.serializers import datastore
from api.restplus import api

from database.models import Datastore
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/datastore', description='Operations related to datastores')

@ns.route('/')
class DatastoreCollection(Resource):

    @api.marshal_list_with(datastore)
    def get(self):
        """
        Returns list of all datastores.
        """
        datastores = db.session.query(Datastore).all()
        return datastores

    @api.response(201, 'Datastore successfully created.')
    @api.expect(datastore)
    def post(self):
        """
        Creates a new datastore.
        """
        data = request.json
        create_datastore(data)
        return None, 201

    
@ns.route('/<int:id>')
@api.response(404, 'Datastore not found.')
class DatastoreItem(Resource):

    @api.marshal_with(datastore)
    def get(self, id):
        """
        Returns a datastore.
        """
        return db.session.query(Datastore).filter(Datastore.id == id).one()
    
    @api.expect(datastore)
    @api.response(204, 'Datastore successfully updated.')
    def put(self, id):
        """
        Updates a datastore.
        Use this method to change the properties of a datastore.
        * Send a JSON object with the new name in the request body.
        ```
        {
          "name": "New datastore name",
          "username": "New datastore username",
          "password": "New datastore password",
          "host": "New datastore host",
          "type": "New datastore type"
        }
        ```
        * Specify the ID of the datastore to modify in the request URL path.
        """
        data = request.json
        update_datastore(id, data)
        return None, 204

    @api.response(204, 'Datastore successfully deleted.')
    def delete(self, id):
        """
        Deletes a datastore.
        """
        delete_datastore(id)
        return None, 204