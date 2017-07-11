from flask import request
from flask_restplus import Resource

from api.xen.business import create_schedule, delete_schedule, update_schedule
from api.xen.serializers import schedule, schedule_ro, schedule_rw
from api.restplus import api

from database.models import Schedule
from database import db

import logging.config
log = logging.getLogger(__name__)

ns = api.namespace('xen/schedule', description='Operations related to schedules')


@ns.route('/')
class ScheduleCollection(Resource):

    @api.marshal_list_with(schedule_ro)
    def get(self):
        """
        Returns list of schedules.
        """
        schedules = db.session.query(Schedule).all()
        return schedules

    @api.response(201, 'Schedule successfully created.')
    @api.expect(schedule_rw)
    def post(self):
        """
        Creates a new schedule.
        Use this method to create a new schedule.
        * Send a JSON object with the properties in the request body.
        ```
        {
          "name": "The given display name of a schedule",
          "minute": "Cron: minute",
          "hour": "Cron: hour",
          "day": "Cron: day",
          "month": "Cron: month",
          "week": "Cron: week",
          "uuid": "VM UUID",
          "datastore_id": "The datastore id",
          "pool_id": "The pool id",
        }
        ```
        """
        data = request.json
        create_schedule(data)
        return None, 201

    
@ns.route('/<int:id>')
@api.response(404, 'Schedule not found.')
class ScheduleItem(Resource):

    @api.marshal_with(schedule_ro)
    def get(self, id):
        """
        Returns a schedule.
        """
        return db.session.query(Schedule).filter(Schedule.id == id).one()
    
    @api.expect(schedule_rw)
    @api.response(204, 'Schedule successfully updated.')
    def put(self, id):
        """
        Updates a schedule.
        Use this method to change the properties of a schedule.
        * Send a JSON object with the properties in the request body.
        ```
        {
          "name": "The given display name of a schedule",
          "minute": "Cron: minute",
          "hour": "Cron: hour",
          "day": "Cron: day",
          "month": "Cron: month",
          "week": "Cron: week",
          "uuid": "VM UUID",
          "datastore_id": "The datastore id",
          "pool_id": "The pool id",
        }
        ```
        * Specify the ID of the schedule to modify in the request URL path.
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