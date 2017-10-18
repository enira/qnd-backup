import psutil
from sys import platform

import copy

from flask import request
from flask_restplus import Resource

from api.xen.serializers import system, messages, stats
from api.restplus import api

from xen.flow import Flow
from xen.types import MessageType

from database.models import BackupTask, ArchiveTask, RestoreTask
from database import db

import logging.config
log = logging.getLogger(__name__)

ns = api.namespace('xen/ui', description='Operations related to ui')
    
@ns.route('/system')
@api.response(404, 'Statistics not found.')
class SystemItem(Resource):

    @api.marshal_with(system)
    def get(self):
        """
        Returns System stats.
        """
        cpu_max = None
        if 'linux' in platform:
            # for Linux VMs the code cannot find the maximum CPU speed :(
            cpu_max = 0
        else:
            cpu_max = psutil.cpu_freq().max

        obj = type('',(object,),{"cpu_load": psutil.cpu_percent() ,
                                 "ram_pct": psutil.virtual_memory().percent ,
                                 "ram_used": psutil.virtual_memory().used,
                                 "ram_max": psutil.virtual_memory().total,
                                 "cpu_num": psutil.cpu_count(logical=False),
                                 "cpu_freq": cpu_max,
                                })()

        return obj

@ns.route('/messages')
@api.response(404, 'Messages not found.')
class MessageItem(Resource):

    @api.marshal_with(messages)
    def get(self):
        """
        Returns Messages.
        """

        tasks = Flow.instance().messages

        # Gather all tasks
        uitasks = []
        uimessages = []
        uinotifications = []
        for task in tasks:
            if task[1] == MessageType.TASK:
                uitask = type('',(object,),{"title": task[2],
                                     "percent": task[3],
                                    })()

                uitasks.append(uitask)
            if task[1] == MessageType.MESSAGE:
                uimessage = type('',(object,),{"from": task[2],
                                 "time": task[4],
                                 "message": task[3],
                                })()

                uimessages.append(uimessage)
            if task[1] == MessageType.NOTIFICATION:
                uinotification = type('',(object,),{"icon": "fa fa-" + task[2] + " text" + task[3],
                                 "message": task[4],
                                })()

                uinotifications.append(uinotification)


        obj = type('',(object,),{"messages": len(uimessages),
                                 "notifications": len(uinotifications),
                                 "tasks": len(uitasks),
                                 "messages_items": uimessages,
                                 "notifications_items": uinotifications,
                                 "tasks_items": uitasks,
                                })()

        return obj

@ns.route('/stats/<string:start>/<string:end>')
@api.response(404, 'Statistics not found.')
class SystemItem(Resource):

    @api.marshal_with(stats)
    def get(self, start, end):
        """
        Returns backup and restore stats.
        """

        backups = db.session.query(BackupTask).filter(BackupTask.started >= start + ' 00:00:01').filter(BackupTask.started <= end + ' 23:59:59').all()
        restores = db.session.query(RestoreTask).filter(RestoreTask.started >= start  + ' 00:00:01').filter(RestoreTask.started <= end + ' 23:59:59').all()
        # TODO
        #archives = db.session.query(ArchiveTask).filter(ArchiveTask.started >= start).filter(ArchiveTask.started <= end).all()
        
        restore_pass = []
        restore_failed  = []
        backup_pass = []
        backup_failed = []

        for backup in backups:
            try:
                if backup.status == "backup_done":
                    if backup.backupname == None:
                        str = 'VM: ' + backup.backup.vmname + '. ' + backup.backup.comment
                    else:
                        str = 'VM: ' + backup.backup.vmname + ' snapshot: ' + backup.backupname +'. ' + backup.backup.comment
                    bo = type('',(object,),{"object": str, "date": backup.ended})()
                    backup_pass.append(bo)
                else:
                    if backup.status == "backup_pending":
                        # if pending backup: don't count it towards failed
                        pass
                    else:
                        bo = type('',(object,),{"object": 'Failed: '+ backup.backupname +'. ', "date": backup.started})()
                        backup_failed.append(bo)
            except Exception as e:
                log.error(repr(e))

        for restore in restores:
            try:
                if backup.status == "restore_done":
                    # TODO
                    bo = type('',(object,),{"object": restore.backupname, "date": restore.started})()
                    restore_pass.append(ro)
                else:
                    # TODO
                    bo = type('',(object,),{"object": restore.backupname, "date": restore.started})()
                    restore_failed.append(ro)
            except Exception as e:
                log.error(repr(e))

        # TODO
        #for archive in archives:

        


        # object date

        obj = type('',(object,),{"restore_pass": restore_pass,
                                 "restore_failed": restore_failed,
                                 "backup_pass": backup_pass,
                                 "backup_failed": backup_failed,
                                })()

        return obj
