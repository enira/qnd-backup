import logging

from flask import request
from flask_restplus import Resource

from api.xen.business import create_schedule, delete_schedule, update_schedule
from api.xen.serializers import schedule
from api.restplus import api

from database.models import Schedule

from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/schedule', description='Operations related to schedules')


@ns.route('/')
class ScheduleCollection(Resource):

    @api.marshal_list_with(pool)
    def get(self):
        """
        Returns list of pools.
        """
        pools = db.session.query(Schedule).all()
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
@api.response(404, 'Schedule not found.')
class ScheduleItem(Resource):

    @api.marshal_with(schedule)
    def get(self, id):
        """
        Returns a pool.
        """
        return db.session.query(Schedule).filter(Pool.id == id).one()
    
    @api.expect(schedule)
    @api.response(204, 'Schedule successfully updated.')
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
        update_schedule(id, data)
        return None, 204

    @api.response(204, 'Schedule successfully deleted.')
    def delete(self, id):
        """
        Deletes a schedule.
        """
        delete_schedule(id)
        return None, 204