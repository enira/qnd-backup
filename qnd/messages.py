import datetime

RESTORE_START = 'Restore job starting'
RESTORE_DISCOVERY = 'RESTORE_DISCOVERY'
RESTORE_MOUNT = 'RESTORE_MOUNT'
RESTORE_FAILED_MOUNT = 'RESTORE_FAILED_MOUNT'
RESTORE_COPY = 'RESTORE_COPY'

BACKUP_START = 'Backup job starting'
BACKUP_DISCOVERY = 'Discovering environment'
BACKUP_FAILED_FIND_VM = 'Searching for VM'
BACKUP_VM_NOT_FOUND = 'Failed to find VM with uuid: '
BACKUP_FIND_HOST = 'Finding VM resident'
BACKUP_CONNECTING_HOST = 'Connecting to host: $HOST'
BACKUP_CHECK_MOUNT = 'Checking mount point: $DATASTORE'
BACKUP_MOUNT = 'Mounting datastore: $DATASTORE'
BACKUP_FAILED_MOUNT = 'Failed to mount datastore: '
BACKUP_CREATE_SNAPSHOT = 'Creating snapshot'
BACKUP_BACKUP = 'Backing up VM'
BACKUP_FAILED_SNAPSHOT_CHAIN = 'BACKUP_FAILED_SNAPSHOT_CHAIN'
BACKUP_EXPORT = 'Exporting backup to datastore'
BACKUP_REMOVE_SNAPSHOT = 'Removing snapshot'
BACKUP_CLOSE = 'Closing backup'
BACKUP_DONE = 'Backup Done'

BACKUP_NOTIFICATION_FAILED_1 = 'Backup failed'
BACKUP_NOTIFICATION_FAILED_2 = 'Failed to create a snapshot for VM \'$BACKUPNAME\''

BACKUP_MESSAGE_COMPLETE_1 = 'Backup done.'
BACKUP_MESSAGE_COMPLETE_2 = 'Backup of VM \'$BACKUPNAME\' completed.'

def time():
    return datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d')