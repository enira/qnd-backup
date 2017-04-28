import datetime
import sys
import paramiko
import configparser

from bridge import Bridge
from xenbridge import XenBridge

from database import db
from database.models import BackupTask, ArchiveTask, RestoreTask, Backup, Datastore, Pool

import logging
import os
log = logging.getLogger(__name__)

class XenBackup:
    """
    Xen Backup tasks
    """

    servers = []            # all servers
    poolmaster = None       # poolmaster

    backuptasks = []
    hosts = None            #
    
    BACKUPROOT = '/media/.qnd'
    _server = None

    def __init__(self, servers, pool_name, pool_id):
        """
        Initialize the servers, copy all db info to workable XenBridge objects
        """
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
                print 'No bridge found, bridge not possible.'
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

    def update_pct(self, task, pct1, pct2, divisor, status, session):
        """
        Update percentages for a given task
        """

        task.pct1 = 0
        if pct2 != None:
            task.pct2 = 0
        task.divisor = 0.20
        task.status = 'backup_' + status
        session.add(task)
        session.commit()
        
    def backup_smb(self, task_id):
        """
        Backup a VM to a SMB fileshare
        """
        session = db.session
        task = session.query(BackupTask).filter(BackupTask.id == task_id).one()
        datastore = session.query(Datastore).filter(Datastore.id == task.datastore_id).one()
        pool = session.query(Pool).filter(Pool.id == task.pool_id).one()
        uuid = task.uuid

        # make folder name
        bckfolder = self.BACKUPROOT + '/ds-' + str(task.datastore_id)

        self.update_pct(task, 0, 0, 0.20, 'discovery', session)

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
            self.update_pct(task, 1, 1, 0.20, 'failed_find_vm', session)
            return

        self.update_pct(task, 0.10, 0, 0.20, 'discovery', session)

        # search which host we can use
        backuphost = self.get_native_host(tobackup[1]["resident_on"], hosts)

        self.update_pct(task, 0.20, 0, 0.20, 'discovery', session)

        # start backing up: create a connection
        connection = Bridge(self._server[0], self._server[1], self._server[2])

        self.update_pct(task, 0.30, 0, 0.20, 'mount', session)

        # create mount point
        connection.sudo_command('mkdir -p ' + bckfolder, self._server[2])

        self.update_pct(task, 0.40, 0, 0.20, 'mount', session)

        # check if already mounted
        result = connection.command('df -h | grep -i ' + bckfolder)
        if len(result) == 0:
            # mount smb
            result = connection.sudo_command('mount -t cifs -o username=' + datastore.username + ',password=' + datastore.password + ' ' + datastore.host + ' ' + bckfolder, self._server[2])

        result = connection.command('df -h | grep -i ' + bckfolder)
        if len(result) == 0:
            log.error('Could not mount the datastore')
            self.update_pct(task, 1, 1, 0.20, 'failed_mount', session)
            return

        self.update_pct(task, 0.50, 0, 0.20, 'snapshot', session)

        log.info("Backing up: " + tobackup[1]["name_label"] + "(" + tobackup[1]["uuid"] + ")")
        
        # creating names
        snapshot_label = tobackup[1]["name_label"] + "." + datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
        backup_name = tobackup[1]["name_label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".xva"
        meta_name = tobackup[1]["name_label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".meta"
        if backup_name.startswith("."):
            backup_name = backup_name[1:]

        self.update_pct(task, 0.70, None, 0.20, 'backup', session)

        # create a snapshot
        snapshot = self.get_active_host().create_snapshot(tobackup[0], snapshot_label)        

        self.update_pct(task, 0.80, None, 0.20, 'export', session)

        ####

        #http://xapi-project.github.io/xen-api/classes/task.html

        # download the xva TODO: connect on task
        dlsession = self.get_active_host().create_session()

        taskref = self.get_active_host().create_task(dlsession, 
                                           'Exporting backup of machine' + tobackup[1]["name_label"] + '. Downloading file ' + backup_name + '.')

        result = connection.sudo_command('curl https://' + backuphost + '/export?session_id=' + dlsession._session + '\\&ref=' + snapshot + ' -o ' + bckfolder + '/' + backup_name +' --insecure', self._server[2])
        
        self.get_active_host().remove_task(dlsession, taskref)

        dlsession.close()

        self.update_pct(task, 0.80, None, 0.20, 'cleanup', session)

        # remove snapshot
        self.get_active_host().remove_snapshot(snapshot)      

        self.update_pct(task, 0.90, None, 0.20, 'closing', session)

        # create backup object as done
        backup = Backup(metafile=meta_name, 
                        backupfile=backup_name, 
                        snapshotname=snapshot_label,
                        comment='Backup created at: ' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
                        uuid=uuid,
                        datastore=datastore,
                        pool=pool)

        session.add(backup)
        session.commit()

        # update the task
        task.ended=datetime.datetime.now()
        task.backup=backup

        session.add(task)
        session.commit()
        
        self.update_pct(task, 1, 1, 0.20, 'done', session)

        session.close()
        
    def restore_smb(self, task_id):
        """
        Restore a VM from a SMB fileshare
        """

        #curl -T <exportfile> http://root:foo@myxenserver2/import?sr_id=<ref_of_sr>

        session = db.session
        task = session.query(Task).filter(Task.id == task_id).one()
        datastore = task.datastore
        uuid = task.uuid

        # make folder name
        bckfolder = self.BACKUPROOT + '/ds-' + str(task.datastore_id)

        self.update_pct(task, 0, 0, 0.20, 'discovery', session)

        # search the VM if it already exists
        vms = self.get_vms()
        hosts = self.get_hosts()
        tobackup = None
        for vm in vms:
            if vm[1]["uuid"] == uuid:
                tobackup = vm
                break

        if tobackup == None:
            log.error('VM not found')
            self.update_pct(task, 1, 1, 0.20, 'failed_find_vm', session)
            return