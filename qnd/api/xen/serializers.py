from flask_restplus import fields
from api.restplus import api

vm_full = api.model('VMFull', {
    'name': fields.String(required=True, description='VM name'),
    'uuid': fields.String(required=True, description='VM uuid'),
    'status': fields.String(required=True, description='VM status'),
    'resident': fields.String(required=True, description='VM host resident'),
    'resident_uuid': fields.String(required=True, description='VM host resident uuid'),
    'mem': fields.String(required=True, description='VM memory'),
    'cpu': fields.String(required=True, description='CPUs'),
    'disk_used': fields.String(required=True, description='Disk usage on disk'),
    'disk_virtual': fields.String(required=True, description='Virtual allocated size on disk'),
})

vm = api.model('VM', {
    'name': fields.String(required=True, description='VM name'),
    'uuid': fields.String(required=True, description='VM uuid'),
    'status': fields.String(required=True, description='VM status'),
})

system = api.model('System', {
    'cpu_load': fields.Integer(readOnly=True, description='CPU load (in percent)'),
    'cpu_num': fields.Integer(readOnly=True, description='Amount of cores'),
    'cpu_freq': fields.Integer(readOnly=True, description='CPU frequency (in MHz)'),
    'ram_max': fields.Integer(readOnly=True, description='Installed amount of RAM (in MB)'),
    'ram_used': fields.Integer(readOnly=True, description='RAM used (in MB)'),
    'ram_pct': fields.Integer(readOnly=True, description='RAM used (in percent)'),
})


pool = api.model('Pool', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a pool'),
    'name': fields.String(required=True, description='Pool name'),
})

host = api.model('Host', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a host'),
    'username': fields.String(required=True, description='Username being used by the host'),
    'password': fields.String(required=True, description='Password being used by the host'),
    'address': fields.String(required=True, description='Host address'),
    'type': fields.String(required=True, description='Host type (only used internally)'),
    'pool_id': fields.Integer(required=True, description='The unique identifier of the associated pool'),
})

datastore = api.model('Datastore', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a datastore'),
    'name': fields.String(required=True, description='Name being used by the datastore'),
    'username': fields.String(required=True, description='Username being used by the datastore'),
    'password': fields.String(required=True, description='Password being used by the datastore'),
    'host': fields.String(required=True, description='Datastore host address (ip or hostname)'),
    'type': fields.String(required=True, description='Datastore type (Supported values: \'smb\')'),
})

datastore_safe = api.model('Datastore_Safe', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a datastore'),
    'name': fields.String(required=True, description='Name being used by the datastore'),
    'host': fields.String(required=True, description='Datastore host address (ip or hostname)'),
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
    'percent': fields.String(required=True, description='Percent complete'),
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
    'pct1': fields.Integer(required=True, description='Percent complete of task 1'),
    'pct2': fields.Integer(required=True, description='Percent complete of task 2'),
    'divisor': fields.Integer(required=True, description='Division of percentage compared against task 1 & task 2'),
    'status': fields.String(required=True, description='The status of the task'),
    'pool_id': fields.Integer(required=True, description='The associated pool id'),
    'datastore_id': fields.Integer(required=True, description='The associated datastore id'),
    'started': fields.DateTime(dt_format='rfc822', required=True, description='The time the task ahs been started'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has ended'),
})

archive = api.model('Archive', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of an archive'),
    'name': fields.String(required=True, description='The given display name of an archive'),
    'source_id': fields.Integer(required=True, description='The associated datastore id of the source'),
    'target_id': fields.Integer(required=True, description='The associated datastore id of the target'),
    'encryption_key': fields.String(required=True, description='The encryption key used for encrypting the archived backups'),
    'retention': fields.Integer(required=True, description='The retention versions policy (versions to keep)'),
    'incremental': fields.Integer(required=True, description='Incremental policy (0=no, 1=yes)'),
})


schedule = api.model('Schedule', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a schedule'),
    'name': fields.String(required=True, description='The given display name of a schedule'),
    'minute': fields.String(required=True, description='Cron: minute'),
    'hour': fields.String(required=True, description='Cron: hour'),
    'day': fields.String(required=True, description='Cron: day'),
    'month': fields.String(required=True, description='Cron: month'),
    'week': fields.String(required=True, description='Cron: week'),
    'uuid': fields.String(required=True, description='VM UUID'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'pool_id': fields.Integer(required=True, description='The pool id'),
})

schedule_rw = api.model('ScheduleUpdate', {
    'name': fields.String(required=True, description='The given display name of a schedule'),
    'minute': fields.String(required=True, description='Cron: minute'),
    'hour': fields.String(required=True, description='Cron: hour'),
    'day': fields.String(required=True, description='Cron: day'),
    'month': fields.String(required=True, description='Cron: month'),
    'week': fields.String(required=True, description='Cron: week'),
    'uuid': fields.String(required=True, description='VM UUID'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'pool_id': fields.Integer(required=True, description='The pool id'),
})

schedule_ro = api.model('ScheduleRead', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a schedule'),
    'name': fields.String(required=True, description='The given display name of a schedule'),
    'minute': fields.String(required=True, description='Cron: minute'),
    'hour': fields.String(required=True, description='Cron: hour'),
    'day': fields.String(required=True, description='Cron: day'),
    'month': fields.String(required=True, description='Cron: month'),
    'week': fields.String(required=True, description='Cron: week'),
    'uuid': fields.String(required=True, description='VM UUID'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'datastore': fields.Nested(datastore_safe),
    'pool_id': fields.Integer(required=True, description='The pool id'),
    'pool': fields.Nested(pool),
})

