import logging
import os

from flask import request
from flask_restplus import Resource

from api.xen.business import create_backup_task, delete_backup_task, create_restore_task, delete_restore_task
from api.xen.serializers import backuptask, backuptask_rw, archivetask, restoretask, restoretask_rw
from api.restplus import api

from database.models import BackupTask, ArchiveTask, RestoreTask
from database import db

log = logging.getLogger(__name__)

ns = api.namespace('xen/task', description='Operations related to tasks')

@ns.route('/backup/')
class TaskCollection(Resource):

    @api.marshal_list_with(backuptask)
    def get(self):
        """
        Returns list of all backup tasks.
        """
        tasks = db.session.query(BackupTask).all()
        return tasks

    @api.response(201, 'BackupTask successfully created.')
    @api.expect(backuptask_rw)
    def post(self):
        """
        Creates a new backup task.
        """
        data = request.json
        create_backup_task(data)
        return None, 201

    
@ns.route('/backup/<int:id>')
@api.response(404, 'BackupTask not found.')
class TaskItem(Resource):

    @api.marshal_with(backuptask)
    def get(self, id):
        """
        Returns a backup task.
        """
        return db.session.query(BackupTask).filter(BackupTask.id == id).one()

    @api.response(204, 'BackupTask successfully deleted.')
    def delete(self, id):
        """
        Deletes a task.
        """
        delete_backup_task(id)
        return None, 204


@ns.route('/restore/')
class TaskCollection(Resource):

    @api.marshal_list_with(restoretask)
    def get(self):
        """
        Returns list of all restore tasks.
        """
        tasks = db.session.query(RestoreTask).all()
        return tasks

    @api.response(201, 'RestoreTask successfully created.')
    @api.expect(restoretask_rw)
    def post(self):
        """
        Creates a new restore task.
        """
        data = request.json
        create_restore_task(data)
        return None, 201

    
@ns.route('/restore/<int:id>')
@api.response(404, 'RestoreTask not found.')
class TaskItem(Resource):

    @api.marshal_with(restoretask)
    def get(self, id):
        """
        Returns a restore task.
        """
        return db.session.query(RestoreTask).filter(RestoreTask.id == id).one()

    @api.response(204, 'RestoreTask successfully deleted.')
    def delete(self, id):
        """
        Deletes a restore task.
        """
        delete_restore_task(id)
        return None, 204

@ns.route('/archive/')
class TaskCollection(Resource):

    @api.marshal_list_with(archivetask)
    def get(self):
        """
        Returns list of archive tasks.
        """
        tasks = db.session.query(ArchiveTask).all()
        return tasks
    
@ns.route('/archive/<int:id>')
@api.response(404, 'ArchiveTask not found.')
class TaskItem(Resource):

    @api.marshal_with(archivetask)
    def get(self, id):
        """
        Returns an archive task.
        """
        return db.session.query(ArchiveTask).filter(ArchiveTask.id == id).one()
    