

import logging
import os
import configparser

log = logging.getLogger(__name__)


from bridge import Bridge

from database import db
from database.models import ArchiveTask

class Mover:
    """
    """
    archivetasks = []

    _server = None

    # TODO: remove lock
    _lock = False

    ARCHIVEROOT = '/media/.qnd'

    def __init__(self):
        # checking if mover is external
        if os.path.isfile('mover.ini'):
            # load the external mover
            config = configparser.ConfigParser()
            config.read('mover.ini')
            self._server=[config['mover']['hostname'], config['mover']['username'], config['mover']['password']]

    def run_archives(self):

        # Todo remove lock
        if self._lock == True:
            self._lock = True
            # run all archives

            # copy all jobs
            jobs = list(self.archivetasks)

            # empty tasks
            self.archive_tasks = []

            for job in jobs:
                self.archive(job)
            self._lock = False


    def archive(self, task_id):
        session = db.session
        # get backup object 
        task = session.query(ArchiveTask).filter(ArchiveTask.id == task_id[0]).one()

        # folders
        sid = self.ARCHIVEROOT + '/a-' + str(task.archive.source.id)
        tid = self.ARCHIVEROOT + '/a-' + str(task.archive.target.id)

        if self._server != None:
            m = Bridge(self._server[0], self._server[1], self._server[2])

            m.sudo_command('mkdir -p ' + sid, self._server[2])
            m.sudo_command('mkdir -p ' + tid, self._server[2])

            result = m.sudo_command('mount -t cifs -o username=' + task.archive.source.username + ',password=' + task.archive.source.password + ' ' + task.archive.source.host + ' ' + sid, self._server[2])
            result = m.sudo_command('mount -t cifs -o username=' + task.archive.target.username + ',password=' + task.archive.target.password + ' ' + task.archive.target.host + ' ' + tid, self._server[2])

            # move file
            result = m.sudo_command('mv ' + sid + '/' + task.backup.backupfile + ' ' + tid + '/' + task.backup.backupfile, self._server[2])

            # cleanup original task and backup
            cpb = task.backup
            cpt = task.archive
            task.status = 'archive_done'
            task.backup = None
            task.backup_id = None
            task.archive = None
            task.archive_id = None

            session.add(task)
            session.delete(cpb)
            session.delete(cpt)

            session.commit()

        session.close()