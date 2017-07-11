import psutil
from sys import platform

import copy

from flask import request
from flask_restplus import Resource

from api.xen.serializers import system, messages, stats
from api.restplus import api

from xen.flow import Flow
from xen.types import MessageType

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
                                 "time": task[3],
                                 "message": task[4],
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
        


        # object date

        obj = type('',(object,),{"restore_pass": len(uimessages),
                                 "restore_failed": len(uinotifications),
                                 "backup_pass": len(uitasks),
                                 "backup_failed": uimessages,
                                })()

        return obj
