import threading
import datetime

import logging
import os 
log = logging.getLogger(__name__)

from apscheduler.schedulers.background import BackgroundScheduler

from database.models import Pool, Host, Task, Datastore, Schedule, Archive, Backup, ArchiveTask
from database import db

from mover import Mover

from xenbackup import XenBackup

logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)

class Flow(object):
    """
    Internal flow of the application.
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
    _scheduler = None
    _mover = Mover()

    def get_environment(self, pool_id):
        obj = {}

        if pool_id not in self._poolcache:
            obj["vms"] = []
            obj["hosts"] = []
            obj["disks"] = []
            return obj

        obj["vms"] = self._poolcache[pool_id]["backup"].get_vms()
        obj["hosts"] = self._poolcache[pool_id]["backup"].get_hosts()
        obj["disks"] = self._poolcache[pool_id]["backup"].get_attached_disks(obj["vms"])

        return obj

    def create_task(self, schedule_id):
        session = db.session
        schedule = session.query(Schedule).filter(Schedule.id == schedule_id).one()
        print str(datetime.datetime.now()) + '>>' + str(schedule.id)

        task = Task(status='backup_pending', pct1=0, pct2=0, pool=schedule.pool, datastore=schedule.datastore, uuid=schedule.uuid)
        try:
            session.add(task)
            session.commit()
        except Exception as e:
            print e
        session.close()

    def initialize_scheduler(self):
        # initialize the scheduler
        session = db.session()
        self._scheduler = BackgroundScheduler()

        # read the cron jobs from DB
        schedules = session.query(Schedule).all()
        for schedule in schedules:
            print 'Adding schedule: ' + schedule.name + ' with id ' + str(schedule.id)
            self._scheduler.add_job(self.create_task, 'cron', [int(schedule.id)], 
                                    day=schedule.day, 
                                    hour=schedule.hour, 
                                    minute=schedule.minute, 
                                    month=schedule.month,
                                    day_of_week=schedule.week,
                                    id=str(schedule.id))

        # run
        self._scheduler.add_job(self.archive, 'cron', minute='*', id='archive_job', max_instances=1, coalesce=True)
        self._scheduler.add_job(self.run, 'cron', minute='*', id='run_job', max_instances=1, coalesce=True)
        self._scheduler.add_job(self.cleanup, 'cron', minute='*', id='cleanup_job', max_instances=1, coalesce=True)

        session.close()
        self._scheduler.start()

    def check_schedules(self):
        pass

    def run(self):
        session = db.session
        # create a xenbackup for each xen master
        pools = session.query(Pool).all()

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
                            self._poolcache[pool.id]["backup"].remove_server(cachedhost)

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
            self.check_schedules()

        # submit all backup tasks
        tasks = session.query(Task).filter(Task.status == 'backup_pending').all()
        for task in tasks:
            self._poolcache[task.pool_id]["backup"].backuptasks.append([task.id, task.datastore.type])
            task.status = 'backup_submitted'

            session.add(task)
            session.commit()

        session.close()

        for pool in self._poolcache:
            self._poolcache[pool]["backup"].run_backups()


    def cleanup(self):
        # cleanup task
        session = db.session
        
        orphans = session.query(Host).filter(Host.pool_id == None).all()
        for orphan in orphans:
            log.info('Orphaned host found: ' + str(orphan.address))
            session.delete(orphan)
            session.commit()

        session.close()


    def archive(self):
        # if no lock in place
        
        try:
            session = db.session

            # get all the healthy archives 
            archives = session.query(Archive).filter(Archive.source_id.isnot(None), Archive.target_id.isnot(None)).all()
            for archive in archives:
                machines = {}
                # for each archive check attached datastore backups
                backups = session.query(Backup).join(Task).filter(Task.datastore_id == archive.source_id)
                archivetasks = session.query(ArchiveTask).filter(ArchiveTask.archive_id == archive.id)

                # group for each uuid
                for backup in backups:
                    if 'done' in backup.task.status:
                        if backup.task.uuid in machines:
                            machines[backup.task.uuid].append(backup)
                        else:
                            machines[backup.task.uuid] = []
                            machines[backup.task.uuid].append(backup)

                for machine in machines:
                    length = len(machines[machine])

                    # remove ongoing tasks
                    for archivetask in archivetasks:
                        if 'done' not in archivetask.status:
                            length = length - 1

                    # if we need to archive
                    if length > archive.retention:
                        print 'Retention policy of : ' + str(archive.retention) + ' exceeded for uuid: ' + machine

                        toarchive = self._internal_get_archive(machine, machines, session)

                        committask = ArchiveTask(archive=archive, backup=toarchive, status='archive_pending')
                        session.add(committask)
                        session.commit()

                        self._mover.archive(committask.id)
            session.close()

        except Exception as e :
            print 'Uh oh, exception: ' + str(e)


    def _internal_get_archive(self, machine, machines, session):
        oldest = None

        for b in machines[machine]:
            if oldest is None:
                ongoing = session.query(ArchiveTask).filter(ArchiveTask.backup_id == b.id).all()
                if len(ongoing) == 0:
                    oldest = b
            else:
                if oldest.task.started > b.task.started:
                    ongoing = session.query(ArchiveTask).filter(ArchiveTask.backup_id == b.id).all()
                    if len(ongoing) == 0:
                        oldest = b

        return oldest
