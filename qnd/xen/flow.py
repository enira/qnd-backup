import threading
import datetime

import logging
import os 
log = logging.getLogger(__name__)

from apscheduler.schedulers.background import BackgroundScheduler

from database.models import Pool, Host, BackupTask, ArchiveTask, RestoreTask, Datastore, Schedule, Archive, Backup
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

    def get_vms(self, pool_id):
        obj = {}

        if pool_id not in self._poolcache:
            return obj

        return self._poolcache[pool_id]["backup"].get_vms()


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
        self._scheduler.add_job(self.archive, 'cron', minute='*', second='30', id='archive_job', max_instances=1, coalesce=True)
        self._scheduler.add_job(self.run, 'cron', minute='*', id='run_job', max_instances=1, coalesce=True)
        self._scheduler.add_job(self.cleanup, 'cron', minute='*', second='45', id='cleanup_job', max_instances=1, coalesce=True)

        session.close()
        self._scheduler.start()

    def schedule_edit(self, id):
        if self._scheduler.get_job(str(id)) != None:
            self._scheduler.remove_job(str(id))

        session = db.session
        schedule = session.query(Schedule).filter(Schedule.id == id).one()

        self._scheduler.add_job(self.create_task, 'cron', [int(schedule.id)], 
                                    day=schedule.day, 
                                    hour=schedule.hour, 
                                    minute=schedule.minute, 
                                    month=schedule.month,
                                    day_of_week=schedule.week,
                                    id=str(schedule.id))

        session.close()
                

    def schedule_add(self, id):
        session = db.session
        schedule = session.query(Schedule).filter(Schedule.id == id).one()
        self._scheduler.add_job(self.create_task, 'cron', [int(schedule.id)], 
                                    day=schedule.day, 
                                    hour=schedule.hour, 
                                    minute=schedule.minute, 
                                    month=schedule.month,
                                    day_of_week=schedule.week,
                                    id=str(schedule.id))
        session.close()

    def schedule_delete(self, id):
        if self._scheduler.get_job(str(id)) != None:
            self._scheduler.remove_job(str(id))

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
                log.info("No pool object created. Creating a xenbackup for pool_id=" + str(pool.id))
                self._poolcache[pool.id] = {}
                self._poolcache[pool.id]["hosts"] = []

                localhosts = []
                for host in pool.hosts:
                    self._poolcache[pool.id]["hosts"].append(host.id)
                    localhosts.append(host)

                log.info("Initialized a pool with " + str(len(self._poolcache[pool.id]["hosts"])) + " hosts")

                self._poolcache[pool.id]["backup"] = XenBackup(localhosts, pool.name, pool.id)

                log.info("Created a pool with " + str(len(self._poolcache[pool.id]["hosts"])) + " hosts")

                self._poolcache[pool.id]["backup"].discover()

        # submit all backup tasks
        tasks = session.query(BackupTask).filter(BackupTask.status == 'backup_pending').all()
        for task in tasks:
            type =  session.query(Datastore).filter(Datastore.id == task.datastore_id).one().type
            self._poolcache[task.pool_id]["backup"].backuptasks.append([task.id, type])
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
                backups = session.query(Backup).filter(Backup.datastore_id == archive.source_id)
                archivetasks = session.query(ArchiveTask).filter(ArchiveTask.archive_id == archive.id)

                # group for each uuid
                for backup in backups:
                    if backup.uuid in machines:
                        machines[backup.uuid].append(backup)
                    else:
                        machines[backup.uuid] = []
                        machines[backup.uuid].append(backup)

                for machine in machines:
                    length = len(machines[machine])

                    # remove ongoing tasks
                    for archivetask in archivetasks:
                        if 'done' in archivetask.status or 'failed' in archivetask.status:
                            pass
                        else:
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

                # if there are no archive tasks ongoing for this backup id
                if len(ongoing) == 0:
                    oldest = b
            else:
                # if oldest is newer then the one we have take that one
                if oldest.created > b.created:
                    ongoing = session.query(ArchiveTask).filter(ArchiveTask.backup_id == b.id).all()

                    # we aren't busy right?
                    if len(ongoing) == 0:
                        oldest = b

        return oldest
