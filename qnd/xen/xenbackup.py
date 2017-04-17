import datetime
import sys
import paramiko
import configparser

from bridge import Bridge
from xenbridge import XenBridge

from database import db
from database.models import Task, Backup

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
    _commandpool = []
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

    
    def get_native_host(self, uuid):
        # todo
        pass


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

                    for img in images:
                        if img[0] == bd[1]['VDI']:

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
        task = session.query(Task).filter(Task.id == task_id).one()
        datastore = task.datastore
        uuid = task.uuid

        # make folder name
        bckfolder = self.BACKUPROOT + '/ds-' + str(task.datastore_id)

        self.update_pct(task, 0, 0, 0.20, 'discovery', session)

        # search the VM
        vms = self.get_vms()
        tobackup = None
        for vm in vms:
            if vm["uuid"] == uuid:
                tobackup = vm
                break

        self.update_pct(task, 0.10, 0, 0.20, 'discovery', session)

        # search which host we can use
        backuphost = self.get_native_host(vm["resident-on"])

        self.update_pct(task, 0.20, 0, 0.20, 'discovery', session)

        # start backing up: create a connection
        connection = Bridge(self._server[0], self._server[1], self._server[2])

        self.update_pct(task, 0.30, 0, 0.20, 'mount', session)

        # create mount point
        connection.sudo_command('mkdir -p ' + bckfolder, self._server[2])

        self.update_pct(task, 0.40, 0, 0.20, 'mount', session)

        # mount smb
        # TODO: create error 
        result = connection.sudo_command('mount -t cifs -o username=' + datastore.username + ',password=' + datastore.password + ' ' + datastore.host + ' ' + bckfolder, self._server[2])

        self.update_pct(task, 0.50, 0, 0.20, 'snapshot', session)

        # TODO: check if mounted, if not mounted change os filling root OS

        # TODO: remove
        print "Backing up: " + vm["name-label"] + "(" + vm["uuid"] + ")"
        
        # creating names
        snapshot_label = vm["name-label"] + "." + datetime.datetime.now().strftime("%Y%m%d.%H%M%S")
        backup_name = vm["name-label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".xva"
        meta_name = vm["name-label"] + "-" + datetime.datetime.now().strftime("%Y-%m-%d.%H%M%S") + ".meta"
        if backup_name.startswith("."):
            backup_name = backup_name[1:]

        # create a snapshot
        #snapshotuuid = connection.command('xe vm-snapshot uuid=' + vm["uuid"] + ' new-name-label=' + snapshot_label)
        snapshot = self.poolmaster.create_snapshot()

        self.update_pct(task, 0.60, None, 0.20, 'snapshot', session)

        # change snapshot to a vm 
        connection.command('xe template-param-set is-a-template=false ha-always-run=false uuid=' + snapshotuuid[0])

        self.update_pct(task, 0.70, None, 0.20, 'backup', session)

        # create a task viewer
        tcmd = 'xe task-list name-label="Export of VM: ' + vm["uuid"] + '"'
        self._commandpool.append(tcmd)

        # export as a xva
        connection.command('xe vm-export vm=' + snapshotuuid[0] + ' filename=' + bckfolder + '/' + backup_name)

        self.update_pct(task, 0.80, None, 0.20, 'export', session)

        # remove snapshot
        connection.command('xe vm-uninstall uuid=' + snapshotuuid[0] + ' force=true')

        self.update_pct(task, 0.90, None, 0.20, 'closing', session)

        # unmount smb
        # connection.command('umount ' + bckfolder)

        # delete mount point
        # connection.command('rmdir -r ' + bckfolder)

        # create backup object
        backup = Backup(task_id=task.id, 
                        metafile=meta_name, 
                        backupfile=backup_name, 
                        comment='Backup created at :' + datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'))
        session.add(backup)
        session.commit()
        
        self.update_pct(task, 1, 1, 0.20, 'done', session)

        session.close()
        