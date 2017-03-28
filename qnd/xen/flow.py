
import threading
import datetime

import logging
import os 
log = logging.getLogger(__name__)

from database.models import Pool, Host, Task, Datastore
from database import db

from xenbackup import XenBackup

class Flow(object):
    """
    """

    __lock = threading.Lock()
    __instance = None

    @classmethod
    def instance(cls):
        if not cls.__instance:
            with cls.__lock:
                if not cls.__instance:
                    cls.__instance = cls()

        return cls.__instance

    _minute = None
    _poolcache = {}

    def get_environment(self, pool_id):
        obj = {}
        obj["vms"] = self._poolcache[pool_id]["backup"].get_vms()
        obj["hosts"] = self._poolcache[pool_id]["backup"].get_hosts()
        obj["disks"] = self._poolcache[pool_id]["backup"].get_attached_disks(obj["vms"])

        return obj

    def run(self):
        # create a xenbackup for each xen master
        pools = db.session.query(Pool).all()
        for pool in pools:
            if pool.id in self._poolcache:
                # we have our pool
                log.info("Pool bridge ok for pool_id=" + str(pool.id))
                # check the members
                if len(self._poolcache[pool.id]["hosts"]) == len(pool.hosts):
                    pass
                elif len(self._poolcache[pool.id]["hosts"]) < len(pool.hosts):
                    # change in datastores
                    for host in pool.hosts:
                        if host.id not in self._poolcache[pool.id]["hosts"]:
                            # found it
                            self._poolcache[pool.id]["hosts"].append(host.id)
                            self._poolcache[pool.id]["backup"].add_server(host)

                    self._poolcache[pool.id]["backup"].discover()
                else:
                    # deleted a host
                    for cachedhost in self._poolcache[pool.id]["hosts"]:
                        found = False
                        for host in pool.hosts:
                            if host.id == cachedhost:
                                found = True
                                break
                                
                        if found == False:
                            log.info('Removing orphaned hostid: ' + str(cachedhost))
                            self._poolcache[pool.id]["backup"].delete_server(cachedhost)

                    self._poolcache[pool.id]["backup"].discover()

            else:
                log.info("No pool object created. Creating a bridge for pool_id=" + str(pool.id))
                self._poolcache[pool.id] = {}
                self._poolcache[pool.id]["hosts"] = []

                localhosts = []
                for host in pool.hosts:
                    self._poolcache[pool.id]["hosts"].append(host.id)
                    localhosts.append(host)

                log.info("Initialized a pool with " + str(len(self._poolcache[pool.id]["hosts"])) + " hosts")

                self._poolcache[pool.id]["backup"] = XenBackup(localhosts, pool.name)

                log.info("Created a pool with " + str(len(self._poolcache[pool.id]["hosts"])) + " hosts")

                self._poolcache[pool.id]["backup"].discover()

        # check schedules
        now = datetime.datetime.now()
        if now.minute != self._minute:
            log.debug('Tick tock: ' + str(now.year) + "/" + str(now.month) + "/" + str(now.day) + " " + str(now.hour) + ":" + str(now.minute) + ":" + str(now.second)) 
            self._minute = now.minute

            # a new minute, calculate the schedules if they need to spawn tasks
            # TODO

        # get all tasks
        tasks = db.session.query(Task).filter(Task.status == 'pending')

        for task in tasks:
            self._poolcache[task.pool_id]["backup"].tasks.append(task)
            task.status = 'submitted'
            db.session.add(task)
            db.session.commit()

        for pool in self._poolcache:
            self._poolcache[pool]["backup"].run()


        # run all tasks


        # constant flow
        threading.Timer(3, self.run).start()

        