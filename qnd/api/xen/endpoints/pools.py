import logging

from flask import request
from flask_restplus import Resource

from api.xen.business import create_pool, delete_pool, update_pool
from api.xen.serializers import pool
from api.restplus import api

from database.models import Pool
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/pool', description='Operations related to pools')


@ns.route('/')
class PoolCollection(Resource):

    @api.marshal_list_with(pool)
    def get(self):
        """
        Returns list of pools.
        """
        pools = db.session.query(Pool).all()
        return pools

    @api.response(201, 'Pool successfully created.')
    @api.expect(pool)
    def post(self):
        """
        Creates a new pool.
        """
        data = request.json
        create_pool(data)
        return None, 201

    
@ns.route('/<int:id>')
@api.response(404, 'Pool not found.')
class PoolItem(Resource):

    @api.marshal_with(pool)
    def get(self, id):
        """
        Returns a pool.
        """
        return db.session.query(Pool).filter(Pool.id == id).one()
    
    @api.expect(pool)
    @api.response(204, 'Pool successfully updated.')
    def put(self, id):
        """
        Updates a pool.
        Use this method to change the name of a pool.
        * Send a JSON object with the new name in the request body.
        ```
        {
          "name": "New pool name"
        }
        ```
        * Specify the ID of the pool to modify in the request URL path.
        """
        data = request.json
        update_pool(id, data)
        return None, 204

    @api.response(204, 'Pool successfully deleted.')
    def delete(self, id):
        """
        Deletes a pool.
        """
        delete_pool(id)
        return None, 204