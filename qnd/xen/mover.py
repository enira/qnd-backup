import logging
import os
import configparser

log = logging.getLogger(__name__)

from bridge import Bridge

from database import db
from database.models import BackupTask, ArchiveTask, RestoreTask, Backup

class Mover:
    """
    Mover class, moves a VM backup from a datastore to an archive
    """
    _server = None

    ARCHIVEROOT = '/media/.qnd'

    def __init__(self):
        # checking if mover is external
        if os.path.isfile('config.ini'):
            # load the external mover
            config = configparser.ConfigParser()
            config.read('config.ini')
            self._server=[config['mover']['hostname'], config['mover']['username'], config['mover']['password']]
        else:
            if os.path.isfile('config.cfg'):
                # load the external mover
                config = configparser.ConfigParser()
                config.read('config.cfg')
                self._server=[config['mover']['hostname'], config['mover']['username'], config['mover']['password']]
            else:
                print 'No mover found, archiving not possible.'
                exit()


    def update_pct(self, task, pct1, pct2, divisor, status, session):
        """
        Update percentages for a given task
        """

        task.pct1 = 0
        if pct2 != None:
            task.pct2 = 0
        task.divisor = 0.20
        task.status = 'archive_' + status
        session.add(task)
        session.commit()

    def delete_reference(self, session, backup_id):
        """
        Deleting all reference tasks.
        """
        tasks = session.query(ArchiveTask).filter(ArchiveTask.backup_id == backup_id).all()
        for task in tasks:
            task.backup = None
            session.add(task)
            session.commit()

        tasks = session.query(BackupTask).filter(BackupTask.backup_id == backup_id).all()
        for task in tasks:
            task.backup = None
            session.add(task)
            session.commit()

        tasks = session.query(RestoreTask).filter(RestoreTask.backup_id == backup_id).all()
        for task in tasks:
            task.backup = None
            session.add(task)
            session.commit()    

    def archive(self, task_id):
        """
        Archive a VM.
        """
        print 'Archiving'

        session = db.session
        # get backup object 
        task = session.query(ArchiveTask).filter(ArchiveTask.id == task_id).one()

        # folders
        sid = self.ARCHIVEROOT + '/a-' + str(task.archive.source.id)
        tid = self.ARCHIVEROOT + '/a-' + str(task.archive.target.id)

        self.update_pct(task, 0.10, 0, 0.20, 'connecting', session)

        if self._server != None:
            m = Bridge(self._server[0], self._server[1], self._server[2])

            self.update_pct(task, 0.10, 0, 0.20, 'mounting', session)

            m.sudo_command('mkdir -p ' + sid, self._server[2])
            if m.is_connected() == False:
                # error trying to connect to data mover
                session.delete(task)
                session.commit()
                return
            m.sudo_command('mkdir -p ' + tid, self._server[2])

            result = m.sudo_command('mount -t cifs -o username=' + task.archive.source.username + ',password=' + task.archive.source.password + ' ' + task.archive.source.host + ' ' + sid, self._server[2])
            result = m.sudo_command('mount -t cifs -o username=' + task.archive.target.username + ',password=' + task.archive.target.password + ' ' + task.archive.target.host + ' ' + tid, self._server[2])

            result = m.command('df -h | grep -i ' + sid)
            if len(result) == 0:
                log.error('Could not mount the datastore')
                self.update_pct(task, 0.10, 0, 0.20, 'failed_mount', session)
                return
            result = m.command('df -h | grep -i ' + tid)
            if len(result) == 0:
                log.error('Could not mount the datastore')
                self.update_pct(task, 0.10, 0, 0.20, 'failed_mount', session)
                return

            # check if file is there 0: is there
            result = m.command('ls -ltr ' +  sid + '/' + task.backup.backupfile)
            if len(result) == 0:
                log.error('File does not exists')
                cpb = task.backup
                task.backup = None
                self.delete_reference(session, cpb.id)
                session.delete(cpb)
                session.commit()

                self.update_pct(task, 0.10, 0, 0.20, 'failed_notfound', session)
                return

            # move file
            result = m.sudo_command('mv ' + sid + '/' + task.backup.backupfile + ' ' + tid + '/' + task.backup.backupfile, self._server[2])

            # check if done
            if len(result) == 4:
                # this is an error
                self.update_pct(task, 0.10, 0, 0.20, 'failed_error', session)
                return

            # cleanup original task and backup
            cpb = task.backup
            task.backup = None
            self.delete_reference(session, cpb.id)
            session.delete(cpb)
            session.commit()

            self.update_pct(task, 0.10, 0, 0.20, 'done', session)

        else:
            self.update_pct(task, 0.10, 0, 0.20, 'failed_noserver', session)

        session.close()
        print 'Archiving done'