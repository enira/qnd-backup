from xapi import XenAPI
from urllib.parse import urlparse

import logging.config
log = logging.getLogger(__name__)

class XenBridge:
    """
    Bridge between a server and the host. This class uses SSH to connect to the Xen server.
    """
    id = None
    username = None
    password = None
    address = None
    url = None
    master = None

    
    def __init__(self, id, address, username, password):
        """
        Initialize the class
        """
        self.id = id
        self.address = address
        self.username = username
        self.password = password
        self.url = 'https://' + address

    def create_session(self):
        """
        Create a session with XenAPI
        """
        try:
            session = XenAPI.Session(self.url, ignore_ssl=True)
            session.xenapi.login_with_password(self.username, self.password)
            
            self.master = True
        except Exception as e:
            if hasattr(e, 'details') and e.details[0] == 'HOST_IS_SLAVE':
                # Redirect to cluster master
                url = urlparse(self.url).scheme + '://' + e.details[1]
                try:
                    self.master = False

                    session = XenAPI.Session(url, ignore_ssl=True)
                    session.login_with_password(self.username, self.password)
                except Exception as e:
                    raise e
            else:
                raise e
        return session

    def ismaster(self):
        """
        Check if this instance is a master instance in a pool. Do this by logging in and logging out.
        """

        if self.master == None:
            session = self.create_session()
            session.logout()
        return self.master

    def get_sr(self, address):
        """
        Get all SRs for a hostid (based on an IP address)
        """
        session = self.create_session()

        # get all hosts
        hosts = session.xenapi.host.get_all()
        srs = []

        for h in hosts:
            record = session.xenapi.host.get_record(h)
            if record['address'] == address:
                # found the correct host

                # get all pbd's
                for p in record['PBDs']:
                    pbd = session.xenapi.PBD.get_record(p)
                    # get the associated SR
                    sr = session.xenapi.SR.get_record(pbd['SR'])
                    if sr['type'] == 'nfs' or sr['type'] == 'ext':
                        srs.append([pbd['SR'],sr])

        return srs

    def get_vms(self):
        """
        Get all VMs
        """
        session = self.create_session()
        all = session.xenapi.VM.get_all()
        vms = []
        for vm in all:
            record = session.xenapi.VM.get_record(vm)
            if not(record["is_a_template"]) and not(record["is_control_domain"]) and record["is_a_snapshot"] == False:
                vms.append([vm, record])

        session.logout()

        return vms

    def get_hosts(self):
        """
        Get all hosts
        """
        session = self.create_session()
        all =  session.xenapi.host.get_all()
        hosts = []
        for host in all:
            record = session.xenapi.host.get_record(host)
            hosts.append([host, record])
        session.logout()

        return hosts

    def get_host_by_sr(self, sr):
        """
        Get a host based on a SR
        """
        session = self.create_session()
        all =  session.xenapi.host.get_all()
        found = None
        for host in all:
            record = session.xenapi.host.get_record(host)

            # get the underlying SR of al PBDs
            for pbd in record['PBDs']:
                record_pbd = session.xenapi.PBD.get_record(pbd)
                if record_pbd['SR'] == sr:
                    found = record
                    break

        session.logout()

        return found

    def get_block_devices(self):
        """
        Get all block devices
        """
        session = self.create_session()
        all =  session.xenapi.VBD.get_all()
        blocks = []
        for block in all:
            record = session.xenapi.VBD.get_record(block)
            try:
                if record['type'] != 'CD': 
                    blocks.append([block, record])
            except:
                pass
        session.logout()

        return blocks

    def get_images(self):
        """
        Get all disks
        """
        session = self.create_session()
        all =  session.xenapi.VDI.get_all()
        disks = []
        for disk in all:
            record = session.xenapi.VDI.get_record(disk)
            disks.append([disk, record])
        session.logout()

        return disks

    def create_task(self, session, description):
        """
        Create a task
        """
        task = session.xenapi.task.create(session._session, description)
        return task

    def remove_task(self, session, ref):
        """
        Destroy task
        """
        session.xenapi.task.destroy(ref)

    def get_task(self, taskref):
        """
        Get all SR for a host
        """
        session = self.create_session()

        task = session.xenapi.task.get_record(taskref)

        session.logout()
        return task

    def create_snapshot(self, ref, name):
        """
        Create an exportable snapshot
        """
        session = self.create_session()

        snapshot = session.xenapi.VM.snapshot(ref, name)
        
        session.xenapi.VM.set_is_a_template(snapshot, False)
        
        session.logout()
        return snapshot

    def remove_snapshot(self, ref):
        """
        Remove a snapshot
        """
        session = self.create_session()

        # delete the underlying VDI
        vm = session.xenapi.VM.get_record(ref)
        for vdb in vm['VBDs']:
            record = session.xenapi.VBD.get_record(vdb)
            if record['type'] != 'CD':
                session.xenapi.VDI.destroy(record['VDI'])

        session.xenapi.VM.destroy(ref)

        session.logout()

    def get_vm_by_name(self, name):
        """
        Get VM by name
        """
        session = self.create_session()
        refs = session.xenapi.VM.get_by_name_label(name)
        vms = session.xenapi.VM.get_record(refs[0])
        session.logout()

        return [refs[0], vms]

    def set_vm_name(self, ref, name):
        """
        Set a VM name
        """
        session = self.create_session()
        session.xenapi.VM.set_name_label(ref, name)
        session.logout()

    def set_disk_names(self, vbds, name):
        """
        Set a VM name
        """
        session = self.create_session()
        index = 0
        for vbd in vbds:
            record = session.xenapi.VBD.get_record(vbd)
            if record['VDI'] != 'OpaqueRef:NULL':
                # count the disks
                index = index + 1
                
        # only one disk
        if index == 1:
            for vbd in vbds:
                record = session.xenapi.VBD.get_record(vbd)
                if record['VDI'] != 'OpaqueRef:NULL':
                    # get the attached VDI
                    session.xenapi.VDI.set_name_label(record['VDI'], 'disk-' + name)
        else:
            # more than one
            index = 0
            for vbd in vbds:
                record = session.xenapi.VBD.get_record(vbd)
                if record['VDI'] != 'OpaqueRef:NULL':
                    # get the attached VDI
                    index = index + 1
                    session.xenapi.VDI.set_name_label(record['VDI'], 'disk-' + name + '-' + str(index))
        session.logout()