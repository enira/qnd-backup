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
    _orphan_lock = False
    _archive_lock = False

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
        self._scheduler.add_job(self.archive, 'cron', minute='*', id='archive_job')

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
            self.check_schedules()

        # submit all backup tasks
        tasks = session.query(Task).filter(Task.status == 'backup_pending').all()
        for task in tasks:
            self._poolcache[task.pool_id]["backup"].backuptasks.append([task.id, task.datastore.type])
            task.status = 'backup_submitted'

            session.add(task)
            session.commit()

        tasks = session.query(ArchiveTask).filter(ArchiveTask.status == 'archive_pending').all()
        for task in tasks:
            # submit a task to the archive mover
            self._mover.archivetasks.append([task.id])
            task.status = 'archive_submitted'

            session.add(task)
            session.commit()

        session.close()

        for pool in self._poolcache:
            self._poolcache[pool]["backup"].run_backups()

        self._mover.run_archives()
        
        
        #threading.Timer(5, self.archive).start()
        threading.Timer(5, self.cleanup).start()

        # constant flow, wait five seconds
        threading.Timer(5, self.run).start()

    def cleanup(self):
        # cleanup task
        session = db.session
        if self._orphan_lock == False:
            # locking the cleanup task
            self._orphan_lock = True
            orphans = session.query(Host).filter(Host.pool_id == None).all()
            for orphan in orphans:
                log.info('Orphaned host found: ' + str(orphan.address))
                session.delete(orphan)
                session.commit()
            self._orphan_lock = False
        session.close()


    def archive(self):
        # if no lock in place
        if self._archive_lock == False:
            self._archive_lock = True

            session = db.session

            # get all the healthy archives 
            archives = session.query(Archive).filter(Archive.source_id.isnot(None), Archive.target_id.isnot(None)).all()
            for archive in archives:
                # for each archive check attached datastore backups
                backups = session.query(Backup).join(Task).filter(Task.datastore_id == archive.source_id)

                machines = {}
                # group in uuid
                for backup in backups:
                    if 'done' in backup.task.status:
                        try:
                            machines[backup.task.uuid].append(backup)
                        except: 
                            machines[backup.task.uuid] = []
                            machines[backup.task.uuid].append(backup)

                for machine in machines:
                    if len(machines[machine]) > archive.retention:
                        print 'Retention policy of : ' + str(archive.retention) + ' exceeded for uuid: ' + machine
                        # getting oldest: we only do one each time
                        oldest = None
                        try:
                            for b in machines[machine]:
                                if oldest is None:
                                    ongoing = session.query(ArchiveTask).filter(ArchiveTask.backup_id == b.id).all()
                                    if len(ongoing) == 0:
                                        oldest = b
                                else:
                                    if oldest.task.started > b.task.started:
                                         # check if not already archiving:
                                        ongoing = session.query(ArchiveTask).filter(ArchiveTask.backup_id == b.id).all()

                                        if len(ongoing) == 0:
                                            oldest = b
                        except Exception as e:
                            print e
                        print 'Marking backup to archive: ' + str(oldest.id)

                        # oldest.task.status = 'archive_pending'
                        archivetask = ArchiveTask(archive=archive, backup=oldest, status='archive_pending')

                        session.add(archivetask)
                        session.commit()

            # unlock
            session.close()
            self._archive_lock = False

