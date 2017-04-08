import logging
import psutil
from sys import platform

import copy

from flask import request
from flask_restplus import Resource

from api.xen.serializers import system, messages
from api.restplus import api

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
        # dummy information to implement

        dummy_message = type('',(object,),{"from": "Dummy System",
                                 "time": "Now",
                                 "message": "Test Message",
                                })()
        dummy_notification1 = type('',(object,),{"icon": "fa fa-users text-aqua",
                                 "message": "Message 1",
                                })()
        dummy_notification2 = type('',(object,),{"icon": "fa fa-shopping-cart text-green",
                                 "message": "Message 2",
                                })()
        dummy_notification3 = type('',(object,),{"icon": "fa fa-users text-red",
                                 "message": "Message 3",
                                })()
        dummy_task1 = type('',(object,),{"title": "Task 1",
                                 "percent": "60",
                                })()
        dummy_task2 = type('',(object,),{"title": "Task 2",
                                 "percent": "20",
                                })()
        dummy_messages = [copy.deepcopy(dummy_message), 
                          copy.deepcopy(dummy_message), 
                          copy.deepcopy(dummy_message), 
                          copy.deepcopy(dummy_message), 
                          copy.deepcopy(dummy_message)]
        dummy_notifications = [dummy_notification1, dummy_notification2, dummy_notification3]
        dummy_tasks = [dummy_task1, dummy_task2]

        index = 0
        for d in dummy_messages:
            index = index + 1
            d.message = 'Test Message' + str(index)

        obj = type('',(object,),{"messages": 5,
                                 "notifications": 3,
                                 "tasks": 2,
                                 "messages_items": dummy_messages,
                                 "notifications_items": dummy_notifications,
                                 "tasks_items": dummy_tasks,
                                })()

        return obj
