import datetime
import sys
import paramiko
import configparser

from bridge import Bridge
from xenbridge import XenBridge

from database import db
from database.models import BackupTask, ArchiveTask, RestoreTask, Backup, Datastore, Pool, Host

from xen.types import MessageType

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
            return self.servers[0]
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

    def get_sr(self, address):
        """
        Get all SR for a host
        """
        return self.get_active_host().get_sr(address)

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

        # start backing up: create a connection
        connection = Bridge(self._server[0], self._server[1], self._server[2])

        # make folder name
        resfolder = self.BACKUPROOT + '/ds-' + str(task.backup.datastore_id)

        self.update_pct(task, 0, 0, 0.20, messages.RESTORE_DISCOVERY, session, taskid)

        # create mount point
        connection.sudo_command('mkdir -p ' + resfolder, self._server[2])

        self.update_pct(task, 0.40, 0, 0.20, messages.RESTORE_MOUNT, session, taskid)

        # check if already mounted
        result = connection.command('df -h | grep -i ' + resfolder)
        if len(result) == 0:
            # mount smb
            result = connection.sudo_command('mount -t cifs -o username=' + datastore.username + ',password=' + datastore.password + ' ' + datastore.host + ' ' + resfolder, self._server[2])

        result = connection.command('df -h | grep -i ' + resfolder)
        if len(result) == 0:
            log.error('Could not mount the datastore')
            self.update_pct(task, 1, 1, 0.20, messages.RESTORE_FAILED_MOUNT, session, taskid)
            return

        # download the xva TODO: connect on task
        dlsession = self.get_active_host().create_session()

        taskref = self.get_active_host().create_task(dlsession, 
                                           'Importing backup of machine' + task.backup.vmname + '. Importing file ' + task.backup.backupfile + '.')

        result = connection.sudo_command('curl -T ' + resfolder + '/' + task.backup.backupfile + ' https://' + host.address + '/import?session_id=' + dlsession._session + '\\&sr=' + task.sr + ' --insecure', self._server[2])
        
        self.get_active_host().remove_task(dlsession, taskref)

        dlsession.close()

        # rename the imported vm task.backup.snapshotname => task.backupname
        vm = self.get_active_host().get_vm_by_name(task.backup.snapshotname)
        self.get_active_host().set_vm_name(vm[0], task.backupname)
        
        # rename the imported disk task.backupname
        self.get_active_host().set_disk_names(vm[1]['VBDs'], task.backupname)

    def update_pct(self, task, pct1, pct2, divisor, status, session, id):
        """
        Update percentages for a given task
        """

        task.pct1 = pct1
        if pct2 != None:
            task.pct2 = pct2
        task.divisor = divisor

        # isinstance
        #if isinstance(task, BackupTask): 
        #    task.status = 'backup_' + status
        #if isinstance(task, RestoreTask):
        #    task.status = 'restore_' + status
        task.status = status
        session.add(task)
        session.commit()

        self._flow.edit_message(id, task.status, str(int(round(task.pct() *100,0))) , None)
        
    def backup_smb(self, task_id):
        """
        Backup a VM to a SMB fileshare
        """
        
        session = db.session
        task = session.query(BackupTask).filter(BackupTask.id == task_id).one()
        datastore = session.query(Datastore).filter(Datastore.id == task.datastore_id).one()
        pool = session.query(Pool).filter(Pool.id == task.pool_id).one()
        uuid = task.uuid

        taskid = self._flow.add_message(MessageType.TASK, 'Backup job starting...' , messages.time(), None)

        # make folder name
        bckfolder = self.BACKUPROOT + '/ds-' + str(task.datastore_id)

        self.update_pct(task, 0, 0, 0.20,  messages.BACKUP_DISCOVERY, session, taskid)

        # search the VM
        vms = self.get_vms()
        hosts = self.get_hosts()
        tobackup = None
        for vm in vms:
            if vm[1]["uuid"] == uuid:
                tobackup = vm
                break

        if tobackup == None:
            log.error('VM not found')
            self.update_pct(task, 1, 1, 0.20, messages.BACKUP_FAILED_FIND_VM, session, taskid)

            self._flow.remove_message(taskid)
            self._flow.add_message(MessageType.NOTIFICATION, 'Backup failed' ,'Failed to find VM with uuid: ' + uuid, messages.time())

            return

        self.update_pct(task, 0.10, 0, 0.20, messages.BACKUP_FIND_HOST, session, taskid)

        # search which host we can use
        backuphost = self.get_native_host(tobackup[1]["resident_on"], hosts)

        self.update_pct(task, 0.20, 0, 0.20, messages.BACKUP_CONNECTING_HOST, session, taskid)

        # start backing up: create a connection
        connection = Bridge(self._server[0], self._server[1], self._server[2])

        self.update_pct(task, 0.30, 0, 0.20, messages.BACKUP_CHECK_MOUNT, session, taskid)

        # create mount point
        connection.sudo_command('mkdir -p ' + bckfolder, self._server[2])

        self.update_pct(task, 0.40, 0, 0.20, messages.BACKUP_MOUNT, session, taskid)

        # check if already mounted
        result = connection.command('df -h | grep -i ' + bckfolder)
        if len(result) == 0:
            # mount smb
            result = connection.sudo_command('mount -t cifs -o username=' + datastore.username + ',password=' + datastore.password + ' ' + datastore.host + ' ' + bckfolder, self._server[2])

        result = connection.command('df -h | grep -i ' + bckfolder)
        if len(result) == 0:
            log.error('Could not mount the datastore')
            self.update_pct(task, 1, 1, 0.20, messages.BACKUP_FAILED_MOUNT, session, taskid)

            self._flow.remove_message(taskid)
            self._flow.add_message(MessageType.NOTIFICATION, 'Backup failed' ,'Failed to mount datastore ' + datastore.name, messages.time())

            return

        self.update_pct(task, 0.50, 0, 0.20, messages.BACKUP_CREATE_SNAPSHOT, session, taskid)

        log.info("Backing up: " + tobackup[1]["name_label"] + "(" + tobackup[1]["uuid"] + ")")

        # creating names
        snapshot_label = tobackup[1]["name_label"] + "." + datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
        backup_name = tobackup[1]["name_label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".xva"
        task.backupname = snapshot_label 
        meta_name = tobackup[1]["name_label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".meta"
        if backup_name.startswith("."):
            backup_name = backup_name[1:]

        self.update_pct(task, 0.70, None, 0.20, messages.BACKUP_BACKUP, session, taskid)

        #        # TODO check if snapshots are ok

        # create a snapshot
        try:
            snapshot = self.get_active_host().create_snapshot(tobackup[0], snapshot_label)        
        except Exception as e:
            log.error(str(e.details))
            
            if e.details[0] == 'SR_BACKEND_FAILURE_109':
                # snapshot chain too long
                self.update_pct(task, 1, 1, 0.20, messages.BACKUP_FAILED_SNAPSHOT_CHAIN, session, taskid)

                self._flow.remove_message(taskid)
                self._flow.add_message(MessageType.NOTIFICATION, messages.BACKUP_NOTIFICATION_FAILED_1 , messages.BACKUP_NOTIFICATION_FAILED_2.replace('$BACKUPNAME', tobackup[1]["name_label"]), messages.time())

                return


        self.update_pct(task, 0.80, None, 0.20, messages.BACKUP_EXPORT, session, taskid)

        ####

        #http://xapi-project.github.io/xen-api/classes/task.html

        # download the xva TODO: connect on task
        dlsession = self.get_active_host().create_session()

        taskref = self.get_active_host().create_task(dlsession, 
                                           'Exporting backup of machine' + tobackup[1]["name_label"] + '. Downloading file ' + backup_name + '.')

        result = connection.sudo_command('wget \'https://' + backuphost + '/export?session_id=' + dlsession._session + '&ref=' + snapshot + '\' --no-check-certificate -O ' + bckfolder + '/' + backup_name, self._server[2])
        
        self.get_active_host().remove_task(dlsession, taskref)

        dlsession.close()

        self.update_pct(task, 0.80, None, 0.20, messages.BACKUP_REMOVE_SNAPSHOT, session, taskid)

        # remove snapshot
        self.get_active_host().remove_snapshot(snapshot)      

        self.update_pct(task, 0.90, None, 0.20, messages.BACKUP_CLOSE, session, taskid)

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
        task.backup = backup
        task.backupname = snapshot_label 

        session.add(task)
        session.commit()
        
        self.update_pct(task, 1, 1, 0.20, messages.BACKUP_DONE, session, taskid)

        self._flow.remove_message(taskid)

        self._flow.add_message(MessageType.MESSAGE, messages.BACKUP_MESSAGE_COMPLETE_1, messages.BACKUP_MESSAGE_COMPLETE_2.replace('$BACKUPNAME', tobackup[1]["name_label"]), messages.time())

        session.close()
        
