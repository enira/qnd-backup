import datetime
import sys
import paramiko
import configparser

from bridge import Bridge
from xenbridge import XenBridge

from database import db
from database.models import BackupTask, ArchiveTask, RestoreTask, Backup, Datastore, Pool, Host

from xen.types import MessageType, TaskType

import messages
import os
import logging.config
log = logging.getLogger(__name__)

class XenBackup:
    """
    Xen Backup tasks
    """

    servers = []            # all servers
    poolmaster = None       # poolmaster

    pool_id = None           # current poolid

    backuptasks = []
    restoretasks = []
    hosts = None            # hosts
    
    BACKUPROOT = '/media/.qnd'
    _server = None

    _flow = None

    def __init__(self, flow, servers, pool_name, pool_id):
        """
        Initialize the servers, copy all db info to workable XenBridge objects
        """
        self._flow = flow
        self.servers = []
        self.pool_id = pool_id
        # create the server objects
        for server in servers:
            self.servers.append(XenBridge(server.id, server.address, server.username, server.password))

        # checking if xenbridge is external
        if os.path.isfile('config.ini'):
            # load the external xenbridge
            config = configparser.ConfigParser()
            config.read('config.ini')
            self._server=[config['bridge']['hostname'], config['bridge']['username'], config['bridge']['password']]
        else:
            if os.path.isfile('config.cfg'):
                # load the external xenbridge
                config = configparser.ConfigParser()
                config.read('config.cfg')
                self._server=[config['bridge']['hostname'], config['bridge']['username'], config['bridge']['password']]
            else:
                log.error('No bridge found, bridge not possible.')
                exit()

    def add_server(self, server):
        """
        Add a XenBridge object
        """
        self.servers.append(XenBridge(server.id, server.address, server.username, server.password))

    def remove_server(self, serverid):
        """
        Remove a XenBridge object
        """
        for server in self.servers:
            if serverid == server.id:
                self.servers.remove(server)
                break
    
    def get_native_host(self, ref, hosts):
        """
        Find the active host by opaque ref id
        """
        # find the active host by opaque ref id
        for host in hosts:
            if host[0] == ref:
                return host[1]['address']

        # return just an active host
        return hosts[0][1]['address']

    def get_active_host(self):
        """
        Return an active host
        """
        if self.poolmaster == None:
            if len(self.servers) > 1:
                return self.servers[0]
            return None
        else:
            return self.poolmaster
    
    def discover(self):
        """
        Find the Xenserver who is a master
        """
        for server in self.servers:
            log.info('Searching master.')
            if server.ismaster():
                self.poolmaster = server
                break

        if self.poolmaster == None:
            log.warning('Performance degraded, pool master not in pool.')

    def get_host_by_sr(self, sr):
        """
        Get a host based on SR. 
        """
        return self.get_active_host().get_host_by_sr(sr)

    def get_sr(self, address):
        """
        Get all SR for a host
        """
        return self.get_active_host().get_sr(address)

    def get_task(self, taskref):
        """
        Get all SR for a host
        """
        return self.get_active_host().get_task(taskref)

    def get_vms(self):   
        """
        Get all VMs in the pool
        """
        return self.get_active_host().get_vms()

    def get_hosts(self): 
        """
        Get all hosts in the pool
        """
        return self.get_active_host().get_hosts()

    def get_attached_disks(self, vms):
        """
        Get all disks attached to a VM
        """
        result = {}

        # get all disks
        blockdevices = self.get_active_host().get_block_devices()
        images = self.get_active_host().get_images()

        for e in vms:
            vm = e[1]
            # empty object
            result[vm["uuid"]] = []

            # search all blockdevices
            for bd in blockdevices:
                if bd[1]['VM'] == e[0]:
                    # vm matching id
                    for img in images:
                        if img[0] == bd[1]['VDI']:
                            # image matching id
                            result[vm["uuid"]].append(img[1])

        return result
    
    def run_backups(self):
        """
        Run all backups
        """

        # copy all jobs
        jobs = list(self.backuptasks)

        # empty tasks
        self.backuptasks = []

        for job in jobs:
            if job[1] == 'smb':
                self.backup_smb(job[0])

    def run_restores(self):
        """
        Run all backups
        """

        # copy all jobs
        jobs = list(self.restoretasks)

        # empty tasks
        self.restoretasks = []

        for job in jobs:
            self.restore(job[0])

    def restore(self, task_id):
        """
        Restore a VM
        """
        session = db.session
        task = session.query(RestoreTask).filter(RestoreTask.id == task_id).one()
        host = session.query(Host).filter(Host.id == task.host_id).one()
        datastore = session.query(Datastore).filter(Datastore.id == task.backup.datastore_id).one()

        # variables
        backup_ds_id = task.backup.datastore_id
        ds_username = datastore.username
        ds_password = datastore.password
        ds_host = datastore.host
        task_backupfile = task.backup.backupfile
        task_sr = task.sr
        task_snapshot = task.backup.snapshotname
        task_backupname = task.backupname

        session.close()


        taskid = self._flow.add_message(MessageType.TASK, messages.RESTORE_START , messages.time(), None)

        # start backing up: create a connection
        connection = Bridge(self._server[0], self._server[1], self._server[2])

        # make folder name
        resfolder = self.BACKUPROOT + '/ds-' + str(backup_ds_id)

        self.update_pct(TaskType.RESTORE, task_id, 0, 0, 0.20, 'RESTORE_DISCOVERY', messages.RESTORE_DISCOVERY, taskid)

        # create mount point
        connection.sudo_command('mkdir -p ' + resfolder, self._server[2])

        self.update_pct(TaskType.RESTORE, task_id, 0.40, 0, 0.20, 'RESTORE_MOUNT', messages.RESTORE_MOUNT, taskid)

        
        # check if wrong mounted
        result = connection.command('df -h | grep -i ' + ds_host)
        if len(result) != 0:
            split = result[0].split(' ')
            if split[len(split) - 1] != resfolder:
                result = connection.sudo_command('umount '+ split[len(split) - 1], self._server[2])

        # check if already mounted
        result = connection.command('df -h | grep -i ' + resfolder)
        if len(result) == 0:
            # mount smb
            result = connection.sudo_command('mount -t cifs -o username=' + ds_username + ',password=' + ds_password + ' ' + ds_host + ' ' + resfolder, self._server[2])
        else:
            # if we have a wrong mount
            if ds_host != result[0].split(' ')[0]:
                # unmount
                result = connection.sudo_command('umount '+ resfolder, self._server[2])
                result = connection.sudo_command('mount -t cifs -o username=' + ds_username + ',password=' + ds_password + ' ' + ds_host + ' ' + resfolder, self._server[2])
        

        result = connection.command('df -h | grep -i ' + resfolder)
        if len(result) == 0:
            log.error('Could not mount the datastore')
            self.update_pct(TaskType.RESTORE, task_id, 1, 1, 0.20, 'RESTORE_FAILED_MOUNT', messages.RESTORE_FAILED_MOUNT, taskid)
            return


        self.update_pct(TaskType.RESTORE, task_id, 0.60, 0, 0.20, 'RESTORE_COPY', messages.RESTORE_COPY, taskid)


        # download the xva TODO: connect on task
        dlsession = self.get_active_host().create_session()

        taskref = self.get_active_host().create_task(dlsession, 
                                           'Importing backup of machine' + task.backup.vmname + '. Importing file ' + task_backupfile + '.')

        self._flow.task_submit(self.pool_id, 'restore', task_id, taskref, taskid)
        cmd = 'curl -k -T ' + resfolder + '/' + task_backupfile + ' https://' + host.address + '/import?session_id=' + dlsession._session.replace(':','\\:') + '&sr=' + task_sr.replace(':','\\:') + '&task_id=' + taskref.replace(':','\\:')
        result = connection.command(cmd)
        
        self.get_active_host().remove_task(dlsession, taskref)

        dlsession.close()

        # rename the imported vm task.backup.snapshotname => task.backupname
        vm = self.get_active_host().get_vm_by_name(task_snapshot)
        self.get_active_host().set_vm_name(vm[0], task_backupname)
        
        # rename the imported disk task.backupname
        self.get_active_host().set_disk_names(vm[1]['VBDs'], task_backupname)




    def update_pct(self, type, task_id, pct1, pct2, divisor, status, message, id):
        """
        Update percentages for a given task
        """
        session = db.session
        if type == TaskType.BACKUP:
            task = session.query(BackupTask).filter(BackupTask.id == task_id).one()
        if type == TaskType.RESTORE:
            task = session.query(RestoreTask).filter(RestoreTask.id == task_id).one()

        task.pct1 = pct1
        if pct2 != None:
            task.pct2 = pct2
        task.divisor = divisor

        task.message = message
        task.status = status
        session.add(task)
        session.commit()

        self._flow.edit_message(id, message, str(int(round(task.pct() *100,0))) , None)

        session.close()

        
    def backup_smb(self, task_id):
        """
        Backup a VM to a SMB fileshare
        """
        
        # open a session to the database
        session = db.session

        # get all required objects from the database
        task = session.query(BackupTask).filter(BackupTask.id == task_id).one()
        datastore = session.query(Datastore).filter(Datastore.id == task.datastore_id).one()
        pool = session.query(Pool).filter(Pool.id == task.pool_id).one()

        # variables
        task_datastore_id = task.datastore_id
        uuid = task.uuid
        ds_username = datastore.username
        ds_password = datastore.password
        ds_host = datastore.host


        # close database session again
        session.close()

        taskid = self._flow.add_message(MessageType.TASK, messages.BACKUP_START , messages.time(), None)

        # make folder name
        bckfolder = self.BACKUPROOT + '/ds-' + str(task_datastore_id)
        self.update_pct(TaskType.BACKUP, task_id, 0, 0, 0.20, 'BACKUP_DISCOVERY', messages.BACKUP_DISCOVERY, taskid)

        # search the VM
        vms = self.get_vms()
        hosts = self.get_hosts()
        tobackup = None
        for vm in vms:
            if vm[1]["uuid"] == uuid:
                tobackup = vm
                break

        # if we didn't found the backup VM
        if tobackup == None:
            log.error('VM not found: ' + uuid)
            self.update_pct(TaskType.BACKUP, task_id, 1, 1, 0.20, 'BACKUP_FAILED_FIND_VM', messages.BACKUP_FAILED_FIND_VM, taskid)

            self._flow.remove_message(taskid)
            self._flow.add_message(MessageType.NOTIFICATION, 'Backup failed' ,messages.BACKUP_VM_NOT_FOUND + uuid, messages.time())

            return

        self.update_pct(TaskType.BACKUP, task_id, 0.10, 0, 0.20, 'BACKUP_FIND_HOST', messages.BACKUP_FIND_HOST, taskid)

        session = db.session
        # create backup object
        datastore = session.query(Datastore).filter(Datastore.id == task.datastore_id).one()
        pool = session.query(Pool).filter(Pool.id == task.pool_id).one()

        backup = Backup(metafile='', 
                        backupfile='', 
                        snapshotname='',
                        comment='Backup started at: ' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                        uuid=uuid,
                        vmname=tobackup[1]["name_label"],
                        datastore=datastore,
                        pool=pool)

        session.add(backup)
        session.commit()

        task.backup = backup
        session.add(task)
        session.commit()

        session.close()

        # search which host we can use
        backuphost = self.get_native_host(tobackup[1]["resident_on"], hosts)

        self.update_pct(TaskType.BACKUP, task_id, 0.20, 0, 0.20, 'BACKUP_CONNECTING_HOST', messages.BACKUP_CONNECTING_HOST, taskid)

        # start backing up: create a connection
        connection = Bridge(self._server[0], self._server[1], self._server[2])

        self.update_pct(TaskType.BACKUP, task_id, 0.30, 0, 0.20, 'BACKUP_CHECK_MOUNT', messages.BACKUP_CHECK_MOUNT, taskid)

        # create mount point
        connection.sudo_command('mkdir -p ' + bckfolder, self._server[2])

        self.update_pct(TaskType.BACKUP, task_id, 0.40, 0, 0.20, 'BACKUP_MOUNT', messages.BACKUP_MOUNT, taskid)

        # check if wrong mounted
        result = connection.command('df -h | grep -i ' + ds_host)
        if len(result) != 0:
            split = result[0].split(' ')
            if split[len(split) - 1] != bckfolder:
                result = connection.sudo_command('umount '+ split[len(split) - 1], self._server[2])

        # check if already mounted
        result = connection.command('df -h | grep -i ' + bckfolder)
        if len(result) == 0:
            # mount smb
            result = connection.sudo_command('mount -t cifs -o username=' + ds_username + ',password=' + ds_password + ' ' + ds_host + ' ' + bckfolder, self._server[2])
        else:
            # if we have a wrong mount
            if ds_host != result[0].split(' ')[0]:
                # unmount
                result = connection.sudo_command('umount '+ bckfolder, self._server[2])
                result = connection.sudo_command('mount -t cifs -o username=' + ds_username + ',password=' + ds_password + ' ' + ds_host + ' ' + bckfolder, self._server[2])
        
        
        result = connection.command('df -h | grep -i ' + bckfolder)
        if len(result) == 0:
            log.error('Could not mount the datastore')
            self.update_pct(TaskType.BACKUP, task_id, 1, 1, 0.20, 'BACKUP_FAILED_MOUNT', messages.BACKUP_FAILED_MOUNT + datastore.name, taskid)

            self._flow.remove_message(taskid)
            self._flow.add_message(MessageType.NOTIFICATION, 'Backup failed' , messages.BACKUP_FAILED_MOUNT + datastore.name, messages.time())

            return

        self.update_pct(TaskType.BACKUP, task_id, 0.50, 0, 0.20, 'BACKUP_CREATE_SNAPSHOT', messages.BACKUP_CREATE_SNAPSHOT, taskid)

        log.info("Backing up: " + tobackup[1]["name_label"] + "(" + tobackup[1]["uuid"] + ")")

        # creating names
        snapshot_label = tobackup[1]["name_label"] + "." + datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
        backup_name = tobackup[1]["name_label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".xva"
        meta_name = tobackup[1]["name_label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".meta"
        if backup_name.startswith("."):
            backup_name = backup_name[1:]

        session = db.session
        task = session.query(BackupTask).filter(BackupTask.id == task_id).one()
        task.backupname = snapshot_label 
        session.close()

        self.update_pct(TaskType.BACKUP, task_id, 0.70, None, 0.20, 'BACKUP_BACKUP', messages.BACKUP_BACKUP, taskid)

        # create a snapshot
        try:
            snapshot = self.get_active_host().create_snapshot(tobackup[0], snapshot_label)        
        except Exception as e:
            log.error(str(e.details))
            
            if e.details[0] == 'SR_BACKEND_FAILURE_109':
                # snapshot chain too long
                self.update_pct(TaskType.BACKUP, task_id, 1, 1, 0.20, 'BACKUP_FAILED_SNAPSHOT_CHAIN', messages.BACKUP_FAILED_SNAPSHOT_CHAIN, taskid)

                self._flow.remove_message(taskid)
                self._flow.add_message(MessageType.NOTIFICATION, messages.BACKUP_NOTIFICATION_FAILED_1 , messages.BACKUP_NOTIFICATION_FAILED_2.replace('$BACKUPNAME', tobackup[1]["name_label"]), messages.time())

                return


        self.update_pct(TaskType.BACKUP, task_id, 0.80, None, 0.20, 'BACKUP_EXPORT', messages.BACKUP_EXPORT, taskid)

        ####
        # http://xapi-project.github.io/xen-api/classes/task.html

        # download the xva TODO: connect on task
        dlsession = self.get_active_host().create_session()

        taskref = self.get_active_host().create_task(dlsession, 
                                           'Exporting backup of machine' + tobackup[1]["name_label"] + '. Downloading file ' + backup_name + '.')
        
        # pool_id, type, taskid, taskref, messageid
        self._flow.task_submit(self.pool_id, 'backup', task_id, taskref, taskid)

        result = connection.sudo_command('wget \'https://' + backuphost + '/export?session_id=' + dlsession._session + '&task_id=' + taskref +'&ref=' + snapshot + '\' --no-check-certificate -O ' + bckfolder + '/' + backup_name, self._server[2])
        
        self.get_active_host().remove_task(dlsession, taskref)

        dlsession.close()

        self.update_pct(TaskType.BACKUP, task_id, 0.80, 1.0, 0.20, 'BACKUP_REMOVE_SNAPSHOT', messages.BACKUP_REMOVE_SNAPSHOT, taskid)

        # remove snapshot
        self.get_active_host().remove_snapshot(snapshot)      

        self.update_pct(TaskType.BACKUP, task_id, 0.90, 1.0, 0.20, 'BACKUP_CLOSE', messages.BACKUP_CLOSE, taskid)

        # open a session to the database
        session = db.session

        # get all required objects from the database
        task = session.query(BackupTask).filter(BackupTask.id == task_id).one()
        datastore = session.query(Datastore).filter(Datastore.id == task.datastore_id).one()
        pool = session.query(Pool).filter(Pool.id == task.pool_id).one()

        # create backup object as done
        backup = Backup(metafile=meta_name, 
                        backupfile=backup_name, 
                        snapshotname=snapshot_label,
                        comment='Backup created at: ' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                        uuid=uuid,
                        vmname=tobackup[1]["name_label"],
                        datastore=datastore,
                        pool=pool)

        session.add(backup)
        session.commit()

        # update the task
        task.ended = datetime.datetime.now()
        task.backupname = snapshot_label 

        session.add(task)
        session.commit()
        
        self._flow.remove_message(taskid)
        self._flow.add_message(MessageType.MESSAGE, messages.BACKUP_MESSAGE_COMPLETE_1, messages.BACKUP_MESSAGE_COMPLETE_2.replace('$BACKUPNAME', tobackup[1]["name_label"]), messages.time())

        session.close()
        
        self.update_pct(TaskType.BACKUP, task_id, 1, 1, 0.20, 'BACKUP_DONE', messages.BACKUP_DONE, taskid)

