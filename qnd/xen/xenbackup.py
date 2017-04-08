import datetime
import sys
import paramiko

from bridge import Bridge

from database import db
from database.models import Task, Backup

import logging
import os
log = logging.getLogger(__name__)

class XenBackup:
    """
    """

    servers = []
    backuptasks = []
    hosts = None
    
    BACKUPROOT = '/media/.qnd'
    _commandpool = []

    def __init__(self, servers, pool):
        self.servers = servers

    def add_server(self, server):
        self.servers.append(server)

    def remove_server(self, serverid):
        for server in self.servers:
            if serverid == server.id:
                self.servers.remove(server)
                break

    def get_native_host(self, uuid):
        found = None
        for host in self.hosts:
            if host["uuid"] == uuid:
                log.info('Found assigned host: ' + host["name-label"])
                if host["attached"] == True:
                    found = host["address"]
                break

        if found == None:
            # credentials are not found just return one
            log.info('Native host credentials not found, using first active host. Performance is severely impacted')
            return self.get_active_server()
            
        else:
            # host credentials are there
            for server in self.servers:
                if server.address == found:
                    log.info('Active server found: ' + server.address)
                    return server

        # default return default
        return self.get_active_server()


    def discover(self):
        connection = self.get_active_server()

        if connection == None:
            log.info('No hosts attached.')
            return

        # discover the host list 
        hosts = connection.command_array('xe host-list params=all')

        # check if all hosts are available
        self.hosts = hosts

        # set all hosts as unattached
        for host in hosts:
            host["attached"] = False

        for host in hosts:
            for server in self.servers:
                if host["address"] == server.address:
                    log.info('Host discovered: ' + host["address"] + ', OK')
                    host["attached"] = True
        
        for host in hosts:
            if host["attached"] == False:
                log.info(host["address"] + ', No credentials found, VMs running on this host may backup slow.')


    def get_active_server(self):
        # connect to xen
        connection = None 

        # get the first available connection
        for server in self.servers:
            connection = Bridge(server.address, server.username, server.password)
            connection.connect()

            if not connection.is_connected():
                connection = None
            else:
                break

        if connection == None:
            log.info('No available servers!')
            return None

        return connection


    def get_vms(self):   
        if self.get_active_server() == None:
            return None
        result = self.get_active_server().command_array('xe vm-list params')
        return result

    def get_hosts(self): 
        if self.get_active_server() == None:
            return None
        result = self.get_active_server().command_array('xe host-list params')
        return result

    def get_attached_disks(self, vms):
        result = {}
        if vms == None:
            return result

        for vm in vms:
            result[vm["uuid"]] = []

            disks = self.get_active_server().command_array('xe snapshot-disk-list uuid=' + vm["uuid"] + ' params=all')

            # weed through
            for disk in disks:
                #
                if disk["type"] == 'User':
                    result[vm["uuid"]].append([disk['sr-name-label'], disk['name-label'], disk['physical-utilisation'], disk['virtual-size']])
                
        return result

    
    def run_backups(self):
        # run all backups

        # copy all jobs
        jobs = list(self.backuptasks)

        # empty tasks
        self.backuptasks = []

        for job in jobs:
            if job[1] == 'smb':
                self.backup_smb(job[0])


    def update_pct(self, task, pct1, pct2, divisor, status, session):
        task.pct1 = 0
        if pct2 != None:
            task.pct2 = 0
        task.divisor = 0.20
        task.status = 'backup_' + status
        session.add(task)
        session.commit()
        
    def backup_smb(self, task_id):
        session = db.session
        task = session.query(Task).filter(Task.id == task_id).one()
        datastore = task.datastore
        uuid = task.uuid

        # folder 
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
        connection = Bridge(backuphost.address, backuphost.username, backuphost.password)

        self.update_pct(task, 0.30, 0, 0.20, 'mount', session)

        # create mount point
        connection.command('mkdir -p ' + bckfolder)

        self.update_pct(task, 0.40, 0, 0.20, 'mount', session)

        # mount smb
        # TODO: create error 
        result = connection.command('mount -t cifs -o username=' + datastore.username + ',password=' + datastore.password + ' ' + datastore.host + ' ' + bckfolder)

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
        snapshotuuid = connection.command('xe vm-snapshot uuid=' + vm["uuid"] + ' new-name-label=' + snapshot_label)

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
        