from flask_restplus import fields
from api.restplus import api

vm = api.model('VM', {
    'name': fields.String(required=True, description='VM name'),
    'uuid': fields.String(required=True, description='VM uuid'),
    'status': fields.String(required=True, description='VM status'),
    'resident': fields.String(required=True, description='VM host resident'),
    'mem_actual': fields.String(required=True, description='VM memory in use'),
    'mem_max': fields.String(required=True, description='VM installed memory'),
    'mem_pct': fields.String(required=True, description='VM memory used in percent'),
})

system = api.model('System', {
    'cpu_load': fields.Integer(readOnly=True, description='CPU load in percent'),
    'cpu_num': fields.Integer(readOnly=True, description='Amount of cores'),
    'cpu_freq': fields.Integer(readOnly=True, description='CPU frequency'),
    'ram_max': fields.Integer(readOnly=True, description='Installed amount of RAM'),
    'ram_used': fields.Integer(readOnly=True, description='RAM used'),
    'ram_pct': fields.Integer(readOnly=True, description='RAM used in percent'),
})


pool = api.model('Pool', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a pool'),
    'name': fields.String(required=True, description='Pool name'),
})

host = api.model('Host', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a host'),
    'username': fields.String(required=True, description='Username being used by the host'),
    'password': fields.String(required=True, description='Password being used by the host (omitted in get requests)'),
    'address': fields.String(required=True, description='Host address'),
    'type': fields.String(required=True, description='Host type (only used internally)'),
    'pool_id': fields.Integer(required=True, description='The unique identifier of the associated pool'),
})


datastore = api.model('Datastore', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a datastore'),
    'name': fields.String(required=True, description='Name being used by the datastore'),
    'username': fields.String(required=True, description='Username being used by the datastore'),
    'password': fields.String(required=True, description='Password being used by the datastore'),
    'host': fields.String(required=True, description='Datastore host'),
    'type': fields.String(required=True, description='Datastore type (Supported values: \'smb\')'),
})


user = api.model('user', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a user'),
    'name': fields.String(required=True, description='The username'),
})

messages_item = api.model('messages_item', {
    'from': fields.String(readOnly=True, description='System submitted'),
    'time': fields.String(required=True, description='Time submitted'),
    'message': fields.String(required=True, description='Message'),
})
notifications_item = api.model('notifications_item', {
    'icon': fields.String(readOnly=True, description='Icon'),
    'message': fields.String(required=True, description='Message'),
})
tasks_item = api.model('tasks_item', {
    'title': fields.String(readOnly=True, description='Title of the task'),
    'percent': fields.String(required=True, description='percent complete'),
})

messages = api.model('messages', {
    'messages': fields.Integer(readOnly=True, description='Amount of messages'),
    'notifications': fields.Integer(readOnly=True, description='Amount of notifications'),
    'tasks': fields.Integer(readOnly=True, description='Amount of tasks'),
    'messages_items': fields.List(fields.Nested(messages_item)),
    'notifications_items': fields.List(fields.Nested(notifications_item)),
    'tasks_items': fields.List(fields.Nested(tasks_item)),
})

task = api.model('Task', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a task'),
    'uuid': fields.String(required=True, description='The uuid being used by the task'),
    'pct1': fields.Integer(required=True, description='Password being used by the host (omitted in get requests)'),
    'pct2': fields.Integer(required=True, description='Host address'),
    'divisor': fields.Integer(required=True, description='Host type (only used internally)'),
    'status': fields.String(required=True, description='The unique identifier of the associated pool'),
    'pool_id': fields.Integer(required=True, description='The unique identifier of the associated pool'),
    'datastore_id': fields.Integer(required=True, description='The unique identifier of the associated pool'),
    'started': fields.DateTime(dt_format='rfc822', required=True, description='The unique identifier of the associated pool'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The unique identifier of the associated pool'),
})

