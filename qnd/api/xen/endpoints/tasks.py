import logging
import os

from flask import request
from flask_restplus import Resource

from api.xen.business import create_task, delete_task, update_task
from api.xen.serializers import task
from api.restplus import api

from database.models import Task
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/task', description='Operations related to tasks')


@ns.route('/')
class TaskCollection(Resource):

    @api.marshal_list_with(task)
    def get(self):
        """
        Returns list of tasks.
        """
        tasks = db.session.query(Task).all()
        return tasks

    @api.response(201, 'Task successfully created.')
    @api.expect(task)
    def post(self):
        """
        Creates a new task.
        """
        data = request.json
        create_task(data)
        return None, 201

    
@ns.route('/<int:id>')
@api.response(404, 'Task not found.')
class TaskItem(Resource):

    @api.marshal_with(task)
    def get(self, id):
        """
        Returns a task.
        """
        return db.session.query(Task).filter(Task.id == id).one()
    
    @api.expect(task)
    @api.response(204, 'Task successfully updated.')
    def put(self, id):
        """
        Updates a task.
        Use this method to change the properties of a task.
        * Send a JSON object with the new name in the request body.
        ```
        {
          "uuid": "New uuid",
          "divisor": "New divisor",
          "status": "New status",
          "datastore_id": "New datastore_id",
          "pool_id": "New pool_id",
        }
        ```
        * Specify the ID of the pool to modify in the request URL path.
        """
        data = request.json
        update_task(id, data)
        return None, 204

    @api.response(204, 'Task successfully deleted.')
    def delete(self, id):
        """
        Deletes a task.
        """
        delete_task(id)
        return None, 204