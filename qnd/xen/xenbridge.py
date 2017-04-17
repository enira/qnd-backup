from xapi import XenAPI
from urlparse import urlparse


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
        except Exception, e:
            if hasattr(e, 'details') and e.details[0] == 'HOST_IS_SLAVE':
                # Redirect to cluster master
                url = urlparse(self.url).scheme + '://' + e.details[1]
                try:
                    self.master = False

                    session = XenAPI.Session(url, ignore_ssl=True)
                    session.login_with_password(self.username, self.password)
                except Exception, e:
                    raise e
            else:
                raise e
        return session

    def ismaster(self):
        if self.master == None:
            session = self.create_session()
            session.logout()
        return self.master

    def get_vms(self):
        """
        Get all VMs
        """
        session = self.create_session()
        all = session.xenapi.VM.get_all()
        vms = []
        for vm in all:
            record = session.xenapi.VM.get_record(vm)
            if not(record["is_a_template"]) and not(record["is_control_domain"]):
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
            if not(record["is_a_snapshot"]) and not(record["is_tools_iso"]) and not(record["missing"]) and record['type'] == 'user' and bool(record['sm_config']) == True:
                if record['name_label'] != 'base copy': 
                    # base copy are orphaned vdi's
                    disks.append([disk, record])
        session.logout()

        return disks


    def create_snapshot(self, uuid, name):
        session = self.create_session()

        snapshot = session.xenapi.VM.snapshot(uuid, name)
        
        session.xenapi.VM.set_is_a_template(snapshot, False)
        
        session.logout()
        return snapshot