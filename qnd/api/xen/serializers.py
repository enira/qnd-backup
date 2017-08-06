from flask_restplus import fields
from api.restplus import api

vm_full = api.model('vm_full', {
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

vm = api.model('vm', {
    'name': fields.String(required=True, description='VM name'),
    'uuid': fields.String(required=True, description='VM uuid'),
    'status': fields.String(required=True, description='VM status'),
})

system = api.model('system', {
    'cpu_load': fields.Integer(readOnly=True, description='CPU load (in percent)'),
    'cpu_num': fields.Integer(readOnly=True, description='Amount of cores'),
    'cpu_freq': fields.Integer(readOnly=True, description='CPU frequency (in MHz)'),
    'ram_max': fields.Integer(readOnly=True, description='Installed amount of RAM (in MB)'),
    'ram_used': fields.Integer(readOnly=True, description='RAM used (in MB)'),
    'ram_pct': fields.Integer(readOnly=True, description='RAM used (in percent)'),
})

substat = api.model('substat', {
    'object': fields.String(required=True, description='Object'),
    'date': fields.String(required=True, description='Date'),
})

stats = api.model('stats', {
    'restore_pass': fields.Nested(substat),
    'restore_failed': fields.Nested(substat),
    'backup_pass': fields.Nested(substat),
    'backup_failed': fields.Nested(substat),
})


pool = api.model('pool', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a pool'),
    'name': fields.String(required=True, description='Pool name'),
})

pool_rw = api.model('pool_rw', {
    'name': fields.String(required=True, description='Pool name'),
})

host = api.model('host', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a host'),
    'username': fields.String(required=True, description='Username being used by the host'),
    'password': fields.String(required=True, description='Password being used by the host'),
    'address': fields.String(required=True, description='Host address'),
    'type': fields.String(required=True, description='Host type (only used internally)'),
    'pool_id': fields.Integer(required=True, description='The unique identifier of the associated pool'),
})

host_rw = api.model('host_rw', {
    'username': fields.String(required=True, description='Username being used by the host'),
    'password': fields.String(required=True, description='Password being used by the host'),
    'address': fields.String(required=True, description='Host address'),
    'type': fields.String(required=True, description='Host type (only used internally)'),
    'pool_id': fields.Integer(required=True, description='The unique identifier of the associated pool'),
})

host_test = api.model('host_test', {
    'username': fields.String(required=True, description='Username being used by the host'),
    'password': fields.String(required=True, description='Password being used by the host'),
    'address': fields.String(required=True, description='Host address'),
})

datastore = api.model('datastore', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a datastore'),
    'name': fields.String(required=True, description='Name being used by the datastore'),
    'username': fields.String(required=True, description='Username being used by the datastore'),
    'password': fields.String(required=True, description='Password being used by the datastore'),
    'host': fields.String(required=True, description='Datastore host address (ip or hostname)'),
    'type': fields.String(required=True, description='Datastore type (Supported values: \'smb\' & \'smb-archive\')'),
})

datastore_rw = api.model('datastore_rw', {
    'name': fields.String(required=True, description='Name being used by the datastore'),
    'username': fields.String(required=True, description='Username being used by the datastore'),
    'password': fields.String(required=True, description='Password being used by the datastore'),
    'host': fields.String(required=True, description='Datastore host address (ip or hostname)'),
    'type': fields.String(required=True, description='Datastore type (Supported values: \'smb\' & \'smb-archive\')'),
})

datastore_test = api.model('datastore_test', {
    'username': fields.String(required=True, description='Username being used by the datastore'),
    'password': fields.String(required=True, description='Password being used by the datastore'),
    'host': fields.String(required=True, description='Datastore host address (ip or hostname)'),
    'type': fields.String(required=True, description='Datastore type (Supported values: \'smb\' & \'smb-archive\')'),
})

datastore_safe = api.model('datastore_safe', {
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

archive = api.model('archive', {
    'name': fields.String(required=True, description='The given display name of an archive'),
    'source_id': fields.Integer(required=True, description='The associated datastore id of the source'),
    'target_id': fields.Integer(required=True, description='The associated datastore id of the target'),
    'encryption_key': fields.String(required=True, description='The encryption key used for encrypting the archived backups'),
    'retention': fields.Integer(required=True, description='The retention versions policy (versions to keep)'),
    'incremental': fields.Integer(required=True, description='Incremental policy (0=no, 1=yes)'),
})

archive_rw = api.model('archive_rw', {
    'name': fields.String(required=True, description='The given display name of an archive'),
    'source_id': fields.Integer(required=True, description='The associated datastore id of the source'),
    'target_id': fields.Integer(required=True, description='The associated datastore id of the target'),
    'encryption_key': fields.String(required=True, description='The encryption key used for encrypting the archived backups'),
    'retention': fields.Integer(required=True, description='The retention versions policy (versions to keep)'),
    'incremental': fields.Integer(required=True, description='Incremental policy (0=no, 1=yes)'),
})

archive_ro = api.model('archive_ro', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of an archive'),
    'name': fields.String(required=True, description='The given display name of an archive'),
    'source_id': fields.Integer(required=True, description='The associated datastore id of the source'),
    'source': fields.Nested(datastore_safe),
    'target_id': fields.Integer(required=True, description='The associated datastore id of the target'),
    'target': fields.Nested(datastore_safe),
    'retention': fields.Integer(required=True, description='The retention versions policy (versions to keep)'),
    'incremental': fields.Integer(required=True, description='Incremental policy (0=no, 1=yes)'),
})


schedule = api.model('schedule', {
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
    'advanced': fields.Integer(required=True, description='Simple or advanced (0=simple, 1=advanced)'),
})

schedule_rw = api.model('schedule_rw', {
    'name': fields.String(required=True, description='The given display name of a schedule'),
    'minute': fields.String(required=True, description='Cron: minute'),
    'hour': fields.String(required=True, description='Cron: hour'),
    'day': fields.String(required=True, description='Cron: day'),
    'month': fields.String(required=True, description='Cron: month'),
    'week': fields.String(required=True, description='Cron: week'),
    'uuid': fields.String(required=True, description='VM UUID'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'pool_id': fields.Integer(required=True, description='The pool id'),
    'advanced': fields.Integer(required=True, description='Simple or advanced (0=simple, 1=advanced)'),
})

schedule_ro = api.model('schedule_ro', {
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
    'advanced': fields.Integer(required=True, description='Simple or advanced (0=simple, 1=advanced)'),
})

backup_safe = api.model('backup_safe', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a backup'),
    'metafile': fields.String(required=True, description='The metafile name'),
    'backupfile': fields.String(required=True, description='The backupfile name'),
    'comment': fields.String(required=True, description='The comment of the backup'),
    'uuid': fields.String(required=True, description='VM UUID'),
    'vmname': fields.String(required=True, description='VM Name of backed up VM'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'datastore': fields.Nested(datastore_safe),
    'pool_id': fields.Integer(required=True, description='The pool id'),
    'pool': fields.Nested(pool),
})


backuptask = api.model('backuptask', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a backup task'),
    'schedule_id': fields.Integer(required=True, description='The associated schedule id'),
    'snapshotname': fields.String(required=True, description='The snapshot name'),

    'pool_id': fields.Integer(required=True, description='The pool id'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'uuid': fields.String(required=True, description='VM UUID'),

    'backup_id': fields.Integer(required=True, description='The backup id'),
    'backup': fields.Nested(backup_safe),

    'started': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has been started'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has ended'),
    'pct1': fields.Integer(required=True, description='Percent complete of task 1'),
    'pct2': fields.Integer(required=True, description='Percent complete of task 2'),
    'divisor': fields.Integer(required=True, description='Division of percentage compared against task 1 & task 2'),
    'status': fields.String(required=True, description='The status of the task'),
})

backuptask_rw = api.model('backuptask_rw', {
    'pool_id': fields.Integer(required=True, description='The pool id'),
    'datastore_id': fields.Integer(required=True, description='The datastore id'),
    'uuid': fields.String(required=True, description='VM UUID'),
    'started': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has been started'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has ended'),
    'pct1': fields.Integer(required=True, description='Percent complete of task 1'),
    'pct2': fields.Integer(required=True, description='Percent complete of task 2'),
    'divisor': fields.Integer(required=True, description='Division of percentage compared against task 1 & task 2'),
    'status': fields.String(required=True, description='The status of the task'),
})

archivetask = api.model('archivetask', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a task'),

    'backup_id': fields.Integer(required=True, description='The backup id'),
    'backup': fields.Nested(backup_safe),

    'archive_id': fields.Integer(required=True, description='The archive id'),
    'archive': fields.Nested(archive_ro),

    'started': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has been started'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has ended'),
    'pct1': fields.Integer(required=True, description='Percent complete of task 1'),
    'pct2': fields.Integer(required=True, description='Percent complete of task 2'),
    'divisor': fields.Integer(required=True, description='Division of percentage compared against task 1 & task 2'),
    'status': fields.String(required=True, description='The status of the task'),
})

restoretask = api.model('restoretask', {
    'id': fields.Integer(readOnly=True, description='The unique identifier of a task'),
    'backupname': fields.String(required=True, description='The backup name'),

    'backup_id': fields.Integer(required=True, description='The backup id'),
    'backup': fields.Nested(backup_safe),

    'host_id': fields.Integer(required=True, description='The host id'),

    'sr': fields.String(required=True, description='The software repository (SR) where to place the VM'),

    'started': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has been started'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has ended'),
    'pct1': fields.Integer(required=True, description='Percent complete of task 1'),
    'pct2': fields.Integer(required=True, description='Percent complete of task 2'),
    'divisor': fields.Integer(required=True, description='Division of percentage compared against task 1 & task 2'),
    'status': fields.String(required=True, description='The status of the task'),
})

restoretask_rw = api.model('restoretask_rw', {
    'backupname': fields.String(required=True, description='The backup name'),
    'backup_id': fields.Integer(required=True, description='The backup id'),
    'host_id': fields.Integer(required=True, description='The host id'),
    'sr': fields.String(required=True, description='The software repository (SR) where to place the VM'),
    'started': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has been started'),
    'ended': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has ended'),
    'pct1': fields.Integer(required=True, description='Percent complete of task 1'),
    'pct2': fields.Integer(required=True, description='Percent complete of task 2'),
    'divisor': fields.Integer(required=True, description='Division of percentage compared against task 1 & task 2'),
    'status': fields.String(required=True, description='The status of the task'),
})


available_backups = api.model('available_backups', {
    'id': fields.Integer(readOnly=True, description='The backup id'),
    'backupfile': fields.String(required=True, description='The backupfile name'),
    'metafile': fields.String(required=True, description='The metafile'),
    'comment': fields.String(required=True, description='Comment'),
    'created': fields.DateTime(dt_format='rfc822', required=True, description='The time the task has been started'),
    'uuid': fields.String(required=True, description='The VM UUID'),
    'snapshotname': fields.String(required=True, description='The snapshot name of the backup'),
    'vmname': fields.String(required=True, description='VM Name of backed up VM'),
    'pool': fields.Nested(pool),
    'datastore': fields.Nested(datastore_safe),
})


host_sr = api.model('host_sr', {
    'name': fields.String(readOnly=True, description='Name of the SR'),
    'sr': fields.String(required=True, description='Xen OpaqueID of the SR'),
})
