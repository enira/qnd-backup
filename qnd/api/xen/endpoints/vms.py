import logging
import os

from flask import request
from flask_restplus import Resource

from api.xen.serializers import vm
from api.restplus import api
from xen.flow import Flow

log = logging.getLogger(__name__)

ns = api.namespace('xen/vms', description='Operations related to vms')

@ns.route('/<int:pool_id>')
class VmsCollection(Resource):

    def calc(self, bytes):
        try:
            return str(int(bytes) / 1024 / 1024) + "Mb"
        except:
            return bytes

    @api.marshal_list_with(vm)
    def get(self, pool_id):
        """
        Returns list of vms.
        """
        env = Flow.instance().get_environment(pool_id)

        wrapped = []
        for vm in env['vms']:
            if vm["is-a-snapshot"] == 'false' and 'Control domain on host' not in vm["name-label"]:
                # finding resident
                hostlabel = ''
                for host in env["hosts"]:
                    if vm["power-state"] == 'running':
                        if vm["resident-on"] == host["uuid"]:
                            hostlabel = host["hostname"] + ' (' + host["address"] + ')'
                    else:
                        # suspended or paused
                        if vm["affinity"] == host["uuid"]:
                            hostlabel = host["hostname"] + ' (' + host["address"] + ')'

                disks = env['disks'][vm["uuid"]]


                obj = type('',(object,),{"name": vm["name-label"], 
                                         "uuid": vm["uuid"],
                                         "status": vm["power-state"],
                                         "resident": hostlabel,
                                         "mem_actual": vm["memory-actual"],
                                         "mem_max": vm["memory-static-max"],
                                         "mem_pct": (float(vm["memory-actual"]) - float(vm["memory-overhead"]))  / float( vm["memory-static-max"])
                                         })()
           
                wrapped.append(obj)

        return wrapped

    
    
@ns.route('/<int:vm_uuid>/<string:uuid>')
@api.response(404, 'VM not found.')
class VmItem(Resource):

    @api.marshal_with(vm)
    def get(self, pool_id, uuid):
        """
        Returns a VM.
        """
        return db.session.query(Pool).filter(Pool.id == id).one()
   