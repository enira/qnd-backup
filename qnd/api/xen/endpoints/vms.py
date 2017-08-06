import os

from flask import request
from flask_restplus import Resource

from api.xen.serializers import vm, vm_full
from api.restplus import api
from xen.flow import Flow

import logging.config
log = logging.getLogger(__name__)

ns = api.namespace('xen/vms', description='Operations related to vms')

@ns.route('/full/<int:pool_id>')
class VmsFullCollection(Resource):

    def calc(self, bytes):
        """
        Calculate in Mb
        """
        try:
            return str(int(bytes) / 1024 / 1024) + "Mb"
        except:
            return bytes

    @api.marshal_list_with(vm_full)
    def get(self, pool_id):
        """
        Returns list of vms with full info.
        """
        env = Flow.instance().get_environment(pool_id)

        wrapped = []
        if env['vms'] == None:
            return wrapped

        for e in env['vms']:
            vm = e[1]

            # finding resident
            hostlabel = ''
            for host in env["hosts"]:
                if vm["power_state"].lower() == 'running':
                    if vm["resident_on"] == host[0]:
                        hostlabel = host[1]["hostname"] + ' (' + host[1]["address"] + ')'
                else:
                    # suspended or paused
                    if vm["affinity"] == host[0]:
                        hostlabel = host[1]["hostname"] + ' (' + host[1]["address"] + ')'

            

            disks = env['disks'][vm["uuid"]]
            disk_used = 0
            disk_virtual = 0
            for disk in disks:
                disk_used = disk_used + int(disk['physical_utilisation'])
                disk_virtual = disk_virtual + int(disk['virtual_size'])

            # exceptional case; can't find the host
            if hostlabel == '':
                if len(disks) > 0:
                    host = Flow.instance().get_host_by_sr(pool_id, disks[0]['SR'])
                    if host != None:
                        hostlabel = host["hostname"] + ' (' + host["address"] + ')'

            # create object
            obj = type('',(object,),{"name": vm["name_label"], 
                                     "uuid": vm["uuid"],
                                     "status": vm["power_state"].lower(),
                                     "resident": hostlabel,
                                     "cpu": vm['VCPUs_at_startup'],
                                     "mem": vm["memory_static_max"],
                                     "disk_used": str(disk_used),
                                     "disk_virtual": str(disk_virtual),
                                    })()
           
            wrapped.append(obj)
        return wrapped

    
@ns.route('/summary/<int:pool_id>')
class VmsCollection(Resource):

    @api.marshal_list_with(vm)
    def get(self, pool_id):
        """
        Returns list of vms with short info.
        """
        env = Flow.instance().get_vms(pool_id)

        wrapped = []
        if len(env) == 0:
            return wrapped

        for e in env:
            vm = e[1]
            # create object
            obj = type('',(object,),{"name": vm["name_label"], 
                                     "uuid": vm["uuid"],
                                     "status": vm["power_state"].lower(),
                                    })()
           
            wrapped.append(obj)
        return wrapped


    
@ns.route('/<int:pool_id>/<string:uuid>')
@api.response(404, 'VM not found.')
class VmItem(Resource):

    @api.marshal_with(vm)
    def get(self, pool_id, uuid):
        """
        Returns a VM.
        """
        # this is a todo
        return None
   