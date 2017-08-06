import datetime

RESTORE_DISCOVERY = 'RESTORE_DISCOVERY'
RESTORE_MOUNT = 'RESTORE_MOUNT'
RESTORE_FAILED_MOUNT = 'RESTORE_FAILED_MOUNT'

BACKUP_DISCOVERY = 'Discovering environment'
BACKUP_FAILED_FIND_VM = 'Searching for VM'
BACKUP_FIND_HOST = 'Finding VM resident'
BACKUP_CONNECTING_HOST = 'Connecting to host: $HOST'
BACKUP_CHECK_MOUNT = 'Checking mount point: $DATASTORE'
BACKUP_MOUNT = 'Mounting datastore: $DATASTORE'
BACKUP_FAILED_MOUNT = 'BACKUP_BACKUP'
BACKUP_CREATE_SNAPSHOT = 'Creating snapshot'
BACKUP_BACKUP = 'Backing up VM'
BACKUP_FAILED_SNAPSHOT_CHAIN = 'BACKUP_FAILED_SNAPSHOT_CHAIN'
BACKUP_EXPORT = 'Exporting backup to datastore'
BACKUP_REMOVE_SNAPSHOT = 'Removing snapshot'
BACKUP_CLOSE = 'Closing backup'
BACKUP_DONE = 'Backup Done'

def time():
    return datetime.datetime.now().strftime('%H:%M:%S %Y-%m-%d')